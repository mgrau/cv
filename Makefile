# Makefile for CV compilation
# Usage: make all, make full, make web, make 3p, make 2p, make 1p, make clean

LATEX = latexmk -pdf -interaction=nonstopmode
SECTIONS_MD = $(wildcard sections/*.md) $(wildcard sections/grants/*.md)
SECTIONS_SCRIPT = scripts/build_sections.py

.PHONY: all full web 3p 2p 1p clean

all: full web 3p 2p 1p

full: cv-full.pdf

web: cv-web.pdf

3p: cv-3p.pdf

2p: cv-2p.pdf

1p: cv-1p.pdf

cv-full.pdf: cv-full.tex preamble.tex $(SECTIONS_MD) $(SECTIONS_SCRIPT) sections/tex/*.tex sections/tex/grants/*.tex publications/*.bib
	python3 $(SECTIONS_SCRIPT)
	$(LATEX) cv-full.tex

cv-web.pdf: cv-web.tex preamble.tex $(SECTIONS_MD) $(SECTIONS_SCRIPT) sections/tex/*.tex publications/*.bib
	python3 $(SECTIONS_SCRIPT)
	$(LATEX) cv-web.tex

cv-3p.pdf: cv-3p.tex preamble.tex $(SECTIONS_MD) $(SECTIONS_SCRIPT) sections/tex/*.tex publications/*.bib
	python3 $(SECTIONS_SCRIPT)
	$(LATEX) cv-3p.tex

cv-2p.pdf: cv-2p.tex preamble.tex $(SECTIONS_MD) $(SECTIONS_SCRIPT) sections/tex/*.tex publications/*.bib
	python3 $(SECTIONS_SCRIPT)
	$(LATEX) cv-2p.tex

cv-1p.pdf: cv-1p.tex preamble.tex $(SECTIONS_MD) $(SECTIONS_SCRIPT) sections/tex/*.tex publications/*.bib
	python3 $(SECTIONS_SCRIPT)
	$(LATEX) cv-1p.tex

clean:
	latexmk -C
	rm -f *.bbl *.run.xml *.bcf *.bcf-SAVE-ERROR *.bbl-SAVE-ERROR
