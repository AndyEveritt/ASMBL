from math import ceil

import re


class Simplify3DGcodeLayer:
    def __init__(self, gcode, name=None, layer_height=None):
        self.gcode = gcode
        self.name = name
        self.layer_height = layer_height

        if name is None:
            self.name = self.get_name(self.gcode)

        if layer_height is None:
            self.layer_height = self.get_layer_height(self.gcode)

    def get_name(self, gcode):
        return gcode.split(',')[0][2:]

    def get_layer_height(self, gcode):
        return gcode.split('\n')[0][15:]


class CamGcodeLine:
    def __init__(self, gcode, name=None):
        self.gcode = gcode
        self.name = name
        self.layer_height = self.get_layer_height(self.gcode)

    def get_layer_height(self, gcode):
        return float(gcode.split('Z')[1].split(' ')[0])


class CamGcodeLayer:
    def __init__(self):
        self.initiate_at = None  # height to print to before running the operation
        self.operations = []


class Parser:
    def __init__(self, gcode_add, gcode_sub):
        self.gcode_add = gcode_add
        self.gcode_sub = gcode_sub

        self.split_additive_layers(self.gcode_add)
        self.split_cam_layers(self.gcode_sub)

    def split_additive_layers(self, gcode_add):
        """ Takes Simplify3D gcode and splits in by layer """
        tmp_list = re.split('(; layer)', gcode_add)

        gcode_add_layers = []
        gcode_add_layers.append(Simplify3DGcodeLayer(
            tmp_list[0],
            name="initialise",
            layer_height=0,
        ))    # slicer settings & initialise

        for i in range(ceil(len(tmp_list)/2)):
            if i == 0:
                continue

            layer = tmp_list[2*i-1] + tmp_list[2*i]
            name = layer.split(',')[0][2:]

            if 2*i == len(tmp_list) - 1:
                gcode_add_layers.append(Simplify3DGcodeLayer(
                    layer, 'end', gcode_add_layers[-1].layer_height))
                continue

            gcode_add_layers.append(Simplify3DGcodeLayer(layer))

        self.gcode_add_layers = gcode_add_layers

    def split_cam_layers(self, gcode_sub):
        """ Takes fusion360 CAM gcode and splits the operations by execution height """
        tmp_operation_list = gcode_sub.split('\n\n')

        operations = []

        for i, operation in enumerate(tmp_operation_list):
            if i == 0:  # ignore setup gcode
                continue

            lines = operation.split('\n')
            name = lines.pop(0)
            lines.reverse() # required since printing is bottom up, but CAM is top down
            lines = [line for line in lines if line != '']

            for index, line in enumerate(lines):
                lines[index] = CamGcodeLine(line, name)

    def merge_gcode(self, gcode_add, cam_instructions):
        """ Takes the individual CAM instructions and merges them into the additive file from Simplify3D """
        pass

    def create_output_file(self, file):
        """ Saves the file to the output folder """
        pass


if __name__ == "__main__":
    gcode_add_file = open("gcode/additive_box.gcode", "r")
    gcode_add = gcode_add_file.read()

    gcode_sub_file = open("gcode/double_box_side_top_no_arc.nc", "r")
    gcode_sub = gcode_sub_file.read()

    parser = Parser(gcode_add, gcode_sub)
    pass
