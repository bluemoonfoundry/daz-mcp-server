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
_SCENE_INFO_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var figures = [];
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var s = Scene.getSkeleton(i);
        // Skip follower figures (eyelashes, tear surfaces, etc.) — their node
        // parent is another figure, not the scene root.
        var parent = s.getNodeParent();
        if (parent && parent.inherits("DzFigure")) continue;
        figures.push({ name: s.getName(), label: s.getLabel(), type: s.className() });
    }
    var cameras = [];
    for (var i = 0; i < Scene.getNumCameras(); i++) {
        var c = Scene.getCamera(i);
        cameras.push({ name: c.getName(), label: c.getLabel() });
    }
    var lights = [];
    for (var i = 0; i < Scene.getNumLights(); i++) {
        var l = Scene.getLight(i);
        lights.push({ name: l.getName(), label: l.getLabel(), type: l.className() });
    }
    var sel = Scene.getPrimarySelection();
    return {
        sceneFile: Scene.getFilename(),
        selectedNode: sel ? sel.getLabel() : null,
        figures: figures,
        cameras: cameras,
        lights: lights,
        totalNodes: Scene.getNumNodes()
    };
})()
"""

# args: {nodeLabel} — label, internal name, elementID, or Parent/Label
# Returns: {name, label, type, elementID, parent, properties:{label:value}}
_GET_NODE_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var n = resolveNode(args.nodeLabel);
    var props = {};
    var seen = {};
    function addNumeric(pr) {
        if (!pr || !pr.inherits("DzNumericProperty")) return;
        var key = pr.getName();
        if (seen[key]) return;
        seen[key] = true;
        props[pr.getLabel()] = pr.getValue();
    }
    var p;
    for (p = 0; p < n.getNumProperties(); p++) addNumeric(n.getProperty(p));
    var obj = (typeof n.getObject === "function") ? n.getObject() : null;
    if (obj && typeof obj.getNumModifiers === "function") {
        for (p = 0; p < obj.getNumModifiers(); p++) {
            var m = obj.getModifier(p);
            if (!m) continue;
            if (typeof m.getValueChannel === "function") addNumeric(m.getValueChannel());
            if (typeof m.getNumProperties === "function") {
                for (var j = 0; j < m.getNumProperties(); j++) addNumeric(m.getProperty(j));
            }
        }
    }
    var parent = n.getNodeParent ? n.getNodeParent() : null;
    return {
        name: n.getName(),
        label: n.getLabel(),
        type: n.className(),
        elementID: n.elementID,
        parent: parent ? parent.getLabel() : null,
        properties: props
    };
})()
"""

# args: {nodeLabel, propertyName, value}
# Returns: {node, property, value}
# Matches propertyName against both display label and internal name.
_SET_PROPERTY_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var n = resolveNode(args.nodeLabel);
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
    var prop = findProp(n, args.propertyName);
    if (!prop) throw new Error("Property not found: " + args.propertyName + " on " + args.nodeLabel);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);
    if (typeof prop.lock === "function" && prop.isLocked && prop.isLocked()) prop.lock(false);
    prop.setValue(args.value);
    return { node: n.getLabel(), elementID: n.elementID, property: prop.getLabel(), value: prop.getValue() };
})()
"""

# args: {outputPath?}
# Returns: {success}
# Render options are set directly on the DzRenderOptions object (Qt property syntax).
_RENDER_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();
    var path = args.outputPath || opts.renderImgFilename;
    if (!path) {
        throw new Error("Render output path is not set. Pass output_path or call daz_set_render_output first — otherwise Studio opens a filename dialog.");
    }
    opts.renderImgToId = opts.DirectToFile;
    opts.renderImgFilename = path;
    try {
        var helper = renderMgr.getOptionHelper();
        if (helper) {
            var slash = Math.max(String(path).lastIndexOf("/"), String(path).lastIndexOf("\\\\"));
            var dir = slash >= 0 ? String(path).substring(0, slash) : "";
            var name = slash >= 0 ? String(path).substring(slash + 1) : String(path);
            var np = helper.findProperty("Image Name");
            var pp = helper.findProperty("Image Path");
            if (np && typeof np.setValue === "function") np.setValue(name);
            if (pp && typeof pp.setValue === "function") pp.setValue(dir);
        }
    } catch (e) {}
    opts.applyChanges();
    if (Number(opts.renderImgToId) !== Number(opts.DirectToFile) || !opts.renderImgFilename) {
        throw new Error("Render-to-file did not persist (renderImgToId=" + opts.renderImgToId + ", file=" + opts.renderImgFilename + ")");
    }
    renderMgr.doRender(opts);
    return { success: true, outputPath: opts.renderImgFilename };
})()
"""

# args: {filePath, merge}
# Returns: {success, file}
# openFile(path, true)  → merge into current scene
# openFile(path, false) → replace current scene
_LOAD_FILE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    App.getContentMgr().openFile(args.filePath, args.merge);
    return { success: true, file: args.filePath };
})()
"""

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
_GET_NODE_HIERARCHY_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var node = resolveNode(args.nodeLabel);

    var maxDepth = args.maxDepth !== undefined ? args.maxDepth : 10;
    var totalDescendants = 0;

    function buildHierarchy(n, depth) {
        if (maxDepth > 0 && depth >= maxDepth) {
            return null;
        }

        var nodeInfo = {
            label: n.getLabel(),
            name: n.getName(),
            type: n.className(),
            elementID: n.elementID
        };

        var children = [];
        for (var i = 0; i < n.getNumNodeChildren(); i++) {
            totalDescendants++;
            var childHierarchy = buildHierarchy(n.getNodeChild(i), depth + 1);
            if (childHierarchy) {
                children.push(childHierarchy);
            }
        }

        if (children.length > 0) {
            nodeInfo.children = children;
        }

        return nodeInfo;
    }

    var hierarchy = buildHierarchy(node, 0);

    return {
        node: node.getLabel(),
        hierarchy: hierarchy,
        totalDescendants: totalDescendants
    };
})()
"""

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
_SET_PARENT_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var node = resolveNode(args.nodeLabel);
    var newParent = resolveNode(args.parentLabel);

    var maintainWorldTransform = args.maintainWorldTransform !== undefined ? args.maintainWorldTransform : true;

    var previousParent = node.getNodeParent();
    var previousParentLabel = previousParent ? previousParent.getLabel() : null;

    // addNodeChild detaches node from its current parent (or scene root) automatically.
    // inPlace=true means maintain world position (child's local transform is adjusted).
    newParent.addNodeChild(node, maintainWorldTransform);

    return {
        success: true,
        node: node.getLabel(),
        newParent: newParent.getLabel(),
        previousParent: previousParentLabel
    };
})()
"""

# args: {characterLabel, targetX, targetY, targetZ, mode}
# mode: "eyes", "head", "neck", "torso", "full"
# Returns: {success, character, mode, rotatedBones}
# Makes character look at a world-space point with cascading body involvement
_LOOK_AT_POINT_SCRIPT = """\
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

    var figure = Scene.findNodeByLabel(args.characterLabel);
    if (!figure) figure = Scene.findNode(args.characterLabel);
    if (!figure) throw new Error("Character not found: " + args.characterLabel);

    var targetX = args.targetX;
    var targetY = args.targetY;
    var targetZ = args.targetZ;
    var mode = args.mode || "head";

    var rotatedBones = [];

    // Get bone positions and calculate rotations
    function rotateBoneToward(bone, tx, ty, tz, scale) {
        if (!bone) return false;
        var pos = bone.getWSPos();
        var dx = tx - pos.x;
        var dy = ty - pos.y;
        var dz = tz - pos.z;

        // Calculate angles (absolute, not additive — look-at is a state, not a delta)
        var angleY = Math.atan2(dx, dz) * (180 / Math.PI) * scale;
        var dist = Math.sqrt(dx*dx + dz*dz);
        var angleX = Math.atan2(dy, dist) * (180 / Math.PI) * scale;

        var yProp = bone.findProperty("YRotate");
        var xProp = bone.findProperty("XRotate");

        // Set absolute rotation; DAZ clamps to the property's own min/max automatically
        if (yProp) yProp.setValue(angleY);
        if (xProp) xProp.setValue(angleX);

        rotatedBones.push(bone.getLabel());
        return true;
    }

    // Generation-agnostic bone lookup (Gen9: l_eye/neck1/spine3; Gen3/8: lEye/neckUpper/chestUpper)
    var lEyeBone     = findBone(figure, "l_eye")      || findBone(figure, "lEye");
    var rEyeBone     = findBone(figure, "r_eye")      || findBone(figure, "rEye");
    var headBone     = findBone(figure, "head");
    var neckUpBone   = findBone(figure, "neck2")      || findBone(figure, "neckUpper");
    var neckLowBone  = findBone(figure, "neck1")      || findBone(figure, "neckLower");
    var chestUpBone  = findBone(figure, "spine3")     || findBone(figure, "chestUpper");
    var chestLowBone = findBone(figure, "spine2")     || findBone(figure, "chestLower");
    var hipBone      = findBone(figure, "hip");

    // Eyes (if mode is eyes or higher)
    if (mode === "eyes" || mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        if (lEyeBone) rotateBoneToward(lEyeBone, targetX, targetY, targetZ, 1.0);
        if (rEyeBone) rotateBoneToward(rEyeBone, targetX, targetY, targetZ, 1.0);
    }

    // Head (if mode is head or higher)
    if (mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        if (headBone) rotateBoneToward(headBone, targetX, targetY, targetZ, 0.6);
    }

    // Neck (if mode is neck or higher)
    if (mode === "neck" || mode === "torso" || mode === "full") {
        if (neckUpBone)  rotateBoneToward(neckUpBone,  targetX, targetY, targetZ, 0.3);
        if (neckLowBone) rotateBoneToward(neckLowBone, targetX, targetY, targetZ, 0.3);
    }

    // Torso (if mode is torso or full)
    if (mode === "torso" || mode === "full") {
        if (chestUpBone)  rotateBoneToward(chestUpBone,  targetX, targetY, targetZ, 0.15);
        if (chestLowBone) rotateBoneToward(chestLowBone, targetX, targetY, targetZ, 0.15);
    }

    // Full body rotation (if mode is full)
    if (mode === "full") {
        if (hipBone) rotateBoneToward(hipBone, targetX, targetY, targetZ, 0.1);
    }

    return {
        success: true,
        character: figure.getLabel(),
        mode: mode,
        rotatedBones: rotatedBones
    };
})()
"""

# args: {sourceLabel, targetLabel, mode}
# mode: "eyes", "head", "neck", "torso", "full" (default: "head")
# Returns: {success, source, target, mode, targetPosition}
# Makes source character look at target character's head position
_LOOK_AT_CHARACTER_SCRIPT = """\
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

    var source = Scene.findNodeByLabel(args.sourceLabel);
    if (!source) source = Scene.findNode(args.sourceLabel);
    if (!source) throw new Error("Source character not found: " + args.sourceLabel);

    var target = Scene.findNodeByLabel(args.targetLabel);
    if (!target) target = Scene.findNode(args.targetLabel);
    if (!target) throw new Error("Target character not found: " + args.targetLabel);

    // Find target's head to get face position
    var targetHead = findBone(target, "head");
    if (!targetHead) {
        // Fallback to figure root position + approximate head height
        var pos = target.getWSPos();
        var targetX = pos.x;
        var targetY = pos.y + 163; // Approximate head height for Genesis 9
        var targetZ = pos.z;
    } else {
        var headPos = targetHead.getWSPos();
        var targetX = headPos.x;
        var targetY = headPos.y;
        var targetZ = headPos.z;
    }

    var mode = args.mode || "head";
    var rotatedBones = [];

    // Reuse rotation logic from look-at-point
    function rotateBoneToward(bone, tx, ty, tz, scale) {
        if (!bone) return false;
        var pos = bone.getWSPos();
        var dx = tx - pos.x;
        var dy = ty - pos.y;
        var dz = tz - pos.z;

        var angleY = Math.atan2(dx, dz) * (180 / Math.PI) * scale;
        var dist = Math.sqrt(dx*dx + dz*dz);
        var angleX = Math.atan2(dy, dist) * (180 / Math.PI) * scale;

        var yProp = bone.findProperty("YRotate");
        var xProp = bone.findProperty("XRotate");

        // Absolute rotation — look-at is a state, not a delta
        if (yProp) yProp.setValue(angleY);
        if (xProp) xProp.setValue(angleX);

        rotatedBones.push(bone.getLabel());
        return true;
    }

    // Generation-agnostic bone lookup
    var lEyeBone    = findBone(source, "l_eye")   || findBone(source, "lEye");
    var rEyeBone    = findBone(source, "r_eye")   || findBone(source, "rEye");
    var headBone    = findBone(source, "head");
    var neckUpBone  = findBone(source, "neck2")   || findBone(source, "neckUpper");
    var neckLowBone = findBone(source, "neck1")   || findBone(source, "neckLower");

    if (mode === "eyes" || mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        if (lEyeBone) rotateBoneToward(lEyeBone, targetX, targetY, targetZ, 1.0);
        if (rEyeBone) rotateBoneToward(rEyeBone, targetX, targetY, targetZ, 1.0);
    }

    if (mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        if (headBone) rotateBoneToward(headBone, targetX, targetY, targetZ, 0.6);
    }

    if (mode === "neck" || mode === "torso" || mode === "full") {
        if (neckUpBone)  rotateBoneToward(neckUpBone,  targetX, targetY, targetZ, 0.3);
        if (neckLowBone) rotateBoneToward(neckLowBone, targetX, targetY, targetZ, 0.3);
    }

    if (mode === "torso" || mode === "full") {
        var chestUpBone2  = findBone(source, "spine3")  || findBone(source, "chestUpper");
        var chestLowBone2 = findBone(source, "spine2")  || findBone(source, "chestLower");
        if (chestUpBone2)  rotateBoneToward(chestUpBone2,  targetX, targetY, targetZ, 0.15);
        if (chestLowBone2) rotateBoneToward(chestLowBone2, targetX, targetY, targetZ, 0.15);
    }

    if (mode === "full") {
        var hipBone2 = findBone(source, "hip");
        if (hipBone2) rotateBoneToward(hipBone2, targetX, targetY, targetZ, 0.1);
    }

    return {
        success: true,
        source: source.getLabel(),
        target: target.getLabel(),
        mode: mode,
        targetPosition: {x: targetX, y: targetY, z: targetZ},
        rotatedBones: rotatedBones
    };
})()
"""

# args: {characterLabel, side, targetX, targetY, targetZ}
# side: "left" or "right"
# Returns: {success, character, side, bones}
# Position arm/hand to reach toward world-space point using pseudo-IK
_REACH_TOWARD_SCRIPT = """\
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

    var figure = Scene.findNodeByLabel(args.characterLabel);
    if (!figure) figure = Scene.findNode(args.characterLabel);
    if (!figure) throw new Error("Character not found: " + args.characterLabel);

    var side = args.side || "right";
    var prefix8 = (side === "right") ? "r" : "l";   // Genesis 3/8 prefix
    var prefix9 = (side === "right") ? "r" : "l";   // Genesis 9 prefix (same letter, different naming)

    // Try Genesis 9 names first, fall back to Genesis 3/8
    var shoulder = findBone(figure, prefix9 + "_upperarm") ||
                   findBone(figure, prefix8 + "ShldrBend") ||
                   findBone(figure, prefix8 + "Shldr");
    var forearm  = findBone(figure, prefix9 + "_forearm") ||
                   findBone(figure, prefix8 + "ForearmBend") ||
                   findBone(figure, prefix8 + "Forearm");
    var hand     = findBone(figure, prefix9 + "_hand") ||
                   findBone(figure, prefix8 + "Hand");

    if (!shoulder || !forearm) {
        throw new Error("Arm bones not found for side: " + side);
    }

    var targetX = args.targetX;
    var targetY = args.targetY;
    var targetZ = args.targetZ;

    // Get shoulder world position
    var shoulderPos = shoulder.getWSPos();
    var dx = targetX - shoulderPos.x;
    var dy = targetY - shoulderPos.y;
    var dz = targetZ - shoulderPos.z;

    // Calculate distance to target
    var dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

    // Calculate shoulder rotation angles
    // YRotate: turn toward target (left/right)
    var angleY = Math.atan2(dx, dz) * (180 / Math.PI);

    // XRotate: pitch toward target (up/down)
    var horizDist = Math.sqrt(dx*dx + dz*dz);
    var angleX = Math.atan2(dy, horizDist) * (180 / Math.PI);

    // ZRotate: lift arm away from body
    var angleZ = Math.atan2(Math.abs(dx), Math.abs(dy)) * (180 / Math.PI);
    if (side === "left") angleZ = -angleZ;

    // Apply shoulder rotations with realistic limits
    var xProp = shoulder.findProperty("XRotate");
    var yProp = shoulder.findProperty("YRotate");
    var zProp = shoulder.findProperty("ZRotate");

    if (xProp) xProp.setValue(clamp(angleX, -90, 180));
    if (yProp) yProp.setValue(clamp(angleY, -90, 90));
    if (zProp) zProp.setValue(clamp(angleZ, side === "right" ? -30 : -180, side === "right" ? 180 : 30));

    // Calculate elbow bend based on distance
    // Approximate arm length: shoulder to hand ~60cm
    // If target is far, straighten arm; if close, bend elbow
    var maxReach = 60; // Approximate full arm length in cm
    var bendFactor = Math.max(0, Math.min(1, 1 - (dist / maxReach)));
    var elbowBend = -140 * bendFactor; // -140 is max elbow bend

    var elbowProp = forearm.findProperty("YRotate");
    if (elbowProp) elbowProp.setValue(clamp(elbowBend, -140, 0));

    // Slight hand rotation for natural look
    if (hand) {
        var handXProp = hand.findProperty("XRotate");
        if (handXProp) handXProp.setValue(-10); // Slight downward tilt
    }

    return {
        success: true,
        character: figure.getLabel(),
        side: side,
        targetDistance: dist,
        bones: [
            shoulder.getLabel(),
            forearm.getLabel(),
            hand ? hand.getLabel() : null
        ]
    };
})()
"""

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
_BATCH_SET_PROPERTIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var operations = args.operations || [];
    var results = [];
    var successCount = 0;
    var failureCount = 0;

    for (var i = 0; i < operations.length; i++) {
        var op = operations[i];
        var result = { success: false, node: op.nodeLabel };

        try {
            var n = Scene.findNodeByLabel(op.nodeLabel);
            if (!n) n = Scene.findNode(op.nodeLabel);
            if (!n) throw new Error("Node not found: " + op.nodeLabel);

            var prop = null;
            for (var p = 0; p < n.getNumProperties(); p++) {
                var pr = n.getProperty(p);
                if (pr.getLabel() === op.propertyName || pr.getName() === op.propertyName) {
                    prop = pr;
                    break;
                }
            }

            if (!prop) throw new Error("Property not found: " + op.propertyName);
            if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + op.propertyName);

            prop.setValue(op.value);
            result.success = true;
            result.property = prop.getLabel();
            result.value = prop.getValue();
            successCount++;
        } catch (e) {
            result.error = e.message || String(e);
            failureCount++;
        }

        results.push(result);
    }

    return {
        results: results,
        successCount: successCount,
        failureCount: failureCount,
        total: operations.length
    };
})()
"""

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
_SET_ACTIVE_CAMERA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);
    if (!cam.inherits("DzCamera")) throw new Error("Node is not a camera: " + args.cameraLabel);

    var previousCamera = null;
    var viewportMgr = MainWindow.getViewportMgr();
    if (viewportMgr) {
        var activeViewport = viewportMgr.getActiveViewport();
        if (activeViewport) {
            var prevCam = activeViewport.get3DViewport().getCamera();
            if (prevCam) previousCamera = prevCam.getLabel();
            activeViewport.get3DViewport().setCamera(cam);
        }
    }

    return {
        success: true,
        camera: cam.getLabel(),
        previousCamera: previousCamera
    };
})()
"""

# args: {cameraLabel, targetLabel, distance, angleHorizontal, angleVertical}
# Returns: {success, camera, target, position}
# Position camera orbiting around a target node at specified angle and distance
_ORBIT_CAMERA_AROUND_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var target = Scene.findNodeByLabel(args.targetLabel);
    if (!target) target = Scene.findNode(args.targetLabel);
    if (!target) throw new Error("Target not found: " + args.targetLabel);

    var distance = args.distance !== undefined ? args.distance : 200;
    var angleH = args.angleHorizontal !== undefined ? args.angleHorizontal : 45;
    var angleV = args.angleVertical !== undefined ? args.angleVertical : 15;

    // Get target world position
    var targetPos = target.getWSPos();
    var targetY = targetPos.y;

    // Calculate camera position using spherical coordinates
    var angleHRad = angleH * (Math.PI / 180);
    var angleVRad = angleV * (Math.PI / 180);

    var x = targetPos.x + distance * Math.cos(angleVRad) * Math.sin(angleHRad);
    var y = targetY + distance * Math.sin(angleVRad);
    var z = targetPos.z + distance * Math.cos(angleVRad) * Math.cos(angleHRad);

    // Set camera position
    cam.findProperty("XTranslate").setValue(x);
    cam.findProperty("YTranslate").setValue(y);
    cam.findProperty("ZTranslate").setValue(z);

    // Aim camera at target
    cam.aimAt(targetPos);

    return {
        success: true,
        camera: cam.getLabel(),
        target: target.getLabel(),
        position: {x: x, y: y, z: z},
        targetPosition: {x: targetPos.x, y: targetPos.y, z: targetPos.z}
    };
})()
"""

# args: {cameraLabel, nodeLabel, distance}
# Returns: {success, camera, node, position}
# Frame camera to show a node by positioning at calculated distance
_FRAME_CAMERA_TO_NODE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    // Get node bounding box (getWSBoundingBox is on DzNode; getSize() returns scalar diagonal)
    var bbox = node.getWSBoundingBox();
    var center = bbox.getCenter();
    var sizeX = bbox.maxX - bbox.minX;
    var sizeY = bbox.maxY - bbox.minY;
    var sizeZ = bbox.maxZ - bbox.minZ;
    var maxDim = Math.max(sizeX, Math.max(sizeY, sizeZ));

    // Calculate distance based on object size or use provided distance
    var distance = args.distance !== undefined ? args.distance : maxDim * 2.5;

    // Position camera in front of object (positive Z)
    var camX = center.x;
    var camY = center.y;
    var camZ = center.z + distance;

    cam.findProperty("XTranslate").setValue(camX);
    cam.findProperty("YTranslate").setValue(camY);
    cam.findProperty("ZTranslate").setValue(camZ);

    // Aim camera at center
    cam.aimAt(center);

    return {
        success: true,
        camera: cam.getLabel(),
        node: node.getLabel(),
        position: {x: camX, y: camY, z: camZ},
        nodeCenter: {x: center.x, y: center.y, z: center.z},
        nodeSize: {x: sizeX, y: sizeY, z: sizeZ}
    };
})()
"""

# args: {cameraLabel}
# Returns: {preset: {transforms, label}}
# Save camera position and rotation as preset data
_SAVE_CAMERA_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var preset = {
        label: cam.getLabel(),
        transforms: {}
    };

    var props = ["XTranslate", "YTranslate", "ZTranslate",
                 "XRotate", "YRotate", "ZRotate",
                 "XScale", "YScale", "ZScale"];

    for (var i = 0; i < props.length; i++) {
        var prop = cam.findProperty(props[i]);
        if (prop) {
            preset.transforms[props[i]] = prop.getValue();
        }
    }

    return {preset: preset};
})()
"""

# args: {cameraLabel, preset}
# Returns: {success, camera, applied}
# Restore camera position and rotation from preset data
_LOAD_CAMERA_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var preset = args.preset;
    if (!preset || !preset.transforms) throw new Error("Invalid preset data");

    var applied = [];
    for (var propName in preset.transforms) {
        var prop = cam.findProperty(propName);
        if (prop) {
            prop.setValue(preset.transforms[propName]);
            applied.push(propName);
        }
    }

    return {
        success: true,
        camera: cam.getLabel(),
        applied: applied
    };
})()
"""

# args: {cameraLabel, outputPath}
# Returns: {success, camera, outputPath}
# Render from specific camera (doesn't change active viewport camera)
_RENDER_WITH_CAMERA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);
    if (!cam.inherits("DzCamera")) throw new Error("Node is not a camera: " + args.cameraLabel);

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    var path = args.outputPath || opts.renderImgFilename;
    if (!path) {
        throw new Error("Render output path is not set. Pass output_path or call daz_set_render_output first — otherwise Studio opens a filename dialog.");
    }

    // DS6: doRender() renders from the active 3D viewport's camera and ignores
    // opts.camera, so the viewport camera must be switched too (verified live:
    // viewport=FaceCam + opts.camera="Portrait Cam" rendered FaceCam).
    var viewport3D = null;
    try {
        var vpMgr = MainWindow.getViewportMgr();
        var activeVp = vpMgr ? vpMgr.getActiveViewport() : null;
        viewport3D = activeVp ? activeVp.get3DViewport() : null;
    } catch (e) { viewport3D = null; }
    if (!viewport3D) throw new Error("Cannot access the active 3D viewport to select the render camera");
    var previousViewportCam = viewport3D.getCamera();

    // Save previous camera
    var previousCam = opts.camera;
    var renderedFrom = null;

    try {
        // Set render camera (viewport camera is what DS6 actually renders from)
        opts.camera = cam;
        viewport3D.setCamera(cam);

        opts.renderImgToId = opts.DirectToFile;
        opts.renderImgFilename = path;
        try {
            var helper = renderMgr.getOptionHelper();
            if (helper) {
                var slash = Math.max(String(path).lastIndexOf("/"), String(path).lastIndexOf("\\\\"));
                var dir = slash >= 0 ? String(path).substring(0, slash) : "";
                var name = slash >= 0 ? String(path).substring(slash + 1) : String(path);
                var np = helper.findProperty("Image Name");
                var pp = helper.findProperty("Image Path");
                if (np && typeof np.setValue === "function") np.setValue(name);
                if (pp && typeof pp.setValue === "function") pp.setValue(dir);
            }
        } catch (e) {}
        opts.applyChanges();
        if (Number(opts.renderImgToId) !== Number(opts.DirectToFile) || !opts.renderImgFilename) {
            throw new Error("Render-to-file did not persist (renderImgToId=" + opts.renderImgToId + ", file=" + opts.renderImgFilename + ")");
        }
        var activeCam = viewport3D.getCamera();
        renderedFrom = activeCam ? activeCam.getLabel() : null;
        if (renderedFrom !== cam.getLabel()) {
            throw new Error("Viewport camera did not switch to " + cam.getLabel() + " (active: " + renderedFrom + ")");
        }
        renderMgr.doRender(opts);
    } finally {
        if (previousViewportCam) viewport3D.setCamera(previousViewportCam);
        opts.camera = previousCam;  // may be null; never leave a dangling camera ref
        opts.applyChanges();
    }

    return {
        success: true,
        camera: cam.getLabel(),
        renderedFromCamera: renderedFrom,
        outputPath: args.outputPath || null
    };
})()
"""

# args: none
# Returns: {renderToFile, currentCamera, aspectRatio, aspectWidth, aspectHeight}
# Get current render settings
_GET_RENDER_SETTINGS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    // DzRenderOptions.renderImgToId is an enum, and DirectToFile is 2 - not 0.
    // Comparing against 0 made renderToFile always false and outputPath always
    // null, even with a correctly configured file render. Compare against the
    // named constant so this cannot drift again.
    var directToFile = Number(opts.DirectToFile);
    var rendersToFile = Number(opts.renderImgToId) === directToFile;

    var sz = opts.imageSize;
    var renderType = Number(opts.renderType);
    var engine = "other";
    var renderTypeName = null;
    if (renderType === Number(opts.ScreenShot)) {
        engine = "viewport";
        renderTypeName = "ScreenShot";
    } else if (renderType === Number(opts.HardwareAssisted)) {
        engine = "multi_pass_opengl";
        renderTypeName = "HardwareAssisted";
    } else if (renderType === Number(opts.Software)) {
        engine = "iray";
        renderTypeName = "Software";
    }
    var active = renderMgr.getActiveRenderer();
    var result = {
        renderToFile: rendersToFile,
        outputPath: rendersToFile ? opts.renderImgFilename : null,
        aspectRatio: opts.aspect,
        aspectWidth: opts.aspectWidth,
        aspectHeight: opts.aspectHeight,
        width: sz ? sz.width : null,
        height: sz ? sz.height : null,
        engine: engine,
        renderType: renderType,
        renderTypeName: renderTypeName,
        activeRenderer: active ? active.getName() : null,
        activeRendererClass: active ? active.className() : null
    };
    if (engine === "viewport") {
        result.warning = "Engine Viewport opens a filename dialog unless DirectToFile + output path are set.";
    }

    // Get current render camera
    if (opts.camera) {
        result.currentCamera = opts.camera.getLabel();
    } else {
        result.currentCamera = null;
    }

    return result;
})()
"""

# args: {cameras: [labels], outputDir, baseFilename}
# Returns: {success, rendered: [{camera, outputPath}], total}
# Render from multiple cameras in sequence
_BATCH_RENDER_CAMERAS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cameras = args.cameras || [];
    var outputDir = args.outputDir || "";
    var baseFilename = args.baseFilename || "render";

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();
    var previousCam = opts.camera;
    var previousFilename = opts.renderImgFilename;

    // DS6: doRender() renders from the active 3D viewport's camera and ignores
    // opts.camera, so the viewport camera must be switched too (verified live:
    // viewport=FaceCam + opts.camera="Portrait Cam" rendered FaceCam).
    var viewport3D = null;
    try {
        var vpMgr = MainWindow.getViewportMgr();
        var activeVp = vpMgr ? vpMgr.getActiveViewport() : null;
        viewport3D = activeVp ? activeVp.get3DViewport() : null;
    } catch (e) { viewport3D = null; }
    if (!viewport3D) throw new Error("Cannot access the active 3D viewport to select the render camera");
    var previousViewportCam = viewport3D.getCamera();

    var rendered = [];

    try {
        for (var i = 0; i < cameras.length; i++) {
            var camLabel = cameras[i];
            var cam = Scene.findNodeByLabel(camLabel);
            if (!cam) cam = Scene.findNode(camLabel);

            if (cam && cam.inherits("DzCamera")) {
                // Build output path
                var outputPath = outputDir;
                if (outputPath && outputPath.charAt(outputPath.length - 1) !== "/" &&
                    outputPath.charAt(outputPath.length - 1) !== "\\\\") {
                    outputPath += "/";
                }
                outputPath += baseFilename + "_" + camLabel.replace(/[^a-zA-Z0-9]/g, "_") + ".png";

                // Viewport camera is what DS6 actually renders from
                opts.camera = cam;
                viewport3D.setCamera(cam);
                var activeCam = viewport3D.getCamera();
                if (!activeCam || activeCam.getLabel() !== cam.getLabel()) {
                    throw new Error("Viewport camera did not switch to " + cam.getLabel());
                }
                opts.renderImgToId = opts.DirectToFile;
                opts.renderImgFilename = outputPath;
                opts.applyChanges();
                renderMgr.doRender(opts);

                rendered.push({
                    camera: cam.getLabel(),
                    renderedFromCamera: activeCam.getLabel(),
                    outputPath: outputPath
                });
            }
        }
    } finally {
        if (previousViewportCam) viewport3D.setCamera(previousViewportCam);
        opts.camera = previousCam;  // may be null; never leave a dangling camera ref
        opts.renderImgFilename = previousFilename;
        opts.applyChanges();
    }

    return {
        success: true,
        rendered: rendered,
        total: cameras.length
    };
})()
"""

# args: {startFrame, endFrame, outputDir, filenamePattern, camera}
# Returns: {success, rendered: [{frame, outputPath}], total}
# Render animation frame range
_RENDER_ANIMATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var startFrame = args.startFrame !== undefined ? args.startFrame : Scene.getAnimRange().getStart();
    var endFrame = args.endFrame !== undefined ? args.endFrame : Scene.getAnimRange().getEnd();
    var outputDir = args.outputDir || "";
    var filenamePattern = args.filenamePattern || "frame";

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    // DS6: doRender() renders from the active 3D viewport's camera and ignores
    // opts.camera, so the viewport camera must be switched too (verified live:
    // viewport=FaceCam + opts.camera="Portrait Cam" rendered FaceCam).
    var viewport3D = null;
    try {
        var vpMgr = MainWindow.getViewportMgr();
        var activeVp = vpMgr ? vpMgr.getActiveViewport() : null;
        viewport3D = activeVp ? activeVp.get3DViewport() : null;
    } catch (e) { viewport3D = null; }
    if (!viewport3D) throw new Error("Cannot access the active 3D viewport to select the render camera");
    var previousViewportCam = viewport3D.getCamera();

    // Set camera if specified (viewport camera is what DS6 actually renders from)
    var previousCam = opts.camera;
    var cam = null;
    if (args.camera) {
        cam = Scene.findNodeByLabel(args.camera);
        if (!cam) cam = Scene.findNode(args.camera);
        if (!cam || !cam.inherits("DzCamera")) throw new Error("Camera not found: " + args.camera);
    }

    var rendered = [];
    var previousFrame = Scene.getFrame();
    var previousFilename = opts.renderImgFilename;
    var renderedFrom = null;

    try {
        if (cam) {
            opts.camera = cam;
            viewport3D.setCamera(cam);
            var activeCam = viewport3D.getCamera();
            if (!activeCam || activeCam.getLabel() !== cam.getLabel()) {
                throw new Error("Viewport camera did not switch to " + cam.getLabel());
            }
        }
        var vpCam = viewport3D.getCamera();
        renderedFrom = vpCam ? vpCam.getLabel() : null;

        opts.renderImgToId = opts.DirectToFile;
        opts.applyChanges();

        for (var frame = startFrame; frame <= endFrame; frame++) {
            Scene.setFrame(frame);

            var frameStr = String(frame);
            while (frameStr.length < 4) frameStr = "0" + frameStr;

            var outputPath = outputDir;
            if (outputPath && outputPath.charAt(outputPath.length - 1) !== "/" &&
                outputPath.charAt(outputPath.length - 1) !== "\\\\") {
                outputPath += "/";
            }
            outputPath += filenamePattern + "_" + frameStr + ".png";

            opts.renderImgFilename = outputPath;
            opts.applyChanges();
            renderMgr.doRender(opts);

            rendered.push({
                frame: frame,
                outputPath: outputPath
            });
        }
    } finally {
        // Restore previous frame, camera, and output path
        Scene.setFrame(previousFrame);
        if (cam && previousViewportCam) viewport3D.setCamera(previousViewportCam);
        opts.camera = previousCam;  // may be null; never leave a dangling camera ref
        opts.renderImgFilename = previousFilename;
        opts.applyChanges();
    }

    return {
        success: true,
        rendered: rendered,
        total: rendered.length,
        renderedFromCamera: renderedFrom,
        frames: {start: startFrame, end: endFrame}
    };
})()
"""

# args: {nodeLabel, propertyName, frame, value}
# Returns: {success, node, property, frame, value}
# Set a keyframe on a property at specified frame
_SET_KEYFRAME_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var frame = args.frame;
    var value = args.value;

    // Set value at frame — two-arg setValue creates a keyframe (DzFloatProperty)
    prop.setValue(frame, value);

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        frame: frame,
        value: value
    };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {keyframes: [{frame, value}], count}
# Get all keyframes for a property
_GET_KEYFRAMES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var keyframes = [];
    var numKeys = prop.getNumKeys();

    for (var i = 0; i < numKeys; i++) {
        var frame = prop.getKeyTime(i);
        var value = prop.getKeyValue(i);
        keyframes.push({frame: frame, value: value});
    }

    return {
        keyframes: keyframes,
        count: numKeys
    };
})()
"""

# args: {nodeLabel, propertyName, frame}
# Returns: {success, node, property, frame, removed}
# Remove a keyframe at specified frame
_REMOVE_KEYFRAME_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var frame = args.frame;

    // Find and remove keyframe at the given frame
    var keyIndex = prop.findKeyIndex(frame);
    var removed = keyIndex >= 0;
    if (removed) {
        prop.deleteKeys(frame, frame);
    }

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        frame: frame,
        removed: removed
    };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {success, node, property, removed}
# Remove all keyframes from a property
_CLEAR_ANIMATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var numKeys = prop.getNumKeys();
    prop.deleteAllKeys();

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        removed: numKeys
    };
})()
"""

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
_INSPECT_PROPERTIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var typeFilter = args.propertyType || "all";

    var TRANSFORM_NAMES = {
        "XTranslate": 1, "YTranslate": 1, "ZTranslate": 1,
        "XRotate": 1, "YRotate": 1, "ZRotate": 1,
        "Scale": 1, "XScale": 1, "YScale": 1, "ZScale": 1
    };

    var props = [];
    for (var i = 0; i < node.getNumProperties(); i++) {
        var prop = node.getProperty(i);
        var className = prop.className();
        var isNumeric = prop.inherits("DzNumericProperty");
        var isBool = className === "DzBoolProperty";
        var isTransform = TRANSFORM_NAMES[prop.getName()] === 1;
        var isString = className === "DzStringProperty";

        var include = false;
        if (typeFilter === "all") include = true;
        else if (typeFilter === "numeric" && isNumeric) include = true;
        else if (typeFilter === "transform" && isTransform) include = true;
        else if (typeFilter === "bool" && isBool) include = true;
        else if (typeFilter === "string" && isString) include = true;
        else if (typeFilter === "morph" && isNumeric && !isTransform) include = true;

        if (!include) continue;

        var entry = {
            label: prop.getLabel(),
            name: prop.getName(),
            type: className,
            path: prop.getPath ? prop.getPath() : "",
            is_animatable: prop.isAnimatable ? prop.isAnimatable() : false
        };

        if (isNumeric) {
            entry.value = prop.getValue();
            entry.min = prop.getMin ? prop.getMin() : null;
            entry.max = prop.getMax ? prop.getMax() : null;
        } else if (isString && prop.getValue) {
            entry.value = prop.getValue();
            entry.min = null;
            entry.max = null;
        } else {
            entry.value = null;
            entry.min = null;
            entry.max = null;
        }

        props.push(entry);
    }

    return { node: node.getLabel(), properties: props, count: props.length };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {label, name, type, current_value, default_value, min, max,
#           is_animatable, path}
_GET_PROPERTY_METADATA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var i = 0; i < node.getNumProperties(); i++) {
        var p = node.getProperty(i);
        if (p.getLabel() === args.propertyName || p.getName() === args.propertyName) {
            prop = p; break;
        }
    }
    if (!prop) throw new Error("Property not found: " + args.propertyName +
                                " on " + args.nodeLabel);

    var isNumeric = prop.inherits("DzNumericProperty");

    return {
        label: prop.getLabel(),
        name: prop.getName(),
        type: prop.className(),
        current_value: isNumeric ? prop.getValue() : null,
        default_value: (isNumeric && prop.getDefaultValue) ? prop.getDefaultValue() : null,
        min: (isNumeric && prop.getMin) ? prop.getMin() : null,
        max: (isNumeric && prop.getMax) ? prop.getMax() : null,
        is_animatable: prop.isAnimatable ? prop.isAnimatable() : false,
        path: prop.getPath ? prop.getPath() : "",
        node: node.getLabel()
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Lighting Preset Script
# ---------------------------------------------------------------------------

# args: {preset, subjectLabel}
# preset: "three-point" | "rembrandt" | "butterfly" | "split" | "loop"
# Returns: {preset, subject, lights_created:[{label,type,position}], environment_mode}
# Creates lights relative to subject bounding box center.
# Genesis figures face +Z so "front" = positive Z side.
_APPLY_LIGHTING_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var preset = args.preset || "three-point";
    var subjectLabel = args.subjectLabel;

    // Get subject center if provided
    var subjectCenter = { x: 0, y: 150, z: 0 };
    var subjectHeight = 170;
    if (subjectLabel) {
        var subjectNode = Scene.findNodeByLabel(subjectLabel);
        if (!subjectNode) subjectNode = Scene.findNode(subjectLabel);
        if (subjectNode) {
            var bbox = subjectNode.getWSBoundingBox();
            subjectCenter = {
                x: (bbox.minX + bbox.maxX) / 2,
                y: (bbox.minY + bbox.maxY) / 2,
                z: (bbox.minZ + bbox.maxZ) / 2
            };
            subjectHeight = bbox.maxY - bbox.minY;
        }
    }

    var faceHeight = subjectCenter.y + subjectHeight * 0.2;  // ~head height
    var R = subjectHeight * 1.2;  // light orbit radius

    // Lighting configurations: [label, flux, azimuthDeg, elevDeg, lightClass, shadowSoftness]
    // azimuth: 0=front(+Z), 90=right(+X), 180=back, -90=left
    var configs = {
        "three-point": [
            ["Key Light",  2000, 45,   35,  "DzSpotLight", 30],
            ["Fill Light",  800, -45,  20,  "DzSpotLight", 60],
            ["Rim Light",  1200, 180,  45,  "DzDistantLight", 20]
        ],
        "rembrandt": [
            ["Key Light",  2200, 45,   45,  "DzSpotLight", 20],
            ["Fill Light",  400, -90,  10,  "DzSpotLight", 80]
        ],
        "butterfly": [
            ["Key Light",  2000,  0,   45,  "DzSpotLight", 25],
            ["Fill Light",  500,  0,   -5,  "DzSpotLight", 80]
        ],
        "split": [
            ["Key Light",  2200, 90,   15,  "DzSpotLight", 15],
            ["Rim Light",   800, -90,  20,  "DzSpotLight", 40]
        ],
        "loop": [
            ["Key Light",  2000, 35,   30,  "DzSpotLight", 35],
            ["Fill Light",  700, -50,  15,  "DzSpotLight", 70],
            ["Rim Light",   900, 160,  40,  "DzSpotLight", 25]
        ]
    };

    var lightDefs = configs[preset];
    if (!lightDefs) throw new Error("Unknown preset: " + preset +
        ". Valid: three-point, rembrandt, butterfly, split, loop");

    // Remove existing preset lights with same names to avoid duplicates
    var existingLabels = {};
    for (var d = 0; d < lightDefs.length; d++) {
        existingLabels[lightDefs[d][0]] = 1;
    }
    for (var ni = 0; ni < Scene.getNumLights(); ni++) {
        var existingLight = Scene.getLight(ni);
        if (existingLabels[existingLight.getLabel()]) {
            Scene.removeNode(existingLight);
            ni--;
        }
    }

    var created = [];

    for (var i = 0; i < lightDefs.length; i++) {
        var def = lightDefs[i];
        var label     = def[0];
        var flux      = def[1];
        var azimuthDeg = def[2];
        var elevDeg   = def[3];
        var lightClass = def[4];
        var softness  = def[5];

        var azRad = azimuthDeg * Math.PI / 180;
        var elRad = elevDeg * Math.PI / 180;

        var lx = subjectCenter.x + R * Math.sin(azRad) * Math.cos(elRad);
        var ly = subjectCenter.y + R * Math.sin(elRad) + subjectHeight * 0.1;
        var lz = subjectCenter.z + R * Math.cos(azRad) * Math.cos(elRad);

        var light = null;
        if (lightClass === "DzSpotLight") {
            light = new DzSpotLight();
        } else {
            light = new DzDistantLight();
        }

        Scene.addNode(light);
        light.setLabel(label);

        var fluxProp = light.findProperty("Flux");
        if (fluxProp) fluxProp.setValue(flux);

        var softProp = light.findProperty("Shadow Softness");
        if (softProp) softProp.setValue(softness);

        var xtp = light.findProperty("XTranslate");
        var ytp = light.findProperty("YTranslate");
        var ztp = light.findProperty("ZTranslate");
        if (xtp) xtp.setValue(lx);
        if (ytp) ytp.setValue(ly);
        if (ztp) ztp.setValue(lz);

        light.aimAt(new DzVec3(subjectCenter.x, faceHeight, subjectCenter.z));

        created.push({
            label: label,
            type: lightClass,
            position: { x: Math.round(lx), y: Math.round(ly), z: Math.round(lz) },
            flux: flux
        });
    }

    // Set environment to scene-lights-only
    var envNode = Scene.getNode(1);
    if (envNode) {
        var envMode = envNode.findProperty("Environment Mode");
        if (envMode) envMode.setValue(3);
    }

    return {
        preset: preset,
        subject: subjectLabel || null,
        lights_created: created,
        environment_mode: "Scene Only (3)"
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Scene Validation Script
# ---------------------------------------------------------------------------

# args: none
# Returns: {valid, issues:[{type,severity,nodes,description,suggestion}],
#           warnings:[...], score, score_breakdown}
_VALIDATE_SCENE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var issues = [];
    var warnings = [];

    // --- 1. Collision detection between figures (bounding box AABB) ---
    var figures = [];
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var skel = Scene.getSkeleton(i);
        var bb = skel.getWSBoundingBox();
        figures.push({ label: skel.getLabel(), bb: bb });
    }

    for (var a = 0; a < figures.length; a++) {
        for (var b = a + 1; b < figures.length; b++) {
            var f1 = figures[a];
            var f2 = figures[b];
            var overlapX = Math.min(f1.bb.maxX, f2.bb.maxX) - Math.max(f1.bb.minX, f2.bb.minX);
            var overlapY = Math.min(f1.bb.maxY, f2.bb.maxY) - Math.max(f1.bb.minY, f2.bb.minY);
            var overlapZ = Math.min(f1.bb.maxZ, f2.bb.maxZ) - Math.max(f1.bb.minZ, f2.bb.minZ);

            if (overlapX > 0 && overlapY > 0 && overlapZ > 0) {
                var depth = Math.round(Math.min(overlapX, overlapY, overlapZ));
                issues.push({
                    type: "collision",
                    severity: "high",
                    nodes: [f1.label, f2.label],
                    description: f1.label + " and " + f2.label +
                                 " bounding boxes overlap by ~" + depth + " cm",
                    suggestion: "Move one character away to resolve interpenetration"
                });
            }
        }
    }

    // --- 2. Lighting checks ---
    var numLights = Scene.getNumLights();
    var envNode = Scene.getNode(1);
    var envMode = envNode ? envNode.findProperty("Environment Mode") : null;
    var envModeVal = envMode ? envMode.getValue() : 0;
    var hasEnvLight = (envModeVal !== 3);  // not scene-only → env dome contributes

    if (numLights === 0 && !hasEnvLight) {
        issues.push({
            type: "no-lights",
            severity: "high",
            nodes: [],
            description: "Scene has no lights and environment lighting is disabled",
            suggestion: "Use daz_apply_lighting_preset('three-point') to add lights"
        });
    } else if (numLights === 1) {
        warnings.push({
            type: "poor-lighting",
            severity: "medium",
            description: "Scene has only one light source, may cause harsh shadows",
            suggestion: "Add a fill light at low intensity to soften shadows"
        });
    }

    // --- 3. Camera framing check ---
    var numCameras = Scene.getNumCameras();
    if (numCameras === 0) {
        warnings.push({
            type: "no-camera",
            severity: "medium",
            description: "Scene has no cameras (will use default perspective view)",
            suggestion: "Add a camera with daz_execute('var c = new DzBasicCamera(); Scene.addNode(c);')"
        });
    }

    // --- 4. Empty scene check ---
    var numFigures = Scene.getNumSkeletons();
    if (numFigures === 0) {
        warnings.push({
            type: "no-figures",
            severity: "low",
            description: "Scene has no figures/characters",
            suggestion: "Load a character with daz_load_file()"
        });
    }

    // --- Score calculation ---
    var lightScore = 100;
    if (numLights === 0 && !hasEnvLight) lightScore = 0;
    else if (numLights === 1) lightScore = 50;

    var collisionScore = issues.filter(function(i){ return i.type === "collision"; }).length === 0 ? 100 : 30;
    var cameraScore = numCameras > 0 ? 100 : 60;
    var figureScore = numFigures > 0 ? 100 : 60;

    var score = Math.round((lightScore + collisionScore + cameraScore + figureScore) / 4);

    return {
        valid: issues.length === 0,
        issues: issues,
        warnings: warnings,
        score: score,
        score_breakdown: {
            lighting: lightScore,
            collision: collisionScore,
            camera: cameraScore,
            figures: figureScore
        },
        summary: {
            figures: numFigures,
            cameras: numCameras,
            lights: numLights,
            environment_lighting: hasEnvLight
        }
    };
})()
"""

# args: {preset, maxSamples, renderQuality}
# Returns: {preset, propertiesSet: [{property, value}], note}
# Sets Iray render quality via Max Samples and Render Quality properties on the
# active renderer options.  Falls back gracefully if properties are not found.
_SET_RENDER_QUALITY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    if (!renderMgr) throw "No render manager available";

    // getOptionHelper() returns a DzElement (renderer's option node) which has findProperty
    var optHelper = renderMgr.getOptionHelper ? renderMgr.getOptionHelper() : null;

    var targets = ["Max Samples", "Render Quality"];
    var targetValues = {"Max Samples": args.maxSamples, "Render Quality": args.renderQuality};

    var propertiesSet = [];
    var notFound = [];

    for (var i = 0; i < targets.length; i++) {
        var name = targets[i];
        var prop = optHelper ? optHelper.findProperty(name) : null;
        if (prop) {
            prop.setValue(targetValues[name]);
            propertiesSet.push({property: name, value: prop.getValue()});
        } else {
            notFound.push(name);
        }
    }

    var result = {preset: args.preset, propertiesSet: propertiesSet};
    if (notFound.length > 0) {
        result.note = "Properties not found on active renderer option helper: " + notFound.join(", ");
    }
    return result;
})()
"""

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

_SAVE_SCENE_STATE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodes = [];
    var transformKeys = ["XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate", "Scale"];
    var transformSet = {XTranslate:1, YTranslate:1, ZTranslate:1,
                        XRotate:1, YRotate:1, ZRotate:1,
                        Scale:1, XScale:1, YScale:1, ZScale:1};

    function captureTransforms(node) {
        var t = {};
        for (var i = 0; i < transformKeys.length; i++) {
            var p = node.findProperty(transformKeys[i]);
            if (p) t[transformKeys[i]] = p.getValue();
        }
        return t;
    }

    // Skeletons / figures
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var skel = Scene.getSkeleton(i);
        var morphs = [];
        for (var p = 0; p < skel.getNumProperties(); p++) {
            var mp = skel.getProperty(p);
            if (mp.inherits("DzFloatProperty") && !transformSet[mp.getName()]) {
                var v = mp.getValue();
                if (v !== 0) morphs.push({name: mp.getName(), value: v});
            }
        }
        nodes.push({label: skel.getLabel(), type: "skeleton",
                    transforms: captureTransforms(skel), active_morphs: morphs, extra: {}});
    }

    // Cameras
    for (var ci = 0; ci < Scene.getNumCameras(); ci++) {
        var cam = Scene.getCamera(ci);
        nodes.push({label: cam.getLabel(), type: "camera",
                    transforms: captureTransforms(cam), active_morphs: [], extra: {}});
    }

    // Lights
    for (var li = 0; li < Scene.getNumLights(); li++) {
        var light = Scene.getLight(li);
        var extra = {};
        var lightProps = ["Flux", "Shadow Softness", "Spread Angle"];
        for (var lk = 0; lk < lightProps.length; lk++) {
            var lp = light.findProperty(lightProps[lk]);
            if (lp) extra[lightProps[lk]] = lp.getValue();
        }
        nodes.push({label: light.getLabel(), type: "light",
                    transforms: captureTransforms(light), active_morphs: [], extra: extra});
    }

    return {checkpoint: args.checkpointName, nodes: nodes, node_count: nodes.length};
})()
"""

_RESTORE_SCENE_STATE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodes = args.nodes || [];
    var restored = [];
    var errors = [];

    for (var i = 0; i < nodes.length; i++) {
        var nd = nodes[i];
        var node = Scene.findNodeByLabel(nd.label);
        if (!node) { errors.push("Node not found: " + nd.label); continue; }

        // Restore transforms
        var transforms = nd.transforms || {};
        for (var key in transforms) {
            var prop = node.findProperty(key);
            if (prop) prop.setValue(transforms[key]);
        }

        // Restore active morphs
        var morphs = nd.active_morphs || [];
        for (var m = 0; m < morphs.length; m++) {
            var mp = node.findProperty(morphs[m].name);
            if (mp) mp.setValue(morphs[m].value);
        }

        // Restore extra properties (lights)
        var extra = nd.extra || {};
        for (var ek in extra) {
            var ep = node.findProperty(ek);
            if (ep) ep.setValue(extra[ek]);
        }

        restored.push(nd.label);
    }

    return {checkpoint: args.checkpointName, restored: restored, errors: errors};
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

_READ_NODE_CONFIG_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabels = args.nodeLabels || [];    // [] = capture all scene nodes
    var includeTypes = args.includeTypes || ["transforms", "morphs", "lights", "cameras"];

    var captureTransforms = includeTypes.indexOf("transforms") !== -1;
    var captureMorphs     = includeTypes.indexOf("morphs")     !== -1;
    var captureLights     = includeTypes.indexOf("lights")     !== -1;
    var captureCameras    = includeTypes.indexOf("cameras")    !== -1;

    var TRANSFORM_PROPS = [
        "XTranslate", "YTranslate", "ZTranslate",
        "XRotate", "YRotate", "ZRotate",
        "XScale", "YScale", "ZScale", "Scale"
    ];
    var LIGHT_PROPS = ["Flux", "Shadow Softness", "Spread Angle", "Photometric Mode"];
    var CAMERA_PROPS = [
        "FocalLength", "Focal Distance", "Focus Distance",
        "F/Stop", "Depth of Field", "DOF Active"
    ];

    // Resolve node list: explicit labels OR all skeletons+cameras+lights
    var nodesToCapture = [];

    if (nodeLabels.length > 0) {
        for (var i = 0; i < nodeLabels.length; i++) {
            var n = Scene.findNodeByLabel(nodeLabels[i]) || Scene.findNode(nodeLabels[i]);
            if (n) nodesToCapture.push(n);
        }
    } else {
        // Default: all skeletons, cameras, lights
        for (var s = 0; s < Scene.getNumSkeletons(); s++) nodesToCapture.push(Scene.getSkeleton(s));
        for (var c = 0; c < Scene.getNumCameras();   c++) nodesToCapture.push(Scene.getCamera(c));
        for (var l = 0; l < Scene.getNumLights();    l++) nodesToCapture.push(Scene.getLight(l));
    }

    var config = {};
    var summary = {nodes: 0, properties: 0, morphs: 0};

    for (var ni = 0; ni < nodesToCapture.length; ni++) {
        var node = nodesToCapture[ni];
        var label = node.getLabel();
        var nodeData = {_type: node.className()};

        // Transforms
        if (captureTransforms) {
            for (var ti = 0; ti < TRANSFORM_PROPS.length; ti++) {
                var tp = node.findProperty(TRANSFORM_PROPS[ti]);
                if (tp) nodeData[TRANSFORM_PROPS[ti]] = tp.getValue();
            }
        }

        // Light-specific properties
        if (captureLights) {
            for (var li = 0; li < LIGHT_PROPS.length; li++) {
                var lp = node.findProperty(LIGHT_PROPS[li]);
                if (lp) nodeData[LIGHT_PROPS[li]] = lp.getValue();
            }
        }

        // Camera-specific properties
        if (captureCameras) {
            for (var ci = 0; ci < CAMERA_PROPS.length; ci++) {
                var cp = node.findProperty(CAMERA_PROPS[ci]);
                if (cp) nodeData[CAMERA_PROPS[ci]] = cp.getValue();
            }
        }

        // Morphs: non-zero numeric properties not already captured
        if (captureMorphs) {
            var captured = {};
            for (var k in nodeData) captured[k] = true;

            for (var pi = 0; pi < node.getNumProperties(); pi++) {
                var prop = node.getProperty(pi);
                if (!prop.inherits("DzNumericProperty")) continue;
                var pname = prop.getName();
                if (captured[pname]) continue;
                var pval = prop.getValue();
                if (pval !== 0) {
                    nodeData[pname] = pval;
                    summary.morphs++;
                }
            }
        }

        config[label] = nodeData;
        summary.nodes++;
        summary.properties += Object.keys(nodeData).length - 1; // exclude _type
    }

    return {
        config: config,
        summary: summary
    };
})()
"""

_WRITE_NODE_CONFIG_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var config = args.config || {};
    var skipMissing = args.skipMissing !== false;
    var scaleTransforms = args.scaleTransforms !== undefined ? args.scaleTransforms : 1.0;

    var TRANSFORM_PROPS = {
        "XTranslate": true, "YTranslate": true, "ZTranslate": true
    };

    var results = [];
    var successCount = 0;
    var failureCount = 0;
    var skippedCount = 0;

    var nodeLabels = Object.keys(config);

    for (var ni = 0; ni < nodeLabels.length; ni++) {
        var label = nodeLabels[ni];
        var nodeData = config[label];

        var node = Scene.findNodeByLabel(label) || Scene.findNode(label);
        if (!node) {
            if (skipMissing) {
                results.push({node: label, status: "skipped", reason: "not found in scene"});
                skippedCount++;
                continue;
            } else {
                results.push({node: label, status: "error", reason: "not found in scene"});
                failureCount++;
                continue;
            }
        }

        var nodeResult = {node: label, status: "ok", applied: [], failed: []};
        var propNames = Object.keys(nodeData);

        for (var pi = 0; pi < propNames.length; pi++) {
            var pname = propNames[pi];
            if (pname === "_type") continue;

            var pval = nodeData[pname];

            // Scale translation properties if requested
            if (scaleTransforms !== 1.0 && TRANSFORM_PROPS[pname]) {
                pval = pval * scaleTransforms;
            }

            var prop = node.findProperty(pname);
            if (prop) {
                try {
                    prop.setValue(pval);
                    nodeResult.applied.push(pname);
                } catch (e) {
                    nodeResult.failed.push({property: pname, error: String(e)});
                }
            } else {
                nodeResult.failed.push({property: pname, error: "property not found"});
            }
        }

        if (nodeResult.failed.length === 0) {
            successCount++;
        } else if (nodeResult.applied.length > 0) {
            nodeResult.status = "partial";
            successCount++;
        } else {
            nodeResult.status = "error";
            failureCount++;
        }

        results.push(nodeResult);
    }

    return {
        results: results,
        successCount: successCount,
        failureCount: failureCount,
        skippedCount: skippedCount,
        totalNodes: nodeLabels.length
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 4.13: Performance Timing scripts
# ---------------------------------------------------------------------------

_TIME_EXPRESSION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel      = args.nodeLabel;
    var morphList      = args.morphList || [];
    var bodyAdjustments = args.bodyAdjustments || [];
    var intensity      = args.intensity !== undefined ? args.intensity : 0.7;
    var easeInStart    = args.easeInStart;
    var holdStart      = args.holdStart;
    var holdEnd        = args.holdEnd;
    var easeOutEnd     = args.easeOutEnd;
    var baselineFrame  = args.baselineFrame !== undefined ? args.baselineFrame : null;

    var node = Scene.findNodeByLabel(nodeLabel) || Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    var applied = [];
    var notFound = [];
    var keyframesSet = 0;

    // Helper: set a keyframe on a property — two-arg setValue creates a keyframe (DzFloatProperty)
    function setKey(prop, frame, value) {
        prop.setValue(frame, value);
        return true;
    }

    // Process each morph entry — try candidate names in order, first match wins
    for (var i = 0; i < morphList.length; i++) {
        var entry = morphList[i];
        var peakValue = entry.value * intensity;
        var found = false;

        for (var j = 0; j < entry.names.length; j++) {
            var prop = node.findProperty(entry.names[j]);
            if (!prop || !prop.inherits("DzNumericProperty")) continue;

            // Optional baseline keyframe (before ease-in, value=0)
            if (baselineFrame !== null && baselineFrame < easeInStart) {
                setKey(prop, baselineFrame, 0);
                keyframesSet++;
            }

            // Ease-in start: value = 0
            if (setKey(prop, easeInStart, 0)) keyframesSet++;

            // Hold start: peak value
            if (easeInStart < holdStart) {
                if (setKey(prop, holdStart, peakValue)) keyframesSet++;
            } else {
                // No ease-in — jump straight to peak
                if (setKey(prop, easeInStart, peakValue)) keyframesSet++;
            }

            // Hold end: still at peak
            if (holdEnd > holdStart) {
                if (setKey(prop, holdEnd, peakValue)) keyframesSet++;
            }

            // Ease-out end: back to 0
            if (easeOutEnd > holdEnd) {
                if (setKey(prop, easeOutEnd, 0)) keyframesSet++;
            }

            applied.push({morph: entry.names[j], peakValue: peakValue});
            found = true;
            break;
        }

        if (!found) notFound.push(entry.names[0] || "unknown");
    }

    // Process body adjustments (bone rotations)
    var bodyApplied = [];
    for (var k = 0; k < bodyAdjustments.length; k++) {
        var adj = bodyAdjustments[k];
        var peakRot = adj.value * intensity;
        var bone = null;

        for (var b = 0; b < node.getNumNodeChildren(); b++) {
            var child = node.getNodeChild(b);
            if (child && (child.getLabel() === adj.bone || child.getName() === adj.bone)) {
                bone = child;
                break;
            }
        }
        if (!bone) bone = Scene.findNodeByLabel(adj.bone);
        if (!bone) continue;

        var boneProp = bone.findProperty(adj.property);
        if (!boneProp) continue;

        if (baselineFrame !== null && baselineFrame < easeInStart)
            setKey(boneProp, baselineFrame, 0);

        setKey(boneProp, easeInStart, 0);
        setKey(boneProp, holdStart, peakRot);
        if (holdEnd > holdStart) setKey(boneProp, holdEnd, peakRot);
        if (easeOutEnd > holdEnd) setKey(boneProp, easeOutEnd, 0);

        bodyApplied.push({bone: adj.bone, property: adj.property, peakValue: peakRot});
        keyframesSet += 4;
    }

    return {
        character: node.getLabel(),
        easeInStart: easeInStart,
        holdStart: holdStart,
        holdEnd: holdEnd,
        easeOutEnd: easeOutEnd,
        intensity: intensity,
        appliedMorphs: applied,
        bodyAdjustments: bodyApplied,
        notFound: notFound,
        keyframesSet: keyframesSet,
        durationFrames: easeOutEnd - easeInStart,
        holdFrames: holdEnd - holdStart
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Materials / Surfaces
# ---------------------------------------------------------------------------


_GET_MATERIAL_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);
    var obj = node.getObject();
    if (!obj) throw new Error("Node has no geometry: " + args.nodeLabel);
    var shape = obj.getCurrentShape();
    if (!shape) throw new Error("Node has no material shape: " + args.nodeLabel);
    var mat = null;
    for (var i = 0; i < shape.getNumMaterials(); i++) {
        var m = shape.getMaterial(i);
        if (m.getLabel() === args.materialName || m.getName() === args.materialName) {
            mat = m; break;
        }
    }
    if (!mat) throw new Error("Material not found: " + args.materialName);
    function toHex(n) {
        var v = Math.round(n);
        if (v < 0) v = 0;
        if (v > 255) v = 255;
        return ("0" + v.toString(16)).slice(-2);
    }
    function colorChannel(col, name) {
        if (!col) return 0;
        var v = col[name];
        if (typeof v === "function") v = v.call(col);
        return v;
    }
    function colorToHex(col) {
        if (!col) return null;
        var r = colorChannel(col, "red");
        var g = colorChannel(col, "green");
        var b = colorChannel(col, "blue");
        if (r <= 1 && g <= 1 && b <= 1) {
            r *= 255; g *= 255; b *= 255;
        }
        return "#" + toHex(r) + toHex(g) + toHex(b);
    }
    function readColorProp(prop) {
        try {
            if (typeof prop.getFloatColorValue === "function") {
                var fc = prop.getFloatColorValue();
                if (fc && typeof fc.getColor === "function") {
                    var qc = fc.getColor();
                    if (qc) return colorToHex(qc);
                }
                if (fc) return colorToHex(fc);
            }
        } catch (e1) {}
        try {
            if (typeof prop.getColorValue === "function") {
                return colorToHex(prop.getColorValue());
            }
        } catch (e2) {}
        return null;
    }
    var props = [];
    for (var p = 0; p < mat.getNumProperties(); p++) {
        var prop = mat.getProperty(p);
        var entry = { name: prop.getName(), label: prop.getLabel(), type: "unknown", value: null };
        if (prop.inherits("DzColorProperty") || prop.inherits("DzFloatColorProperty")) {
            entry.type = "color";
            entry.value = readColorProp(prop);
        } else if (prop.inherits("DzNumericProperty")) {
            entry.type = "numeric";
            entry.value = prop.getValue();
        } else if (prop.inherits("DzImageProperty")) {
            entry.type = "image";
            try {
                var img = prop.getValue();
                entry.value = img ? img.getFilename() : null;
            } catch(e) { entry.value = null; }
        }
        props.push(entry);
    }
    return {
        node: node.getLabel(),
        material: mat.getLabel(),
        shader: mat.className(),
        property_count: props.length,
        properties: props
    };
})()
"""

_SET_MATERIAL_PROPERTY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);
    var obj = node.getObject();
    if (!obj) throw new Error("Node has no geometry: " + args.nodeLabel);
    var shape = obj.getCurrentShape();
    if (!shape) throw new Error("Node has no material shape: " + args.nodeLabel);
    var mat = null;
    for (var i = 0; i < shape.getNumMaterials(); i++) {
        var m = shape.getMaterial(i);
        if (m.getLabel() === args.materialName || m.getName() === args.materialName) {
            mat = m; break;
        }
    }
    if (!mat) throw new Error("Material not found: " + args.materialName);
    var prop = mat.findProperty(args.propertyName);
    if (!prop) throw new Error("Property not found: " + args.propertyName + " on material " + args.materialName);
    if (prop.inherits("DzColorProperty")) {
        var hex = String(args.value).replace("#", "");
        var r = parseInt(hex.substr(0, 2), 16);
        var g = parseInt(hex.substr(2, 2), 16);
        var b = parseInt(hex.substr(4, 2), 16);
        prop.setColorValue(new QColor(r, g, b));
        return {
            node: node.getLabel(), material: mat.getLabel(),
            property: prop.getLabel(), type: "color", value: args.value
        };
    } else if (prop.inherits("DzNumericProperty")) {
        prop.setValue(parseFloat(args.value));
        return {
            node: node.getLabel(), material: mat.getLabel(),
            property: prop.getLabel(), type: "numeric", value: prop.getValue()
        };
    } else {
        throw new Error(
            "Property '" + args.propertyName + "' is not a settable color or numeric property"
        );
    }
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Direct morph setting
# ---------------------------------------------------------------------------

_SET_MORPH_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var node = resolveNode(args.nodeLabel);
    var search = (args.morphName || "").toLowerCase();
    var channels = [];
    function addChannel(p) {
        if (p && p.inherits("DzNumericProperty")) channels.push(p);
    }
    var i, p, obj, m, j;
    for (i = 0; i < node.getNumProperties(); i++) addChannel(node.getProperty(i));
    obj = (typeof node.getObject === "function") ? node.getObject() : null;
    if (obj && typeof obj.getNumModifiers === "function") {
        for (i = 0; i < obj.getNumModifiers(); i++) {
            m = obj.getModifier(i);
            if (!m) continue;
            if (typeof m.getValueChannel === "function") addChannel(m.getValueChannel());
            if (typeof m.getNumProperties === "function") {
                for (j = 0; j < m.getNumProperties(); j++) addChannel(m.getProperty(j));
            }
        }
    }
    var prop = null;
    for (i = 0; i < channels.length; i++) {
        p = channels[i];
        if (p.getLabel().toLowerCase() === search || p.getName().toLowerCase() === search) {
            prop = p; break;
        }
    }
    if (!prop) {
        for (i = 0; i < channels.length; i++) {
            p = channels[i];
            if (p.getLabel().toLowerCase().indexOf(search) !== -1 ||
                p.getName().toLowerCase().indexOf(search) !== -1) {
                prop = p; break;
            }
        }
    }
    if (!prop) throw new Error("Morph not found: " + args.morphName);
    if (typeof prop.lock === "function" && prop.isLocked && prop.isLocked()) prop.lock(false);
    prop.setValue(args.value);
    return {
        node: node.getLabel(),
        morph: prop.getLabel(),
        internal_name: prop.getName(),
        value: prop.getValue()
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Node lifecycle
# ---------------------------------------------------------------------------

_DELETE_NODE_SCRIPT = "(function(){\n" + _RESOLVE_NODE_JS + """
    var args = getArguments()[0] || {};
    var node = resolveNode(args.nodeLabel);
    var label = node.getLabel();
    var childCount = node.getNumNodeChildren();
    Scene.removeNode(node);
    return { deleted: label, child_count: childCount };
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Light management
# ---------------------------------------------------------------------------

_LIST_LIGHTS_SCRIPT = """\
(function(){
    var lights = [];
    for (var i = 0; i < Scene.getNumLights(); i++) {
        var l = Scene.getLight(i);
        var pos = l.getWSPos();
        var fluxProp = l.findProperty("Flux");
        var visibleProp = l.findProperty("Visible");
        lights.push({
            index: i,
            label: l.getLabel(),
            name: l.getName(),
            type: l.className(),
            position: {
                x: Math.round(pos.x * 100) / 100,
                y: Math.round(pos.y * 100) / 100,
                z: Math.round(pos.z * 100) / 100
            },
            flux: fluxProp ? Math.round(fluxProp.getValue()) : null,
            enabled: visibleProp ? (visibleProp.getValue() !== 0) : true
        });
    }
    return { light_count: lights.length, lights: lights };
})()
"""

_CREATE_LIGHT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var t = (args.lightType || "spot").toLowerCase();
    var light;
    if (t === "distant") {
        light = new DzDistantLight();
    } else if (t === "point") {
        light = new DzPointLight();
    } else {
        light = new DzSpotLight();
        t = "spot";
    }
    light.setLabel(args.label || (t + "_light"));
    Scene.addNode(light);
    // See _CREATE_CAMERA_SCRIPT for why this is needed: a script-created node's
    // internal name is empty until set explicitly, and daz_list_lights (via
    // dazpy) resolves nodes by that name.
    var baseName = String(args.label || (t + "_light")).replace(/[^A-Za-z0-9_]/g, "_") || "Light";
    var candidateName = baseName, nameSuffix = 1;
    while (Scene.findNode(candidateName)) {
        candidateName = baseName + "_" + (++nameSuffix);
    }
    light.setName(candidateName);
    var xp = light.findProperty("XTranslate");
    var yp = light.findProperty("YTranslate");
    var zp = light.findProperty("ZTranslate");
    if (xp) xp.setValue(args.x !== undefined ? args.x : 0);
    if (yp) yp.setValue(args.y !== undefined ? args.y : 200);
    if (zp) zp.setValue(args.z !== undefined ? args.z : 200);
    if (args.flux !== undefined && args.flux !== null) {
        var fp = light.findProperty("Flux");
        if (fp) fp.setValue(args.flux);
    }
    if (args.aimAtLabel) {
        var target = Scene.findNodeByLabel(args.aimAtLabel);
        if (!target) target = Scene.findNode(args.aimAtLabel);
        if (target) {
            var bbox = target.getWSBoundingBox();
            var cx = (bbox.minX + bbox.maxX) / 2;
            var cy = (bbox.minY + bbox.maxY) / 2;
            var cz = (bbox.minZ + bbox.maxZ) / 2;
            light.aimAt(new DzVec3(cx, cy, cz));
        }
    }
    var pos = light.getWSPos();
    var fp2 = light.findProperty("Flux");
    return {
        label: light.getLabel(),
        type: t,
        position: { x: pos.x, y: pos.y, z: pos.z },
        flux: fp2 ? fp2.getValue() : null
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Camera management
# ---------------------------------------------------------------------------

_LIST_CAMERAS_SCRIPT = """\
(function(){
    var cameras = [];
    for (var i = 0; i < Scene.getNumCameras(); i++) {
        var c = Scene.getCamera(i);
        var pos = c.getWSPos();
        var focalProp = c.getFocalLengthControl();
        cameras.push({
            index: i,
            label: c.getLabel(),
            name: c.getName(),
            type: c.className(),
            position: {
                x: Math.round(pos.x * 100) / 100,
                y: Math.round(pos.y * 100) / 100,
                z: Math.round(pos.z * 100) / 100
            },
            focal_length: focalProp ? Math.round(focalProp.getValue() * 10) / 10 : null
        });
    }
    return { camera_count: cameras.length, cameras: cameras };
})()
"""

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


_SET_RENDER_OUTPUT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();
    var changed = {};
    if (args.outputPath) {
        opts.renderImgFilename = args.outputPath;
        opts.renderImgToId = opts.DirectToFile;
        changed.output_path = args.outputPath;
    }
    if ((args.width !== undefined && args.width !== null) ||
        (args.height !== undefined && args.height !== null)) {
        var sz = opts.imageSize;
        var w = (args.width !== undefined && args.width !== null) ? args.width : sz.width;
        var h = (args.height !== undefined && args.height !== null) ? args.height : sz.height;
        opts.imageSize = new QSize(w, h);
        if (args.width !== undefined && args.width !== null) changed.width = args.width;
        if (args.height !== undefined && args.height !== null) changed.height = args.height;
    }
    opts.applyChanges();
    var cur = opts.imageSize;
    return {
        changed: changed,
        current: {
            output_path: opts.renderImgFilename || null,
            width: cur ? cur.width : null,
            height: cur ? cur.height : null
        }
    };
})()
"""

# args: {engine}
# Returns: {success, engine, renderType, renderTypeName, activeRenderer,
#           activeRendererClass, warning?}
# DS6 Engine dropdown is DzRenderOptions.renderType, not getActiveRenderer().
_SET_RENDER_ENGINE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var requested = String(args.engine || "").toLowerCase().replace(/-/g, "_").replace(/ /g, "_");
    if (requested === "opengl" || requested === "hardware" || requested === "hardware_assisted") {
        requested = "multi_pass_opengl";
    }
    if (requested === "nvidia_iray" || requested === "nvidia_iray_mdl" || requested === "software") {
        requested = "iray";
    }
    if (requested !== "iray" && requested !== "multi_pass_opengl" && requested !== "viewport") {
        throw new Error("Unknown render engine: " + args.engine + ". Use iray, multi_pass_opengl, or viewport.");
    }

    var mgr = App.getRenderMgr();
    var opts = mgr.getRenderOptions();
    if (requested === "viewport") {
        opts.renderType = opts.ScreenShot;
    } else if (requested === "multi_pass_opengl") {
        opts.renderType = opts.HardwareAssisted;
    } else {
        var iray = mgr.findRenderer("DzIrayRenderer");
        if (!iray) throw new Error("DzIrayRenderer is not registered");
        mgr.setActiveRenderer(iray);
        opts.renderType = opts.Software;
    }
    opts.applyChanges();
    try {
        var pane = MainWindow.getPaneMgr().findPane("DzRenderSettingsPane");
        if (pane && pane.refresh) pane.refresh();
    } catch (e) {}

    var renderType = Number(opts.renderType);
    var engine = requested;
    var renderTypeName = renderType === Number(opts.ScreenShot) ? "ScreenShot"
        : renderType === Number(opts.HardwareAssisted) ? "HardwareAssisted"
        : renderType === Number(opts.Software) ? "Software" : null;
    var expected = requested === "viewport" ? Number(opts.ScreenShot)
        : requested === "multi_pass_opengl" ? Number(opts.HardwareAssisted)
        : Number(opts.Software);
    if (renderType !== expected) {
        throw new Error("Render engine readback mismatch: wanted " + requested + " got renderType " + renderType);
    }
    var active = mgr.getActiveRenderer();
    var result = {
        success: true,
        engine: engine,
        renderType: renderType,
        renderTypeName: renderTypeName,
        activeRenderer: active ? active.getName() : null,
        activeRendererClass: active ? active.className() : null
    };
    if (engine === "viewport") {
        result.warning = "Engine Viewport opens a filename dialog unless DirectToFile + output path are set.";
    }
    return result;
})()
"""

# ---------------------------------------------------------------------------
# Phase 5: Pose reset
# ---------------------------------------------------------------------------

_RESET_POSE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);
    var bonesReset = 0;
    function resetRotations(n) {
        var rx = n.findProperty("XRotate");
        var ry = n.findProperty("YRotate");
        var rz = n.findProperty("ZRotate");
        if (rx) { rx.setValue(0); bonesReset++; }
        if (ry) ry.setValue(0);
        if (rz) rz.setValue(0);
        for (var i = 0; i < n.getNumNodeChildren(); i++) {
            resetRotations(n.getNodeChild(i));
        }
    }
    resetRotations(node);
    if (args.zeroTransforms) {
        var xt = node.findProperty("XTranslate");
        var yt = node.findProperty("YTranslate");
        var zt = node.findProperty("ZTranslate");
        var sc = node.findProperty("Scale");
        if (xt) xt.setValue(0);
        if (yt) yt.setValue(0);
        if (zt) zt.setValue(0);
        if (sc) sc.setValue(1);
    }
    return {
        node: node.getLabel(),
        bones_reset: bonesReset,
        transforms_zeroed: args.zeroTransforms === true
    };
})()
"""

_LIST_FITTED_ITEMS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var fig = Scene.findNodeByLabel(args.figureLabel);
    if (!fig) fig = Scene.findNode(args.figureLabel);
    if (!fig) throw new Error("Figure not found: " + args.figureLabel);

    var fitted = [];
    var numNodes = Scene.getNumNodes();
    for (var i = 0; i < numNodes; i++) {
        var node = Scene.getNode(i);
        if (!node || node === fig) continue;
        // Skip the figure's own skeleton (e.g. the Hip root bone is parented to the figure)
        if (typeof node.inherits === 'function' && node.inherits("DzBone")) continue;

        var isFitted = false;
        var itemType = "prop";

        // Figure-based clothing/hair: it has a follow target pointing at our figure
        if (typeof node.getFollowTarget === 'function') {
            var ft = node.getFollowTarget();
            if (ft && ft.elementID === fig.elementID) {
                isFitted = true;
                itemType = node.inherits("DzHair") ? "hair" : "clothing";
            }
        }

        // Props/accessories: directly parented to the figure node
        if (!isFitted && typeof node.getNodeParent === 'function') {
            var parent = node.getNodeParent();
            if (parent && parent.elementID === fig.elementID) {
                isFitted = true;
                itemType = node.inherits("DzHair") ? "hair" : "prop";
            }
        }

        if (isFitted) {
            fitted.push({
                label: node.getLabel(),
                name: node.getName(),
                type: itemType,
                element_id: node.elementID
            });
        }
    }

    return {
        figure: fig.getLabel(),
        fitted_count: fitted.length,
        fitted_items: fitted
    };
})()
"""

_FIT_CLOTHING_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var clothing = Scene.findNodeByLabel(args.clothingLabel);
    if (!clothing) clothing = Scene.findNode(args.clothingLabel);
    if (!clothing) throw new Error("Clothing node not found: " + args.clothingLabel);

    var figure = Scene.findNodeByLabel(args.figureLabel);
    if (!figure) figure = Scene.findNode(args.figureLabel);
    if (!figure) throw new Error("Figure not found: " + args.figureLabel);

    var method;
    if (typeof clothing.setFollowTarget === 'function') {
        clothing.setFollowTarget(figure);
        method = "setFollowTarget";
    } else if (typeof clothing.followSkeleton === 'function') {
        clothing.followSkeleton(figure);
        method = "followSkeleton";
    } else {
        // Fallback: parent the item to the figure preserving world position
        figure.addNodeChild(clothing, true);
        method = "addNodeChild";
    }

    return {
        success: true,
        clothing: clothing.getLabel(),
        figure: figure.getLabel(),
        method: method
    };
})()
"""

_UNFIT_ITEM_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var item = Scene.findNodeByLabel(args.itemLabel);
    if (!item) item = Scene.findNode(args.itemLabel);
    if (!item) throw new Error("Item not found: " + args.itemLabel);

    var prevFigureLabel = null;
    var methods = [];

    // Remove follow target if one exists
    if (typeof item.getFollowTarget === 'function') {
        var ft = item.getFollowTarget();
        if (ft) {
            prevFigureLabel = ft.getLabel();
            if (typeof item.setFollowTarget === 'function') {
                item.setFollowTarget(null);
                methods.push("cleared follow target");
            }
        }
    }

    // Detach from parent figure (props parented directly)
    if (typeof item.getNodeParent === 'function') {
        var parent = item.getNodeParent();
        if (parent && parent.inherits && parent.inherits("DzSkeleton")) {
            prevFigureLabel = prevFigureLabel || parent.getLabel();
            parent.removeNodeChild(item, true);  // true = inPlace: preserve world position
            methods.push("detached from parent");
        }
    }

    return {
        success: true,
        item: item.getLabel(),
        previous_figure: prevFigureLabel,
        actions: methods.length ? methods : ["no fitting relationship found"]
    };
})()
"""

_RUN_DFORCE_SIMULATION_SCRIPT = """\
(function(){
    // NOTE (Bug 21): DzSimulationMgr.simulate()'s DzTimeRange argument does
    // NOT control how much is actually simulated -- verified live: calling
    // with a 0-frame range and a 30-frame range produced bit-identical
    // results, and pre-setting Scene.setAnimRange() to a 1-frame window
    // first made no difference either. The actual duration is governed by
    // DAZ Studio's own Simulation Settings > Duration panel, which has no
    // known scripting entry point. Do not reintroduce start/end frame
    // parameters here without a verified way to make them do something.
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;

    if (nodeLabel) {
        var node = Scene.findNodeByLabel(nodeLabel);
        if (!node) node = Scene.findNode(nodeLabel);
        if (!node) throw new Error("Node not found: " + nodeLabel);
        Scene.clearSelection();
        Scene.selectNode(node);
    }

    var simMgr = App.getSimulationMgr ? App.getSimulationMgr() : null;
    if (!simMgr) throw new Error("DzSimulationMgr not available via App.getSimulationMgr()");

    if (typeof simMgr.simulate === 'function') {
        var animRange = Scene.getAnimRange();
        simMgr.simulate(new DzTimeRange(animRange.start, animRange.end));
    } else {
        var methods = [];
        for (var k in simMgr) { if (typeof simMgr[k] === 'function') methods.push(k); }
        throw new Error("simulate() not found on DzSimulationMgr. Available: " + methods.join(", "));
    }

    return {
        success: true,
        node: nodeLabel || "all simulatable nodes"
    };
})()
"""

_BAKE_SIMULATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;

    if (nodeLabel) {
        var node = Scene.findNodeByLabel(nodeLabel);
        if (!node) node = Scene.findNode(nodeLabel);
        if (!node) throw new Error("Node not found: " + nodeLabel);
        Scene.clearSelection();
        Scene.selectNode(node);
    }

    var simMgr = App.getSimulationMgr ? App.getSimulationMgr() : null;
    if (!simMgr) throw new Error("DzSimulationMgr not available via App.getSimulationMgr()");

    var bakeMethod = null;
    if (typeof simMgr.bakeSimulation === 'function') {
        simMgr.bakeSimulation();
        bakeMethod = "bakeSimulation";
    } else if (typeof simMgr.freezeSimulation === 'function') {
        simMgr.freezeSimulation();
        bakeMethod = "freezeSimulation";
    } else if (typeof simMgr.bakeCurrentPose === 'function') {
        simMgr.bakeCurrentPose();
        bakeMethod = "bakeCurrentPose";
    } else {
        var methods = [];
        for (var k in simMgr) { if (typeof simMgr[k] === 'function') methods.push(k); }
        throw new Error("No bake method found on DzSimulationMgr. Available: " + methods.join(", "));
    }

    return {
        success: true,
        node: nodeLabel || "all",
        method: bakeMethod
    };
})()
"""

_SET_DFORCE_PROPERTY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;
    var propertyName = args.propertyName;
    var value = parseFloat(args.value);

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    function isDforceMod(mod) {
        if (!mod) return false;
        var cn = (mod.className ? mod.className() : "").toLowerCase();
        if (cn.indexOf("dforce") !== -1 || cn.indexOf("dynamics") !== -1) return true;
        if (typeof mod.findProperty === "function") {
            if (mod.findProperty("Freeze Simulation") || mod.findProperty("Dynamics Strength")) return true;
        }
        return false;
    }
    function searchMods(host) {
        if (!host || typeof host.getNumModifiers !== "function") return null;
        for (var i = 0; i < host.getNumModifiers(); i++) {
            var mod = host.getModifier(i);
            if (isDforceMod(mod)) return mod;
        }
        return null;
    }
    var obj = (typeof node.getObject === "function") ? node.getObject() : null;
    var shape = obj && obj.getCurrentShape ? obj.getCurrentShape() : null;
    var modifier = searchMods(node) || searchMods(obj) || searchMods(shape);

    if (!modifier) {
        var nodeModNames = [];
        function collectMods(host, prefix) {
            if (!host || typeof host.getNumModifiers !== "function") return;
            for (var nm = 0; nm < host.getNumModifiers(); nm++) {
                var m = host.getModifier(nm);
                nodeModNames.push(prefix + (m && m.className ? m.className() : "unknown"));
            }
        }
        collectMods(node, "node:");
        collectMods(obj, "obj:");
        collectMods(shape, "shape:");
        throw new Error("No dForce modifier found on '" + nodeLabel + "'. Node modifiers: [" + nodeModNames.join(", ") + "]");
    }

    // Find property: exact name first, then case-insensitive
    var prop = typeof modifier.findProperty === 'function' ? modifier.findProperty(propertyName) : null;
    if (!prop) {
        var propCount = typeof modifier.getNumProperties === 'function' ? modifier.getNumProperties() : 0;
        for (var p = 0; p < propCount; p++) {
            var mp = modifier.getProperty(p);
            if (mp && mp.getName().toLowerCase() === propertyName.toLowerCase()) {
                prop = mp;
                break;
            }
        }
    }

    if (!prop) {
        var available = [];
        var propCount2 = typeof modifier.getNumProperties === 'function' ? modifier.getNumProperties() : 0;
        for (var p2 = 0; p2 < propCount2; p2++) {
            var mp2 = modifier.getProperty(p2);
            if (mp2) available.push(mp2.getName());
        }
        throw new Error("Property '" + propertyName + "' not found on dForce modifier. Available: " + available.join(", "));
    }

    var oldValue = typeof prop.getValue === 'function' ? prop.getValue() : null;
    if (typeof prop.setDoubleValue === 'function') {
        prop.setDoubleValue(value);
    } else if (typeof prop.setValue === 'function') {
        prop.setValue(value);
    }

    return {
        success: true,
        node: node.getLabel(),
        modifier: modifier.className ? modifier.className() : "unknown",
        property: prop.getName(),
        old_value: oldValue,
        new_value: value
    };
})()
"""

_RUN_TRANSFER_UTILITY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var sourceLabel = args.sourceLabel;
    var targetLabel = args.targetLabel;

    var source = Scene.findNodeByLabel(sourceLabel);
    if (!source) source = Scene.findNode(sourceLabel);
    if (!source) throw new Error("Source node not found: " + sourceLabel);

    var target = Scene.findNodeByLabel(targetLabel);
    if (!target) target = Scene.findNode(targetLabel);
    if (!target) throw new Error("Target node not found: " + targetLabel);

    var tu = new DzTransferUtility();
    tu.setSilentImporters(true);
    tu.setSource(source);
    tu.setTarget(target);
    tu.setTransferBinding(!!args.transferBinding);
    tu.setTransferMorphs(!!args.transferMorphs);
    tu.setTransferUVs(!!args.transferUVs);
    tu.setTransferMaterialGroups(!!args.transferMaterialGroups);
    tu.setTransferFaceGroups(!!args.transferFaceGroups);
    tu.setFitToFigure(!!args.fitToFigure);
    tu.setParentToFigure(!!args.parentToFigure);
    tu.setMergeHierarchies(!!args.mergeHierarchies);

    var ok = tu.doTransfer();
    if (!ok) {
        throw new Error("DzTransferUtility.doTransfer() returned false (source: '" +
            sourceLabel + "', target: '" + targetLabel + "')");
    }

    return {
        success: true,
        source: source.getLabel(),
        target: target.getLabel()
    };
})()
"""

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

_GET_DFORCE_SURFACE_PROPERTIES_SCRIPT = "(function(){\n" + _RESOLVE_DFORCE_PROVIDER_JS + """
    var args = getArguments()[0] || {};
    var resolved = resolveDforceProvider(args.nodeLabel, args.materialName);
    var provider = resolved.provider;

    var props = [];
    for (var p = 0; p < provider.getNumProperties(); p++) {
        var prop = provider.getProperty(p);
        var entry = { name: prop.getName(), label: prop.getLabel(), type: "unknown", value: null };
        if (prop.inherits("DzNumericProperty")) {
            entry.type = "numeric";
            entry.value = prop.getValue();
        }
        props.push(entry);
    }

    return {
        node: resolved.node.getLabel(),
        material: resolved.materialName,
        property_count: props.length,
        properties: props
    };
})()
"""

_SET_DFORCE_SURFACE_PROPERTY_SCRIPT = "(function(){\n" + _RESOLVE_DFORCE_PROVIDER_JS + """
    var args = getArguments()[0] || {};
    var resolved = resolveDforceProvider(args.nodeLabel, args.materialName);
    var provider = resolved.provider;

    var prop = provider.findProperty(args.propertyName);
    if (!prop) {
        var available = [];
        for (var p = 0; p < provider.getNumProperties(); p++) {
            available.push(provider.getProperty(p).getName());
        }
        throw new Error("Property '" + args.propertyName + "' not found on dForce surface '" +
            resolved.materialName + "'. Available: " + available.join(", "));
    }
    if (!prop.inherits("DzNumericProperty")) {
        throw new Error("Property '" + args.propertyName + "' is not a settable numeric property");
    }

    var oldValue = prop.getValue();
    prop.setValue(parseFloat(args.value));

    return {
        success: true,
        node: resolved.node.getLabel(),
        material: resolved.materialName,
        property: prop.getName(),
        old_value: oldValue,
        new_value: prop.getValue()
    };
})()
"""

_ADD_DFORCE_DYNAMIC_SURFACE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    function hasDforceModifier(host) {
        if (!host || typeof host.getNumModifiers !== 'function') return false;
        for (var i = 0; i < host.getNumModifiers(); i++) {
            var mod = host.getModifier(i);
            if (mod.className && mod.className() === "DzDForceModifier") return true;
        }
        return false;
    }

    var obj = (typeof node.getObject === "function") ? node.getObject() : null;
    if (hasDforceModifier(node) || hasDforceModifier(obj)) {
        return {
            success: true,
            node: node.getLabel(),
            already_present: true,
            modifier: "DzDForceModifier"
        };
    }

    var mgr = MainWindow.getActionMgr();
    var act = mgr.findAction("DzAddDForceModifierDynamicSurfaceAction");
    if (!act) throw new Error("Action 'DzAddDForceModifierDynamicSurfaceAction' not found in DzActionMgr");

    Scene.selectAllNodes(false);
    node.select(true);
    act.trigger();

    obj = (typeof node.getObject === "function") ? node.getObject() : null;
    if (!hasDforceModifier(node) && !hasDforceModifier(obj)) {
        throw new Error("Action triggered but no DzDForceModifier found on '" + nodeLabel + "' afterward");
    }

    return {
        success: true,
        node: node.getLabel(),
        already_present: false,
        modifier: "DzDForceModifier"
    };
})()
"""

_SET_DFORCE_INFLUENCE_WEIGHTS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;
    var defaultWeight = args.defaultWeight !== undefined ? parseFloat(args.defaultWeight) : 1.0;
    var overrides = args.vertexWeights || {};

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    function isDforceMod(mod) {
        if (!mod) return false;
        var cn = (mod.className ? mod.className() : "").toLowerCase();
        if (cn.indexOf("dforce") !== -1 || cn.indexOf("dynamics") !== -1) return true;
        if (typeof mod.findProperty === "function") {
            if (mod.findProperty("Freeze Simulation") || mod.findProperty("Dynamics Strength")) return true;
        }
        return false;
    }
    function searchMods(host) {
        if (!host || typeof host.getNumModifiers !== "function") return null;
        for (var i = 0; i < host.getNumModifiers(); i++) {
            var mod = host.getModifier(i);
            if (isDforceMod(mod)) return mod;
        }
        return null;
    }
    var obj = (typeof node.getObject === "function") ? node.getObject() : null;
    var shape = obj && obj.getCurrentShape ? obj.getCurrentShape() : null;
    var modifier = searchMods(node) || searchMods(obj) || searchMods(shape);
    if (!modifier) {
        throw new Error("No dForce modifier found on '" + nodeLabel + "'. Add one first with daz_add_dforce_dynamic_surface.");
    }

    // The dForce simulation vertex count (modifier.getTargetVertexCount()) is NOT
    // the same as the node's rendered/subdivided vertex count (getCachedGeom() —
    // confirmed live to differ, e.g. 3401 vs 13456 on the same node). Weight maps
    // must be sized to the simulation resolution, or setInfluenceWeights() silently
    // replaces any existing (correctly-sized) map with a wrong-sized one.
    var numVerts = modifier.getTargetVertexCount();
    if (!numVerts) {
        var existing = modifier.getInfluenceWeights();
        numVerts = existing ? existing.getNumWeights() : 0;
    }
    if (!numVerts) {
        throw new Error(
            "Could not determine dForce simulation vertex count for '" + nodeLabel +
            "' (modifier.getTargetVertexCount() returned 0 and no existing influence " +
            "weights to infer it from). Run a dForce simulation on this node at least " +
            "once first, then retry."
        );
    }

    var wm = new DzWeightMap();
    wm.setNumWeights(numVerts);
    for (var i = 0; i < numVerts; i++) {
        wm.setFloatWeight(i, defaultWeight);
    }

    var overriddenCount = 0;
    for (var key in overrides) {
        var idx = parseInt(key, 10);
        if (isNaN(idx) || idx < 0 || idx >= numVerts) continue;
        wm.setFloatWeight(idx, parseFloat(overrides[key]));
        overriddenCount++;
    }

    modifier.setInfluenceWeights(wm);

    return {
        success: true,
        node: node.getLabel(),
        vertex_count: numVerts,
        default_weight: defaultWeight,
        overridden_count: overriddenCount
    };
})()
"""

_GET_DFORCE_INFLUENCE_WEIGHTS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    function isDforceMod(mod) {
        if (!mod) return false;
        var cn = (mod.className ? mod.className() : "").toLowerCase();
        if (cn.indexOf("dforce") !== -1 || cn.indexOf("dynamics") !== -1) return true;
        if (typeof mod.findProperty === "function") {
            if (mod.findProperty("Freeze Simulation") || mod.findProperty("Dynamics Strength")) return true;
        }
        return false;
    }
    function searchMods(host) {
        if (!host || typeof host.getNumModifiers !== "function") return null;
        for (var i = 0; i < host.getNumModifiers(); i++) {
            var mod = host.getModifier(i);
            if (isDforceMod(mod)) return mod;
        }
        return null;
    }
    var obj = (typeof node.getObject === "function") ? node.getObject() : null;
    var shape = obj && obj.getCurrentShape ? obj.getCurrentShape() : null;
    var modifier = searchMods(node) || searchMods(obj) || searchMods(shape);
    if (!modifier) {
        throw new Error("No dForce modifier found on '" + nodeLabel + "'. Add one first with daz_add_dforce_dynamic_surface.");
    }

    var wm = modifier.getInfluenceWeights();
    if (!wm) {
        return {
            success: true,
            node: node.getLabel(),
            has_influence_weights: false,
            weights: []
        };
    }

    var n = wm.getNumWeights();
    var weights = [];
    for (var i = 0; i < n; i++) weights.push(wm.getFloatWeight(i));

    return {
        success: true,
        node: node.getLabel(),
        has_influence_weights: true,
        vertex_count: n,
        weights: weights
    };
})()
"""


# ---------------------------------------------------------------------------
# Phase 6.4: Material preset scripts
# ---------------------------------------------------------------------------

_APPLY_MATERIAL_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;
    var presetPath = args.presetPath;

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    // Select only the target node so the preset applies to it. Node
    // selection alone is NOT sufficient - Material/Shader Preset application
    // acts on the currently-selected SURFACE(S), not just the selected node;
    // without also selecting every material zone, openFile() below returns
    // true (no error) but silently applies nothing (confirmed live while
    // fixing the identical bug in _CONVERT_TO_IRAY_UBER_SCRIPT).
    Scene.selectAllNodes(false);
    node.select(true);
    var objForSelect = typeof node.getObject === 'function' ? node.getObject() : null;
    var shapeForSelect = objForSelect && typeof objForSelect.getCurrentShape === 'function' ? objForSelect.getCurrentShape() : null;
    if (shapeForSelect) {
        for (var s = 0; s < shapeForSelect.getNumMaterials(); s++) {
            shapeForSelect.getMaterial(s).select(true);
        }
    }

    var mapPaths = args.mapPaths || [];
    var allowMissing = args.allowMissing === true;
    var missing = [];
    var mi, rel, absPath, info;
    for (mi = 0; mi < mapPaths.length; mi++) {
        rel = mapPaths[mi];
        if (!rel) continue;
        info = new DzFileInfo(rel);
        if (info && typeof info.exists === "function" && info.exists()) continue;
        absPath = App.getContentMgr().getAbsolutePath(rel, true, "");
        if (absPath) {
            info = new DzFileInfo(absPath);
            if (info && typeof info.exists === "function" && info.exists()) continue;
        }
        missing.push(rel);
    }
    if (missing.length && !allowMissing) {
        throw new Error("Missing texture files (refusing openFile to avoid Missing Files dialog): " + missing.join(", "));
    }

    var ioSettings = new DzFileIOSettings();
    var ok = App.getContentMgr().openFile(presetPath, ioSettings, false);
    if (!ok) throw new Error("Failed to apply material preset. Check that the path exists and is a valid .duf material file: " + presetPath);

    // Collect resulting material names for confirmation. Materials live on
    // the shape, not the object directly - DzObject has no getNumMaterials()
    // of its own (see daz://guide/dazscript "Materials - always go through
    // getCurrentShape()"). Calling it on the bare object throws and was
    // silently discarding a *successful* preset application, since the
    // openFile() call above had already completed by this point.
    var obj = typeof node.getObject === 'function' ? node.getObject() : null;
    var shape = obj && typeof obj.getCurrentShape === 'function' ? obj.getCurrentShape() : null;
    var matNames = [];
    if (shape) {
        for (var i = 0; i < shape.getNumMaterials(); i++) {
            var mat = shape.getMaterial(i);
            if (mat) matNames.push(mat.getLabel());
        }
    }

    return {
        success: true,
        node: node.getLabel(),
        preset: presetPath,
        materials: matNames,
        material_count: matNames.length
    };
})()
"""

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

_COPY_MATERIAL_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var srcNodeLabel = args.sourceNodeLabel;
    var srcMatName = args.sourceMaterialName;
    var dstNodeLabel = args.destNodeLabel;
    var dstMatName = args.destMaterialName;

    // Resolve source node + material
    var srcNode = Scene.findNodeByLabel(srcNodeLabel);
    if (!srcNode) srcNode = Scene.findNode(srcNodeLabel);
    if (!srcNode) throw new Error("Source node not found: " + srcNodeLabel);

    var srcObj = typeof srcNode.getObject === 'function' ? srcNode.getObject() : null;
    var srcShape = srcObj && typeof srcObj.getCurrentShape === 'function' ? srcObj.getCurrentShape() : null;
    if (!srcShape) throw new Error("Source node has no material shape: " + srcNodeLabel);

    var srcMat = null;
    for (var i = 0; i < srcShape.getNumMaterials(); i++) {
        var m = srcShape.getMaterial(i);
        if (m && (m.getLabel() === srcMatName || m.getName() === srcMatName)) {
            srcMat = m;
            break;
        }
    }
    if (!srcMat) {
        var srcNames = [];
        for (var ii = 0; ii < srcShape.getNumMaterials(); ii++) {
            var mm = srcShape.getMaterial(ii);
            if (mm) srcNames.push(mm.getLabel());
        }
        throw new Error("Material '" + srcMatName + "' not found on " + srcNodeLabel + ". Available: " + srcNames.join(", "));
    }

    // Resolve dest node + material
    var dstNode = Scene.findNodeByLabel(dstNodeLabel);
    if (!dstNode) dstNode = Scene.findNode(dstNodeLabel);
    if (!dstNode) throw new Error("Dest node not found: " + dstNodeLabel);

    var dstObj = typeof dstNode.getObject === 'function' ? dstNode.getObject() : null;
    var dstShape = dstObj && typeof dstObj.getCurrentShape === 'function' ? dstObj.getCurrentShape() : null;
    if (!dstShape) throw new Error("Dest node has no material shape: " + dstNodeLabel);

    var dstMat = null;
    for (var j = 0; j < dstShape.getNumMaterials(); j++) {
        var n = dstShape.getMaterial(j);
        if (n && (n.getLabel() === dstMatName || n.getName() === dstMatName)) {
            dstMat = n;
            break;
        }
    }
    if (!dstMat) {
        var dstNames = [];
        for (var jj = 0; jj < dstShape.getNumMaterials(); jj++) {
            var nn = dstShape.getMaterial(jj);
            if (nn) dstNames.push(nn.getLabel());
        }
        throw new Error("Material '" + dstMatName + "' not found on " + dstNodeLabel + ". Available: " + dstNames.join(", "));
    }

    // Copy properties from source to destination
    var copied = 0;
    var skipped = 0;
    for (var p = 0; p < srcMat.getNumProperties(); p++) {
        var srcProp = srcMat.getProperty(p);
        if (!srcProp) continue;
        var dstProp = dstMat.findProperty(srcProp.getName());
        if (!dstProp) { skipped++; continue; }
        try {
            if (typeof srcProp.getValue === 'function' && typeof dstProp.setValue === 'function') {
                dstProp.setValue(srcProp.getValue());
                copied++;
            } else {
                skipped++;
            }
        } catch(e) {
            skipped++;
        }
    }

    return {
        success: true,
        source: srcNodeLabel + "/" + srcMat.getLabel(),
        destination: dstNodeLabel + "/" + dstMat.getLabel(),
        properties_copied: copied,
        properties_skipped: skipped
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 6.5: Figure diagnostics scripts
# ---------------------------------------------------------------------------

_GET_FIGURE_INFO_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var figLabel = args.figureLabel;

    var fig = Scene.findNodeByLabel(figLabel);
    if (!fig) fig = Scene.findNode(figLabel);
    if (!fig) throw new Error("Figure not found: " + figLabel);

    var figName = fig.getName() || "";

    // Detect Genesis generation from node name and label (most reliable in DazScript)
    var generation = "other";
    var checkStr = (figName + " " + figLabel).toLowerCase();
    if (checkStr.indexOf("genesis 9") !== -1 || checkStr.indexOf("genesis9") !== -1 ||
        checkStr.indexOf("g9f") !== -1 || checkStr.indexOf("g9m") !== -1) {
        generation = "Genesis9";
    } else if (checkStr.indexOf("genesis 8") !== -1 || checkStr.indexOf("genesis8") !== -1 ||
               checkStr.indexOf("g8f") !== -1 || checkStr.indexOf("g8m") !== -1) {
        generation = "Genesis8";
    } else if (checkStr.indexOf("genesis 3") !== -1 || checkStr.indexOf("genesis3") !== -1 ||
               checkStr.indexOf("g3f") !== -1 || checkStr.indexOf("g3m") !== -1) {
        generation = "Genesis3";
    } else if (checkStr.indexOf("genesis 2") !== -1 || checkStr.indexOf("genesis2") !== -1 ||
               checkStr.indexOf("g2f") !== -1 || checkStr.indexOf("g2m") !== -1) {
        generation = "Genesis2";
    } else if (checkStr.indexOf("genesis") !== -1) {
        generation = "Genesis";
    }

    // Detect sex from name/label heuristics and generation-suffix
    var sex = "unknown";
    if (checkStr.indexOf("female") !== -1 || checkStr.indexOf("victoria") !== -1 ||
        checkStr.indexOf("aiko") !== -1 || checkStr.indexOf("stephanie") !== -1 ||
        checkStr.indexOf("g9f") !== -1 || checkStr.indexOf("g8f") !== -1 ||
        checkStr.indexOf("g3f") !== -1 || checkStr.indexOf("g2f") !== -1) {
        sex = "female";
    } else if (checkStr.indexOf("male") !== -1 || checkStr.indexOf("michael") !== -1 ||
               checkStr.indexOf("victor") !== -1 || checkStr.indexOf("g9m") !== -1 ||
               checkStr.indexOf("g8m") !== -1 || checkStr.indexOf("g3m") !== -1 ||
               checkStr.indexOf("g2m") !== -1) {
        sex = "male";
    }

    // Collect active morphs (non-zero numeric properties in morph/actor/shape paths)
    var activeMorphs = [];
    for (var i = 0; i < fig.getNumProperties(); i++) {
        var prop = fig.getProperty(i);
        if (!prop) continue;
        if (typeof prop.inherits === 'function' && !prop.inherits("DzFloatProperty")) continue;
        var path = typeof prop.getPath === 'function' ? prop.getPath() : "";
        var pLower = path.toLowerCase();
        var inMorphSection = pLower.indexOf("morph") !== -1 || pLower.indexOf("actor") !== -1 ||
                             pLower.indexOf("shape") !== -1 || pLower.indexOf("expression") !== -1 ||
                             pLower.indexOf("pose") !== -1;
        if (!inMorphSection) continue;
        var val = typeof prop.getValue === 'function' ? prop.getValue() : 0;
        if (Math.abs(val) > 0.0005) {
            activeMorphs.push({ name: prop.getName(), label: prop.getLabel(), value: val, path: path });
        }
    }

    // Count fitted items (nodes with follow target pointing to this figure, or direct children)
    var fittedCount = 0;
    var myID = fig.elementID;
    for (var n = 0; n < Scene.getNumNodes(); n++) {
        var other = Scene.getNode(n);
        if (!other || other.elementID === myID) continue;
        // Skip the figure's own skeleton (e.g. the Hip root bone is parented to the figure)
        if (typeof other.inherits === 'function' && other.inherits("DzBone")) continue;
        if (typeof other.getFollowTarget === 'function') {
            var ft = other.getFollowTarget();
            if (ft && ft.elementID === myID) { fittedCount++; continue; }
        }
        if (typeof other.getNodeParent === 'function') {
            var par = other.getNodeParent();
            if (par && par.elementID === myID) fittedCount++;
        }
    }

    // Subdivision level
    var subDivProp = fig.findProperty("SubDivision Level");
    if (!subDivProp) subDivProp = fig.findProperty("Subdivision Level");
    if (!subDivProp) subDivProp = fig.findProperty("Subdivision");
    var subDivLevel = subDivProp ? (typeof subDivProp.getValue === 'function' ? subDivProp.getValue() : 0) : 0;

    return {
        label: fig.getLabel(),
        name: fig.getName(),
        generation: generation,
        sex: sex,
        active_morphs: activeMorphs,
        active_morph_count: activeMorphs.length,
        fitted_item_count: fittedCount,
        subdivision_level: subDivLevel
    };
})()
"""

_SET_SUBDIVISION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabel = args.nodeLabel;
    var level = parseInt(args.level);
    if (isNaN(level) || level < 0) level = 0;
    if (level > 4) level = 4;

    var node = Scene.findNodeByLabel(nodeLabel);
    if (!node) node = Scene.findNode(nodeLabel);
    if (!node) throw new Error("Node not found: " + nodeLabel);

    // Search for subdivision property by common names
    var prop = node.findProperty("SubDivision Level");
    if (!prop) prop = node.findProperty("Subdivision Level");
    if (!prop) prop = node.findProperty("Subdivision");
    if (!prop) prop = node.findProperty("SDiv");

    // Fallback: linear scan for any property containing "subdivision"
    if (!prop) {
        for (var i = 0; i < node.getNumProperties(); i++) {
            var p = node.getProperty(i);
            if (p && p.getName().toLowerCase().indexOf("subdivision") !== -1) {
                prop = p;
                break;
            }
        }
    }

    if (!prop) {
        throw new Error("No subdivision property found on '" + nodeLabel + "'. This node may not support subdivision.");
    }

    var oldValue = typeof prop.getValue === 'function' ? prop.getValue() : null;
    if (typeof prop.setValue === 'function') {
        prop.setValue(level);
    } else {
        throw new Error("Subdivision property is read-only on '" + nodeLabel + "'.");
    }

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getName(),
        old_level: oldValue,
        new_level: level
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 6.6: Scene export script (shared; format param selects FBX vs OBJ)
# ---------------------------------------------------------------------------

_EXPORT_SCENE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var outputPath = args.outputPath;
    var nodeLabels = args.nodeLabels || [];
    var format = args.format || "Filmbox";
    var includeMorphs = args.includeMorphs !== false;
    var applyCurrentPose = args.applyCurrentPose !== false;
    var scaleFactor = args.scaleFactor !== undefined ? parseFloat(args.scaleFactor) : 1.0;

    if (!outputPath) throw new Error("outputPath is required");

    // Select nodes for export
    Scene.selectAllNodes(false);
    var exportedLabels = [];

    if (nodeLabels.length === 0) {
        // Export all top-level nodes (full scene)
        for (var i = 0; i < Scene.getNumNodes(); i++) {
            var n = Scene.getNode(i);
            if (n) { n.select(true); exportedLabels.push(n.getLabel()); }
        }
    } else {
        for (var j = 0; j < nodeLabels.length; j++) {
            var n2 = Scene.findNodeByLabel(nodeLabels[j]);
            if (!n2) n2 = Scene.findNode(nodeLabels[j]);
            if (n2) { n2.select(true); exportedLabels.push(n2.getLabel()); }
        }
        if (exportedLabels.length === 0) {
            throw new Error("None of the specified nodes were found in the scene: " + nodeLabels.join(", "));
        }
    }

    var exportMgr = App.getExportMgr();
    if (!exportMgr) throw new Error("DzExportMgr not available in this version of DAZ Studio.");

    var exporter = typeof exportMgr.findExporter === "function" ? exportMgr.findExporter(outputPath) : null;
    if (!exporter) {
        var numExp = typeof exportMgr.getNumExporters === "function" ? exportMgr.getNumExporters() : 0;
        for (var k = 0; k < numExp; k++) {
            var cand = exportMgr.getExporter(k);
            if (!cand) continue;
            var desc = typeof cand.getDescription === "function" ? cand.getDescription() : "";
            var cn = cand.className ? cand.className() : "";
            if (desc === format ||
                (format === "Filmbox" && cn === "DzFbxExporter") ||
                (format === "Wavefront Object" && cn === "DzObjExporter")) {
                exporter = cand;
                break;
            }
        }
    }
    if (!exporter || typeof exporter.writeFile !== "function") {
        var available = [];
        var numExp2 = typeof exportMgr.getNumExporters === "function" ? exportMgr.getNumExporters() : 0;
        for (var k2 = 0; k2 < numExp2; k2++) {
            var exp2 = exportMgr.getExporter(k2);
            if (exp2 && typeof exp2.getDescription === "function") {
                available.push(exp2.getDescription());
            }
        }
        var hint = available.length > 0
            ? " Available exporters: " + available.join(", ") + "."
            : " No exporters found — the required DAZ Studio exporter plugin may not be installed.";
        throw new Error("Exporter for '" + format + "' not found." + hint);
    }

    var settings = new DzFileIOSettings();
    if (typeof exporter.getDefaultOptions === "function") exporter.getDefaultOptions(settings);
    settings.setIntValue("RunSilent", 1);
    settings.setFloatValue("Scale", scaleFactor);
    settings.setBoolValue("SelectedOnly", true);
    settings.setBoolValue("SelectedRootsOnly", nodeLabels.length > 0);
    settings.setBoolValue("IncludeSelectedOnly", true);
    settings.setBoolValue("Morphs", includeMorphs);
    settings.setBoolValue("IncludeMorphs", includeMorphs);
    settings.setBoolValue("Pose", applyCurrentPose);
    settings.setBoolValue("IncludeAnimations", applyCurrentPose);
    settings.setBoolValue("IncludeFigures", true);
    settings.setBoolValue("IncludeProps", true);

    var err = exporter.writeFile(outputPath, settings);
    var errCode = (err && typeof err.valueOf === "function") ? err.valueOf() : err;
    if (errCode) {
        var errMsg = (typeof getErrorMessage === "function") ? getErrorMessage(errCode) : ("" + errCode);
        throw new Error("Export to '" + format + "' failed (" + errCode + "): " + errMsg);
    }

    return {
        success: true,
        format: format,
        output_path: outputPath,
        exported_nodes: exportedLabels,
        node_count: exportedLabels.length,
        include_morphs: includeMorphs,
        apply_current_pose: applyCurrentPose,
        scale_factor: scaleFactor
    };
})()
"""

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

_FIND_NODES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var query = args.query === undefined || args.query === null ? "" : String(args.query);
    if (!query) throw new Error("query is required");
    var matches = [];
    for (var i = 0; i < Scene.getNumNodes(); i++) {
        var n = Scene.getNode(i);
        if (!n) continue;
        if (n.getLabel() === query || n.getName() === query) {
            var p = n.getNodeParent ? n.getNodeParent() : null;
            matches.push({
                label: n.getLabel(),
                name: n.getName(),
                type: n.className(),
                elementID: n.elementID,
                parent: p ? p.getLabel() : null
            });
        }
    }
    return { query: query, count: matches.length, matches: matches };
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
    "vangard-scene-info": (
        "Return a snapshot of the current DAZ Studio scene",
        _SCENE_INFO_SCRIPT,
    ),
    "vangard-get-node": (
        "Return all numeric properties of a scene node by label",
        _GET_NODE_SCRIPT,
    ),
    "vangard-set-property": (
        "Set a numeric property on a scene node",
        _SET_PROPERTY_SCRIPT,
    ),
    "vangard-render": (
        "Trigger a render using current DAZ Studio render settings",
        _RENDER_SCRIPT,
    ),
    "vangard-load-file": (
        "Load a file into the current DAZ Studio scene",
        _LOAD_FILE_SCRIPT,
    ),
    "vangard-get-node-hierarchy": (
        "Get complete hierarchy tree for a node with recursive children",
        _GET_NODE_HIERARCHY_SCRIPT,
    ),
    "vangard-set-parent": (
        "Set parent of a node (parenting operation)",
        _SET_PARENT_SCRIPT,
    ),
    "vangard-look-at-point": (
        "Make character look at world-space point with configurable body involvement",
        _LOOK_AT_POINT_SCRIPT,
    ),
    "vangard-look-at-character": (
        "Make one character look at another character's head position",
        _LOOK_AT_CHARACTER_SCRIPT,
    ),
    "vangard-reach-toward": (
        "Position arm/hand to reach toward world-space point using pseudo-IK",
        _REACH_TOWARD_SCRIPT,
    ),
    "vangard-interactive-pose": (
        "Coordinate two characters for interactive poses (hug, handshake, etc)",
        _INTERACTIVE_POSE_SCRIPT,
    ),
    "vangard-batch-set-properties": (
        "Set multiple properties on one or more nodes with individual error handling",
        _BATCH_SET_PROPERTIES_SCRIPT,
    ),
    "vangard-set-active-camera": (
        "Set which camera is active in the viewport",
        _SET_ACTIVE_CAMERA_SCRIPT,
    ),
    "vangard-orbit-camera-around": (
        "Position camera orbiting around a target node at specified angle and distance",
        _ORBIT_CAMERA_AROUND_SCRIPT,
    ),
    "vangard-frame-camera-to-node": (
        "Frame camera to show a node by positioning at calculated distance",
        _FRAME_CAMERA_TO_NODE_SCRIPT,
    ),
    "vangard-save-camera-preset": (
        "Save camera position and rotation as preset data",
        _SAVE_CAMERA_PRESET_SCRIPT,
    ),
    "vangard-load-camera-preset": (
        "Restore camera position and rotation from preset data",
        _LOAD_CAMERA_PRESET_SCRIPT,
    ),
    "vangard-set-keyframe": (
        "Set a keyframe on a property at specified frame",
        _SET_KEYFRAME_SCRIPT,
    ),
    "vangard-get-keyframes": (
        "Get all keyframes for a property",
        _GET_KEYFRAMES_SCRIPT,
    ),
    "vangard-remove-keyframe": (
        "Remove a keyframe at specified frame",
        _REMOVE_KEYFRAME_SCRIPT,
    ),
    "vangard-clear-animation": (
        "Remove all keyframes from a property",
        _CLEAR_ANIMATION_SCRIPT,
    ),
    "vangard-render-with-camera": (
        "Render from specific camera without changing viewport",
        _RENDER_WITH_CAMERA_SCRIPT,
    ),
    "vangard-get-render-settings": (
        "Get current render settings and configuration",
        _GET_RENDER_SETTINGS_SCRIPT,
    ),
    "vangard-batch-render-cameras": (
        "Render from multiple cameras in sequence",
        _BATCH_RENDER_CAMERAS_SCRIPT,
    ),
    "vangard-render-animation": (
        "Render animation frame range as image sequence",
        _RENDER_ANIMATION_SCRIPT,
    ),
    # Phase 1: Property introspection
    "vangard-inspect-properties": (
        "List all properties on a node with metadata (type, value, min, max)",
        _INSPECT_PROPERTIES_SCRIPT,
    ),
    "vangard-get-property-metadata": (
        "Get detailed metadata for a single property on a node",
        _GET_PROPERTY_METADATA_SCRIPT,
    ),
    # Phase 1: Lighting presets
    "vangard-apply-lighting-preset": (
        "Create a professional lighting setup (three-point, rembrandt, butterfly, split, loop)",
        _APPLY_LIGHTING_PRESET_SCRIPT,
    ),
    # Phase 1: Scene validation
    "vangard-validate-scene": (
        "Validate scene for common issues: collisions, lighting, camera, figure presence",
        _VALIDATE_SCENE_SCRIPT,
    ),
    # Phase 1.5: Render quality preset (used by daz_set_render_quality)
    "vangard-set-render-quality": (
        "Set Iray render quality preset (draft/preview/good/final) via Max Samples and "
        "Render Quality properties",
        _SET_RENDER_QUALITY_SCRIPT,
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
    # Phase 2: Checkpoint system
    "vangard-save-scene-state": (
        "Serialize all node transforms, morphs, and light properties for checkpoint storage",
        _SAVE_SCENE_STATE_SCRIPT,
    ),
    "vangard-restore-scene-state": (
        "Restore node transforms, morphs, and light properties from a checkpoint snapshot",
        _RESTORE_SCENE_STATE_SCRIPT,
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
    "vangard-read-node-config": (
        "Read properties from named scene nodes and return as a serialisable dict",
        _READ_NODE_CONFIG_SCRIPT,
    ),
    "vangard-write-node-config": (
        "Apply a property dict to matching scene nodes, with per-node error handling",
        _WRITE_NODE_CONFIG_SCRIPT,
    ),
    "vangard-time-expression": (
        "Set keyframed morph animation for an expression with ease-in, hold, and ease-out phases",
        _TIME_EXPRESSION_SCRIPT,
    ),
    # Phase 5: Materials / Surfaces
    "vangard-get-material": (
        "Get all properties of a named material zone on a node (numeric, color, image types)",
        _GET_MATERIAL_SCRIPT,
    ),
    "vangard-set-material-property": (
        "Set a numeric or color property on a named material zone",
        _SET_MATERIAL_PROPERTY_SCRIPT,
    ),
    # Phase 5: Direct morph setting
    "vangard-set-morph": (
        "Set a morph value on a node by display label with fuzzy matching fallback",
        _SET_MORPH_SCRIPT,
    ),
    # Phase 5: Node lifecycle
    "vangard-delete-node": (
        "Remove a node (and its children) from the scene",
        _DELETE_NODE_SCRIPT,
    ),
    # Phase 5: Light management
    "vangard-list-lights": (
        "List all lights in the scene with type, position, and flux",
        _LIST_LIGHTS_SCRIPT,
    ),
    "vangard-create-light": (
        "Create a new light (spot/distant/point) and add it to the scene",
        _CREATE_LIGHT_SCRIPT,
    ),
    # Phase 5: Camera management
    "vangard-list-cameras": (
        "List all cameras in the scene with position and focal length",
        _LIST_CAMERAS_SCRIPT,
    ),
    "vangard-create-camera": (
        "Create a new camera and add it to the scene",
        _CREATE_CAMERA_SCRIPT,
    ),
    # Phase 5: Scene file operations
    "vangard-set-render-output": (
        "Set render output filename path and/or image dimensions (width x height)",
        _SET_RENDER_OUTPUT_SCRIPT,
    ),
    "vangard-set-render-engine": (
        "Set DS6 render engine via DzRenderOptions.renderType "
        "(iray / multi_pass_opengl / viewport)",
        _SET_RENDER_ENGINE_SCRIPT,
    ),
    # Phase 5: Pose reset
    "vangard-reset-pose": (
        "Zero all bone rotations on a figure recursively; optionally zero root transforms too",
        _RESET_POSE_SCRIPT,
    ),
    "vangard-list-fitted-items": (
        "List all clothing, hair, and prop nodes fitted or parented to a figure",
        _LIST_FITTED_ITEMS_SCRIPT,
    ),
    "vangard-fit-clothing": (
        "Fit a clothing or prop node to a base figure using follow-target or parenting",
        _FIT_CLOTHING_SCRIPT,
    ),
    "vangard-unfit-item": (
        "Remove the fitting relationship between a clothing/prop item and its figure",
        _UNFIT_ITEM_SCRIPT,
    ),
    # Phase 6.2: dForce simulation
    "vangard-add-dforce-dynamic-surface": (
        "Add a dForce Dynamic Surface modifier to a node via DzActionMgr "
        "(Edit > Object > Geometry > Add dForce Modifier: Dynamic Surface)",
        _ADD_DFORCE_DYNAMIC_SURFACE_SCRIPT,
    ),
    "vangard-set-dforce-influence-weights": (
        "Pin/free individual vertices for dForce simulation via "
        "DzDForceModifier.setInfluenceWeights (0 = fixed to base shape, 1 = free)",
        _SET_DFORCE_INFLUENCE_WEIGHTS_SCRIPT,
    ),
    "vangard-get-dforce-influence-weights": (
        "Read the per-vertex dForce influence (pinning) weights on a node",
        _GET_DFORCE_INFLUENCE_WEIGHTS_SCRIPT,
    ),
    "vangard-run-dforce-simulation": (
        "Run dForce cloth/hair simulation (duration set by DAZ's own Simulation "
        "Settings, not scriptable), optionally limited to one node",
        _RUN_DFORCE_SIMULATION_SCRIPT,
    ),
    "vangard-bake-simulation": (
        "Bake dForce simulation results to keyframes so the simulated shape is preserved",
        _BAKE_SIMULATION_SCRIPT,
    ),
    "vangard-set-dforce-property": (
        "Set a dForce modifier property (stiffness, gravity scale, etc.) on a scene node",
        _SET_DFORCE_PROPERTY_SCRIPT,
    ),
    "vangard-run-transfer-utility": (
        "Project rigging/morphs/UVs/groups from a source node onto a target node "
        "via DzTransferUtility (headless equivalent of Edit > Object > Rigging > "
        "Transfer Utility...)",
        _RUN_TRANSFER_UTILITY_SCRIPT,
    ),
    "vangard-get-dforce-surface-properties": (
        "List per-surface dForce simulation properties (Collision Offset, Self "
        "Collide, Dynamics Strength, stiffness, etc.) via DzDForceSettingsProvider "
        "— these live on the Surfaces-pane 'Simulation' category, not on DzMaterial",
        _GET_DFORCE_SURFACE_PROPERTIES_SCRIPT,
    ),
    "vangard-set-dforce-surface-property": (
        "Set a per-surface dForce simulation property via DzDForceSettingsProvider",
        _SET_DFORCE_SURFACE_PROPERTY_SCRIPT,
    ),
    # Phase 6.4: Material preset
    "vangard-apply-material-preset": (
        "Apply a .duf material preset file to a named scene node",
        _APPLY_MATERIAL_PRESET_SCRIPT,
    ),
    "vangard-convert-to-iray-uber": (
        "Upgrade every material zone on a node from DzDefaultMaterial to DzUberIrayMaterial "
        "via Daz's own shader-preset-application codepath",
        _CONVERT_TO_IRAY_UBER_SCRIPT,
    ),
    "vangard-copy-material": (
        "Copy all property values from one material slot to another within the scene",
        _COPY_MATERIAL_SCRIPT,
    ),
    # Phase 6.5: Figure diagnostics
    "vangard-get-figure-info": (
        "Return generation, sex, active morphs, fitted item count, and subdivision "
        "level for a figure",
        _GET_FIGURE_INFO_SCRIPT,
    ),
    "vangard-set-subdivision": (
        "Set the SubDivision Level property on a figure or prop (integer 0–4)",
        _SET_SUBDIVISION_SCRIPT,
    ),
    # Phase 6.6: Scene export
    "vangard-export-scene": (
        "Export selected nodes to FBX or OBJ via DzExportMgr",
        _EXPORT_SCENE_SCRIPT,
    ),
    "vangard-import-obj": (
        "Import a Wavefront OBJ with Scale=1 and RunSilent (no options dialog)",
        _IMPORT_OBJ_SCRIPT,
    ),
    "vangard-find-nodes": (
        "List every scene node matching a label or internal name, with elementIDs",
        _FIND_NODES_SCRIPT,
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

