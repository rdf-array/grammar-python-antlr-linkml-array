#!/usr/bin/env bash
# Regenerate pyshexc/parser/ from grammar/ShExDoc.g4.
#
# RDF-: the ShEx- grammar (the spec's ShExDoc.g4 plus the Collection shape expression
# `((shapeExpr))[min, max]`) lives in this repository; upstream copied it from a sibling
# checkout of shexSpec/grammar. The generated parser must match the Python runtime this
# package pins (antlr4-python3-runtime ~= 4.9.3), so run the ANTLR 4.9.3 tool:
#
#   ANTLR_JAR=/path/to/antlr4-4.9.3-complete.jar scripts/genpython.sh
#
# (https://www.antlr.org/download/antlr-4.9.3-complete.jar)
set -euo pipefail
cd "$(dirname "$0")/.."
: "${ANTLR_JAR:?set ANTLR_JAR to the path of antlr4-4.9.3-complete.jar}"
java -jar "$ANTLR_JAR" -Dlanguage=Python3 -package parser -o pyshexc/parser -Xexact-output-dir \
     -no-listener -visitor grammar/ShExDoc.g4
