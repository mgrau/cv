# CV Workflow

This project keeps CV content in simple Markdown files and renders them into LaTeX (for PDF) and HTML (for web) via a small build pipeline.

## Directory Layout

- `sections/` — Source content for CV sections (Markdown). This is the primary place to edit content.
- `generated/` — Generated LaTeX and Markdown, rebuilt on every render. Gitignored; do not edit by hand.
- `publications/` — BibTeX files for publications.
- `scripts/` — Build helpers and live-metrics updater.
- `cv-*.qmd` — Quarto entry points (PDF + HTML where relevant).

## How the Build Works

1. `scripts/build_sections.py` parses the Markdown in `sections/` and generates:
   - `generated/tex/*.tex` for LaTeX.
2. `scripts/update_metrics.py` (optional) fetches Google Scholar stats and parses BibTeX counts into `data/stats.*`.
3. Quarto renders QMD files to PDF/HTML using the generated LaTeX sections.
4. `scripts/clean_artifacts.py` removes LaTeX artifacts after rendering.

Quarto runs steps 1, 2, and 4 automatically via `_quarto.yml` (`pre-render` and `post-render`).

## Editing Content

Edit the Markdown in `sections/`.

### Dated Sections

```markdown
<!--
type: dated
-->

## Teaching

### Institution

- Fall 2025 | Course title
```

### Enumerated Sections (Descending)

```markdown
<!--
type: enumerated
date_position: end
-->

## Invited Conference Talks

- May 2017 | Talk title. Venue
```

### Grants (Number + Date + Amount)

```markdown
<!--
type: grants
-->

## Grants Awarded

- September 2024 -- December 2026 | \$472,000 | _Grant title_ (Agency). Role: Co-PI (50\%).
```

The `## Heading` is required — it is what the Quarto filter keys on to find the
section and map it to its generated `.tex` file. Escape LaTeX specials (`\$`, `\%`,
`\&`). Add `tex: <path>` to the metadata comment when the source filename differs
from the slugified heading (e.g. `teaching_condensed.md` → `## Teaching`).

## Quarto Builds

Quarto entry points:

- `cv.qmd` — Canonical CV entry point. The body is pure section includes; a format-specific filter turns that into the HTML template or PDF `curve`/`\makerubric` output.
- `cv-odu.qmd` — Full CV for ODU workflow (PDF).
- `cv-1p.qmd` — 1-page CV (PDF).
- `cv-2p.qmd` — 2-page CV (PDF).
- `cv-3p.qmd` — 3-page CV (PDF).
- `cv-full.qmd` — PDF-only wrapper using the same pure section-include body pattern.
- `cv-web.qmd` — HTML-only wrapper using the same pure section-include body pattern.

Render a single target:

```bash
quarto render cv.qmd --to pdf
quarto render cv.qmd --to html
```

Render all QMD files:

```bash
quarto render
```

## LaTeX Builds (Makefile)

Legacy LaTeX workflows are still supported:

```bash
make full
make web
make 3p
make 2p
make 1p
```

The Makefile runs `scripts/build_sections.py` first to keep LaTeX sections up to date.

## Live Metrics (Google Scholar)

`update_metrics.py` reads BibTeX counts and fetches Google Scholar stats using `scholarly`.

Environment variables:

- `CV_SCHOLAR_USER` (default: `lnh9kdIAAAAJ`)
- `CV_SCHOLAR_REFRESH` (`1/true/yes` forces refresh)
- `CV_SCHOLAR_TTL_HOURS` (cache TTL, default 168)
- `CV_SCHOLAR_TIMEOUT_SECONDS` (default 20)
- `CV_SCHOLAR_DISABLE` (`1/true/yes` to skip scholar fetch)

Cache location: `data/gs_cache.json`

## Python Dependencies (via uv)

Create the virtual environment:

```bash
uv venv .venv
```

Install required packages:

```bash
uv pip install scholarly
```

## Other Requirements

- Quarto (for `.qmd` rendering)
- TeX Live (for PDF builds) with `latexmk`

## Formatting Notes

- Markdown supports `*italic*` and `**bold**` inline formatting.
- Use `|` to separate date and text in dated sections.
- Section metadata lives in a top HTML comment:
  ```markdown
  <!--
  type: dated
  date_position: end
  -->
  ```
- For LaTeX-specific symbols in Markdown, keep the LaTeX escapes (e.g., `\%`, `\&`, `\$`).
