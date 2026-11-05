#!/usr/bin/env bash
# Build the Linux packages: one PyInstaller bundle, then deb and rpm from it.
#
# This runs inside the manylinux container in CI (the bundle must be built against an old glibc
# so it starts on RHEL/Alma/Rocky 9, Debian 12 and Ubuntu 22.04 alike) and can run on any host
# that has nfpm and a working PyInstaller, for a local smoke test.
#
# Usage: packaging/linux/build_linux_packages.sh [--skip-bundle]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUTPUT_DIR="$ROOT_DIR/dist/installer"
BUNDLE_DIR="$ROOT_DIR/dist/linux/FlatCAM-Plus"
SKIP_BUNDLE=0

for argument in "$@"; do
    case "$argument" in
        --skip-bundle) SKIP_BUNDLE=1 ;;
        *) echo "[ERROR] unknown argument: $argument" >&2; exit 2 ;;
    esac
done

if [ -z "${PYTHON_BIN:-}" ]; then
    if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
    else
        PYTHON_BIN="$(command -v python3)"
    fi
fi

if ! command -v nfpm >/dev/null 2>&1; then
    echo "[ERROR] nfpm is not on PATH; it produces both packages from packaging/linux/nfpm.yaml" >&2
    exit 1
fi

VERSION="$("$PYTHON_BIN" - <<'PY'
import tomllib
from pathlib import Path
print(tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
PY
)"
echo "[INFO] Version: $VERSION"

if [ "$SKIP_BUNDLE" -eq 0 ]; then
    echo "[INFO] Building the PyInstaller bundle"
    "$ROOT_DIR/packaging/linux/build_linux_portable.sh"
else
    echo "[INFO] Reusing the existing bundle in dist/linux"
fi

if [ ! -d "$BUNDLE_DIR" ]; then
    echo "[ERROR] no bundle at $BUNDLE_DIR" >&2
    exit 1
fi

echo "[INFO] Checking the glibc floor before packaging"
"$PYTHON_BIN" "$ROOT_DIR/packaging/linux/check_glibc_floor.py" "$BUNDLE_DIR" "${GLIBC_FLOOR:-2.28}"

mkdir -p "$OUTPUT_DIR"
for packager in deb rpm; do
    echo "[INFO] Packaging $packager"
    VERSION="$VERSION" nfpm package \
        --config "$ROOT_DIR/packaging/linux/nfpm.yaml" \
        --packager "$packager" \
        --target "$OUTPUT_DIR/"
done

echo "[INFO] Packages written to $OUTPUT_DIR:"
ls -1 "$OUTPUT_DIR"/flatcam-plus_*."${VERSION}"-* 2>/dev/null || ls -1 "$OUTPUT_DIR"
