import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # For this example, we are adding the already exisiting 'Extrude' command into a new panel:
        cmdDefinitions = ui.commandDefinitions
        anotherExtrudeCmd = cmdDefinitions.itemById('Extrude')
                
        # For a few months, the customer might run either classic UI or tabbed toolbar UI.
        # Find out what is being used:
        runningTabbedToolbar = ui.isTabbedToolbarUI

        if runningTabbedToolbar:
            # Get all workspaces:
            allWorkspaces = ui.workspaces

            # Get the CAM workspace:
            camWorkspace = allWorkspaces.itemById('CAMEnvironment')
            if (camWorkspace):
                # Get all the tabs for the CAM workspace:
                allCamTabs = camWorkspace.toolbarTabs
                if (allCamTabs.count > 0):
                    # Add a new tab to the CAM workspace:
                    newCamTab = allCamTabs.add('NewCamTabHere', 'ASMBL')
                    if (newCamTab):
                        # Get all of the toolbar panels for the NewCam tab:
                        allNewCamTabPanels = newCamTab.toolbarPanels

                        # Has the panel been added already?
                        # You'll get an error if you try to add this more than once to the tab.

                        #Activate the Render Workspace before activating the newly added Tab
                        camWorkspace.activate()
                            
                        brandNewCamPanel = None
                        brandNewCamPanel = allNewCamTabPanels.itemById('bestCamPanelEverId')
                        if brandNewCamPanel is None:
                            # We have not added the panel already.  Go ahead and add it.
                            brandNewCamPanel = allNewCamTabPanels.add('bestCamPanelEverId', 'Best Cam Panel')

                        if brandNewCamPanel:
                            # We want this panel to be visible:
                            brandNewCamPanel.isVisible = True
                            # Access the controls that belong to the panel:
                            newPanelControls = brandNewCamPanel.controls

                            # Do we already have this command in the controls?  
                            # You'll get an error if you try to add it more than once to the panel:
                            extrudeCmdControl =  None
                            extrudeCmdControl = newPanelControls.itemById('Extrude')
                            if extrudeCmdControl is None:
                            
                            # Activate the newly added Tab in Render Workspace before adding commad to the Panel
                                if camWorkspace.isActive: 
                                    camTab = allCamTabs.itemById('NewCamTabHere')
                                    if not camTab.isActive :
                                        activationState = camTab.activate()
                                        if activationState :
                                            if anotherExtrudeCmd:
                                                # Go ahead and add the command to the panel:
                                                extrudeCmdControl = newPanelControls.addCommand(anotherExtrudeCmd)
                                                if extrudeCmdControl:
                                                    extrudeCmdControl.isVisible = True
                                                    extrudeCmdControl.isPromoted = True
                                                    extrudeCmdControl.isPromotedByDefault = True
                                                    ui.messageBox('Do you see Best Cam Panel now?')
                                            
                            else:
                                # If the command is already added to the Panel check if it is visible and display a message
                                if camWorkspace.isActive: 
                                    camTab = allCamTabs.itemById('NewCamTabHere')
                                    if not camTab.isActive :
                                        activationState = camTab.activate()
                                        if activationState :
                                            if brandNewCamPanel.isVisible:
                                                ui.messageBox('Do you see Best Cam Panel now?')     
                                            else:
                                                totalControlsInPanel = newPanelControls.count
                                                if (totalControlsInPanel == 1):
                                                    if extrudeCmdControl.isVisible:
                                                        ui.messageBox('Not visible control')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
			
# When the addin stops we need to clean up the ui
def stop(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        # Get all the toolbar panels
        allToolbarPanels = ui.allToolbarPanels

        # See if our cam panel still exists
        brandNewCamPanel = allToolbarPanels.itemById('bestCamPanelEverId')
        if brandNewCamPanel is not None:

            # Remove the controls we added to our panel
            for control in brandNewCamPanel.controls:
                if control.isValid:
                    control.deleteMe()

            # Remove our panel
            brandNewCamPanel.deleteMe()

        # Get all of the toolbar tabs
        allToolbarTabs = ui.allToolbarTabs

        # See if our render tab still exists
        newCamTab = allToolbarTabs.itemById('NewCamTabHere')
        if brandNewCamPanel is not None:

            # Remove our render tab from the UI
            if newCamTab.isValid:
                newCamTab.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))