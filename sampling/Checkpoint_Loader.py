# Todo:
# 
# Want to have
# - implement auto backup of settings file regularly
# - add quality_scroll settings (sets positive and negative quality prompts)
# - add a pipeup checkpoint that feeds all checkpoint settings into the Scroll system
# - add a pipe extract node that extracts all single contents of the checkpoint
# - add a pipe input node that takes in akk single contents of a checkpoint
# - add  
# thoughts
# 

import os
import json
import hashlib
import folder_paths
import comfy.samplers
import comfy.sd
import nodes as comfy_nodes  # gives access to built-in CLIPTextEncode
from ..lib import img_latent_syntax

# ---------------- Checkpoint_w_Settings Node ----------------
#region Settings ckpt
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
                "positive_quality_Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "best Quality, masterpiece, realistic, high quality, 8k, ultra-detailed",
                    "tooltip": (
                        "Positive prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                }),
                "negative_quality_Prompt": ("STRING", {
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

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "INT", "FLOAT", "COMBO", "COMBO", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "steps", "cfg", "sampler_name", "scheduler", "ckpt_name","ckpt_path","ckpt_rel_path", "positive_quality_Prompt", "negative_quality_Prompt")
    FUNCTION = "load"
    CATEGORY = "loaders/settings"

    def load(self, ckpt_name, steps, cfg, sampler_name, scheduler, positive_quality_Prompt, negative_quality_Prompt):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        ckpt_rel_path = ckpt_name
        ckpt_name = ckpt_name.split(os.sep)[-1]  # Ensure only the filename is returned, not the full path
        return (model, clip, vae, steps, cfg, sampler_name, scheduler, ckpt_name, ckpt_path, ckpt_rel_path, positive_quality_Prompt, negative_quality_Prompt)


#NODE_CLASS_MAPPINGS = {"Checkpoint_w_Settings": Checkpoint_w_Settings}
#NODE_DISPLAY_NAME_MAPPINGS = {"Checkpoint_w_Settings": "Checkpoint w/ Settings"}

#endregion
#region Pipe ckpt
class Checkpoint_KSampler_Piped:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
                "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "positive_quality_Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "best Quality, masterpiece, realistic, high quality, 8k, ultra-detailed",
                    "tooltip": (
                        "Positive prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                }),
                "negative_quality_Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "worst quality, low quality, blurry, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts",
                    "tooltip": (
                        "Negative prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                })
            }
        }

    RETURN_TYPES = ("PIPE_LINE",)
    RETURN_NAMES = ("pipe",)
    FUNCTION = "build_pipe"
    CATEGORY = "loaders/settings"

    def build_pipe(self, ckpt_name, steps, cfg, sampler_name, scheduler, resolution, aspect_ratio, custom_width_scale, custom_height_scale, positive_quality_Prompt, negative_quality_Prompt, seed):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        ckpt_rel_path = ckpt_name
        ckpt_name = ckpt_name.split(os.sep)[-1]  # Ensure only the filename is returned, not the full path

        text_encoder = comfy_nodes.CLIPTextEncode()
        (positive_cond,) = text_encoder.encode(clip, positive_quality_Prompt)
        (negative_cond,) = text_encoder.encode(clip, negative_quality_Prompt)

        pipe = {
            "model": model,
            "clip": clip,
            "vae": vae,
            "positive": positive_cond,
            "positive_str": positive_quality_Prompt,
            "negative": negative_cond,
            "negative_str": negative_quality_Prompt,
            "latent": None,
            "seed": None,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler
        }
        return (pipe,)


#endregion
#region prompts ckpt

class Checkpoint_w_prompts:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),            
                "positive_quality_Prompt": ("STRING", {
                    "multiline": True, 
                    "default": "best Quality, masterpiece, realistic, high quality, 8k, ultra-detailed",
                    "tooltip": (
                        "Positive prompt.\n"
                        "Supports only strings so far\n"
                        "no wildcards or random lines from files yet."
                    )
                }),
                "negative_quality_Prompt": ("STRING", {
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

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "ckpt_name", "ckpt_path", "ckpt_rel_path", "positive_quality_Prompt", "negative_quality_Prompt")
    FUNCTION = "load"
    CATEGORY = "loaders/settings"

    def load(self, ckpt_name, positive_quality_Prompt, negative_quality_Prompt):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        ckpt_rel_path = ckpt_name
        ckpt_name = ckpt_name.split(os.sep)[-1]  # Ensure only the filename is returned, not the full path
        return (model, clip, vae, ckpt_name, ckpt_path, ckpt_rel_path, positive_quality_Prompt, negative_quality_Prompt)

#NODE_CLASS_MAPPINGS = {"Checkpoint_w_prompts": Checkpoint_w_prompts}
#NODE_DISPLAY_NAME_MAPPINGS = {"Checkpoint_w_prompts": "Checkpoint w/ Prompts"}
#endregion
#region simple ckpt
class Checkpoint_simple:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),)
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "ckpt_name", "ckpt_path", "ckpt_rel_path")
    FUNCTION = "load"
    CATEGORY = "loaders/settings"

    def load(self, ckpt_name):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        ckpt_rel_path = ckpt_name
        ckpt_name = ckpt_name.split(os.sep)[-1]  # Ensure only the filename is returned, not the full path
        return (model, clip, vae, ckpt_name, ckpt_path, ckpt_rel_path)
#endregion

#region minimal ckpt
class Checkpoint_minimal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),)            
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("model", "clip", "vae")
    FUNCTION = "load"
    CATEGORY = "loaders/settings"

    def load(self, ckpt_name):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        model, clip, vae = out[:3]
        return (model, clip, vae)

#endregion
# ---------------------------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "Checkpoint_w_Settings": Checkpoint_w_Settings,
    "Checkpoint_w_prompts": Checkpoint_w_prompts,
    "Checkpoint_KSampler_Piped": Checkpoint_KSampler_Piped,
    "Checkpoint_simple": Checkpoint_simple,
    "Checkpoint_minimal": Checkpoint_minimal
    }
NODE_DISPLAY_NAME_MAPPINGS = {
    "Checkpoint_w_Settings": "Checkpoint w/ Settings",
    "Checkpoint_w_prompts": "Checkpoint w/ Prompts",
    "Checkpoint_KSampler_Piped": "Checkpoint+KSampler Piped",
    "Checkpoint_simple": "Checkpoint Simple",
    "Checkpoint_minimal": "Checkpoint Minimal"
    }

