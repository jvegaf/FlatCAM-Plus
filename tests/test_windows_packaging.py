"""The Windows installer is an Inno Setup script driven by PowerShell.

Neither tool runs on Linux, so these guards pin the two things that only break on the runner: how
PowerShell hands defines to ISCC, and that every preprocessor variable the script uses has a
default in the .iss.
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOWS_DIR = os.path.join(REPO_ROOT, "packaging", "windows")
SCRIPT = os.path.join(WINDOWS_DIR, "build_windows_installer.ps1")
SETUP = os.path.join(WINDOWS_DIR, "FlatCAMPlus.iss")


def read(path):
    with open(path, encoding="utf-8-sig") as handle:
        return handle.read()


def test_the_iscc_defines_never_carry_their_own_quotes():
    """PowerShell 7 passes inner quotes through, and ISCC keeps them in the value."""
    call = [line for line in read(SCRIPT).splitlines() if "InnoCompiler" in line and "/D" in line]

    assert call, "no ISCC invocation found"
    for line in call:
        assert '""' not in line, line
        assert not re.search(r'/D\w+="', line), line


def test_every_preprocessor_variable_used_has_a_default():
    setup = read(SETUP)
    used = set(re.findall(r"\{#(\w+)\}", setup))
    defined = set(re.findall(r"^#define\s+(\w+)", setup, re.MULTILINE))
    guarded = set(re.findall(r"^#ifndef\s+(\w+)", setup, re.MULTILINE))

    assert used
    missing = {name for name in used if name not in defined and name not in guarded}
    assert not missing, "the .iss uses undefined preprocessor variables: {0}".format(sorted(missing))
    for name in used:
        assert name in defined or name in guarded, name


def test_the_installer_name_is_built_from_defines_not_inno_constants():
    setup = read(SETUP)
    line = [l for l in setup.splitlines() if l.startswith("OutputBaseFilename=")]

    assert line, "no OutputBaseFilename directive"
    value = line[0]
    assert "{#AppVersion}" in value
    # A bare {name} is an Inno constant, and Inno has no {version} or {arch}.
    for wrong in ("{version}", "{arch}", "{Version}"):
        assert wrong not in value, value
