import adsk.core
import adsk.fusion
import traceback

from .src.fusion_api import Handlers
from .src.fusion_api.Handlers import handlers


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


def create_button(workspace, tab, panel, button_name, CreatedEventHandler, tooltip=None, resources=''):
    # We want this panel to be visible:
    workspace.activate()

    app = adsk.core.Application.get()
    ui = app.userInterface
    cmdDefinitions = ui.commandDefinitions

    # Check if Setup Button exists
    buttonId = button_name.replace(' ', '') + 'Id'
    button = cmdDefinitions.itemById(buttonId)
    if not tooltip:
        tooltip = button_name

    if not button:
        # Create a button command definition.
        button = cmdDefinitions.addButtonDefinition(
            buttonId, button_name, tooltip, resources)

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


def remove_pannel(tab, panel_name):
    # Get all the tabs for the workspace:
    panelId = panel_name + 'PanelId'

    # check if tab exists
    panel = tab.toolbarPanels.itemById(panelId)

    # Remove the controls we added to our panel
    for control in panel.controls:
        if control.isValid:
            control.deleteMe()

    # Remove our panel
    panel.deleteMe()


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
        # asmblSetupPanel = create_panel(camWorkspace, AsmblTab, 'Setup')
        
        asmblActionsPanel = create_panel(camWorkspace, AsmblTab, 'Actions')

        # asmbl post process button
        asmblPostProcessControl = create_button(camWorkspace, AsmblTab, asmblActionsPanel,
                                     'Generate ASMBL Script', Handlers.PostProcessCreatedEventHandler,
                                     tooltip='Generate combined gcode file for ASMBL',
                                     resources='./resources/GenerateAsmbl')
        asmblPostProcessControl.isPromotedByDefault = True
        asmblPostProcessControl.isPromoted = True
        asmblPostProcessControl.commandDefinition.tooltipDescription = '\
            <br>Requires an FFF setup and a milling setup</br>\
            <br>Will not work if there are any more/fewer setups</br>'
        asmblPostProcessControl.commandDefinition.toolClipFilename = 'resources/GenerateAsmbl/tooltip.png'
            
        # cam post process button
        camPostProcessControl = create_button(camWorkspace, AsmblTab, asmblActionsPanel,
                                     'Post Process CAM', Handlers.PostProcessCamCreatedEventHandler,
                                     tooltip='Generate subtractive gcode file for ASMBL',
                                     resources='./resources/PostProcess')
        camPostProcessControl.isPromotedByDefault = False
        camPostProcessControl.isPromoted = False
        camPostProcessControl.commandDefinition.tooltipDescription = '\
            <br>Post process all unsuppressed milling setups for the standalone ASMBL program</br>'

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
        
        allTabs = camWorkspace.toolbarTabs

        # check if tab exists
        tab = allTabs.itemById('AsmblTabId')

        # remove_pannel(tab, 'Setup')
        remove_pannel(tab, 'Actions')

        # Remove our render tab from the UI
        if tab.isValid:
            tab.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
