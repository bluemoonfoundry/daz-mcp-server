"""DazScript fragments and the script registry for DazScriptServer."""
from __future__ import annotations

import dazpy.exceptions as daz_exc
from dazpy.aio import AsyncDazClient


async def _register_scripts(client: AsyncDazClient) -> None:
    """Register all built-in scripts with DazScriptServer.

    Called at startup and automatically on 404 (DAZ Studio restarted and cleared
    the session registry). Silently skips remaining entries on connection failure.
    """
    for script_id, (description, script_text) in _REGISTRY.items():
        try:
            await client.register_script(script_id, script_text, description)
        except (daz_exc.ConnectionError, daz_exc.TimeoutError):
            break  # DAZ Studio not running; remaining registrations skipped


# ---------------------------------------------------------------------------
# Embedded DazScript fragments
#
# All scripts must be wrapped in (function(){ ... })() — DazScript does not
# allow bare top-level return statements.
#
# Global objects available in the DAZ Studio scripting environment:
#   Scene   – the current DzScene
#   App     – the DzApp (application) object
#   MainWindow – the main window
# ---------------------------------------------------------------------------

_RESOLVE_NODE_JS = """\
    function resolveNode(id) {
        if (id === undefined || id === null || String(id) === "") {
            throw new Error("Node id is required");
        }
        var s = String(id);
        if (/^[0-9]+$/.test(s) && typeof Scene.findNodeByElementID === "function") {
            var byId = Scene.findNodeByElementID(parseInt(s, 10));
            if (!byId) throw new Error("Node not found: elementID " + s);
            return byId;
        }
        var slash = s.lastIndexOf("/");
        if (slash > 0) {
            var parent = resolveNode(s.substring(0, slash));
            var childPart = s.substring(slash + 1);
            var child = null;
            if (typeof parent.findNodeChildByLabel === "function") {
                child = parent.findNodeChildByLabel(childPart, true);
            }
            if (!child && typeof parent.findNodeChild === "function") {
                child = parent.findNodeChild(childPart, true);
            }
            if (!child) throw new Error("Node not found: " + s);
            return child;
        }
        var matches = [];
        var i, n, p, bits;
        for (i = 0; i < Scene.getNumNodes(); i++) {
            n = Scene.getNode(i);
            if (!n) continue;
            if (n.getLabel() === s || n.getName() === s) matches.push(n);
        }
        if (matches.length === 1) return matches[0];
        if (matches.length === 0) throw new Error("Node not found: " + s);
        bits = [];
        for (i = 0; i < matches.length && i < 12; i++) {
            n = matches[i];
            p = n.getNodeParent ? n.getNodeParent() : null;
            bits.push(n.getLabel() + " name=" + n.getName() + " elementID=" + n.elementID + " parent=" + (p ? p.getLabel() : ""));
        }
        throw new Error("Ambiguous node '" + s + "' (" + matches.length + " matches). Use elementID or Parent/Label. " + bits.join(" | "));
    }
"""

# Returns: {sceneFile, selectedNode, figures:[{name,label,type}], cameras:[...],
#           lights:[...], totalNodes}
# Uses skeleton list (characters + clothing) rather than all nodes (potentially thousands).

# args: {nodeLabel} — label, internal name, elementID, or Parent/Label
# Returns: {name, label, type, elementID, parent, properties:{label:value}}

# args: {nodeLabel, propertyName, value}
# Returns: {node, property, value}
# Matches propertyName against both display label and internal name.

# args: {outputPath?}
# Returns: {success}
# Render options are set directly on the DzRenderOptions object (Qt property syntax).

# args: {filePath, merge}
# Returns: {success, file}
# openFile(path, true)  → merge into current scene
# openFile(path, false) → replace current scene

# args: {nodeLabel, includeZero}
# includeZero: if true, return all morphs; if false, only return morphs with non-zero values
# Returns: {morphs: [{label, name, value, path}], count}
# Lists all numeric properties (morphs) on a node

# args: {nodeLabel, pattern, includeZero}
# pattern: substring to search for in morph label or name (case-insensitive)
# includeZero: if true, return all matching morphs; if false, only non-zero values
# Returns: {morphs: [{label, name, value, path}], count, pattern}
# Searches for morphs matching a pattern

# args: {nodeLabel, maxDepth}
# maxDepth: maximum recursion depth (default 10, 0 = unlimited)
# Returns: {node, children: [{node, children}], totalDescendants}
# Gets complete hierarchy tree for a node

# args: {nodeLabel}
# Returns: {node, children: [{label, name, type}], count}
# Lists direct children of a node

# args: {nodeLabel}
# Returns: {node, parent: {label, name, type} | null}
# Gets parent node of a node

# args: {nodeLabel, parentLabel, maintainWorldTransform}
# maintainWorldTransform: if true, adjust local transform to maintain world position
# Returns: {success, node, newParent, previousParent}
# Sets parent of a node

# args: {characterLabel, targetX, targetY, targetZ, mode}
# mode: "eyes", "head", "neck", "torso", "full"
# Returns: {success, character, mode, rotatedBones}
# Makes character look at a world-space point with cascading body involvement

# args: {sourceLabel, targetLabel, mode}
# mode: "eyes", "head", "neck", "torso", "full" (default: "head")
# Returns: {success, source, target, mode, targetPosition}
# Makes source character look at target character's head position

# args: {characterLabel, side, targetX, targetY, targetZ}
# side: "left" or "right"
# Returns: {success, character, side, bones}
# Position arm/hand to reach toward world-space point using pseudo-IK

# args: {char1Label, char2Label, interactionType, distance}
# interactionType: "hug", "shoulder-arm", "handshake", "face-each-other"
# distance: optional override for character spacing (cm)
# Returns: {success, char1, char2, interactionType, applied}
# Coordinate two characters for interactive poses

# args: {operations: [{nodeLabel, propertyName, value}]}
# Returns: {results: [{success, node, property, value, error}], successCount, failureCount}
# Batch property setting with individual error handling for each operation

# args: {nodeLabels: [string], transforms: {propertyName: value}}
# Returns: {results: [{success, node, applied, error}], successCount, failureCount}
# Apply same transform properties to multiple nodes

# args: {nodeLabels: [string], visible: boolean}
# Returns: {results: [{success, node, visible, error}], successCount, failureCount}
# Show or hide multiple nodes

# args: {nodeLabels: [string], addToSelection: boolean}
# Returns: {selected: [labels], count}
# Select multiple nodes (replace or add to current selection)

# args: {cameraLabel}
# Returns: {success, camera, previousCamera}
# Set which camera is active in the viewport

# args: {cameraLabel, targetLabel, distance, angleHorizontal, angleVertical}
# Returns: {success, camera, target, position}
# Position camera orbiting around a target node at specified angle and distance

# args: {cameraLabel, nodeLabel, distance}
# Returns: {success, camera, node, position}
# Frame camera to show a node by positioning at calculated distance

# args: {cameraLabel}
# Returns: {preset: {transforms, label}}
# Save camera position and rotation as preset data

# args: {cameraLabel, preset}
# Returns: {success, camera, applied}
# Restore camera position and rotation from preset data

# args: {cameraLabel, outputPath}
# Returns: {success, camera, outputPath}
# Render from specific camera (doesn't change active viewport camera)

# args: none
# Returns: {renderToFile, currentCamera, aspectRatio, aspectWidth, aspectHeight}
# Get current render settings

# args: {cameras: [labels], outputDir, baseFilename}
# Returns: {success, rendered: [{camera, outputPath}], total}
# Render from multiple cameras in sequence

# args: {startFrame, endFrame, outputDir, filenamePattern, camera}
# Returns: {success, rendered: [{frame, outputPath}], total}
# Render animation frame range

# args: {nodeLabel, propertyName, frame, value}
# Returns: {success, node, property, frame, value}
# Set a keyframe on a property at specified frame

# args: {nodeLabel, propertyName}
# Returns: {keyframes: [{frame, value}], count}
# Get all keyframes for a property

# args: {nodeLabel, propertyName, frame}
# Returns: {success, node, property, frame, removed}
# Remove a keyframe at specified frame

# args: {nodeLabel, propertyName}
# Returns: {success, node, property, removed}
# Remove all keyframes from a property

# args: {frame}
# Returns: {success, frame, previousFrame}
# Set current animation frame

# args: {startFrame, endFrame}
# Returns: {success, startFrame, endFrame, previousStart, previousEnd}
# Set animation frame range

# args: none
# Returns: {currentFrame, startFrame, endFrame, fps}
# Get animation timeline info

# ---------------------------------------------------------------------------
# Phase 1: Spatial Query Scripts
# ---------------------------------------------------------------------------

# args: {nodeLabel}
# Returns: {node, world_position, local_position, rotation, scale}

# args: {nodeLabel}
# Returns: {node, min, max, center, width, height, depth}

# args: {node1Label, node2Label}
# Returns: {node1, node2, distance, vector, horizontal_distance, vertical_distance}

# args: {node1Label, node2Label}
# Returns: {node1, node2, distance, direction, angle_horizontal, angle_vertical,
#           relative_position, overlapping}
# Provides natural language spatial relationship between two nodes.
# Angles are from node1's perspective looking toward node2.
# angle_horizontal: 0=front(+Z), 90=right, 180=back, -90=left (in node1 local space)
# angle_vertical: positive=above, negative=below

# args: {node1Label, node2Label}
# Returns: {node1, node2, overlapping, penetration_depth, suggestion}

# ---------------------------------------------------------------------------
# Phase 1: Property Introspection Scripts
# ---------------------------------------------------------------------------

# args: {nodeLabel, propertyType}
# propertyType: "all" | "numeric" | "transform" | "bool" | "string"
# Returns: {node, properties:[{label,name,type,value,min,max,path,is_animatable}], count}

# args: {nodeLabel, propertyName}
# Returns: {label, name, type, current_value, default_value, min, max,
#           is_animatable, path}

# ---------------------------------------------------------------------------
# Phase 1: Lighting Preset Script
# ---------------------------------------------------------------------------

# args: {preset, subjectLabel}
# preset: "three-point" | "rembrandt" | "butterfly" | "split" | "loop"
# Returns: {preset, subject, lights_created:[{label,type,position}], environment_mode}
# Creates lights relative to subject bounding box center.
# Genesis figures face +Z so "front" = positive Z side.

# ---------------------------------------------------------------------------
# Phase 1: Scene Validation Script
# ---------------------------------------------------------------------------

# args: none
# Returns: {valid, issues:[{type,severity,nodes,description,suggestion}],
#           warnings:[...], score, score_breakdown}

# args: {preset, maxSamples, renderQuality}
# Returns: {preset, propertiesSet: [{property, value}], note}
# Sets Iray render quality via Max Samples and Render Quality properties on the
# active renderer options.  Falls back gracefully if properties are not found.

# ---------------------------------------------------------------------------
# Phase 2 script constants
# ---------------------------------------------------------------------------


# args: {char1Label, char2Label,
#        dialogueBeats: [{speaker, startFrame, endFrame, emotion, gesture?}]}
# Returns: {char1, char2, beatsApplied: [{beat, actions}], totalFrames}
# Choreograph animated conversation between two characters

# args: {description, characters: []}
# description: Natural language scene description
# characters: List of character labels already in scene
# Returns: {sceneType, actions: [], suggestions: []} (cameras are built in Python by dazpy)
# Generate a complete scene from natural language description

# args: {characterLabel, waypoints: [{position: {x, y, z}, frame: int}], pathType, walkingStyle}
# pathType: "straight", "curved", "circular"
# walkingStyle: "casual", "hurried", "sneaking"
# Returns: {character, waypoints: int, pathType, frameRange, distance}
# Animate character movement along a path

# args: {characters: [], arrangement, spacing, facing, centerPosition?}
# arrangement: "line", "semicircle", "triangle", "conversation-circle"
# facing: "center", "camera", "forward"
# Returns: {characters: [{label, position, rotation}], arrangement, spacing}
# Position multiple characters in formation

# args: {actionType, characters: [], startFrame, duration}
# actionType: "handshake", "hug", "fight", "dance"
# Returns: {actionType, characters: [], positions: [], suggestions: []}
# Choreograph simple action between characters

# ---------------------------------------------------------------------------
# Phase 4.8: Lighting Animation scripts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 4.10: Focus & DOF scripts
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Phase 4.11: Visual Composition scripts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 4.12: Multi-Scene Management scripts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 4.13: Performance Timing scripts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 5: Materials / Surfaces
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 5: Direct morph setting
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 5: Node lifecycle
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 5: Light management
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 5: Camera management
# ---------------------------------------------------------------------------


_CREATE_CAMERA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = new DzBasicCamera();
    cam.setLabel(args.label || "Camera");
    Scene.addNode(cam);
    // DAZ Studio leaves the internal name ("" via getName()) unset for a node
    // created via script + Scene.addNode() (confirmed live), unlike a UI-created
    // one. dazpy's node lookup by name (used by daz_list_cameras) needs a
    // non-empty, unique name to resolve this camera afterward -- setName() does
    // NOT auto-uniquify on collision (confirmed live: Scene.findNode() then just
    // returns whichever node got the name first), so dedupe manually.
    var baseName = String(args.label || "Camera").replace(/[^A-Za-z0-9_]/g, "_") || "Camera";
    var candidateName = baseName, nameSuffix = 1;
    while (Scene.findNode(candidateName)) {
        candidateName = baseName + "_" + (++nameSuffix);
    }
    cam.setName(candidateName);
    var xp = cam.findProperty("XTranslate");
    var yp = cam.findProperty("YTranslate");
    var zp = cam.findProperty("ZTranslate");
    if (xp) xp.setValue(args.x !== undefined ? args.x : 0);
    if (yp) yp.setValue(args.y !== undefined ? args.y : 150);
    if (zp) zp.setValue(args.z !== undefined ? args.z : 300);
    if (args.focalLength) {
        var fp = cam.getFocalLengthControl();
        if (fp) fp.setValue(args.focalLength);
    }
    if (args.aimAtLabel) {
        var target = Scene.findNodeByLabel(args.aimAtLabel);
        if (!target) target = Scene.findNode(args.aimAtLabel);
        if (target) {
            var bbox = target.getWSBoundingBox();
            var cx = (bbox.minX + bbox.maxX) / 2;
            var cy = (bbox.minY + bbox.maxY) / 2;
            var cz = (bbox.minZ + bbox.maxZ) / 2;
            cam.aimAt(new DzVec3(cx, cy, cz));
        }
    }
    var pos = cam.getWSPos();
    var fl = cam.getFocalLengthControl();
    return {
        label: cam.getLabel(),
        position: { x: pos.x, y: pos.y, z: pos.z },
        focal_length: fl ? fl.getValue() : null
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Scene file operations
# ---------------------------------------------------------------------------


# args: {engine}
# Returns: {success, engine, renderType, renderTypeName, activeRenderer,
#           activeRendererClass, warning?}
# DS6 Engine dropdown is DzRenderOptions.renderType, not getActiveRenderer().

# ---------------------------------------------------------------------------
# Phase 5: Pose reset
# ---------------------------------------------------------------------------


_RESOLVE_DFORCE_PROVIDER_JS = """
    function resolveDforceProvider(nodeLabel, materialName) {
        var node = Scene.findNodeByLabel(nodeLabel);
        if (!node) node = Scene.findNode(nodeLabel);
        if (!node) throw new Error("Node not found: " + nodeLabel);
        var obj = node.getObject();
        if (!obj) throw new Error("Node has no geometry: " + nodeLabel);
        var shape = obj.getCurrentShape();
        if (!shape) throw new Error("Node has no shape: " + nodeLabel);
        if (typeof shape.findSimulationSettingsProvider !== "function") {
            throw new Error("findSimulationSettingsProvider not available on this shape/DS version");
        }
        var matName = materialName;
        if (!matName) {
            if (shape.getNumMaterials() === 0) throw new Error("Node has no materials: " + nodeLabel);
            matName = shape.getMaterial(0).getName();
        }
        var provider = shape.findSimulationSettingsProvider(matName);
        if (!provider) {
            var names = [];
            if (typeof shape.getSimulationProviderNames === "function") {
                var pn = shape.getSimulationProviderNames();
                for (var i = 0; i < pn.length; i++) names.push(pn[i]);
            }
            throw new Error("No dForce simulation settings for material '" + matName +
                "' on '" + nodeLabel + "' (dForce modifier may be missing). Available: " + names.join(", "));
        }
        return { node: node, materialName: matName, provider: provider };
    }
"""


# ---------------------------------------------------------------------------
# Phase 6.4: Material preset scripts
# ---------------------------------------------------------------------------


# WHY THIS EXISTS: content merged/imported into a scene as raw DSON (a
# hand-authored .duf, or content run through a from-scratch scene-merge
# pipeline) reliably instantiates as the legacy DzDefaultMaterial ("DAZ
# Studio Default (RSL)" in the UI) instead of DzUberIrayMaterial, no matter
# how complete its "studio_material_channels" data is - confirmed by direct
# isolation testing (byte-for-byte real-asset channel data still comes back
# as DzDefaultMaterial). Daz's scene-graph *parser* apparently never
# promotes a material past DzDefaultMaterial from raw JSON alone.
#
# What does work: going through Daz's own preset-*application* codepath
# instead of describing a shader in JSON - the same thing that runs when a
# user drags a Shader Preset from Smart Content onto a figure
# (App.getContentMgr().openFile() on a selected node). That path builds a
# real native shader object rather than parsing one, and reliably flips
# every material zone on the node from DzDefaultMaterial to genuine
# DzUberIrayMaterial - confirmed live. It also resets every channel to
# shader defaults, so callers should follow this with daz_get_material /
# daz_set_material_property per zone to restore actual diffuse/PBR values
# and texture maps.
#
# If presetPath is omitted, this resolves Daz Studio's own stock "!Iray
# Uber Base" shader preset (ships with every installation, author "DAZ 3D",
# ~650 bytes, just the "studio/material/uber_iray" marker with no channel
# data - its only job is to flip the shader class) via
# DzContentMgr.getAbsolutePath(), so callers don't need to know where the
# user's content library lives.
_CONVERT_TO_IRAY_UBER_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;
    var presetPath = args.presetPath;

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    if (!presetPath) {
        presetPath = App.getContentMgr().getAbsolutePath(
            "Shader Presets/Iray/DAZ Uber/!Iray Uber Base.duf", false, "");
        if (!presetPath) {
            throw new Error(
                "No presetPath given and the stock 'Iray Uber Base' preset could not be " +
                "located in any configured content directory. Pass an explicit presetPath."
            );
        }
    }

    function zoneList() {
        var obj = node.getObject();
        if (!obj) throw new Error("Node has no geometry: " + nodeLabel);
        var shape = obj.getCurrentShape();
        if (!shape) throw new Error("Node has no material shape: " + nodeLabel);
        var zones = [];
        for (var i = 0; i < shape.getNumMaterials(); i++) {
            var m = shape.getMaterial(i);
            zones.push({ label: m.getLabel(), shader: m.className() });
        }
        return zones;
    }

    var before = zoneList();

    // Select only the target node so the preset applies to it alone. Node
    // selection alone is NOT sufficient - Shader Preset application acts on
    // the currently-selected SURFACE(S) (Surfaces-pane-level selection), not
    // just the selected node. Without explicitly selecting each material
    // zone too, openFile() below returns true (no error) but silently
    // converts nothing - confirmed live: a node selected via node.select(true)
    // alone stayed DzDefaultMaterial after a successful-looking openFile()
    // call, and only started converting once every DzMaterial on the shape
    // was also explicitly .select(true)'d.
    Scene.selectAllNodes(false);
    node.select(true);
    var shapeForSelect = node.getObject().getCurrentShape();
    for (var s = 0; s < shapeForSelect.getNumMaterials(); s++) {
        shapeForSelect.getMaterial(s).select(true);
    }

    var ioSettings = new DzFileIOSettings();
    var ok = App.getContentMgr().openFile(presetPath, ioSettings, false);
    if (!ok) throw new Error("Failed to apply shader preset: " + presetPath);

    var after = zoneList();

    return {
        success: true,
        node: node.getLabel(),
        preset: presetPath,
        before: before,
        after: after
    };
})()
"""


# ---------------------------------------------------------------------------
# Phase 6.5: Figure diagnostics scripts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 6.6: Scene export script (shared; format param selects FBX vs OBJ)
# ---------------------------------------------------------------------------


_IMPORT_OBJ_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var filePath = args.filePath;
    var scaleFactor = args.scaleFactor !== undefined ? parseFloat(args.scaleFactor) : 1.0;
    if (!filePath) throw new Error("filePath is required");

    var importMgr = App.getImportMgr();
    if (!importMgr) throw new Error("DzImportMgr not available in this version of DAZ Studio.");
    var importer = typeof importMgr.findImporter === "function" ? importMgr.findImporter(filePath) : null;
    if (!importer && typeof importMgr.findImporterByClassName === "function") {
        importer = importMgr.findImporterByClassName("DzObjImporter");
    }
    if (!importer || typeof importer.readFile !== "function") {
        throw new Error("OBJ importer not available for: " + filePath);
    }

    var settings = new DzFileIOSettings();
    if (typeof importer.getDefaultOptions === "function") importer.getDefaultOptions(settings);
    settings.setFloatValue("Scale", scaleFactor);
    settings.setIntValue("RunSilent", 1);

    var err = importer.readFile(filePath, settings);
    var errCode = (err && typeof err.valueOf === "function") ? err.valueOf() : err;
    if (errCode) {
        var errMsg = (typeof getErrorMessage === "function") ? getErrorMessage(errCode) : ("" + errCode);
        throw new Error("OBJ import failed (" + errCode + "): " + errMsg);
    }

    return {
        success: true,
        file: filePath,
        scale: scaleFactor,
        silent: true
    };
})()
"""


_FIND_ACTIONS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var query = args.query === undefined || args.query === null ? "" : String(args.query);
    if (!query) throw new Error("query is required");
    var maxResults = parseInt(args.maxResults, 10);
    if (isNaN(maxResults) || maxResults < 1) maxResults = 30;
    if (maxResults > 100) maxResults = 100;
    var q = query.toLowerCase();

    var mgr = MainWindow.getActionMgr();
    if (!mgr) throw new Error("MainWindow.getActionMgr() returned null");

    var matches = [];
    var n = mgr.getNumActions();
    var i, a, cn, txt, desc, menu, group, hay;
    for (i = 0; i < n; i++) {
        a = mgr.getAction(i);
        if (!a) continue;
        cn = a.className();
        txt = "";
        desc = "";
        menu = "";
        group = "";
        try { txt = String(a.simpleText || ""); } catch (e1) {}
        try { desc = String(a.description || ""); } catch (e2) {}
        try { menu = String(a.defaultMenu || ""); } catch (e3) {}
        try { group = String(a.actionGroup || ""); } catch (e4) {}
        hay = (cn + " " + txt + " " + desc + " " + menu + " " + group).toLowerCase();
        if (hay.indexOf(q) === -1) continue;
        matches.push({
            className: cn,
            simpleText: txt,
            description: desc,
            defaultMenu: menu,
            actionGroup: group
        });
        if (matches.length >= maxResults) break;
    }
    return {
        query: query,
        count: matches.length,
        scanned: n,
        truncated: matches.length >= maxResults,
        matches: matches
    };
})()
"""

_ERC_FREEZE_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    if (typeof DzERCFreeze !== "function") {
        throw new Error("DzERCFreeze is not available (enable the Property Hierarchy plugin)");
    }
    var controllerNode = resolveNode(args.controllerNode);
    function matchName(item, name) {
        return item.getLabel() === name || item.getName() === name;
    }
    function findProp(node, name) {
        var i, pr, obj, m, ch, j;
        for (i = 0; i < node.getNumProperties(); i++) {
            pr = node.getProperty(i);
            if (matchName(pr, name)) return pr;
        }
        obj = (typeof node.getObject === "function") ? node.getObject() : null;
        if (!obj || typeof obj.getNumModifiers !== "function") return null;
        for (i = 0; i < obj.getNumModifiers(); i++) {
            m = obj.getModifier(i);
            if (!m) continue;
            if (matchName(m, name) && typeof m.getValueChannel === "function") {
                ch = m.getValueChannel();
                if (ch) return ch;
            }
            if (typeof m.getNumProperties === "function") {
                for (j = 0; j < m.getNumProperties(); j++) {
                    pr = m.getProperty(j);
                    if (matchName(pr, name)) return pr;
                }
            }
        }
        return null;
    }
    var controllerProp = findProp(controllerNode, args.controllerProperty);
    if (!controllerProp) {
        throw new Error("Controller property not found: " + args.controllerProperty + " on " + args.controllerNode);
    }
    if (!controllerProp.inherits("DzNumericProperty")) {
        throw new Error("Controller property is not numeric: " + args.controllerProperty);
    }

    var freeze = new DzERCFreeze();
    freeze.setControllerNode(controllerNode);
    freeze.setControllerProperty(controllerProp);
    if (args.restoreFigure !== undefined) freeze.setRestoreFigure(!!args.restoreFigure);
    if (args.restoreRigging !== undefined) freeze.setRestoreRigging(!!args.restoreRigging);
    if (args.applyController !== undefined) freeze.setApplyController(!!args.applyController);
    if (args.keyed !== undefined) freeze.setKeyed(!!args.keyed);

    var freezeLabels = args.freezeNodes;
    var added = [];
    var k, fn, okAdd;
    if (freezeLabels && freezeLabels.length) {
        for (k = 0; k < freezeLabels.length; k++) {
            fn = resolveNode(freezeLabels[k]);
            okAdd = freeze.addPropertiesToFreeze(fn);
            added.push({ node: fn.getLabel(), added: !!okAdd });
        }
    } else {
        okAdd = freeze.addPropertiesToFreeze(controllerNode);
        added.push({ node: controllerNode.getLabel(), added: !!okAdd });
    }

    var frozen = freeze.getPropertiesToFreeze();
    var frozenCount = (frozen && typeof frozen.length !== "undefined") ? frozen.length : 0;
    if (frozenCount === 0) {
        throw new Error("No properties to freeze (values at default?). Change morphs/transforms first.");
    }

    var ok = freeze.doFreeze();
    if (!ok) throw new Error("DzERCFreeze.doFreeze() returned false");
    return {
        success: true,
        controllerNode: controllerNode.getLabel(),
        controllerProperty: controllerProp.getLabel(),
        freezeNodes: added,
        propertiesFrozen: frozenCount
    };
})()
"""

# Content-Library Prop/Figure Support Asset export

# Phase 6.12: Morph Loader Pro

_CREATE_STRAND_HAIR_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var targetLabel = args.targetNodeLabel;

    var target = Scene.findNodeByLabel(targetLabel);
    if (!target) target = Scene.findNode(targetLabel);
    if (!target) throw new Error("Target node not found: " + targetLabel);

    function strandHairLabels() {
        var labels = [];
        for (var i = 0; i < Scene.getNumNodes(); i++) {
            var n = Scene.getNode(i);
            if (n.inherits("DzStrandHairNode")) labels.push(n.getLabel());
        }
        return labels;
    }

    var before = strandHairLabels();

    var mgr = MainWindow.getActionMgr();
    var act = mgr.findAction("DzStrandHairCreateNodeAction");
    if (!act) throw new Error("Action 'DzStrandHairCreateNodeAction' not found in DzActionMgr");

    Scene.selectAllNodes(false);
    target.select(true);

    // This call blocks until the user confirms (or cancels) DAZ Studio's
    // "Create Strand-Based Hair" dialog. That's expected — this script is
    // meant to be run via the async endpoint so the HTTP caller doesn't
    // block waiting for a human to click a button in the DAZ Studio window.
    act.trigger();

    var after = strandHairLabels();
    var newLabels = [];
    for (var i = 0; i < after.length; i++) {
        if (before.indexOf(after[i]) === -1) newLabels.push(after[i]);
    }

    if (newLabels.length === 0) {
        throw new Error(
            "No new Strand-Based Hair node appeared after the action ran. " +
            "The user likely cancelled the confirmation dialog, or DAZ Studio " +
            "is still waiting for it to be confirmed."
        );
    }

    var newNode = Scene.findNodeByLabel(newLabels[0]);
    var obj = newNode.getObject();
    var hasGeometry = !!obj;

    return {
        success: true,
        node: newNode.getLabel(),
        target: target.getLabel(),
        has_geometry: hasGeometry
    };
})()
"""


# Phase 6.12: Wearable Preset save trigger (Bug-Katalog #22 Teil 2)
# Selects the target figure and fires DzWearablesAssetFilterAction. This
# BLOCKS on two native dialogs (a file-save dialog, then a Qt options
# dialog) — must be submitted via the async endpoint. The Python-side
# tool (daz_save_wearable_preset, _ui_automation.py) drives those dialogs
# via Windows UI Automation once this has fired; DzWearablesAssetFilter's
# own doSave() script API reproducibly fails with an unexplained generic
# error and is not used here (see docs/daz-mcp-bridge-bugs.md #22 Teil 2).
_TRIGGER_WEARABLE_SAVE_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var fig = resolveNode(args.figureLabel);
    Scene.selectAllNodes(false);
    fig.select(true);
    var mgr = MainWindow.getActionMgr();
    var act = mgr.findAction("DzWearablesAssetFilterAction");
    if (!act) throw new Error("DzWearablesAssetFilterAction not found in DzActionMgr");
    act.trigger();
    return { success: true, figure: fig.getLabel() };
})()
"""

# Registry entries: script_id → (description, script_text)
# Registered with DazScriptServer on startup so high-level tools call by ID.
_REGISTRY: dict[str, tuple[str, str]] = {
    # Phase 6.6: Scene export
    "vangard-import-obj": (
        "Import a Wavefront OBJ with Scale=1 and RunSilent (no options dialog)",
        _IMPORT_OBJ_SCRIPT,
    ),
    "vangard-find-actions": (
        "Search DzActionMgr actions by className/simpleText/description (no menuBar, no trigger)",
        _FIND_ACTIONS_SCRIPT,
    ),
    "vangard-erc-freeze": (
        "Headless ERC Freeze via DzERCFreeze (Property Hierarchy plugin), not DzERCFreezeAction",
        _ERC_FREEZE_SCRIPT,
    ),
    # Phase 6.13: Strand-Based Hair
    "vangard-create-strand-hair": (
        "Create a native Strand-Based Hair node fit to a target figure via "
        "DzStrandHairCreateNodeAction. BLOCKS on a DAZ Studio confirmation "
        "dialog the user must click — always submit via the async endpoint",
        _CREATE_STRAND_HAIR_SCRIPT,
    ),
    "vangard-trigger-wearable-save": (
        "Select a figure and fire DzWearablesAssetFilterAction (File > Save As > "
        "Wearable(s) Preset) — blocks on native dialogs, submit via async endpoint only; "
        "daz_save_wearable_preset drives the resulting dialogs via UI Automation",
        _TRIGGER_WEARABLE_SAVE_SCRIPT,
    ),
}

