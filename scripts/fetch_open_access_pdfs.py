#!/usr/bin/env python3
"""Fetch legally accessible PDFs for the AquaCrop KB.

This script intentionally uses official/open routes only:
- direct PDF URLs already present in the manifest,
- Unpaywall OA PDF locations,
- Crossref PDF links.

It does not use shadow-library mirrors. Items that cannot be obtained are
left visible as NEEDS_USER in references/pdf_status.csv and in
references/MANUAL_PDF_REQUEST_QUEUE.md.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
STATUS_CSV = REFERENCES / "pdf_status.csv"
QUEUE_MD = REFERENCES / "MANUAL_PDF_REQUEST_QUEUE.md"
ATTEMPTS_LOG = REFERENCES / "pdf_fetch_attempts.jsonl"
EMAIL = "open-access-fetch@example.com"
UA = "Mozilla/5.0 (compatible; MAS-KB-OA-Fetch/1.0)"


@dataclass
class Candidate:
    url: str
    source: str


def request_json(url: str, timeout: int = 30) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def request_bytes(url: str, timeout: int = 60) -> tuple[bytes | None, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/pdf,text/html;q=0.8,*/*;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read(), response.headers.get("content-type", "")
    except Exception:
        return None, ""


def is_pdf(data: bytes | None, content_type: str) -> bool:
    if not data:
        return False
    head = data[:1024].lstrip()
    return head.startswith(b"%PDF") or ("application/pdf" in content_type.lower() and b"%PDF" in data[:4096])


def safe_url(url: str) -> str:
    return url.replace(" ", "%20")


def candidate_urls(row: dict[str, str]) -> Iterable[Candidate]:
    doi = row.get("doi", "").strip()
    url = row.get("url", "").strip()

    if url.lower().endswith(".pdf"):
        yield Candidate(safe_url(url), "manifest_direct_pdf")

    if doi:
        unpaywall_url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={EMAIL}"
        data = request_json(unpaywall_url)
        if data:
            best = data.get("best_oa_location") or {}
            if best.get("url_for_pdf"):
                yield Candidate(safe_url(best["url_for_pdf"]), "unpaywall_best_oa_pdf")
            for loc in data.get("oa_locations") or []:
                if loc.get("url_for_pdf"):
                    yield Candidate(safe_url(loc["url_for_pdf"]), "unpaywall_oa_pdf")

        crossref_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi.lower())}"
        cr = request_json(crossref_url)
        if cr and cr.get("message"):
            for link in cr["message"].get("link", []) or []:
                link_url = link.get("URL", "")
                content_type = link.get("content-type", "")
                if link_url and ("pdf" in content_type.lower() or link_url.lower().endswith(".pdf")):
                    yield Candidate(safe_url(link_url), "crossref_pdf_link")


def unique_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in candidates:
        if not c.url or c.url in seen:
            continue
        seen.add(c.url)
        out.append(c)
    return out


def log_attempt(record: dict) -> None:
    with ATTEMPTS_LOG.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_manual_queue(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Manual PDF Request Queue",
        "",
        "Rows with `NEEDS_USER` could not be obtained through official/OA routes by the automated fetcher.",
        "Drop supplied PDFs into `references/` using the target filename, then change status to `USER_SUPPLIED`.",
        "",
        "| status | citation | year | DOI/URL | target filename | notes |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        if row["status"] not in {"NEEDS_USER", "PENDING_PDF"}:
            continue
        doi_url = f"https://doi.org/{row['doi']}" if row.get("doi") else row.get("url", "")
        lines.append(
            f"| {row['status']} | {row['citation']} | {row['year']} | {doi_url} | "
            f"`{row['target_filename']}` | {row['notes']} |"
        )
    QUEUE_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    REFERENCES.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(STATUS_CSV.open()))
    changed = False
    success = 0
    failed = 0
    skipped = 0

    for row in rows:
        target = REFERENCES / row["target_filename"]
        if target.exists() and target.stat().st_size > 0:
            row["status"] = row.get("status") or "FOUND_OFFICIAL_PDF"
            row["notes"] = f"Existing file present: references/{target.name}"
            skipped += 1
            continue

        candidates = unique_candidates(candidate_urls(row))
        if not candidates:
            row["status"] = "NEEDS_USER"
            row["notes"] = "No official/OA PDF candidate found automatically; request from user/library."
            failed += 1
            changed = True
            log_attempt({"citation": row["citation"], "status": "no_candidates"})
            continue

        fetched = False
        for candidate in candidates:
            data, content_type = request_bytes(candidate.url)
            ok = is_pdf(data, content_type)
            log_attempt(
                {
                    "citation": row["citation"],
                    "doi": row.get("doi"),
                    "candidate": candidate.url,
                    "source": candidate.source,
                    "content_type": content_type,
                    "ok_pdf": ok,
                }
            )
            if ok and data:
                target.write_bytes(data)
                row["status"] = "FOUND_OFFICIAL_PDF"
                row["notes"] = f"Fetched via {candidate.source}: {candidate.url}"
                success += 1
                changed = True
                fetched = True
                break
            time.sleep(0.5)

        if not fetched:
            row["status"] = "NEEDS_USER"
            row["notes"] = "Official/OA candidates tried but no valid PDF downloaded; request from user/library."
            failed += 1
            changed = True

    if changed:
        with STATUS_CSV.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        write_manual_queue(rows)

    print(json.dumps({"success": success, "failed": failed, "skipped": skipped}, ensure_ascii=False))
    return 0 if success or skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())

