"""Subprocess probe: boot the real application and report what it actually loaded.

Run as ``python tests/theme_probe.py <home>``. This lives outside the test module
because the application builds a multiprocessing pool whose forkserver child
re-imports the main module: any boot driver must keep its top-level work behind the
``__main__`` guard, or the child re-runs it.
"""

import json
import os
import sys


def main():
    home = sys.argv[1]

    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["HOME"] = home
    for variable, suffix in (
        ("XDG_CONFIG_HOME", ".config"),
        ("XDG_DATA_HOME", os.path.join(".local", "share")),
        ("XDG_CACHE_HOME", ".cache"),
    ):
        os.environ[variable] = os.path.join(home, suffix)

    from PyQt6 import QtCore, QtWidgets

    qapp = QtWidgets.QApplication(["flatcam"])

    from flatcam_plus.appMain import App

    app = App(qapp=qapp, startup_project_request=None)

    tree = app.collection.view
    horizontal = QtCore.Qt.Orientation.Horizontal
    display = QtCore.Qt.ItemDataRole.DisplayRole

    result = {
        "theme": app.options.get("global_theme"),
        "dark_resources": "dark_resources" in str(app.resource_location),
        "vendor_sheet_chars": len(qapp.styleSheet() or ""),
        "tree_header_hidden": tree.isHeaderHidden(),
        "tree_columns": app.collection.columnCount(),
        "kind_header": app.collection.headerData(1, horizontal, display),
    }

    app.quit_application()

    print("PROBE " + json.dumps(result))


if __name__ == "__main__":
    main()
