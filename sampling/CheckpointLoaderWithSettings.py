# Todo:
# Save load checkpoint
# hash identity of checkpoint
# check name first
# -> fallback metadata embedded hash (safetensors header and first block)
# -> fallback A1111-Style short hash
# -> fallback full sha256 hash of file
# 
# Want to have
# - implement auto backup of settings file regularly
# - save multiple settings per checkpoint (by hash) and allow user to select which to load
# - add ksampler that fills in the settings from the checkpoint loader node
# - add lora manager support
# - add quality_scroll settings (sets positive and negative quality prompts)
# - add a pipeup checkpoint that feeds all checkpoint settings into the Scroll system
# - add a pipe extract node that extracts all single contents of the checkpoint
# - add a pipe input node that takes in akk single contents of a checkpoint
# - add  
# thoughts
# - more robust settings save naming for checkpoints that have the same name but different hashes 
#       (e.g. "model.ckpt" and "model.ckpt" with different hashes)
# - externalize functions so that other nodes can use them to save/load settings
# 

import os
import json
import hashlib
import folder_paths
import comfy.samplers
import comfy.sd

NODE_ROOT = os.path.dirname(os.path.dirname(__file__)) # steps up one level to the root of the node package
SETTINGS_FILE = os.path.join(NODE_ROOT, "data", "checkpoint_settings.json")
os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)


def compute_hash(filepath, quick=True, chunk_size=1024 * 1024):
    """Quick hash reads only the first 1MB (fast, good enough to detect the same file).
    Set quick=False for a full-file SHA-256 (slower on large checkpoints)."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        if quick:
            hasher.update(f.read(chunk_size))
        else:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    return hasher.hexdigest()


def load_all_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_all_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


class CheckpointLoaderWithSettings:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
                "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "INT", "FLOAT", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("model", "clip", "vae", "steps", "cfg", "sampler_name", "scheduler", "width", "height")
    FUNCTION = "load"
    CATEGORY = "loaders/settings"

    def load(self, ckpt_name, steps, cfg, sampler_name, scheduler, width, height):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        return (model, clip, vae, steps, cfg, sampler_name, scheduler, width, height)


NODE_CLASS_MAPPINGS = {"CheckpointLoaderWithSettings": CheckpointLoaderWithSettings}
NODE_DISPLAY_NAME_MAPPINGS = {"CheckpointLoaderWithSettings": "Checkpoint Loader (w/ Settings Save)"}