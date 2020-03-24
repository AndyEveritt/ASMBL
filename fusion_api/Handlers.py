import adsk.core
import adsk.fusion
import traceback
import time
import os

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


def generateAllTootpaths(ui, cam):
    # Check CAM data exists.
    if not cam:
        ui.messageBox('No CAM data exists in the active document.')
        return

    # Verify that there are any setups.
    if cam.allOperations.count == 0:
        ui.messageBox('No CAM operations exist in the active document.')
        return

    # Generate all toolpaths
    future = cam.generateAllToolpaths(False)
    message = 'The toolpaths for all operations in the document have been generated.'

    numOps = future.numberOfOperations

    #  create and show the progress dialog while the toolpaths are being generated.
    progress = ui.createProgressDialog()
    progress.isCancelButtonShown = False
    progress.show('Toolpath Generation Progress', 'Generating Toolpaths', 0, 10)

    # Enter a loop to wait while the toolpaths are being generated and update
    # the progress dialog.
    while not future.isGenerationCompleted:
        # since toolpaths are calculated in parallel, loop the progress bar while the toolpaths
        # are being generated but none are yet complete.
        n = 0
        start = time.time()
        while future.numberOfCompleted == 0:
            if time.time() - start > .125:  # increment the progess value every .125 seconds.
                start = time.time()
                n += 1
                progress.progressValue = n
                adsk.doEvents()
            if n > 10:
                n = 0

        # The first toolpath has finished computing so now display better
        # information in the progress dialog.

        # set the progress bar value to the number of completed toolpaths
        progress.progressValue = future.numberOfCompleted

        # set the progress bar max to the number of operations to be completed.
        progress.maximumValue = numOps

        # set the message for the progress dialog to track the progress value and the total number of operations to be completed.
        progress.message = 'Generating %v of %m' + ' Toolpaths'
        adsk.doEvents()

    progress.hide()
    ui.messageBox(message)


def postToolpaths(ui, cam):
    # Check CAM data exists.
    if not cam:
        ui.messageBox('No CAM data exists in the active document.')
        return

    # Verify that there are any setups.
    if cam.allOperations.count == 0:
        ui.messageBox('No CAM operations exist in the active document.')
        return
    
    setupsCount = cam.setups.count
    if setupsCount < 2:
        ui.messageBox('Only 1 setup, requires an additive & milling setup to work')
        return
    if setupsCount > 2:
        ui.messageBox('Too many setups, requires an additive & milling setup to work')
        return
    
    outputFolder = cam.temporaryFolder

    # specify the NC file output units
    units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput

    # prompt the user with an option to view the resulting NC file.
    viewResults = ui.messageBox('View results when post is complete?', 'Post NC Files',
                                adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                                adsk.core.MessageBoxIconTypes.QuestionIconType)
    if viewResults == adsk.core.DialogResults.DialogNo:
        viewResult = False
    else:
        viewResult = True

    for i in range(setupsCount):
        setup = cam.setups.item(i)
        setupOperationType = None
        try:
            setupOperationType = setup.operationType
        except:
            pass # there is a bug in Fusion as of writing that means Additive setups don't have an operation type

        if setupOperationType == adsk.cam.OperationTypes.MillingOperation:
            programName = 'tmpSubtractive'
            postConfig = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'post_processors', 'asmbl_cam.cps')

            # create the postInput object
            postInput = adsk.cam.PostProcessInput.create(programName, postConfig, outputFolder, units)
            postInput.isOpenInEditor = viewResult

            cam.postProcess(setup, postInput)
        
        elif setupOperationType == None:
            programName = 'tmpAdditive'
            postConfig = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'post_processors', 'asmbl_fff.cps')

            # create the postInput object
            postInput = adsk.cam.PostProcessInput.create(programName, postConfig, outputFolder, units)
            postInput.isOpenInEditor = viewResult

            cam.postProcess(setup, postInput)
        
    # open the output folder in Finder on Mac or in Explorer on Windows
    if (os.name == 'posix'):
        os.system('open "%s"' % outputFolder)
    elif (os.name == 'nt'):
        os.startfile(outputFolder)


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

            # # Create setup tab input.
            # tabCmdInputSetup = inputs.addTabCommandInput('setup', 'Setup')
            # tabSetupChildInputs = tabCmdInputSetup.children

            # # Create input setups group.
            # groupSetupCmdInput = tabSetupChildInputs.addGroupCommandInput('inputSetups', 'Input Setups')
            # groupSetupCmdInput.isExpanded = True
            # groupSetupChildInputs = groupSetupCmdInput.children

            # # Create selection inputs for setups.
            # additiveSetup = groupSetupChildInputs.addSelectionInput(
            #     'additiveSetup', 'Additive Setup', 'Select the additive setup')
            # additiveSetup.setSelectionLimits(1)

            # camSetup = groupSetupChildInputs.addSelectionInput('camSetup', 'CAM Setup', 'Select the milling setup')
            # camSetup.setSelectionLimits(1)

            # Create settings tab inputs
            tabCmdInputSettings = inputs.addTabCommandInput('settings', 'Settings')
            tabSettingsChildInputs = tabCmdInputSettings.children

            # Create bool value input to check whether you should generate toolpaths.
            tabSettingsChildInputs.addBoolValueInput('generateToolpaths', 'Generate Toolpaths', True, '', False)

            groupPrintCmdInput = tabSettingsChildInputs.addGroupCommandInput('print', 'Print Settings')
            groupPrintCmdInput.isExpanded = True
            groupPrintChildInputs = groupPrintCmdInput.children

            # Create print inputs
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
        app = adsk.core.Application.get()
        ui = app.userInterface

        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        generateToolpaths = inputs.itemById('generateToolpaths').value
        layerHeight = inputs.itemById('layerHeight').value
        layerDropdown = inputs.itemById('layerDropdown').value
        layerIntersect = inputs.itemById('layerIntersect').value

        doc = app.activeDocument
        products = doc.products
        product = products.itemByProductType('CAMProductType')
        cam = adsk.cam.CAM.cast(product)

        if generateToolpaths:
            generateAllTootpaths(ui, cam)
        
        postToolpaths(ui, cam)

        config = {
            "InputFiles": {
                "additive_gcode": "gcode/box/box.gcode",
                "subtractive_gcode": "gcode/box/tmp.nc"
            },
            "Printer": {
                "bed_centre_x": 0,  # alignment is done in Fusion so does not matter here (set to 0)
                "bed_centre_y": 0
            },
            "PrintSettings": {
                "raft_height": 0,   # alignment is done in Fusion
                "layer_height": layerHeight
            },
            "CamSettings": {
                "layer_dropdown": layerDropdown,
                "layer_intersect": layerIntersect
            },
            "OutputSettings": {
                "filename": "tmp"
            }
        }

        # Code to react to the event.
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('In command execute event handler.')
