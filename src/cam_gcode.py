from math import inf
import src.utils as utils


class CamGcodeLine:
    """ Stores a single line of fusion360 CAM gcode. """

    def __init__(self, gcode, offset, line_type):
        self.gcode = utils.offset_gcode(gcode, offset)
        self.layer_height = self.get_layer_height(self.gcode)
        self.type = line_type

    def get_layer_height(self, gcode):
        """Return the layer height of single line of gcode."""
        return float(gcode.split('Z')[1].split(' ')[0])


class CamGcodeSegment:
    """ Stores gcode lines for a sequence of a specific movement type """

    def __init__(self, index, lines, segment_type):
        self.type = segment_type
        self.lines = lines
        self.index = index
        self.planar = None
        self.height = None

        if self.type == 'cutting':
            self.set_z_height()

    def get_min_z_height(self):
        op_height = min(
            [line.layer_height for line in self.lines])
        return op_height

    def get_max_z_height(self):
        # Filter out retracts, only care about max Z height of cutting ops
        op_height = max(
            [line.layer_height for line in self.lines])
        return op_height

    def set_z_height(self, threshold=0.05):
        max_height = self.get_max_z_height()
        min_height = self.get_min_z_height()

        if round(max_height - min_height, 6) > threshold:
            self.height = max_height
            self.planar = False

        else:
            self.height = min_height
            self.planar = True


class CamGcodeLayer:
    """ Stores all the CAM operations in a specific layer. """

    def __init__(self, segments, name=None, strategy=None, tool=None, cutting_height=None):
        self.segments = segments
        self.name = name
        self.strategy = strategy
        self.tool = tool
        self.planar = None
        self.cutting_height = cutting_height
        self.gcode = None

        if self.segments:
            self.set_cutting_height()
            self.set_planar()
            self.gcode = self.parse_gcode()

        self.layer_height = None  # height to print to before running the operation

    def parse_gcode(self):
        """ Combines the gcode lines from all the operations into a single string """
        gcode = ''

        for segment in self.segments:
            for line in segment.lines:
                gcode += line.gcode + '\n'

        return gcode

    def set_cutting_height(self):
        self.cutting_height = max(
            [segment.height for segment in self.segments if segment.type == 'cutting'])

    def set_planar(self):
        non_planar_segments = [segment for segment in self.segments if segment.planar is False]
        if len(non_planar_segments) > 0:
            self.planar = False
        else:
            self.planar = True


class NonPlanarOperation():
    def __init__(self, operation):
        self.name = operation[0].name
        self.tool = operation[0].tool
        self.cam_layers = operation
        self.set_z_height()

    def set_z_height(self):
        self.height = -inf
        for layer in self.cam_layers:
            if layer.height > self.height:
                self.height = layer.height
