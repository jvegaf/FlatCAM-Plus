"""``python -m flatcam_plus`` entry point.

Kept as a two-line shim so the module the interpreter executes is never the module that owns the
launcher: runpy executes a ``__main__`` module without a package context, which would break the
``flatcam_plus`` imports ``flatcam_plus.launcher`` performs.

The ``flatcam-plus`` console script and the PyInstaller bundles call ``flatcam_plus.launcher.main``
directly.
"""

from flatcam_plus.launcher import main

if __name__ == "__main__":
    main()
