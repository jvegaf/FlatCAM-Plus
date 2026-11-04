"""The locale directory must resolve from the application root, not from the module file.

``appTranslation.load_languages()`` used to derive ``locale/`` from
``os.path.dirname(os.path.abspath(__file__))`` with a silent ``parents[1]`` fallback. That
worked only while the module sat at the repository root: one level deeper the first candidate
points at ``flatcam_plus/locale``, which does not exist, and the failure is invisible because an
empty language list simply leaves the UI in English. T4.5 moves the module, so the lookup is
anchored to the directory that actually holds ``locale/`` and pinned here.
"""

import os

import flatcam_plus.appTranslation as app_translation

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_languages_dir_is_anchored_to_the_application_root():
    assert app_translation.languages_dir() == os.path.join(REPO_ROOT, "locale")


def test_languages_dir_is_absolute_and_survives_a_cwd_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert os.path.isabs(app_translation.languages_dir())
    assert os.path.isdir(app_translation.languages_dir())


def test_load_languages_finds_every_shipped_translation():
    languages = app_translation.load_languages()

    assert len(languages) == len(app_translation.languages_dict)
    assert "Español" in languages.values()


def test_a_frozen_library_layout_still_finds_the_shipped_translations(tmp_path, monkeypatch):
    """A frozen build that unpacks the package inside ``lib/`` keeps ``locale/`` at the app root.

    The pre-move module reached it with ``Path(__file__).parents[1]``; the module now sits one
    level deeper, so the same directory is one level further up.
    """

    app_root = tmp_path / "app"
    (app_root / "lib" / "flatcam_plus").mkdir(parents=True)
    for code in app_translation.languages_dict:
        (app_root / "locale" / code).mkdir(parents=True)
    frozen_module = app_root / "lib" / "flatcam_plus" / "appTranslation.py"
    frozen_module.write_text("", encoding="utf-8")

    monkeypatch.setattr(app_translation, "__file__", str(frozen_module))
    monkeypatch.setattr(app_translation, "translations", {})

    languages = app_translation.load_languages()

    assert len(languages) == len(app_translation.languages_dict)
