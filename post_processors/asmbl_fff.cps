/**
  Copyright (C) 2018-2020 by Autodesk, Inc.
  All rights reserved.

  3D additive printer post configuration.

  $Revision: 42679 9471a22a72e5b6a8be7a1bf341716ac0009d9847 $
  $Date: 2020-03-09 10:36:19 $
  
  FORKID {A316FBC4-FA6E-41C5-A347-3D94F72F5D06}
*/

description = "ASMBL FFF";
vendor = "ASMBL";
certificationLevel = 2;
minimumRevision = 45633;

longDescription = "Simple post to export toolpath for generic FFF Machine in gcode format for ASMBL";

extension = "gcode";
setCodePage("ascii");

capabilities = CAPABILITY_ADDITIVE;
tolerance = spatial(0.002, MM);
highFeedrate = (unit == MM) ? 6000 : 236;

// needed for range checking, will be effectively passed from Fusion
var printerLimits = {
  x: {min: 0, max: 300.0}, //Defines the x bed size
  y: {min: 0, max: 300.0}, //Defines the y bed size
  z: {min: 0, max: 300.0} //Defines the z bed size
};

var extruderOffsets = [[0, 0, 0], [0, 0, 0]];
var activeExtruder = 0;  //Track the active extruder.

var xyzFormat = createFormat({decimals: (unit == MM ? 3 : 4)});
var xFormat = createFormat({decimals: (unit == MM ? 3 : 4)});
var yFormat = createFormat({decimals: (unit == MM ? 3 : 4)});
var zFormat = createFormat({decimals: (unit == MM ? 3 : 4)});
var gFormat = createFormat({prefix: "G", width: 1, zeropad: false, decimals: 0});
var mFormat = createFormat({prefix: "M", width: 2, zeropad: true, decimals: 0});
var tFormat = createFormat({prefix: "T", width: 1, zeropad: false, decimals: 0});
var feedFormat = createFormat({decimals: (unit == MM ? 0 : 1)});
var integerFormat = createFormat({decimals:0});
var dimensionFormat = createFormat({decimals: (unit == MM ? 3 : 4), zeropad: false, suffix: (unit == MM ? "mm" : "in")});

var gMotionModal = createModal({force: true}, gFormat); // modal group 1 // G0-G3, ...
var gPlaneModal = createModal({onchange: function () {gMotionModal.reset();}}, gFormat); // modal group 2 // G17-19 //Actually unused
var gAbsIncModal = createModal({}, gFormat); // modal group 3 // G90-91

var xOutput = createVariable({prefix: "X"}, xFormat);
var yOutput = createVariable({prefix: "Y"}, yFormat);
var zOutput = createVariable({prefix: "Z"}, zFormat);
var feedOutput = createVariable({prefix: "F"}, feedFormat);
var eOutput = createVariable({prefix: "E"}, xyzFormat);  // Extrusion length
var sOutput = createVariable({prefix: "S", force: true}, xyzFormat);  // Parameter temperature or speed
var pOutput = createVariable({prefix: "P", force: true}, xyzFormat);  // P parameter

// Writes the specified block.
function writeBlock() {
  writeWords(arguments);
}

function onOpen() {
  getPrinterGeometry();

  writeComment("Fusion360")

  if (programName) {
    writeComment(programName);
  }
  if (programComment) {
    writeComment(programComment);
  }

  writeComment("Printer Name: " + machineConfiguration.getVendor() + " " + machineConfiguration.getModel());
  writeComment("Print time: " + xyzFormat.format(printTime) + "s");
  writeComment("Extruder 1 Material used: " + dimensionFormat.format(getExtruder(1).extrusionLength));
  writeComment("Extruder 1 Material name: " + getExtruder(1).materialName);
  writeComment("Extruder 1 Filament diameter: " + dimensionFormat.format(getExtruder(1).filamentDiameter));
  writeComment("Extruder 1 Nozzle diameter: " + dimensionFormat.format(getExtruder(1).nozzleDiameter));
  writeComment("Extruder 1 offset x: " + dimensionFormat.format(extruderOffsets[0][0]));
  writeComment("Extruder 1 offset y: " + dimensionFormat.format(extruderOffsets[0][1]));
  writeComment("Extruder 1 offset z: " + dimensionFormat.format(extruderOffsets[0][2]));
  writeComment("Max temp: " + integerFormat.format(getExtruder(1).temperature));
  writeComment("Bed temp: " + integerFormat.format(bedTemp));
  writeComment("Layer Count: " + integerFormat.format(layerCount));

  if (hasGlobalParameter("ext2-extrusion-len") &&
    hasGlobalParameter("ext2-nozzle-dia") &&
    hasGlobalParameter("ext2-temp") && hasGlobalParameter("ext2-filament-dia") &&
    hasGlobalParameter("ext2-material-name")
  ) {
    writeComment("Extruder 2 material used: " + dimensionFormat.format(getExtruder(2).extrusionLength));
    writeComment("Extruder 2 material name: " + getExtruder(2).materialName);
    writeComment("Extruder 2 filament diameter: " + dimensionFormat.format(getExtruder(2).filamentDiameter));
    writeComment("Extruder 2 nozzle diameter: " + dimensionFormat.format(getExtruder(2).nozzleDiameter));
    writeComment("Extruder 2 max temp: " + integerFormat.format(getExtruder(2).temperature));
    writeComment("Extruder 2 offset x: " + dimensionFormat.format(extruderOffsets[1][0]));
    writeComment("Extruder 2 offset y: " + dimensionFormat.format(extruderOffsets[1][1]));
    writeComment("Extruder 2 offset z: " + dimensionFormat.format(extruderOffsets[1][2]));
  }
  
  writeComment("width: " + dimensionFormat.format(printerLimits.x.max));
  writeComment("depth: " + dimensionFormat.format(printerLimits.y.max));
  writeComment("height: " + dimensionFormat.format(printerLimits.z.max));
  writeComment("Count of bodies: " + integerFormat.format(partCount));
  writeComment("Version of Fusion: " + getGlobalParameter("version"));
}

function getPrinterGeometry() {
  machineConfiguration = getMachineConfiguration();

  // Get the printer geometry from the machine configuration
  printerLimits.x.min = 0 - machineConfiguration.getCenterPositionX();
  printerLimits.y.min = 0 - machineConfiguration.getCenterPositionY();
  printerLimits.z.min = 0 + machineConfiguration.getCenterPositionZ();

  printerLimits.x.max = machineConfiguration.getWidth() - machineConfiguration.getCenterPositionX();
  printerLimits.y.max = machineConfiguration.getDepth() - machineConfiguration.getCenterPositionY();
  printerLimits.z.max = machineConfiguration.getHeight() + machineConfiguration.getCenterPositionZ();

  extruderOffsets[0][0] = machineConfiguration.getExtruderOffsetX(1);
  extruderOffsets[0][1] = machineConfiguration.getExtruderOffsetY(1);
  extruderOffsets[0][2] = machineConfiguration.getExtruderOffsetZ(1);
  if (numberOfExtruders > 1) {
    extruderOffsets[1] = [];
    extruderOffsets[1][0] = machineConfiguration.getExtruderOffsetX(2);
    extruderOffsets[1][1] = machineConfiguration.getExtruderOffsetY(2);
    extruderOffsets[1][2] = machineConfiguration.getExtruderOffsetZ(2);
  }
}

function onClose() {
  writeComment("layer end,")
  writeComment("END OF GCODE");
  
  // turn off the ESC
  writeBlock(mFormat.format(42), pOutput.format(7), sOutput.format(0))

  // deselect tool
  writeBlock(tFormat.format(-1));

  // writeBlock(gMotionModal.format(0), 0, 0, zFormat.format(printerLimits.z.max));
}

function onComment(message) {
  writeComment(message);
}

function onSection() {
  var range = currentSection.getBoundingBox();
  axes = ["x", "y", "z"];
  formats = [xFormat, yFormat, zFormat];
  for (var element in axes) {
    var min = formats[element].getResultingValue(range.lower[axes[element]]);
    var max = formats[element].getResultingValue(range.upper[axes[element]]);
    if (printerLimits[axes[element]].max < max || printerLimits[axes[element]].min > min) {
      error(localize("A toolpath is outside of the build volume."));
    }
  }

  // set unit
  writeBlock(gFormat.format(unit == MM ? 21 : 20));
  writeBlock(gAbsIncModal.format(90)); // absolute spatial co-ordinates
  writeBlock(mFormat.format(82)); // absolute extrusion co-ordinates

  // set initial tool
  onExtruderChange(activeExtruder)

  // load mesh bed level
  writeBlock(gFormat.format(29), sOutput.format(1));

  // turn on the ESC
  writeBlock(mFormat.format(280), pOutput.format(7), sOutput.format(40))
}

function onRapid(_x, _y, _z) {
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  if (x || y || z) {
    writeBlock(gMotionModal.format(0), x, y, z);
  }
}

function onLinearExtrude(_x, _y, _z, _f, _e) {
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  var f = feedOutput.format(_f);
  var e = eOutput.format(_e);
  if (x || y || z || f || e) {
    writeBlock(gMotionModal.format(1), x, y, z, f, e);
  }
}

// Temp controller not needed for ASMBL
// function onBedTemp(temp, wait) {
//   if (wait) {
//     writeBlock(mFormat.format(190), sOutput.format(temp));
//   } else {
//     writeBlock(mFormat.format(140), sOutput.format(temp));
//   }
// }

function onExtruderChange(id) {
  if (id < numberOfExtruders) {
    writeBlock(tFormat.format(id));
    activeExtruder = id;
    xOutput.reset();
    yOutput.reset();
    zOutput.reset();
  } else {
    error(localize("This printer doesn't support the extruder ") + integerFormat.format(id) + " !");
  }
}

function onExtrusionReset(length) {
  eOutput.reset();
  writeBlock(gFormat.format(92), eOutput.format(length));
}

function onLayer(num) {
  writeComment("layer " + integerFormat.format(num) + " of " + integerFormat.format(layerCount) + ",");  // comment format to match Simplify3D
}

// Temp controller not needed for ASMBL
// function onExtruderTemp(temp, wait, id) {
//   if (id < numberOfExtruders) {
//     if (wait) {
//       writeBlock(mFormat.format(109), sOutput.format(temp), tFormat.format(id));
//     } else {
//       writeBlock(mFormat.format(104), sOutput.format(temp), tFormat.format(id));
//     }
//   } else {
//     error(localize("This printer doesn't support the extruder ") + integerFormat.format(id) + " !");
//   }
// }

function onFanSpeed(speed, id) {
  // to do handle id information
  if (speed == 0) {
    writeBlock(mFormat.format(107));
  } else {
    writeBlock(mFormat.format(106), sOutput.format(speed));
  }
}

function onParameter(name, value) {
  switch (name) {
  //feedrate is set before rapid moves and extruder change
  case "feedRate":
    if (unit == IN) {
      value /= 25.4;
    }
    setFeedRate(value);
    break;
  //warning or error message on unhandled parameter?
  }
}

//user defined functions
function setFeedRate(value) {
  feedOutput.reset();
  writeBlock(gFormat.format(1), feedOutput.format(value));
}

function writeComment(text) {
  writeln("; " + text);
}

/** Output block to do safe retract and/or move to home position. */
function writeRetract() {
  if (arguments.length == 0) {
    error(localize("No axis specified for writeRetract()."));
    return;
  }
  var words = []; // store all retracted axes in an array
  for (var i = 0; i < arguments.length; ++i) {
    let instances = 0; // checks for duplicate retract calls
    for (var j = 0; j < arguments.length; ++j) {
      if (arguments[i] == arguments[j]) {
        ++instances;
      }
    }
    if (instances > 1) { // error if there are multiple retract calls for the same axis
      error(localize("Cannot retract the same axis twice in one line"));
      return;
    }
    switch (arguments[i]) {
    case X:
      words.push("X" + xyzFormat.format(machineConfiguration.hasHomePositionX() ? machineConfiguration.getHomePositionX() : 0));
      xOutput.reset();
      break;
    case Y:
      words.push("Y" + xyzFormat.format(machineConfiguration.hasHomePositionY() ? machineConfiguration.getHomePositionY() : 0));
      yOutput.reset();
      break;
    case Z:
      words.push("Z" + xyzFormat.format(0));
      zOutput.reset();
      retracted = true; // specifies that the tool has been retracted to the safe plane
      break;
    default:
      error(localize("Bad axis specified for writeRetract()."));
      return;
    }
  }
  if (words.length > 0) {
    gMotionModal.reset();
    writeBlock(gFormat.format(28), gAbsIncModal.format(90), words); // retract
  }
}
