import sys
import os
import re
from math import (
    inf,
    ceil,
    floor,
)
from . import utils
from .additive_gcode import AdditiveGcodeLayer
from .cam_gcode import (
    CamGcodeLine,
    CamGcodeSegment,
    CamGcodeLayer,
)


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

        print('Opening files...')
        if progress:
            progress.message = 'Opening files'
            progress.progressValue += 1
        self.open_files(self.config)

        # Fusion 360 currently only exports absolute extrusion gcode, this needs to be converted
        # This method will not convert gcode if it is already relative
        print('Converting additive gcode to relative positioning...')
        if progress:
            progress.message = 'Converting additive gcode to relative positioning'
            progress.progressValue += 1
        self.gcode_add = utils.convert_relative(self.gcode_add)

        print('Spliting additive gcode layers...')
        if progress:
            progress.message = 'Spliting additive gcode layers'
            progress.progressValue += 1
        self.gcode_add_layers = self.split_additive_layers(self.gcode_add)

        print('Spliting subtractive gcode layers...')
        if progress:
            progress.message = 'Spliting subtractive gcode layers'
            progress.progressValue += 1
        operations = self.split_cam_operations(self.gcode_sub)

        print('Ordering subtractive gcode layers...')
        if progress:
            progress.message = 'Ordering subtractive gcode layers'
            progress.progressValue += 1
        self.cam_layers = self.order_cam_operations_by_layer(operations)

        print('Merging gcode layers...')
        if progress:
            progress.message = 'Merging gcode layers'
            progress.progressValue += 1
        self.merged_gcode = self.merge_gcode_layers(self.gcode_add_layers, self.cam_layers)

        print('Creating gcode script...')
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

            if 2*i + 1 == len(tmp_list) - 1:
                gcode_add_layers.append(AdditiveGcodeLayer(
                    layer, 'end', inf))
                continue

            gcode_add_layers.append(AdditiveGcodeLayer(layer, name))

        return gcode_add_layers

    def assign_cam_line_type(self, unlabelled_lines):
        """ extract type information from string, returns a list of CamGcodeLine's """
        lines = []
        line_type = None
        for line in unlabelled_lines:
            if line.startswith('(type: '):
                line_type = line[7:].strip(')')
            elif line.startswith('('):
                continue
            else:
                lines.append(CamGcodeLine(line, self.offset, line_type))

        return lines

    def group_cam_lines(self, lines):
        """
        Group consequetive lines of the same type into segments
        Returns a list of segments
        """
        segments = []
        segment_lines = [lines[0]]
        for i, line in enumerate(lines[1:]):
            if line.type != lines[i].type:
                segment_index = len(segments)
                segments.append(CamGcodeSegment(segment_index, segment_lines, lines[i].type))
                segment_lines = [line]
            else:
                segment_lines.append(line)

        segment_index = len(segments)
        segments.append(CamGcodeSegment(segment_index, segment_lines, lines[-1].type))

        return segments

    def add_lead_in_out(self, segments, cutting_group):
        pre_index = cutting_group[0].index - 1
        post_index = cutting_group[-1].index + 1
        if segments[pre_index].type == 'lead in' or segments[pre_index].type == 'plunge':
            start_index = pre_index
        else:
            start_index = cutting_group[0].index

        if segments[post_index].type == 'lead out':
            end_index = post_index
        else:
            end_index = cutting_group[-1].index

        return segments[start_index:end_index+1]

    def group_cam_segments(self, segments, name, strategy, tool):
        """
        Group all cutting segments with a continuous and equal cutting height, including all intermediary segments.
        Lead-ins and lead-outs will be added to the start and end respectively if they exist.
        Consequetive non planar segments are also grouped together.

        Returns a list of layers, each to be merged as a whole unit.
        """
        cutting_segments = [segment for segment in segments if segment.type == 'cutting']
        cam_layers = []
        cutting_group = [cutting_segments[0]]
        cutting_height = cutting_segments[0].height
        for cutting_segment in cutting_segments[1:]:
            # TODO logic needs fixing to deal with non planar and planar segments in same operation
            if cutting_segment.height == cutting_height or cutting_segment.planar is False:
                cutting_group.append(cutting_segment)
                cutting_height = cutting_segment.height
            else:
                cutting_height = cutting_segment.height

                layer_group = self.add_lead_in_out(segments, cutting_group)
                cam_layers.append(CamGcodeLayer(layer_group, name, strategy, tool))
                cutting_group = [cutting_segment]

        layer_group = self.add_lead_in_out(segments, cutting_group)
        cam_layers.append(CamGcodeLayer(layer_group, name, strategy, tool))

        return cam_layers

    def split_cam_operations(self, gcode_sub):
        """ Takes fusion360 CAM gcode and splits the operations by execution height """
        tmp_operation_list = gcode_sub.split('\n\n')

        operations = []

        for i, operation in enumerate(tmp_operation_list):
            unlabelled_lines = operation.split('\n')
            name = unlabelled_lines.pop(0)
            strategy = unlabelled_lines.pop(0)[11:].strip(')')
            tool = unlabelled_lines.pop(0)
            unlabelled_lines = [line for line in unlabelled_lines if line != '']

            lines = self.assign_cam_line_type(unlabelled_lines)
            segments = self.group_cam_lines(lines)
            operation_layers = self.group_cam_segments(segments, name, strategy, tool)
            operations.append(operation_layers)

        return operations

    def assign_cam_layer_height(self, cam_layer, later_cam_layers, layer_overlap):
        if len(later_cam_layers) > 0:
            next_cam_layer_height = min([layer.cutting_height for layer in later_cam_layers])
            later_additive = [layer for layer in self.gcode_add_layers[:-1]
                              if layer.layer_height > next_cam_layer_height]

            if layer_overlap == 0:
                cam_layer.layer_height = next_cam_layer_height

            elif len(later_additive) == 0:
                cam_layer.layer_height = next_cam_layer_height

            elif len(later_additive) >= layer_overlap:
                cam_layer.layer_height = later_additive[layer_overlap - 1].layer_height

            else:
                cam_layer.layer_height = later_additive[-1].layer_height

        else:  # no later ops
            later_additive = [layer for layer in self.gcode_add_layers[:-1]
                              if layer.layer_height > cam_layer.cutting_height]

            if len(later_additive) == 0:   # no further printing
                # add 10 since it is unlikely that the printed layer height will exceed 10 mm
                # but still want to place cutting after a print at the same height
                cam_layer.layer_height = cam_layer.cutting_height + 10

            elif len(later_additive) >= layer_overlap:
                cam_layer.layer_height = later_additive[layer_overlap - 1].layer_height

            else:
                cam_layer.layer_height = later_additive[-1].layer_height

        if cam_layer.layer_height == inf:
            raise ValueError("CAM op height can't be 'inf'")

    def order_cam_operations_by_layer(self, operations):
        """ Takes a list of cam operations and calculates the layer that they should be executed """
        unordered_cam_layers = []

        for operation in operations:
            for cam_layer in operation:
                unordered_cam_layers.append(cam_layer)

        ordered_cam_layers = sorted(unordered_cam_layers, key=lambda x: x.cutting_height)

        layer_overlap = self.config['CamSettings']['layer_overlap']

        # TODO assign layer height per layer in each operation independently. There is an issue if you have sparse CAM currently
        for i, cam_layer in enumerate(ordered_cam_layers):
            later_cam_layers = [
                layer for layer in ordered_cam_layers if layer.cutting_height > cam_layer.cutting_height]
            self.assign_cam_layer_height(cam_layer, later_cam_layers, layer_overlap)

        return ordered_cam_layers

    def add_retracts(self, cam_layer, clearance_height=5):
        first_line = cam_layer.segments[0].lines[0]
        last_line = cam_layer.segments[-1].lines[-1]

        offset = (0, 0, clearance_height)
        pre_retract = utils.offset_gcode(first_line.gcode, offset)
        post_retract = utils.offset_gcode(last_line.gcode, offset)

        cam_layer.gcode = '; retract\n' + pre_retract + '\n' + cam_layer.gcode + '; retract\n' + post_retract + '\n'

    def merge_gcode_layers(self, gcode_add, cam_layers):
        """ Takes the individual CAM instructions and merges them into the additive file from Simplify3D """
        for cam_layer in cam_layers:
            self.add_retracts(cam_layer)

        merged_gcode = gcode_add + cam_layers
        merged_gcode.sort(key=lambda x: x.layer_height)

        return merged_gcode

    def create_gcode_script(self, gcode):
        self.merged_gcode_script = '; ASMBL gcode created by https://github.com/AndyEveritt/ASMBL\n'
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
