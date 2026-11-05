#!/bin/sh
# Launcher for a system install: the payload sits in /opt and the application
# resolves its own data relative to the bundle, not to this script's directory.
set -eu

APPDIR="${FLATCAM_PLUS_HOME:-/opt/flatcam-plus}"

if [ ! -x "$APPDIR/FlatCAM-Plus" ]; then
    echo "flatcam-plus: no executable payload at $APPDIR/FlatCAM-Plus" >&2
    exit 1
fi

exec "$APPDIR/FlatCAM-Plus" "$@"
