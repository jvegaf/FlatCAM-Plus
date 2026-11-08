"""The shipped ``.po`` files keep their obsolete entries, and ``msgfmt`` counts them.

Every ``flatcam_plus/locale/*/LC_MESSAGES/strings.po`` carries thousands of ``#~`` obsolete
entries left behind by translators, and in several languages an obsolete entry repeats the
``msgid`` of an active one (``ru`` has an active ``msgid "FlatCAM Plus"`` and an obsolete copy of
it). ``msgfmt`` looks at obsolete entries too, so it refuses the file with ``duplicate message
definition`` and the build compiles no translation at all.

Deleting the obsolete blocks from the sources is not an option: it is some 43k lines of diff and
it throws the translators' history away. The build therefore drops the obsolete lines while it
compiles and leaves the ``.po`` files alone. These tests pin that rule with a fixture of their own
instead of the current contents of the locale tree: one active entry and one obsolete entry with
the same ``msgid``, which is exactly the shape ``msgfmt`` rejects and the pipeline must accept.

They run the ``compile_translations()`` function taken from the build script, so a change to the
real compile step is what they measure, not a copy of it.
"""

import gettext
import os
import re
import shutil
import subprocess

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_SCRIPT = os.path.join(REPO_ROOT, "packaging", "linux", "build_linux_portable.sh")

PO_WITH_OBSOLETE_DUPLICATE = """\
msgid ""
msgstr ""
"Project-Id-Version: flatcam-plus-test\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

msgid "FlatCAM Plus"
msgstr "FlatCAM Plus Plus"

#~ msgid "FlatCAM Plus"
#~ msgstr "FlatCAM Plus (obsolete)"
"""

PO_WITH_DUPLICATE_ACTIVE_ENTRIES = """\
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "FlatCAM Plus"
msgstr "FlatCAM Plus Plus"

msgid "FlatCAM Plus"
msgstr "FlatCAM Plus Encore"
"""

pytestmark = pytest.mark.skipif(
    shutil.which("msgfmt") is None,
    reason="the gettext tools are missing (install gettext, or `pacman -S gettext`)",
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def compile_translations_function():
    """Return the source of ``compile_translations()`` as the build script defines it."""
    script = read(BUILD_SCRIPT)
    match = re.search(
        r"^compile_translations\(\) \{\n(.*?)^\}$",
        script,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "compile_translations() is missing from packaging/linux/build_linux_portable.sh"
    return match.group(1)


def write_po(tmp_path, text):
    """Lay out a throwaway locale tree the way the build script finds it."""
    messages_dir = tmp_path / "flatcam_plus" / "locale" / "xx" / "LC_MESSAGES"
    messages_dir.mkdir(parents=True)
    po_file = messages_dir / "strings.po"
    po_file.write_text(text, encoding="utf-8")
    return po_file


def run_compile_translations(tmp_path, po_text, skip_translations=0):
    """Execute the build script's own compile step against a temporary locale tree."""
    write_po(tmp_path, po_text)
    script = "\n".join(
        [
            "set -euo pipefail",
            "SKIP_TRANSLATIONS=%d" % skip_translations,
            "compile_translations() {",
            compile_translations_function(),
            "}",
            "compile_translations",
        ]
    )
    completed = subprocess.run(
        ["bash", "-c", script], cwd=str(tmp_path), capture_output=True, text=True
    )
    return completed, tmp_path / "flatcam_plus" / "locale" / "xx" / "LC_MESSAGES" / "strings.mo"


def test_the_build_compiles_a_po_file_whose_obsolete_entry_repeats_an_active_msgid(tmp_path):
    completed, mo_file = run_compile_translations(tmp_path, PO_WITH_OBSOLETE_DUPLICATE)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert mo_file.is_file(), completed.stdout + completed.stderr
    with open(mo_file, "rb") as handle:
        catalog = gettext.GNUTranslations(handle)
    assert catalog.gettext("FlatCAM Plus") == "FlatCAM Plus Plus"


def test_plain_msgfmt_rejects_the_same_fixture_with_a_duplicate_definition(tmp_path):
    po_file = write_po(tmp_path, PO_WITH_OBSOLETE_DUPLICATE)
    mo_file = tmp_path / "strings.mo"

    completed = subprocess.run(
        ["msgfmt", str(po_file), "-o", str(mo_file)], capture_output=True, text=True
    )

    assert completed.returncode != 0, "msgfmt accepted the duplicate the pipeline has to strip"
    assert "duplicate message definition" in completed.stderr
    assert not mo_file.exists()


def test_a_genuinely_broken_po_file_still_fails_the_build(tmp_path):
    completed, mo_file = run_compile_translations(tmp_path, PO_WITH_DUPLICATE_ACTIVE_ENTRIES)

    assert completed.returncode != 0, completed.stdout
    assert "duplicate message definition" in completed.stderr
    assert not mo_file.exists()


def test_skipping_translations_leaves_the_po_file_uncompiled(tmp_path):
    completed, mo_file = run_compile_translations(
        tmp_path, PO_WITH_OBSOLETE_DUPLICATE, skip_translations=1
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Skipping translation compilation." in completed.stdout
    assert not mo_file.exists()
