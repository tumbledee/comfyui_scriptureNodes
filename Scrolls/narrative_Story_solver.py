"""
storyCollapse — "story Collapse" node
Merges story + SCENE + CHARACTER[] + QUALITY into sampler-ready prompts.

Sub-systems
───────────
1. story resolver   : expands story line → wildcard files in storys/ folder
2. Action parser        : "girl1:hugging:girl2:boy1" → per-character action prompts
3. Scene variable resolver : {sittingObject} tokens replaced with scene-defined values
4. Character resolver   : counts → "2girls, 1boy"; character_value → weight adjustments
5. LoRA injector        : collects from SCENE lora_tags, appends to end
6. BREAK assembler      : inserts BREAK tokens between semantic sections to reduce bleeding
7. Debug preview        : full human-readable breakdown
"""

# Future Ideas
# - Dynamic Block system 
#     in Settings Each block can be defined with the aformentioned sub systems
# 
# 
# 
# 
# 
# 

import os
import re
import json
import random
from collections import Counter, defaultdict
from .lib.file_io import save_json, load_json, load_text_lines
from .lib.settings import get_root_directory
# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
# _NODE_DIR       = os.path.dirname(os.path.abspath(__file__))
_NODE_DIR = get_root_directory
#WILDCARDS_DIR   = os.environ.get(
#    "WILDCARDS_PATH",
#    os.path.join(_NODE_DIR, "..", "..", "wildcards"),
#)
#storyS_DIR  = os.path.join(WILDCARDS_DIR, "storys")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Wildcard / story file resolver
# ─────────────────────────────────────────────────────────────────────────────
_wc_cache: dict[str, list[str]] = {}

def _load_lines(path: str) -> list[str]:
    if path in _wc_cache:
        return _wc_cache[path]
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        _wc_cache[path] = lines
        return lines
    _wc_cache[path] = []
    return []

def _wildcard_path(name: str) -> str:
    return os.path.join(WILDCARDS_DIR, f"{name}.txt")

def resolve_wildcards(text: str, rng: random.Random, depth: int = 0) -> str:
    """Recursively expand __wildcard__ tokens."""
    if depth > 16 or not text:
        return text
    def _sub(m):
        lines = _load_lines(_wildcard_path(m.group(1)))
        return resolve_wildcards(rng.choice(lines), rng, depth + 1) if lines else m.group(0)
    return re.sub(r"__([a-zA-Z0-9_/\-]+)__", _sub, text)


def resolve_story_line(line: str, rng: random.Random) -> str:
    """
    Expand a story line.
    1. If the line is a bare filename token (no spaces, no commas) we look for
       wildcards/storys/<token>.txt and pick a random entry from it.
    2. Then run standard wildcard expansion on the result.
    """
    bare = line.strip()
    if bare and " " not in bare and "," not in bare:
        candidate = os.path.join(storyS_DIR, f"{bare}.txt")
        lines = _load_lines(candidate)
        if lines:
            bare = rng.choice(lines)
    return resolve_wildcards(bare, rng)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Action parser
# Syntax: "identifier:action:target1:target2:..."
# The acting character gets "(action another, ...)"
# Each target gets "(being [action])"
# Multiple action blocks separated by " | "
#
# Example: "girl1:hugging:girl2:boy1 | boy1:looking at:girl1"
# ─────────────────────────────────────────────────────────────────────────────

def parse_actions(action_str: str, id_map: dict) -> dict[str, list[str]]:
    """
    Returns {identifier: [action_fragment, ...]} for all involved characters.
    """
    results: dict[str, list[str]] = defaultdict(list)
    if not action_str.strip():
        return results

    for block in re.split(r"\s*\|\s*", action_str):
        parts = [p.strip() for p in block.split(":") if p.strip()]
        if len(parts) < 2:
            continue
        actor   = parts[0]
        action  = parts[1]
        targets = parts[2:]

        # Resolve target display names (use character field if available)
        target_labels = []
        for t in targets:
            char = id_map.get(t, {})
            label = char.get("character") or t
            target_labels.append(label)

        if target_labels:
            results[actor].append(f"{action} {', '.join(target_labels)}")
        else:
            results[actor].append(action)

        for t in targets:
            results[t].append(f"being {action}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 3. Scene variable resolver
# Scene dict may carry a "scene_variables" sub-dict: {"sittingObject": "couch", ...}
# Also auto-populates from the scene text using heuristics (see _infer_scene_vars).
# Token syntax in story/character text: {varName}
# ─────────────────────────────────────────────────────────────────────────────

_SCENE_KEYWORD_VARS = {
    # location keyword → {varName: default}
    "living room":  {"sittingObject": "couch",     "lyingObject": "carpet",   "table": "coffee table"},
    "bedroom":      {"sittingObject": "bed",        "lyingObject": "bed",      "table": "nightstand"},
    "kitchen":      {"sittingObject": "bar stool",  "lyingObject": "floor",    "table": "kitchen counter"},
    "park":         {"sittingObject": "bench",      "lyingObject": "grass",    "table": "picnic table"},
    "office":       {"sittingObject": "office chair","lyingObject": "floor",   "table": "desk"},
    "beach":        {"sittingObject": "beach chair","lyingObject": "sand",     "table": "beach umbrella stand"},
    "classroom":    {"sittingObject": "desk chair", "lyingObject": "floor",    "table": "school desk"},
    "cafe":         {"sittingObject": "cafe chair", "lyingObject": "floor",    "table": "cafe table"},
    "bathroom":     {"sittingObject": "bathtub edge","lyingObject": "bathtub", "table": "sink counter"},
    "rooftop":      {"sittingObject": "ledge",      "lyingObject": "floor",    "table": "rooftop railing"},
}

def _infer_scene_vars(scene_text: str) -> dict[str, str]:
    """Infer scene variables by matching location keywords in scene text."""
    lower = scene_text.lower()
    for keyword, var_map in _SCENE_KEYWORD_VARS.items():
        if keyword in lower:
            return dict(var_map)
    return {}

def resolve_scene_vars(text: str, scene_vars: dict[str, str]) -> str:
    """Replace {varName} tokens with scene variable values."""
    def _sub(m):
        key = m.group(1)
        return scene_vars.get(key, m.group(0))
    return re.sub(r"\{([a-zA-Z0-9_]+)\}", _sub, text)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Character resolver
# ─────────────────────────────────────────────────────────────────────────────

_GENDER_LABELS = {
    "female": ("girl", "girls"),
    "male":   ("boy",  "boys"),
    "other":  ("person", "people"),
}

def build_gender_count_tag(gender_counts: dict) -> str:
    """{'female': 2, 'male': 1} → '2girls, 1boy'"""
    parts = []
    for gender, count in sorted(gender_counts.items()):
        singular, plural = _GENDER_LABELS.get(gender, ("person", "people"))
        label = singular if count == 1 else plural
        parts.append(f"{count}{label}")
    return ", ".join(parts)


def character_value_modifiers(char: dict, action_fragments: list[str]) -> str:
    """
    Returns extra prompt tokens driven by character_value.
    Negative  (<-0.4)  → subdued/shy adjustments
    Neutral   (-0.4 to 0.4) → no adjustment
    Positive  (>0.4)   → energetic/dominant adjustments
    Also applies action fragments with weight emphasis if value is extreme.
    """
    val = float(char.get("character_value", 0.0))
    fragments = []

    # Value-driven mood tokens
    if val < -0.6:
        fragments.append("(shy:1.1), looking away, timid posture")
    elif val < -0.2:
        fragments.append("reserved expression")
    elif val > 0.6:
        fragments.append("(confident:1.2), bold pose, intense gaze")
    elif val > 0.2:
        fragments.append("expressive pose")

    # Action fragments with weight scaling
    for af in action_fragments:
        weight = 1.0 + abs(val) * 0.3   # extreme values push weight up to ~1.3
        weight = round(min(weight, 1.5), 2)
        if weight > 1.05:
            fragments.append(f"({af}:{weight})")
        else:
            fragments.append(af)

    return ", ".join(fragments)


def build_character_prompt(char: dict, action_fragments: list[str], rng: random.Random) -> str:
    """Assemble per-character positive prompt block."""
    parts = []

    # Character description
    character_field = resolve_wildcards(char.get("character", ""), rng)
    if character_field:
        parts.append(character_field)

    # Character type (tsundere etc.)
    char_type = resolve_wildcards(char.get("character_type", ""), rng)
    if char_type:
        parts.append(char_type)

    # Physical features
    for field in ["hair", "face", "bodytype"]:
        val = resolve_wildcards(char.get(field, ""), rng)
        if val:
            parts.append(val)

    # Clothing (choose nude or clothing based on what's filled)
    clothing = resolve_wildcards(char.get("clothing", ""), rng)
    nude     = resolve_wildcards(char.get("nude", ""), rng)
    underwear = resolve_wildcards(char.get("underwear", ""), rng)
    if clothing:
        parts.append(clothing)
        if underwear:
            parts.append(underwear)
    elif nude:
        parts.append(nude)

    # Positive additional
    pos_add = resolve_wildcards(char.get("positive_additional", ""), rng)
    if pos_add:
        parts.append(pos_add)

    # Value modifiers + actions
    modifiers = character_value_modifiers(char, action_fragments)
    if modifiers:
        parts.append(modifiers)

    return ", ".join(p for p in parts if p)


# ─────────────────────────────────────────────────────────────────────────────
# 5. BREAK assembler
# Strategy:
#   [QUALITY POS]  BREAK
#   [GENDER COUNTS + SCENE style]  BREAK
#   [CHARACTER 1 block]  BREAK
#   [CHARACTER 2 block]  BREAK  ...
#   [SCENE environment + lighting + camera]  BREAK
#   [VFX + story line residual]  BREAK
#   [LORA TAGS]
# ─────────────────────────────────────────────────────────────────────────────

def assemble_with_breaks(sections: list[str], separator: str = " BREAK\n") -> str:
    """Join non-empty sections with BREAK tokens."""
    return separator.join(s.strip() for s in sections if s and s.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────

class narrative_story_Collapse_node:
    CATEGORY = "NarrativeSystem"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "characters": ("CHARACTER_COLLECTOR", {}),   # accepts list from collector OR single dict
                "story":  ("STORY", {}),
                "scene":      ("SCENE",     {}),
                "visuals":      ("VISUALS",     {}),
                "quality":    ("QUALITY",   {}),
            },
            "optional": {
                "positive_addition": ("STRING", {"default": "", "multiline": True}),
                "negative_addition": ("STRING", {"default": "", "multiline": True}),
                "wildcard_seed": ("INT", {
                    "default": -1, "min": -1, "max": 2*32,
                    "tooltip": "-1 = random each run",
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING",    "STRING",    "STRING")
    RETURN_NAMES = ("positive",  "negative",  "debug_preview")
    FUNCTION     = "collapse"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always re-run (wildcard seeds change each time if -1)
        return float("NaN")

    def collapse(
        self,
        characters,
        story,
        scene,
        visuals,
        quality,
        positive_addition="",
        negative_addition="",
        wildcard_seed=-1,
        unique_id=None,
    ):
        # ─────────────────────────────────────────────────────────────────────
        # STEP 0 — Initialise Quality
        # ─────────────────────────────────────────────────────────────────────
        try:
            wildcard_seed = int(wildcard_seed)
        except (TypeError, ValueError):
            wildcard_seed = -1
        seed = wildcard_seed if wildcard_seed >= 0 else random.randint(0, 2**32)
        rng  = random.Random(seed)

        # ── Normalise characters input (single dict OR list of dicts) ─────────
        #if characters is None:
        #    char_list = []
        #elif isinstance(characters, dict):
        #    char_list = [characters]
        #elif isinstance(characters, list):
        #    char_list = [c for c in characters if isinstance(c, dict)]
        #else:
        #    char_list = []

        #id_map = {c.get("identifier", f"char_{i}"): c for i, c in enumerate(char_list)}

        # ─────────────────────────────────────────────────────────────────────
        # STEP 1 — Resolve story line
        # ─────────────────────────────────────────────────────────────────────
        raw_story_line = story.get("current_positive", "")
        resolved_story = raw_story_line
        resolved_story_neg = story.get("current_negative", "")
        # resolved_story = resolve_story_line(raw_story_line, rng)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 2 — Build scene variables + resolve scene fields
        # ─────────────────────────────────────────────────────────────────────
        scene_text     = scene.get("scene",    "")
        scene_vars_raw = scene.get("scene_variables", {})      # explicit overrides
        #inferred_vars  = _infer_scene_vars(scene_text)
        #scene_vars     = {**inferred_vars, **scene_vars_raw}   # explicit wins
        resolved_scene    = scene_text
        resolved_lighting = scene.get("lighting", "")
        resolved_camera   = scene.get("camera", "")
        resolved_style    = scene.get("style", "")
        resolved_vfx      = scene.get("vfx", "")
        #resolved_scene    = resolve_scene_vars(resolve_wildcards(scene_text,              rng), scene_vars)
        #resolved_lighting = resolve_scene_vars(resolve_wildcards(scene.get("lighting",""), rng), scene_vars)
        #resolved_camera   = resolve_scene_vars(resolve_wildcards(scene.get("camera",""),   rng), scene_vars)
        #resolved_style    = resolve_scene_vars(resolve_wildcards(scene.get("style",""),    rng), scene_vars)
        #resolved_vfx      = resolve_scene_vars(resolve_wildcards(scene.get("vfx",""),      rng), scene_vars)

        # Apply scene vars to the story line too
        #resolved_story = resolve_scene_vars(resolved_story, scene_vars)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 3 — Parse actions
        # ─────────────────────────────────────────────────────────────────────
        #action_map = parse_actions(action_script, id_map)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 4 — Gender count tag
        # ─────────────────────────────────────────────────────────────────────
        #gender_count = characters.get("total_count", 0)
        gender_tag = characters.get("gender_prompt", "")
        #gender_counts: dict[str, int] = Counter()
        #for char in char_list:
        #    gender_counts[char.get("gender", "other")] += int(char.get("count", 1))
        #gender_tag = build_gender_count_tag(dict(gender_counts))
        

        # ─────────────────────────────────────────────────────────────────────
        # STEP 5 — Per-character blocks
        # ─────────────────────────────────────────────────────────────────────
        char_blocks     = []
        char_neg_parts  = []
        #for char in char_list:
        character = characters.get("characters", "")
        for char in character:
            char_pos = []
            
            character_value = char.get("character_value", 0)
            character_ident = char.get("identifier", "")
            character_gender = char.get("gender", "")
            char_pos.append(char.get("character", ""))
            char_pos.append(char.get("character_type", ""))
            char_pos.append(char.get("hair", ""))
            char_pos.append(char.get("face", ""))
            char_pos.append(char.get("bodytype", ""))
            
            # evaluate underwear and clothing; Contains nudism or exposed marker add sequential nudes, character value for extremes
            nudism = character_value = char.get("character_value", "")
            character_nude = char.get("nude", "")
            character_underwear = char.get("underwear", "")
            character_clothing = char.get("clothing", "")

            char_pos.append(char.get("nude", ""))
            char_pos.append(char.get("clothing", ""))
            char_pos.append(char.get("underwear", ""))
            char_pos.append(char.get("positive_additional", ""))
            character_block = ", ".join(char_pos)

            char_blocks.append(character_block)
            char_neg_parts.append(char.get("negative_additional", ""))
            #actions    = action_map.get(ident, [])
            #block      = build_character_prompt(char, actions, rng)
            #block      = resolve_scene_vars(block, scene_vars)
            #neg_part   = resolve_wildcards(char.get("negative_additional", ""), rng)
            #if block:
            #    char_blocks.append(block)
            #if neg_part:
            #    char_neg_parts.append(neg_part)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 6 — Collect LoRA tags (from scene + any character loras)
        # ─────────────────────────────────────────────────────────────────────
        #lora_tags = scene.get("lora_tags", "")

        # ─────────────────────────────────────────────────────────────────────
        # STEP 7 — Assemble POSITIVE with BREAK sections
        # ─────────────────────────────────────────────────────────────────────
        #  Section order (each BREAK = new token chunk, reduces bleeding):
        #  [1] Quality tags                          ← global aesthetic anchor
        #  [2] Style + gender count tag              ← model-wide framing
        #  [3] Scene environment                     ← spatial context
        #  [4] story action line                 ← story beat
        #  [5..N] One block per character            ← per-character isolation
        #  [N+1] Lighting + camera                   ← cinematography
        #  [N+2] VFX                                 ← post-process feel
        #  [N+3] LoRA tags + positive additions      ← modifiers last

        sections_pos = []
        sections_pos.append(quality.get("positive_quality", ""))
        #sections_pos.append(", ".join(p for p in [resolved_style, gender_tag] if p))
        sections_pos.append(resolved_style)
        sections_pos.append(gender_tag)
        sections_pos.append(resolved_story)
        sections_pos.extend(char_blocks)
        sections_pos.append(resolved_scene)
        sections_pos.append(resolved_lighting)
        sections_pos.append(resolved_camera)
        #sections_pos.append(", ".join(p for p in [resolved_lighting, resolved_camera] if p))
        if resolved_vfx:
            sections_pos.append(resolved_vfx)
        #trailing = ", ".join(p for p in [positive_addition, lora_tags] if p and p.strip())
        #if trailing:
        #    sections_pos.append(trailing)

        positive_prompt = assemble_with_breaks(sections_pos)
        # ─────────────────────────────────────────────────────────────────────
        # STEP 8 — Assemble NEGATIVE
        # ─────────────────────────────────────────────────────────────────────
        neg_sections = []
        neg_sections.append(quality.get("negative_quality", ""))
        neg_sections.append(resolved_story_neg)
        neg_sections.append(scene.get("negative_additional", ""))
        story_neg = story.get("story_line_negative", "")
        scene_neg     = scene.get("negative_additional", "")
        #if story_neg:
        #    neg_sections.append(resolve_wildcards(story_neg, rng))
        #if scene_neg:
        #    neg_sections.append(resolve_wildcards(scene_neg, rng))
        #if char_neg_parts:
        #    neg_sections.append(", ".join(char_neg_parts))
        #if negative_addition:
        #    neg_sections.append(negative_addition)

        #negative_prompt = assemble_with_breaks(neg_sections)
        negative_prompt = ", ".join(neg_sections)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 9 — Debug preview
        # ─────────────────────────────────────────────────────────────────────
        sep = "─" * 52
        debug_lines = [
            f"╔ story COLLAPSE  [seed: {seed}]",
            sep,
            f"  story LINE  : {raw_story_line}",
            f"  → resolved      : {resolved_story}",
            sep,
            f"  STYLE           : {resolved_style}",
            f"  ENVIRONMENT     : {resolved_scene}",
            f"  LIGHTING        : {resolved_lighting}",
            f"  CAMERA          : {resolved_camera}",
            f"  VFX             : {resolved_vfx}",
            sep,
            f"  GENDER TAG      : {gender_tag}",
            sep,
        ]
        for i, (char, block) in enumerate(zip(character, char_blocks)):
            ident   = char.get("identifier", f"char_{i}")
            debug_lines.append(f"  CHAR [{ident}]  val={char.get('character_value',0):.2f}  ")
            debug_lines.append(f"    → {block}")
        debug_lines += [
            sep,
            f"  LoRA TAGS       : {'(none)'}",
            sep,
            "  ► POSITIVE PROMPT:",
        ]
        for section in [s for s in sections_pos if s and s.strip()]:
            debug_lines.append(f"    | {section}")
            debug_lines.append(f"    BREAK")
        debug_lines += [
            sep,
            "  ► NEGATIVE PROMPT:",
            f"    {negative_prompt}",
            "╚" + sep,
        ]

        debug_preview = "\n".join(debug_lines)

        return (positive_prompt, negative_prompt, debug_preview)


# ── Registration ──────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS        = {"narrative_Story_Collapse_node": narrative_story_Collapse_node}
NODE_DISPLAY_NAME_MAPPINGS = {"narrative_Story_Collapse_node": "narrative Story Solver 🌀"}
