# Frontend Dragon — build targets. See README.md.
PY ?= python3

.PHONY: setup fonts pdf site all lint fixture-pdf fixture-site preview clean

setup:            ## install Python deps (pip) — WeasyPrint also needs Pango/Cairo (see README)
	$(PY) -m pip install -r production/requirements.txt

fonts:            ## download the three typefaces into production/fonts/lib
	./production/fetch-fonts.sh

pdf:              ## build out/Frontend-Dragon.pdf
	$(PY) production/build.py pdf

site:             ## build out/site/ (static HTML)
	$(PY) production/build.py site

all: pdf site

lint:             ## check fenced blocks for over-wide lines
	$(PY) production/build.py lint

fixture-pdf:      ## design-session build from the small fixture manuscript
	$(PY) production/build.py pdf --fixture

fixture-site:
	$(PY) production/build.py site --fixture

preview:          ## serve out/site on http://localhost:8000
	cd out/site && $(PY) -m http.server 8000

contact-sheet:    ## render the PDF as thumbnails for visual QC (needs poppler)
	rm -rf out/pg && mkdir -p out/pg && pdftoppm -r 45 -png out/Frontend-Dragon.pdf out/pg/p

clean:
	rm -rf out
