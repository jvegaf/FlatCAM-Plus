"""Version metadata for FlatCAM Plus.

The build scripts extract ``APP_VERSION`` from this file with a regular expression, so keep the
assignment on a single line and in this module path: ``packaging/*`` and the Windows installer
wrapper both parse it by path.
"""

APP_NAME = "FlatCAM Plus"
APP_VERSION = "1.2.0"
APP_VERSION_DATE = "2026.07.09"
APP_RELEASE_CHANNEL = "beta"
APP_BETA = True

__version__ = APP_VERSION
