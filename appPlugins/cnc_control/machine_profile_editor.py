# FlatCAM Plus CNC Control Module
# License: FlatCAM Plus CNC Control Module Non-Commercial License.
# See appPlugins/cnc_control/LICENSE.

import builtins
import gettext

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal

from .machine_profiles import normalize_machine_profile, normalize_machine_profiles
from .widgets import FluidStyleButton

import appTranslation as fcTranslate

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext


class MachineProfilesEditor(QtWidgets.QWidget):
    """Profile list and editor form shared by the dialog and the Preferences tab."""

    profiles_changed = pyqtSignal(list, str)

    def __init__(self, profiles, active_name="", parent=None):
        super().__init__(parent)
        self.profiles = normalize_machine_profiles(profiles)
        self.active_name = active_name or self.profiles[0]["name"]

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        list_panel = QtWidgets.QGroupBox(_("Profiles"))
        list_lay = QtWidgets.QVBoxLayout(list_panel)
        self.profile_list = QtWidgets.QListWidget()
        self.profile_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        list_lay.addWidget(self.profile_list, 1)

        self.new_btn = FluidStyleButton(_("New"), "#5cb85c", "#449d44")
        self.delete_btn = FluidStyleButton(_("Delete"), "#d9534f", "#c9302c")
        list_btns = QtWidgets.QHBoxLayout()
        list_btns.addWidget(self.new_btn)
        list_btns.addWidget(self.delete_btn)
        list_lay.addLayout(list_btns)
        lay.addWidget(list_panel, 1)

        editor_panel = QtWidgets.QGroupBox(_("Profile Settings"))
        form = QtWidgets.QFormLayout(editor_panel)
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(8)

        self.name_edit = QtWidgets.QLineEdit()
        self.safe_z = self.double_spin(-100000.0, 100000.0, " mm")
        self.jog_feed = self.int_spin(1, 60000, " mm/min")
        self.probe_feed = self.int_spin(1, 60000, " mm/min")
        self.spindle_max = self.int_spin(0, 100000, " RPM")
        self.travel_x = self.double_spin(0.0, 100000.0, " mm")
        self.travel_y = self.double_spin(0.0, 100000.0, " mm")
        self.travel_z = self.double_spin(0.0, 100000.0, " mm")

        form.addRow(_("Name:"), self.name_edit)
        form.addRow(_("Safe Z:"), self.safe_z)
        form.addRow(_("Default jog feed:"), self.jog_feed)
        form.addRow(_("Probe feed:"), self.probe_feed)
        form.addRow(_("Max spindle:"), self.spindle_max)
        form.addRow(_("Travel X:"), self.travel_x)
        form.addRow(_("Travel Y:"), self.travel_y)
        form.addRow(_("Travel Z:"), self.travel_z)

        self.save_btn = FluidStyleButton(_("Save Profile"), "#337ab7", "#286090")
        form.addRow("", self.save_btn)
        lay.addWidget(editor_panel, 2)

        self.new_btn.clicked.connect(self.on_new)
        self.delete_btn.clicked.connect(self.on_delete)
        self.save_btn.clicked.connect(self.on_save)
        self.profile_list.itemSelectionChanged.connect(self.on_selection_changed)

        self.refresh_list()
        self.select_profile(self.active_name)

    @staticmethod
    def double_spin(minimum, maximum, suffix):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(3)
        spin.setSuffix(suffix)
        return spin

    @staticmethod
    def int_spin(minimum, maximum, suffix):
        spin = QtWidgets.QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSuffix(suffix)
        return spin

    def refresh_list(self):
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        for profile in self.profiles:
            self.profile_list.addItem(profile["name"])
        self.profile_list.blockSignals(False)

    def select_profile(self, name):
        self.profile_list.blockSignals(True)
        found = False
        for row in range(self.profile_list.count()):
            if self.profile_list.item(row).text() == name:
                self.profile_list.setCurrentRow(row)
                found = True
                break
        if not found and self.profile_list.count():
            self.profile_list.setCurrentRow(0)
        self.profile_list.blockSignals(False)
        self._load_selected_profile()

    def selected_index(self):
        row = self.profile_list.currentRow()
        return row if 0 <= row < len(self.profiles) else -1

    def set_profiles(self, profiles, active_name=""):
        self.profiles = normalize_machine_profiles(profiles)
        names = {profile["name"] for profile in self.profiles}
        self.active_name = active_name if active_name in names else self.profiles[0]["name"]
        self.refresh_list()
        self.select_profile(self.active_name)

    def _load_selected_profile(self):
        idx = self.selected_index()
        if idx < 0:
            return
        profile = self.profiles[idx]
        self.active_name = profile["name"]
        self.name_edit.setText(profile["name"])
        self.safe_z.setValue(profile["safe_z"])
        self.jog_feed.setValue(profile["jog_feed"])
        self.probe_feed.setValue(profile["probe_feed"])
        self.spindle_max.setValue(profile["spindle_max"])
        self.travel_x.setValue(profile["travel_x"])
        self.travel_y.setValue(profile["travel_y"])
        self.travel_z.setValue(profile["travel_z"])

    def _emit_changed(self):
        self.profiles_changed.emit([dict(profile) for profile in self.profiles], self.active_name)

    def on_selection_changed(self):
        self._load_selected_profile()
        self._emit_changed()

    def on_new(self):
        base = _("New Machine")
        names = {profile["name"] for profile in self.profiles}
        name = base
        suffix = 2
        while name in names:
            name = f"{base} {suffix}"
            suffix += 1
        self.profiles.append(normalize_machine_profile({"name": name}, fallback_name=name))
        self.active_name = name
        self.refresh_list()
        self.select_profile(name)
        self._emit_changed()

    def on_delete(self):
        idx = self.selected_index()
        if idx < 0:
            return
        if len(self.profiles) == 1:
            QtWidgets.QMessageBox.warning(self, _("Machine Profiles"), _("At least one machine profile is required."))
            return
        removed = self.profiles.pop(idx)
        if self.active_name == removed["name"]:
            self.active_name = self.profiles[0]["name"]
        self.refresh_list()
        self.select_profile(self.active_name)
        self._emit_changed()

    def on_save(self):
        idx = self.selected_index()
        if idx < 0:
            return

        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, _("Machine Profiles"), _("Profile name is required."))
            return

        for row, profile in enumerate(self.profiles):
            if row != idx and profile["name"] == name:
                QtWidgets.QMessageBox.warning(self, _("Machine Profiles"), _("Profile name must be unique."))
                return

        old_name = self.profiles[idx]["name"]
        self.profiles[idx] = normalize_machine_profile({
            "name": name,
            "safe_z": self.safe_z.value(),
            "jog_feed": self.jog_feed.value(),
            "probe_feed": self.probe_feed.value(),
            "spindle_max": self.spindle_max.value(),
            "travel_x": self.travel_x.value(),
            "travel_y": self.travel_y.value(),
            "travel_z": self.travel_z.value(),
        }, fallback_name=old_name)
        self.active_name = name
        self.refresh_list()
        self.select_profile(name)
        self._emit_changed()
