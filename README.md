# Overview

This code is designed to create a gcode file suitable for Additive & Subtractive Manufacturing By Layer (ASMBL).

It takes 2 input files:
* An additive`.gcode` file from Simplify3D using the `ASMBL.factory` file to get the appropriate settings.
* A subtractive `.nc` file from Fusion360.

These files require specific setup for this program to work


# Installation

```bash
git clone {repo address}
python3 -m venv env
pip install -r requirements.txt
```

# How to Setup

## Simplify3D

* Open the `ASMBL.factory` file
* Import the STL file
* Orient the part in the desired orientation
* Click `Center and Arrange`
* Click `Prepare to Print!`
* In the preview, use the layer view to find the height of the top layer of the raft, it is needed for `config.json`
* Save the file to the desired project location

### Settings that are important

Tab | Setting | Default | Effect | Other Notes
--- | ------- | ------- | ------ | -----------
Layer | Primary Layer Height | `0.2` | Layer height of the print | Thicker layers can create smoother surfaces with ASMBL (requires further testing). Layers less than 0.2 mm should be avoided
Additions | Use Raft | `Enabled` | Prevents cutting into bed
Other | Horizontal size compensation | `0.25` | Amount of horizontal cut-in | Any dimension that is not CAM'd will be this much too large

### Other points

* It is important that the centre of the part is in the centre of the bed to ensure the CAM settings correctly align
* The part must also be oriented with the same XYZ axis as the CAM'd part

## Fusion360

### Stock setup

* Create a new Setup by clicking `Setup` > `New Setup`
* Select `From solid` for the Stock mode
* Click on the part body to select it
* Move the origin to the bottom middle of the part
* Orient the Z axis to be vertically upwards

### CAM setup

The CAMing proceedures for ASMBL can be configured with the following processes:

Process | Usage
------- | -----
2D Contour | Used for vertical side walls of parts
2D Adaptive | Used for top surfacing
3D Contour | Used for vertical & close to vertical side walls (including chamfers & filets). May not be able to cut internal features (ie walls with a roof over them)

#### 2D Contour

* `Tool`
  * Select/create a cutting tool with appropriate dimensions for what is installed on you ASMBL machine
* `Geometry`
  * Select all the contours for the sides you would like to cut
* `Heights`
  * Set the `Clearance Height`, `Retract Height`, and `Feed Height` equal
    * These must be equal for all processes
  * Set the `Top Height` and `Bottom Height` appropriately for the desired process
    * ie top and bottom of the surface
* `Passes`
  * Set `Sideways Compensation` to `Right (conventional)`
  * Set `Finishing Overlap` to non zero for better finish
  * Enable `Multiple Depths`
  * Set `Maximum Roughing Stepdown` to be equal to ~1-2 layers
    * Ensure this is an integer multiple of the layer height to get the most consistent results
  * Disable `Stock to Leave`
* `Linking`
  * Set `Vertical Lead-In Radius` to `0` mm
  * Disable `Ramp`

2D Contour can be used when fine control over the process is needed. Undercuts can be done using this process.

<img src="docs/images/2d_contour_undercuts.png" width=480>

#### 2D Adaptive

* `Tool`
  * Select/create a cutting tool with appropriate dimensions for what is installed on you ASMBL machine
* `Geometry`
  * Select the surface you would like to top surface
* `Heights`
  * Set the `Clearance Height`, `Retract Height`, and `Feed Height` equal
    * These must be equal for all processes
* `Passes`
  * Set `Optimal Load` to ~0.2-0.8 mm
  * Set `Direction` to `Conventional`
  * Disable `Stock to Leave`
* `Linking`
  * Set `Vertical Lead In/Out Radius` to `0` mm
  * Set `Ramp Type` to `Plunge`


Multiple surfaces at different heights can be selected with the same process. This can help reduce setup time in Fusion

<img src="docs/images/2d_adaptive_selection.png" width=480>

#### 3D Contour

* `Tool`
  * Select/create a cutting tool with appropriate dimensions for what is installed on you ASMBL machine
* `Geometry`
  * Select the boundry contours for the sides you would like to cut (everything in the boundry will be cut)
  * You can specify an out and inner boundary to only cut a certain region
* `Heights`
  * Set the `Clearance Height`, `Retract Height`, and `Feed Height` equal
    * These must be equal for all processes
  * Set the `Top Height` and `Bottom Height` appropriately for the desired process
    * ie top and bottom of the surface
* `Passes`
  * Set `Direction` to `Conventional`
  * Set `Finishing Overlap` to non zero for better finish
  * Set `Maximum Stepdown` to be equal to ~0.5-2 layers
  * Disable `Stock to Leave`
* `Linking`
  * Set `Maximum Stay Down Distance` to `0` mm
  * Set `Vertical Lead-In Radius` to `0` mm
  * Set `Ramp Type` to `Profile`



3D Contour can be used for most none flat surfaces that have nothing above them. They are good for quickly CAM'ing a large number of faces.

<img src="docs/images/3d_contour_1.png" width="480">

The machining boundary can be used to restrict which faces are machined. Here the centre sloped surface is diselected but everything within the inner centre hole is machined.

<img src="docs/images/3d_contour_machining_boundaries.png" width="480">

Undercuts do not work with 3D Contour. 2D Contour can be used for this instead.

<img src="docs/images/3d_contour_undercuts.png" width="480">

### Post Processing

* Generate and Simulate the full Setup to ensure in looks sensible
* Click `Actions` > `Post Process`
* Select the `BoXYZ (Grbl) / boxyz` config
* Set the `Output folder` to the desired project location
* Click `Post`

## Config

The `config.json` contains the parameters that control how the ASMBL parser merges the 2 input files

Update the `config.json` so that the following settings are correct for your project:

```json
{
    "InputFiles": {
        "additive_gcode": "path to Simplify3D additive .gcode file",
        "subtractive_gcode": "path to Fusion360 CAM .nc file"
    },
    "Printer": {
        "bed_centre_x": "mm from origin to bed centre in x axis",
        "bed_centre_y": "mm from origin to bed centre in y axis",
        "cam_tool": "Tool used for CAM (eg 'T3')"
    },
    "PrintSettings": {
        "raft_height": "Height of the top layer of the raft",
        "layer_height": "layer height of printed part"
    },
    "CamSettings": {
        "layer_dropdown": "How many layers the tip of the cutter should be lower than the layers being cut",
        "layer_intersect": "What percentage (0-1) of a layer line should the tip of the cutter sit at when cutting"
    },
    "OutputSettings": {
        "filename": "Name of the output file containing the merged gcode script
    }
}
```

## Program

The program takes the following arguments:

Arg (long) | Arg (short) | Default | Usage
---------- | ----------- | ------- | -----
`--config` | `-C` | `config.json` | Path to the configuration JSON file

## Run

To run the program, ensure the python virtual environment is enabled, then use `python main.py`

The program will output the file with a name according the the config settings in the `output` folder. 

>**Always preview the generated gcode in Simplify3D before attempting to print it**

Set the coloring to `Active Toolhead` and enable `Travel moves` to ensure the part is using the correct tools at the correct times.

The subtractive processes are displayed as travel moves, scroll through the layers to check the subtractive processes have been added at the correct point in the print (defined in `config.json`)

<img src="docs/images/simplify3d_preview.png" width="480">
