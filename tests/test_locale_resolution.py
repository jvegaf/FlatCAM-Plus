"""The locale directory must resolve from the package directory, not from the process CWD.

``appTranslation.load_languages()`` used to derive ``locale/`` from
``os.path.dirname(os.path.abspath(__file__))`` with a silent ``parents[1]`` fallback, which only
worked while ``locale/`` sat beside the package. The translation tree now ships inside the
package, so the first candidate is the package's own ``locale/`` and it resolves in a checkout,
in an installed wheel and in a frozen bundle alike. An empty language list would be invisible:
it just leaves the UI in English.
"""

import os

import flatcam_plus.appTranslation as app_translation

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(REPO_ROOT, "flatcam_plus")


def test_languages_dir_is_anchored_to_the_package_directory():
    assert app_translation.languages_dir() == os.path.join(PACKAGE_DIR, "locale")


def test_languages_dir_is_absolute_and_survives_a_cwd_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert os.path.isabs(app_translation.languages_dir())
    assert os.path.isdir(app_translation.languages_dir())


def test_load_languages_finds_every_shipped_translation():
    languages = app_translation.load_languages()

    assert len(languages) == len(app_translation.languages_dict)
    assert "Español" in languages.values()


def test_a_frozen_library_layout_still_finds_the_shipped_translations(tmp_path, monkeypatch):
    """A frozen build that unpacks the package inside ``lib/`` keeps ``locale/`` inside it.

    The translation tree ships as package data, so it travels with the package rather than
    staying at the application root of whatever directory the bundle unpacks into.
    """

    app_root = tmp_path / "app"
    package = app_root / "lib" / "flatcam_plus"
    package.mkdir(parents=True)
    for code in app_translation.languages_dict:
        (package / "locale" / code).mkdir(parents=True)
    frozen_module = package / "appTranslation.py"
    frozen_module.write_text("", encoding="utf-8")

    monkeypatch.setattr(app_translation, "__file__", str(frozen_module))
    monkeypatch.setattr(app_translation, "translations", {})

    languages = app_translation.load_languages()

    assert len(languages) == len(app_translation.languages_dict)
