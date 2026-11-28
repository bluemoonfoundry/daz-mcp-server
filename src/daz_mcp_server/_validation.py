"""Pre-render scene validation for daz_validate_scene / daz_auto_improve_scene.

Lighting and framing come from dazpy's ``DazScene.check``; figure collisions
(world bounding-box overlap between top-level figures) and the 0-100 score
are computed here.
"""
from __future__ import annotations

from typing import Any

import dazpy.exceptions as daz_exc

_FINDING_SUGGESTIONS = {
    "no_light": "Use daz_apply_lighting_preset('three-point') to add lights",
    "no_subject_in_frame": "Aim the camera at a figure (daz_frame_shot / daz_plan_shot)",
    "subject_not_in_frame": "Re-aim or widen the camera so the figure is in frame",
    "subject_out_of_frame": "Widen the shot or move the camera back if the crop is unintended",
    "camera_not_found": "Pick an existing camera (daz_list_cameras)",
}


def _boxes_overlap(a: dict, b: dict) -> float | None:
    """Smallest overlap depth of two world AABBs, or None if they don't intersect."""
    depths = [min(a["max"][k], b["max"][k]) - max(a["min"][k], b["min"][k]) for k in "xyz"]
    return min(depths) if all(d > 0 for d in depths) else None


def _collisions(scene: Any, figures: list[dict]) -> list[dict]:
    """A collision issue per pair of top-level figures whose world AABBs overlap."""
    boxes = []
    for fig in figures:
        try:
            box = scene.resolve_node(fig["label"]).bounding_box()
        except (daz_exc.NodeNotFoundError, daz_exc.AmbiguousNodeError):
            continue  # duplicate labels: skip rather than guess which figure
        if box:
            boxes.append((fig["label"], box))
    found = []
    for i, (la, ba) in enumerate(boxes):
        for lb, bb in boxes[i + 1:]:
            depth = _boxes_overlap(ba, bb)
            if depth is not None:
                found.append({
                    "type": "collision", "severity": "high", "nodes": [la, lb],
                    "description": f"{la} and {lb} bounding boxes overlap by ~{round(depth)} cm",
                    "suggestion": "Move one character away to resolve interpenetration"})
    return found


def validate_scene(scene: Any) -> dict[str, Any]:
    """Pre-render validation: dazpy's scene check plus figure collisions."""
    overview = scene.overview()
    report = scene.check()
    figures = overview.get("figures", [])  # top-level only (no eyelashes etc.)
    num_lights = len(overview.get("lights", []))
    num_cameras = len(overview.get("cameras", []))

    issues: list[dict] = []
    warnings: list[dict] = []
    for finding in report.findings:
        entry = {"type": finding.code,
                 "severity": "high" if finding.severity == "error" else "medium",
                 "nodes": [finding.subject] if finding.subject not in ("", "scene") else [],
                 "description": finding.message,
                 "suggestion": _FINDING_SUGGESTIONS.get(finding.code, "")}
        (issues if finding.severity == "error" else warnings).append(entry)

    collisions = _collisions(scene, figures)
    issues.extend(collisions)

    lit = not any(finding.code == "no_light" for finding in report.findings)
    if lit and num_lights == 1:
        warnings.append({"type": "poor-lighting", "severity": "medium",
                         "description": "Scene has only one light source, may cause harsh shadows",
                         "suggestion": "Add a fill light at low intensity to soften shadows"})
    if num_cameras == 0:
        warnings.append({"type": "no-camera", "severity": "medium",
                         "description": "Scene has no cameras (will use the viewport camera)",
                         "suggestion": "Add a camera with daz_create_camera"})
    if not figures:
        warnings.append({"type": "no-figures", "severity": "low",
                         "description": "Scene has no figures/characters",
                         "suggestion": "Load a character with daz_load_file()"})

    breakdown = {
        "lighting": 0 if not lit else (50 if num_lights == 1 else 100),
        "collision": 30 if collisions else 100,
        "camera": 100 if num_cameras else 60,
        "figures": 100 if figures else 60,
    }
    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "score": round(sum(breakdown.values()) / 4),
        "score_breakdown": breakdown,
        "summary": {"figures": len(figures), "cameras": num_cameras, "lights": num_lights,
                    "lit": lit},
        "findings": [finding.to_dict() for finding in report.findings],
    }
