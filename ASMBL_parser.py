import sys
import os
venv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'env', 'Lib', 'site-packages')
if venv_path not in sys.path:
    sys.path.append(venv_path)  # add venv to python path

from scipy.signal import find_peaks
from math import (
    inf,
    ceil,
)
import numpy as np
import re


class AdditiveGcodeLayer:
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
        lines = gcode.split('\n')
        
        # Check for Simplify3D end of file code
        if lines[0] == '; layer end':
            height = inf
        
        else:
            line_heights = []
            for line in lines:
                if line == '':
                    continue
                if line[0] == ';':
                    continue
                line_segments = line.split('Z')
                if len(line_segments) > 1:
                    line_height = float(line_segments[1].split(' ')[0])
                    line_heights.append(line_height)
            
            height = min(line_heights)

        return height

    def comment_all_gcode(self):
        commented_gcode = ''
        lines = self.gcode.split('\n')
        for line in lines:
            if line != '':
                if line[0] != ';':
                    line = '; ' + line
                commented_gcode += line + '\n'
        self.gcode = commented_gcode


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

    def set_min_z_height(self):
        op_height = min(
            [line.layer_height for line in self.operations])
        self.height = op_height

    def set_max_z_height(self):
        lines = []
        # Filter out retracts, only care about max Z height of cutting ops
        for line in self.operations:
            if len(line.gcode.split('F')) > 1:
                lines.append(line)
        
        op_height = max(
            [line.layer_height for line in lines])
        self.height = op_height


class Parser:
    """ Main parsing class. """

    def __init__(self, config, progress=None):
        self.config = config
        self.progress = progress    # progress bar for Fusion add-in
        self.offset = (config['Printer']['bed_centre_x'],
                       config['Printer']['bed_centre_y'],

                       config['PrintSettings']['raft_height'] - config['CamSettings']['layer_dropdown']
                       )

        self.last_additive_tool = None
        self.last_subtractive_tool = None

        self.main()

    def main(self):
        progress = self.progress

        if progress:
            progress.message = 'Opening files'
            progress.progressValue += 1
        self.open_files(self.config)

        if progress:
            progress.message = 'Spliting additive gcode layers'
            progress.progressValue += 1
        self.gcode_add_layers = self.split_additive_layers(self.gcode_add)

        if progress:
            progress.message = 'Spliting subtractive gcode layers'
            progress.progressValue += 1
        operations = self.split_cam_operations(self.gcode_sub)

        if progress:
            progress.message = 'Ordering subtractive gcode layers'
            progress.progressValue += 1
        self.cam_operations = self.order_cam_operations_by_layer(operations)

        if progress:
            progress.message = 'Merging gcode layers'
            progress.progressValue += 1
        self.merged_gcode = self.merge_gcode_layers(self.gcode_add_layers, self.cam_operations)

        if progress:
            progress.message = 'Creating gcode script'
            progress.progressValue += 1
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
        initialise_layer = AdditiveGcodeLayer(
            tmp_list.pop(0),
            name="initialise",
            layer_height=0,
        )    # slicer settings & initialise
        self.set_last_additive_tool(initialise_layer)
        # initialise_layer.comment_all_gcode()
        gcode_add_layers.append(initialise_layer)

        for i in range(ceil(len(tmp_list)/2)):

            layer = tmp_list[2*i] + tmp_list[2*i+1]
            name = layer.split(',')[0][2:]

            if 2*i == len(tmp_list) - 1:
                gcode_add_layers.append(AdditiveGcodeLayer(
                    layer, 'end', inf))
                continue

            gcode_add_layers.append(AdditiveGcodeLayer(layer))

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
                    # if op_instance.name.startswith('(Radial'):
                    #     op_instance.set_max_z_height()
                    # else:
                    op_instance.set_min_z_height()
                    unordered_ops.append(op_instance)

        ordered_operations = sorted(unordered_ops, key=lambda x: x.height)
        layer_overlap = self.config['CamSettings']['layer_overlap']

        for i, operation in enumerate(ordered_operations):
            later_ops = [op for op in ordered_operations if op.height > operation.height]
            if len(later_ops) > 0:
                next_op_height = min([op.height for op in later_ops])
                later_additive = [layer for layer in self.gcode_add_layers if layer.layer_height > next_op_height]

                if layer_overlap == 0:
                    operation.layer_height = next_op_height

                elif len(later_additive) == 0:
                    operation.layer_height = next_op_height

                elif len(later_additive) >= layer_overlap:
                    operation.layer_height = later_additive[layer_overlap - 1].layer_height

                else:
                    operation.layer_height = later_additive[-1].layer_height

            else:  # no later ops
                later_additive = [layer for layer in self.gcode_add_layers if layer.layer_height > operation.height]

                if len(later_additive) >= layer_overlap:
                    operation.layer_height = later_additive[layer_overlap - 1].layer_height
                
                elif len(later_additive) == 0:   # no further printing
                    # add 10 since it is unlikely that the printed layer height will exceed 10 mm
                    # but still want to place cutting after a print at the same height
                    operation.layer_height = operation.height + 10
                
                else:
                    operation.layer_height = later_additive[-1].layer_height

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
        if isinstance(layer, AdditiveGcodeLayer):
            process_list = layer.gcode.split('\nT')
            if len(process_list) > 1:
                self.last_additive_tool = 'T' + process_list[-1].split('\n')[0]

    def tool_change(self, layer, prev_layer):
        if type(layer) == AdditiveGcodeLayer:
            if layer.name == 'initialise' or prev_layer.name == 'initialise':
                return  # no need to add a tool change
            first_gcode = layer.gcode.split('\n')[1]
            if first_gcode[0] is not 'T':
                self.merged_gcode_script += self.last_additive_tool + '\n'
        elif type(layer) == CamGcodeLayer:
            self.merged_gcode_script += layer.tool + '\n'

    def create_output_file(self, gcode, folder_path="output/", relative_path=True):
        """ Saves the file to the output folder """
        file_path = folder_path + self.config['OutputSettings']['filename'] + ".gcode"

        file_path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(gcode)
        
        f.close()

        try:
            os.startfile(file_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    gcode_add_file = open("gcode/cyclodial_gear/additive.gcode", "r")
    gcode_add = gcode_add_file.read()

    gcode_sub_file = open("gcode/cyclodial_gear/cam.nc", "r")
    gcode_sub = gcode_sub_file.read()

    parser = Parser(gcode_add, gcode_sub)
    parser.create_output_file(parser.merged_gcode_script)
    pass
