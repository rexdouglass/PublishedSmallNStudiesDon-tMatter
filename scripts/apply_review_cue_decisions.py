#!/usr/bin/env python3
"""Apply review-cue decisions as per-lead route receipt target files.

This step deliberately does not edit root tables yet. It validates decision
JSON artifacts and materializes one stable receipt file per reviewed lead under
the cue's configured receipt root. Future cue builds can skip reviewed leads by
checking those files.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_YML = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"


def safe_text(value: object, max_len: int = 6000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def slugify(value: object, fallback: str = "lead") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:160] or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def load_cue(cue_id: str) -> dict[str, Any]:
    payload = yaml.safe_load(PIPELINE_YML.read_text(encoding="utf-8")) or {}
    root = payload.get("PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH") or {}
    for cue in root.get("review_cues") or []:
        if cue.get("id") == cue_id:
            return cue
    raise ValueError(f"Unknown review cue {cue_id!r}")


def decision_contract(cue: dict[str, Any]) -> dict[str, Any]:
    return cue.get("decision_contract") or {}


def decision_files(cue: dict[str, Any], explicit_paths: list[str]) -> list[Path]:
    if explicit_paths:
        return [resolve_path(path) for path in explicit_paths]
    paths: list[Path] = []
    for pattern in cue.get("reviewed_decision_globs") or []:
        paths.extend(sorted(ROOT.glob(pattern)))
    return paths


def receipt_path(cue: dict[str, Any], decision: dict[str, Any]) -> Path:
    receipts = cue.get("route_receipts") or {}
    root = resolve_path(str(receipts.get("root") or f"steps/review_cue/{cue['id']}/receipts"))
    routes = receipts.get("decision_directories") or {}
    decision_value = safe_text(decision.get("decision"))
    directory = safe_text(routes.get(decision_value) or routes.get("default") or "needs_more_evidence")
    key = safe_text(decision.get("lead_key") or decision.get("review_id"))
    return root / directory / f"{slugify(key)}.json"


def validate_decision(cue: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    contract = decision_contract(cue)
    errors: list[str] = []
    for field in contract.get("required_fields") or ["review_id", "lead_key", "decision", "confidence", "reason", "next_action"]:
        if not safe_text(decision.get(field)):
            errors.append(f"missing_required_field:{field}")
    allowed = set(contract.get("allowed_decisions") or [])
    decision_value = safe_text(decision.get("decision"))
    if allowed and decision_value not in allowed:
        errors.append(f"unknown_decision:{decision_value}")
    allowed_confidence = set(contract.get("allowed_confidence") or ["high", "medium", "low"])
    confidence = safe_text(decision.get("confidence"))
    if confidence and confidence not in allowed_confidence:
        errors.append(f"unknown_confidence:{confidence}")
    if "sources_checked" in decision and not isinstance(decision.get("sources_checked"), list):
        errors.append("sources_checked_must_be_list")
    if "promote_payload" in decision and not isinstance(decision.get("promote_payload") or {}, dict):
        errors.append("promote_payload_must_be_object")
    if "route_payload" in decision and not isinstance(decision.get("route_payload") or {}, dict):
        errors.append("route_payload_must_be_object")
    route_payload = decision.get("route_payload") or {}
    decision_requirements = (contract.get("decision_specific_requirements") or {}).get(decision_value) or {}
    for field in decision_requirements.get("required_route_payload_fields") or []:
        if not safe_text(route_payload.get(field)):
            errors.append(f"missing_route_payload_field:{field}")
    for key, allowed_values in decision_requirements.items():
        if not str(key).startswith("allowed_") or not isinstance(allowed_values, list):
            continue
        field = str(key).removeprefix("allowed_")
        value = safe_text(route_payload.get(field) or decision.get(field))
        if value and value not in set(safe_text(item) for item in allowed_values):
            errors.append(f"unknown_{field}:{value}")
    return errors


def remove_superseded_receipts(cue: dict[str, Any], decision: dict[str, Any], keep_path: Path, dry_run: bool) -> int:
    receipts = cue.get("route_receipts") or {}
    root = resolve_path(str(receipts.get("root") or f"steps/review_cue/{cue['id']}/receipts"))
    if not root.exists():
        return 0
    target_keys = {
        safe_text(decision.get("lead_key")),
        safe_text(decision.get("review_id")),
    }
    target_keys = {key for key in target_keys if key}
    removed = 0
    for path in root.glob("*/*.json"):
        if path == keep_path:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        existing_keys = {
            safe_text(payload.get("lead_key")),
            safe_text(payload.get("review_id")),
        }
        if target_keys & {key for key in existing_keys if key}:
            print(f"{'Would remove' if dry_run else 'Removing'} superseded receipt {repo_path(path)}")
            if not dry_run:
                path.unlink()
            removed += 1
    return removed


def apply_file(cue: dict[str, Any], path: Path, replace: bool, dry_run: bool) -> tuple[int, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    written = 0
    skipped = 0
    for decision in payload.get("decisions", []):
        if not isinstance(decision, dict):
            skipped += 1
            continue
        errors = validate_decision(cue, decision)
        if errors:
            print(f"Skipped decision in {repo_path(path)}: {', '.join(errors)}")
            skipped += 1
            continue
        out_path = receipt_path(cue, decision)
        if out_path.exists() and not replace:
            print(f"Skipped existing receipt {repo_path(out_path)}")
            skipped += 1
            continue
        if replace:
            remove_superseded_receipts(cue, decision, out_path, dry_run)
        receipt = {
            "cue_id": cue["id"],
            "created_at": utc_now(),
            "decision_source": repo_path(path),
            "review_id": safe_text(decision.get("review_id")),
            "lead_key": safe_text(decision.get("lead_key")),
            "canonical_source_key": safe_text(decision.get("canonical_source_key")),
            "duplicate_of": safe_text(decision.get("duplicate_of")),
            "decision": safe_text(decision.get("decision")),
            "confidence": safe_text(decision.get("confidence")),
            "reason": safe_text(decision.get("reason")),
            "next_action": safe_text(decision.get("next_action")),
            "sources_checked": decision.get("sources_checked") or [],
            "promote_payload": decision.get("promote_payload") or {},
            "route_payload": decision.get("route_payload") or {},
            "user_gpt_prompt_request": safe_text(decision.get("user_gpt_prompt_request")),
            "notes": safe_text(decision.get("notes")),
        }
        print(f"{'Would write' if dry_run else 'Writing'} {repo_path(out_path)}")
        if not dry_run:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        written += 1
    return written, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cue-id", required=True)
    parser.add_argument("--decision-file", action="append", default=[])
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cue = load_cue(args.cue_id)
    total_written = 0
    total_skipped = 0
    for path in decision_files(cue, args.decision_file):
        if not path.exists():
            print(f"Missing decision file {repo_path(path)}")
            total_skipped += 1
            continue
        written, skipped = apply_file(cue, path, args.replace, args.dry_run)
        total_written += written
        total_skipped += skipped
    print(f"Review cue {args.cue_id}: receipts_written={total_written}; skipped={total_skipped}")


if __name__ == "__main__":
    main()
