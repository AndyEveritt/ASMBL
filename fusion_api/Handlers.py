import adsk.core
import adsk.fusion
import traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

# Event handler for the commandCreated event.


class SetupCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.
        inputs = cmd.commandInputs

        # Create a check box to get if it should be an equilateral triangle or not.
        equilateral = inputs.addBoolValueInput('equilateral', 'Equilateral',
                                               True, '', False)

        # Create the slider to get the base length, setting the range of the slider to
        # be 1 to 10 of whatever the current document unit is.
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
        minVal = des.unitsManager.convert(1, des.unitsManager.defaultLengthUnits, 'cm')
        maxVal = des.unitsManager.convert(10, des.unitsManager.defaultLengthUnits, 'cm')
        baseLength = inputs.addFloatSliderCommandInput('baseLength',
                                                       'Base Length',
                                                       des.unitsManager.defaultLengthUnits,
                                                       minVal, maxVal, False)

        # Create the value input to get the height scale.
        heightScale = inputs.addValueInput('heightScale', 'Height Scale',
                                           '', adsk.core.ValueInput.createByReal(0.75))

        # Connect to the execute event.
        onExecute = SetupExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create a tab input.
            tabCmdInput1 = inputs.addTabCommandInput('tab_1', 'Tab 1')
            tab1ChildInputs = tabCmdInput1.children

            # Create a read only textbox input.
            tab1ChildInputs.addTextBoxCommandInput(
                'readonly_textBox', 'Text Box 1', 'This is an example of a read-only text box.', 2, True)

            # Create an editable textbox input.
            tab1ChildInputs.addTextBoxCommandInput(
                'writable_textBox', 'Text Box 2', 'This is an example of an editable text box.', 2, False)

            # Create a message that spans the entire width of the dialog by leaving out the "name" argument.
            message = '<div align="center">A "full width" message using <a href="http:fusion360.autodesk.com">html.</a></div>'
            tab1ChildInputs.addTextBoxCommandInput('fullWidth_textBox', '', message, 1, True)

            # Create a selection input.
            selectionInput = tab1ChildInputs.addSelectionInput('selection', 'Select', 'Basic select command input')
            selectionInput.setSelectionLimits(0)

            # Create a string value input.
            strInput = tab1ChildInputs.addStringValueInput('string', 'Text', 'Basic string command input')

            # Create value input.
            tab1ChildInputs.addValueInput('value', 'Value', 'cm', adsk.core.ValueInput.createByReal(0.0))

            # Create bool value input with checkbox style.
            tab1ChildInputs.addBoolValueInput('checkbox', 'Checkbox', True, '', False)

            # Create bool value input with button style that can be clicked.
            tab1ChildInputs.addBoolValueInput('buttonClick', 'Click Button', False, 'resources/button', True)

            # Create bool value input with button style that has a state.
            tab1ChildInputs.addBoolValueInput('buttonState', 'State Button', True, 'resources/button', True)

            # Create float slider input with two sliders.
            tab1ChildInputs.addFloatSliderCommandInput('floatSlider', 'Float Slider', 'cm', 0, 10.0, True)

            # Create float slider input with two sliders and a value list.
            floatValueList = [1.0, 3.0, 4.0, 7.0]
            tab1ChildInputs.addFloatSliderListCommandInput('floatSlider2', 'Float Slider 2', 'cm', floatValueList)

            # Create float slider input with two sliders and visible texts.
            floatSlider3 = tab1ChildInputs.addFloatSliderCommandInput(
                'floatSlider3', 'Float Slider 3', '', 0, 50.0, False)
            floatSlider3.setText('Min', 'Max')

            # Create integer slider input with one slider.
            tab1ChildInputs.addIntegerSliderCommandInput('intSlider', 'Integer Slider', 0, 10)
            valueList = [1, 3, 4, 7, 11]

            # Create integer slider input with two sliders and a value list.
            tab1ChildInputs.addIntegerSliderListCommandInput('intSlider2', 'Integer Slider 2', valueList)

            # Create float spinner input.
            tab1ChildInputs.addFloatSpinnerCommandInput('spinnerFloat', 'Float Spinner', 'cm', 0.2, 9.0, 2.2, 1)

            # Create integer spinner input.
            tab1ChildInputs.addIntegerSpinnerCommandInput('spinnerInt', 'Integer Spinner', 2, 9, 2, 3)

            # Create dropdown input with checkbox style.
            dropdownInput = tab1ChildInputs.addDropDownCommandInput(
                'dropdown', 'Dropdown 1', adsk.core.DropDownStyles.CheckBoxDropDownStyle)
            dropdownItems = dropdownInput.listItems
            dropdownItems.add('Item 1', False, 'resources/One')
            dropdownItems.add('Item 2', False, 'resources/Two')

            # Create dropdown input with icon style.
            dropdownInput2 = tab1ChildInputs.addDropDownCommandInput(
                'dropdown2', 'Dropdown 2', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            dropdown2Items = dropdownInput2.listItems
            dropdown2Items.add('Item 1', True, 'resources/One')
            dropdown2Items.add('Item 2', False, 'resources/Two')

            # Create dropdown input with radio style.
            dropdownInput3 = tab1ChildInputs.addDropDownCommandInput(
                'dropdown3', 'Dropdown 3', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            dropdown3Items = dropdownInput3.listItems
            dropdown3Items.add('Item 1', True, '')
            dropdown3Items.add('Item 2', False, '')

            # Create dropdown input with test list style.
            dropdownInput4 = tab1ChildInputs.addDropDownCommandInput(
                'dropdown4', 'Dropdown 4', adsk.core.DropDownStyles.TextListDropDownStyle)
            dropdown4Items = dropdownInput4.listItems
            dropdown4Items.add('Item 1', True, '')
            dropdown4Items.add('Item 2', False, '')

            # Create single selectable button row input.
            buttonRowInput = tab1ChildInputs.addButtonRowCommandInput('buttonRow', 'Single Select Buttons', False)
            buttonRowInput.listItems.add('Item 1', False, 'resources/One')
            buttonRowInput.listItems.add('Item 2', False, 'resources/Two')

            # Create multi selectable button row input.
            buttonRowInput2 = tab1ChildInputs.addButtonRowCommandInput('buttonRow2', 'Multi-select Buttons', True)
            buttonRowInput2.listItems.add('Item 1', False, 'resources/One')
            buttonRowInput2.listItems.add('Item 2', False, 'resources/Two')

            # Create tab input 2
            tabCmdInput2 = inputs.addTabCommandInput('tab_2', 'Tab 2')
            tab2ChildInputs = tabCmdInput2.children

            # Create group input.
            groupCmdInput = tab2ChildInputs.addGroupCommandInput('group', 'Group')
            groupCmdInput.isExpanded = True
            groupCmdInput.isEnabledCheckBoxDisplayed = True
            groupChildInputs = groupCmdInput.children

            # Create radio button group input.
            radioButtonGroup = groupChildInputs.addRadioButtonGroupCommandInput(
                'radioButtonGroup', 'Radio button group')
            radioButtonItems = radioButtonGroup.listItems
            radioButtonItems.add("Item 1", False)
            radioButtonItems.add("Item 2", False)
            radioButtonItems.add("Item 3", False)

            # Create image input.
            groupChildInputs.addImageCommandInput('image', 'Image', "resources/image.png")

            # Create direction input 1.
            directionCmdInput = tab2ChildInputs.addDirectionCommandInput('direction', 'Direction1')
            directionCmdInput.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(1, 0, 0))

            # Create direction input 2.
            directionCmdInput2 = tab2ChildInputs.addDirectionCommandInput('direction2', 'Direction 2', 'resources/One')
            directionCmdInput2.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(0, 1, 0))
            directionCmdInput2.isDirectionFlipped = True

            # Create distance value input 1.
            distanceValueInput = tab2ChildInputs.addDistanceValueCommandInput(
                'distanceValue', 'DistanceValue', adsk.core.ValueInput.createByReal(2))
            distanceValueInput.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(1, 0, 0))
            distanceValueInput.minimumValue = 0
            distanceValueInput.isMinimumValueInclusive = True
            distanceValueInput.maximumValue = 10
            distanceValueInput.isMaximumValueInclusive = True

            # Create distance value input 2.
            distanceValueInput2 = tab2ChildInputs.addDistanceValueCommandInput(
                'distanceValue2', 'DistanceValue 2', adsk.core.ValueInput.createByReal(1))
            distanceValueInput2.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(0, 1, 0))
            distanceValueInput2.expression = '1 in'
            distanceValueInput2.hasMinimumValue = False
            distanceValueInput2.hasMaximumValue = False

            # Create angle value input.
            angleValueInput = tab2ChildInputs.addAngleValueCommandInput(
                'angleValue', 'AngleValue', adsk.core.ValueInput.createByString('30 degree'))
            angleValueInput.setManipulator(adsk.core.Point3D.create(
                0, 0, 0), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 0, 1))
            angleValueInput.hasMinimumValue = False
            angleValueInput.hasMaximumValue = False
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

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
