from math import ceil

import re


class GcodeLayer:
    def __init__(self, name, gcode):
        self.name = name
        self.gcode = gcode

        self.layer_height = self.get_initial_height(self.gcode)

    def get_initial_height(self, gcode):
        return None


class Parser:

    def __init__(self, gcode_add, gcode_sub):
        self.gcode_add = gcode_add
        self.gcode_sub = gcode_sub

        self.split_additive_layers(self.gcode_add)

    def split_additive_layers(self, gcode_add):
        """ Takes Simplify3D gcode and splits in by layer """
        tmp_list = re.split('(; layer)', gcode_add)
        gcode_add_layers = [{
            "name": "initialise",
            "gcode": tmp_list[0],
            "layer_height": 0,
        }]  # slicer settings & initialise

        for i in range(ceil(len(tmp_list)/2)):
            if i == 0:
                continue

            layer = tmp_list[2*i-1] + tmp_list[2*i]

            gcode_add_layers.append({
                "name": layer.split(',')[0][2:],
                "gcode": layer,
                "layer_height": layer.split('\n')[0][15:],
            })

        self.gcode_add_layers = gcode_add_layers

    def split_cam_layers(self, gcode_sub):
        """ Takes fusion360 CAM gcode and splits the operations by execution height """
        pass

    def merge_gcode(self, gcode_add, cam_instructions):
        """ Takes the individual CAM instructions and merges them into the additive file from Simplify3D """
        pass

    def create_output_file(self, file):
        """ Saves the file to the output folder """
        pass


if __name__ == "__main__":
    gcode_add_file = open("additive_box.gcode", "r")
    gcode_add = gcode_add_file.read()

    gcode_sub_file = open("double_box_side_top_no_arc.nc", "r")
    gcode_sub = gcode_sub_file.read()

    parser = Parser(gcode_add, gcode_sub)
    pass
