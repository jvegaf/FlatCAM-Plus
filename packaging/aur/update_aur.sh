#!/usr/bin/env bash
# Regenerate the AUR package for a release: bump pkgver, write the real checksums, rebuild .SRCINFO.
#
# Run it once the release assets exist (after the tag pipeline publishes the tarball), or let the
# release workflow call it. It needs `makepkg` (Arch) and `curl`; inside another distribution, run
# it in an archlinux container, which is what the workflow does.
#
# Usage: packaging/aur/update_aur.sh <version>
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AUR_DIR="$ROOT_DIR/packaging/aur"
PKGBUILD="$AUR_DIR/PKGBUILD"

if [ "$#" -ne 1 ]; then
    echo "usage: update_aur.sh <version>   (for example 1.3.0)" >&2
    exit 2
fi
VERSION="$1"

if ! command -v makepkg >/dev/null 2>&1; then
    echo "[ERROR] makepkg is not on PATH; run this inside an archlinux container" >&2
    exit 1
fi

# Fetch and hash first: a release that is not published yet must leave the files untouched
# instead of leaving a bumped pkgver with placeholder checksums behind.
echo "[INFO] Downloading the release assets to compute their checksums"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
base="https://github.com/thebestgoodguy/FlatCAM-Plus"
assets=(
    "FlatCAMPlus-${VERSION}-linux-x86_64.tar.gz::${base}/releases/download/v${VERSION}/FlatCAMPlus-${VERSION}-linux-x86_64.tar.gz"
    "flatcam-plus.desktop::${base}/raw/v${VERSION}/packaging/linux/flatcam-plus.desktop"
    "flatcam-plus.metainfo.xml::${base}/raw/v${VERSION}/packaging/linux/flatcam-plus.metainfo.xml"
    "flatcam-plus.png::${base}/raw/v${VERSION}/assets/resources/app256.png"
)
sums=()
for entry in "${assets[@]}"; do
    url="${entry#*::}"
    name="$(basename "${entry%%::*}")"
    curl -sSfL --retry 3 -o "$workdir/$name" "$url"
    sums+=("$(sha256sum "$workdir/$name" | cut -d' ' -f1)")
done

printf "[INFO] checksums: %s\n" "${sums[*]}"
echo "[INFO] pkgver -> $VERSION"
sed -i "s/^pkgver=.*/pkgver=$VERSION/" "$PKGBUILD"
python3 - "$PKGBUILD" "${sums[@]}" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
sums = sys.argv[2:]
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
for index, line in enumerate(lines):
    if line.startswith("sha256sums="):
        lines[index] = "sha256sums=(" + " ".join("'{0}'".format(value) for value in sums) + ")"
        break
else:
    raise SystemExit("no sha256sums line in the PKGBUILD")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

echo "[INFO] Regenerating .SRCINFO"
cd "$AUR_DIR"
makepkg --printsrcinfo > .SRCINFO
echo "[OK] packaging/aur is ready for v$VERSION"
