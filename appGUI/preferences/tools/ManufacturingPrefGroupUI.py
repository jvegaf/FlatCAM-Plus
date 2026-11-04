# ##########################################################
# FlatCAM PLUS: 2D Post-processing for Manufacturing       #
# File Updated By Sadri ERCAN - 2026                      #
# License:  MIT Licence                                   #
# ##########################################################

from appGUI.GUIElements import FCFrame, FCLabel, GLay
from appGUI.preferences.OptionsGroupUI import OptionsGroupUI

import gettext
from flatcam_plus import appTranslation as fcTranslate
import builtins

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext


class ManufacturingPrefGroupUI(OptionsGroupUI):
    def __init__(self, app, parent=None):
        super(ManufacturingPrefGroupUI, self).__init__(self, parent=parent)

        self.setTitle(str(_("Manufacturing Settings")))

        self.workflow_label = FCLabel('%s' % _("Fallback Defaults"), color='blue', bold=True)
        self.workflow_label.setToolTip(
            _("Tool-specific values should be stored in Tools Database presets. Preferences are fallback values.")
        )
        self.layout.addWidget(self.workflow_label)

        workflow_frame = FCFrame()
        self.layout.addWidget(workflow_frame)

        workflow_grid = GLay(v_spacing=5, h_spacing=3)
        workflow_frame.setLayout(workflow_grid)

        self.tooling_status = FCLabel(
            "%s\n%s\n%s" % (
                _("Tool presets: define cutting values in the Tools Database."),
                _("Fallback defaults: use Milling, Drilling, Cutout and engraving groups only for missing values."),
                _("Output defaults: use CNCJob preferences.")
            )
        )
        self.tooling_status.setWordWrap(True)
        workflow_grid.addWidget(self.tooling_status, 0, 0, 1, 2)

        self.layout.addStretch()
