#!/usr/bin/env python3
"""Validate and render the provenance pipeline graph registry."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"
SPEC_ROOT_KEY = "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH"
REPORT_PATH = ROOT / "reports" / "provenance_pipeline_graph.md"


def load_spec() -> dict[str, Any]:
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{SPEC_PATH} did not parse to a mapping")
    if SPEC_ROOT_KEY in data:
        spec = data[SPEC_ROOT_KEY]
        if not isinstance(spec, dict):
            raise ValueError(f"{SPEC_PATH}.{SPEC_ROOT_KEY} did not parse to a mapping")
        return spec
    return data


def id_map(spec: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    items = spec.get(key, [])
    if not isinstance(items, list):
        raise ValueError(f"{key} must be a list")
    out: dict[str, dict[str, Any]] = {}
    duplicates = []
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"{key} contains an item without id")
        item_id = str(item["id"])
        if item_id in out:
            duplicates.append(item_id)
        out[item_id] = item
    if duplicates:
        raise ValueError(f"{key} contains duplicate IDs: {', '.join(sorted(set(duplicates)))}")
    return out


def eligibility_refs(eligibility: dict[str, Any]) -> list[str]:
    fields = [
        "include_when_all",
        "include_when_any",
        "include_when_applicable",
        "exclude_when_any",
        "allowed_with_caveat",
    ]
    refs: list[str] = []
    for field in fields:
        values = eligibility.get(field, [])
        if isinstance(values, list):
            refs.extend(str(value) for value in values)
        elif values:
            refs.append(str(values))
    return refs


def topological_order(node_ids: list[str], edges: list[dict[str, Any]], dag_id: str) -> list[str]:
    adjacency = {node_id: [] for node_id in node_ids}
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        start = str(edge.get("from", ""))
        end = str(edge.get("to", ""))
        adjacency[start].append(end)
        indegree[end] += 1

    ready = [node_id for node_id in node_ids if indegree[node_id] == 0]
    order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for child in adjacency[node_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(order) != len(node_ids):
        cycle_nodes = sorted(node_id for node_id in node_ids if indegree[node_id] > 0)
        raise ValueError(f"execution DAG {dag_id} contains a cycle involving: {', '.join(cycle_nodes)}")
    return order


def validate(spec: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    plot_universes = id_map(spec, "plot_universes")
    criteria = id_map(spec, "plot_universe_criteria")
    node_types = id_map(spec, "node_types")
    edge_types = id_map(spec, "edge_types")
    stages = id_map(spec, "stages")
    strategies = id_map(spec, "strategies")
    queues = id_map(spec, "queues")

    figure_scope = spec.get("current_figure_focus", {})
    for item in figure_scope.get("active_figures", []):
        universe_id = item.get("plot_universe_id")
        if universe_id not in plot_universes:
            raise ValueError(f"current_figure_focus.active_figures references unknown universe {universe_id!r}")
    for universe_id in figure_scope.get("catalog_only_universes", []):
        if universe_id not in plot_universes:
            raise ValueError(f"current_figure_focus.catalog_only_universes references unknown universe {universe_id!r}")

    for criterion_id, criterion in criteria.items():
        unknown_universes = sorted(
            universe_id
            for universe_id in criterion.get("reusable_in", [])
            if universe_id not in plot_universes
        )
        if unknown_universes:
            raise ValueError(
                f"plot_universe_criteria.{criterion_id}.reusable_in references unknown universes: "
                + ", ".join(unknown_universes)
            )

    for universe_id, universe in plot_universes.items():
        eligibility = universe.get("eligibility", {})
        if not isinstance(eligibility, dict):
            raise ValueError(f"plot_universes.{universe_id}.eligibility must be a mapping")
        unknown_criteria = sorted(ref for ref in eligibility_refs(eligibility) if ref not in criteria)
        if unknown_criteria:
            raise ValueError(
                f"plot_universes.{universe_id}.eligibility references unknown criteria: "
                + ", ".join(unknown_criteria)
            )

    for edge_id, edge in edge_types.items():
        for endpoint in ["from", "to"]:
            node_id = edge.get(endpoint)
            if node_id not in node_types:
                raise ValueError(f"edge_types.{edge_id}.{endpoint} references unknown node type {node_id!r}")

    required = set(spec.get("strategy_contract", {}).get("required_fields", []))
    if not required:
        raise ValueError("strategy_contract.required_fields is missing")

    for strategy_id, strategy in strategies.items():
        missing = sorted(field for field in required if field not in strategy)
        if missing:
            raise ValueError(f"strategy {strategy_id} missing required fields: {', '.join(missing)}")
        stage = strategy.get("stage")
        if stage not in stages:
            raise ValueError(f"strategy {strategy_id} references unknown stage {stage!r}")
        for field in ["input_node_types", "output_node_types"]:
            values = strategy.get(field, [])
            if not isinstance(values, list):
                raise ValueError(f"strategy {strategy_id}.{field} must be a list")
            unknown = sorted(value for value in values if value not in node_types)
            if unknown:
                raise ValueError(f"strategy {strategy_id}.{field} references unknown node types: {', '.join(unknown)}")
        if not strategy.get("writes"):
            warnings.append(f"strategy {strategy_id} has no writes declared")

    for queue_id, queue in queues.items():
        node_type = queue.get("node_type")
        if node_type not in node_types:
            raise ValueError(f"queue {queue_id} references unknown node_type {node_type!r}")
        table = queue.get("table")
        if table and not (ROOT / table).exists():
            warnings.append(f"queue {queue_id} table does not currently exist: {table}")

    for dag in spec.get("execution_dags", []):
        if not isinstance(dag, dict) or not dag.get("id"):
            raise ValueError("execution_dags contains an item without id")
        dag_id = str(dag["id"])
        nodes = dag.get("nodes", [])
        edges = dag.get("edges", [])
        if not isinstance(nodes, list) or not nodes:
            raise ValueError(f"execution DAG {dag_id} must contain nodes")
        if not isinstance(edges, list):
            raise ValueError(f"execution DAG {dag_id}.edges must be a list")
        node_ids: list[str] = []
        for node in nodes:
            if not isinstance(node, dict) or not node.get("id"):
                raise ValueError(f"execution DAG {dag_id} contains a node without id")
            node_id = str(node["id"])
            if node_id in node_ids:
                raise ValueError(f"execution DAG {dag_id} contains duplicate node id {node_id!r}")
            node_ids.append(node_id)
        node_id_set = set(node_ids)
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError(f"execution DAG {dag_id} contains a non-mapping edge")
            for endpoint in ["from", "to"]:
                endpoint_id = str(edge.get(endpoint, ""))
                if endpoint_id not in node_id_set:
                    raise ValueError(
                        f"execution DAG {dag_id} edge references unknown {endpoint} node {endpoint_id!r}"
                    )
        topological_order(node_ids, edges, dag_id)

    return warnings


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        values = []
        for key, _label in columns:
            value = row.get(key, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            value = str(value).replace("\n", " ").replace("|", "\\|")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return lines


def current_metrics(spec: dict[str, Any]) -> list[str]:
    benchmark = spec.get("current_benchmark", {})
    source_result_path = ROOT / benchmark.get("source_result_table", "")
    tail_path = ROOT / benchmark.get("tail_queue_table", "")
    lines: list[str] = []
    if source_result_path.exists():
        source_result = pd.read_csv(source_result_path, sep="\t", dtype=str, keep_default_na=False)
        levels = source_result["evidence_level"].astype(int)
        n = len(source_result)
        labels = {
            int(row["level"]): row["name"]
            for row in spec.get("evidence_ladder", [])
            if "level" in row and "name" in row
        }
        lines.extend(["## Current 300-Row Benchmark", ""])
        lines.extend(
            markdown_table(
                [
                    {
                        "minimum": f"{level}: {labels.get(level, '')}",
                        "rows": int((levels >= level).sum()),
                        "percent": f"{(levels >= level).sum() / n * 100:.1f}%",
                    }
                    for level in range(2, 8)
                ],
                [("minimum", "Minimum Evidence Standard"), ("rows", "Rows"), ("percent", "Percent")],
            )
        )
        lines.append("")
        counts = (
            source_result.groupby(["evidence_level", "evidence_level_name"])
            .size()
            .reset_index(name="rows")
            .sort_values("evidence_level", key=lambda col: col.astype(int))
        )
        lines.extend(
            markdown_table(
                [
                    {
                        "level": f"{row.evidence_level}: {row.evidence_level_name}",
                        "rows": int(row.rows),
                        "percent": f"{int(row.rows) / n * 100:.1f}%",
                    }
                    for row in counts.itertuples(index=False)
                ],
                [("level", "Current Level"), ("rows", "Rows"), ("percent", "Percent")],
            )
        )
        lines.append("")
    if tail_path.exists():
        tail = pd.read_csv(tail_path, sep="\t", dtype=str, keep_default_na=False)
        lines.extend(["## Active Tail Queue", ""])
        by_bucket = tail.groupby(["rank", "next_bucket", "tail_problem_family"]).size().reset_index(name="rows")
        by_bucket = by_bucket.sort_values(["rank", "next_bucket"])
        lines.extend(
            markdown_table(
                [
                    {
                        "rank": row.rank,
                        "bucket": row.next_bucket,
                        "family": row.tail_problem_family,
                        "rows": int(row.rows),
                    }
                    for row in by_bucket.itertuples(index=False)
                ],
                [("rank", "Rank"), ("bucket", "Bucket"), ("family", "Problem Family"), ("rows", "Rows")],
            )
        )
        lines.append("")
    return lines


def render(spec: dict[str, Any], warnings: list[str]) -> str:
    node_types = id_map(spec, "node_types")
    edge_types = id_map(spec, "edge_types")
    criteria = list(id_map(spec, "plot_universe_criteria").values())
    strategies = list(id_map(spec, "strategies").values())
    stages = list(id_map(spec, "stages").values())
    queues = list(id_map(spec, "queues").values())

    status_counts = Counter(strategy.get("status", "unknown") for strategy in strategies)
    stage_counts = Counter(strategy.get("stage", "unknown") for strategy in strategies)

    lines: list[str] = [
        "# Provenance Pipeline Graph",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Spec: `{SPEC_PATH.relative_to(ROOT)}`",
        f"- Spec root: `{SPEC_ROOT_KEY}`",
        f"- Schema version: `{spec.get('schema_version', '')}`",
        f"- Strategies: {len(strategies)}",
        f"- Node types: {len(node_types)}",
        f"- Edge types: {len(edge_types)}",
        f"- Execution DAGs: {len(spec.get('execution_dags', []))}",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(["## Operating Principles", ""])
    for principle in spec.get("principles", []):
        lines.append(f"- `{principle['id']}`: {principle['text']}")
    lines.append("")

    figure_scope = spec.get("current_figure_focus", {})
    if figure_scope:
        lines.extend(["## Current Figure Focus", ""])
        lines.extend(
            markdown_table(
                figure_scope.get("active_figures", []),
                [
                    ("figure_number", "Figure"),
                    ("plot_universe_id", "Universe"),
                    ("role", "Role"),
                    ("plain_english", "Plain English"),
                ],
            )
        )
        lines.append("")
        catalog_rows = [
            {"plot_universe_id": universe_id, "role": "catalog_only_future_plot_seed"}
            for universe_id in figure_scope.get("catalog_only_universes", [])
        ]
        if catalog_rows:
            lines.extend(
                markdown_table(
                    catalog_rows,
                    [("plot_universe_id", "Catalog Universe"), ("role", "Role")],
                )
            )
            lines.append("")
        if figure_scope.get("catalog_policy"):
            lines.extend(["Catalog policy:", ""])
            for policy in figure_scope["catalog_policy"]:
                lines.append(f"- {policy}")
            lines.append("")

    schema_contract = spec.get("database_schema_contract", {})
    if schema_contract:
        lines.extend(["## Database Schema Contract", ""])
        if schema_contract.get("purpose"):
            lines.extend([str(schema_contract["purpose"]), ""])
        if schema_contract.get("operating_rules"):
            lines.extend(["Operating rules:", ""])
            for rule in schema_contract["operating_rules"]:
                lines.append(f"- {rule}")
            lines.append("")
        layer_rows = []
        for layer in schema_contract.get("table_layers", []):
            tables = []
            roles = []
            for table in layer.get("tables", []):
                tables.append(table.get("table", ""))
                roles.append(f"{table.get('table', '')}: {table.get('grain', '')}")
            layer_rows.append(
                {
                    "id": layer.get("id", ""),
                    "context_sensitivity": layer.get("context_sensitivity", ""),
                    "tables": tables,
                    "roles": roles,
                }
            )
        if layer_rows:
            lines.extend(
                markdown_table(
                    layer_rows,
                    [
                        ("id", "Layer"),
                        ("context_sensitivity", "Context Sensitivity"),
                        ("tables", "Tables"),
                        ("roles", "Grains"),
                    ],
                )
            )
            lines.append("")
        if schema_contract.get("sample_300_lessons"):
            lines.extend(["300-sample lessons:", ""])
            for lesson in schema_contract["sample_300_lessons"]:
                lines.append(f"- {lesson}")
            lines.append("")

    execution_dags = spec.get("execution_dags", [])
    if execution_dags:
        lines.extend(["## Execution DAGs", ""])
        for dag in execution_dags:
            nodes = dag.get("nodes", [])
            edges = dag.get("edges", [])
            node_ids = [str(node.get("id", "")) for node in nodes]
            order = topological_order(node_ids, edges, str(dag.get("id", "")))
            lines.append(f"### `{dag.get('id', '')}`")
            lines.append("")
            lines.append(f"- Scope: `{dag.get('scope', '')}`")
            lines.append(f"- Status: `{dag.get('status', '')}`")
            if dag.get("principle"):
                lines.append(f"- Principle: {dag['principle']}")
            lines.append(f"- Topological order: {' -> '.join(order)}")
            lines.append("")
            lines.extend(
                markdown_table(
                    nodes,
                    [
                        ("id", "Node"),
                        ("kind", "Kind"),
                        ("materialized_as", "Materialized As"),
                        ("role", "Role"),
                        ("dedupe_order", "Dedupe Order"),
                    ],
                )
            )
            lines.append("")
            lines.extend(
                markdown_table(
                    edges,
                    [("from", "From"), ("to", "To"), ("kind", "Edge Kind")],
                )
            )
            lines.append("")

    lines.extend(["## Plot Universe Criteria Registry", ""])
    lines.extend(
        markdown_table(
            criteria,
            [
                ("id", "Criterion"),
                ("gate_type", "Gate Type"),
                ("rule", "Rule"),
                ("accept_if", "Accept If"),
                ("reject_if", "Reject If"),
                ("evidence_fields", "Evidence Fields"),
            ],
        )
    )
    lines.append("")

    lines.extend(["## Plot Universes", ""])
    universe_rows = []
    for universe in spec.get("plot_universes", []):
        eligibility = universe.get("eligibility", {})
        universe_rows.append(
            {
                **universe,
                "current_scope_role": universe.get("current_scope_role", ""),
                "figure_label": universe.get("figure_label", ""),
                "publication_requirement": eligibility.get("publication_requirement", ""),
                "publication_policy": eligibility.get("publication_policy", ""),
                "search_direction": eligibility.get("search_direction", ""),
                "search_policy": eligibility.get("search_policy", ""),
                "output_unit": eligibility.get("output_unit", ""),
                "include_when_all": eligibility.get("include_when_all", []),
                "include_when_applicable": eligibility.get("include_when_applicable", []),
                "exclude_when_any": eligibility.get("exclude_when_any", []),
            }
        )
    lines.extend(
        markdown_table(
            universe_rows,
            [
                ("id", "Universe"),
                ("figure_label", "Figure"),
                ("current_scope_role", "Current Scope"),
                ("result_target_kind", "Result Target"),
                ("publication_requirement", "Publication Required"),
                ("publication_policy", "Publication Policy"),
                ("search_direction", "Search Direction"),
                ("search_policy", "Search Policy"),
                ("output_unit", "Output Unit"),
                ("include_when_all", "Required Criteria"),
                ("include_when_applicable", "Applicable Criteria"),
                ("exclude_when_any", "Exclusion Criteria"),
                ("represented_source_kinds", "Represented Sources"),
                ("evidence_object_kinds", "Evidence Objects"),
            ],
        )
    )
    lines.append("")

    lines.extend(["## Stages", ""])
    stage_rows = sorted(stages, key=lambda row: int(row.get("rank", 999)))
    lines.extend(
        markdown_table(
            stage_rows,
            [("rank", "Rank"), ("id", "Stage"), ("question", "Question"), ("primary_output_nodes", "Primary Outputs")],
        )
    )
    lines.append("")

    lines.extend(["## Node Types", ""])
    lines.extend(
        markdown_table(
            list(node_types.values()),
            [("id", "Node Type"), ("description", "Description"), ("canonical_tables", "Canonical Tables")],
        )
    )
    lines.append("")

    lines.extend(["## Edge Types", ""])
    lines.extend(
        markdown_table(
            list(edge_types.values()),
            [("id", "Edge"), ("from", "From"), ("to", "To"), ("meaning", "Meaning")],
        )
    )
    lines.append("")

    lines.extend(["## Strategy Registry", ""])
    strategy_rows = sorted(strategies, key=lambda row: (int(row.get("rank", 999)), row.get("id", "")))
    lines.extend(
        markdown_table(
            [
                {
                    "rank": strategy.get("rank", ""),
                    "id": strategy.get("id", ""),
                    "stage": strategy.get("stage", ""),
                    "status": strategy.get("status", ""),
                    "inputs": strategy.get("input_node_types", []),
                    "outputs": strategy.get("output_node_types", []),
                    "applies_when": strategy.get("applies_when", ""),
                }
                for strategy in strategy_rows
            ],
            [
                ("rank", "Rank"),
                ("id", "Strategy"),
                ("stage", "Stage"),
                ("status", "Status"),
                ("inputs", "Inputs"),
                ("outputs", "Outputs"),
                ("applies_when", "Applies When"),
            ],
        )
    )
    lines.append("")

    lines.extend(["## Strategy Counts", ""])
    lines.extend(["### By Status", ""])
    lines.extend(
        markdown_table(
            [{"status": key, "strategies": value} for key, value in sorted(status_counts.items())],
            [("status", "Status"), ("strategies", "Strategies")],
        )
    )
    lines.extend(["", "### By Stage", ""])
    lines.extend(
        markdown_table(
            [{"stage": key, "strategies": value} for key, value in sorted(stage_counts.items())],
            [("stage", "Stage"), ("strategies", "Strategies")],
        )
    )
    lines.append("")

    lines.extend(["## Queues", ""])
    lines.extend(
        markdown_table(
            queues,
            [("id", "Queue"), ("table", "Table"), ("node_type", "Node Type"), ("description", "Description")],
        )
    )
    lines.append("")

    lines.extend(["## Promotion Gates", ""])
    for gate_id, gate in spec.get("promotion_gates", {}).items():
        lines.append(f"### `{gate_id}`")
        lines.append("")
        lines.append(f"- After: `{gate.get('source_state_after', '')}`")
        lines.append(f"- Required evidence: {', '.join(gate.get('required_evidence', []))}")
        lines.append(f"- Reject if: {', '.join(gate.get('reject_if', []))}")
        lines.append("")

    lines.extend(current_metrics(spec))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    spec = load_spec()
    warnings = validate(spec)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render(spec, warnings), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
