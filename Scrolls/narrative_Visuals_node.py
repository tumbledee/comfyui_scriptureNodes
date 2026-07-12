# Scene Node
#A node to list simple keywords

#input:
#- Scene Keywords
#- vfx keywords
#- light keywords
#- camera keywords
#- style keywords
#- artist keywords

#output:
#- Scene slot

import json
import os
import re
import random
import glob
from .lib.file_io import save_json, load_json, load_text_lines
from .lib.settings import get_character_setting
# ---------------------------------------------------------------------------
# Wildcard resolver – reads .txt files from a wildcards folder.
# Supports __wildcard_name__ syntax inside any string field.
# Default path: ComfyUI/wildcards/  (override via WILDCARDS_PATH env var)
# ---------------------------------------------------------------------------

WILDCARDS_DIR = os.environ.get(
    "WILDCARDS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "wildcards"),
)

_wildcard_cache: dict[str, list[str]] = {}


def _load_wildcard(name: str) -> list[str]:
    if name in _wildcard_cache:
        return _wildcard_cache[name]
    path = os.path.join(WILDCARDS_DIR, f"{name}.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        _wildcard_cache[name] = lines
        return lines
    _wildcard_cache[name] = []
    return []


def resolve_wildcards(text: str, seed: int = -1) -> str:
    """Recursively expand __wildcard__ tokens in text."""
    if not text:
        return text
    rng = random.Random(seed) if seed >= 0 else random.Random()

    def _expand(t: str, depth: int = 0) -> str:
        if depth > 16:
            return t
        pattern = r"__([a-zA-Z0-9_/\-]+)__"
        def _replace(m):
            entries = _load_wildcard(m.group(1))
            if not entries:
                return m.group(0)  # leave token intact if file missing
            chosen = rng.choice(entries)
            return _expand(chosen, depth + 1)
        return re.sub(pattern, _replace, t)

    return _expand(text)


# ---------------------------------------------------------------------------
# LoRA injection helpers
# Builds <lora:name:weight> tags from a simple "name:weight" shorthand string.
# Multiple entries separated by commas or newlines.
# Example input:  "add_detail:0.8, light_anime:0.6"
# Output appended to positive prompt: "<lora:add_detail:0.8> <lora:light_anime:0.6>"
# ---------------------------------------------------------------------------

def parse_loras(raw: str) -> list[dict]:
    """Parse 'lora_name:weight' or 'lora_name' entries into structured list."""
    loras = []
    if not raw.strip():
        return loras
    for entry in re.split(r"[,\n]+", raw):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.rsplit(":", 1)
        name = parts[0].strip()
        try:
            weight = float(parts[1].strip()) if len(parts) == 2 else 1.0
        except ValueError:
            weight = 1.0
        loras.append({"name": name, "weight": weight})
    return loras


def build_lora_tags(loras: list[dict]) -> str:
    return " ".join(f"<lora:{l['name']}:{l['weight']:.2f}>" for l in loras)


# ---------------------------------------------------------------------------
# Value-driven wildcard rules
# scene_value drives automatic wildcard resolution per category.
# Categories: scene, light, camera, vfx
# For each category we look for files:
#   wildcards/scene/low/<category>.txt   (value < -0.33)
#   wildcards/scene/mid/<category>.txt   (value -0.33 to 0.33)
#   wildcards/scene/high/<category>.txt  (value > 0.33)
# Falls back gracefully if files don't exist.
# ---------------------------------------------------------------------------

def value_tier(v: float) -> str:
    if v < -0.33:
        return "low"
    elif v > 0.33:
        return "high"
    return "mid"


def resolve_value_wildcard(category: str, value: float, seed: int) -> str:
    tier = value_tier(value)
    key = f"scene/{tier}/{category}"
    entries = _load_wildcard(key)
    if not entries:
        return ""
    rng = random.Random(seed) if seed >= 0 else random.Random()
    return rng.choice(entries)


# ---------------------------------------------------------------------------
# Scene node
# ---------------------------------------------------------------------------

class narrative_Visuals:
    CATEGORY = "NarrativeSystem"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vfx_id": ("STRING", {"default": "vfx_01", "multiline": False}),
            },
            "optional": {
                # ── Core scene fields ──────────────────────────────────────
                "lighting": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Light quality, colour, direction. Supports __wildcards__"}),
                "camera": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Shot type, angle, lens feel. Supports __wildcards__"}),
                "style": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Art style, medium, rendering look. Supports __wildcards__"}),
                "vfx": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Particles, bloom, depth-of-field, motion blur, overlays. Supports __wildcards__"}),

                # ── Dynamic driver ─────────────────────────────────────────
                "scene_value": ("FLOAT", {
                    "default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01,
                    "tooltip": (
                        "Drives auto-wildcard resolution from wildcards/scene/{low|mid|high}/<category>.txt. "
                        "Negative = muted/dark, Positive = vibrant/dramatic"
                    ),
                }),
                # ── Extra prompting ────────────────────────────────────────
                "positive_additional": ("STRING", {"default": "", "multiline": True}),
                "negative_additional": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("VISUALS", "STRING")
    RETURN_NAMES = ("visuals", "debug_preview")
    FUNCTION = "build_scene"

    def build_scene(
        self,
        vfx_id,
        lighting="",
        camera="",
        style="",
        vfx="",
        scene_value=0.0,
        wildcard_seed=-1,
        loras="",
        positive_additional="",
        negative_additional="",
        save_file_path="",
        load_file_path="",
    ):
        # ── LOAD ─────────────────────────────────────────────────────────────
        load_path = load_file_path.strip()
        if load_path and os.path.isfile(load_path):
            try:
                with open(load_path, "r", encoding="utf-8") as f:
                    scene_dict = json.load(f)
                debug = self._render_debug(scene_dict)
                print(f"[SceneBuilder] Loaded from: {load_path}")
                return (scene_dict, debug)
            except Exception as e:
                print(f"[SceneBuilder] WARNING: Failed to load '{load_path}': {e}")

        # ── Resolve effective seed ────────────────────────────────────────────
        seed = wildcard_seed if wildcard_seed >= 0 else random.randint(0, 2**32)

        # ── Expand inline wildcards in all text fields ────────────────────────
        fields_raw = {
            "lighting":             lighting,
            "camera":               camera,
            "style":                style,
            "vfx":                  vfx,
            "positive_additional":  positive_additional,
            "negative_additional":  negative_additional,
        }
        fields_resolved = {k: resolve_wildcards(v, seed) for k, v in fields_raw.items()}

        # ── Auto-inject value-driven wildcards ────────────────────────────────
        # Only injects when the field is empty, so manual entries always win.
        auto_categories = ["lighting", "camera", "vfx"]
        for cat in auto_categories:
            if not fields_resolved[cat].strip():
                auto = resolve_value_wildcard(cat, scene_value, seed)
                if auto:
                    fields_resolved[cat] = auto

        # ── Parse LoRAs ───────────────────────────────────────────────────────
        parsed_loras = parse_loras(loras)
        lora_tags = build_lora_tags(parsed_loras)

        # ── Assemble positive prompt parts ────────────────────────────────────
        positive_parts = [
            fields_resolved["style"],
            fields_resolved["lighting"],
            fields_resolved["camera"],
            fields_resolved["vfx"],
            fields_resolved["positive_additional"],
            lora_tags,
        ]
        assembled_positive = ", ".join(p for p in positive_parts if p.strip())

        # ── Build output dict ─────────────────────────────────────────────────
        scene_dict = {
            "vfx_id":             vfx_id,
            "scene_value":          scene_value,
            # Raw resolved fields (for downstream nodes to pick apart)
            "lighting":             fields_resolved["lighting"],
            "camera":               fields_resolved["camera"],
            "style":                fields_resolved["style"],
            "vfx":                  fields_resolved["vfx"],
            "positive_additional":  fields_resolved["positive_additional"],
            "negative_additional":  fields_resolved["negative_additional"],
            # Convenience assembled strings
            "assembled_positive":   assembled_positive,
            "loras":                parsed_loras,
            "lora_tags":            lora_tags,
        }

        # ── SAVE ──────────────────────────────────────────────────────────────
        save_path = save_file_path.strip()
        if save_path:
            try:
                dir_part = os.path.dirname(save_path)
                if dir_part:
                    os.makedirs(dir_part, exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(scene_dict, f, indent=2, ensure_ascii=False)
                print(f"[SceneBuilder] Saved to: {save_path}")
            except Exception as e:
                print(f"[SceneBuilder] WARNING: Failed to save '{save_path}': {e}")

        debug = self._render_debug(scene_dict)
        return (scene_dict, debug)

    # ── Debug renderer ────────────────────────────────────────────────────────
    @staticmethod
    def _render_debug(d: dict) -> str:
        sep = "─" * 48
        lines = [
            f"╔ SCENE BUILDER DEBUG  [{d.get('vfx_id', '?')}]",
            sep,
            f"  scene_value  : {d.get('scene_value', 0):.2f}   seed: {d.get('wildcard_seed', '?')}",
            sep,
            f"  [STYLE]   {d.get('style', '')}",
            f"  [LIGHT]   {d.get('lighting', '')}",
            f"  [CAMERA]  {d.get('camera', '')}",
            f"  [VFX]     {d.get('vfx', '')}",
            f"  [POS+]    {d.get('positive_additional', '')}",
            f"  [NEG+]    {d.get('negative_additional', '')}",
            sep,
            f"  [LoRAs]   {d.get('lora_tags', '(none)')}",
            sep,
            "  ► ASSEMBLED POSITIVE:",
            f"  {d.get('assembled_positive', '')}",
            "╚" + sep,
        ]
        return "\n".join(lines)


# ── Registration ──────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "narrative_visuals_node": narrative_Visuals,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "narrative_visuals_node": "narrative Visuals 🎬",
}
