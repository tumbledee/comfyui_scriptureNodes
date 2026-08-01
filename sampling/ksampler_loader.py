import comfy.samplers
import nodes as comfy_nodes


class KSamplerFromCheckpointDB:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "latent_image": ("LATENT",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "sample"
    CATEGORY = "sampling/settings"

    def sample(self, model, positive, negative, latent_image, seed, steps, cfg, sampler_name, scheduler, denoise):
        real_ksampler = comfy_nodes.KSampler()
        return real_ksampler.sample(
            model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image, denoise
        )


NODE_CLASS_MAPPINGS = {"KSamplerFromCheckpointDB": KSamplerFromCheckpointDB}
NODE_DISPLAY_NAME_MAPPINGS = {"KSamplerFromCheckpointDB": "KSampler (synced with Checkpoint DB)"}