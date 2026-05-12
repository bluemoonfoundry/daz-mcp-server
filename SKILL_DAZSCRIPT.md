# Skill: DazScript Specialist
Rules for writing DazScript for DAZ Studio 4.24+.

## Globals & Environment
- `Scene` (DzScene), `App` (DzApp), `MainWindow`.
- Version check: `App.longVersionString`.

## Scripting Rules
- **No Bare Returns:** Wrap in IIFE: `(function(){ return {foo:42}; })()`.
- **Node Finding:** Prefer `Scene.findNodeByLabel(label)` (unique) over `findNode`.
- **Creation:** Use `new DzBasicCamera()` or `new DzSpotLight()`. Do NOT use UI Actions/Menus.
- **Coordinate System:** Genesis figures face **+Z** (Front).
- **Element ID:** `node.elementID` is a property, not a method.

## Common Property Internal Names
- **Transforms:** `XTranslate`, `YRotate`, `Scale`.
- **Lights:** `Flux`, `Shadow Softness`, `Spread Angle`, `Environment Mode`.

## Verified API Patterns (live-tested against DAZ Studio 4.24)

These were confirmed by running scripts against a live instance. Do not assume alternatives work.

### Saving the scene
```javascript
Scene.saveScene(filePath);   // saves without a dialog — the ONLY working headless save
// BROKEN: App.saveScene(), App.getInterface().saveScene(), Scene.setFilename(),
//         MainWindow.triggerAction(), MainWindow.saveScene(), MainWindow.saveSceneAs()
// BLOCKS (opens UI dialog): MainWindow.doDAZSave(), MainWindow.doDAZSaveAs()
```

### Materials — always go through getCurrentShape()
```javascript
var shape = node.getObject().getCurrentShape();  // DzShape — has getNumMaterials()
// BROKEN: node.getObject().getNumMaterials() — DzObject has no materials directly
```

### Bounding box
```javascript
var bbox = node.getWSBoundingBox();          // returns DzBox3
var cx = (bbox.minX + bbox.maxX) / 2;       // compute center manually
// BROKEN: node.getBoundingBox(), bbox.getCenter()
```

### Render options — property assignment, no setter methods
```javascript
var opts = App.getRenderMgr().getRenderOptions();
opts.renderImgFilename = path;   // BROKEN: opts.setRenderImgFilename(path)
opts.aspectWidth  = w;           // BROKEN: opts.setImageSize(w, h)
opts.aspectHeight = h;
// Read back the same properties: opts.renderImgFilename, opts.aspectWidth, opts.aspectHeight
```

### Bone naming by generation
**Authoritative** — probed live from DAZ Studio 4.24. Full reference: `src/vangard_daz_mcp/genesis_bones.json`.

Genesis 3 and Genesis 8 share identical internal bone names. Genesis 9 uses a completely different `l_`/`r_` underscore scheme.

| Joint | Genesis 3 & 8 | Genesis 9 |
|-------|--------------|-----------|
| Hip / root | `hip` | `hip` |
| Pelvis | `pelvis` | `pelvis` |
| Spine (low→high) | `abdomenLower`, `abdomenUpper`, `chestLower`, `chestUpper` | `spine1`, `spine2`, `spine3`, `spine4` |
| Neck (low→high) | `neckLower`, `neckUpper` | `neck1`, `neck2` |
| Head | `head` | `head` |
| Eyes | `lEye` / `rEye` | `l_eye` / `r_eye` |
| Shoulder (upper arm) | `lShldrBend` / `rShldrBend` | `l_upperarm` / `r_upperarm` |
| Shoulder twist | `lShldrTwist` / `rShldrTwist` | *(no direct equivalent)* |
| Forearm | `lForearmBend` / `rForearmBend` | `l_forearm` / `r_forearm` |
| Hand | `lHand` / `rHand` | `l_hand` / `r_hand` |
| Thigh | `lThighBend` / `rThighBend` | `l_thigh` / `r_thigh` |
| Shin | `lShin` / `rShin` | `l_shin` / `r_shin` |
| Foot | `lFoot` / `rFoot` | `l_foot` / `r_foot` |

**Detection:** `fig.getName()` contains `"Genesis3"`, `"Genesis8"`, or `"Genesis9"`.

**Fallback pattern for generation-agnostic scripts:**
```javascript
var lUpperArm = findBone(fig, "l_upperarm") || findBone(fig, "lShldrBend");
var neckUp    = findBone(fig, "neck2")      || findBone(fig, "neckUpper");
var lEye      = findBone(fig, "l_eye")      || findBone(fig, "lEye");
var spineTop  = findBone(fig, "spine3")     || findBone(fig, "chestUpper");
```

### Re-parenting nodes
```javascript
// BROKEN: node.setNodeParent(newParent, inPlace)  — method does not exist
// CORRECT: call addNodeChild on the NEW parent; it auto-detaches from current parent
newParent.addNodeChild(node, maintainWorldTransform);
// To explicitly remove from current parent (without deleting):
currentParent.removeNodeChild(node, inPlace);
// inPlace=true preserves world position by adjusting local transform
```

### Cameras — Perspective view is NOT a DzCamera
`Scene.getNumCameras()` returns 0 in a fresh scene. The "Perspective Camera" seen in the
DAZ Studio viewport is a built-in viewport mode, not a `DzCamera` object. Only cameras
created with `new DzBasicCamera()` (or loaded from a `.duf`) appear in `Scene.getNumCameras()`.
Always handle `camera_count == 0` as a valid state.

### Keyframe animation — correct API
```javascript
// DzFloatProperty (camera controls, morph/transform props): two-arg setValue = keyframe
prop.setValue(frame, value);     // creates a keyframe at the given frame number
prop.setValue(value);            // one-arg: sets current value, NO keyframe

// DzNumericProperty subclass (props from findProperty on figures):
prop.setDoubleValue(frame, value);  // two-arg form = keyframe

// BROKEN: prop.setKeyFrame(frame, value) — does not exist on any property class
// BROKEN: prop.setKey(frame, value)      — does not exist on any property class
// BROKEN: prop.getAnimation()            — does not exist
```

### Camera controls — always use dedicated control accessors (DzBasicCamera)
Never use `findProperty("Focal Length")` etc. on cameras. Use the typed control methods defined
in `DzBasicCamera` — they always return a `DzFloatProperty` / `DzBoolProperty` you can
call `.setValue()` / `.setKey()` on:

```javascript
camera.getDepthOfFieldControl().setBoolValue(true);   // enable DOF (DzBoolProperty)
camera.getFocalDistanceControl().setValue(200);        // focal distance in cm
camera.getFocalDistanceControl().setKey(frame, 200);  // keyframe focal distance
camera.getFocalLengthControl().setValue(85);           // focal length in mm
camera.getFocalLengthControl().setKey(frame, 85);     // keyframe focal length
camera.getFStopControl().setValue(2.8);               // aperture / F-stop
camera.getFocalPointScaleControl().setValue(1.0);     // focal point scale

// BROKEN: cam.findProperty("Focal Distance")  — returns null on a bare DzBasicCamera
// BROKEN: cam.findProperty("Focal Length")    — same; use getFocalLengthControl()
// BROKEN: cam.findProperty("F/Stop")          — use getFStopControl()
```

### Probing unknown objects
When a method name is uncertain, enumerate at runtime before writing the script:
```javascript
var methods = [];
for (var k in SomeObject) {
    if (typeof SomeObject[k] === 'function') methods.push(k);
}
return { methods: methods };
```
