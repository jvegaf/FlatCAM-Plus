# ##########################################################
# FlatCAM PLUS: CNC Machine Settings                       #
# License:  MIT Licence                                    #
# ##########################################################

from PyQt6.QtCore import QSettings

from appGUI.preferences.OptionsGroupUI import OptionsGroupUI
from appPlugins.cnc_control.machine_profile_editor import MachineProfilesEditor
from appPlugins.cnc_control.machine_profiles import normalize_machine_profiles

import gettext
import appTranslation as fcTranslate
import builtins
import json

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext


class MachinePrefGroupUI(OptionsGroupUI):
    def __init__(self, app, parent=None):
        super(MachinePrefGroupUI, self).__init__(self, parent=parent)

        self.setTitle(str(_("Machine Settings")))
        self.app = app

        profiles, active_name = self._load_machine_profiles()
        self.editor = MachineProfilesEditor(profiles, active_name, self)
        self.editor.profiles_changed.connect(self.on_profiles_changed)

        self.layout.addWidget(self.editor)
        self.layout.addStretch()

    def _load_machine_profiles(self):
        settings = QSettings("Open Source", "FlatCAM_Plus")
        profiles = []
        if settings.contains("cnc_machine_profiles"):
            try:
                profiles = json.loads(settings.value("cnc_machine_profiles"))
            except (TypeError, json.JSONDecodeError):
                profiles = []

        profiles = normalize_machine_profiles(profiles)
        active_name = settings.value("cnc_active_machine_profile", "")
        names = {profile["name"] for profile in profiles}
        if active_name not in names:
            active_name = profiles[0]["name"]
        return profiles, active_name

    def _save_machine_profiles(self, profiles, active_name):
        settings = QSettings("Open Source", "FlatCAM_Plus")
        settings.setValue("cnc_machine_profiles", json.dumps(profiles))
        settings.setValue("cnc_active_machine_profile", active_name)

    def on_profiles_changed(self, profiles, active_name):
        profiles = normalize_machine_profiles(profiles)
        names = {profile["name"] for profile in profiles}
        if active_name not in names:
            active_name = profiles[0]["name"]
        self._save_machine_profiles(profiles, active_name)

        cnc_tool = getattr(self.app, "cnc_control_tool", None)
        if cnc_tool is not None and hasattr(cnc_tool, "load_machine_profiles"):
            cnc_tool.load_machine_profiles()

    def refresh_from_storage(self):
        profiles, active_name = self._load_machine_profiles()
        self.editor.set_profiles(profiles, active_name)
