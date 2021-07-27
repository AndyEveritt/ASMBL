from math import inf

from .gcode_parser import GcodeParser, Commands


class AdditiveGcodeLayer:
    """ Stores a complete layer of gcode produced in Simplify3d """

    def __init__(self, gcode, name=None, layer_height=None):
        self.gcode = gcode
        self.name = name
        self.layer_height = layer_height

        self.remove_park_gcode()

        if layer_height is None:
            self.layer_height = self.get_layer_height(self.gcode)

    def get_layer_height(self, gcode):
        height = None
        lines = GcodeParser(gcode, include_comments=True).lines

        # Check for Simplify3D end of file code
        if lines[0].to_gcode == '; layer end':
            height = inf

        else:
            line_heights = []
            for line in lines:
                if line.type == Commands.COMMENT:
                    continue
                line_height = line.get_param('Z')
                if line_height is not None:
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

    def remove_park_gcode(self):
        # Fusion adds some dirty end gcode
        # Kill it with fire until they let us control the end gcode with the post processor
        self.gcode = self.gcode.split('; move to park position')[0]
