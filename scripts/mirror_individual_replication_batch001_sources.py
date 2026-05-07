#!/usr/bin/env python3
"""Mirror source objects for individual-replication search worklists."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKLISTS = [
    ROOT / "steps" / "individual_replication_papers" / "figure1" / "individual-paper-worklist-from-search.tsv",
    ROOT / "steps" / "individual_replication_papers" / "figure1" / "individual-paper-worklist-d-equivalent.tsv",
    ROOT / "steps" / "individual_replication_papers" / "figure1" / "individual-paper-worklist-native-only.tsv",
    ROOT / "steps" / "individual_replication_papers" / "figure1" / "individual-paper-worklist-coverage-only.tsv",
]
OUT_DIR = ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch001"
STATUS = ROOT / "steps" / "individual_replication_papers" / "figure1" / "individual-paper-source-mirror-batch001.tsv"


def configure_batch(batch_id: str) -> None:
    global OUT_DIR, STATUS
    OUT_DIR = ROOT / "data" / "raw" / "replication_projects" / f"individual_search_{batch_id}"
    STATUS = ROOT / "steps" / "individual_replication_papers" / "figure1" / f"individual-paper-source-mirror-{batch_id}.tsv"


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def slugify(text: str, max_len: int = 72) -> str:
    text = re.sub(r"^https?://", "", text.lower())
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:max_len].strip("_") or "source"


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def extension_from(content_type: str, url: str) -> str:
    lower_url = url.lower()
    if "format=pdf" in lower_url:
        return ".pdf"
    for ext in [".pdf", ".html", ".htm", ".xml", ".json", ".csv", ".tsv", ".xlsx", ".zip"]:
        if ext in lower_url:
            return ext
    ctype = content_type.split(";", 1)[0].strip().lower()
    if ctype in {"text/html", "application/xhtml+xml"}:
        return ".html"
    if ctype == "application/pdf":
        return ".pdf"
    guessed = mimetypes.guess_extension(ctype)
    return guessed or ".bin"


def fetch(url: str, timeout: int) -> tuple[str, dict[str, str], bytes | None, str]:
    url = clean(url)
    if re.match(r"^10\.\d{4,9}/", url, flags=re.I):
        url = f"https://doi.org/{url}"
    if not re.match(r"^https?://", url, flags=re.I):
        return url, {}, None, "invalid_url_no_http_scheme"
    headers = {
        "User-Agent": "Mozilla/5.0 figure1-replication-source-mirror/1.0",
        "Accept": "text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            data = resp.read()
            final_url = resp.geturl()
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return final_url, hdrs, data, ""
    except urllib.error.HTTPError as exc:
        return exc.geturl() or url, {k.lower(): v for k, v in exc.headers.items()}, None, f"http_error_{exc.code}"
    except Exception as exc:
        return url, {}, None, f"{type(exc).__name__}: {exc}"


def existing_local_mirror(cand_dir: Path, index: int) -> tuple[str, str, int, str] | None:
    files = sorted(path for path in cand_dir.glob(f"{index:02d}_*") if path.is_file())
    if not files:
        return None
    path = files[0]
    data = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or ""
    return str(path.relative_to(ROOT)), sha256_bytes(data), len(data), content_type


def write_status(rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).fillna("").to_csv(STATUS, sep="\t", index=False)


def load_worklists() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in WORKLISTS:
        if not path.exists():
            continue
        frame = pd.read_csv(path, sep="\t", dtype=str).fillna("")
        frame["worklist_path"] = str(path.relative_to(ROOT))
        frames.append(frame)
    if not frames:
        raise FileNotFoundError("No individual-replication worklist TSVs found.")
    return pd.concat(frames, ignore_index=True, sort=False).fillna("")


def mirror(timeout: int, sleep_seconds: float) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    worklist = load_worklists()
    rows: list[dict[str, Any]] = []
    for _, candidate in worklist.iterrows():
        candidate_id = clean(candidate["candidate_id"])
        urls = json.loads(candidate["source_object_urls_json"] or "[]")
        cand_dir = OUT_DIR / candidate_id
        cand_dir.mkdir(parents=True, exist_ok=True)
        for index, url in enumerate(urls, start=1):
            existing = existing_local_mirror(cand_dir, index)
            final_url = url
            error = ""
            content_type = ""
            status = "mirrored"
            local_path = ""
            digest = ""
            byte_count = 0
            retrieval_method = "python_urllib_user_agent"
            data = None
            if existing:
                local_path, digest, byte_count, content_type = existing
                retrieval_method = "existing_local_file_reuse"
            else:
                final_url, headers, data, error = fetch(url, timeout=timeout)
                content_type = headers.get("content-type", "")
                status = "mirrored" if data else "failed"
            if data:
                digest = sha256_bytes(data)
                byte_count = len(data)
                ext = extension_from(content_type, final_url)
                file_name = f"{index:02d}_{slugify(final_url)}_{digest[:12]}{ext}"
                path = cand_dir / file_name
                path.write_bytes(data)
                local_path = str(path.relative_to(ROOT))
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_name": clean(candidate["candidate_name"]),
                    "route_type": clean(candidate.get("route_type")),
                    "candidate_route": clean(candidate.get("candidate_route")),
                    "worklist_path": clean(candidate.get("worklist_path")),
                    "source_url": url,
                    "final_url": final_url,
                    "mirror_status": status,
                    "error_or_blocker": error,
                    "content_type": content_type,
                    "byte_count": byte_count,
                    "sha256": digest,
                    "local_path": local_path,
                    "retrieval_method": retrieval_method,
                    "created_at": "2026-05-05T00:00:00",
                }
            )
            write_status(rows)
            if sleep_seconds:
                time.sleep(sleep_seconds)
    write_status(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--replace", action="store_true", help="Accepted for Makefile consistency; outputs are always regenerated.")
    args = parser.parse_args()
    configure_batch(args.batch_id)
    mirror(timeout=args.timeout, sleep_seconds=args.sleep)


if __name__ == "__main__":
    main()
