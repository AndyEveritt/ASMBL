import adsk.core
import adsk.fusion
import traceback

from .fusion_api import Handlers

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


def create_tab(workspace, tab_name):
    # Get all the tabs for the workspace:
    allTabs = workspace.toolbarTabs
    tabId = tab_name + 'TabId'

    # check if tab exists
    newTab = allTabs.itemById(tabId)

    if not newTab:
        # Add a new tab to the workspace:
        newTab = allTabs.add(tabId, tab_name)
    return newTab


def create_panel(workspace, tab, panel_name):
    # Get all of the toolbar panels for the NewCam tab:
    allTabPanels = tab.toolbarPanels

    # Activate the Cam Workspace before activating the newly added Tab
    workspace.activate()

    panel = None
    panel = allTabPanels.itemById(panel_name + 'PanelId')
    if panel is None:
        # Add setup panel
        panel = allTabPanels.add(panel_name + 'PanelId', panel_name)
    return panel


def create_button(workspace, tab, panel, button_name, CreatedEventHandler, tooltip=None):
    # We want this panel to be visible:
    workspace.activate()
    panel.isVisible = True

    app = adsk.core.Application.get()
    ui = app.userInterface
    cmdDefinitions = ui.commandDefinitions

    # Check if Setup Button exists
    buttonId = button_name + 'Id'
    button = cmdDefinitions.itemById(buttonId)
    if not tooltip:
        tooltip = button_name

    if not button:
        # Create a button command definition.
        button = cmdDefinitions.addButtonDefinition(
            buttonId, button_name, tooltip)

    # Connect to the command created event.
    newcommandCreated = CreatedEventHandler()
    button.commandCreated.add(newcommandCreated)
    handlers.append(newcommandCreated)

    # Add setup button to ASMBL setup panel
    panelControls = panel.controls
    buttonControl = panelControls.itemById(buttonId)
    if not buttonControl:
        buttonControl = panelControls.addCommand(button)
    return buttonControl


def remove_tab(workspace, tab_name):
    # Get all the tabs for the workspace:
    allTabs = workspace.toolbarTabs
    tabId = tab_name + 'TabId'

    # check if tab exists
    tab = allTabs.itemById(tabId)

    allTabPanels = tab.toolbarPanels

    if allTabPanels.count > 0:
        for panel in allTabPanels:

            # Remove the controls we added to our panel
            for control in panel.controls:
                if control.isValid:
                    control.deleteMe()

            # Remove our panel
            panel.deleteMe()

    # Remove our render tab from the UI
    if tab.isValid:
        tab.deleteMe()


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        cmdDefinitions = ui.commandDefinitions

        # Get all workspaces:
        allWorkspaces = ui.workspaces

        # Get the CAM workspace:
        camWorkspace = allWorkspaces.itemById('CAMEnvironment')

        AsmblTab = create_tab(camWorkspace, 'Asmbl')
        asmblSetupPanel = create_panel(camWorkspace, AsmblTab, 'Setup')
        setupControl = create_button(camWorkspace, AsmblTab, asmblSetupPanel,
                                     'setup', Handlers.SetupCreatedEventHandler)

        pass

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# When the addin stops we need to clean up the ui
def stop(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        # Get all workspaces:
        allWorkspaces = ui.workspaces

        # Get the CAM workspace:
        camWorkspace = allWorkspaces.itemById('CAMEnvironment')
        
        remove_tab(camWorkspace, 'Asmbl')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
