"""Shared emotion, posture and bone-role definitions.

Used by tools/morph.py (daz_set_emotion, daz_set_body_language,
daz_direct_gaze) and tools/cinematic.py (shot/story tools that reason about
emotional expression); centralized here so the copies cannot drift.

Each emotion has:

- ``face``: full-face expression controllers, tried in order (Genesis 9 FACS,
  then the Genesis 8 HD expression pack, then base Genesis 8). When one
  resolves, it carries the whole expression and the ``morphs`` slots are
  skipped, so the two never stack.
- ``morphs``: per-feature slots ``{names: [...], value}``; the first name that
  resolves on the figure wins. Stock Genesis 9 (``facs_ctrl_*``) and Genesis 8
  (``eCTRL*``) controller names come first, then older names.
- ``body``: bone adjustments keyed by Genesis 8 bone names; see
  ``BONE_CANDIDATES`` for the per-generation equivalents.

Stock names verified live on Genesis 9 and Genesis 8 Female, DS 4.24
(2026-11-24).
"""
from __future__ import annotations

_EMOTION_DEFINITIONS: dict[str, dict] = {
    "happy": {
        "face": ["facs_ctrl_Happy", "eCTRLHappy_HD", "eCTRLHappy"],
        "morphs": [
            {
                "names": [
                    "eCTRLMouthSmile", "PHMSmile", "Smile", "CTRLSmile", "MouthSmile",
                    "SmileSimple",
                ],
                "value": 0.85,
            },
            {
                "names": [
                    "facs_ctrl_EyeSquint", "PHMEyesSquint", "EyesSquint", "EyeSquintL",
                    "SquintEyes",
                ],
                "value": 0.25,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": 3.0},
        ],
    },
    "sad": {
        "face": ["facs_ctrl_Sad", "eCTRLSad_HD", "eCTRLSad"],
        "morphs": [
            {
                "names": [
                    "facs_ctrl_MouthFrown", "eCTRLMouthFrown", "PHMFrown", "Frown", "MouthFrown",
                    "CTRLFrown", "FrownSimple",
                ],
                "value": 0.75,
            },
            {
                "names": [
                    "facs_ctrl_BrowInnerUp", "PHMBrowInnerDown", "BrowDownL", "BrowDown",
                    "CTRLBrowDown", "BrowInnerDown",
                ],
                "value": 0.6,
            },
            {
                "names": ["facs_ctrl_EyeSquint", "PHMEyesSquint", "EyesSquint", "EyeSquintL"],
                "value": 0.3,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": -6.0},
        ],
    },
    "angry": {
        "face": ["facs_ctrl_Angry", "eCTRLAngry_HD", "eCTRLAngry"],
        "morphs": [
            {
                "names": [
                    "facs_ctrl_MouthFrown", "eCTRLMouthFrown", "PHMFrown", "Frown", "MouthFrown",
                    "CTRLFrown",
                ],
                "value": 0.5,
            },
            {
                "names": [
                    "facs_ctrl_BrowDown", "PHMBrowDown", "BrowDown", "BrowDownLeft",
                    "CTRLBrowDown", "BrowDownR",
                ],
                "value": 0.85,
            },
            {
                "names": [
                    "facs_ctrl_NoseSneer", "eCTRLNoseWrinkle", "PHMNoseWrinkle", "NoseWrinkle",
                    "NoseSneerL", "NoseSneer",
                ],
                "value": 0.4,
            },
            {
                "names": ["PHMEyesTighten", "EyesTighten", "EyeSquintL", "CheekSquintL"],
                "value": 0.4,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": -3.0},
        ],
    },
    "surprised": {
        "face": ["facs_ctrl_Surprised", "eCTRLSurprised_HD", "eCTRLSurprised"],
        "morphs": [
            {
                "names": [
                    "facs_ctrl_BrowUp", "PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp",
                    "BrowsUp",
                ],
                "value": 0.85,
            },
            {
                "names": ["facs_ctrl_EyeWide", "PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"],
                "value": 0.75,
            },
            {
                "names": [
                    "eCTRLMouthOpen", "PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen",
                ],
                "value": 0.6,
            },
        ],
        "body": [],
    },
    "fearful": {
        "face": ["facs_ctrl_Fear", "eCTRLFear_HD", "eCTRLFear"],
        "morphs": [
            {
                "names": ["facs_ctrl_BrowUp", "PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp"],
                "value": 0.7,
            },
            {
                "names": ["facs_ctrl_EyeWide", "PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"],
                "value": 0.6,
            },
            {
                "names": [
                    "eCTRLMouthOpen", "PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen",
                ],
                "value": 0.3,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": -4.0},
        ],
    },
    "disgusted": {
        "face": ["facs_ctrl_Disgust", "eCTRLDisgust_HD", "eCTRLDisgust"],
        "morphs": [
            {
                "names": [
                    "facs_ctrl_NoseSneer", "eCTRLNoseWrinkle", "PHMNoseWrinkle", "NoseWrinkle",
                    "NoseSneerL", "NoseSneer",
                ],
                "value": 0.75,
            },
            {
                "names": [
                    "facs_ctrl_MouthFrown", "eCTRLMouthFrown", "PHMFrown", "Frown", "MouthFrown",
                    "CTRLFrown",
                ],
                "value": 0.4,
            },
            {
                "names": [
                    "facs_ctrl_MouthUpperUp", "PHMUpperLipUp", "UpperLipUp", "MouthUpperUp_L",
                    "LipUpperUp_L",
                ],
                "value": 0.3,
            },
        ],
        "body": [],
    },
    "neutral": {
        "morphs": [],
        "body": [],
    },
    "excited": {
        "face": ["facs_ctrl_Excitement", "eCTRLExcitement_HD"],
        "morphs": [
            {
                "names": ["eCTRLMouthSmile", "PHMSmile", "Smile", "CTRLSmile", "MouthSmile"],
                "value": 1.0,
            },
            {
                "names": ["facs_ctrl_BrowUp", "PHMBrowUp", "BrowUp", "CTRLBrowUp", "BrowsUp"],
                "value": 0.5,
            },
            {
                "names": ["facs_ctrl_EyeWide", "PHMEyesWide", "EyesWide", "EyeOpenL"],
                "value": 0.4,
            },
            {
                "names": [
                    "eCTRLMouthOpen", "PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen",
                ],
                "value": 0.4,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": 5.0},
        ],
    },
    "bored": {
        "face": ["facs_ctrl_Bored", "eCTRLBored_HD"],
        "morphs": [
            {
                "names": [
                    "facs_ctrl_EyeBlink", "eCTRLEyesClosed", "PHMEyesClosed", "EyesClosed",
                    "EyeClosedL", "CTRLEyesClosed",
                ],
                "value": 0.4,
            },
            {
                "names": [
                    "facs_ctrl_MouthFrown", "eCTRLMouthFrown", "PHMFrown", "Frown", "MouthFrown",
                ],
                "value": 0.2,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": -4.0},
        ],
    },
    "confident": {
        "face": ["facs_ctrl_Confident", "eCTRLConfident_HD"],
        "morphs": [
            {
                "names": ["eCTRLMouthSmile", "PHMSmile", "Smile", "MouthSmile", "CTRLSmile"],
                "value": 0.3,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": 4.0},
        ],
    },
    "shy": {
        "morphs": [
            {
                "names": ["eCTRLMouthSmile", "PHMSmile", "Smile", "MouthSmile"],
                "value": 0.2,
            },
            {
                "names": ["facs_ctrl_EyeSquint", "PHMEyesSquint", "EyesSquint", "EyeSquintL"],
                "value": 0.15,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": -5.0},
        ],
    },
    "loving": {
        "morphs": [
            {
                "names": ["eCTRLMouthSmile", "PHMSmile", "Smile", "MouthSmile", "CTRLSmile"],
                "value": 0.6,
            },
            {
                "names": ["facs_ctrl_EyeSquint", "PHMEyesSquint", "EyesSquint", "EyeSquintL"],
                "value": 0.35,
            },
        ],
        "body": [
            {"bone": "chestUpper", "property": "XRotate", "value": 2.0},
        ],
    },
    "contemptuous": {
        "face": ["facs_ctrl_Contempt", "eCTRLContempt_HD"],
        "morphs": [
            {
                "names": [
                    "eCTRLMouthSmileSimpleR", "PHMSmileR", "SmileR", "MouthSmileR", "MouthSmile_R",
                ],
                "value": 0.5,
            },
            {
                "names": ["PHMFrownL", "FrownL", "MouthFrownL", "MouthFrown_L"],
                "value": 0.3,
            },
        ],
        "body": [],
    },
}

BONE_CANDIDATES: dict[str, tuple[str, ...]] = {
    # Genesis 3/8 name first, then Genesis 9, then Genesis 1/2. Axis
    # conventions match across these (verified live: +X on chestUpper and
    # spine4 tips the head forward by the same amount; -Z on lShldrBend and
    # l_upperarm lowers the arm identically).
    "hip": ("hip",),
    "chestLower": ("chestLower", "spine3"),
    "chestUpper": ("chestUpper", "spine4"),
    "abdomenLower": ("abdomenLower", "spine1"),
    "neckLower": ("neckLower", "neck1"),
    "neckUpper": ("neckUpper", "neck2"),
    "head": ("head",),
    "lEye": ("lEye", "l_eye"),
    "rEye": ("rEye", "r_eye"),
    "lShldr": ("lShldrBend", "l_upperarm", "lShldr"),
    "rShldr": ("rShldrBend", "r_upperarm", "rShldr"),
}
"""Role (Genesis 8 bone name) -> bone names to try on the figure, in order."""

AXIS_BY_PROPERTY: dict[str, str] = {"XRotate": "x", "YRotate": "y", "ZRotate": "z"}

POSTURES: dict[str, list[dict]] = {
    "confident": [
        {"bone": "chestUpper", "property": "XRotate", "value": 5.0},
        {"bone": "lShldr", "property": "ZRotate", "value": -5.0},
        {"bone": "rShldr", "property": "ZRotate", "value": 5.0},
    ],
    "defensive": [
        {"bone": "chestUpper", "property": "XRotate", "value": -8.0},
        {"bone": "abdomenLower", "property": "XRotate", "value": -3.0},
        {"bone": "lShldr", "property": "ZRotate", "value": 10.0},
        {"bone": "rShldr", "property": "ZRotate", "value": -10.0},
    ],
    "relaxed": [
        {"bone": "chestUpper", "property": "XRotate", "value": -3.0},
        {"bone": "lShldr", "property": "ZRotate", "value": 4.0},
        {"bone": "rShldr", "property": "ZRotate", "value": -4.0},
        {"bone": "neckLower", "property": "XRotate", "value": 2.0},
    ],
    "tense": [
        {"bone": "chestUpper", "property": "XRotate", "value": 4.0},
        {"bone": "lShldr", "property": "ZRotate", "value": -12.0},
        {"bone": "rShldr", "property": "ZRotate", "value": 12.0},
        {"bone": "neckLower", "property": "XRotate", "value": -3.0},
    ],
}


def resolve_bone(role: str, bone_names: set[str] | list[str]) -> str | None:
    """Return the figure's bone for *role* (a Genesis 8 bone name), or None."""
    present = set(bone_names)
    for candidate in BONE_CANDIDATES.get(role, (role,)):
        if candidate in present:
            return candidate
    return None
