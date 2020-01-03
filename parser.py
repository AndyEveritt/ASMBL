from math import (
    inf,
    ceil,
)

import re


class Simplify3DGcodeLayer:
    """ Stores a complete layer of gcode produced in Simplify3d """

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
        return float(gcode.split('\n')[0][15:])


class CamGcodeLine:
    """ Stores a single line of fusion360 CAM gcode. """

    def __init__(self, gcode, name=None):
        self.gcode = gcode
        self.name = name
        self.layer_height = self.get_layer_height(self.gcode)

    def get_layer_height(self, gcode):
        """Return the layer height of single line of gcode."""
        return float(gcode.split('Z')[1].split(' ')[0])


class CamGcodeLayer:
    """ Stores all the CAM operations in a specific layer. """

    def __init__(self, height, operations):
        self.height = height
        self.operations = operations
        self.gcode = self.parse_gcode(self.operations)
        self.layer_height = None  # height to print to before running the operation

    def parse_gcode(self, operations):
        """ Combines the gcode lines from all the operations into a single string """
        gcode = ''

        for op in operations:
            gcode += op.gcode + '\n'

        return gcode


class Parser:
    """ Main parsing class. """

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
                    layer, 'end', inf))
                continue

            gcode_add_layers.append(Simplify3DGcodeLayer(layer))

        self.gcode_add_layers = gcode_add_layers

    def split_cam_layers(self, gcode_sub):
        """ Takes fusion360 CAM gcode and splits the operations by execution height """
        tmp_operation_list = gcode_sub.split('\n\n')

        operations = [None]

        for i, operation in enumerate(tmp_operation_list):
            if i == 0:  # ignore setup gcode
                continue

            lines = operation.split('\n')
            name = lines.pop(0)
            lines.reverse()  # required since printing is bottom up, but CAM is top down
            lines = [line for line in lines if line != '']

            operations.append([])

            # extract information from string
            lines = [CamGcodeLine(line, name) for line in lines]

            retraction_height = max(line.layer_height for line in lines)

            op_start = 0
            retracted = True
            for index, line in enumerate(lines):
                if line.layer_height == retraction_height:
                    if retracted is False:
                        op_end = index
                        operations[i].append(lines[op_start:op_end+1])
                        op_start = op_end+1
                    retracted = True
                elif line.layer_height < retraction_height:
                    retracted = False

        self.order_cam_operations_by_layer(operations)

    def order_cam_operations_by_layer(self, operations):
        """ Takes a list of cam operations and calculates the layer that they should be executed """
        min_height = inf
        ordered_operations = []
        for operation in operations:
            if operation:
                for op_instance in operation:
                    op_height = min(
                        [height.layer_height for height in op_instance])
                    min_height = min((min_height, op_height))
                    ordered_operations.append(
                        CamGcodeLayer(op_height, op_instance))

        ordered_operations.sort(key=lambda x: x.height)
        for i, operation in enumerate(ordered_operations):
            later_ops = [
                op for op in ordered_operations if op.height > operation.height]
            try:
                operation.layer_height = min(
                    [op.height for op in later_ops])
            except ValueError:
                operation.layer_height = operation.height

        self.cam_operations = ordered_operations
        self.merged_gcode = self.merge_gcode(
            self.gcode_add_layers, self.cam_operations)

    def merge_gcode(self, gcode_add, cam_operations):
        """ Takes the individual CAM instructions and merges them into the additive file from Simplify3D """
        merged_gcode = gcode_add + cam_operations
        merged_gcode.sort(key=lambda x: x.layer_height)

        self.merged_gcode_script = ''
        prev_layer = None
        for layer in merged_gcode:
            self.tool_change(layer, prev_layer)
            prev_layer = layer
            self.merged_gcode_script += layer.gcode

        return merged_gcode

    def tool_change(self, layer, prev_layer):
        if type(layer) != type(prev_layer):
            if type(layer) == Simplify3DGcodeLayer:
                self.merged_gcode_script += 'T0\n'
            elif type(layer == CamGcodeLayer):
                self.merged_gcode_script += 'T3\n'

    def create_output_file(self, gcode):
        """ Saves the file to the output folder """
        output_file = open("output/tmp.gcode", "w")
        output_file.write(gcode)
        pass


if __name__ == "__main__":
    gcode_add_file = open("gcode/additive_box.gcode", "r")
    gcode_add = gcode_add_file.read()

    gcode_sub_file = open("gcode/double_box_side_top_lead_no_arc.nc", "r")
    gcode_sub = gcode_sub_file.read()

    parser = Parser(gcode_add, gcode_sub)
    parser.create_output_file(parser.merged_gcode_script)
    pass
