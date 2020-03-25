from math import (
    inf,
    ceil,
)

from scipy.signal import find_peaks

import re
import os
import numpy as np


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
        height = None
        try:
            height = float(gcode.split('\n')[0].split('Z = ')[-1])  # Simplify3D layer height
        except ValueError:
            # Fusion 360 layer height #TODO (THIS IS NOT ROBUST...IT NEEDS CHANGING)
            height = float(gcode.split('Z')[1].split('\n')[0])

        return height


class CamGcodeLine:
    """ Stores a single line of fusion360 CAM gcode. """

    def __init__(self, gcode, offset):
        self.gcode = self.offset_gcode(gcode, offset)
        self.layer_height = self.get_layer_height(self.gcode)

    def offset_gcode(self, gcode, offset):
        gcode_segments = gcode.split(' ')
        offset_gcode = ''
        for gcode_segment in gcode_segments:
            if gcode_segment[0] == 'X':
                x_pos = float(gcode_segment[1:])
                x_pos += offset[0]
                gcode_segment = gcode_segment[0] + str(x_pos)

            elif gcode_segment[0] == 'Y':
                y_pos = float(gcode_segment[1:])
                y_pos += offset[1]
                gcode_segment = gcode_segment[0] + str(y_pos)

            elif gcode_segment[0] == 'Z':
                z_pos = float(gcode_segment[1:])
                z_pos += offset[2]
                gcode_segment = gcode_segment[0] + str(z_pos)

            offset_gcode += ' ' + gcode_segment

        return offset_gcode[1:]

    def get_layer_height(self, gcode):
        """Return the layer height of single line of gcode."""
        return float(gcode.split('Z')[1].split(' ')[0])


class CamGcodeLayer:
    """ Stores all the CAM operations in a specific layer. """

    def __init__(self, operations, name=None, tool=None, height=None):
        self.height = height
        self.operations = operations
        self.name = name
        self.tool = tool

        if self.operations:
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

    def __init__(self, config):
        self.config = config
        self.offset = (config['Printer']['bed_centre_x'],
                       config['Printer']['bed_centre_y'],

                       config['PrintSettings']['raft_height'] -
                       config['PrintSettings']['layer_height']*config['CamSettings']['layer_intersect']
                       )

        self.last_additive_tool = None
        self.last_subtractive_tool = None

        self.main()

    def main(self):
        self.open_files(self.config)

        self.gcode_add_layers = self.split_additive_layers(self.gcode_add)

        operations = self.split_cam_operations(self.gcode_sub)
        self.cam_operations = self.order_cam_operations_by_layer(operations)

        self.merged_gcode = self.merge_gcode_layers(self.gcode_add_layers, self.cam_operations)
        self.create_gcode_script(self.merged_gcode)

    def open_files(self, config):
        gcode_add_file = open(config['InputFiles']['additive_gcode'], 'r')
        self.gcode_add = gcode_add_file.read()

        gcode_sub_file = open(config['InputFiles']['subtractive_gcode'], 'r')
        self.gcode_sub = gcode_sub_file.read()

    def split_additive_layers(self, gcode_add):
        """ Takes Simplify3D gcode and splits in by layer """
        tmp_list = re.split('(; layer)', gcode_add)

        gcode_add_layers = []
        gcode_add_layers.append(Simplify3DGcodeLayer(
            tmp_list.pop(0),
            name="initialise",
            layer_height=0,
        ))    # slicer settings & initialise

        for i in range(ceil(len(tmp_list)/2)):

            layer = tmp_list[2*i] + tmp_list[2*i+1]
            name = layer.split(',')[0][2:]

            if 2*i == len(tmp_list) - 1:
                gcode_add_layers.append(Simplify3DGcodeLayer(
                    layer, 'end', inf))
                continue

            gcode_add_layers.append(Simplify3DGcodeLayer(layer))

        return gcode_add_layers

    def split_cam_operations(self, gcode_sub):
        """ Takes fusion360 CAM gcode and splits the operations by execution height """
        tmp_operation_list = gcode_sub.split('\n\n')

        operations = []

        for i, operation in enumerate(tmp_operation_list):

            lines = operation.split('\n')
            name = lines.pop(0)
            tool = lines.pop(0)
            lines = [line for line in lines if line != '']

            operations.append([])

            # extract information from string
            lines = [CamGcodeLine(line, self.offset) for line in lines]

            line_heights = np.array([line.layer_height for line in lines])
            local_peaks = find_peaks(line_heights)[0]

            if len(local_peaks) > 0:
                op_lines = lines[0: local_peaks[0]+1]
                operations[i].append(CamGcodeLayer(op_lines, name, tool))

                for index, peak in enumerate(local_peaks[:-1]):
                    op_lines = lines[local_peaks[index]: local_peaks[index+1]+1]
                    operations[i].append(CamGcodeLayer(op_lines, name, tool))

                op_lines = lines[local_peaks[-1]:]
                operations[i].append(CamGcodeLayer(op_lines, name, tool))
            else:
                operations[i].append(CamGcodeLayer(lines, name, tool))

        return operations

    def order_cam_operations_by_layer(self, operations):
        """ Takes a list of cam operations and calculates the layer that they should be executed """
        unordered_ops = []
        for operation in operations:
            if operation:
                for op_instance in operation:
                    op_height = min(
                        [line.layer_height for line in op_instance.operations])
                    op_instance.height = op_height
                    unordered_ops.append(op_instance)

        ordered_operations = sorted(unordered_ops, key=lambda x: x.height)
        for i, operation in enumerate(ordered_operations):
            later_ops = [
                op for op in ordered_operations if op.height > operation.height]
            try:
                operation.layer_height = min(
                    [op.height for op in later_ops]) + self.config['PrintSettings']['layer_height'] * self.config['CamSettings']['layer_dropdown']
            except ValueError:
                operation.layer_height = operation.height + \
                    self.config['PrintSettings']['layer_height'] * self.config['CamSettings']['layer_dropdown']

        return ordered_operations

    def merge_gcode_layers(self, gcode_add, cam_operations):
        """ Takes the individual CAM instructions and merges them into the additive file from Simplify3D """
        merged_gcode = gcode_add + cam_operations
        merged_gcode.sort(key=lambda x: x.layer_height)

        return merged_gcode

    def create_gcode_script(self, gcode):
        self.merged_gcode_script = ''
        prev_layer = gcode[0]
        for layer in gcode:
            self.set_last_additive_tool(prev_layer)
            self.tool_change(layer, prev_layer)
            prev_layer = layer
            self.merged_gcode_script += layer.gcode

    def set_last_additive_tool(self, layer):
        if isinstance(layer, Simplify3DGcodeLayer):
            process_list = layer.gcode.split('\nT')
            if len(process_list) > 1:
                self.last_additive_tool = 'T' + process_list[-1].split('\n')[0]

    def tool_change(self, layer, prev_layer):
        if type(layer) == Simplify3DGcodeLayer:
            first_gcode = layer.gcode.split('\n')[1]
            if first_gcode[0] is not 'T':
                self.merged_gcode_script += self.last_additive_tool + '\n'
        elif type(layer) == CamGcodeLayer:
            self.merged_gcode_script += layer.tool + '\n'

    def create_output_file(self, gcode):
        """ Saves the file to the output folder """
        file_path = "output/" + self.config['OutputSettings']['filename'] + ".gcode"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(gcode)


if __name__ == "__main__":
    gcode_add_file = open("gcode/cyclodial_gear/additive.gcode", "r")
    gcode_add = gcode_add_file.read()

    gcode_sub_file = open("gcode/cyclodial_gear/cam.nc", "r")
    gcode_sub = gcode_sub_file.read()

    parser = Parser(gcode_add, gcode_sub)
    parser.create_output_file(parser.merged_gcode_script)
    pass
