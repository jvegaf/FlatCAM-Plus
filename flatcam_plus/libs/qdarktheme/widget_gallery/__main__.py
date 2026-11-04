"""Module allowing for `python -m qdarktheme.widget_gallery`."""
import sys

import flatcam_plus.libs.qdarktheme
from flatcam_plus.libs.qdarktheme.qtpy.QtCore import Qt
from flatcam_plus.libs.qdarktheme.qtpy.QtWidgets import QApplication
from flatcam_plus.libs.qdarktheme.widget_gallery.mainwindow import WidgetGallery

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):  # Enable High DPI display with Qt5
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)  # type: ignore
    win = WidgetGallery()
    win.menuBar().setNativeMenuBar(False)
    app.setStyleSheet(flatcam_plus.libs.qdarktheme.load_stylesheet())
    win.show()
    app.exec()
