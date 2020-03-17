/**
  Copyright (C) 2012-2016 by Autodesk, Inc.
  All rights reserved.

  Dump configuration.

  $Revision: 42603 3b163ceb4fb3f9de43d6ed04c5a8e975107ada5b $
  $Date: 2019-12-04 08:24:31 $
  
  FORKID {4E9DFE89-DA1C-4531-98C9-7FECF672BD47}
*/

description = "Dumper";
vendor = "Autodesk";
vendorUrl = "http://www.autodesk.com";
legal = "Copyright (C) 2012-2016 by Autodesk, Inc.";
certificationLevel = 2;

longDescription = "Use this post to understand which information is available when developing a new post. The post will output the primary information for each entry function being called.";

extension = "dmp";
// using user code page

capabilities = CAPABILITY_INTERMEDIATE;

allowMachineChangeOnSection = true;
allowHelicalMoves = true;
allowSpiralMoves = true;
allowedCircularPlanes = undefined; // allow any circular motion
maximumCircularSweep = toRad(1000000);
minimumCircularRadius = spatial(0.001, MM);
maximumCircularRadius = spatial(1000000, MM);

// user-defined properties
properties = {
  showParameters: true, // displays parameters
  showTool: true, // display tool details
  showState: true, // show the commonly interesting current state
  expandCycles: true, // enable to expand cycles when supported
  showTCP: false // enable to show xyz positions in Part system
};

// user-defined property definitions
propertyDefinitions = {
  showParameters: {title:"Show Parameter values", description:"If enabled, all Parameter values will be displayed", type:"boolean"},
  showTool: {title:"Show Tool values", description:"If enabled, all Tool values will be displayed", type:"boolean"},
  showState: {title:"Show state", description:"Shows the commonly interesting current state.", type:"boolean"},
  expandCycles: {title:"Expand cycles", description:"If enabled, unhandled cycles are expanded.", type:"boolean"},
  showTCP: {title:"Show TCP values", description:"If enabled, XYZ positions are shown in the Setup system.  Disable to show the coordinates in the Working Plane system", type:"boolean"}
};

var spatialFormat = createFormat({decimals:6});
var angularFormat = createFormat({decimals:6, scale:DEG});
var rpmFormat = createFormat({decimals:6});
var otherFormat = createFormat({decimals:6});

var expanding = false;

function toString(value) {
  if (typeof value == "string") {
    return "'" + value + "'";
  } else {
    return value;
  }
}

function dumpImpl(name, text) {
  writeln(getCurrentRecordId() + ": " + name + "(" + text + ")");
}

function dump(name, _arguments) {
  var result = getCurrentRecordId() + ": " + (expanding ? "EXPANDED " : "") + name + "(";
  for (var i = 0; i < _arguments.length; ++i) {
    if (i > 0) {
      result += ", ";
    }
    if (typeof _arguments[i] == "string") {
      result += "'" + _arguments[i] + "'";
    } else {
      result += _arguments[i];
    }
  }
  result += ")";
  writeln(result);
}

function onMachine() {
  dump("onMachine", arguments);
  if (machineConfiguration.getVendor()) {
    writeln("  " + "Vendor" + ": " + machineConfiguration.getVendor());
  }
  if (machineConfiguration.getModel()) {
    writeln("  " + "Model" + ": " + machineConfiguration.getModel());
  }
  if (machineConfiguration.getDescription()) {
    writeln("  " + "Description" + ": "  + machineConfiguration.getDescription());
  }
}

function onOpen() {
  writeln("  Post Engine Version = " + getVersion());
  dump("onOpen", arguments);
}

function onPassThrough() {
  dump("onPassThrough", arguments);
}

function onComment() {
  dump("onComment", arguments);
}

/** Write the current state. */
function dumpState() {
  if (!properties.showState) {
    return;
  }

  writeln("  STATE position=[" + spatialFormat.format(getCurrentPosition().x) + ", " + spatialFormat.format(getCurrentPosition().y) + ", " + spatialFormat.format(getCurrentPosition().z) + "]");
  if ((currentSection.getType() == TYPE_MILLING) || (currentSection.getType() == TYPE_TURNING)) {
    writeln("  STATE spindleSpeed=" + rpmFormat.format(spindleSpeed));
  }
  if (currentSection.getType() == TYPE_JET) {
    writeln("  STATE power=" + (power ? "ON" : "OFF"));
  }
  // writeln("  STATE movement=" + movement);
  // writeln("  STATE feedrate=" + spatialFormat.format(feedrate));
  // writeln("  STATE compensationOffset=" + compensationOffset);

  var id;
  switch (radiusCompensation) {
  case RADIUS_COMPENSATION_OFF:
    id = "RADIUS_COMPENSATION_OFF";
    break;
  case RADIUS_COMPENSATION_LEFT:
    id = "RADIUS_COMPENSATION_LEFT";
    break;
  case RADIUS_COMPENSATION_RIGHT:
    id = "RADIUS_COMPENSATION_RIGHT";
    break;
  }
  if (id != undefined) {
    writeln("  STATE radiusCompensation=" + id + " // " + RADIUS_COMPENSATION_MAP[radiusCompensation]);
  } else {
    writeln("  STATE radiusCompensation=" + radiusCompensation + " // " + RADIUS_COMPENSATION_MAP[radiusCompensation]);
  }
}

function onSection() {
  dump("onSection", arguments);

  var name;
  for (name in currentSection) {
    value = currentSection[name];
    if (typeof value != "function") {
      writeln("  currentSection." + name + "=" + toString(value));
    }
  }

  if (properties.showTool) {
    for (name in tool) {
      value = tool[name];
      if (typeof value != "function") {
        writeln("  tool." + name + "=" + toString(value));
      }
    }

    {
      var shaft = tool.shaft;
      if (shaft && shaft.hasSections()) {
        var n = shaft.getNumberOfSections();
        for (var i = 0; i < n; ++i) {
          writeln("  tool.shaft[" + i + "] H=" + shaft.getLength(i) + " D=" + shaft.getDiameter(i));
        }
      }
    }

    {
      var holder = tool.holder;
      if (holder && holder.hasSections()) {
        var n = holder.getNumberOfSections();
        for (var i = 0; i < n; ++i) {
          writeln("  tool.holder[" + i + "] H=" + holder.getLength(i) + " D=" + holder.getDiameter(i));
        }
      }
    }
  }

  if (currentSection.isPatterned && currentSection.isPatterned()) {
    var patternId = currentSection.getPatternId();
    var sections = [];
    var first = true;
    for (var i = 0; i < getNumberOfSections(); ++i) {
      var section = getSection(i);
      if (section.getPatternId() == patternId) {
        if (i < getCurrentSectionId()) {
          first = false; // not the first pattern instance
        }
        if (i != getCurrentSectionId()) {
          sections.push(section.getId());
        }
      }
    }
    writeln("  >>> Pattern instances: " + sections);
    if (!first) {
      // writeln("  SKIPPING PATTERN INSTANCE");
      // skipRemainingSection();
    }
  }

  if (properties.showTCP) {
    setRotation(currentSection.workPlane); // TCP mode
  } else {
    cancelTransformation();
  }

  dumpState();
}

function onSectionSpecialCycle() {
  dump("onSectionSpecialCycle", arguments);
  writeln("  cycle: " +  toString(currentSection.getFirstCycle()));
}

function onPower() {
  dump("onPower", arguments);
}

function onProbe() {
  dump("onProbe", arguments);
}

function onSpindleSpeed() {
  dump("onSpindleSpeed", arguments);
}

function onParameter() {
  if (properties.showParameters) {
    dump("onParameter", arguments);
  }
}

function onDwell() {
  dump("onDwell", arguments);
}

function onCyclePath() {
  dump("onCyclePath", arguments);

  writeln("  cycleType=" + toString(cycleType));
  for (var name in cycle) {
    value = cycle[name];
    if (typeof value != "function") {
      writeln("  cycle." + name + "=" + toString(value));
    }
  }
}

function onCycle() {
  dump("onCycle", arguments);

  writeln("  cycleType=" + toString(cycleType));
  for (var name in cycle) {
    value = cycle[name];
    if (typeof value != "function") {
      writeln("  cycle." + name + "=" + toString(value));
    }
  }
}

function onCyclePoint(x, y, z) {
  dump("onCyclePoint", arguments);

  if (properties.expandCycles) {

    switch (cycleType) {
    case "drilling": // G81 style
    case "counter-boring": // G82 style
    case "chip-breaking": // G73 style
    case "deep-drilling": // G83 style
    case "break-through-drilling":
    case "gun-drilling":
    case "tapping":
    case "left-tapping": // G74 style
    case "right-tapping": // G84 style
    case "tapping-with-chip-breaking":
    case "left-tapping-with-chip-breaking":
    case "right-tapping-with-chip-breaking":
    case "reaming": // G85 style
    case "boring": // G89 style
    case "stop-boring": // G86 style
    case "fine-boring": // G76 style
    case "back-boring": // G87 style
    case "manual-boring":
    case "bore-milling":
    case "thread-milling":
    case "circular-pocket-milling":
      expanding = true;
      expandCyclePoint(x, y, z);
      expanding = false;
      break;
    default:
      writeln("  CYCLE CANNOT BE EXPANDED");
    }
  }

  dumpState();
}

function onCycleEnd() {
  dump("onCycleEnd", arguments);
}

function onCyclePathEnd() {
  dump("onCyclePathEnd", arguments);
}

/**
  Returns the string id for the specified movement. Returns the movement id as
  a string if unknown.
*/
function getMovementStringId(movement, jet) {
  switch (movement) {
  case MOVEMENT_RAPID:
    return "rapid";
  case MOVEMENT_LEAD_IN:
    return "lead in";
  case MOVEMENT_CUTTING:
    return "cutting";
  case MOVEMENT_LEAD_OUT:
    return "lead out";
  case MOVEMENT_LINK_TRANSITION:
    return !jet ? "transition" : "bridging";
  case MOVEMENT_LINK_DIRECT:
    return "direct";
  case MOVEMENT_RAMP_HELIX:
    return !jet ? "helix ramp" : "circular pierce";
  case MOVEMENT_RAMP_PROFILE:
    return !jet ? "profile ramp" : "profile pierce";
  case MOVEMENT_RAMP_ZIG_ZAG:
    return !jet ? "zigzag ramp" : "linear pierce";
  case MOVEMENT_RAMP:
    return !jet ? "ramp" : "pierce";
  case MOVEMENT_PLUNGE:
    return !jet ? "plunge" : "pierce";
  case MOVEMENT_PREDRILL:
    return "predrill";
  case MOVEMENT_EXTENDED:
    return "extended";
  case MOVEMENT_REDUCED:
    return "reduced";
  case MOVEMENT_FINISH_CUTTING:
    return "finish cut";
  case MOVEMENT_HIGH_FEED:
    return "high feed";
  default:
    return String(movement);
  }
}

function onMovement(movement) {
  var jet = tool.isJetTool && tool.isJetTool();
  var id;
  switch (movement) {
  case MOVEMENT_RAPID:
    id = "MOVEMENT_RAPID";
    break;
  case MOVEMENT_LEAD_IN:
    id = "MOVEMENT_LEAD_IN";
    break;
  case MOVEMENT_CUTTING:
    id = "MOVEMENT_CUTTING";
    break;
  case MOVEMENT_LEAD_OUT:
    id = "MOVEMENT_LEAD_OUT";
    break;
  case MOVEMENT_LINK_TRANSITION:
    id = jet ? "MOVEMENT_BRIDGING" : "MOVEMENT_LINK_TRANSITION";
    break;
  case MOVEMENT_LINK_DIRECT:
    id = "MOVEMENT_LINK_DIRECT";
    break;
  case MOVEMENT_RAMP_HELIX:
    id = jet ? "MOVEMENT_PIERCE_CIRCULAR" : "MOVEMENT_RAMP_HELIX";
    break;
  case MOVEMENT_RAMP_PROFILE:
    id = jet ? "MOVEMENT_PIERCE_PROFILE" : "MOVEMENT_RAMP_PROFILE";
    break;
  case MOVEMENT_RAMP_ZIG_ZAG:
    id = jet ? "MOVEMENT_PIERCE_LINEAR" : "MOVEMENT_RAMP_ZIG_ZAG";
    break;
  case MOVEMENT_RAMP:
    id = "MOVEMENT_RAMP";
    break;
  case MOVEMENT_PLUNGE:
    id = jet ? "MOVEMENT_PIERCE" : "MOVEMENT_PLUNGE";
    break;
  case MOVEMENT_PREDRILL:
    id = "MOVEMENT_PREDRILL";
    break;
  case MOVEMENT_EXTENDED:
    id = "MOVEMENT_EXTENDED";
    break;
  case MOVEMENT_REDUCED:
    id = "MOVEMENT_REDUCED";
    break;
  case MOVEMENT_HIGH_FEED:
    id = "MOVEMENT_HIGH_FEED";
    break;
  }
  if (id != undefined) {
    dumpImpl("onMovement", id + " /*" + getMovementStringId(movement, jet) + "*/");
  } else {
    dumpImpl("onMovement", movement + " /*" + getMovementStringId(movement, jet) + "*/");
  }
}

var RADIUS_COMPENSATION_MAP = {0:"off", 1:"left", 2:"right"};

function onRadiusCompensation() {
  var id;
  switch (radiusCompensation) {
  case RADIUS_COMPENSATION_OFF:
    id = "RADIUS_COMPENSATION_OFF";
    break;
  case RADIUS_COMPENSATION_LEFT:
    id = "RADIUS_COMPENSATION_LEFT";
    break;
  case RADIUS_COMPENSATION_RIGHT:
    id = "RADIUS_COMPENSATION_RIGHT";
    break;
  }
  dump("onRadiusCompensation", arguments);
  if (id != undefined) {
    writeln("  radiusCompensation=" + id + " // " + RADIUS_COMPENSATION_MAP[radiusCompensation]);
  } else {
    writeln("  radiusCompensation=" + radiusCompensation + " // " + RADIUS_COMPENSATION_MAP[radiusCompensation]);
  }
}

function onRapid() {
  dump("onRapid", arguments);
}

function onLinear() {
  dump("onLinear", arguments);
}

function onRapid5D() {
  dump("onRapid5D", arguments);
}

function onLinear5D() {
  dump("onLinear5D", arguments);
}

function onCircular(clockwise, cx, cy, cz, x, y, z, feed) {
  dump("onCircular", arguments);
  writeln("  direction: " + (clockwise ? "CW" : "CCW"));
  writeln("  sweep: " + angularFormat.format(getCircularSweep()) + "deg");
  var n = getCircularNormal();
  var plane = "";
  switch (getCircularPlane()) {
  case PLANE_XY:
    plane = "(XY)";
    break;
  case PLANE_ZX:
    plane = "(ZX)";
    break;
  case PLANE_YZ:
    plane = "(YZ)";
    break;
  }
  writeln("  normal: X=" + spatialFormat.format(n.x) + " Y=" + spatialFormat.format(n.y) + " Z=" + spatialFormat.format(n.z) + " " + plane);
  if (isSpiral()) {
    writeln("  spiral");
    writeln("  start radius: " + spatialFormat.format(getCircularStartRadius()));
    writeln("  end radius: " + spatialFormat.format(getCircularRadius()));
    writeln("  delta radius: " + spatialFormat.format(getCircularRadius() - getCircularStartRadius()));
  } else {
    writeln("  radius: " + spatialFormat.format(getCircularRadius()));
  }
  if (isHelical()) {
    writeln("  helical pitch: " + spatialFormat.format(getHelicalPitch()));
  }
}

function onCommand(command) {
  if (isWellKnownCommand(command)) {
    dumpImpl("onCommand", getCommandStringId(command));
  } else {
    dumpImpl("onCommand", command);
  }
}

function onSectionEnd() {
  dump("onSectionEnd", arguments);

  dumpState();
}

function onSectionEndSpecialCycle() {
  dump("onSectionEndSpecialCycle", arguments);
  writeln("  cycle: " +  toString(currentSection.getFirstCycle()));
}

function onClose() {
  dump("onClose", arguments);
}

//Additive Specific Functions

function onBedTemp(temp, wait) {
  var state = "";
  dump("onBedTemp", arguments);
  writeln("  Temperature : " + spatialFormat.format(temp));
  if (wait) {
    state = "true";
  } else {
    state = false;
  }
  writeln("  Wait : " + state);
}

function onExtruderChange(id) {
  dump("onExtruderChange", arguments);
  writeln("  Extruder id : " + spatialFormat.format(id));
}

function onExtrusionReset() {
  dump("onExtrusionReset", arguments);
}

function onExtruderTemp(temp, wait, id) {
  var state = "";
  dump("onExtruderTemp", arguments);
  writeln("  Temperature : " + spatialFormat.format(temp));
  if (wait) {
    state = "true";
  } else {
    state = false;
  }
  writeln("  Wait : " + state);
  writeln("  Extruder id : " + spatialFormat.format(id));
}

function onFanSpeed(speed, id) {
  dump("onFanSpeed", arguments);
  writeln("  Fan speed : " + spatialFormat.format(speed));
  writeln("  Fan id : " + spatialFormat.format(id));
}

function onLayer() {
  dump("onLayer", arguments);
}

function onLinearExtrude(_x, _y, _z, feed, extDist) {
  dump("onLinearExtrude", arguments);
  writeln("  feedRate : " + spatialFormat.format(feed));
  writeln("  extrusion distance : " + spatialFormat.format(extDist));
}

function onPrime() {
  dump("onPrime", arguments);
}
