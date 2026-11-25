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
_INTERACTIVE_POSE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    function clamp(val, min, max) {
        return Math.max(min, Math.min(max, val));
    }

    var char1 = Scene.findNodeByLabel(args.char1Label);
    if (!char1) char1 = Scene.findNode(args.char1Label);
    if (!char1) throw new Error("Character 1 not found: " + args.char1Label);

    var char2 = Scene.findNodeByLabel(args.char2Label);
    if (!char2) char2 = Scene.findNode(args.char2Label);
    if (!char2) throw new Error("Character 2 not found: " + args.char2Label);

    var interactionType = args.interactionType || "face-each-other";
    var distance = args.distance;

    var pos1 = char1.getWSPos();
    var pos2 = char2.getWSPos();

    var applied = [];

    // Face each other (base for all interactions)
    if (interactionType === "face-each-other" || interactionType === "hug" ||
        interactionType === "handshake" || interactionType === "shoulder-arm") {

        // Position characters to face each other at specified distance
        if (distance) {
            var midX = (pos1.x + pos2.x) / 2;
            var midZ = (pos1.z + pos2.z) / 2;

            char1.findProperty("XTranslate").setValue(midX - distance/2);
            char1.findProperty("ZTranslate").setValue(midZ);

            char2.findProperty("XTranslate").setValue(midX + distance/2);
            char2.findProperty("ZTranslate").setValue(midZ);
        }

        // Rotate to face each other
        var hip1 = findBone(char1, "hip");
        var hip2 = findBone(char2, "hip");

        if (hip1) hip1.findProperty("YRotate").setValue(90);
        if (hip2) hip2.findProperty("YRotate").setValue(-90);

        applied.push("facing");
    }

    // Hug pose
    if (interactionType === "hug") {
        // Both arms around each other
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");
        var l1Shoulder = findBone(char1, "lShldrBend");
        var l1Forearm = findBone(char1, "lForearmBend");

        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(10);
            r1Shoulder.findProperty("ZRotate").setValue(70);
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-80);

        if (l1Shoulder) {
            l1Shoulder.findProperty("XRotate").setValue(10);
            l1Shoulder.findProperty("ZRotate").setValue(-70);
        }
        if (l1Forearm) l1Forearm.findProperty("YRotate").setValue(-80);

        // Char 2 mirror
        var r2Shoulder = findBone(char2, "rShldrBend");
        var r2Forearm = findBone(char2, "rForearmBend");
        var l2Shoulder = findBone(char2, "lShldrBend");
        var l2Forearm = findBone(char2, "lForearmBend");

        if (r2Shoulder) {
            r2Shoulder.findProperty("XRotate").setValue(10);
            r2Shoulder.findProperty("ZRotate").setValue(70);
        }
        if (r2Forearm) r2Forearm.findProperty("YRotate").setValue(-80);

        if (l2Shoulder) {
            l2Shoulder.findProperty("XRotate").setValue(10);
            l2Shoulder.findProperty("ZRotate").setValue(-70);
        }
        if (l2Forearm) l2Forearm.findProperty("YRotate").setValue(-80);

        applied.push("hug arms");
    }

    // Shoulder-arm (char1 puts arm around char2's shoulders)
    if (interactionType === "shoulder-arm") {
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");

        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(0);
            r1Shoulder.findProperty("ZRotate").setValue(90); // Arm out to side
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-45); // Slight bend

        // Char 2 leans slightly toward char1
        var chest2 = findBone(char2, "chestUpper");
        if (chest2) chest2.findProperty("ZRotate").setValue(-10);

        applied.push("shoulder-arm");
    }

    // Handshake
    if (interactionType === "handshake") {
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");

        var r2Shoulder = findBone(char2, "rShldrBend");
        var r2Forearm = findBone(char2, "rForearmBend");

        // Char 1 reaches right hand forward
        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(30); // Forward
            r1Shoulder.findProperty("ZRotate").setValue(10); // Slightly out
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-90);

        // Char 2 reaches right hand forward (mirror)
        if (r2Shoulder) {
            r2Shoulder.findProperty("XRotate").setValue(30);
            r2Shoulder.findProperty("ZRotate").setValue(10);
        }
        if (r2Forearm) r2Forearm.findProperty("YRotate").setValue(-90);

        applied.push("handshake");
    }

    return {
        success: true,
        char1: char1.getLabel(),
        char2: char2.getLabel(),
        interactionType: interactionType,
        applied: applied
    };
})()
"""

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
_ANIMATE_CONVERSATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};

    // Helper: Find bone in figure hierarchy
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        prop.setValue(frame, value);
        return true;
    }

    // Helper: Apply emotion morphs
    function applyEmotion(figure, emotion, intensity, frame) {
        var emotionMorphs = {
            happy: [
                {names: ["PHMSmile", "Smile"], value: 0.8},
                {names: ["PHMBrowsUp", "Brows Up"], value: 0.3},
                {names: ["PHMEyesClosedL", "Eyes Closed"], value: 0.15}
            ],
            sad: [
                {names: ["PHMMouthFrownL", "Mouth Frown"], value: 0.7},
                {names: ["PHMBrowsDown", "Brows Down"], value: 0.6},
                {names: ["PHMEyesClosedL", "Eyes Closed"], value: 0.25}
            ],
            angry: [
                {names: ["PHMBrowsDown", "Brows Down"], value: 0.9},
                {names: ["PHMMouthFrownL", "Mouth Frown"], value: 0.5},
                {names: ["PHMNoseWrinkleL", "Nose Wrinkle"], value: 0.4}
            ],
            surprised: [
                {names: ["PHMEyesWide", "Eyes Wide"], value: 0.85},
                {names: ["PHMBrowsUp", "Brows Up"], value: 0.8},
                {names: ["PHMMouthOpen", "Mouth Open"], value: 0.5}
            ],
            neutral: []
        };

        var morphList = emotionMorphs[emotion] || [];
        var applied = 0;

        for (var i = 0; i < morphList.length; i++) {
            var entry = morphList[i];
            var targetValue = entry.value * intensity;
            for (var j = 0; j < entry.names.length; j++) {
                var prop = figure.findProperty(entry.names[j]);
                if (prop && prop.inherits("DzNumericProperty")) {
                    setKeyframe(figure, entry.names[j], frame, targetValue);
                    applied++;
                    break;
                }
            }
        }
        return applied;
    }

    // Helper: Rotate bone to look at target
    function rotateBoneToward(bone, targetX, targetY, targetZ, intensity, frame) {
        var boneWS = bone.getWSPos();
        var dx = targetX - boneWS.x;
        var dy = targetY - boneWS.y;
        var dz = targetZ - boneWS.z;
        var hDist = Math.sqrt(dx*dx + dz*dz);

        var yaw = Math.atan2(dx, dz) * 180 / Math.PI;
        var pitch = Math.atan2(dy, hDist) * 180 / Math.PI;

        setKeyframe(bone, "YRotate", frame, yaw * intensity);
        setKeyframe(bone, "XRotate", frame, pitch * intensity * -1);
    }

    // Get characters
    var char1 = Scene.findNodeByLabel(args.char1Label);
    if (!char1) char1 = Scene.findNode(args.char1Label);
    if (!char1) throw new Error("Character 1 not found: " + args.char1Label);

    var char2 = Scene.findNodeByLabel(args.char2Label);
    if (!char2) char2 = Scene.findNode(args.char2Label);
    if (!char2) throw new Error("Character 2 not found: " + args.char2Label);

    // Get head positions for look-at targets
    var char1Head = findBone(char1, "head");
    var char2Head = findBone(char2, "head");

    var char1Pos = char1.getWSPos();
    var char2Pos = char2.getWSPos();
    var char1TargetY = char1Pos.y + 163; // Approx head height
    var char2TargetY = char2Pos.y + 163;

    if (char1Head) {
        var char1HeadPos = char1Head.getWSPos();
        char1TargetY = char1HeadPos.y;
    }
    if (char2Head) {
        var char2HeadPos = char2Head.getWSPos();
        char2TargetY = char2HeadPos.y;
    }

    var char1TargetX = char1Pos.x;
    var char1TargetZ = char1Pos.z;
    var char2TargetX = char2Pos.x;
    var char2TargetZ = char2Pos.z;

    // Process dialogue beats
    var dialogueBeats = args.dialogueBeats || [];
    var beatsApplied = [];
    var maxFrame = 0;

    for (var i = 0; i < dialogueBeats.length; i++) {
        var beat = dialogueBeats[i];
        var speaker = beat.speaker;
        var startFrame = beat.startFrame || 0;
        var endFrame = beat.endFrame || startFrame + 30;
        var emotion = beat.emotion || "neutral";
        var intensity = beat.intensity || 0.7;

        if (endFrame > maxFrame) maxFrame = endFrame;

        var actions = [];

        // Determine who's speaking and who's listening
        var speakerFig = (speaker === args.char1Label) ? char1 : char2;
        var listenerFig = (speaker === args.char1Label) ? char2 : char1;
        var listenerTargetX = (speaker === args.char1Label) ? char2TargetX : char1TargetX;
        var listenerTargetY = (speaker === args.char1Label) ? char2TargetY : char1TargetY;
        var listenerTargetZ = (speaker === args.char1Label) ? char2TargetZ : char1TargetZ;
        var speakerTargetX = (speaker === args.char1Label) ? char1TargetX : char2TargetX;
        var speakerTargetY = (speaker === args.char1Label) ? char1TargetY : char2TargetY;
        var speakerTargetZ = (speaker === args.char1Label) ? char1TargetZ : char2TargetZ;

        // Apply emotion to speaker at start of beat
        var morphsApplied = applyEmotion(speakerFig, emotion, intensity, startFrame);
        if (morphsApplied > 0) {
            actions.push("Applied " + emotion + " emotion (" + morphsApplied + " morphs)");
        }

        // Make listener look at speaker
        var listenerHead = findBone(listenerFig, "head");
        var listenerNeck = findBone(listenerFig, "neckLower");

        if (listenerHead) {
            rotateBoneToward(listenerHead, speakerTargetX, speakerTargetY, speakerTargetZ, 0.6, startFrame);
            rotateBoneToward(listenerHead, speakerTargetX, speakerTargetY, speakerTargetZ, 0.6, endFrame);
            actions.push("Listener looks at speaker");
        }
        if (listenerNeck) {
            rotateBoneToward(listenerNeck, speakerTargetX, speakerTargetY, speakerTargetZ, 0.3, startFrame);
            rotateBoneToward(listenerNeck, speakerTargetX, speakerTargetY, speakerTargetZ, 0.3, endFrame);
        }

        beatsApplied.push({
            beat: i + 1,
            speaker: speaker,
            frameRange: {start: startFrame, end: endFrame},
            emotion: emotion,
            actions: actions
        });
    }

    return {
        char1: char1.getLabel(),
        char2: char2.getLabel(),
        beatsApplied: beatsApplied,
        totalFrames: maxFrame,
        beatCount: dialogueBeats.length
    };
})()
"""

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
_CREATE_CHARACTER_PATH_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var characterLabel = args.characterLabel;
    var waypoints = args.waypoints || [];
    var pathType = args.pathType || "straight";
    var walkingStyle = args.walkingStyle || "casual";

    // Find character
    var character = Scene.findNodeByLabel(characterLabel);
    if (!character) character = Scene.findNode(characterLabel);
    if (!character) throw new Error("Character not found: " + characterLabel);

    if (waypoints.length < 2) {
        throw new Error("At least 2 waypoints required");
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        prop.setValue(frame, value);
        return true;
    }

    // Sort waypoints by frame
    waypoints.sort(function(a, b) { return a.frame - b.frame; });

    var keyframesSet = 0;
    var totalDistance = 0;

    // Set position keyframes and calculate distance
    for (var i = 0; i < waypoints.length; i++) {
        var wp = waypoints[i];
        var pos = wp.position;
        var frame = wp.frame;

        if (!pos || pos.x === undefined || pos.y === undefined || pos.z === undefined) {
            throw new Error("Waypoint " + i + " missing position (x, y, z)");
        }
        if (frame === undefined) {
            throw new Error("Waypoint " + i + " missing frame");
        }

        setKeyframe(character, "XTranslate", frame, pos.x);
        setKeyframe(character, "YTranslate", frame, pos.y);
        setKeyframe(character, "ZTranslate", frame, pos.z);
        keyframesSet += 3;

        // Calculate distance to next waypoint
        if (i > 0) {
            var prevPos = waypoints[i - 1].position;
            var dx = pos.x - prevPos.x;
            var dy = pos.y - prevPos.y;
            var dz = pos.z - prevPos.z;
            totalDistance += Math.sqrt(dx*dx + dy*dy + dz*dz);
        }

        // Rotate character to face direction of travel
        if (i < waypoints.length - 1) {
            var nextPos = waypoints[i + 1].position;
            var angle = Math.atan2(nextPos.x - pos.x, nextPos.z - pos.z) * 180 / Math.PI;
            setKeyframe(character, "YRotate", frame, angle);
            keyframesSet++;
        }
    }

    var startFrame = waypoints[0].frame;
    var endFrame = waypoints[waypoints.length - 1].frame;

    return {
        character: character.getLabel(),
        waypointCount: waypoints.length,
        pathType: pathType,
        walkingStyle: walkingStyle,
        keyframesSet: keyframesSet,
        frameRange: {start: startFrame, end: endFrame},
        totalDistance: Math.round(totalDistance * 10) / 10,
        note: "Character will move along path. Walking cycle animation not automatically applied."
    };
})()
"""

# args: {characters: [], arrangement, spacing, facing, centerPosition?}
# arrangement: "line", "semicircle", "triangle", "conversation-circle"
# facing: "center", "camera", "forward"
# Returns: {characters: [{label, position, rotation}], arrangement, spacing}
# Position multiple characters in formation
_ARRANGE_CHARACTERS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var characterLabels = args.characters || [];
    var arrangement = args.arrangement || "line";
    var spacing = args.spacing || 80;
    var facing = args.facing || "forward";
    var centerPosition = args.centerPosition || {x: 0, y: 0, z: 0};

    if (characterLabels.length === 0) {
        return {characters: [], arrangement: arrangement, spacing: spacing, count: 0};
    }

    // Find all characters
    var characters = [];
    for (var i = 0; i < characterLabels.length; i++) {
        var char = Scene.findNodeByLabel(characterLabels[i]);
        if (!char) char = Scene.findNode(characterLabels[i]);
        if (!char) throw new Error("Character not found: " + characterLabels[i]);
        characters.push(char);
    }

    var count = characters.length;
    var positions = [];
    var cx = centerPosition.x;
    var cy = centerPosition.y;
    var cz = centerPosition.z;

    // Calculate positions based on arrangement type
    if (arrangement === "line") {
        // Straight line along X axis
        var startX = cx - (spacing * (count - 1)) / 2;
        for (var i = 0; i < count; i++) {
            positions.push({
                x: startX + i * spacing,
                y: cy,
                z: cz
            });
        }

    } else if (arrangement === "semicircle") {
        // Arc formation
        var radius = (spacing * count) / Math.PI;
        for (var i = 0; i < count; i++) {
            var angle = count > 1 ? (i / (count - 1)) * Math.PI : 0;
            positions.push({
                x: cx + radius * Math.sin(angle),
                y: cy,
                z: cz - radius * Math.cos(angle)
            });
        }

    } else if (arrangement === "triangle") {
        // Triangular formation
        if (count === 2) {
            positions.push({x: cx - spacing/2, y: cy, z: cz});
            positions.push({x: cx + spacing/2, y: cy, z: cz});
        } else if (count === 3) {
            positions.push({x: cx, y: cy, z: cz - spacing * 0.6});
            positions.push({x: cx - spacing/2, y: cy, z: cz + spacing * 0.3});
            positions.push({x: cx + spacing/2, y: cy, z: cz + spacing * 0.3});
        } else {
            // Arrange in rows
            var row1 = Math.floor(count / 2);
            var row2 = count - row1;
            for (var i = 0; i < row1; i++) {
                var xOffset = (i - (row1 - 1) / 2) * spacing;
                positions.push({x: cx + xOffset, y: cy, z: cz - spacing * 0.6});
            }
            for (var i = 0; i < row2; i++) {
                var xOffset = (i - (row2 - 1) / 2) * spacing;
                positions.push({x: cx + xOffset, y: cy, z: cz + spacing * 0.3});
            }
        }

    } else if (arrangement === "conversation-circle") {
        // Circle facing inward
        var radius = spacing;
        for (var i = 0; i < count; i++) {
            var angle = (i / count) * 2 * Math.PI;
            positions.push({
                x: cx + radius * Math.sin(angle),
                y: cy,
                z: cz + radius * Math.cos(angle)
            });
        }

    } else {
        throw new Error("Unknown arrangement: " + arrangement +
            ". Valid: line, semicircle, triangle, conversation-circle");
    }

    // Apply positions and rotations
    var results = [];
    for (var i = 0; i < count; i++) {
        var char = characters[i];
        var pos = positions[i];

        // Set position
        var xp = char.findProperty("XTranslate");
        var yp = char.findProperty("YTranslate");
        var zp = char.findProperty("ZTranslate");
        if (xp) xp.setValue(pos.x);
        if (yp) yp.setValue(pos.y);
        if (zp) zp.setValue(pos.z);

        // Calculate rotation based on facing
        var rotation = 0;
        if (facing === "center") {
            // Face toward center
            var angle = Math.atan2(pos.x - cx, pos.z - cz) * 180 / Math.PI;
            rotation = angle + 180;
        } else if (facing === "camera") {
            // Face camera (assuming camera at +Z)
            rotation = 0;
        } else if (facing === "forward") {
            // Face forward (+Z direction)
            rotation = 0;
        }

        var rp = char.findProperty("YRotate");
        if (rp) rp.setValue(rotation);

        results.push({
            label: char.getLabel(),
            position: {x: Math.round(pos.x * 10) / 10, y: Math.round(pos.y * 10) / 10, z: Math.round(pos.z * 10) / 10},
            rotation: Math.round(rotation * 10) / 10
        });
    }

    return {
        characters: results,
        arrangement: arrangement,
        spacing: spacing,
        facing: facing,
        count: count
    };
})()
"""

# args: {actionType, characters: [], startFrame, duration}
# actionType: "handshake", "hug", "fight", "dance"
# Returns: {actionType, characters: [], positions: [], suggestions: []}
# Choreograph simple action between characters
_CHOREOGRAPH_ACTION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var actionType = args.actionType;
    var characterLabels = args.characters || [];
    var startFrame = args.startFrame || 0;
    var duration = args.duration || 90;

    if (characterLabels.length < 1) {
        throw new Error("At least 1 character required");
    }

    // Find all characters
    var characters = [];
    for (var i = 0; i < characterLabels.length; i++) {
        var char = Scene.findNodeByLabel(characterLabels[i]);
        if (!char) char = Scene.findNode(characterLabels[i]);
        if (!char) throw new Error("Character not found: " + characterLabels[i]);
        characters.push(char);
    }

    var positions = [];
    var suggestions = [];

    if (actionType === "handshake") {
        if (characters.length < 2) {
            throw new Error("handshake requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters facing each other
        var spacing = 60; // Close enough for handshake
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90); // Face right
        if (r2) r2.setValue(-90); // Face left

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Use daz_reach_toward to position hands for handshake");
        suggestions.push("Apply 'friendly' or 'professional' emotion to both characters");

    } else if (actionType === "hug") {
        if (characters.length < 2) {
            throw new Error("hug requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters very close, facing each other
        var spacing = 30; // Very close for hug
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Use daz_interactive_pose with 'hug' type for arm positioning");
        suggestions.push("Apply 'loving' or 'happy' emotion to both characters");

    } else if (actionType === "fight") {
        if (characters.length < 2) {
            throw new Error("fight requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters at fighting distance
        var spacing = 100;
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Apply fighting stance poses from content library");
        suggestions.push("Apply 'angry' or 'aggressive' emotion");
        suggestions.push("Use low-angle camera for dramatic effect");

    } else if (actionType === "dance") {
        if (characters.length < 2) {
            throw new Error("dance requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters for partner dance
        var spacing = 40;
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Apply partner dance poses from content library");
        suggestions.push("Use daz_create_character_path for dance movement");
        suggestions.push("Apply 'happy' or 'excited' emotion");

    } else {
        throw new Error("Unknown action type: " + actionType +
            ". Valid: handshake, hug, fight, dance");
    }

    return {
        actionType: actionType,
        characters: characterLabels,
        positions: positions,
        frameRange: {start: startFrame, end: startFrame + duration},
        suggestions: suggestions
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 4.8: Lighting Animation scripts
# ---------------------------------------------------------------------------

_ANIMATE_LIGHT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var lightLabel = args.lightLabel;
    var movementType = args.movementType || "flicker";
    var startFrame = args.startFrame !== undefined ? args.startFrame : 0;
    var endFrame = args.endFrame !== undefined ? args.endFrame : 90;
    var intensity = args.intensity !== undefined ? args.intensity : 1500;
    var flickerAmount = args.flickerAmount !== undefined ? args.flickerAmount : 0.3;
    var colorKeyframes = args.colorKeyframes || null;

    // Find light node
    var light = Scene.findNodeByLabel(lightLabel);
    if (!light) light = Scene.findNode(lightLabel);
    if (!light) throw new Error("Light not found: " + lightLabel);

    var fluxProp = light.findProperty("Flux");
    if (!fluxProp) throw new Error("Light has no Flux property: " + lightLabel);

    var keyframesCreated = [];
    var duration = endFrame - startFrame;

    if (movementType === "flicker") {
        // Random flicker: vary flux at irregular intervals
        var flickerFrames = Math.max(4, Math.floor(duration / 5));
        var step = Math.floor(duration / flickerFrames);
        if (step < 1) step = 1;

        for (var f = startFrame; f <= endFrame; f += step) {
            // Random variation within flickerAmount percent of intensity
            var variation = (Math.random() * 2 - 1) * flickerAmount * intensity;
            var frameValue = Math.max(0, intensity + variation);

            fluxProp.setValue(f, frameValue);
            keyframesCreated.push({frame: f, value: frameValue});
        }
        // Ensure end frame
        if (keyframesCreated.length === 0 || keyframesCreated[keyframesCreated.length - 1].frame !== endFrame) {
            fluxProp.setValue(endFrame, intensity);
            keyframesCreated.push({frame: endFrame, value: intensity});
        }

    } else if (movementType === "pulse") {
        // Smooth pulse: sine wave intensity change
        var pulseCount = args.pulseCount !== undefined ? args.pulseCount : 3;
        var minIntensity = intensity * (1 - flickerAmount);
        var maxIntensity = intensity;
        var numKeyframes = pulseCount * 4 + 1; // 4 keyframes per pulse cycle
        var frameStep = duration / (numKeyframes - 1);

        for (var i = 0; i < numKeyframes; i++) {
            var frame = Math.round(startFrame + i * frameStep);
            var phase = (i / (numKeyframes - 1)) * pulseCount * 2 * Math.PI;
            var sine = (Math.sin(phase) + 1) / 2; // 0 to 1
            var frameValue = minIntensity + sine * (maxIntensity - minIntensity);

            fluxProp.setValue(frame, frameValue);
            keyframesCreated.push({frame: frame, value: frameValue});
        }

    } else if (movementType === "fade-in") {
        // Fade from 0 to target intensity
        fluxProp.setValue(startFrame, 0);
        keyframesCreated.push({frame: startFrame, value: 0});

        fluxProp.setValue(endFrame, intensity);
        keyframesCreated.push({frame: endFrame, value: intensity});

    } else if (movementType === "fade-out") {
        // Fade from current intensity to 0
        fluxProp.setValue(startFrame, intensity);
        keyframesCreated.push({frame: startFrame, value: intensity});

        fluxProp.setValue(endFrame, 0);
        keyframesCreated.push({frame: endFrame, value: 0});

    } else if (movementType === "strobe") {
        // Alternating on/off at regular intervals
        var strobeInterval = args.strobeInterval !== undefined ? args.strobeInterval : 5;
        var frame = startFrame;
        var on = true;

        while (frame <= endFrame) {
            var frameValue = on ? intensity : 0;
            fluxProp.setValue(frame, frameValue);
            keyframesCreated.push({frame: frame, value: frameValue});

            // Add keyframe one frame before change for hard cut
            var nextFrame = frame + strobeInterval;
            if (nextFrame <= endFrame) {
                fluxProp.setValue(nextFrame - 1, frameValue);
                keyframesCreated.push({frame: nextFrame - 1, value: frameValue});
            }

            frame = nextFrame;
            on = !on;
        }

    } else if (movementType === "color-cycle") {
        // Animate light color temperature (warm/cool shift)
        // Use default warm-to-cool-to-warm cycle if no keyframes provided
        if (!colorKeyframes) {
            colorKeyframes = [
                {frame: startFrame, r: 1.0, g: 0.8, b: 0.5},
                {frame: Math.round(startFrame + duration * 0.33), r: 1.0, g: 1.0, b: 1.0},
                {frame: Math.round(startFrame + duration * 0.66), r: 0.5, g: 0.7, b: 1.0},
                {frame: endFrame, r: 1.0, g: 0.8, b: 0.5}
            ];
        }

        // Find color channel properties
        var colorPropR = light.findProperty("Color/Red");
        var colorPropG = light.findProperty("Color/Green");
        var colorPropB = light.findProperty("Color/Blue");

        if (!colorPropR) {
            // Fall back to simpler flux animation with color note
            fluxProp.setValue(startFrame, intensity);
            fluxProp.setValue(endFrame, intensity);
            keyframesCreated.push({frame: startFrame, value: intensity});
        } else {
            for (var k = 0; k < colorKeyframes.length; k++) {
                var ckf = colorKeyframes[k];
                if (colorPropR) {
                    colorPropR.setValue(ckf.frame, ckf.r);
                }
                if (colorPropG) {
                    colorPropG.setValue(ckf.frame, ckf.g);
                }
                if (colorPropB) {
                    colorPropB.setValue(ckf.frame, ckf.b);
                }
                keyframesCreated.push({frame: ckf.frame, r: ckf.r, g: ckf.g, b: ckf.b});
            }
        }

    } else {
        throw new Error("Unknown movementType: " + movementType +
            ". Valid: flicker, pulse, fade-in, fade-out, strobe, color-cycle");
    }

    return {
        light: lightLabel,
        movementType: movementType,
        startFrame: startFrame,
        endFrame: endFrame,
        targetIntensity: intensity,
        keyframesCreated: keyframesCreated.length,
        keyframes: keyframesCreated,
        suggestions: [
            "Use daz_render_animation to render the lighting animation",
            "Combine with daz_animate_camera_movement for cinematic effect",
            "Layer multiple lights with offset timing for rich atmosphere"
        ]
    };
})()
"""

_CREATE_LIGHT_SEQUENCE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var sequenceType = args.sequenceType || "day-to-night";
    var subjectLabel = args.subjectLabel || null;
    var startFrame = args.startFrame !== undefined ? args.startFrame : 0;
    var endFrame = args.endFrame !== undefined ? args.endFrame : 120;
    var createLights = args.createLights !== false;

    var duration = endFrame - startFrame;
    var midFrame = Math.round(startFrame + duration / 2);
    var quarterFrame = Math.round(startFrame + duration / 4);
    var threeQuarterFrame = Math.round(startFrame + duration * 0.75);

    var lightsCreated = [];
    var keyframesSet = [];

    // Helper to find or create a light
    function getOrCreateLight(label, lightClass) {
        var existingLight = Scene.findNodeByLabel(label);
        if (existingLight) return {node: existingLight, created: false};

        if (!createLights) return {node: null, created: false};

        var newLight;
        if (lightClass === "spot") {
            newLight = new DzSpotLight();
        } else {
            newLight = new DzDistantLight();
        }
        Scene.addNode(newLight);
        newLight.setLabel(label);
        return {node: newLight, created: true};
    }

    // Helper to set a keyframe on a light property
    function setLightKey(light, propName, frame, value) {
        var prop = light.findProperty(propName);
        if (prop) {
            prop.setValue(value);
            prop.setValue(frame, value);
            keyframesSet.push({light: light.getLabel(), property: propName, frame: frame, value: value});
            return true;
        }
        return false;
    }

    if (sequenceType === "day-to-night") {
        // Bright daylight → warm sunset → dark night
        var sunResult = getOrCreateLight("Sun_Key", "distant");
        var fillResult = getOrCreateLight("Sky_Fill", "spot");

        if (sunResult.node) {
            if (sunResult.created) lightsCreated.push("Sun_Key");
            var sun = sunResult.node;

            // Day: bright white light from above
            setLightKey(sun, "Flux", startFrame, 8000);
            setLightKey(sun, "Flux", quarterFrame, 6000);
            // Sunset: warm dim
            setLightKey(sun, "Flux", midFrame, 3000);
            setLightKey(sun, "Flux", threeQuarterFrame, 800);
            // Night: off
            setLightKey(sun, "Flux", endFrame, 0);
        }

        if (fillResult.node) {
            if (fillResult.created) lightsCreated.push("Sky_Fill");
            var fill = fillResult.node;

            // Sky fill: ambient that dims with sun
            setLightKey(fill, "Flux", startFrame, 2000);
            setLightKey(fill, "Flux", midFrame, 800);
            setLightKey(fill, "Flux", endFrame, 100);
        }

    } else if (sequenceType === "night-to-dawn") {
        // Dark night → pre-dawn glow → sunrise
        var sunResult = getOrCreateLight("Dawn_Key", "distant");
        var ambResult = getOrCreateLight("Night_Ambient", "spot");

        if (sunResult.node) {
            if (sunResult.created) lightsCreated.push("Dawn_Key");
            var sun = sunResult.node;

            // Night: no sun
            setLightKey(sun, "Flux", startFrame, 0);
            setLightKey(sun, "Flux", threeQuarterFrame, 500);
            // Dawn: growing sunrise
            setLightKey(sun, "Flux", endFrame, 6000);
        }

        if (ambResult.node) {
            if (ambResult.created) lightsCreated.push("Night_Ambient");
            var amb = ambResult.node;

            // Night ambient: low blue fill
            setLightKey(amb, "Flux", startFrame, 200);
            setLightKey(amb, "Flux", midFrame, 300);
            setLightKey(amb, "Flux", endFrame, 1500);
        }

    } else if (sequenceType === "interrogation") {
        // Harsh single overhead light, tension build
        var overheadResult = getOrCreateLight("Overhead_Key", "spot");

        if (overheadResult.node) {
            if (overheadResult.created) lightsCreated.push("Overhead_Key");
            var overhead = overheadResult.node;

            // Build tension: starts dim, pulses brighter
            setLightKey(overhead, "Flux", startFrame, 2000);
            setLightKey(overhead, "Flux", quarterFrame, 3000);
            setLightKey(overhead, "Flux", midFrame, 2500);
            setLightKey(overhead, "Flux", threeQuarterFrame, 4000);
            setLightKey(overhead, "Flux", endFrame, 5000);
        }

        // Optional subject-aimed spot for reveal
        var revealResult = getOrCreateLight("Reveal_Spot", "spot");
        if (revealResult.node) {
            if (revealResult.created) lightsCreated.push("Reveal_Spot");
            var reveal = revealResult.node;

            // Off until climax
            setLightKey(reveal, "Flux", startFrame, 0);
            setLightKey(reveal, "Flux", threeQuarterFrame - 1, 0);
            setLightKey(reveal, "Flux", threeQuarterFrame, 3000);
            setLightKey(reveal, "Flux", endFrame, 3000);
        }

    } else if (sequenceType === "romantic") {
        // Warm candlelight flicker, soft fill
        var candleResult = getOrCreateLight("Candle_Key", "spot");
        var softResult = getOrCreateLight("Soft_Fill", "spot");

        if (candleResult.node) {
            if (candleResult.created) lightsCreated.push("Candle_Key");
            var candle = candleResult.node;

            // Gentle flicker
            var flickerStep = Math.max(3, Math.floor(duration / 15));
            for (var f = startFrame; f <= endFrame; f += flickerStep) {
                var variation = (Math.random() * 0.4 - 0.2) * 800;
                var fluxVal = Math.max(200, 800 + variation);
                setLightKey(candle, "Flux", f, fluxVal);
            }
        }

        if (softResult.node) {
            if (softResult.created) lightsCreated.push("Soft_Fill");
            var soft = softResult.node;

            // Constant soft fill
            setLightKey(soft, "Flux", startFrame, 400);
            setLightKey(soft, "Flux", endFrame, 400);
        }

    } else if (sequenceType === "action-tension") {
        // Multiple lights building to climax, then flash
        var keyResult = getOrCreateLight("Action_Key", "spot");
        var rimResult = getOrCreateLight("Action_Rim", "spot");
        var flashResult = getOrCreateLight("Flash_Light", "spot");

        if (keyResult.node) {
            if (keyResult.created) lightsCreated.push("Action_Key");
            var key = keyResult.node;

            setLightKey(key, "Flux", startFrame, 3000);
            setLightKey(key, "Flux", threeQuarterFrame, 5000);
            setLightKey(key, "Flux", endFrame, 5000);
        }

        if (rimResult.node) {
            if (rimResult.created) lightsCreated.push("Action_Rim");
            var rim = rimResult.node;

            setLightKey(rim, "Flux", startFrame, 1000);
            setLightKey(rim, "Flux", endFrame, 2000);
        }

        if (flashResult.node) {
            if (flashResult.created) lightsCreated.push("Flash_Light");
            var flash = flashResult.node;

            // Flash at climax
            setLightKey(flash, "Flux", startFrame, 0);
            setLightKey(flash, "Flux", threeQuarterFrame - 1, 0);
            setLightKey(flash, "Flux", threeQuarterFrame, 15000);
            setLightKey(flash, "Flux", threeQuarterFrame + 3, 15000);
            setLightKey(flash, "Flux", threeQuarterFrame + 4, 0);
            setLightKey(flash, "Flux", endFrame, 0);
        }

    } else {
        throw new Error("Unknown sequenceType: " + sequenceType +
            ". Valid: day-to-night, night-to-dawn, interrogation, romantic, action-tension");
    }

    return {
        sequenceType: sequenceType,
        startFrame: startFrame,
        endFrame: endFrame,
        lightsCreated: lightsCreated,
        totalKeyframes: keyframesSet.length,
        keyframes: keyframesSet,
        suggestions: [
            "Position lights in scene before rendering",
            "Use daz_render_animation to render the full sequence",
            "Adjust Flux values with daz_set_keyframe to fine-tune timing"
        ]
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 4.10: Focus & DOF scripts
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Phase 4.11: Visual Composition scripts
# ---------------------------------------------------------------------------

_SET_SCENE_ATMOSPHERE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var environmentMode = args.environmentMode !== undefined ? args.environmentMode : null;
    var environmentIntensity = args.environmentIntensity !== undefined ? args.environmentIntensity : null;
    var drawDome = args.drawDome !== undefined ? args.drawDome : null;
    var domeScale = args.domeScale !== undefined ? args.domeScale : null;
    var domeRotation = args.domeRotation !== undefined ? args.domeRotation : null;
    var sunLightIntensity = args.sunLightIntensity !== undefined ? args.sunLightIntensity : null;
    var ambientColor = args.ambientColor || null;

    // Environment node is always Scene.getNode(1)
    var envNode = Scene.getNode(1);
    if (!envNode) throw new Error("Environment node not found at Scene.getNode(1)");

    var results = {};
    var changes = [];

    // Environment mode:
    //   0 = Sun-Sky Only, 1 = Dome Only, 2 = Sun-Sky + Dome, 3 = Scene Only (no dome)
    if (environmentMode !== null) {
        var modeProp = envNode.findProperty("Environment Mode");
        if (modeProp) {
            modeProp.setValue(environmentMode);
            results.environmentMode = environmentMode;
            var modeNames = {0: "Sun-Sky Only", 1: "Dome Only", 2: "Sun-Sky + Dome", 3: "Scene Only"};
            changes.push("Environment Mode → " + (modeNames[environmentMode] || environmentMode));
        } else {
            results.environmentModeNote = "Environment Mode property not found";
        }
    }

    // Environment intensity (controls dome/HDRI brightness)
    if (environmentIntensity !== null) {
        var intensProp = envNode.findProperty("Environment Intensity");
        if (!intensProp) intensProp = envNode.findProperty("Dome Intensity");
        if (intensProp) {
            intensProp.setValue(environmentIntensity);
            results.environmentIntensity = environmentIntensity;
            changes.push("Environment Intensity → " + environmentIntensity);
        } else {
            results.environmentIntensityNote = "Environment Intensity property not found";
        }
    }

    // Draw dome (show HDRI background in render)
    if (drawDome !== null) {
        var domeProp = envNode.findProperty("Draw Dome");
        if (!domeProp) domeProp = envNode.findProperty("Dome Visible");
        if (domeProp) {
            domeProp.setValue(drawDome ? 1 : 0);
            results.drawDome = drawDome;
            changes.push("Draw Dome → " + (drawDome ? "On" : "Off"));
        } else {
            results.drawDomeNote = "Draw Dome property not found";
        }
    }

    // Dome scale
    if (domeScale !== null) {
        var scaleProp = envNode.findProperty("Dome Scale");
        if (scaleProp) {
            scaleProp.setValue(domeScale);
            results.domeScale = domeScale;
            changes.push("Dome Scale → " + domeScale);
        }
    }

    // Dome rotation (horizontal rotation of the HDRI dome)
    if (domeRotation !== null) {
        var rotProp = envNode.findProperty("Dome Rotation");
        if (!rotProp) rotProp = envNode.findProperty("Dome Orientation");
        if (rotProp) {
            rotProp.setValue(domeRotation);
            results.domeRotation = domeRotation;
            changes.push("Dome Rotation → " + domeRotation + "°");
        }
    }

    // Sun light intensity (for Sun-Sky mode)
    if (sunLightIntensity !== null) {
        var sunProp = envNode.findProperty("Sun Intensity");
        if (!sunProp) sunProp = envNode.findProperty("Sunlight Intensity");
        if (sunProp) {
            sunProp.setValue(sunLightIntensity);
            results.sunLightIntensity = sunLightIntensity;
            changes.push("Sun Intensity → " + sunLightIntensity);
        } else {
            results.sunLightNote = "Sun Intensity property not found";
        }
    }

    // Read back current environment state for context
    var currentMode = null;
    var mp = envNode.findProperty("Environment Mode");
    if (mp) currentMode = mp.getValue();

    return {
        environmentNodeLabel: envNode.getLabel(),
        changesApplied: changes,
        changeCount: changes.length,
        currentEnvironmentMode: currentMode,
        results: results,
        environmentModeReference: {
            0: "Sun-Sky Only (outdoor HDRI sky)",
            1: "Dome Only (HDRI dome image)",
            2: "Sun-Sky + Dome (combined)",
            3: "Scene Only (use only scene lights, no dome)"
        },
        suggestions: [
            "Mode 3 (Scene Only) works best with daz_apply_lighting_preset presets",
            "Mode 1 (Dome Only) requires loading an HDRI map first",
            "Rotate dome to match light direction with key lights",
            "Lower environmentIntensity (0.1-0.5) to blend HDRI with scene lights"
        ]
    };
})()
"""

_APPLY_VISUAL_STYLE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var styleName = args.styleName || "cinematic";
    var subjectLabel = args.subjectLabel || null;
    var intensity = args.intensity !== undefined ? args.intensity : 1.0;

    // Style definitions: each style sets environment + light ratios
    var styles = {
        "cinematic": {
            envMode: 3,             // Scene Only
            keyFlux: 5000,
            fillRatio: 0.15,
            rimRatio: 0.7,
            keyAngle: 40,
            rimAngle: -150,
            shadowSoftness: 0.3,
            description: "High contrast, strong rim, compressed fill — film look"
        },
        "noir": {
            envMode: 3,
            keyFlux: 4000,
            fillRatio: 0.05,
            rimRatio: 0.2,
            keyAngle: 70,
            rimAngle: -160,
            shadowSoftness: 0.1,
            description: "Extreme contrast, deep shadows, minimal fill — classic noir"
        },
        "golden-hour": {
            envMode: 3,
            keyFlux: 6000,
            fillRatio: 0.3,
            rimRatio: 0.9,
            keyAngle: 25,
            rimAngle: -170,
            shadowSoftness: 0.5,
            description: "Warm raking light, strong backlit rim, soft fill — magic hour"
        },
        "blue-hour": {
            envMode: 3,
            keyFlux: 1500,
            fillRatio: 0.6,
            rimRatio: 0.4,
            keyAngle: 20,
            rimAngle: -140,
            shadowSoftness: 0.8,
            description: "Low intensity, even blue-toned fill, subtle — dusk/dawn"
        },
        "high-key": {
            envMode: 3,
            keyFlux: 8000,
            fillRatio: 0.8,
            rimRatio: 0.3,
            keyAngle: 10,
            rimAngle: -160,
            shadowSoftness: 0.9,
            description: "Bright, low contrast, minimal shadows — commercial/fashion"
        },
        "low-key": {
            envMode: 3,
            keyFlux: 2500,
            fillRatio: 0.08,
            rimRatio: 0.3,
            keyAngle: 60,
            rimAngle: -150,
            shadowSoftness: 0.2,
            description: "Dark, moody, shadows dominate — thriller/horror"
        },
        "documentary": {
            envMode: 3,
            keyFlux: 4500,
            fillRatio: 0.5,
            rimRatio: 0.2,
            keyAngle: 30,
            rimAngle: -160,
            shadowSoftness: 0.6,
            description: "Natural-feeling, moderate contrast — realistic interview look"
        },
        "fantasy": {
            envMode: 3,
            keyFlux: 3500,
            fillRatio: 0.4,
            rimRatio: 1.2,
            keyAngle: 35,
            rimAngle: -145,
            shadowSoftness: 0.7,
            description: "Ethereal, glowing rim, soft key — fantasy/magical"
        }
    };

    var style = styles[styleName];
    if (!style) {
        throw new Error("Unknown styleName: " + styleName +
            ". Valid: " + Object.keys(styles).join(", "));
    }

    // Scale fluxes by intensity
    var keyFlux  = Math.round(style.keyFlux * intensity);
    var fillFlux = Math.round(keyFlux * style.fillRatio);
    var rimFlux  = Math.round(keyFlux * style.rimRatio);

    // Find subject for light positioning
    var subjectPos = {x: 0, y: 130, z: 0};
    if (subjectLabel) {
        var sub = Scene.findNodeByLabel(subjectLabel) || Scene.findNode(subjectLabel);
        if (sub) {
            var sx = sub.findProperty("XTranslate");
            var sy = sub.findProperty("YTranslate");
            var sz = sub.findProperty("ZTranslate");
            subjectPos = {
                x: sx ? sx.getValue() : 0,
                y: (sy ? sy.getValue() : 0) + 130,
                z: sz ? sz.getValue() : 0
            };
        }
    }

    // Set environment mode to Scene Only
    var envNode = Scene.getNode(1);
    if (envNode) {
        var modeProp = envNode.findProperty("Environment Mode");
        if (modeProp) modeProp.setValue(style.envMode);
    }

    // Light distance relative to subject
    var lightDist = 250;

    // Helper to get or create a spot light by label
    function getOrCreateSpot(label) {
        var node = Scene.findNodeByLabel(label);
        if (node) return node;
        var light = new DzSpotLight();
        Scene.addNode(light);
        light.setLabel(label);
        return light;
    }

    function positionLight(light, angleDeg, height, dist) {
        var rad = angleDeg * (Math.PI / 180);
        var lx = subjectPos.x + dist * Math.sin(rad);
        var lz = subjectPos.z - dist * Math.cos(rad);
        var ly = height;

        var xp = light.findProperty("XTranslate");
        var yp = light.findProperty("YTranslate");
        var zp = light.findProperty("ZTranslate");
        if (xp) xp.setValue(lx);
        if (yp) yp.setValue(ly);
        if (zp) zp.setValue(lz);

        // Aim at subject
        var dx = subjectPos.x - lx;
        var dy = subjectPos.y - ly;
        var dz = subjectPos.z - lz;
        var distXZ = Math.sqrt(dx*dx + dz*dz);
        var yRot = light.findProperty("YRotate");
        var xRot = light.findProperty("XRotate");
        if (yRot) yRot.setValue(Math.atan2(dx, -dz) * (180 / Math.PI));
        if (xRot) xRot.setValue(Math.atan2(dy, distXZ) * (180 / Math.PI));
    }

    function setLightFlux(light, flux, shadowSoft) {
        var fp = light.findProperty("Flux");
        if (fp) fp.setValue(flux);
        var sp = light.findProperty("Shadow Softness");
        if (sp) sp.setValue(shadowSoft);
    }

    var lightsConfigured = [];

    // Key light
    var keyLight = getOrCreateSpot("Style_Key");
    positionLight(keyLight, style.keyAngle, subjectPos.y + 60, lightDist);
    setLightFlux(keyLight, keyFlux, style.shadowSoftness);
    lightsConfigured.push({role: "key", label: "Style_Key", flux: keyFlux, angle: style.keyAngle});

    // Fill light (opposite side, lower, softer)
    var fillAngle = style.keyAngle - 120;
    var fillLight = getOrCreateSpot("Style_Fill");
    positionLight(fillLight, fillAngle, subjectPos.y + 20, lightDist * 1.2);
    setLightFlux(fillLight, fillFlux, Math.min(1.0, style.shadowSoftness + 0.2));
    lightsConfigured.push({role: "fill", label: "Style_Fill", flux: fillFlux, angle: fillAngle});

    // Rim light (behind subject)
    var rimLight = getOrCreateSpot("Style_Rim");
    positionLight(rimLight, style.rimAngle, subjectPos.y + 80, lightDist * 0.8);
    setLightFlux(rimLight, rimFlux, style.shadowSoftness);
    lightsConfigured.push({role: "rim", label: "Style_Rim", flux: rimFlux, angle: style.rimAngle});

    return {
        styleName: styleName,
        description: style.description,
        intensity: intensity,
        subject: subjectLabel,
        environmentMode: style.envMode,
        lights: lightsConfigured,
        lightingRatios: {
            key: keyFlux,
            fill: fillFlux,
            rim: rimFlux,
            keyToFill: Math.round(keyFlux / Math.max(1, fillFlux) * 10) / 10,
            keyToRim: Math.round(keyFlux / Math.max(1, rimFlux) * 10) / 10
        },
        suggestions: [
            "Adjust intensity (0.5–2.0) to scale the whole look brighter or darker",
            "Fine-tune individual lights with daz_set_property on Style_Key/Fill/Rim",
            "Combine with daz_set_scene_atmosphere to control the environment dome",
            "Use daz_animate_light on Style_Key for dynamic lighting within the style"
        ]
    };
})()
"""

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
    "vangard-interactive-pose": (
        "Coordinate two characters for interactive poses (hug, handshake, etc)",
        _INTERACTIVE_POSE_SCRIPT,
    ),
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
    "vangard-animate-conversation": (
        "Choreograph animated conversation between two characters with look-at and "
        "emotion keyframes",
        _ANIMATE_CONVERSATION_SCRIPT,
    ),
    "vangard-create-scene": (
        "Generate a complete scene from natural language description with lighting, "
        "cameras, and positioning",
        _CREATE_SCENE_SCRIPT,
    ),
    "vangard-create-character-path": (
        "Animate character movement along a path with waypoints",
        _CREATE_CHARACTER_PATH_SCRIPT,
    ),
    "vangard-arrange-characters": (
        "Position multiple characters in formation (line, semicircle, triangle, circle)",
        _ARRANGE_CHARACTERS_SCRIPT,
    ),
    "vangard-choreograph-action": (
        "Choreograph simple action between characters (handshake, hug, fight, dance)",
        _CHOREOGRAPH_ACTION_SCRIPT,
    ),
    "vangard-animate-light": (
        "Animate a light's intensity with flicker, pulse, fade, strobe, or color-cycle effects",
        _ANIMATE_LIGHT_SCRIPT,
    ),
    "vangard-create-light-sequence": (
        "Create a multi-light animated sequence for a mood or time-of-day "
        "(day-to-night, romantic, etc.)",
        _CREATE_LIGHT_SEQUENCE_SCRIPT,
    ),
    "vangard-set-scene-atmosphere": (
        "Configure environment node settings (mode, intensity, dome) for atmosphere and mood",
        _SET_SCENE_ATMOSPHERE_SCRIPT,
    ),
    "vangard-apply-visual-style": (
        "Apply a holistic cinematic visual style (noir, golden-hour, high-key, etc.) "
        "to lights and environment",
        _APPLY_VISUAL_STYLE_SCRIPT,
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

