from appGUI.GUIElements import *

import gettext
from flatcam_plus import appTranslation as fcTranslate
import builtins


fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext
