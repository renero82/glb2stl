#!/usr/bin/env bash
# Local build of glb2stl.app on macOS (for testing before a release).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv-build
source .venv-build/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-gui.txt pyinstaller pillow
pyinstaller --noconfirm glb2stl.spec
echo
echo "Done: dist/glb2stl.app"
echo "Open it with:  open dist/glb2stl.app"
