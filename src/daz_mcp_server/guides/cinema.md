# Skill: Cinematographer & Director
Tools for visual storytelling and rendering. The tools named here are in the
`expert` profile (`DAZ_MCP_PROFILE=expert`); each tool's own description lists
its exact arguments and values. In the compact profile, cameras and shots go
through a scene recipe (daz://guide/recipe).

## Camera Control
- `daz_frame_shot`: Frame a subject at a shot size (`extreme-close-up` … `extreme-wide`), fitted to the camera's lens and aimed at the right height (eyes for a close-up). Prefer this to manual placement.
- `daz_orbit_camera_around`: Spherical positioning; aims at the target's root (a figure's feet), so follow with `daz_frame_shot` for portraits.
- `daz_apply_camera_angle`: `eye-level`, `high-angle`, `low-angle`, `dutch-angle`, `overhead`, `worms-eye`, `over-shoulder`.
- `daz_apply_composition_rule`: `rule-of-thirds`, `golden-ratio`, `center-frame`, `leading-lines`.
- `daz_set_focus_point` / `daz_animate_focus_pull`: Focus on a target (a figure's eyes) or a distance; `dofPreview` gives the sharp range.
- `daz_plan_shot`, `daz_create_storyboard`: Plan shots and storyboards before creating cameras.

## Lighting
- `daz_apply_lighting_preset`: Creates a rig: `three-point`, `rembrandt`, `butterfly`, `split`, `loop`.
- `daz_set_mood_lighting`: Adjusts existing lights to a mood (`romantic`, `dramatic`, `scary`, `golden-hour`, `mysterious`, `peaceful`).
- `daz_apply_time_of_day`: Adjusts existing lights to a time (`dawn`, `morning`, `noon`, `golden-hour`, `dusk`, `night`).
- `daz_list_lights` / `daz_create_light`: Enumerate or create lights by type.
- Lights positioned relative to subject's bounding box.

## Animation
- `daz_set_keyframe`, `daz_set_frame_range`.
- `daz_animate_camera_movement`: `dolly-in`/`-out`, `pan-left`/`-right`, `tilt-up`/`-down`, `crane-up`/`-down`, `handheld-shake`; keys outside the move are kept, so moves chain.
- `daz_create_camera_path`: Keys the camera at each waypoint (Studio interpolates); `aim_at_target` keeps it aimed at a node on every key.

## Production & Rendering
- `daz_render_animation`: Batch render frame sequences.
- `daz_batch_render_cameras`: Multi-angle product/portrait renders.
- `daz_setup_shot_coverage`: Single-subject coverage presets (`standard`, `interview`, `dramatic`, `action`).
- `daz_cover_conversation`: Two-person dialogue — cut one OTS/single shot per `beats` entry (`{speaker, start, end, line}`, optional opening master via `establish_frames`) and get the `cutList`, or omit `beats` for master/two-shot/OTS/singles coverage. Every camera stays on one side of the line; `continuity` reports axis crossings and jump cuts.
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
