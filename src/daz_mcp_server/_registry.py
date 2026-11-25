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

_LIST_CATEGORIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var contentMgr = App.getContentMgr();
    var parentPath = (args.parentPath || "").replace(/^\\/|\\/$/g, "");
    var categories = [];
    var seen = {};

    for (var i = 0; i < contentMgr.getNumContentDirectories(); i++) {
        var dir = contentMgr.getContentDirectory(i);
        if (!dir) continue;
        var basePath = dir.fullPath;
        var searchPath = parentPath ? basePath + "/" + parentPath : basePath;
        var d = new DzDir(searchPath);
        if (!d.exists()) continue;

        var subdirs = d.entryList([], DzDir.Dirs | DzDir.NoDotAndDotDot);
        for (var j = 0; j < subdirs.length; j++) {
            var name = subdirs[j];
            if (seen[name]) continue;
            seen[name] = true;
            var subdir = new DzDir(d.absoluteFilePath(name));
            var dufFiles = subdir.entryList(["*.duf"], DzDir.Files);
            categories.push({
                name: name,
                path: parentPath ? parentPath + "/" + name : name,
                duf_count: dufFiles.length
            });
        }
    }

    categories.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
    return {parent: args.parentPath || "/", categories: categories, count: categories.length};
})()
"""

_BROWSE_CATEGORY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var contentMgr = App.getContentMgr();
    var categoryPath = (args.categoryPath || "").replace(/^\\/|\\/$/g, "");
    var items = [];
    var seen = {};

    for (var i = 0; i < contentMgr.getNumContentDirectories(); i++) {
        var dir = contentMgr.getContentDirectory(i);
        if (!dir) continue;
        var basePath = dir.fullPath;
        var searchPath = categoryPath ? basePath + "/" + categoryPath : basePath;
        var d = new DzDir(searchPath);
        if (!d.exists()) continue;

        var files = d.entryList(["*.duf"], DzDir.Files);
        for (var j = 0; j < files.length; j++) {
            var fname = files[j];
            if (seen[fname]) continue;
            seen[fname] = true;
            items.push({
                name: fname.replace(/\\.duf$/i, ""),
                filename: fname,
                full_path: searchPath + "/" + fname
            });
        }
    }

    items.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
    return {category: args.categoryPath || "/", items: items, count: items.length};
})()
"""


# args: {char1Label, char2Label,
#        dialogueBeats: [{speaker, startFrame, endFrame, emotion, gesture?}]}
# Returns: {char1, char2, beatsApplied: [{beat, actions}], totalFrames}
# Choreograph animated conversation between two characters

# args: {description, characters: []}
# description: Natural language scene description
# characters: List of character labels already in scene
# Returns: {sceneType, actions: [], suggestions: []} (cameras are built in Python by dazpy)
# Generate a complete scene from natural language description
_CREATE_SCENE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var description = (args.description || "").toLowerCase();
    var characters = args.characters || [];

    var actions = [];
    var suggestions = [];
    var sceneType = "generic";

    // Helper: Create spot light
    function createSpotLight(label, x, y, z, flux, aimX, aimY, aimZ) {
        var light = new DzSpotLight();
        light.setLabel(label);
        Scene.addNode(light);
        var xp = light.findProperty("XTranslate");
        var yp = light.findProperty("YTranslate");
        var zp = light.findProperty("ZTranslate");
        if (xp) xp.setValue(x);
        if (yp) yp.setValue(y);
        if (zp) zp.setValue(z);
        light.aimAt(new DzVec3(aimX, aimY, aimZ));
        var fluxProp = light.findProperty("Flux");
        if (fluxProp) fluxProp.setValue(flux);
        return light;
    }

    // Helper: Set environment mode to Scene Only
    function setSceneOnlyLighting() {
        var renderMgr = App.getRenderMgr();
        var opts = renderMgr.getRenderOptions();
        opts.drawGroundPlane = false;
        // DzRenderOptions does not support findProperty — skip environment mode
    }

    // Get primary subject if characters provided
    var subject = null;
    var subjectCenter = {x: 0, y: 100, z: 0};
    var subjectHeight = 170;
    var eyeHeight = 160;

    if (characters.length > 0) {
        subject = Scene.findNodeByLabel(characters[0]);
        if (!subject) subject = Scene.findNode(characters[0]);
        if (subject) {
            var bbox = subject.getWSBoundingBox();
            subjectCenter = {x: (bbox.minX + bbox.maxX) / 2, y: (bbox.minY + bbox.maxY) / 2, z: (bbox.minZ + bbox.maxZ) / 2};
            subjectHeight = bbox.maxY - bbox.minY;
            eyeHeight = bbox.minY + subjectHeight * 0.85;
        }
    }

    // Scene type detection and setup
    if (description.indexOf("dinner") !== -1 || description.indexOf("dining") !== -1 || description.indexOf("meal") !== -1 || description.indexOf("eat") !== -1) {
        sceneType = "dining";
        actions.push("Scene type: Dining/meal scene");

        // Position characters facing each other (if 2+ characters)
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1pos = char1.findProperty("ZTranslate");
                var c2pos = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1pos) c1pos.setValue(-60);
                if (c2pos) c2pos.setValue(60);
                if (c1rot) c1rot.setValue(0);
                if (c2rot) c2rot.setValue(180);
                actions.push("Positioned characters facing each other across table distance");
            }
        }

        // Warm romantic lighting
        if (description.indexOf("romantic") !== -1) {
            createSpotLight("Warm Key Light", 100, 180, 100, 1500, subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Warm Fill Light", -80, 150, 80, 600, subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied warm romantic lighting");
        } else {
            createSpotLight("Key Light", 120, 180, 120, 1800, subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", -100, 150, 100, 700, subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied dining scene lighting");
        }

        setSceneOnlyLighting();

        suggestions.push("Add table prop for dining scene");
        suggestions.push("Add plates, glasses, or food props for realism");
        suggestions.push("Consider adding candles for romantic dinner mood");

    } else if (description.indexOf("interview") !== -1 || description.indexOf("meeting") !== -1 || description.indexOf("business") !== -1) {
        sceneType = "interview";
        actions.push("Scene type: Interview/business meeting");

        // Position characters facing each other
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1x = char1.findProperty("XTranslate");
                var c1z = char1.findProperty("ZTranslate");
                var c2x = char2.findProperty("XTranslate");
                var c2z = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1x) c1x.setValue(-80);
                if (c1z) c1z.setValue(0);
                if (c2x) c2x.setValue(80);
                if (c2z) c2z.setValue(0);
                if (c1rot) c1rot.setValue(90);
                if (c2rot) c2rot.setValue(-90);
                actions.push("Positioned characters facing each other for interview");
            }
        }

        // Professional neutral lighting
        createSpotLight("Key Light", 150, 200, 120, 2200, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Fill Light", -120, 180, 100, 1000, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Back Light", 0, 220, -180, 1400, subjectCenter.x, eyeHeight, subjectCenter.z);
        actions.push("Applied professional three-point lighting");
        setSceneOnlyLighting();

        suggestions.push("Add desk or table prop between characters");
        suggestions.push("Add chairs for seated interview");
        suggestions.push("Consider office props (laptop, papers) for context");

    } else if (description.indexOf("portrait") !== -1 || description.indexOf("headshot") !== -1 || description.indexOf("photo") !== -1) {
        sceneType = "portrait";
        actions.push("Scene type: Portrait/headshot");

        // Three-point lighting
        if (subject) {
            createSpotLight("Key Light", subjectCenter.x + 150, eyeHeight + 30, subjectCenter.z + 120, 2000,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", subjectCenter.x - 120, eyeHeight + 15, subjectCenter.z + 100, 800,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Rim Light", subjectCenter.x, eyeHeight + 50, subjectCenter.z - 150, 1200,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied classic three-point portrait lighting");
            setSceneOnlyLighting();
        }

        suggestions.push("Adjust character facial expression for portrait mood");
        suggestions.push("Consider neutral background or backdrop prop");
        suggestions.push("Try different camera angles (high-angle, low-angle)");

    } else if (description.indexOf("conversation") !== -1 || description.indexOf("talking") !== -1 || description.indexOf("chat") !== -1) {
        sceneType = "conversation";
        actions.push("Scene type: Conversation");

        // Position characters facing each other
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1x = char1.findProperty("XTranslate");
                var c1z = char1.findProperty("ZTranslate");
                var c2x = char2.findProperty("XTranslate");
                var c2z = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1x) c1x.setValue(-50);
                if (c1z) c1z.setValue(0);
                if (c2x) c2x.setValue(50);
                if (c2z) c2z.setValue(0);
                if (c1rot) c1rot.setValue(90);
                if (c2rot) c2rot.setValue(-90);
                actions.push("Positioned characters facing each other at conversation distance");
            }
        }

        // Natural conversational lighting
        createSpotLight("Key Light", 120, 180, 100, 1900, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Fill Light", -100, 160, 80, 850, subjectCenter.x, eyeHeight, subjectCenter.z);
        actions.push("Applied natural conversation lighting");
        setSceneOnlyLighting();

        suggestions.push("Use shot-reverse-shot camera technique for conversation");
        suggestions.push("Apply emotions and look-at for animated dialogue");
        suggestions.push("Consider adding environment props for context");

    } else {
        // Generic scene setup
        sceneType = "generic";
        actions.push("Scene type: Generic scene (no specific template matched)");

        // Basic three-point lighting
        if (subject) {
            createSpotLight("Key Light", subjectCenter.x + 150, eyeHeight + 30, subjectCenter.z + 120, 2000,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", subjectCenter.x - 120, eyeHeight + 15, subjectCenter.z + 100, 800,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Rim Light", subjectCenter.x, eyeHeight + 50, subjectCenter.z - 150, 1200,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied default three-point lighting");
            setSceneOnlyLighting();
        }

        suggestions.push("Provide more specific scene description for tailored setup");
        suggestions.push("Keywords: dinner, interview, portrait, conversation");
        suggestions.push("Add props and environment elements as needed");
    }

    // General suggestions
    if (characters.length === 0) {
        suggestions.push("Load characters into scene before generating setup");
    }

    return {
        sceneType: sceneType,
        description: args.description,
        charactersUsed: characters.length,
        actions: actions,
        suggestions: suggestions
    };
})()
"""

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
_SAVE_PROP_ASSET_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    if (typeof DzNodeSupportAssetFilter !== "function") {
        throw new Error("DzNodeSupportAssetFilter is not available in this DAZ Studio version.");
    }
    if (!args.outputPath) throw new Error("outputPath is required");
    var node = resolveNode(args.nodeLabel);

    // Normalize slashes for prefix comparison against configured content directories.
    function norm(p) { return String(p).replace(/\\\\/g, "/").toLowerCase(); }
    var outNorm = norm(args.outputPath);

    var contentMgr = App.getContentMgr();
    var baseDataPath = null;
    var n = contentMgr.getNumContentDirectories();
    var dirs = [];
    for (var i = 0; i < n; i++) {
        var dir = contentMgr.getContentDirectoryPath(i);
        dirs.push(dir);
        var dirNorm = norm(dir);
        if (outNorm.indexOf(dirNorm) === 0) { baseDataPath = dir; }
    }
    if (!baseDataPath) {
        throw new Error(
            "outputPath must be inside a configured DAZ content directory. outputPath=" +
            args.outputPath + " ; configured directories: " + dirs.join(", ")
        );
    }

    var filter = new DzNodeSupportAssetFilter();
    filter.setNode(node);

    var settings = new DzFileIOSettings();
    filter.getDefaultOptions(settings);
    settings.setStringValue("RunSilent", "yes");
    settings.setStringValue("BaseDataPath", baseDataPath);
    settings.setStringValue("VendorName", args.vendorName || "Author");
    settings.setStringValue("ProductName", args.productName || "Product");
    settings.setStringValue("ItemName", args.itemName || node.getLabel());
    if (args.category) settings.setStringValue("Category", args.category);
    if (args.compatibilityBase) settings.setStringValue("CompatibilityBase", args.compatibilityBase);
    if (args.compatibleWith) settings.setStringValue("CompatibleWith", args.compatibleWith);
    if (args.smartParent !== undefined) settings.setStringValue("SmartParentProp", args.smartParent ? "yes" : "no");
    if (args.writeGeometry !== undefined) settings.setStringValue("WriteGeometryDef", args.writeGeometry ? "yes" : "no");
    if (args.writeParameters !== undefined) settings.setStringValue("WriteParameterDefs", args.writeParameters ? "yes" : "no");
    if (args.writeUvs !== undefined) settings.setStringValue("WriteUVDefs", args.writeUvs ? "yes" : "no");
    if (args.forceUniqueIds !== undefined) settings.setStringValue("ForceUniqueIDs", args.forceUniqueIds ? "yes" : "no");
    if (args.compressOutput !== undefined) settings.setStringValue("CompressOutput", args.compressOutput ? "yes" : "no");

    var err = filter.doSave(settings, args.outputPath, "");
    var errCode = (err && typeof err.valueOf === "function") ? err.valueOf() : err;
    if (errCode) {
        throw new Error("DzNodeSupportAssetFilter.doSave failed (error code " + errCode + ") for node " + node.getLabel());
    }

    return {
        success: true,
        node: node.getLabel(),
        outputPath: args.outputPath,
        baseDataPath: baseDataPath,
        vendorName: args.vendorName || "Author",
        productName: args.productName || "Product",
        itemName: args.itemName || node.getLabel()
    };
})()
"""

# Phase 6.12: Morph Loader Pro
_LOAD_MORPH_PRO_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    if (typeof DzMorphLoader !== "function") {
        throw new Error("DzMorphLoader is not available (enable the Morph Loader Pro plugin)");
    }
    if (!args.objPath) throw new Error("objPath is required");
    var node = resolveNode(args.nodeLabel);

    var LOAD_MODES = {
        EntireFigure: 0, SelectedNodes: 1, PrimaryNode: 2,
        SingleSkinFigure: 3, SingleSkinFigureFromGraft: 4
    };
    var MIRROR_TYPES = {
        DoNotMirror: 0, XSwap: 1, XPosToNeg: 2, XNegToPos: 3,
        YSwap: 4, YPosToNeg: 5, YNegToPos: 6, ZSwap: 7, ZPosToNeg: 8, ZNegToPos: 9
    };
    var OVERWRITE_MODES = { MakeUnique: 0, DeltasAndERCLinks: 1, DeltasOnly: 2 };
    var SUBD_MAPPINGS = { Catmark: 0, FacetOrder: 1, ZBrushCage: 2, MudboxCage: 3 };
    var ERC_TYPES = {
        ERCDeltaAdd: 0, ERCDivideInto: 1, ERCDivideBy: 2,
        ERCMultiply: 3, ERCSubtract: 4, ERCAdd: 5, ERCKeyed: 6
    };

    function lookupEnum(table, name, label) {
        if (table[name] === undefined) {
            var valid = [];
            for (var k in table) valid.push(k);
            throw new Error("Unknown " + label + ": " + name + ". Valid: " + valid.join(", "));
        }
        return table[name];
    }

    function matchName(item, name) {
        return item.getLabel() === name || item.getName() === name;
    }

    function findProp(searchNode, name) {
        var i, pr, obj, m, ch, j;
        for (i = 0; i < searchNode.getNumProperties(); i++) {
            pr = searchNode.getProperty(i);
            if (matchName(pr, name)) return pr;
        }
        obj = (typeof searchNode.getObject === "function") ? searchNode.getObject() : null;
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

    var loader = new DzMorphLoader();
    loader.setFilename(args.objPath);
    if (args.morphName) loader.setMorphName(String(args.morphName));

    var loadModeVal = lookupEnum(LOAD_MODES, args.loadMode || "EntireFigure", "loadMode");
    var okMode = loader.setLoadMode(loadModeVal, node);
    if (!okMode) {
        throw new Error("setLoadMode failed for mode " + args.loadMode + " on node " + node.getLabel());
    }

    loader.setOverwriteExisting(lookupEnum(OVERWRITE_MODES, args.overwriteMode || "MakeUnique", "overwriteMode"));
    loader.setMorphMirroring(lookupEnum(MIRROR_TYPES, args.mirroring || "DoNotMirror", "mirroring"));

    if (args.preserveExistingDeltas !== undefined) loader.setPreserveExistingDeltas(!!args.preserveExistingDeltas);
    if (args.cleanUpOrphans !== undefined) loader.setCleanUpOrphans(!!args.cleanUpOrphans);
    if (args.deltaTolerance !== undefined && args.deltaTolerance !== null) {
        loader.setDeltaTolerance(parseFloat(args.deltaTolerance));
    }

    if (args.subdivision !== undefined) loader.setMorphSubdivision(!!args.subdivision);
    if (args.subdivisionMapping) {
        loader.setSubdivisionMapping(lookupEnum(SUBD_MAPPINGS, args.subdivisionMapping, "subdivisionMapping"));
    }
    if (args.subdivisionMinResolution !== undefined && args.subdivisionMinResolution !== null) {
        loader.setSubdivisionMinResolution(parseInt(args.subdivisionMinResolution, 10));
    }
    if (args.subdivisionMaxResolution !== undefined && args.subdivisionMaxResolution !== null) {
        loader.setSubdivisionMaxResolution(parseInt(args.subdivisionMaxResolution, 10));
    }
    if (args.subdivisionBuiltResolution !== undefined && args.subdivisionBuiltResolution !== null) {
        loader.setSubdivisionBuiltResolution(parseInt(args.subdivisionBuiltResolution, 10));
    }
    if (args.subdivisionSmoothCage !== undefined) loader.setSubdivisionSmoothCage(!!args.subdivisionSmoothCage);

    if (args.attenuateStrength !== undefined && args.attenuateStrength !== null) {
        loader.setAttenuateStrength(parseFloat(args.attenuateStrength));
    }
    if (args.attenuateEdgeStrength !== undefined && args.attenuateEdgeStrength !== null) {
        loader.setAttenuateEdgeStrength(parseFloat(args.attenuateEdgeStrength));
    }
    if (args.attenuateMapPath) loader.setAttenuateMapPath(String(args.attenuateMapPath));

    if (args.propertyGroupPath) loader.setPropertyGroupPath(String(args.propertyGroupPath));
    if (args.hideSecondaryProperties !== undefined) loader.setHideSecondaryProperties(!!args.hideSecondaryProperties);

    // Attention (SDK docs): applyReverseDeformationsPose() must run before createMorph().
    if (args.reverseDeformations) {
        loader.setReverseDeformations(true);
        if (args.reverseDeformationsPosePath) {
            loader.setReverseDeformationsPose(String(args.reverseDeformationsPosePath));
        }
        var okPose = loader.applyReverseDeformationsPose();
        if (!okPose) {
            throw new Error("applyReverseDeformationsPose() failed — check reverseDeformationsPosePath");
        }
    }

    var controlPropLabel = null;
    if (args.createControlProperty) {
        if (!args.controlPropertyName) {
            throw new Error("controlPropertyName is required when createControlProperty is true");
        }
        var controlNode = args.controlNodeLabel ? resolveNode(args.controlNodeLabel) : node;
        var controlProp = findProp(controlNode, args.controlPropertyName);
        if (!controlProp) {
            throw new Error("Control property not found: " + args.controlPropertyName + " on " + controlNode.getLabel());
        }
        if (!controlProp.inherits("DzNumericProperty")) {
            throw new Error("Control property is not numeric: " + args.controlPropertyName);
        }
        loader.setCreateControlProperty(true);
        loader.setControlNode(controlNode);
        loader.setControlProperty(controlProp);
        controlPropLabel = controlProp.getLabel();
        if (args.controlPropertyCustomLabel) {
            loader.setControlPropertyUseCustomLabel(true);
            loader.setControlPropertyCustomLabel(String(args.controlPropertyCustomLabel));
        }
        if (args.controlPropertyErcType) {
            loader.setControlPropertyERCType(
                lookupEnum(ERC_TYPES, args.controlPropertyErcType, "controlPropertyErcType")
            );
        }
        if (args.controlPropertyErcCustomValue !== undefined && args.controlPropertyErcCustomValue !== null) {
            loader.setControlPropertyERCUseCustomValue(true);
            loader.setControlPropertyERCCustomValue(parseFloat(args.controlPropertyErcCustomValue));
        }
    }

    var settings = new DzFileIOSettings();
    settings.setFloatValue("Scale", args.scale !== undefined ? parseFloat(args.scale) : 1.0);
    settings.setIntValue("RunSilent", 1);

    var onlyErrorsOrWarnings = args.onlyErrorsOrWarnings !== undefined ? !!args.onlyErrorsOrWarnings : true;
    var log = loader.createMorph(settings, node, onlyErrorsOrWarnings, true);

    var resolvedMorphName = loader.getMorphName();

    return {
        success: true,
        node: node.getLabel(),
        file: args.objPath,
        morphName: resolvedMorphName,
        loadMode: args.loadMode || "EntireFigure",
        overwriteMode: args.overwriteMode || "MakeUnique",
        mirroring: args.mirroring || "DoNotMirror",
        controlProperty: controlPropLabel,
        log: log || ""
    };
})()
"""

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

_LIST_STRAND_HAIR_NODES_SCRIPT = """\
(function(){
    var result = [];
    for (var i = 0; i < Scene.getNumNodes(); i++) {
        var n = Scene.getNode(i);
        if (!n.inherits("DzStrandHairNode")) continue;

        var target = n.getTargetNode();
        var obj = n.getObject();
        var hasGeometry = !!obj;
        var materials = [];
        if (obj) {
            var shape = obj.getCurrentShape();
            if (shape) {
                for (var m = 0; m < shape.getNumMaterials(); m++) {
                    var mat = shape.getMaterial(m);
                    var lbl = (typeof mat.getLabel === "function") ? mat.getLabel() : mat.getName();
                    materials.push(lbl || mat.getName());
                }
            }
        }

        result.push({
            label: n.getLabel(),
            name: n.getName(),
            target: target ? target.getLabel() : null,
            has_geometry: hasGeometry,
            materials: materials
        });
    }
    return { count: result.length, nodes: result };
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
    # Phase 2: Content library
    "vangard-list-categories": (
        "List content library subdirectories under a parent path across all content directories",
        _LIST_CATEGORIES_SCRIPT,
    ),
    "vangard-browse-category": (
        "List .duf files in a content library category path across all content directories",
        _BROWSE_CATEGORY_SCRIPT,
    ),
    # Phase 2: Scene layout & proximity
    "vangard-create-scene": (
        "Generate a complete scene from natural language description with lighting, "
        "cameras, and positioning",
        _CREATE_SCENE_SCRIPT,
    ),
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
    "vangard-save-prop-asset": (
        "Save a node as a DSON Figure/Prop Support Asset (.duf + .dsf geometry) into "
        "a configured content directory via DzNodeSupportAssetFilter — headless "
        "equivalent of File > Save As > Support Asset > Prop Asset",
        _SAVE_PROP_ASSET_SCRIPT,
    ),
    # Phase 6.12: Morph Loader Pro
    "vangard-load-morph-pro": (
        "Load an OBJ morph target onto a node via DzMorphLoader (Morph Loader Pro "
        "plugin) — full option set: load mode, mirroring, overwrite mode, reverse "
        "deformations, subdivision mapping, attenuation maps, ERC control property",
        _LOAD_MORPH_PRO_SCRIPT,
    ),
    # Phase 6.13: Strand-Based Hair
    "vangard-create-strand-hair": (
        "Create a native Strand-Based Hair node fit to a target figure via "
        "DzStrandHairCreateNodeAction. BLOCKS on a DAZ Studio confirmation "
        "dialog the user must click — always submit via the async endpoint",
        _CREATE_STRAND_HAIR_SCRIPT,
    ),
    "vangard-list-strand-hair-nodes": (
        "List every DzStrandHairNode in the scene with its target figure and "
        "whether it has generated geometry yet",
        _LIST_STRAND_HAIR_NODES_SCRIPT,
    ),
    "vangard-trigger-wearable-save": (
        "Select a figure and fire DzWearablesAssetFilterAction (File > Save As > "
        "Wearable(s) Preset) — blocks on native dialogs, submit via async endpoint only; "
        "daz_save_wearable_preset drives the resulting dialogs via UI Automation",
        _TRIGGER_WEARABLE_SAVE_SCRIPT,
    ),
}

