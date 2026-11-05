"""A packaged build must not update itself.

Once the application ships as a ``deb``/``rpm``/``AUR``/``Flatpak`` package, the package manager
owns its files: a self-update would write into ``/opt`` and desynchronise the package database.
PyInstaller sets ``sys.frozen`` in a bundle, so that is the switch.
"""

import sys

from flatcam_plus.appCommon import AutoUpdater as auto_updater_module


def test_a_frozen_build_leaves_updates_to_its_package(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert auto_updater_module.should_self_update() is False


def test_a_source_checkout_keeps_checking_for_updates(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert auto_updater_module.should_self_update() is True
