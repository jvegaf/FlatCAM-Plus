from PyQt6 import QtWidgets

from appGUI.preferences.machine.MachinePrefGroupUI import MachinePrefGroupUI
from appGUI.ColumnarFlowLayout import ColumnarFlowLayout

import gettext
from flatcam_plus import appTranslation as fcTranslate
import builtins

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext


class MachinePreferencesUI(QtWidgets.QWidget):

    def __init__(self, app, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        if app.defaults['global_gui_layout'] == 0:
            self.layout = QtWidgets.QHBoxLayout()
        else:
            self.layout = ColumnarFlowLayout()
        self.setLayout(self.layout)

        self.machine_group = MachinePrefGroupUI(app=app)
        self.machine_group.setMinimumWidth(480)

        self.layout.addWidget(self.machine_group)
        self.layout.addStretch()
