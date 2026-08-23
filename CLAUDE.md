# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Academic CV workspace using Quarto + LaTeX with the CurVe document class. CV content lives in Markdown; a Python script converts it to LaTeX; Quarto renders the final PDFs.

## Build Commands

Render all CV variants:

```bash
make            # generate + quarto render
```

On a clean checkout you must build `generated/` before Quarto runs:

```bash
make generate   # or: quarto render will fail on missing includes
```

Quarto resolves `{{< include >}}` directives while enumerating project input
files, which happens *before* its own pre-render hooks — so `generated/` has to
exist already. Once it does, plain `quarto render` works and the pre-render
hooks keep it up to date.

Render a single variant:

```bash
quarto render cv.qmd        # Full CV (HTML)
quarto render cv-odu.qmd    # ODU-specific full CV
quarto render cv-3p.qmd     # 3-page version
quarto render cv-2p.qmd     # 2-page version
quarto render cv-1p.qmd     # 1-page version
```

Output goes to `_build/`.

## Build Pipeline

Configured in `_quarto.yml` pre-render/post-render hooks:

1. `scripts/prepare_texlive.py` — Ensures TeX Live packages are available
2. `scripts/build_sections.py` — Parses `sections/*.md` → generates `generated/tex/*.tex`
3. `scripts/update_metrics.py` — Fetches Google Scholar stats, parses grants and students → `data/stats.*`, `data/macros.tex`
4. Quarto renders `.qmd` files to PDF using the CurVe LaTeX class
5. `scripts/clean_artifacts.py` — Removes LaTeX build artifacts

**Do not edit `generated/` files by hand** — the whole directory is rebuilt on every render and is gitignored.
Exception: `publications/publications.tex` is hand-written and tracked in git.

## Project Structure

- `cv-*.qmd` — Entry points for each CV variant (YAML front matter + LaTeX body referencing generated sections)
- `sections/*.md` — **Primary content to edit.** Markdown with YAML front matter specifying section type
- `generated/tex/`, `generated/md/` — Auto-generated LaTeX and Markdown (gitignored, do not edit)
- `publications/published.bib`, `publications/submitted.bib` — BibTeX bibliography files
- `preamble.tex` — Shared LaTeX preamble (biblatex config, fonts, author name bolding)
- `settings.sty` — LaTeX styling, colors, CurVe customization
- `data/` — `stats.*` and `macros.tex` are generated and gitignored.
  `gs_cache.json` is generated but **tracked in git**: CI runs with `CV_SCHOLAR_DISABLE=1`,
  so the committed cache is its only source of citation counts. Refresh with
  `CV_SCHOLAR_REFRESH=1 .venv/bin/python scripts/update_metrics.py` and commit the result.
- `scripts/` — Build helpers (Python)

## Markdown Section Format

Each `sections/*.md` file has YAML front matter and uses `## Headings` for sub-groups and bullet lists for entries.

Section types (set via `type:` in front matter):
- `dated` — Entries with `Date | Description` format (date can be at start or end, controlled by `date_position`)
- `enumerated` — Numbered entries (descending)
- `grants` — Entries with `Date | Amount | Description`

Grant entries put the **full award total** in the amount column and the credit
share as a percentage next to the role, e.g. `Role: Co-PI (50\%)`. Entries with
no percentage are treated as 100% when computing `\CVgrantshare`.

Inline formatting: `*italic*`, `**bold**`. Use LaTeX escapes for special chars (`\%`, `\&`, `\$`).

## Publication Selections

`publications/selections.json` defines named Selected Publications lists. Each one
generates `generated/md/publications_selected_<name>.md`; a `.qmd` chooses a list by
including that file.

Methods: `keys` (hand-picked bib keys), `impact` (top N by Google Scholar citations),
`recent` (newest N), `weighted` (citations discounted by age, `half_life_years`).
`exclude` drops keys from the algorithmic methods. The `impact` and `weighted` methods
require `data/gs_cache.json` and fail loudly without it.

## Bibliography

Publications managed via BibTeX in `publications/`. Author name bolding is configured in `preamble.tex` via `\mynames{}`. The `mynames` field in `.qmd` YAML front matter can also specify variants.

## CV Metrics Macros

`scripts/update_metrics.py` generates `data/macros.tex` (gitignored, rebuilt on every render). These `\newcommand` macros are available in all `.qmd` files via `\input{data/macros}` in `preamble.tex`.

| Macro | Source | Description |
|---|---|---|
| `\CVcitations` | Google Scholar | Total citation count |
| `\CVhindex` | Google Scholar | h-index |
| `\CVipublications` | Google Scholar | i10-index |
| `\CVpublications` | `publications/published.bib` | Peer-reviewed article count |
| `\CVgrantsawarded` | `sections/grants/awarded.md` | Count of USD-denominated grants |
| `\CVgranttotal` | `sections/grants/awarded.md` | Total project funding — full award amounts (e.g. `\$2.6M`) |
| `\CVgrantshare` | `sections/grants/awarded.md` | Attributed share — awards weighted by credit share (e.g. `\$2.3M`) |
| `\CVgradcurrent` | `sections/students.md` | Current ODU grad students |
| `\CVundergradcurrent` | `sections/students.md` | Current ODU undergrad students |
| `\CVstudentscurrent` | `sections/students.md` | Total current ODU students |
| `\CVstudentsall` | `sections/students.md` | All students ever supervised |

To add a new metric: extend `write_macros()` in `update_metrics.py` and add a row to this table.

## Python Environment

```bash
uv venv .venv
uv pip install scholarly
```

The `.venv` is used by pre-render scripts in `_quarto.yml`.
