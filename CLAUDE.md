# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Academic CV workspace using Quarto + LaTeX with the CurVe document class. CV content lives in Markdown; a Python script converts it to LaTeX; Quarto renders the final PDFs.

## Build Commands

Render all CV variants:

```bash
quarto render
```

Render a single variant:

```bash
quarto render cv-full.qmd   # Full CV
quarto render cv-odu.qmd    # ODU-specific full CV
quarto render cv-3p.qmd     # 3-page version
quarto render cv-2p.qmd     # 2-page version
quarto render cv-1p.qmd     # 1-page version
quarto render cv-web.qmd    # Web version
```

Legacy LaTeX build (via Makefile): `make full`, `make 3p`, etc.

Output goes to `_build/`.

## Build Pipeline

Configured in `_quarto.yml` pre-render/post-render hooks:

1. `scripts/prepare_texlive.py` — Ensures TeX Live packages are available
2. `scripts/build_sections.py` — Parses `sections/*.md` → generates `sections/tex/*.tex`
3. `scripts/update_metrics.py` — Fetches Google Scholar stats → `data/stats.*`
4. Quarto renders `.qmd` files to PDF using the CurVe LaTeX class
5. `scripts/clean_artifacts.py` — Removes LaTeX build artifacts

**Do not edit `sections/tex/` files by hand** — they are generated from Markdown sources.

## Project Structure

- `cv-*.qmd` — Entry points for each CV variant (YAML front matter + LaTeX body referencing generated sections)
- `sections/*.md` — **Primary content to edit.** Markdown with YAML front matter specifying section type
- `sections/tex/` — Auto-generated LaTeX (do not edit)
- `publications/published.bib`, `publications/submitted.bib` — BibTeX bibliography files
- `preamble.tex` — Shared LaTeX preamble (biblatex config, fonts, author name bolding)
- `settings.sty` — LaTeX styling, colors, CurVe customization
- `data/` — Generated stats files (`stats.json`, `stats.tex`, `stats.md`, `gs_cache.json`)
- `scripts/` — Build helpers (Python)

## Markdown Section Format

Each `sections/*.md` file has YAML front matter and uses `## Headings` for sub-groups and bullet lists for entries.

Section types (set via `type:` in front matter):
- `dated` — Entries with `Date | Description` format (date can be at start or end, controlled by `date_position`)
- `enumerated` — Numbered entries (descending)
- `grants` — Entries with `Date | Amount | Description`

Inline formatting: `*italic*`, `**bold**`. Use LaTeX escapes for special chars (`\%`, `\&`, `\$`).

## Bibliography

Publications managed via BibTeX in `publications/`. Author name bolding is configured in `preamble.tex` via `\mynames{}`. The `mynames` field in `.qmd` YAML front matter can also specify variants.

## Python Environment

```bash
uv venv .venv
uv pip install scholarly
```

The `.venv` is used by pre-render scripts in `_quarto.yml`.
