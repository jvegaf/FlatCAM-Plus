"""FlatCAM Plus package.

Everything the application needs at runtime lives in here: the modules that used to sit at the
repository root, the two vendored dependency packages (``descartes`` and ``libs``), the
application packages, and the data directories (``assets/``, ``locale/``, ``preprocessors/``,
``config/``). ``flatcam_plus.launcher`` is the process entry point the ``flatcam-plus`` console
script and ``python -m flatcam_plus`` both call; it instantiates ``App`` from ``appMain``. The
package is installable, so ``App.app_home`` is the package directory and resolves the same way in
a checkout, in an installed wheel and in a frozen bundle.
See ``odd/tasks/package-homogenization.md``.
"""
