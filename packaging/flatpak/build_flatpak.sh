#!/usr/bin/env bash
# Build the Flatpak bundle published next to the deb and the rpm.
#
# Runs on a host with flatpak-builder and the org.kde.Platform runtime installed, and in CI. The
# payload is the same PyInstaller tree the other packages use, so this script never builds one:
# pass --skip-bundle only when dist/linux/FlatCAM-Plus already exists.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MANIFEST="$ROOT_DIR/packaging/flatpak/io.github.thebestgoodguy.FlatCAMPlus.yml"
APP_ID="io.github.thebestgoodguy.FlatCAMPlus"
OUTPUT_DIR="$ROOT_DIR/dist/installer"
BUNDLE_DIR="$ROOT_DIR/dist/linux/FlatCAM-Plus"
BUILD_DIR="$ROOT_DIR/dist/flatpak/build"
REPO_DIR="$ROOT_DIR/dist/flatpak/repo"

for argument in "$@"; do
    case "$argument" in
        --skip-bundle) ;;
        *) echo "[ERROR] unknown argument: $argument" >&2; exit 2 ;;
    esac
done

if ! command -v flatpak-builder >/dev/null 2>&1; then
    echo "[ERROR] flatpak-builder is not on PATH" >&2
    exit 1
fi

if [ ! -d "$BUNDLE_DIR" ]; then
    echo "[ERROR] no bundle at $BUNDLE_DIR; build it first or drop --skip-bundle" >&2
    exit 1
fi

VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path
print(tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
PY
)"
echo "[INFO] Version: $VERSION"

mkdir -p "$OUTPUT_DIR" "$(dirname "$BUILD_DIR")"
rm -rf "$BUILD_DIR" "$REPO_DIR"

# rofiles-fuse needs /dev/fuse, which a build container usually does not expose; without it
# flatpak-builder fails with "fuse: device not found" and an uninitialized rofiles directory.
builder_args=(--force-clean --repo="$REPO_DIR")
if [ ! -e /dev/fuse ]; then
    echo "[INFO] /dev/fuse is absent: disabling rofiles-fuse"
    builder_args+=(--disable-rofiles-fuse)
fi
if [ -n "${FLATPAK_BUILDER_ARGS:-}" ]; then
    # shellcheck disable=SC2206  # deliberately word-split: the variable carries several flags
    builder_args+=(${FLATPAK_BUILDER_ARGS})
fi

echo "[INFO] Building the Flatpak"
flatpak-builder "${builder_args[@]}" "$BUILD_DIR" "$MANIFEST"

echo "[INFO] Bundling"
flatpak build-bundle "$REPO_DIR" "$OUTPUT_DIR/FlatCAMPlus-${VERSION}-linux-x86_64.flatpak" "$APP_ID"
ls -l "$OUTPUT_DIR"/*.flatpak
