#!/bin/bash
# Regenerate the ScummGEN game folder and compile it to tentacle.000/.001
set -e
cd "$(dirname "$0")"
python3 -W ignore gen.py build/game >/dev/null
mkdir -p build/out && cd build/out
${SCUMMGEN:-$HOME/src/scummgen/src/scummgen} ../game/ | tail -1
grep -nE 'LOG_ERROR|ERROR|Error|error|Could not|Couldn' log.txt | grep -v 'VAR_ERROR' | head -20 || true
