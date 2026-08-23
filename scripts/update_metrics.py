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
GRANTS_DIR = ROOT / "sections" / "grants"
STUDENTS_PATH = ROOT / "sections" / "students.md"

USER_ID = os.getenv("CV_SCHOLAR_USER", "lnh9kdIAAAAJ")
REFRESH = os.getenv("CV_SCHOLAR_REFRESH", "").lower() in {"1", "true", "yes"}
DISABLE = os.getenv("CV_SCHOLAR_DISABLE", "").lower() in {"1", "true", "yes"}
TTL_HOURS = int(os.getenv("CV_SCHOLAR_TTL_HOURS", "48"))  # default 7 days
TIMEOUT_SECONDS = int(os.getenv("CV_SCHOLAR_TIMEOUT_SECONDS", "20"))

ENTRY_START_RE = re.compile(r"^\s*@", re.IGNORECASE)
ENTRY_TYPE_RE = re.compile(r"^\s*@(?P<type>\w+)", re.IGNORECASE)
YEAR_RE = re.compile(r"year\s*=\s*[{\"]\s*(\d{4})", re.IGNORECASE)
GRANT_USD_RE = re.compile(r"\\\$([0-9,]+)")
# Credit share written next to the role, e.g. "Role: Co-PI (50\%)". Anchored to
# "Role:" so percentages inside grant titles are not picked up by mistake.
GRANT_SHARE_RE = re.compile(r"Role:[^.(]*\((\d+)\s*\\?%\)")


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


def parse_grants(path: Path) -> Tuple[int, int, int]:
    """Return (count, total_usd, share_usd) for USD grant entries in a grants .md file.

    total_usd sums the full award amounts; share_usd sums each award weighted by
    the credit share written next to the role, e.g. "Role: Co-PI (50\\%)".
    Entries with no percentage are counted at 100%.
    """
    if not path.exists():
        return 0, 0, 0
    count = 0
    total = 0
    share = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip().startswith("- "):
            continue
        m = GRANT_USD_RE.search(line)
        if m:
            try:
                amount = int(m.group(1).replace(",", ""))
            except ValueError:
                continue
            total += amount
            count += 1
            pct_match = GRANT_SHARE_RE.search(line)
            pct = int(pct_match.group(1)) if pct_match else 100
            share += round(amount * pct / 100)
    return count, total, share


def parse_students(path: Path) -> Dict[str, int]:
    """Count students by group from sections/students.md bullet lists."""
    if not path.exists():
        return {}
    odu_grad_cur = odu_grad_fmr = 0
    odu_ug_cur = odu_ug_fmr = 0
    other = 0
    in_odu = is_current = is_grad = False
    heading = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            heading = stripped[4:]
            in_odu = "Old Dominion University" in heading
            is_current = "(Current)" in heading
            is_grad = "Graduate" in heading
        elif stripped.startswith("- ") and heading:
            if in_odu:
                if is_grad and is_current:
                    odu_grad_cur += 1
                elif is_grad:
                    odu_grad_fmr += 1
                elif is_current:
                    odu_ug_cur += 1
                else:
                    odu_ug_fmr += 1
            else:
                other += 1
    return {
        "grad_current": odu_grad_cur,
        "undergrad_current": odu_ug_cur,
        "grad_former": odu_grad_fmr,
        "undergrad_former": odu_ug_fmr,
        "other": other,
        "odu_current": odu_grad_cur + odu_ug_cur,
        "odu_total": odu_grad_cur + odu_ug_cur + odu_grad_fmr + odu_ug_fmr,
        "total": odu_grad_cur + odu_ug_cur + odu_grad_fmr + odu_ug_fmr + other,
    }


def fmt_dollars(total: int) -> str:
    r"""Format a dollar amount for LaTeX, e.g. 1165920 -> r'\$1.2M'."""
    if total >= 1_000_000:
        return rf"\${total / 1_000_000:.1f}M"
    if total >= 1_000:
        return rf"\${total / 1_000:.0f}K"
    return rf"\${total:,}"


def write_macros(
    path: Path,
    stats: Dict[str, Any],
    students: Dict[str, int],
    grant_count: int,
    grant_total: int,
    grant_share: int,
) -> None:
    """Write data/macros.tex with \\newcommand definitions for CV metrics."""

    def cmd(name: str, value: Any) -> str:
        return rf"\newcommand{{\{name}}}{{{value}}}"

    scholar = stats.get("scholar") or {}
    pubs = stats.get("publications") or {}
    if not scholar.get("citedby"):
        print(
            "Warning: no Google Scholar data — \\CVcitations/\\CVhindex will render "
            "as 'N/A'. data/gs_cache.json is tracked in git so CI has this data; "
            "refresh with CV_SCHOLAR_REFRESH=1.",
            file=sys.stderr,
        )
    lines = [
        "% Auto-generated by scripts/update_metrics.py — do not edit by hand",
        "% Include in LaTeX via: \\input{data/macros}",
        "",
        "% Google Scholar metrics",
        cmd("CVcitations", scholar.get("citedby", "N/A")),
        cmd("CVhindex", scholar.get("h_index", "N/A")),
        cmd("CVipublications", scholar.get("i10_index", "N/A")),
        "",
        "% Publication counts",
        cmd("CVpublications", pubs.get("published", "N/A")),
        "",
        "% Grant totals (USD-denominated entries from sections/grants/awarded.md)",
        cmd("CVgrantsawarded", grant_count),
        cmd("CVgranttotal", fmt_dollars(grant_total)),
        cmd("CVgrantshare", fmt_dollars(grant_share)),
        "",
        "% Student supervision counts (Old Dominion University)",
        cmd("CVgradcurrent", students.get("grad_current", 0)),
        cmd("CVundergradcurrent", students.get("undergrad_current", 0)),
        cmd("CVstudentscurrent", students.get("odu_current", 0)),
        cmd("CVstudentsall", students.get("total", 0)),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    author = scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])

    publications = []
    for pub in author.get("publications", []):
        bib = pub.get("bib", {})
        title = bib.get("title")
        if not title:
            continue
        publications.append(
            {
                "title": title,
                "year": bib.get("pub_year"),
                "citations": pub.get("num_citations", 0),
            }
        )

    return {
        "name": author.get("name"),
        "citedby": author.get("citedby"),
        "citedby5y": author.get("citedby5y"),
        "h_index": author.get("hindex"),
        "h_index_5y": author.get("hindex5y"),
        "i10_index": author.get("i10index"),
        "i10_index_5y": author.get("i10index5y"),
        "publications": publications,
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
    grant_count, grant_total, grant_share = parse_grants(GRANTS_DIR / "awarded.md")
    student_data = parse_students(STUDENTS_PATH)

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

    write_macros(
        DATA_DIR / "macros.tex", stats, student_data, grant_count, grant_total, grant_share
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
