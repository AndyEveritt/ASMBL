[Back - README](../../README.md)

# Planar

## 2D Adaptive

**Uses**: Top surfacing

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
  * Set `Ramp Type` to `Plunge`


Multiple surfaces at different heights can be selected with the same process. This can help reduce setup time in Fusion

<img src="images/2d_adaptive_selection.png" width=480>

## 3D Contour

**Uses**: Side walls & slopes

* `Tool`
  * Select/create a cutting tool with appropriate dimensions for what is installed on you ASMBL machine
* `Geometry`
  * Select the boundry contours for the sides you would like to cut (everything in the boundry will be cut)
  * You can specify an out and inner boundary to only cut a certain region
* `Heights`
  * Set the `Clearance Height` and `Retract Height` equal
    * These must be equal for all processes
  * Set the `Top Height` and `Bottom Height` appropriately for the desired process
    * ie top and bottom of the surface
* `Passes`
  * Set `Direction` to `Conventional`
  * Set `Maximum Stepdown` to be equal to ~0.5-2 layers
  * Disable `Stock to Leave`
* `Linking`
  * Set `Maximum Stay Down Distance` to `0` mm
  * Set `Ramp Type` to `Profile`

3D Contour can be used for most none flat surfaces that have nothing above them. They are good for quickly CAM'ing a large number of faces.

<img src="images/3d_contour_1.png" width="480">

## 2D Contour

**Uses**: Not sure there are any that 3D Contour doesn't cover. Here is the setup guide anyway

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
  * Disable `Ramp`

2D Contour can be used when fine control over the process is needed. Undercuts can be done using this process.

<img src="images/2d_contour_undercuts.png" width=480>

# Non-planar Operations

Non-planar operations can be configured similarly to the planar operations described above. More care is required when creating the toolpaths as is it easy to accidentally cut into the part.

Some non-planar operations that have been tested to work are:

* Parallel
* Radial
* Spiral
* Scallop

An example Fusion setup can be found [here](../../CAD/Spinner_Demo.f3d)

<img src="images/fusion_cam_nonplanar.png" width=480>