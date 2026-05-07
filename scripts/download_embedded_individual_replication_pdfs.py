#!/usr/bin/env python3
"""Download PDF links embedded in mirrored individual-replication HTML pages."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "replication_projects" / "individual_auto_mining_blockers"
OUT_TSV = (
    ROOT
    / "steps"
    / "individual_replication_papers"
    / "figure1"
    / "auto_mining"
    / "individual-paper-embedded-pdf-downloads.tsv"
)


FIELDNAMES = [
    "candidate_id",
    "source_html_path",
    "pdf_url",
    "http_status",
    "content_type",
    "bytes",
    "sha256",
    "local_path",
    "access_state",
    "error_or_note",
]


PDF_RE = re.compile(r"https?://[^\"'<> ]+?\.pdf(?:\?[^\"'<> ]*)?", re.IGNORECASE)


def clean_url(url: str) -> str:
    return url.replace("&amp;", "&")


def safe_name(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    stem = Path(parsed.path).name or "embedded.pdf"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    if not stem.lower().endswith(".pdf"):
        stem += ".pdf"
    return f"embedded_pdf__{digest}__{stem}"


def download(url: str, out_path: Path, timeout: int = 30) -> tuple[str, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "figure1-replication-miner/0.1 (+local research provenance)",
            "Accept": "application/pdf,text/html,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = str(getattr(response, "status", ""))
        content_type = response.headers.get("Content-Type", "")
        body = response.read()
    out_path.write_bytes(body)
    return status, content_type, body


def existing_rows() -> list[dict[str, str]]:
    if not OUT_TSV.exists():
        return []
    with OUT_TSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    rows: list[dict[str, str]] = [] if args.replace else existing_rows()
    seen = {(row.get("source_html_path", ""), row.get("pdf_url", "")) for row in rows}

    html_paths = sorted(RAW_ROOT.glob("api_candidate_*/*.html"))
    for html_path in html_paths:
        candidate_id = html_path.parent.name
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        for raw_url in sorted({clean_url(match.group(0)) for match in PDF_RE.finditer(text)}):
            key = (str(html_path.relative_to(ROOT)), raw_url)
            if key in seen:
                continue
            seen.add(key)
            out_path = html_path.parent / safe_name(raw_url)
            row = {
                "candidate_id": candidate_id,
                "source_html_path": key[0],
                "pdf_url": raw_url,
                "http_status": "",
                "content_type": "",
                "bytes": "",
                "sha256": "",
                "local_path": "",
                "access_state": "",
                "error_or_note": "",
            }
            try:
                status, content_type, body = download(raw_url, out_path)
                digest = hashlib.sha256(body).hexdigest()
                row.update(
                    {
                        "http_status": status,
                        "content_type": content_type,
                        "bytes": str(len(body)),
                        "sha256": digest,
                        "local_path": str(out_path.relative_to(ROOT)),
                        "access_state": (
                            "mirrored_pdf"
                            if body[:5] == b"%PDF-" or "pdf" in content_type.lower()
                            else "mirrored_non_pdf"
                        ),
                    }
                )
            except urllib.error.HTTPError as exc:
                row.update(
                    {
                        "http_status": str(exc.code),
                        "content_type": exc.headers.get("Content-Type", ""),
                        "access_state": "blocked_or_not_found",
                        "error_or_note": str(exc),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                row.update({"access_state": "download_error", "error_or_note": repr(exc)})
            rows.append(row)
            if args.sleep:
                time.sleep(args.sleep)

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_TSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
