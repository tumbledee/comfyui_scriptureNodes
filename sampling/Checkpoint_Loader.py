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

# Enable second improvement, disable following if else
# Prioritize matching by name first, then by hash. This allows users to retrieve settings
#    if ckpt_name and ckpt_name in data:
#        entry = data[ckpt_name]
#        matched_by = "name"
#    else:
#        file_hash = compute_hash(ckpt_path) if ckpt_path else None
#        for v in data.values():
#            if v.get("hash") == file_hash:
#                # Key = ckpt_name # rename key to ckpt_name for consistency, but still match by hash
#                entry = v
#                matched_by = "hash"
#                break
#    if file_hash and file_hash in data:
#        entry = data[file_hash]
#        matched_by = "hash"
#    else:
#        for v in data.values():
#            if v.get("name") == ckpt_name:
#                entry = v
#                matched_by = "name"
#                break

# ---------------- Checkpoint_w_Settings Node ----------------

class Checkpoint_w_Settings:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
                "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "positive quality Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "best Quality, masterpiece, realistic, high quality, 8k, ultra-detailed",
                    "tooltip": (
                        "Positive prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                }),
                "negative quality Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "worst quality, low quality, blurry, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts",
                    "tooltip": (
                        "Negative prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "INT", "FLOAT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "steps", "cfg", "sampler_name", "scheduler", "positive quality Prompt", "negative quality Prompt")
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


NODE_CLASS_MAPPINGS = {"Checkpoint_w_Settings": Checkpoint_w_Settings}
NODE_DISPLAY_NAME_MAPPINGS = {"Checkpoint_w_Settings": "Checkpoint w/ Settings"}