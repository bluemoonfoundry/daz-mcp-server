# DAZ MCP Server Enhancement Plan

**Version:** 1.0
**Date:** 2026-04-06
**Status:** Planning Phase

## Executive Summary

This document outlines a comprehensive enhancement plan for the DAZ MCP Server to transform it from a low-level scripting interface into a high-level cinematic direction tool. The plan addresses four critical gaps:

1. **DAZ API Assistance** - Enable LLMs to discover and validate API usage dynamically
2. **3D Space Understanding** - Provide spatial reasoning capabilities for natural scene composition
3. **Content Library Intelligence** - Enable semantic search and smart content discovery
4. **Cinematic Direction** - Abstract complex operations into director-friendly high-level commands

**Impact:** Shifts workflow from manual low-level scripting to natural language creative direction, making DAZ Studio accessible to users who understand cinematography but not 3D software.

**Timeline:** 4 phases over 14-19 weeks, prioritized by impact and complexity.

---

## Current State Analysis

### Strengths
- ✅ 39 tools covering basic DAZ Studio operations
- ✅ Low-level script execution (`daz_execute`, `daz_execute_file`)
- ✅ High-level structured tools (scene info, node manipulation, rendering)
- ✅ Morph discovery and batch operations
- ✅ Multi-character interaction helpers (look-at, reach-toward, interactive poses)
- ✅ Animation system (keyframes, frame control)
- ✅ Multi-camera rendering
- ✅ Static documentation via `daz_script_help`

### Weaknesses
- ❌ No dynamic API introspection (LLMs must memorize or guess)
- ❌ No spatial query capabilities (can't reason about 3D positions/distances)
- ❌ No content discovery (must know exact file paths)
- ❌ No high-level scene composition tools
- ❌ No lighting presets or photography rules
- ❌ No emotional/mood direction for characters
- ❌ No validation before execution (errors discovered after)
- ❌ No undo/checkpoint system

---

## Gap Analysis & Proposed Solutions

### 1. DAZ API Assistance for LLMs

#### Current Problem
- LLMs must rely on static documentation that can't cover all properties/methods
- No way to discover "What properties exist on this spotlight?"
- Errors only surface after script execution
- Limited error context makes debugging difficult

#### Proposed Tools

##### 1.1 Dynamic Property Inspection
```python
daz_inspect_properties(
    node_label: str,
    property_type: str = "all"  # "numeric", "string", "bool", "transform", "morph", "all"
) -> dict
```
**Returns:**
```json
{
  "node": "Spotlight 1",
  "properties": [
    {
      "label": "Luminous Flux (Lumen)",
      "name": "Flux",
      "type": "DzFloatProperty",
      "value": 1500.0,
      "min": 0.0,
      "max": 100000.0,
      "path": "Light/Photometrics",
      "is_animatable": true
    }
  ],
  "count": 45
}
```
**Use Case:** "What properties can I set on this spot light?"

**DazScript Implementation:**
```javascript
(function(){
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) throw new Error("Node not found");

    var props = [];
    for (var i = 0; i < node.getNumProperties(); i++) {
        var prop = node.getProperty(i);
        var typeFilter = args.propertyType || "all";

        // Apply type filter
        var include = false;
        if (typeFilter === "all") include = true;
        else if (typeFilter === "numeric" && prop.inherits("DzNumericProperty")) include = true;
        else if (typeFilter === "transform" && isTransformProperty(prop.getName())) include = true;
        else if (typeFilter === "morph" && isMorphProperty(prop)) include = true;

        if (include) {
            props.push({
                label: prop.getLabel(),
                name: prop.getName(),
                type: prop.className(),
                value: prop.getValue ? prop.getValue() : null,
                min: prop.getMin ? prop.getMin() : null,
                max: prop.getMax ? prop.getMax() : null,
                path: prop.getPath ? prop.getPath() : "",
                is_animatable: prop.isAnimatable ? prop.isAnimatable() : false
            });
        }
    }

    return { node: node.getLabel(), properties: props, count: props.length };
})()
```

##### 1.2 Property Metadata Lookup
```python
daz_get_property_metadata(
    node_label: str,
    property_name: str
) -> dict
```
**Returns:**
```json
{
  "label": "Luminous Flux (Lumen)",
  "name": "Flux",
  "type": "DzFloatProperty",
  "current_value": 1500.0,
  "default_value": 1500.0,
  "min": 0.0,
  "max": 100000.0,
  "is_animatable": true,
  "path": "Light/Photometrics",
  "description": "Light intensity in lumens"
}
```
**Use Case:** Validate values before setting, understand property constraints.

##### 1.3 Script Validation (Pre-Flight Check)
```python
daz_validate_script(script: str) -> dict
```
**Returns:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "line": 5,
      "message": "Using deprecated pattern: DzNewCameraAction",
      "suggestion": "Use 'var cam = new DzBasicCamera()' instead"
    }
  ],
  "suggestions": [
    "Consider wrapping in IIFE for return value",
    "Use Scene.findNodeByLabel() before Scene.findNode()"
  ]
}
```
**Use Case:** Catch errors before execution, learn best practices.

**Implementation:** Pattern matching against known anti-patterns (DzNewCameraAction, Point At property, etc.)

##### 1.4 API Reference Query
```python
daz_query_api(
    class_name: str,
    method_name: str = None
) -> dict
```
**Returns:**
```json
{
  "class": "DzBasicCamera",
  "methods": [
    {
      "name": "aimAt",
      "signature": "aimAt(DzVec3 target)",
      "description": "Points camera at target position in world space",
      "returns": "void",
      "example": "camera.aimAt(new DzVec3(0, 160, 0));"
    }
  ],
  "properties": ["XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate"],
  "inherits": ["DzCamera", "DzNode"]
}
```
**Use Case:** "What methods does DzBasicCamera have?"

**Implementation:** Pre-generated reference from DAZ SDK documentation, stored in JSON.

**Priority:** HIGH - Directly improves LLM accuracy and reduces trial-and-error.

---

### 2. 3D Space Understanding

#### Current Problem
- LLMs can't reason about spatial relationships ("is the camera too close?", "are they overlapping?")
- No way to query positions, distances, or bounding boxes
- Manual coordinate math required for all spatial operations
- No collision detection or proximity checking

#### Proposed Tools

##### 2.1 World-Space Position Query
```python
daz_get_world_position(node_label: str) -> dict
```
**Returns:**
```json
{
  "node": "Genesis 9",
  "world_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "local_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
  "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
}
```
**Use Case:** "Where is the character's hand in world space?"

**DazScript:**
```javascript
(function(){
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) throw new Error("Node not found");

    var wsPos = node.getWSPos();
    var localPos = node.getOrigin();
    var rot = node.getWSRot();
    var scale = node.getWSScale();

    return {
        node: node.getLabel(),
        world_position: {x: wsPos.x, y: wsPos.y, z: wsPos.z},
        local_position: {x: localPos.x, y: localPos.y, z: localPos.z},
        rotation: {x: rot.x, y: rot.y, z: rot.z},
        scale: {x: scale.x, y: scale.y, z: scale.z}
    };
})()
```

##### 2.2 Bounding Box Query
```python
daz_get_bounding_box(node_label: str) -> dict
```
**Returns:**
```json
{
  "node": "Genesis 9",
  "min": {"x": -30.0, "y": 0.0, "z": -15.0},
  "max": {"x": 30.0, "y": 175.0, "z": 15.0},
  "center": {"x": 0.0, "y": 87.5, "z": 0.0},
  "width": 60.0,
  "height": 175.0,
  "depth": 30.0
}
```
**Use Case:** Auto-calculate camera framing distance, detect collisions.

**DazScript:**
```javascript
(function(){
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) throw new Error("Node not found");

    var bbox = node.getBoundingBox();
    var min = bbox.min;
    var max = bbox.max;

    return {
        node: node.getLabel(),
        min: {x: min.x, y: min.y, z: min.z},
        max: {x: max.x, y: max.y, z: max.z},
        center: {
            x: (min.x + max.x) / 2,
            y: (min.y + max.y) / 2,
            z: (min.z + max.z) / 2
        },
        width: max.x - min.x,
        height: max.y - min.y,
        depth: max.z - min.z
    };
})()
```

##### 2.3 Distance Calculation
```python
daz_calculate_distance(
    node1_label: str,
    node2_label: str
) -> dict
```
**Returns:**
```json
{
  "node1": "Genesis 9",
  "node2": "Camera 1",
  "distance": 250.5,
  "vector": {"dx": 0.0, "dy": 50.0, "dz": 245.0},
  "horizontal_distance": 245.0,
  "vertical_distance": 50.0
}
```
**Use Case:** "How far apart are these two characters?"

##### 2.4 Spatial Relationship Query
```python
daz_get_spatial_relationship(
    node1_label: str,
    node2_label: str
) -> dict
```
**Returns:**
```json
{
  "node1": "Alice",
  "node2": "Bob",
  "distance": 120.0,
  "direction": "front-right",
  "angle_horizontal": 45.0,
  "angle_vertical": 5.0,
  "relative_position": "Bob is in front and to the right of Alice",
  "overlapping": false
}
```
**Use Case:** Natural language spatial reasoning - "Where is Bob relative to Alice?"

##### 2.5 Scene Layout Map
```python
daz_get_scene_layout(
    include_types: list[str] = ["figures", "cameras", "lights", "props"]
) -> dict
```
**Returns:**
```json
{
  "nodes": [
    {
      "label": "Genesis 9",
      "type": "figure",
      "position": {"x": 0, "y": 0, "z": 0},
      "bounds": {"width": 60, "height": 175, "depth": 30}
    },
    {
      "label": "Camera 1",
      "type": "camera",
      "position": {"x": 0, "y": 160, "z": 250},
      "facing": {"x": 0, "y": 160, "z": 0}
    }
  ],
  "scene_bounds": {
    "min": {"x": -500, "y": 0, "z": -300},
    "max": {"x": 500, "y": 300, "z": 500}
  }
}
```
**Use Case:** "Show me where everything is positioned" - gives LLM spatial map of entire scene.

##### 2.6 Proximity Finder
```python
daz_find_nearby_nodes(
    node_label: str,
    radius: float,
    include_types: list[str] = None
) -> dict
```
**Returns:**
```json
{
  "center_node": "Genesis 9",
  "radius": 100.0,
  "nearby_nodes": [
    {"label": "Chair", "type": "prop", "distance": 45.0, "direction": "left-back"},
    {"label": "Table", "type": "prop", "distance": 80.0, "direction": "right"}
  ],
  "count": 2
}
```
**Use Case:** "What objects are near the character?"

##### 2.7 Collision Detection
```python
daz_check_overlap(
    node1_label: str,
    node2_label: str
) -> dict
```
**Returns:**
```json
{
  "node1": "Alice",
  "node2": "Bob",
  "overlapping": true,
  "penetration_depth": 15.0,
  "suggestion": "Move Bob 20cm in +X direction to resolve collision"
}
```
**Use Case:** Detect interpenetrating characters in multi-character scenes.

**Priority:** HIGH - Essential for natural language scene composition. Without spatial understanding, LLMs can't reason about "move the camera closer" or "position the light above the character."

---

### 3. Content Library Intelligence

#### Current Problem
- No way to search content by description ("medieval armor")
- Must know exact file paths to load content
- No filtering by compatibility, genre, or metadata
- No preview capabilities
- No dependency checking (might load content requiring missing products)

#### Proposed Tools

##### 3.1 Semantic Content Search
```python
daz_search_content(
    query: str,
    content_types: list[str] = None,  # ["character", "clothing", "prop", "hair", "pose", "environment"]
    limit: int = 20
) -> dict
```
**Example Queries:**
- "medieval armor"
- "casual clothing for Genesis 9"
- "sci-fi props"
- "romantic poses"

**Returns:**
```json
{
  "query": "medieval armor",
  "results": [
    {
      "path": "/People/Genesis 9/Clothing/Medieval/Knight_Armor.duf",
      "name": "Knight Armor for Genesis 9",
      "description": "Complete medieval knight armor set",
      "type": "clothing",
      "thumbnail_path": "/.../thumbnail.png",
      "compatibility": ["Genesis 9"],
      "tags": ["medieval", "armor", "knight", "fantasy"],
      "relevance_score": 0.95
    }
  ],
  "count": 15,
  "total_searched": 45231
}
```

**Implementation Requirements:**
1. **Offline Indexing Pipeline:**
   - Crawl all content directories (`App.getContentMgr().getContentDirectoryPath()`)
   - Parse .duf files (JSON) to extract metadata
   - Extract: name, description, type, compatible figures, artist, product
   - Generate embeddings from names + descriptions (sentence-transformers)
   - Build vector index (FAISS or similar)

2. **Index Storage:**
   - SQLite database for metadata
   - FAAS/numpy for vector index
   - Track file modification times for incremental updates

3. **Query Process:**
   - Embed user query
   - Vector similarity search in index
   - Return top K results with metadata

**Challenges:**
- Typical user library: 10k-100k content files
- Initial indexing: 30min-2hrs (one-time)
- Incremental updates on content install
- Embedding model size (~100MB for sentence-transformers)

**Alternative (Simpler):** Text-based search on metadata without embeddings (regex on names/descriptions/tags).

##### 3.2 Category Browser
```python
daz_list_categories(parent_path: str = "/") -> dict
```
**Returns:**
```json
{
  "parent": "/People/Genesis 9",
  "categories": [
    {"path": "/People/Genesis 9/Characters", "count": 156},
    {"path": "/People/Genesis 9/Clothing", "count": 423},
    {"path": "/People/Genesis 9/Hair", "count": 89},
    {"path": "/People/Genesis 9/Poses", "count": 234}
  ]
}
```

```python
daz_browse_category(
    category_path: str,
    sort_by: str = "name"  # "name", "date_added", "date_modified"
) -> dict
```
**Returns:**
```json
{
  "category": "/People/Genesis 9/Hair",
  "items": [
    {
      "path": "/.../Long_Hair_01.duf",
      "name": "Long Hair 01",
      "type": "hair",
      "date_added": "2025-12-15",
      "compatible_figures": ["Genesis 9"]
    }
  ],
  "count": 89
}
```
**Use Case:** Structured navigation - "Show me all Genesis 9 hair assets"

**DazScript Implementation:**
```javascript
(function(){
    var contentMgr = App.getContentMgr();
    var categories = [];

    for (var i = 0; i < contentMgr.getNumContentDirectories(); i++) {
        var basePath = contentMgr.getContentDirectoryPath(i);
        var dir = new DzDir(basePath + args.parentPath);

        if (dir.exists()) {
            var subdirs = dir.entryList([], DzDir.Dirs | DzDir.NoDotAndDotDot);
            for (var j = 0; j < subdirs.length; j++) {
                var subdir = new DzDir(dir.absoluteFilePath(subdirs[j]));
                var fileCount = subdir.entryList(["*.duf"], DzDir.Files).length;
                categories.push({
                    path: args.parentPath + "/" + subdirs[j],
                    count: fileCount
                });
            }
        }
    }

    return { parent: args.parentPath, categories: categories };
})()
```

##### 3.3 Content Metadata Query
```python
daz_get_content_info(file_path: str) -> dict
```
**Returns:**
```json
{
  "path": "/.../Knight_Armor.duf",
  "name": "Knight Armor",
  "description": "Medieval knight armor set",
  "type": "wearable",
  "dependencies": ["Genesis 9 Base"],
  "compatible_figures": ["Genesis 9"],
  "tags": ["medieval", "armor", "knight"],
  "artist": "Artist Name",
  "product_name": "Medieval Armor Collection",
  "install_date": "2025-12-01",
  "file_size_mb": 45.2
}
```
**Use Case:** "What does this require?" before loading.

**Implementation:** Parse .duf JSON file, extract asset_info, compatible_figures, dependencies.

##### 3.4 Compatibility Checker
```python
daz_check_compatibility(
    content_path: str,
    figure_label: str
) -> dict
```
**Returns:**
```json
{
  "content": "Long_Hair_G8F.duf",
  "figure": "Genesis 9",
  "compatible": false,
  "reason": "Hair is for Genesis 8 Female, figure is Genesis 9",
  "alternatives": [
    {"path": "/.../Long_Hair_G9.duf", "name": "Long Hair G9"}
  ],
  "conversion_possible": true,
  "conversion_method": "Use Genesis 8-to-9 converter"
}
```
**Use Case:** "Will this hair work with Genesis 8?"

##### 3.5 Content Recommendations
```python
daz_suggest_content(
    context: str,
    figure_label: str = None,
    limit: int = 10
) -> dict
```
**Example Contexts:**
- "completing this outfit"
- "accessories for warrior character"
- "matching hairstyle"

**Returns:**
```json
{
  "context": "completing this outfit",
  "suggestions": [
    {
      "path": "/.../Combat_Boots.duf",
      "name": "Combat Boots",
      "reason": "Matches loaded military jacket style",
      "relevance": 0.89
    }
  ],
  "count": 10
}
```
**Use Case:** "What shoes go with this dress?"

**Implementation:** Analyze currently loaded clothing items, extract style tags, search for complementary items.

##### 3.6 Thumbnail Preview
```python
daz_get_content_thumbnail(file_path: str) -> dict
```
**Returns:**
```json
{
  "content_path": "/.../Knight_Armor.duf",
  "thumbnail_path": "/.../Knight_Armor.png",
  "has_preview": true,
  "thumbnail_size": {"width": 256, "height": 256}
}
```
**Use Case:** Visual selection without loading full asset.

**Implementation:** DAZ content packages typically include .png thumbnails alongside .duf files.

**Priority:**
- **MEDIUM-HIGH:** Category browser and metadata query (relatively simple, high value)
- **MEDIUM:** Semantic search (complex infrastructure, transformative for UX)
- **LOW:** Recommendations (requires ML or rule-based matching)

---

### 4. Cinematic Director Workflow

#### Current Problem
- No high-level scene composition tools
- No lighting presets (users must manually position lights)
- No emotional/mood direction capabilities
- No pre-built scene templates
- Users must understand low-level 3D operations to create scenes

#### Proposed Tools (Organized by Abstraction Level)

#### A. Scene Composition (Photography Rules)

##### 4.1 Composition Rule Application
```python
daz_apply_composition_rule(
    camera_label: str,
    subject_label: str,
    rule: str  # "rule-of-thirds", "golden-ratio", "center-frame", "leading-lines"
) -> dict
```
**Example:**
```python
# Position camera to frame subject using rule of thirds
daz_apply_composition_rule("Camera 1", "Genesis 9", "rule-of-thirds")
```
**Returns:**
```json
{
  "camera": "Camera 1",
  "subject": "Genesis 9",
  "rule": "rule-of-thirds",
  "adjustments": {
    "camera_position": {"x": -40, "y": 160, "z": 250},
    "camera_rotation": {"x": 0, "y": 8, "z": 0},
    "explanation": "Subject positioned on right third line at eye level"
  }
}
```

**Implementation:**
- Get subject bounding box center
- Calculate camera position to place subject at rule-of-thirds intersection
- Apply offset based on rule (thirds = 33%/66% of frame)

##### 4.2 Shot Type Framing
```python
daz_frame_shot(
    camera_label: str,
    subject_label: str,
    shot_type: str
) -> dict
```
**Shot Types:**
- `"extreme-close-up"` - Eyes/mouth detail (20-30cm)
- `"close-up"` - Face/head (40-60cm)
- `"medium-close-up"` - Head and shoulders (80-100cm)
- `"medium-shot"` - Waist up (120-150cm)
- `"medium-full"` - Knees up (180-220cm)
- `"full-shot"` - Entire body (350-450cm)
- `"wide-shot"` - Body + environment (600-800cm)

**Example:**
```python
daz_frame_shot("Camera 1", "Genesis 9", "medium-close-up")
```
**Returns:**
```json
{
  "camera": "Camera 1",
  "subject": "Genesis 9",
  "shot_type": "medium-close-up",
  "distance": 95.0,
  "framing": "head and shoulders",
  "camera_height": 160.0
}
```

**Implementation:**
- Get subject bounding box
- Calculate distance based on shot type and subject height
- Position camera at appropriate height (typically eye level for most shots)

##### 4.3 Camera Angle Presets
```python
daz_apply_camera_angle(
    camera_label: str,
    subject_label: str,
    angle: str
) -> dict
```
**Angles:**
- `"eye-level"` - Camera at subject's eye height (neutral)
- `"high-angle"` - Camera 30-45° above subject (vulnerable, diminished)
- `"low-angle"` - Camera 20-30° below subject (powerful, dominant)
- `"dutch-angle"` - Tilted camera (unsettling, dynamic)
- `"overhead"` - Camera directly above (bird's eye)
- `"worms-eye"` - Camera at ground level looking up (dramatic)
- `"over-shoulder"` - Positioned behind subject's shoulder

**Example:**
```python
daz_apply_camera_angle("Camera 1", "Genesis 9", "low-angle")
```

**Implementation:**
- Calculate vertical angle from subject center
- Position camera at calculated angle while maintaining distance
- Adjust aim point based on angle type

---

#### B. Lighting Presets (Photography/Cinema)

##### 4.4 Lighting Setup Templates
```python
daz_apply_lighting_preset(
    preset: str,
    subject_label: str = None
) -> dict
```

**Presets:**

1. **Three-Point Lighting** (`"three-point"`)
   - Key light: Front-right, 45° horizontal, 30° vertical, 2000 lumens
   - Fill light: Front-left, 45° horizontal, 15° vertical, 800 lumens
   - Rim light: Back, 180° horizontal, 45° vertical, 1200 lumens

2. **Rembrandt Lighting** (`"rembrandt"`)
   - Key light: 45° to side, 45° above, creates triangle of light under eye
   - Dramatic portrait lighting

3. **Butterfly Lighting** (`"butterfly"`)
   - Key light: Directly in front, 45° above
   - Creates butterfly-shaped shadow under nose
   - Glamour/beauty lighting

4. **Split Lighting** (`"split"`)
   - Key light: 90° to side
   - Half face in shadow, half lit
   - Dramatic, moody

5. **Loop Lighting** (`"loop"`)
   - Key light: 30-45° to side, slightly above
   - Small shadow loop on opposite cheek
   - Standard portrait

6. **Broad Lighting** (`"broad"`)
   - Lights the side of face turned toward camera
   - Makes face appear wider

7. **Short Lighting** (`"short"`)
   - Lights the side of face turned away from camera
   - Makes face appear narrower

**Example:**
```python
result = daz_apply_lighting_preset("three-point", subject_label="Genesis 9")
```

**Returns:**
```json
{
  "preset": "three-point",
  "subject": "Genesis 9",
  "lights_created": [
    {"label": "Key Light", "type": "DzSpotLight", "position": {"x": 150, "y": 180, "z": 150}},
    {"label": "Fill Light", "type": "DzSpotLight", "position": {"x": -120, "y": 150, "z": 120}},
    {"label": "Rim Light", "type": "DzDistantLight", "position": {"x": 0, "y": 200, "z": -200}}
  ],
  "environment_mode": "Scene Only"
}
```

**Implementation:**
- Create appropriate light types (Spot, Point, Distant)
- Calculate positions relative to subject using spherical coordinates
- Set intensity values (Flux property)
- Configure shadow softness
- Disable dome lighting (Environment Mode = 3)

##### 4.5 Mood Lighting
```python
daz_set_mood_lighting(
    mood: str,
    intensity: float = 1.0
) -> dict
```

**Moods:**
- `"romantic"` - Warm, soft, low-intensity
- `"dramatic"` - High contrast, hard shadows
- `"scary"` - Low key, shadows, colored lights
- `"peaceful"` - Soft, even, natural
- `"energetic"` - Bright, multiple colored lights
- `"mysterious"` - Low key, rim lighting
- `"golden-hour"` - Warm orange/yellow tones
- `"blue-hour"` - Cool blue tones
- `"overcast"` - Soft, diffused, no hard shadows
- `"studio-bright"` - High intensity, minimal shadows

**Example:**
```python
daz_set_mood_lighting("romantic", intensity=0.8)
```

**Implementation:**
- Adjust existing light intensities
- Set light color temperatures (warm = orange, cool = blue)
- Configure shadow softness
- Adjust environment lighting mode and intensity

##### 4.6 Time-of-Day Lighting
```python
daz_apply_time_of_day(
    time: str,
    outdoor: bool = True
) -> dict
```

**Times:**
- `"dawn"` - Soft pink/orange, low angle
- `"morning"` - Bright, slightly warm
- `"noon"` - Harsh overhead, neutral white
- `"afternoon"` - Warm, angled
- `"golden-hour"` - Warm orange, low angle
- `"dusk"` - Purple/blue, low angle
- `"night"` - Cool blue moonlight, low intensity
- `"midnight"` - Very dark, minimal lighting

**Example:**
```python
daz_apply_time_of_day("golden-hour", outdoor=True)
```

**Implementation:**
- Create/adjust directional light (sun/moon)
- Set light position based on time (angle above horizon)
- Set light color temperature
- Adjust environment dome brightness
- Configure ambient light intensity

**Priority:** HIGH - Lighting presets provide immediate professional results with minimal user effort. Biggest ROI for cinematic workflow.

---

#### C. Character Direction (High-Level Posing)

##### 4.7 Emotional State
```python
daz_set_emotion(
    character_label: str,
    emotion: str,
    intensity: float = 0.7
) -> dict
```

**Emotions:**
- `"happy"` - Smile, relaxed body, open posture
- `"sad"` - Frown, slumped shoulders, head down
- `"angry"` - Furrowed brow, tense body, clenched fists
- `"surprised"` - Wide eyes, raised eyebrows, open mouth
- `"fearful"` - Wide eyes, tense body, defensive posture
- `"disgusted"` - Wrinkled nose, turned away
- `"neutral"` - Relaxed, no expression
- `"excited"` - Wide smile, animated posture
- `"bored"` - Half-closed eyes, slumped posture
- `"confident"` - Upright posture, chest out, chin up
- `"shy"` - Turned inward, arms crossed, looking down
- `"loving"` - Soft smile, relaxed, open arms
- `"contemptuous"` - Raised lip corner, turned away

**Example:**
```python
daz_set_emotion("Genesis 9", "happy", intensity=0.8)
```

**Returns:**
```json
{
  "character": "Genesis 9",
  "emotion": "happy",
  "intensity": 0.8,
  "applied_morphs": [
    {"morph": "Smile", "value": 0.8},
    {"morph": "Eyes Closed", "value": 0.2},
    {"morph": "Mouth Open", "value": 0.15}
  ],
  "body_adjustments": [
    {"bone": "chestUpper", "property": "XRotate", "value": 3.0}
  ]
}
```

**Implementation:**
1. **Facial Morphs Mapping:**
   - Happy: Smile (0.7-1.0), Eyes Closed (0.1-0.3 squint), Mouth Open (0.1-0.2)
   - Sad: Mouth Frown (0.6-0.9), Brow Down (0.5-0.8), Eyes Closed (0.2-0.4)
   - Angry: Brow Down (0.8-1.0), Mouth Frown (0.6), Eyes Wide (0.3), Nose Wrinkle (0.5)

2. **Body Language Adjustments:**
   - Happy: Slight chest lift (chestUpper XRotate +3-5°)
   - Sad: Slumped shoulders (chestUpper XRotate -5-8°)
   - Confident: Chest out, shoulders back

3. **Intensity Scaling:**
   - Multiply all morph/rotation values by intensity factor

##### 4.8 Action Pose Library
```python
daz_apply_action_pose(
    character_label: str,
    action: str,
    variation: int = 0
) -> dict
```

**Actions:**
- `"standing"` - Neutral standing poses (variations: relaxed, attention, contrapposto)
- `"sitting"` - Sitting poses (variations: formal, casual, cross-legged)
- `"walking"` - Walking cycle poses (variations: casual, hurried, sneaking)
- `"running"` - Running poses
- `"fighting"` - Combat stances (variations: defensive, offensive, boxing)
- `"dancing"` - Dance poses (variations: ballroom, modern, hip-hop)
- `"reaching"` - Reaching/grabbing poses
- `"pointing"` - Pointing gestures
- `"waving"` - Waving gestures
- `"thinking"` - Thinking/pondering poses (variations: hand on chin, arms crossed)
- `"relaxed"` - Relaxed/lounging poses

**Example:**
```python
daz_apply_action_pose("Genesis 9", "standing", variation=2)
```

**Implementation:**
- Load pre-made pose presets (.duf files)
- OR apply procedural bone rotations for simple poses
- Variations select different preset files

##### 4.9 Gaze Direction
```python
daz_direct_gaze(
    character_label: str,
    direction: str,
    target_label: str = None
) -> dict
```

**Directions:**
- `"camera"` - Look at active camera
- `"away"` - Look away from camera
- `"down"` - Look down
- `"up"` - Look up
- `"left"` - Look left
- `"right"` - Look right
- `"character"` - Look at another character (requires target_label)

**Example:**
```python
daz_direct_gaze("Alice", "character", target_label="Bob")
```

**Implementation:**
- Calculate target position based on direction
- Use existing `daz_look_at_point` or `daz_look_at_character` internally
- Default mode="eyes" for subtle gaze, upgrade to "head" if direction is extreme

##### 4.10 Body Language
```python
daz_set_body_language(
    character_label: str,
    posture: str,
    intensity: float = 0.7
) -> dict
```

**Postures:**
- `"confident"` - Chest out, shoulders back, chin up, straight spine
- `"defensive"` - Arms crossed, shoulders hunched, turned away
- `"aggressive"` - Leaning forward, fists clenched, wide stance
- `"submissive"` - Hunched, head down, arms close to body
- `"relaxed"` - Loose shoulders, slight hip tilt (contrapposto)
- `"tense"` - Stiff spine, raised shoulders, clenched hands
- `"open"` - Arms out, chest open, welcoming
- `"closed"` - Arms crossed, turned inward, protective

**Example:**
```python
daz_set_body_language("Genesis 9", "confident", intensity=0.8)
```

**Implementation:**
- Adjust spine bones (chestUpper, abdomenUpper, hip)
- Adjust shoulder positions
- Adjust arm positions (rShldrBend, lShldrBend)
- Scale adjustments by intensity

**Priority:**
- **HIGH:** Emotional state (transforms user experience)
- **MEDIUM:** Gaze direction, Body language
- **LOW:** Action pose library (can use existing pose presets)

---

#### D. Scene Templates (Highest Abstraction)

##### 4.11 Scene Generator from Description
```python
daz_create_scene(
    description: str,
    characters: list[str] = None
) -> dict
```

**Example Descriptions:**
- "romantic dinner for two"
- "warrior preparing for battle"
- "job interview scene"
- "family portrait"
- "two friends having coffee"

**Example:**
```python
daz_create_scene(
    description="romantic dinner for two",
    characters=["Alice", "Bob"]
)
```

**Returns:**
```json
{
  "description": "romantic dinner for two",
  "actions_performed": [
    "Loaded dining table prop",
    "Loaded chairs (2x)",
    "Positioned Alice at chair 1",
    "Positioned Bob at chair 2, facing Alice",
    "Applied 'sitting' pose to both characters",
    "Applied 'romantic' mood lighting",
    "Created camera 1: over-shoulder Alice",
    "Created camera 2: over-shoulder Bob",
    "Created camera 3: wide shot of table",
    "Set emotions: Alice=loving, Bob=loving"
  ],
  "suggestions": [
    "Add wine glasses and candles for atmosphere",
    "Adjust character expressions for more variety",
    "Consider adding background environment"
  ]
}
```

**Implementation:**
- Parse description for scene type, number of characters, objects needed
- Load appropriate props from content library
- Position objects and characters logically
- Apply appropriate lighting preset
- Create cameras at standard angles
- Apply poses and emotions

**Complexity:** HIGH - Requires understanding natural language, scene structure, and chaining multiple operations.

##### 4.12 Pre-Built Scene Templates
```python
daz_apply_scene_template(
    template: str,
    characters: dict = None
) -> dict
```

**Templates:**
- `"portrait-studio"` - Single character, portrait lighting, gray backdrop
- `"interview-setup"` - Two characters facing each other, neutral lighting
- `"dance-floor"` - Open space, colored lights, spotlight
- `"outdoor-landscape"` - HDR environment, natural lighting, wide camera
- `"conference-room"` - Table, multiple chairs, professional lighting
- `"bedroom"` - Bedroom props, soft lighting, intimate framing
- `"kitchen"` - Kitchen props, bright lighting
- `"street-scene"` - Urban environment, natural/street lighting

**Example:**
```python
daz_apply_scene_template(
    "portrait-studio",
    characters={"subject": "Genesis 9"}
)
```

**Implementation:**
- Load pre-configured scene file (.duf) with props and lights
- OR programmatically create props and lights
- Position provided characters at designated spots
- Apply default camera angles

##### 4.13 Shot Sequence Builder
```python
daz_create_shot_sequence(
    sequence_type: str,
    characters: list[str],
    duration: int
) -> dict
```

**Sequences:**
- `"establishing-medium-closeup"` - Wide → Medium → Close-up progression
- `"shot-reverse-shot"` - Alternate between two characters (conversation)
- `"walkthrough"` - Camera follows character movement
- `"orbit"` - Camera orbits around subject
- `"push-in"` - Dolly in from wide to close-up

**Example:**
```python
daz_create_shot_sequence(
    "shot-reverse-shot",
    characters=["Alice", "Bob"],
    duration=240  # frames (8 seconds at 30fps)
)
```

**Implementation:**
- Create multiple cameras
- Set keyframes for camera positions/rotations
- Define frame ranges for each shot
- Return camera switching schedule

##### 4.14 Conversation Choreography
```python
daz_animate_conversation(
    char1: str,
    char2: str,
    dialogue_beats: list[dict]
) -> dict
```

**Example:**
```python
daz_animate_conversation(
    char1="Alice",
    char2="Bob",
    dialogue_beats=[
        {"speaker": "Alice", "start": 0, "end": 60, "emotion": "happy", "gesture": "wave"},
        {"speaker": "Bob", "start": 60, "end": 120, "emotion": "surprised", "gesture": "point"},
        {"speaker": "Alice", "start": 120, "end": 180, "emotion": "thoughtful"}
    ]
)
```

**Implementation:**
- Set look-at keyframes (Alice looks at Bob when Bob speaks, vice versa)
- Apply emotion morphs at start of each beat
- Trigger gesture poses (if specified)
- Add subtle idle animation (breathing, weight shifts)

**Priority:**
- **MEDIUM (v2):** Scene templates (high value, moderate complexity)
- **LOW (v2):** Scene generation, Shot sequences, Conversation choreography (complex, requires AI reasoning)

---

#### E. Quality Assurance & Suggestions

##### 4.15 Scene Validator
```python
daz_validate_scene() -> dict
```

**Returns:**
```json
{
  "valid": true,
  "issues": [
    {
      "type": "collision",
      "severity": "high",
      "nodes": ["Alice", "Chair"],
      "description": "Alice's legs intersect with chair geometry",
      "suggestion": "Move Alice 10cm in +Z direction"
    }
  ],
  "warnings": [
    {
      "type": "poor-lighting",
      "severity": "medium",
      "description": "Scene has only one light source, causing harsh shadows",
      "suggestion": "Add fill light at (-120, 150, 120) with 800 lumens"
    },
    {
      "type": "camera-clipping",
      "severity": "low",
      "camera": "Camera 1",
      "description": "Camera near-clip plane may cut off foreground object",
      "suggestion": "Reduce near-clip distance or move camera back"
    }
  ],
  "suggestions": [
    {
      "improvement": "composition",
      "description": "Subject centered in frame, consider rule-of-thirds",
      "action": "daz_apply_composition_rule('Camera 1', 'Genesis 9', 'rule-of-thirds')"
    }
  ],
  "score": 72,
  "score_breakdown": {
    "lighting": 60,
    "composition": 70,
    "character_spacing": 95,
    "technical": 85
  }
}
```

**Checks:**
1. **Collision Detection** - Characters/props overlapping
2. **Lighting Quality** - Number of lights, intensity balance
3. **Camera Framing** - Subject position, headroom, clipping
4. **Character Spacing** - Distance between characters appropriate
5. **Technical Issues** - Clipping, out-of-bounds objects

**Implementation:**
- Run bounding box overlap checks for all figures/props
- Count lights, check intensity ratios
- Evaluate camera framing against composition rules
- Check for objects outside camera view frustum

##### 4.16 Auto-Improve Scene
```python
daz_auto_improve_scene(
    aspects: list[str]  # ["lighting", "composition", "character-spacing", "camera-angles"]
) -> dict
```

**Example:**
```python
result = daz_auto_improve_scene(aspects=["lighting", "composition"])
```

**Returns:**
```json
{
  "improvements_applied": [
    {
      "aspect": "lighting",
      "action": "Added fill light to reduce shadow harshness",
      "details": "Created 'Fill Light' at (-120, 150, 120) with 800 lumens"
    },
    {
      "aspect": "composition",
      "action": "Applied rule-of-thirds to Camera 1",
      "details": "Moved camera to position subject on right third line"
    }
  ],
  "before_score": 65,
  "after_score": 83,
  "improvement": 18
}
```

**Implementation:**
- Run scene validator
- For each aspect, apply fixes based on detected issues
- Re-run validator to confirm improvements

##### 4.17 Context-Aware Suggestions
```python
daz_suggest_next_action() -> dict
```

**Returns:**
```json
{
  "current_state": {
    "figures": ["Genesis 9"],
    "cameras": ["Camera 1"],
    "lights": [],
    "scene_type": "portrait"
  },
  "suggestions": [
    {
      "action": "Add lighting setup",
      "reason": "Scene has no lights, will render dark",
      "command": "daz_apply_lighting_preset('three-point', 'Genesis 9')",
      "priority": "high"
    },
    {
      "action": "Apply emotion",
      "reason": "Character has neutral expression",
      "command": "daz_set_emotion('Genesis 9', 'happy', 0.7)",
      "priority": "medium"
    },
    {
      "action": "Frame shot",
      "reason": "Camera distance may not be optimal",
      "command": "daz_frame_shot('Camera 1', 'Genesis 9', 'medium-close-up')",
      "priority": "medium"
    }
  ]
}
```

**Implementation:**
- Analyze scene state using `daz_scene_info()`
- Apply heuristics: no lights → suggest lighting, no pose → suggest pose
- Return actionable commands

**Priority:**
- **HIGH:** Scene validator (immediate value, prevents errors)
- **MEDIUM:** Auto-improve scene
- **LOW:** Context-aware suggestions (nice-to-have)

---

#### F. Natural Language Scene Editing

##### 4.18 High-Level Scene Modifier
```python
daz_modify_scene(instruction: str) -> dict
```

**Example Instructions:**
- "Make the scene darker"
- "Move the character closer to the camera"
- "Add more dramatic lighting"
- "Make the pose more casual"
- "Adjust framing to show more headroom"

**Example:**
```python
result = daz_modify_scene("Make the scene darker")
```

**Returns:**
```json
{
  "instruction": "Make the scene darker",
  "interpretation": "Reduce lighting intensity",
  "actions_performed": [
    {"tool": "daz_set_property", "args": {"node_label": "Key Light", "property_name": "Flux", "value": 1000.0}},
    {"tool": "daz_set_property", "args": {"node_label": "Fill Light", "property_name": "Flux", "value": 400.0}}
  ],
  "explanation": "Reduced all light intensities by 50%"
}
```

**Implementation:**
- Parse instruction to identify intent (lighting, positioning, framing, mood)
- Map intent to concrete operations
- Execute operations
- Return explanation

**Complexity:** VERY HIGH - Requires:
1. Natural language understanding (NLU) to parse intent
2. Scene context awareness to determine which objects to modify
3. Multi-step planning for complex instructions
4. Could leverage LLM reasoning (ask Claude to plan operations)

**Alternative Approach:**
Rather than a tool, this could be a workflow where:
1. User gives natural language instruction
2. LLM (Claude) reasons about instruction in context of scene state
3. LLM calls appropriate tools to implement instruction
4. No special "modify_scene" tool needed - just better prompting

**Priority:** LOW (v3+) - Most complex feature. Better suited as LLM workflow than single tool.

---

## 5. Cross-Cutting Improvements

### Undo/History Management

#### 5.1 Scene State Checkpoints
```python
daz_save_scene_state(checkpoint_name: str) -> dict
daz_restore_scene_state(checkpoint_name: str) -> dict
daz_list_checkpoints() -> dict
daz_delete_checkpoint(checkpoint_name: str) -> dict
```

**Example:**
```python
# Save checkpoint before major changes
daz_save_scene_state("before_lighting_experiment")

# Make changes...
daz_apply_lighting_preset("dramatic", "Genesis 9")

# Oops, don't like it - restore
daz_restore_scene_state("before_lighting_experiment")
```

**Implementation:**
- Save entire scene to temporary .duf file with checkpoint name
- Store checkpoint metadata (timestamp, description)
- Restore by loading saved .duf file

**Limitation:** DAZ Studio doesn't have granular undo API, so checkpoint system is scene-level only.

---

### Performance & Diagnostics

#### 5.2 Performance Stats
```python
daz_get_performance_stats() -> dict
```
**Returns:**
```json
{
  "last_operation": {
    "tool": "daz_apply_lighting_preset",
    "duration_ms": 850,
    "timestamp": "2026-04-06T10:30:15Z"
  },
  "session_stats": {
    "total_api_calls": 127,
    "total_duration_ms": 45230,
    "average_call_ms": 356,
    "cache_hit_rate": 0.73
  }
}
```

#### 5.3 Error Explanation
```python
daz_explain_last_error(include_suggestions: bool = True) -> dict
```
**Returns:**
```json
{
  "error": "Property not found: Fluxs on Spotlight 1",
  "explanation": "The property name 'Fluxs' is not valid. Did you mean 'Flux'?",
  "suggestions": [
    "Use daz_inspect_properties('Spotlight 1') to see available properties",
    "Common light properties: Flux, Shadow Softness, Spread Angle",
    "Property names are case-sensitive"
  ],
  "similar_properties": ["Flux", "Shadow Softness"],
  "documentation_link": "topic=light"
}
```

---

### Macro Recording

#### 5.4 Macro System
```python
daz_start_recording(macro_name: str, description: str = "") -> dict
daz_stop_recording() -> dict
daz_replay_macro(macro_name: str, parameters: dict = None) -> dict
daz_list_macros() -> dict
daz_export_macro(macro_name: str, output_path: str) -> dict
daz_import_macro(input_path: str) -> dict
```

**Example:**
```python
# Start recording
daz_start_recording("portrait_setup", "My standard portrait lighting and framing")

# Perform operations (all are recorded)
daz_apply_lighting_preset("three-point", "Genesis 9")
daz_frame_shot("Camera 1", "Genesis 9", "medium-close-up")
daz_apply_composition_rule("Camera 1", "Genesis 9", "rule-of-thirds")
daz_set_emotion("Genesis 9", "happy", 0.7)

# Stop recording
daz_stop_recording()

# Later, replay on different character
daz_replay_macro("portrait_setup", parameters={"subject": "Alice"})
```

**Implementation:**
- Record sequence of tool calls with parameters
- Store as JSON array
- Replay by executing tools in sequence
- Support parameterization (replace "Genesis 9" with variable)

**Use Case:** Reusable workflows for common tasks.

---

## Implementation Roadmap

### Phase 1: Critical Foundation (2-3 weeks)

**Focus:** Spatial reasoning and API discovery

1. **Spatial Query Tools** (Week 1)
   - `daz_get_world_position`
   - `daz_get_bounding_box`
   - `daz_calculate_distance`
   - `daz_get_spatial_relationship`
   - `daz_check_overlap`

2. **Property Introspection** (Week 2)
   - `daz_inspect_properties`
   - `daz_get_property_metadata`
   - Update `daz_script_help` with dynamic API reference

3. **Scene Validation** (Week 2-3)
   - `daz_validate_scene`
   - Collision detection
   - Lighting quality checks
   - Composition analysis

4. **Lighting Presets** (Week 3)
   - `daz_apply_lighting_preset`
   - Implement: three-point, Rembrandt, butterfly
   - Test with various character positions

**Deliverables:**
- 10 new tools
- Updated documentation
- Test suite for spatial queries
- Example workflows

**Success Criteria:**
- LLM can query spatial relationships without math
- LLM can discover properties without memorization
- Users can apply professional lighting in one command

---

### Phase 1.5: Asynchronous Operations (2 weeks) - **HIGH PRIORITY**

**Focus:** Non-blocking long-running operations (renders, animations)

**Status:** CONFIRMED FEASIBLE - DAZ SDK has `killRender()` for cancellation

1. **DazScriptServer Plugin Changes** (Week 1)
   - Request registry (in-memory, serial execution)
   - Async endpoints: `/execute/async`, `/requests/{id}/status`, `/requests/{id}/result`
   - Cancellation support using `DzRenderer::killRender()`
   - TTL cleanup (1 hour)
   - Time estimation based on render history

2. **MCP Server Async Tools** (Week 2)
   - `daz_render_async` - Non-blocking render
   - `daz_render_with_camera_async` - Camera-specific async render
   - `daz_batch_render_cameras_async` - Queue multiple camera renders
   - `daz_render_animation_async` - Animation rendering (hours-long)
   - `daz_get_request_status` - Poll progress
   - `daz_get_request_result` - Retrieve result
   - `daz_cancel_request` - Cancel operation
   - `daz_list_requests` - List all requests
   - `daz_set_render_quality` - Draft/preview/good/final presets

**Deliverables:**
- 9 new MCP tools
- DazScriptServer async execution support
- Request management system with cancellation
- Render history and time estimation
- Documentation with usage patterns
- Test suite

**Success Criteria:**
- Can queue 8 renders and monitor progress
- Can cancel slow render mid-execution
- Test render workflow (draft→adjust→final) works smoothly
- Animation rendering reports frame progress
- Time estimation within 30% accuracy after 10 renders
- No memory leaks from abandoned requests

**Implementation Details:** See `ASYNC_OPERATIONS.md` for complete technical specifications.

---

### Phase 2: Quality of Life (3-4 weeks) — ✅ IMPLEMENTED 2026-04-08

**Focus:** Usability and content discovery

5. **Emotional Direction** (Week 4)
   - `daz_set_emotion`
   - Facial morph mappings for 8 basic emotions
   - Body language adjustments

6. **Content Library - Metadata** (Week 5)
   - `daz_get_content_info`
   - `daz_list_categories`
   - `daz_browse_category`
   - Parse .duf metadata

7. **Scene Composition** (Week 6)
   - `daz_apply_composition_rule`
   - `daz_frame_shot`
   - `daz_apply_camera_angle`
   - Photography rule implementations

8. **Checkpoint System** (Week 6-7)
   - `daz_save_scene_state`
   - `daz_restore_scene_state`
   - `daz_list_checkpoints`

9. **Scene Layout & Proximity** (Week 7)
   - `daz_get_scene_layout`
   - `daz_find_nearby_nodes`

**Deliverables:**
- 11 new tools
- Content library navigation
- Undo/checkpoint system
- Emotional state system

**Success Criteria:**
- LLM can apply emotions with one command
- Users can browse content library programmatically
- Users can experiment safely with checkpoints
- LLM has spatial map of entire scene

---

### Phase 3: Advanced Features (4-6 weeks)

**Focus:** Cinematic workflows and smart search

10. **Semantic Content Search** (Week 8-10)
    - Build indexing pipeline
    - Extract metadata from content library
    - Generate embeddings (sentence-transformers)
    - Build vector index (FAISS)
    - `daz_search_content`
    - `daz_check_compatibility`

11. **Mood & Time-of-Day Lighting** (Week 10)
    - `daz_set_mood_lighting`
    - `daz_apply_time_of_day`
    - Color temperature and intensity mappings

12. **Body Language & Gaze** (Week 11)
    - `daz_set_body_language`
    - `daz_direct_gaze`
    - Posture bone adjustments

13. **Scene Templates** (Week 12)
    - `daz_apply_scene_template`
    - Pre-built templates: portrait-studio, interview, etc.
    - Template file format

14. **Auto-Improvement** (Week 13)
    - `daz_auto_improve_scene`
    - Implement fix logic for common issues
    - `daz_suggest_next_action`

**Deliverables:**
- 7 new tools
- Semantic content search system
- Scene templates library
- Auto-improvement AI

**Success Criteria:**
- Users can find content by description ("medieval armor")
- LLM can create complete scenes from templates
- Auto-improve provides measurable quality increase
- Mood lighting transforms scene atmosphere

---

### Phase 4: Cinematic AI (Future/v2.0)

**Focus:** Natural language workflows and advanced automation

15. **Scene Generation** (Week 14-16)
    - `daz_create_scene`
    - Natural language parsing
    - Multi-step scene construction
    - Intelligent prop/character placement

16. **Shot Sequences** (Week 16-17)
    - `daz_create_shot_sequence`
    - Multi-camera animation
    - Shot-reverse-shot automation

17. **Conversation Choreography** (Week 18)
    - `daz_animate_conversation`
    - Dialogue beat synchronization
    - Look-at animation
    - Gesture triggers

18. **Macro System** (Week 18-19)
    - Recording and replay
    - Parameterization
    - Import/export
    - Macro library

19. **Natural Language Editing** (Research/Future)
    - `daz_modify_scene` OR
    - LLM-based workflow (preferred approach)
    - Instruction parsing and planning

**Deliverables:**
- 5 new tools
- Scene generation AI
- Macro recording system
- Natural language workflow prototype

**Success Criteria:**
- Users can create scenes from descriptions
- Conversation animation is automatic
- Macros enable workflow reuse
- Natural language editing works for simple instructions

---

## Architecture Considerations

### Property Introspection
**Challenge:** DazScript has limited reflection capabilities

**Solution:**
- Pre-generate API reference from DAZ SDK documentation
- Store as JSON in `dazscript_api_reference.json`
- Cache property lists per node type to reduce overhead
- Update reference periodically with new DAZ Studio releases

**File Structure:**
```json
{
  "classes": {
    "DzBasicCamera": {
      "methods": [...],
      "properties": [...],
      "inherits": ["DzCamera", "DzNode"]
    }
  }
}
```

---

### Spatial Queries
**Challenge:** Bounding box calculations can be expensive

**Solution:**
- Cache bounding boxes during session
- Invalidate cache when nodes move/transform
- Use `node.elementID` for cache key
- Consider lazy evaluation (only compute when requested)

**Performance:**
- Bounding box: ~50-100ms per node (acceptable)
- Distance calculation: ~5ms (cheap)
- Scene layout: ~500ms for 50 nodes (batch operation)

---

### Semantic Content Search
**Challenge:** Indexing 10k-100k content files is expensive

**Solution:**
1. **Offline Indexing Pipeline:**
   ```python
   # Run once or incrementally
   python -m vangard_daz_mcp.content_indexer
   ```

2. **Index Storage:**
   - SQLite for metadata: `~/.daz3d/content_index.db`
   - FAAS for vectors: `~/.daz3d/content_vectors.index`
   - Track file mtimes for incremental updates

3. **Embedding Model:**
   - Use `sentence-transformers/all-MiniLM-L6-v2` (80MB)
   - Fast inference (~10ms per query)
   - Good semantic understanding for product names/descriptions

4. **Query Flow:**
   - Embed query → Vector search (FAAS) → Top 100 candidates
   - Re-rank by metadata filters (compatibility, type)
   - Return top 20

**Initial Index Time:** 30min-2hrs (one-time cost)
**Query Time:** 50-200ms
**Storage:** ~100MB for 50k assets

---

### Lighting Presets
**Challenge:** Light positioning must adapt to character size/position

**Solution:**
- Always calculate positions relative to subject bounding box center
- Use subject height to scale distances
- Store presets as relative coordinates (angles + distance multipliers)

**Preset Format:**
```json
{
  "three-point": {
    "lights": [
      {
        "type": "DzSpotLight",
        "name": "Key Light",
        "position_relative": {
          "angle_horizontal": 45,
          "angle_vertical": 30,
          "distance_multiplier": 1.5
        },
        "properties": {
          "Flux": 2000,
          "Shadow Softness": 20,
          "Spread Angle": 60
        }
      }
    ],
    "environment_mode": 3
  }
}
```

---

### Emotional State
**Challenge:** Mapping emotions to morphs is subjective

**Solution:**
1. **Start with consensus mappings:**
   - Research facial action coding system (FACS)
   - Study existing emotion presets in DAZ
   - Create base mappings from research

2. **Allow customization:**
   - Store mappings in editable JSON
   - Users can tune morph values
   - Community can share custom emotion definitions

3. **Iterative refinement:**
   - Collect feedback on emotion accuracy
   - A/B test different morph combinations
   - Build ML model from user corrections (future)

**Emotion Mapping File:**
```json
{
  "emotions": {
    "happy": {
      "morphs": [
        {"name": "Smile", "value": 0.8},
        {"name": "Eyes Closed", "value": 0.2},
        {"name": "Mouth Open", "value": 0.15}
      ],
      "bones": [
        {"bone": "chestUpper", "property": "XRotate", "value": 3.0}
      ]
    }
  }
}
```

---

### Scene Templates
**Challenge:** Templates must be flexible for different characters/props

**Solution:**
1. **Template Specification Format:**
   ```json
   {
     "template_id": "portrait-studio",
     "description": "Professional portrait setup",
     "required_slots": {
       "subject": "figure"
     },
     "optional_props": ["backdrop", "stool"],
     "actions": [
       {
         "type": "create_node",
         "node_type": "DzBasicCamera",
         "label": "Portrait Camera"
       },
       {
         "type": "position_node",
         "node": "Portrait Camera",
         "position_relative_to": "subject",
         "offset": {"x": 0, "y": 160, "z": 250}
       },
       {
         "type": "call_tool",
         "tool": "daz_apply_lighting_preset",
         "args": {"preset": "three-point", "subject_label": "{{subject}}"}
       }
     ]
   }
   ```

2. **Template Execution Engine:**
   - Parse template JSON
   - Substitute slot variables ({{subject}})
   - Execute actions sequentially
   - Return status and created nodes

3. **Template Library:**
   - Ship with 5-10 built-in templates
   - Allow users to save custom templates
   - Community template sharing (future)

---

### Scene Validation
**Challenge:** What constitutes a "good" scene is subjective

**Solution:**
1. **Objective Checks (Always Apply):**
   - Collision detection (bounding box overlap)
   - Lighting present (at least 1 light or environment enabled)
   - Camera framing (subject in frame)
   - Technical issues (clipping, out-of-bounds)

2. **Stylistic Checks (Optional/Informational):**
   - Composition rules (thirds, golden ratio)
   - Lighting ratios (3:1 key-to-fill)
   - Color temperature consistency
   - Headroom/looking room

3. **Scoring System:**
   - Technical: 40% weight (critical issues)
   - Lighting: 30% weight (quality indicator)
   - Composition: 20% weight (aesthetic)
   - Character: 10% weight (spacing, poses)

4. **Configurable Thresholds:**
   - Users can adjust validation sensitivity
   - Professional vs. casual modes

---

## Success Metrics

### Phase 1 Success Criteria
- [ ] LLM can query node properties without documentation lookup (95% success rate)
- [ ] Spatial queries return accurate world-space coordinates
- [ ] Collision detection identifies overlapping nodes
- [ ] Three-point lighting produces professional results in blind test
- [ ] Scene validation catches 80%+ of common issues

### Phase 2 Success Criteria
- [ ] Emotional state produces recognizable expressions (user survey: 4/5 stars)
- [ ] Content browsing allows navigation without file paths
- [ ] Checkpoint system enables risk-free experimentation
- [ ] Composition rules improve framing quality (measured by photography principles)
- [ ] Users can complete "create portrait" task 50% faster

### Phase 3 Success Criteria
- [ ] Semantic search finds relevant content in 90% of queries
- [ ] Scene templates create usable scenes in <1 minute
- [ ] Auto-improve increases scene validator scores by 15+ points
- [ ] Mood lighting transforms atmosphere (user survey confirms mood recognition)
- [ ] Body language adjustments are recognizable in blind test

### Phase 4 Success Criteria
- [ ] Scene generation from description creates relevant scenes 75% of time
- [ ] Conversation choreography produces natural-looking interactions
- [ ] Macro system enables workflow reuse (80% of power users adopt)
- [ ] Natural language editing handles simple instructions correctly

---

## Risk Assessment

### High Risk
1. **Semantic Search Complexity**
   - **Risk:** Indexing infrastructure may be too complex for initial release
   - **Mitigation:** Start with simple text search, upgrade to semantic later
   - **Fallback:** Category browser + manual search

2. **Emotional State Subjectivity**
   - **Risk:** Emotion mappings may not match user expectations
   - **Mitigation:** Make mappings editable, gather user feedback
   - **Fallback:** Provide multiple emotion "styles" (subtle, exaggerated)

3. **Scene Generation Accuracy**
   - **Risk:** NL scene generation may produce poor results
   - **Mitigation:** Start with constrained templates, expand gradually
   - **Fallback:** Template-based approach with parameters

### Medium Risk
4. **Performance with Large Scenes**
   - **Risk:** Spatial queries slow on scenes with 1000+ nodes
   - **Mitigation:** Implement caching, limit scope to relevant nodes
   - **Fallback:** Add timeout warnings, progressive results

5. **Content Library Variations**
   - **Risk:** User libraries vary widely in organization
   - **Mitigation:** Support multiple directory structures, flexible parsing
   - **Fallback:** Manual path configuration option

### Low Risk
6. **API Coverage Gaps**
   - **Risk:** Some DAZ features not accessible via DazScript
   - **Mitigation:** Document limitations clearly, provide workarounds
   - **Fallback:** UI instructions for manual steps

---

## Next Steps

### Immediate Actions (Week 1)
1. **Set up Phase 1 branch:** `git checkout -b phase-1-spatial-api`
2. **Create tool stubs:** Empty functions for Phase 1 tools with docstrings
3. **Write DazScript prototypes:** Test spatial queries in DAZ Studio manually
4. **Design test suite:** Define test cases for each spatial query tool
5. **Update CLAUDE.md:** Add new tools to documentation

### Week 2-3
- Implement and test all Phase 1 tools
- Update test coverage to 80%+
- Write usage examples
- Gather initial user feedback

### Week 4+
- Begin Phase 2 based on Phase 1 learnings
- Iterate on Phase 1 tools based on user feedback
- Plan Phase 3 infrastructure (semantic search)

---

## Questions for Next Session

1. **Prioritization:** Does Phase 1 focus match your immediate needs?
2. **Semantic Search:** Should we start with simple text search or commit to full semantic search in Phase 3?
3. **Emotional State:** Do you have access to FACS data or emotion research to inform morph mappings?
4. **Scene Templates:** What are the top 5 scene types users create most often?
5. **Content Library:** What is the typical size of user content libraries (number of files)?
6. **Performance:** What is acceptable latency for spatial queries? (current: ~100ms per query)
7. **Testing:** Do you have a DAZ Studio test environment for CI/CD integration?

---

## Appendix: Tool Quick Reference

### Phase 1 Tools (10)
1. `daz_get_world_position` - Get node world-space coordinates
2. `daz_get_bounding_box` - Get node bounding box dimensions
3. `daz_calculate_distance` - Calculate distance between two nodes
4. `daz_get_spatial_relationship` - Natural language spatial relationship
5. `daz_check_overlap` - Detect node collision/overlap
6. `daz_inspect_properties` - List all properties on a node with metadata
7. `daz_get_property_metadata` - Get detailed property information
8. `daz_validate_scene` - Check scene for issues and provide suggestions
9. `daz_apply_lighting_preset` - Apply professional lighting setups
10. `daz_validate_script` - Pre-flight script validation (optional)

### Phase 2 Tools (11)
11. `daz_set_emotion` - Apply emotional state to character
12. `daz_get_content_info` - Query content file metadata
13. `daz_list_categories` - List content library categories
14. `daz_browse_category` - Browse content in category
15. `daz_apply_composition_rule` - Apply photography composition rules
16. `daz_frame_shot` - Frame camera by shot type
17. `daz_apply_camera_angle` - Apply cinematic camera angles
18. `daz_save_scene_state` - Save scene checkpoint
19. `daz_restore_scene_state` - Restore scene checkpoint
20. `daz_list_checkpoints` - List available checkpoints
21. `daz_get_scene_layout` - Get spatial map of entire scene
22. `daz_find_nearby_nodes` - Find nodes within radius

### Phase 3 Tools (7)
23. `daz_search_content` - Semantic content library search
24. `daz_check_compatibility` - Check content compatibility
25. `daz_set_mood_lighting` - Apply mood-based lighting
26. `daz_apply_time_of_day` - Apply time-of-day lighting
27. `daz_set_body_language` - Apply body language posture
28. `daz_direct_gaze` - Direct character gaze
29. `daz_apply_scene_template` - Apply pre-built scene template
30. `daz_auto_improve_scene` - Automatically fix scene issues
31. `daz_suggest_next_action` - Context-aware suggestions

### Phase 4 Tools (5)
32. `daz_create_scene` - Generate scene from natural language
33. `daz_create_shot_sequence` - Create multi-camera shot sequence
34. `daz_animate_conversation` - Choreograph conversation animation
35. `daz_start_recording` - Start macro recording
36. `daz_replay_macro` - Replay recorded macro

**Total New Tools:** 36 tools across 4 phases

---

*End of Implementation Plan*
