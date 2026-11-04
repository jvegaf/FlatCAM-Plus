"""The Tcl shell comes up with every command registered.

``register_all_commands`` in the ``tclCommands`` package builds the shell's command table by
filtering ``sys.modules`` down to the modules of its own package. That filter used to spell the
package path as a literal, so moving the package silently selected nothing: the application
booted, the shell opened, and no command answered, with no error anywhere. These tests read the
table the running application actually exposes.
"""

import pytest

# Aliases from unrelated command modules, so a partial discovery cannot pass by luck.
KNOWN_ALIASES = (
    "new",
    "help",
    "delete",
    "del",
    "version",
    "isolate",
    "open_gerber",
    "export_gcode",
    "quit_app",
)


def tcl_command_storage(fc_app):
    """The alias table ``FCShell`` fills through ``register_all_commands``."""
    return fc_app.shell.tcl_commands_storage


def test_the_shell_registers_its_command_table(fc_app):
    storage = tcl_command_storage(fc_app)

    # 101 aliases when this was written; the failure mode this guards is an empty table.
    assert len(storage) >= 100


@pytest.mark.parametrize("alias", KNOWN_ALIASES)
def test_known_command_aliases_are_registered(fc_app, alias):
    assert alias in tcl_command_storage(fc_app)


def test_every_registered_alias_carries_a_callable_and_its_help(fc_app):
    storage = tcl_command_storage(fc_app)
    assert storage, "the Tcl command registry is empty"

    for alias, entry in storage.items():
        assert callable(entry["fcn"]), alias
        assert isinstance(entry["help"], str) and entry["help"], alias
