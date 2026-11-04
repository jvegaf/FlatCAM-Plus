
import pkgutil
import importlib
import sys

# allowed command modules (please append them alphabetically ordered)
import flatcam_plus.tclCommands.TclCommandAddAperture
import flatcam_plus.tclCommands.TclCommandAddCircle
import flatcam_plus.tclCommands.TclCommandAddDrill
import flatcam_plus.tclCommands.TclCommandAddPolygon
import flatcam_plus.tclCommands.TclCommandAddPolyline
import flatcam_plus.tclCommands.TclCommandAddRectangle
import flatcam_plus.tclCommands.TclCommandAddSlot
import flatcam_plus.tclCommands.TclCommandAlignDrill
import flatcam_plus.tclCommands.TclCommandAlignDrillGrid
import flatcam_plus.tclCommands.TclCommandBbox
import flatcam_plus.tclCommands.TclCommandBounds
import flatcam_plus.tclCommands.TclCommandBuffer
import flatcam_plus.tclCommands.TclCommandClearShell
import flatcam_plus.tclCommands.TclCommandCncjob
import flatcam_plus.tclCommands.TclCommandCopperClear
import flatcam_plus.tclCommands.TclCommandCutout
import flatcam_plus.tclCommands.TclCommandDelete
import flatcam_plus.tclCommands.TclCommandDrillcncjob
import flatcam_plus.tclCommands.TclCommandExportDXF
import flatcam_plus.tclCommands.TclCommandExportExcellon
import flatcam_plus.tclCommands.TclCommandExportGerber
import flatcam_plus.tclCommands.TclCommandExportGcode
import flatcam_plus.tclCommands.TclCommandExportSVG
import flatcam_plus.tclCommands.TclCommandExteriors
import flatcam_plus.tclCommands.TclCommandFollow
import flatcam_plus.tclCommands.TclCommandGeoCutout
import flatcam_plus.tclCommands.TclCommandGeoUnion
import flatcam_plus.tclCommands.TclCommandGetActive
import flatcam_plus.tclCommands.TclCommandGetNames
import flatcam_plus.tclCommands.TclCommandGetPath
import flatcam_plus.tclCommands.TclCommandGetSys
import flatcam_plus.tclCommands.TclCommandHelp
import flatcam_plus.tclCommands.TclCommandInteriors
import flatcam_plus.tclCommands.TclCommandIsolate
import flatcam_plus.tclCommands.TclCommandJoinExcellon
import flatcam_plus.tclCommands.TclCommandJoinGeometry
import flatcam_plus.tclCommands.TclCommandListSys
import flatcam_plus.tclCommands.TclCommandListPP
import flatcam_plus.tclCommands.TclCommandMillDrills
import flatcam_plus.tclCommands.TclCommandMillSlots
import flatcam_plus.tclCommands.TclCommandMirror
import flatcam_plus.tclCommands.TclCommandNew
import flatcam_plus.tclCommands.TclCommandNregions
import flatcam_plus.tclCommands.TclCommandNewExcellon
import flatcam_plus.tclCommands.TclCommandNewGeometry
import flatcam_plus.tclCommands.TclCommandNewGerber
import flatcam_plus.tclCommands.TclCommandOffset
import flatcam_plus.tclCommands.TclCommandOpenDXF
import flatcam_plus.tclCommands.TclCommandOpenExcellon
import flatcam_plus.tclCommands.TclCommandOpenFolder
import flatcam_plus.tclCommands.TclCommandOpenGCode
import flatcam_plus.tclCommands.TclCommandOpenGerber
import flatcam_plus.tclCommands.TclCommandOpenProject
import flatcam_plus.tclCommands.TclCommandOpenSVG
import flatcam_plus.tclCommands.TclCommandOptions
import flatcam_plus.tclCommands.TclCommandPaint
import flatcam_plus.tclCommands.TclCommandPanelize
import flatcam_plus.tclCommands.TclCommandPlotAll
import flatcam_plus.tclCommands.TclCommandPlotObjects
import flatcam_plus.tclCommands.TclCommandQuit
import flatcam_plus.tclCommands.TclCommandSaveProject
import flatcam_plus.tclCommands.TclCommandSaveSys
import flatcam_plus.tclCommands.TclCommandScale
import flatcam_plus.tclCommands.TclCommandSetActive
import flatcam_plus.tclCommands.TclCommandSetOrigin
import flatcam_plus.tclCommands.TclCommandSetPath
import flatcam_plus.tclCommands.TclCommandSetSys
import flatcam_plus.tclCommands.TclCommandSkew
import flatcam_plus.tclCommands.TclCommandSplitGeometry
import flatcam_plus.tclCommands.TclCommandSubtractPoly
import flatcam_plus.tclCommands.TclCommandSubtractRectangle
import flatcam_plus.tclCommands.TclCommandVersion
import flatcam_plus.tclCommands.TclCommandWriteGCode


__all__ = []

# for loader, name, is_pkg in pkgutil.walk_packages(__path__):
#     module = loader.find_module(name).load_module(name)
#     __all__.append(name)

for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = importlib.import_module(f"{__name__}.{name}")
    __all__.append(name)


def register_all_commands(app, commands):
    """
    Static method which registers all known commands.

    Command should  be for now in directory flatcam_plus/tclCommands and module should start with TCLCommand
    Class  have to follow same  name as module.

    we need import all  modules  in top section:
    import flatcam_plus.tclCommands.TclCommandExteriors
    at this stage we can include only wanted  commands  with this, auto loading may be implemented in future
    I have no enough knowledge about python's anatomy. Would be nice to include all classes which are descendant etc.

    :param app: FlatCAMApp
    :param commands: List of commands being updated
    :return: None
    """

    # Both halves of the lookup are derived from the package this module actually lives in, so
    # the registration survives the package being moved or renamed. Spelling the package path
    # literally used to select nothing after the move, leaving the shell with an empty command
    # table and no error anywhere.
    base_module = '{}.TclCommand'.format(__name__)
    tcl_modules = {k: v for k, v in list(
        sys.modules.items()) if k.startswith(base_module)}

    for key, mod in list(tcl_modules.items()):
        if key != base_module:
            class_name = key.rsplit('.', 1)[-1]
            class_type = getattr(mod, class_name)
            command_instance = class_type(app)

            for alias in command_instance.aliases:
                try:
                    description = command_instance.description
                except AttributeError:
                    description = ''
                commands[alias] = {
                    'fcn': command_instance.execute_wrapper,
                    'help': command_instance.get_decorated_help(),
                    'description': description
                }
