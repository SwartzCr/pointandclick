# Build Hotel Paradiso: Sacra Pasta.
#   make AGS=~/ags     (AGS 3.6.1 sources, with Compiler/agscc built)

AGS ?= $(HOME)/ags
PY ?= python3

.PHONY: all assets clean

all: dist/sacrapasta.ags

dist/sacrapasta.ags: src/game.asc src/game.ash assets/manifest.json $(wildcard tools/*.py tools/agsbuild/*.py)
	$(PY) tools/build.py --agscc $(AGS)/Compiler/agscc --agsdefns $(AGS)/Editor/AGS.Editor/Resources/agsdefns.sh --out $@

assets:
	$(PY) tools/make_assets.py

clean:
	rm -rf build
