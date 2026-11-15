# Scene recipes

A scene recipe is a JSON document describing a scene declaratively: assets,
actors, props, lighting, cameras, shots and render settings. Apply is
idempotent and only touches nodes the recipe created, so you can iterate: edit
the recipe, apply again. The schema is the `daz://recipe/schema` resource.

## The loop

1. `daz_recipe_validate(recipe)` — fix every `errors` entry (`path`, `code`,
   `message`, `suggestion`) until `ok` is true. Also checks that referenced files exist.
2. `daz_recipe_plan(recipe)` — optional dry run: steps, conflicts, warnings.
3. `daz_recipe_apply(recipe)` — writes the scene. Returns `applied`.
4. `daz_recipe_render(recipe, shots=[...])` — renders the shots.
5. `daz_recipe_observe(recipe)` — any time: `in_sync`, `drift`, `pending`, `conflicts`.

Invalid recipes are returned as data (`{"ok": false, "errors": [...]}`), not as
tool errors: read them, fix the recipe, retry. A bad `on_conflict`, resolution
or shot id comes back as `{"ok": false, "error": "..."}`. Render refuses with
`{"ok": false, "reason": ..., "observe": {...}}` when the scene does not match
the recipe; apply first, or pass `force=true`.

## Conflicts (hand edits)

The user may move things in Studio between applies. For each channel the tool
compares recipe, last-applied base, and live scene:

- Only the live scene changed: a hand tweak, kept (warning `hand_tweak_kept`).
- Only the recipe changed: applied.
- Both changed: a **conflict**. Each has `path` (`<entity>.<channel>`, e.g.
  `cameras.close_up.transform`, `actors.model.pose`,
  `lighting.rigs.main.key.transform`), `kind`, and `desired` / `base` / `live`.
  Kinds include `removed_from_recipe`, `deleted_in_scene`, `has_foreign_children`.

Channels: actors `transform`/`pose`; props `transform`; cameras
`transform`/`optics`; lights and rig lights `transform`/`output`; environment
`environment`.

`on_conflict` policy:

| Value | Meaning |
|---|---|
| `ask` (default) | Any conflict writes nothing; conflicts are returned |
| `recipe_wins` | Overwrite hand edits |
| `scene_wins` | Keep hand edits (adopted as the new base) |

Follow the user's remembered preference: "always override" -> `recipe_wins`,
"always defer" -> `scene_wins`. Otherwise use `ask`, show the user each
conflict (what the recipe wants vs what is in the scene), and re-call apply with
`resolutions`, mapping each conflict path to `"recipe"` or `"scene"`:

```json
{"resolutions": {"lighting.rigs.main.key.transform": "recipe",
                 "actors.model.pose": "scene"}}
```

A `resolutions` key matching no conflict gives an `unknown_resolution` warning.
Resolving `deleted_in_scene` with `scene` records a tombstone; later applies
warn `hand_deleted_kept` until you resolve that path with `recipe`.

## Worked example

```json
{
  "recipe_version": 1,
  "id": "g9-portrait",
  "assets": { "g9": { "path": "/People/Genesis 9/Genesis 9.duf" } },
  "actors": {
    "model": {
      "asset": "g9",
      "position": [0, 0, 0],
      "pose": "/People/Genesis 9/Poses/Base Poses/Base Pose Standing.duf"
    }
  },
  "lighting": {
    "rigs": { "main": { "type": "three_point", "target": "model", "light_type": "spot" } }
  },
  "cameras": {
    "full_body": { "frame": "model", "shot_type": "full_body", "focal_length": 50 },
    "close_up":  { "frame": "model", "shot_type": "close_up", "azimuth_deg": 20, "focal_length": 85 }
  },
  "shots": [
    { "id": "full_body", "camera": "full_body", "output": "C:/temp/recipe_example/full_body.png" },
    { "id": "close_up",  "camera": "close_up",  "output": "C:/temp/recipe_example/close_up.png" }
  ],
  "render": { "engine": "iray", "resolution": [640, 480], "iray_samples": 50 }
}
```

Validate, apply, render. Later the user nudges the key light by hand and you
change the recipe's close-up `azimuth_deg` to 35: observe reports the drift;
apply keeps the hand-moved light (hand tweak) and applies the camera change.
If you changed that light in the recipe too, apply under `ask` returns a
conflict at `lighting.rigs.main.key.transform`: ask the user, then send
`resolutions`.
