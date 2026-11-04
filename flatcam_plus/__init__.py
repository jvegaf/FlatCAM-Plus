"""FlatCAM Plus package.

The modules that used to live at the repository root move in here phase by phase. ``appMain``,
the application controller the root ``flatcam.py`` launcher instantiates, is the last of them;
the data directories it resolves for itself (``assets/``, ``locale/``, ``preprocessors/``,
``config/``) stay beside the package, so ``App.app_home`` is anchored to the package's parent.
See ``odd/tasks/repo-structure-cleanup.md``.
"""
