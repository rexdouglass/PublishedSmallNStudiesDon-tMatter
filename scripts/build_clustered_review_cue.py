#!/usr/bin/env python3
"""Build a bounded Codex prompt for clustered Figure 1 search-lead review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLUSTERS_JSON = ROOT / "steps" / "searches" / "figure1" / "alias-clusters-leads-artifacts-root-v001.json"
REVIEW_ROOT = ROOT / "steps" / "review_cue" / "figure1_search_leads"


def safe_text(value: object, max_len: int = 5000) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\t", " ").split())[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_clusters() -> list[dict[str, Any]]:
    payload = json.loads(CLUSTERS_JSON.read_text(encoding="utf-8"))
    return list(payload.get("clusters") or [])


def select_clusters(clusters: list[dict[str, Any]], offset: int, batch_size: int) -> list[dict[str, Any]]:
    eligible = [
        cluster
        for cluster in clusters
        if cluster.get("recommended_next_action") == "review_cluster_representative"
        and int(cluster.get("open_review_count") or 0) > 0
        and cluster.get("priority_band") in {"high", "medium"}
    ]
    return eligible[offset : offset + batch_size]


def compact_node(node: dict[str, Any]) -> dict[str, str]:
    return {
        "node_id": safe_text(node.get("node_id")),
        "node_source": safe_text(node.get("node_source")),
        "name": safe_text(node.get("name"), 500),
        "record_kind": safe_text(node.get("record_kind")),
        "inventory_status": safe_text(node.get("inventory_status")),
        "review_queue_status": safe_text(node.get("review_queue_status")),
        "landing_url": safe_text(node.get("landing_url"), 500),
        "source_key": safe_text(node.get("source_key"), 500),
        "manifest_path": safe_text(node.get("manifest_path"), 500),
        "why_relevant": safe_text(node.get("why_relevant"), 800),
        "next_action": safe_text(node.get("next_action"), 500),
    }


def compact_cluster(cluster: dict[str, Any], max_nodes: int) -> dict[str, Any]:
    nodes = list(cluster.get("nodes") or [])
    nodes.sort(
        key=lambda node: (
            node.get("review_queue_status") not in {"needs_review", "needs_root_candidate_review"},
            node.get("node_source") != "root_table",
            node.get("name", ""),
        )
    )
    return {
        "cluster_id": cluster.get("cluster_id"),
        "representative_name": cluster.get("representative_name"),
        "priority_band": cluster.get("priority_band"),
        "priority_score": cluster.get("priority_score"),
        "cluster_confidence": cluster.get("cluster_confidence"),
        "preferred_family_hint": cluster.get("preferred_family_hint"),
        "recommended_next_action": cluster.get("recommended_next_action"),
        "node_count": cluster.get("node_count"),
        "open_review_count": cluster.get("open_review_count"),
        "receipt_count": cluster.get("receipt_count"),
        "max_source_object_score": cluster.get("max_source_object_score"),
        "max_pair_evidence_score": cluster.get("max_pair_evidence_score"),
        "strict_keys": list(cluster.get("strict_keys") or [])[:12],
        "record_kind_counts": cluster.get("record_kind_counts") or {},
        "inventory_status_counts": cluster.get("inventory_status_counts") or {},
        "manifest_paths": list(cluster.get("manifest_paths") or [])[:8],
        "nodes_in_prompt": [compact_node(node) for node in nodes[:max_nodes]],
        "omitted_node_count": max(0, len(nodes) - max_nodes),
    }


def prompt_text(clusters: list[dict[str, Any]], decision_path: Path) -> str:
    lines = [
        "# Clustered Codex Review: Figure 1 Search Leads",
        "",
        "Review source-family clusters, not isolated search hits. Use the aliases/artifacts in each cluster to decide what the cluster is.",
        "",
        "Do not edit root tables. Save JSON decisions using the contract below.",
        "",
        f"Save decisions as: `{repo_path(decision_path)}`",
        "",
        "Allowed cluster decisions:",
        "- keep_source_family_candidate",
        "- inventory_source_family_artifacts",
        "- route_cluster_to_result_table_worklist",
        "- route_cluster_to_individual_replication_paper_worklist",
        "- keep_cluster_as_context",
        "- reject_cluster_irrelevant",
        "- needs_more_evidence",
        "",
        "Decision rule:",
        "- Keep/inventory a cluster only when there is evidence of a reusable source object: dataset, database, registry, code/data repository, workbook, table, file inventory, or explicit source-family page.",
        "- Route individual replication papers away from corpus/database intake unless they expose a reusable multi-row source.",
        "- Do not infer file contents from titles alone.",
        "- If a cluster contains child artifacts under a source family, say which parent source-family row should own them.",
        "",
        "Return JSON only:",
        "",
        "```json",
        json.dumps(
            {
                "cluster_decisions": [
                    {
                        "cluster_id": "...",
                        "decision": "keep_source_family_candidate|inventory_source_family_artifacts|route_cluster_to_result_table_worklist|route_cluster_to_individual_replication_paper_worklist|keep_cluster_as_context|reject_cluster_irrelevant|needs_more_evidence",
                        "confidence": "high|medium|low",
                        "preferred_source_family_name": "...",
                        "parent_corpus_database_id_or_key": "...",
                        "reason": "...",
                        "next_action": "...",
                        "sources_checked": ["..."],
                        "lead_level_notes": [
                            {"node_id": "...", "suggested_disposition": "root_source_family|child_artifact|individual_paper|context|reject|needs_more_evidence", "notes": "..."}
                        ],
                    }
                ]
            },
            indent=2,
        ),
        "```",
        "",
        "Clusters:",
    ]
    for idx, cluster in enumerate(clusters, start=1):
        lines.extend(
            [
                "",
                f"## {idx}. {cluster['representative_name']}",
                f"- cluster_id: `{cluster['cluster_id']}`",
                f"- priority: `{cluster['priority_band']} / {cluster['priority_score']}`",
                f"- confidence: `{cluster['cluster_confidence']}`",
                f"- preferred_family_hint: `{cluster.get('preferred_family_hint', '')}`",
                f"- node_count: `{cluster['node_count']}`; open_review_count: `{cluster['open_review_count']}`; omitted_node_count: `{cluster['omitted_node_count']}`",
                f"- strict_keys: `{ ' | '.join(cluster.get('strict_keys') or []) }`",
                f"- record_kind_counts: `{json.dumps(cluster.get('record_kind_counts') or {}, sort_keys=True)}`",
                f"- inventory_status_counts: `{json.dumps(cluster.get('inventory_status_counts') or {}, sort_keys=True)}`",
                "",
                "Compact nodes:",
                "",
                "```json",
                json.dumps(cluster["nodes_in_prompt"], indent=2, sort_keys=True),
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def write_text(path: Path, text: str, replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default="clustered001")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-nodes-per-cluster", type=int, default=12)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    clusters = [compact_cluster(cluster, args.max_nodes_per_cluster) for cluster in select_clusters(load_clusters(), args.offset, args.batch_size)]
    decision_path = REVIEW_ROOT / f"reviewcue-clustered-decisions-figure1_search_leads-codex-{args.batch_id}.json"
    batch_path = REVIEW_ROOT / f"reviewcue-clustered-codex-{args.batch_id}-figure1_search_leads.json"
    prompt_path = REVIEW_ROOT / f"reviewcue-clustered-codex-{args.batch_id}-figure1_search_leads-prompt.md"
    payload = {
        "batch_id": args.batch_id,
        "reviewer": "codex",
        "offset": args.offset,
        "batch_size": args.batch_size,
        "decision_output": repo_path(decision_path),
        "cluster_count": len(clusters),
        "clusters": clusters,
    }
    write_json(batch_path, payload, args.replace)
    write_text(prompt_path, prompt_text(clusters, decision_path), args.replace)
    print(f"Clustered review batch {args.batch_id}: {len(clusters)} cluster(s).")


if __name__ == "__main__":
    main()
