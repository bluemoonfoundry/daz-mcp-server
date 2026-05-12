# Skill: Character Choreographer
Tools for morphs, emotions, and movement.

## Morph Discovery
- `daz_list_morphs`: Use `include_zero=False` to see active morphs.
- `daz_search_morphs`: Pattern match (e.g., "smile", "muscle").

## Emotional Direction
- `daz_set_emotion`: Apply `happy`, `angry`, `confident`, etc., with `intensity`.
- Handles naming differences between Genesis 8 and 9.

## Posing & Interaction
- `daz_look_at_character`, `daz_look_at_point`: Cascading rotation (eyes to torso).
- `daz_reach_toward`: Pseudo-IK for arms.
- `daz_interactive_pose`: Pre-built handshake, hug, or fight spacing.

## Action & Pathing
- `daz_create_character_path`: Animate walking with auto-rotation.
- `daz_arrange_characters`: Formations (semicircle, circle, line).
- `daz_choreograph_action`: Coordinated multi-character sequences.
