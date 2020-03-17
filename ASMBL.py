#Author-AndyEveritt
#Description-Additive and Subtractive Manufacturing By Layer

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the application.
        app = adsk.core.Application.get()

        # Get the active document.
        doc = app.activeDocument

        # Get the products collection on the active document.
        products = doc.products

        # Get the CAM product.
        product = products.itemByProductType('CAMProductType')

        # Check if the document has a CAMProductType. It will not if there are no CAM operations in it.
        if product == None:
            ui.messageBox('There are no CAM operations in the active document')
            return

        # Cast the CAM product to a CAM object (a subtype of product).
        cam = adsk.cam.CAM.cast(product)

        operations = cam.allOperations

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        ui.messageBox('Stop addin')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
