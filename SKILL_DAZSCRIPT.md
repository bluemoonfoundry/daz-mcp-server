# Skill: DazScript Specialist
Rules for writing DazScript for DAZ Studio 4.24+.

## Globals & Environment
- `Scene` (DzScene), `App` (DzApp), `MainWindow`.
- Version check: `App.longVersionString`.

## Scripting Rules
- **No Bare Returns:** Wrap in IIFE: `(function(){ return {foo:42}; })()`.
- **Node Finding:** Labels are **not** unique (e.g. two `Hip` nodes). Prefer `Scene.findNodeByElementID(id)`, or `parent.findNodeChildByLabel(label, true)`. `findNodeByLabel` returns the first match only.
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
Time is in **ticks**, not frames: `var time = frame * Scene.getTimeStep();`

```javascript
// DzFloatProperty (camera controls, morph/transform props): two-arg setValue = keyframe
prop.setValue(time, value);      // creates/overwrites a key at that time (ticks)
prop.setValue(value);            // one-arg: sets current value, NO keyframe

// DzNumericProperty subclass (props from findProperty on figures):
prop.setDoubleValue(time, value);  // two-arg form = keyframe

// READ
prop.getNumKeys();
prop.getKeyTime(i);              // ticks
prop.getKeyValue(i);

// UPDATE existing key by index — never creates a new key
prop.setKeyValue(i, value);

// DELETE one key (range start==end). deleteKey() does not exist.
prop.deleteKeys(time, time);

// DELETE ALL keys on this property — not a substitute for single-key delete
prop.deleteAllKeys();

// BROKEN: prop.setKeyFrame(frame, value) — does not exist on any property class
// BROKEN: prop.getKeyFrame(index)        — use getKeyTime(i)
// BROKEN: prop.deleteKey(index)          — use deleteKeys(time, time)
// BROKEN: prop.setKey(frame, value)      — does not exist on any property class
// BROKEN: prop.getAnimation()            — does not exist
```

### Camera controls — always use dedicated control accessors (DzBasicCamera)
Never use `findProperty("Focal Length")` etc. on cameras. Use the typed control methods defined
in `DzBasicCamera` — they always return a `DzFloatProperty` / `DzBoolProperty` you can
call `.setValue()` on:

```javascript
var time = frame * Scene.getTimeStep();
camera.getDepthOfFieldControl().setBoolValue(true);   // enable DOF (DzBoolProperty)
camera.getFocalDistanceControl().setValue(200);        // focal distance in cm
camera.getFocalDistanceControl().setValue(time, 200);  // keyframe focal distance
camera.getFocalLengthControl().setValue(85);           // focal length in mm
camera.getFocalLengthControl().setValue(time, 85);     // keyframe focal length
camera.getFStopControl().setValue(2.8);               // aperture / F-stop
camera.getFocalPointScaleControl().setValue(1.0);     // focal point scale

// BROKEN: cam.findProperty("Focal Distance")  — returns null on a bare DzBasicCamera
// BROKEN: cam.findProperty("Focal Length")    — same; use getFocalLengthControl()
// BROKEN: cam.findProperty("F/Stop")          — use getFStopControl()
```

### Materials — DzDefaultMaterial vs DzUberIrayMaterial
Content merged into a scene as raw DSON (a hand-authored `.duf`, or a from-scratch scene-merge
exporter's output) reliably instantiates as the legacy `DzDefaultMaterial` ("DAZ Studio Default
(RSL)" in the UI), never `DzUberIrayMaterial`, no matter how complete the material's
`studio_material_channels` data is — confirmed by direct isolation testing (a byte-for-byte copy
of a real, working Iray Uber material's channel data, dropped into a self-contained merge, still
comes back as `DzDefaultMaterial`). The legacy shader doesn't even read modern fields like
`diffuse.channel.image_file`, so textures silently fail to display regardless of how correct the
data is. Use `daz_convert_to_iray_uber(node_label)` to fix this — it goes through Daz's own
shader-preset **application** codepath (`App.getContentMgr().openFile()` on a selected node, the
same thing that runs when a user drags a Shader Preset from Smart Content onto a figure) instead
of describing a shader in JSON, and reliably promotes every zone to genuine `DzUberIrayMaterial`.
This resets every channel to shader defaults — follow up with `daz_set_material_property` per
zone.

### Colors — linear values need `setFloatColorValue`, not `setColorValue`
```javascript
// setColorValue(QColor) is 0-255 sRGB-int and Daz gamma-DECODES it on the way in.
// Correct for a UI hex-picker value ("#RRGGBB", what daz_set_material_property expects),
// WRONG if you already have a linear-space 0-1 float (e.g. from another DCC's shader graph):
prop.setColorValue(new QColor(38, 26, 20));   // feeding linear 0.15 in as if it were sRGB 38/255
prop.getFloatColorValue();                     // reads back ~0.015, NOT 0.15 — silently darkened

// Linear-native setter — round-trips exactly:
prop.setFloatColorValue(new DzFloatColor(0.15, 0.1, 0.08, 1.0));
prop.getFloatColorValue();                     // reads back {red:0.15, green:0.1, blue:0.08, alpha:1}
```

### Texture maps — `setMap()` works on any mappable channel, color or numeric
```javascript
// Confirmed live on both classes — no per-channel-type table needed:
prop.setMap("C:/path/to/texture.png");   // DzFloatColorProperty (e.g. Diffuse Color)
prop.setMap("C:/path/to/rough.png");     // DzFloatProperty too (e.g. Glossy Roughness, Normal Map)
prop.isMapped();                          // true after setMap()
prop.getMapValue().getFilename();         // read back the path
// BROKEN assumption: that setMap only exists on image-specific property classes — it doesn't
// need one; probe with `typeof prop.setMap === 'function'` if unsure on a given class.
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

### Morph Loader Pro (`DzMorphLoader`) — confirmed live
Requires the Morph Loader Pro plugin active in the running instance (`typeof DzMorphLoader
!== "function"` if not). Two gotchas confirmed by live testing (round-tripped a hand-built
cube OBJ through `daz_load_morph_pro`):

```javascript
// setLoadMode(mode, node) validity depends on what node IS — wrong mode raises immediately:
//   plain prop (no skeleton)        -> PrimaryNode only
//   legacy (non-"single skin") figure -> EntireFigure, SelectedNodes, or PrimaryNode
//   "single skin" figure            -> SingleSkinFigure or SingleSkinFigureFromGraft only
// EntireFigure is NOT a safe default for props — check what kind of node you have first.

// createMorph()/createMorphs() need RunSilent on the DzFileIOSettings passed in, same as
// the OBJ importer, or DAZ Studio opens an OBJ import options dialog and blocks:
var settings = new DzFileIOSettings();
settings.setIntValue("RunSilent", 1);

// BROKEN ASSUMPTION: setOverwriteExisting(MakeUnique) silently auto-renames on a name
// collision. It does NOT — DAZ Studio opens a blocking interactive "morph already exists"
// rename dialog regardless of RunSilent on the file settings. There is no known
// FileIOSettings/loader flag that suppresses it. Avoid the collision instead of trying to
// suppress the prompt: check daz_search_morphs/daz_list_morphs for the target name first
// and pass one you know is unique.
```

### Content-Library asset export (`DzNodeSupportAssetFilter`) — confirmed live
`DzSaveFilter`/`DzSaveFilterMgr` are **deprecated** ("script-based presets... in favor of
DSON") — do not use them. The current DSON-based path is the `DzAssetIOFilter` family
(`docs.daz3d.com` group `File Input and Output Objects`), each with an official sample link.
For saving a node as a reusable Prop/Figure Support Asset:

```javascript
var node = Scene.findNodeByLabel("My Prop");
var filter = new DzNodeSupportAssetFilter();
filter.setNode(node);

var settings = new DzFileIOSettings();
filter.getDefaultOptions(settings);
// RunSilent (and every other key on this settings object) is a STRING "yes"/"no", not
// an int/bool — settings.setIntValue("RunSilent", 1) silently does nothing useful here.
settings.setStringValue("RunSilent", "yes");

// REQUIRED or doSave() fails with a generic errCode 98 (DZ_OPERATION_FAILED_ERROR).
// Must be one of App.getContentMgr().getContentDirectoryPath(i) — and outputPath itself
// must be a path INSIDE that same directory. The log (%APPDATA%/DAZ 3D/Studio6/log.txt)
// names this exact cause: dznodesupportassetfilter.cpp(1547): Running silent. No
// "BaseDataPath" defined. — worth checking that log whenever doSave() returns a bare
// numeric error code with no obvious reason.
settings.setStringValue("BaseDataPath", "C:/Users/me/Documents/DAZ 3D/Studio/My Library");
settings.setStringValue("VendorName", "MyStudio");
settings.setStringValue("ProductName", "My Product");
settings.setStringValue("ItemName", "My Prop");

var outputPath = "C:/Users/me/Documents/DAZ 3D/Studio/My Library/Props/MyProduct/My Prop.duf";
var err = filter.doSave(settings, outputPath, "");   // err.valueOf() === 0 on success
```

Confirmed live: writes the `.duf` preset at `outputPath` AND the actual geometry as
`<BaseDataPath>/data/<Vendor>/<Product>/<Item>/....dsf` (Daz's standard content layout) —
round-trip reloadable via the normal scene-merge importer. No thumbnail (`.duf.png`) is
generated by `doSave()` itself (compare to a UI-driven save, which produces one alongside
the `.duf`) — thumbnailing appears to be a separate, still-unconfirmed step.

`DzWearablesAssetFilter` (Wearable Preset, auto-fit-to-figure behavior) has no `setNode()` —
which node(s) to include goes through a `NodeNames` entry in the settings, which is itself a
`DzSettings` sub-object, not a plain string:

```javascript
var settings = new DzFileIOSettings();
new DzWearablesAssetFilter().getDefaultOptions(settings);
var nodeNames = settings.getSettingsValue("NodeNames");   // returns a DzSettings object
nodeNames.setStringValue(node.getName(), "1");             // key = node name, value arbitrary
settings.setSettingsValue("NodeNames", nodeNames);          // write back onto the parent
// MaterialNames works the same way, keyed by material zone name.
```

STILL BROKEN, WORKED AROUND: even with `NodeNames`/`MaterialNames` populated this way
(confirmed correct via `.toString()` → `<Settings><Setting Key="..." Type="String">1</Setting></Settings>`),
`doSave()` reproducibly fails with the same generic `errCode 98` under every configuration
tried (asset-backed vs. ad-hoc node, with/without a parent, keyed by name/label/elementID,
even a real figure with a real fitted item) — and unlike `DzNodeSupportAssetFilter`, the log
never records a specific reason. Do not spend more time on this script API; it is not a
`NodeNames`/settings problem. See Bug-Katalog #22 Teil 2 for the full list of disproven
hypotheses.

**What actually works instead: drive the real GUI action's native dialogs via Windows UI
Automation** (`pywinauto`, Windows-only — see `daz_save_wearable_preset` /
`_ui_automation.py`). Trigger `MainWindow.getActionMgr().findAction("DzWearablesAssetFilterAction")
.trigger()` (figure pre-selected, must already have ≥1 item fit/parented to it or DAZ shows a
"Selection Error" dialog instead of the save dialog), then automate the two resulting windows:

```python
# 1. Native "Filtered Save" file dialog (class "#32770"). Its filename field's
#    window_text()/WM_GETTEXT ALWAYS show only the static label ("Dateiname:") —
#    checking success that way is a trap. Use UIA ValuePattern instead:
edit = win.child_window(auto_id="1001", control_type="Edit")
edit.set_edit_text(str(output_path))
assert edit.get_value() == str(output_path)   # get_value(), never window_text()

# Its Save button: neither UIA .invoke() nor a raw win32gui BM_CLICK on the button's
# own HWND triggers the action (both return without error, dialog stays open). What
# works — WM_COMMAND/BN_CLICKED sent to the DIALOG window, not the button:
win32gui.SendMessage(dialog_hwnd, win32con.WM_COMMAND, win32api.MAKELONG(1, 0), 0)

# 2. The resulting Qt6 "Wearable(s) Preset Save Options" dialog (auto_id prefix
#    "App.WearablesAssetFilterDialog") behaves normally — .invoke() on
#    "...BasicDlgButtonGrpBox.BasicDlgAcceptDialogBtn" works fine, no workaround needed.
# Its node-inclusion checklist (TreeItems under "...AssetFilterNodeAssetSelectionView")
# has no confirmed toggle mechanism (no TogglePattern, is_selected() always 0 — likely
# custom-painted checkboxes) — left at its default (bundles everything currently
# fitted to the figure).

# DAZ finishes writing the file a moment AFTER the dialog visually closes — poll
# path.exists() briefly rather than checking once immediately after Accept.
```
