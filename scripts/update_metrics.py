#!/usr/bin/env python3
"""Update CV metrics from BibTeX files and Google Scholar (optional)."""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PUB_DIR = ROOT / "publications"

USER_ID = os.getenv("CV_SCHOLAR_USER", "lnh9kdIAAAAJ")
REFRESH = os.getenv("CV_SCHOLAR_REFRESH", "").lower() in {"1", "true", "yes"}
DISABLE = os.getenv("CV_SCHOLAR_DISABLE", "").lower() in {"1", "true", "yes"}
TTL_HOURS = int(os.getenv("CV_SCHOLAR_TTL_HOURS", "168"))  # default 7 days
TIMEOUT_SECONDS = int(os.getenv("CV_SCHOLAR_TIMEOUT_SECONDS", "20"))

ENTRY_START_RE = re.compile(r"^\s*@", re.IGNORECASE)
ENTRY_TYPE_RE = re.compile(r"^\s*@(?P<type>\w+)", re.IGNORECASE)
YEAR_RE = re.compile(r"year\s*=\s*[{\"]\s*(\d{4})", re.IGNORECASE)


def parse_bib(path: Path) -> Tuple[int, Counter, Counter]:
    if not path.exists():
        return 0, Counter(), Counter()

    text = path.read_text(encoding="utf-8", errors="replace")
    entries = []
    current = []

    for line in text.splitlines():
        if ENTRY_START_RE.match(line):
            if current:
                entries.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)

    if current:
        entries.append("\n".join(current))

    count = 0
    years = Counter()
    types = Counter()

    for entry in entries:
        match = ENTRY_TYPE_RE.match(entry)
        if not match:
            continue
        entry_type = match.group("type").lower()
        if entry_type in {"comment", "preamble", "string"}:
            continue

        count += 1
        types[entry_type] += 1

        year_match = YEAR_RE.search(entry)
        if year_match:
            years[year_match.group(1)] += 1

    return count, years, types


def load_cache(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def should_refresh(cache: Optional[Dict[str, Any]]) -> bool:
    if DISABLE:
        return False
    if REFRESH:
        return True
    if cache is None:
        return True

    updated_at = cache.get("updated_at")
    if not updated_at:
        return True

    updated_dt = parse_iso(updated_at)
    if not updated_dt:
        return True

    age_hours = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 3600.0
    return age_hours > TTL_HOURS


def fetch_scholar(user_id: str) -> Dict[str, Any]:
    try:
        from scholarly import scholarly  # type: ignore
    except Exception as exc:  # ImportError or runtime issues
        raise RuntimeError("python package 'scholarly' is not available") from exc

    author = scholarly.search_author_id(user_id)
    author = scholarly.fill(author, sections=["basics", "indices", "counts"])

    return {
        "name": author.get("name"),
        "citedby": author.get("citedby"),
        "citedby5y": author.get("citedby5y"),
        "h_index": author.get("hindex"),
        "h_index_5y": author.get("hindex5y"),
        "i10_index": author.get("i10index"),
        "i10_index_5y": author.get("i10index5y"),
    }


def fmt_num(value: Optional[int]) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except Exception:
        return "N/A"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = DATA_DIR / "gs_cache.json"

    pub_count, pub_years, pub_types = parse_bib(PUB_DIR / "published.bib")
    sub_count, sub_years, sub_types = parse_bib(PUB_DIR / "submitted.bib")

    total_years = pub_years + sub_years
    total_types = pub_types + sub_types

    scholar_data: Optional[Dict[str, Any]] = None
    scholar_updated_at: Optional[str] = None

    cache = load_cache(cache_path)
    if cache and isinstance(cache, dict):
        scholar_data = cache.get("data")
        scholar_updated_at = cache.get("updated_at")

    if should_refresh(cache):
        result_holder: list = [None]
        error_holder: list = [None]

        def _fetch_target() -> None:
            try:
                result_holder[0] = fetch_scholar(USER_ID)
            except Exception as exc:
                error_holder[0] = exc

        thread = threading.Thread(target=_fetch_target, daemon=True)
        thread.start()
        thread.join(timeout=TIMEOUT_SECONDS)

        if thread.is_alive():
            print(
                f"Warning: Scholar refresh timed out after {TIMEOUT_SECONDS}s.",
                file=sys.stderr,
            )
        elif error_holder[0] is not None:
            print(f"Warning: Scholar refresh failed: {error_holder[0]}", file=sys.stderr)
        else:
            scholar_data = result_holder[0]
            scholar_updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            cache_path.write_text(
                json.dumps({"updated_at": scholar_updated_at, "data": scholar_data}, indent=2),
                encoding="utf-8",
            )
            print("Updated Google Scholar cache.")

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "publications": {
            "published": pub_count,
            "submitted": sub_count,
            "total": pub_count + sub_count,
            "by_year": dict(sorted(total_years.items(), reverse=True)),
            "by_type": dict(sorted(total_types.items())),
        },
        "scholar": scholar_data or {},
        "scholar_updated_at": scholar_updated_at,
        "scholar_user": USER_ID,
        "scholar_source": "google_scholar",
    }

    (DATA_DIR / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    # Render a small Markdown snippet for Quarto inclusion
    total = stats["publications"]["total"]
    published = stats["publications"]["published"]
    submitted = stats["publications"]["submitted"]

    citations = fmt_num(stats["scholar"].get("citedby") if stats["scholar"] else None)
    h_index = fmt_num(stats["scholar"].get("h_index") if stats["scholar"] else None)
    i10_index = fmt_num(stats["scholar"].get("i10_index") if stats["scholar"] else None)
    updated = stats.get("scholar_updated_at") or "N/A"

    md_lines = [
        f"- Publications: {total} (published: {published}, submitted: {submitted})",
        f"- Citations (Google Scholar): {citations}",
        f"- h-index (Google Scholar): {h_index}",
        f"- i10-index (Google Scholar): {i10_index}",
        f"- Scholar stats updated: {updated}",
    ]

    (DATA_DIR / "stats.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    tex_lines = [
        r"\begin{itemize}",
        rf"\item Publications: {total} (published: {published}, submitted: {submitted})",
        rf"\item Citations (Google Scholar): {citations}",
        rf"\item h-index (Google Scholar): {h_index}",
        rf"\item i10-index (Google Scholar): {i10_index}",
        rf"\item Scholar stats updated: {updated}",
        r"\end{itemize}",
    ]

    (DATA_DIR / "stats.tex").write_text("\n".join(tex_lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
