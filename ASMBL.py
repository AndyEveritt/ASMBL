import adsk.core
import adsk.fusion
import traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


def create_tab(workspace, tab_name):
    pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # For this example, we are adding the already exisiting 'Extrude' command into a new panel:
        cmdDefinitions = ui.commandDefinitions

        # Get all workspaces:
        allWorkspaces = ui.workspaces

        # Get the CAM workspace:
        camWorkspace = allWorkspaces.itemById('CAMEnvironment')

        # Get all the tabs for the CAM workspace:
        allCamTabs = camWorkspace.toolbarTabs

        # Add a new tab to the CAM workspace:
        AsmblTab = allCamTabs.add('AsmblTab', 'ASMBL')

        # Get all of the toolbar panels for the NewCam tab:
        allAsmblTabPanels = AsmblTab.toolbarPanels

        # Activate the Cam Workspace before activating the newly added Tab
        camWorkspace.activate()

        asmblSetupPanel = None
        asmblSetupPanel = allAsmblTabPanels.itemById('asmblSetupPanelId')
        if asmblSetupPanel is None:
            # Add setup panel
            asmblSetupPanel = allAsmblTabPanels.add('asmblSetupPanelId', 'ASMBL Setup Panel')

        if asmblSetupPanel:
            # We want this panel to be visible:
            asmblSetupPanel.isVisible = True

            # Check if Setup Button exists
            setupButton = cmdDefinitions.itemById('SetupButtonID')

            if not setupButton:
                # Create a button command definition.
                setupButton = cmdDefinitions.addButtonDefinition(
                    'SetupButtonID', 'Setup Button', 'Create a new ASMBL setup')

            # Connect to the command created event.
            setupCreated = SetupCreatedEventHandler()
            setupButton.commandCreated.add(setupCreated)
            handlers.append(setupCreated)

            # Add setup button to ASMBL setup panel
            setupControl = asmblSetupPanel.controls.addCommand(setupButton)
        pass

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event.
class SetupCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Connect to the execute event.
        onExecute = SetupExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler for the execute event.
class SetupExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('In command execute event handler.')


# When the addin stops we need to clean up the ui
def stop(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        # Get all the toolbar panels
        allToolbarPanels = ui.allToolbarPanels

        # See if our cam panel still exists
        asmblSetupPanel = allToolbarPanels.itemById('asmblSetupPanelId')
        if asmblSetupPanel is not None:

            # Remove the controls we added to our panel
            for control in asmblSetupPanel.controls:
                if control.isValid:
                    control.deleteMe()

            # Remove our panel
            asmblSetupPanel.deleteMe()

        # Get all of the toolbar tabs
        allToolbarTabs = ui.allToolbarTabs

        # See if our render tab still exists
        AsmblTab = allToolbarTabs.itemById('AsmblTab')
        if asmblSetupPanel is not None:

            # Remove our render tab from the UI
            if AsmblTab.isValid:
                AsmblTab.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
