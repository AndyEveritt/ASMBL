[Back - README](../../README.md)

# Simplify3D

* Open the `ASMBL.factory` file
* Import the STL file
* Orient the part in the desired orientation
* Click `Center and Arrange`
* Click `Prepare to Print!`
* In the preview, use the layer view to find the height of the top layer of the raft, it is needed for `config.json`
* Save the file to the desired project location

## Settings that are important

Tab | Setting | Default | Effect | Other Notes
--- | ------- | ------- | ------ | -----------
Layer | Primary Layer Height | `0.3` | Layer height of the print | Thicker layers can create smoother surfaces with ASMBL (requires further testing). Layers less than 0.2 mm should be avoided
Additions | Use Raft | `Enabled` | Prevents cutting into bed
Other | Horizontal size compensation | `0.25` | Amount of horizontal cut-in | Any dimension that is not CAM'd will be this much too large. **This is not needed if offsetting the geometery in Fusion360**

## Other points

* It is important that the centre of the part is in the centre of the bed to ensure the CAM settings correctly align
  * This can be avoided in Fusion if you create an additive setup with the correct origin for your printer, then use that origin for you cam setup. (you do not need to use the gcode created by the additive setup, only use it to set the origin)
* The part must also be oriented with the same XYZ axis as the CAM'd part

# Other Slicers

This program works by splitting the layers of both the additive and subtractive gcodes and merging them appropriately. It has been designed around Simplify3D and Fusion360 however in theory all the additive gcode requires to separate its layers is the following line on a layer change:

`; layer`

Currently it does not matter if anything comes after this.
