from pathlib import Path
import adsk.core
import adsk.fusion
import traceback
import time
import os

from ..ASMBL_parser import Parser

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
    message = '<br>Please do not press OK until the Additive toolpath has finished.</br>\
        <br>The toolpaths for all cam operations in the document have been generated.</br>'

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


def get_setups(ui, cam):
    if not cam:
        ui.messageBox('No CAM data exists in the active document.')
        return

    # verify there are operations
    if cam.allOperations.count == 0:
        ui.messageBox('No CAM operations exist in the active document.')
        return

    # Verify that there are any setups.
    setups = [setup for setup in cam.setups if not setup.isSuppressed]

    return setups


def remove_old_file(path, file_name):
    file_path = os.path.join(path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    # ensure file deleted
    while os.path.exists(file_path):
        pass


def postToolpaths(ui, cam, viewResult):
    # get any unsuppressed setups.
    setups = get_setups(ui, cam)

    setupsCount = len(setups)
    if setupsCount < 2:
        ui.messageBox('Missing setups, requires an additive & milling setup to work')
        return
    if setupsCount > 2:
        ui.messageBox('Too many setups, requires an additive & milling setup to work')
        return

    outputFolder = cam.temporaryFolder

    # specify the NC file output units
    units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput

    for setup in setups:
        setupOperationType = None
        # verify there are operations in setup
        if setup.operations.count == 0:
            ui.messageBox('No CAM operations exist in {}.'.format(setup.name))
            return

        try:
            setupOperationType = setup.operationType
        except:
            pass  # there is a bug in Fusion as of writing that means Additive setups don't have an operation type

        if setupOperationType == adsk.cam.OperationTypes.MillingOperation:
            programName = 'tmpSubtractive'
            postConfig = os.path.join(Path(__file__).parents[2], 'post_processors', 'asmbl_cam.cps')

            # create the postInput object
            postInput = adsk.cam.PostProcessInput.create(programName, postConfig, outputFolder, units)
            postInput.isOpenInEditor = viewResult

            cam.postProcess(setup, postInput)

        elif setupOperationType == None:
            programName = 'tmpAdditive'
            postConfig = os.path.join(Path(__file__).parents[2], 'post_processors', 'asmbl_fff.cps')

            # create the postInput object
            postInput = adsk.cam.PostProcessInput.create(programName, postConfig, outputFolder, units)
            postInput.isOpenInEditor = viewResult

            cam.postProcess(setup, postInput)

    # open the output folder in Finder on Mac or in Explorer on Windows
    if viewResult:
        if (os.name == 'posix'):
            os.system('open "%s"' % outputFolder)
        elif (os.name == 'nt'):
            os.startfile(outputFolder)


def postCamToolpath(ui, cam, setup, units, output_folder, part_name):
    setup_operation_type = None
    # verify there are operations in setup
    if setup.operations.count == 0:
        ui.messageBox('No CAM operations exist in {}.'.format(setup.name))
        return

    try:
        setup_operation_type = setup.operationType
    except:
        pass  # there is a bug in Fusion as of writing that means Additive setups don't have an operation type

    if setup_operation_type == adsk.cam.OperationTypes.MillingOperation:
        # remove old files
        programName = part_name + '_' + setup.name
        remove_old_file(output_folder, programName)

        # get post processor
        postConfig = os.path.join(Path(__file__).parents[2], 'post_processors', 'asmbl_cam.cps')

        # create the postInput object
        postInput = adsk.cam.PostProcessInput.create(programName, postConfig, output_folder, units)

        cam.postProcess(setup, postInput)

        start = time.time()
        file_path = os.path.join(output_folder, programName + '.gcode')
        while not os.path.exists(file_path):
            if time.time() > start + 10:
                ui.messageBox('Posting timed out')
                return
            pass    # wait until files exist

        checkpoint = time.time()
        while True:
            if time.time() > checkpoint + 10:
                ui.messageBox('Permission Error timed out')
                return
            try:
                open(file_path)
                break
            except PermissionError:
                continue


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class PostProcessCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Connect to the execute event.
            onExecute = PostProcessExecuteHandler()
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
            generateToolpathsInput = tabSettingsChildInputs.addBoolValueInput(
                'generateToolpaths', 'Generate Toolpaths', True, '', False)
            generateToolpathsInput.tooltip = 'Regenerated all toolpaths.'

            viewIntermediateFilesInput = tabSettingsChildInputs.addBoolValueInput(
                'viewIntermediateFiles', 'View Intermediate Files', True, '', False)
            viewIntermediateFilesInput.tooltip = 'Pre-merged gcode files will be opened in your default txt editor.'

            # Create an editable textbox input.
            tabSettingsChildInputs.addTextBoxCommandInput('outputName', 'Output File Name', '1001', 1, False)

            # groupPrintCmdInput = tabSettingsChildInputs.addGroupCommandInput('print', 'Print Settings')
            # groupPrintCmdInput.isExpanded = True
            # groupPrintChildInputs = groupPrintCmdInput.children

            groupCamCmdInput = tabSettingsChildInputs.addGroupCommandInput('cam', 'CAM Settings')
            groupCamCmdInput.isExpanded = True
            groupCamChildInputs = groupCamCmdInput.children

            # Create CAM inputs
            layerOverlapInput = groupCamChildInputs.addIntegerSpinnerCommandInput(
                'layerOverlap', 'Layer Overlap', 0, 10000, 1, 1)
            layerOverlapInput.tooltip = 'How many layers each cutting segment should be delayed by before executing'
            layerOverlapInput.tooltipDescription = '\
                <br>This does <b>NOT</b> alter the toolpath, only when it happens</br>\
                <br></br>\
                <br>This parameter value will delay when a cutting segment is merged into the additive gcode by <code>x</code> layers</br>\
                <br>This will cause the cutter to overlap with <code>x</code> previously cut layers</br>\
                <br></br>\
                <br>A higher value generally makes for a better finish as it uses the side of the cutter instead of the tip, \
                however this is not always possible depending on the geometry.</br>\
                <br>Limited by cutter length</br>'
            layerOverlapInput.toolClipFilename = os.path.join(
                Path(__file__).parents[2], 'resources', 'GenerateAsmbl', 'tooltip_overlap.png')

            layerDropdownInput = groupCamChildInputs.addFloatSpinnerCommandInput(
                'layerDropdown', 'Layer Dropdown', 'mm', 0, 1, 0.1, 0)
            layerDropdownInput.tooltip = 'Controls how much the cutting tip should be lowered on a global level'
            layerDropdownInput.tooltipDescription = '\
                <br>This shifts the entire subtractive toolpath down by this amount</br>\
                <br></br>\
                <br>This does not effect when the cutting operation will happen.\
                <br></br>\
                <br>Set this to 0 mm for accurate parts in the z axis.\
                Setting it equal to half a layer height can create smoother cut surfaces</br>'
            layerDropdownInput.toolClipFilename = os.path.join(
                Path(__file__).parents[2], 'resources', 'GenerateAsmbl', 'tooltip_dropdown.png')

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the execute event.


class PostProcessExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface

        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        generateToolpaths = inputs.itemById('generateToolpaths').value
        viewIntermediateFiles = inputs.itemById('viewIntermediateFiles').value
        layerOverlap = inputs.itemById('layerOverlap').value
        layerDropdown = inputs.itemById('layerDropdown').value
        outputName = inputs.itemById('outputName').text

        doc = app.activeDocument
        products = doc.products
        product = products.itemByProductType('CAMProductType')
        cam = adsk.cam.CAM.cast(product)

        if generateToolpaths:
            try:
                generateAllTootpaths(ui, cam)
            except:
                ui.messageBox('Failed generating toolpaths:\n{}'.format(traceback.format_exc()))
                return

        #  create and show the progress dialog for remainder of process.
        progress = ui.createProgressDialog()
        progress.isCancelButtonShown = False
        progress.show('ASMBL Code Generation', 'Posting Toolpaths', 0, 7)

        outputFolder = cam.temporaryFolder
        tmpAdditive = os.path.join(outputFolder, 'tmpAdditive.gcode')
        tmpSubtractive = os.path.join(outputFolder, 'tmpSubtractive.gcode')

        # remove old files
        if os.path.exists(tmpAdditive):
            os.remove(tmpAdditive)
        if os.path.exists(tmpSubtractive):
            os.remove(tmpSubtractive)

        try:
            start = time.time()
            postToolpaths(ui, cam, viewIntermediateFiles)
            while not (os.path.exists(tmpAdditive) and os.path.exists(tmpSubtractive)):
                if time.time() > start + 10:
                    ui.messageBox('Posting timed out')
                    return
                pass    # wait until files exist
            checkpoint = time.time()
            while True:
                if time.time() > checkpoint + 10:
                    ui.messageBox('Permission Error timed out')
                    return
                try:
                    open(tmpAdditive)
                    open(tmpSubtractive)
                    break
                except PermissionError:
                    continue
        except:
            ui.messageBox('Failed posting toolpaths:\n{}'.format(traceback.format_exc()))
            return

        config = {
            "InputFiles": {
                "additive_gcode": tmpAdditive,
                "subtractive_gcode": tmpSubtractive
            },
            "Printer": {
                "bed_centre_x": 0,  # alignment is done in Fusion so does not matter here (set to 0)
                "bed_centre_y": 0
            },
            "PrintSettings": {
                "raft_height": 0   # alignment is done in Fusion
            },
            "CamSettings": {
                "layer_overlap": layerOverlap,
                "layer_dropdown": layerDropdown
            },
            "OutputSettings": {
                "filename": outputName
            }
        }
        # ui.messageBox(config.__str__())

        try:
            asmbl_parser = Parser(config, progress)

            outputFolder = os.path.expanduser('~/Asmbl/output/')
            asmbl_parser.create_output_file(asmbl_parser.merged_gcode_script, outputFolder)

            if (os.name == 'posix'):
                os.system('open "%s"' % outputFolder)
            elif (os.name == 'nt'):
                os.startfile(outputFolder)
        except:
            ui.messageBox('Failed combing gcode files:\n{}'.format(traceback.format_exc()))
            return

        ui.messageBox('ASMBL gcode has been successfully created. File saved in \'~/Asmbl/output/\'')


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class PostProcessCamCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Connect to the execute event.
            onExecute = PostProcessCamExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create settings tab inputs
            tabCmdInputSettings = inputs.addTabCommandInput('settings', 'Settings')
            tabSettingsChildInputs = tabCmdInputSettings.children

            # Create bool value input to check whether you should generate toolpaths.
            generateToolpathsInput = tabSettingsChildInputs.addBoolValueInput(
                'generateToolpaths', 'Generate Toolpaths', True, '', False)
            generateToolpathsInput.tooltip = 'Regenerated all toolpaths.'

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class PostProcessCamExecuteHandler(adsk.core.CommandEventHandler):
    # Event handler for the execute event.
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface

        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        generateToolpaths = inputs.itemById('generateToolpaths').value

        doc = app.activeDocument
        products = doc.products
        product = products.itemByProductType('CAMProductType')
        cam = adsk.cam.CAM.cast(product)

        if generateToolpaths:
            try:
                generateAllTootpaths(ui, cam)
            except:
                ui.messageBox('Failed generating toolpaths:\n{}'.format(traceback.format_exc()))
                return

        try:
            output_folder = os.path.expanduser('~/Asmbl/output/standalone/')

            # get any unsuppressed setups.
            setups = get_setups(ui, cam)

            # specify the NC file output units
            units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput

            # find part name
            part_name = doc.name

            for setup in setups:
                postCamToolpath(ui, cam, setup, units, output_folder, part_name)

        except:
            ui.messageBox('Failed posting toolpaths:\n{}'.format(traceback.format_exc()))
            return

        if (os.name == 'posix'):
            os.system('open "%s"' % output_folder)
        elif (os.name == 'nt'):
            os.startfile(output_folder)

        ui.messageBox('Milling Setup Post Processing Complete.\nFile saved in \'{}\''.format(output_folder))
