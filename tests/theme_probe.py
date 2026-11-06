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
    ui = app.ui
    horizontal = QtCore.Qt.Orientation.Horizontal
    display = QtCore.Qt.ItemDataRole.DisplayRole

    host = ui.toolbar_center_host
    hosted = [tb for tb in ui.findChildren(QtWidgets.QToolBar) if host.isAncestorOf(tb)]
    outside = [tb for tb in ui.findChildren(QtWidgets.QToolBar) if not host.isAncestorOf(tb)]

    import logging

    logging.getLogger("base").info("probe-record-sentinel")
    qapp.processEvents()
    log_text = ui.log_view.toPlainText() if hasattr(ui, "log_view") else ""
    ui.cnc_console_view.append_entry('<span style="color:#6a9955;">probe-cnc-sentinel</span>')
    cnc_mirror_ok = "probe-cnc-sentinel" in ui.cnc_console_view.toPlainText()
    terminal = ui.shell_terminal() if hasattr(ui, "shell_terminal") else None

    result = {
        "shell_tabs": [ui.shell_tabs.tabText(i) for i in range(ui.shell_tabs.count())],
        "dock_widget": type(ui.shell_dock.widget()).__name__,
        "log_captured": "probe-record-sentinel" in log_text,
        "cnc_mirror_accepts": cnc_mirror_ok,
        "shell_terminal": type(terminal).__name__ if terminal is not None else None,
        "stored_menu_show_text": QtCore.QSettings(
            "Open Source", "FlatCAM_Plus").value("menu_show_text", type=str),
        "hosted_toolbar_styles": [tb.toolButtonStyle().name for tb in hosted],
        "readout_toolbar_styles": [
            tb.toolButtonStyle().name for tb in outside
            if tb.objectName() in ("Coords_TB", "Snap_TB", "Delta_Coords_TB")
        ],
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
