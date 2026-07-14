# Checkpoint with Ksampler integrated

# Useful to pipein all at one spot


# Planned Features
# - scrolls automatically resolve the pipe
# - Lora Manager Support 
# - load and save settings per checkpoint
# - load and save multiple node layouts

import folder_paths
import comfy.sd
import nodes


class CheckpointKSamplerPipe:
    """
    Bundles:
      CheckpointLoaderSimple
      CLIPTextEncode (positive)
      CLIPTextEncode (negative)
      EmptyLatentImage
      KSampler
      VAEDecode

    Outputs the generated IMAGE and the LATENT, plus MODEL/CLIP/VAE so the
    checkpoint components can optionally feed other workflow nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (
                    folder_paths.get_filename_list("checkpoints"),
                    {
                        "tooltip": "Checkpoint from models/checkpoints or extra_model_paths.yaml",
                    },
                ),
                "positive": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "masterpiece, best quality",
                    },
                ),
                "negative": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "worst quality, low quality, bad anatomy",
                    },
                ),
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                    },
                ),
                "batch_size": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 64,
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                    },
                ),
                "steps": (
                    "INT",
                    {
                        "default": 28,
                        "min": 1,
                        "max": 150,
                    },
                ),
                "cfg": (
                    "FLOAT",
                    {
                        "default": 6.0,
                        "min": 0.0,
                        "max": 30.0,
                        "step": 0.1,
                    },
                ),
                "sampler_name": (
                    nodes.KSampler.SAMPLERS,
                ),
                "scheduler": (
                    nodes.KSampler.SCHEDULERS,
                ),
                "denoise": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "LATENT", "MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("image", "latent", "model", "clip", "vae")
    FUNCTION = "generate"
    CATEGORY = "YourSuite/Sampling"

    def generate(
        self,
        ckpt_name,
        positive,
        negative,
        width,
        height,
        batch_size,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        denoise,
    ):
        checkpoint_path = folder_paths.get_full_path("checkpoints", ckpt_name)

        if checkpoint_path is None:
            raise ValueError(
                f"Checkpoint '{ckpt_name}' was not found in the ComfyUI checkpoints paths."
            )

        model, clip, vae, _ = comfy.sd.load_checkpoint_guess_config(
            checkpoint_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )

        positive_conditioning = nodes.CLIPTextEncode().encode(
            clip=clip,
            text=positive,
        )[0]

        negative_conditioning = nodes.CLIPTextEncode().encode(
            clip=clip,
            text=negative,
        )[0]

        latent_image = nodes.EmptyLatentImage().generate(
            width=width,
            height=height,
            batch_size=batch_size,
        )[0]

        sampled_latent = nodes.KSampler().sample(
            model=model,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            positive=positive_conditioning,
            negative=negative_conditioning,
            latent_image=latent_image,
            denoise=denoise,
        )[0]

        image = nodes.VAEDecode().decode(
            samples=sampled_latent,
            vae=vae,
        )[0]

        return (image, sampled_latent, model, clip, vae)