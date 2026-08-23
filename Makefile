# Makefile for CV compilation via Quarto
# Usage: make [target]
#
# Targets:
#   generate     Build generated/ (required before a first render)
#   all          Render all documents (both PDF and HTML)
#   pdf          Render all documents to PDF only
#   html         Render all documents to HTML only
#   cv           Render cv.qmd (both formats)
#   odu          Render cv-odu.qmd (both formats)
#   3p           Render cv-3p.qmd (both formats)
#   2p           Render cv-2p.qmd (both formats)
#   1p           Render cv-1p.qmd (both formats)
#   cv-pdf       Render cv.qmd to PDF
#   cv-html      Render cv.qmd to HTML
#   odu-pdf      Render cv-odu.qmd to PDF
#   odu-html     Render cv-odu.qmd to HTML
#   3p-pdf / 2p-pdf / 1p-pdf
#   3p-html / 2p-html / 1p-html
#   clean        Remove _build/

.PHONY: all generate pdf html cv odu 3p 2p 1p \
        cv-pdf cv-html odu-pdf odu-html \
        3p-pdf 3p-html 2p-pdf 2p-html 1p-pdf 1p-html \
        clean

PYTHON = .venv/bin/python

# Build generated/ before Quarto runs. Quarto resolves {{< include >}}
# directives while enumerating project files, which happens before its own
# pre-render hooks, so on a clean checkout the includes fail without this.
generate:
	$(PYTHON) scripts/build_sections.py
	$(PYTHON) scripts/update_metrics.py
	$(PYTHON) scripts/render_publications_web.py

all: generate
	quarto render

pdf:
	quarto render --to pdf

html:
	quarto render --to html

cv:
	quarto render cv.qmd

odu:
	quarto render cv-odu.qmd

3p:
	quarto render cv-3p.qmd

2p:
	quarto render cv-2p.qmd

1p:
	quarto render cv-1p.qmd

cv-pdf:
	quarto render cv.qmd --to pdf

cv-html:
	quarto render cv.qmd --to html

odu-pdf:
	quarto render cv-odu.qmd --to pdf

odu-html:
	quarto render cv-odu.qmd --to html

3p-pdf:
	quarto render cv-3p.qmd --to pdf

3p-html:
	quarto render cv-3p.qmd --to html

2p-pdf:
	quarto render cv-2p.qmd --to pdf

2p-html:
	quarto render cv-2p.qmd --to html

1p-pdf:
	quarto render cv-1p.qmd --to pdf

1p-html:
	quarto render cv-1p.qmd --to html

clean:
	rm -rf _build/
