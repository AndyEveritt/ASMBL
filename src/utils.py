import sys
import os
import subprocess
import time


def convert_relative(gcode_abs):
    """ Converts absolute extrusion gcode into relative extrusion gcode """
    absolute_mode = False
    last_tool = None
    last_e = {}     # {'tool': last extrusion value}

    lines = gcode_abs.split('\n')

    gcode_rel = ''

    for line in lines:
        if line == '':
            continue

        line_start = line.split(' ')[0]
        # Check for absolute extrusion
        if line_start == ('M82'):
            absolute_mode = True
            line = 'M83'

        # Check for relative extrusion
        elif line_start == ('M83'):
            absolute_mode = False

        # Check for tool change
        elif line_start[0] == 'T':
            last_tool = line_start

        # Check for extrusion reset
        elif line_start == 'G92':
            extrusion_reset = line.split('E')[1]
            last_e[last_tool] = extrusion_reset

        # Convert Extrusion coordinates to relative if in absolute mode
        if absolute_mode:
            if line_start == 'G0' or line_start == 'G1':
                try:
                    line_split = line.split('E')
                    current_extrusion = line_split[1]
                    extrusion_diff = float(current_extrusion) - float(last_e[last_tool])
                    extrusion_diff = round(extrusion_diff, 3)
                    last_e[last_tool] = current_extrusion
                    line = line_split[0] + 'E' + str(extrusion_diff)
                except IndexError:
                    pass
        gcode_rel += line + '\n'

    return gcode_rel


def offset_gcode(gcode, offset):
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


def find_maxima(numbers):
    """
    Returns the index of all the local maxima in a list of numbers

    Will return the middle index if there is a flat peak
    """
    from math import ceil

    maxima = []
    length = len(numbers)
    flat_index = 0
    prev_increasing = False
    if length > 3:
        for i in range(1, length-1):
            if numbers[i] > numbers[i-1]:
                flat_index = 0
                prev_increasing = True
                if numbers[i] > numbers[i+1]:
                    maxima.append(i)
                    prev_increasing = False

            elif prev_increasing:
                if numbers[i] >= numbers[i-1] and numbers[i] == numbers[i+1]:
                    flat_index += 1

                elif numbers[i] == numbers[i-1] and numbers[i] > numbers[i+1]:
                    mid_index = ceil(flat_index/2 + 0.5)
                    maxima.append(i - mid_index)
                    flat_index = 0
                    prev_increasing = False

    return maxima


def open_file(path):
    if sys.platform == 'win32':
        path = os.path.normpath(path)
        os.startfile(path, 'open')
    else:
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([opener, path])
