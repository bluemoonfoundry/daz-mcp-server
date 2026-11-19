# Skill: Cinematographer & Director
Tools for visual storytelling and rendering.

## Camera Control
- `daz_orbit_camera_around`: Spherical positioning.
- `daz_frame_shot`: Cinematic presets (`close-up`, `full-shot`, etc.).
- `daz_apply_camera_angle`: Standard angles (`low-angle`, `eye-level`).
- `daz_apply_composition_rule`: `rule-of-thirds`, `golden-ratio`.

## Lighting
- `daz_apply_lighting_preset`: `three-point`, `rembrandt`, `butterfly`, `split`.
- `daz_set_mood_lighting`: Atmospheric mood (`romantic`, `tense`, `hopeful`, `dramatic`).
- `daz_apply_time_of_day`: Time simulation (`dawn`, `morning`, `noon`, `golden-hour`, `dusk`, `night`).
- `daz_list_lights` / `daz_create_light`: Enumerate or create lights by type.
- Lights positioned relative to subject's bounding box.

## Animation
- `daz_set_keyframe`, `daz_set_frame_range`.
- `daz_animate_camera_movement`: `dolly-in`, `pan-left`, `handheld-shake`.
- `daz_create_camera_path`: Keys the camera at each waypoint (Studio interpolates); `aim_at_target` keeps it aimed at a node on every key.

## Production & Rendering
- `daz_render_animation`: Batch render frame sequences.
- `daz_batch_render_cameras`: Multi-angle product/portrait renders.
- `daz_setup_shot_coverage`: Single-subject coverage presets (`standard`, `interview`, `dramatic`, `action`).
- `daz_create_shot_sequence`: Establishing → medium → close-up, shot/reverse-shot (180-degree rule kept, `side` picks the side), orbit, push-in.
- `daz_create_camera_rig`: Ring of cameras aimed at a centre, parented to a `<name>_Rig` group (rotate it to orbit them all); re-running reuses the rig.
- `daz_plan_shot`: Read-only plan — camera pose, lens, lighting and the `shot` (a `dazpy.shots.Shot` dict) without touching the scene.
- `daz_create_storyboard`: One camera per shot with contiguous frame ranges; returns the board as a `dazpy.shots.Sequence` dict.
- `daz_create_scene`: Template lights/blocking (script) plus template coverage cameras from `dazpy.shot_library`.

## Conventions
- Shots come from `dazpy.shot_library`; cameras are labelled with shot ids (`CU_Alice`, `OTS_Bob_over_Alice`).
- Two-person coverage keeps every camera on one side of the line between the actors so eyelines match across cuts.
- Shot sizes fit the camera's current lens; set the lens first if it matters.
- Azimuth 0 is the subject's front (`+Z`, where Genesis figures face); 90 is its `+X` side.
