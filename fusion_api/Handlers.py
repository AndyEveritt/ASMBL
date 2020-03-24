import adsk.core
import adsk.fusion
import traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class SetupCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Connect to the execute event.
            onExecute = SetupExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create setup tab input.
            tabCmdInputSetup = inputs.addTabCommandInput('setup', 'Setup')
            tabSetupChildInputs = tabCmdInputSetup.children

            # Create input setups group.
            groupSetupCmdInput = tabSetupChildInputs.addGroupCommandInput('inputSetups', 'Input Setups')
            groupSetupCmdInput.isExpanded = True
            groupSetupChildInputs = groupSetupCmdInput.children

            # Create selection inputs for setups.
            additiveSetup = groupSetupChildInputs.addSelectionInput(
                'additiveSetup', 'Additive Setup', 'Select the additive setup')
            additiveSetup.setSelectionLimits(1)

            camSetup = groupSetupChildInputs.addSelectionInput('camSetup', 'CAM Setup', 'Select the milling setup')
            camSetup.setSelectionLimits(1)

            # Create settings tab inputs
            tabCmdInputSettings = inputs.addTabCommandInput('settings', 'Settings')
            tabSettingsChildInputs = tabCmdInputSettings.children

            groupPrintCmdInput = tabSettingsChildInputs.addGroupCommandInput('print', 'Print Settings')
            groupPrintCmdInput.isExpanded = True
            groupPrintChildInputs = groupPrintCmdInput.children

            # Create print inputs
            groupPrintChildInputs.addFloatSpinnerCommandInput('raftHeight', 'Raft Height', 'mm', 0, 10000, 0.1, 0)
            groupPrintChildInputs.addFloatSpinnerCommandInput(
                'layerHeight', 'Layer Height', 'mm', 0.000001, 10000, 0.1, 0.2)

            groupCamCmdInput = tabSettingsChildInputs.addGroupCommandInput('cam', 'CAM Settings')
            groupCamCmdInput.isExpanded = True
            groupCamChildInputs = groupCamCmdInput.children

            # Create CAM inputs
            groupCamChildInputs.addIntegerSpinnerCommandInput('layerDropdown', 'Layer Dropdown', 0, 10000, 1, 1)
            groupCamChildInputs.addFloatSpinnerCommandInput('layerIntersect', 'Layer Intersect', 'mm', 0, 1, 0.1, 0.5)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the execute event.


class SetupExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        # Code to react to the event.
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('In command execute event handler.')
