# # Quality checkpoint
# A node that sets quality keywords to negative and positive prompts based on the checkpoint

#input:
#- Quality addition Positive
#- Quality addition Negative
#- Checkpoint Name
#- filepath to load
#- filepath to save

#output:
#- Quality slot

# Future Ideas:
# - new random seed only after certain iterations 
# - advance seed with iteration
# - random seed each iteration
# 
# 
# 
# 
# 
# 

import json
import os
from .lib.file_io import save_json, load_json, load_text_lines
from .lib.settings import get_character_setting
# ---------------------------------------------------------------------------
# Default save location: same directory as this file.
# Toggling custom_directory=True reveals a text field for an override path.
# All checkpoint data is stored in one shared JSON registry file.
# ---------------------------------------------------------------------------

_DEFAULT_DB_DIR  = os.path.dirname(os.path.abspath(__file__))
_DB_FILENAME     = "quality_checkpoint_db.json"

def _db_path(custom_dir: str = "") -> str:
    base = custom_dir.strip() if custom_dir.strip() else _DEFAULT_DB_DIR
    return os.path.join(base, _DB_FILENAME)

def _load_db(custom_dir: str = "") -> dict:
    path = _db_path(custom_dir)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_db(db: dict, custom_dir: str = "") -> None:
    path = _db_path(custom_dir)
    dir_part = os.path.dirname(path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


class narrative_Quality_Node:
    """
    Stores and retrieves per-checkpoint quality settings.
    On every execution the current values are written back to the registry.
    If a checkpoint_name is provided, its saved values are loaded first (auto-populate).
    """

    CATEGORY = "NarrativeSystem"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "checkpoint_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Key used to save/load this checkpoint's quality profile. Leave blank to skip auto-load.",
                }),
                "positive_quality": ("STRING", {
                    "default": "masterpiece, best quality, very aesthetic, absurdres",
                    "multiline": True,
                }),
                "negative_quality": ("STRING", {
                    "default": "worst quality, low quality, jpeg artifacts, blurry",
                    "multiline": True,
                }),
                # ── Sampler settings ──────────────────────────────────────
                "steps": ("INT",   {"default": 28, "min": 1,   "max": 150}),
                "cfg":   ("FLOAT", {"default": 6.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "sampler_name": ([
                    "dpmpp_2m", "dpmpp_sde", "dpmpp_2m_sde",
                    "euler", "euler_ancestral", "dpm_adaptive",
                    "lcm", "ddim", "uni_pc",
                ], {}),
                "scheduler": ([
                    "karras", "exponential", "sgm_uniform",
                    "simple", "normal", "beta",
                ], {}),
                "clip_skip": ("INT", {"default": -2, "min": -12, "max": -1, "step": 1}),
                # ── Notes ─────────────────────────────────────────────────
                "notes": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Free-text info: model source, trigger words, known issues, etc.",
                }),
                # ── Save path toggle ──────────────────────────────────────
                "custom_directory": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enable to specify a custom folder for the quality DB file.",
                }),
            },
            "optional": {
                "custom_db_path": ("STRING", {
                    "default": "",
                    "tooltip": "Only used when custom_directory=True. Folder path (not filename).",
                }),
            },
        }

    RETURN_TYPES = ("QUALITY", "STRING")
    RETURN_NAMES = ("quality", "debug")
    FUNCTION     = "execute"

    @classmethod
    def IS_CHANGED(cls, checkpoint_name, **kwargs):
        # Re-run whenever checkpoint name changes or always if blank
        return checkpoint_name if checkpoint_name.strip() else float("NaN")

    def execute(
        self,
        checkpoint_name,
        positive_quality,
        negative_quality,
        steps,
        cfg,
        sampler_name,
        scheduler,
        clip_skip,
        notes,
        custom_directory,
        custom_db_path="",
    ):
        db_dir = custom_db_path if custom_directory else ""

        # ── AUTO-LOAD from registry if checkpoint_name is set ─────────────────
        if checkpoint_name.strip():
            db = _load_db(db_dir)
            saved = db.get(checkpoint_name.strip(), {})
            if saved:
                positive_quality = saved.get("positive_quality", positive_quality)
                negative_quality = saved.get("negative_quality", negative_quality)
                steps            = saved.get("steps",            steps)
                cfg              = saved.get("cfg",              cfg)
                sampler_name     = saved.get("sampler_name",     sampler_name)
                scheduler        = saved.get("scheduler",        scheduler)
                clip_skip        = saved.get("clip_skip",        clip_skip)
                notes            = saved.get("notes",            notes)
                print(f"[QualityNode] Loaded profile for '{checkpoint_name}'")
            else:
                print(f"[QualityNode] No profile found for '{checkpoint_name}', using widget values.")

        # ── Build quality dict ────────────────────────────────────────────────
        quality_dict = {
            "checkpoint_name":  checkpoint_name,
            "positive_quality": positive_quality,
            "negative_quality": negative_quality,
            "steps":            steps,
            "cfg":              cfg,
            "sampler_name":     sampler_name,
            "scheduler":        scheduler,
            "clip_skip":        clip_skip,
            "notes":            notes
        }

        # ── ALWAYS SAVE current values back to registry ───────────────────────
        if checkpoint_name.strip():
            try:
                db = _load_db(db_dir)
                db[checkpoint_name.strip()] = quality_dict
                _save_db(db, db_dir)
                print(f"[QualityNode] Saved profile for '{checkpoint_name}'")
            except Exception as e:
                print(f"[QualityNode] WARNING: Failed to save profile: {e}")

        # ── Debug string ──────────────────────────────────────────────────────
        sep = "─" * 48
        debug = "\n".join([
            f"╔ QUALITY NODE  [{checkpoint_name or '(no checkpoint)'}]",
            sep,
            f"  Steps: {steps}   CFG: {cfg}   CLIP skip: {clip_skip}",
            f"  Sampler: {sampler_name}   Scheduler: {scheduler}",
            sep,
            f"  [POS] {positive_quality}",
            f"  [NEG] {negative_quality}",
            sep,
            f"  [NOTES] {notes or '(none)'}",
            "╚" + sep,
        ])

        return (
            quality_dict,
            positive_quality,
            negative_quality,
            steps,
            cfg,
            sampler_name,
            scheduler,
            clip_skip,
        )


NODE_CLASS_MAPPINGS        = {"narrative_Quality_node": narrative_Quality_Node}
NODE_DISPLAY_NAME_MAPPINGS = {"narrative_Quality_node": "narrative Quality ⭐"}
