"""A preferences file the application writes must load without a reset.

``AppDefaults.load`` compares the ``version`` stored in the preferences file with the
running build's version (``defaults.py::__is_old_defaults``) and, in a beta build, wipes
every preference on a mismatch. The value in that file comes from ``AppDefaults.write``,
and the dict it writes is ``app.options`` copied into the defaults by
``quit_application``: a project saved by an older build carries ``version: <old>`` inside
its options and ``restore_project_handler`` merges it back, so one open project was enough
to poison the profile and every later launch reset the preferences.

The rule these tests pin is the user-visible one: whatever arrived through ``options``,
the file the app writes has to load again in the same build without a reset.
"""

import json

from flatcam_plus.defaults import AppDefaults
from flatcam_plus.version import APP_VERSION as VERSION


class _Inform:
    """Stand-in for the status-bar signal ``AppDefaults.load`` emits on."""

    def __init__(self):
        self.messages = []

    def emit(self, message):
        self.messages.append(message)


def test_a_written_preferences_file_loads_without_a_reset(tmp_path):
    writer = AppDefaults(beta=True, version=VERSION)
    writer.defaults["global_theme"] = "dark"
    # What a project saved by 1.3.1 injects into ``app.options`` before the quit copies
    # them into the defaults that get written.
    writer.defaults["version"] = "1.3.1"

    filename = tmp_path / ("current_defaults_%s.FlatConfig" % VERSION)
    writer.write(str(filename))

    # The file itself must carry this build's version: that is the whole invariant, and the
    # load below only observes it.
    assert json.loads(filename.read_text())["version"] == VERSION, (
        "the preferences file kept the version that came in through options"
    )

    reader = AppDefaults(beta=True, version=VERSION)
    inform = _Inform()
    reader.load(filename=str(filename), inform=inform)

    # ``reset_to_factory_defaults`` clears the flag again, so this assertion alone would not
    # catch the reset; the theme below is what makes it observable.
    assert reader.old_defaults_found is False, (
        "the preferences file written by this build was reported as old and reset; the "
        f"stored version was {writer.defaults['version']!r} instead of {VERSION!r}"
    )
    assert reader.defaults["global_theme"] == "dark", (
        "the preference stored in the file was replaced by its factory value"
    )
    assert inform.messages == []
