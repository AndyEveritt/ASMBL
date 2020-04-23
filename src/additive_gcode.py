from math import inf


class AdditiveGcodeLayer:
    """ Stores a complete layer of gcode produced in Simplify3d """

    def __init__(self, gcode, name=None, layer_height=None):
        self.gcode = gcode
        self.name = name
        self.layer_height = layer_height

        self.remove_park_gcode()

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

    def remove_park_gcode(self):
        # Fusion adds some dirty end gcode
        # Kill it with fire until they let us control the end gcode with the post processor
        self.gcode = self.gcode.split('; move to park position')[0]
