```bash
python3 -m venv env
pip install -r requirements.txt
```

# Config

```
{
    "InputFiles": {
        "additive_gcode": path to Simplify3D additive gcode file,
        "subtractive_gcode": path to Fusion360 CAM nc file
    },
    "Printer": {
        "bed_centre_x": mm from origin to bed centre in x axis,
        "bed_centre_y": mm from origin to bed centre in y axis,
        "print_tool": Tool used to print part (eg "T0"),
        "cam_tool": Tool used for CAM (eg "T3")
    },
    "PrintSettings": {
        "raft_height": Height of the top layer of the raft,
        "layer_height": layer height of printed part
    },
    "CamSettings": {
        "layer_dropdown": How many layers the tip of the cutter should be lower than the layers being cut,
        "layer_intersect": What percentage (0-1) of a layer line should the tip of the cutter sit at when cutting
    }
}
```