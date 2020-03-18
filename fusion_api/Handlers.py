import adsk.core
import adsk.fusion
import traceback


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
