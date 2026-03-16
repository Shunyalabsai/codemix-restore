#!/usr/bin/env bash
# Install codemix_restore-shunyalabs with neural (IndicXlit) support.
#
# This script handles the dependency issues between fairseq, omegaconf, and
# modern pip (>= 24.1). fairseq requires omegaconf<2.1, but all 2.0.x versions
# have invalid metadata. We install omegaconf>=2.1 (valid metadata) and our
# compatibility patches handle runtime differences.
#
# Usage:
#   bash install_neural.sh
#   # or inside a venv/conda env:
#   source .venv/bin/activate && bash install_neural.sh

set -euo pipefail

echo "=== Step 1: Install codemix_restore with neural deps ==="
pip install "codemix_restore-shunyalabs[neural]"

echo "=== Step 2: Install fairseq + ai4bharat (skip dep resolution) ==="
pip install fairseq==0.12.2 --no-deps
pip install ai4bharat-transliteration --no-deps

echo ""
echo "=== Done! Verify with: ==="
echo '  python -c "from codemix_restore import ScriptRestorer; r = ScriptRestorer(); print(r.restore(\"प्लीज मीटिंग शेड्यूल करो\", lang=\"hi\"))"'
