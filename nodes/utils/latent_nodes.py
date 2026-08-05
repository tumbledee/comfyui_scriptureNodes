
from ...lib import img_latent_syntax



class img_res_latent:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":{
                "resolution": ("INT", {"default": 512, "min": 64, "max": 4095}),
                "aspect_ratio": (list(img_latent_syntax.ASPECT_RATIOS.keys()), {"default": "1:1 (Square)"}),
                "custom_width_scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 100.0, "step": 0.01}),
                "custom_height_scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 100.0, "step": 0.01}),
                "batch_size"
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})
            }
        }

    RETURN_TYPES = ("Latent_dict", "INT")
    RETURN_NAMES = ("latent", "Seed")
    FUNCTION = "latent"
    CATEGORY = "utils/pipeline"

    def latent(self, resolution, aspect_ratio, custom_width_scale, custom_height_scale, batch_size, seed):
        width, height = img_latent_syntax.calculate_dimensions(resolution, aspect_ratio, custom_width_scale, custom_height_scale)
        latent_dict = img_latent_syntax.latent_img_simple(batch_size, width, height)
        return (latent_dict, seed)

NODE_CLASS_MAPPINGS = {"img_res_latent": img_res_latent}
NODE_DISPLAY_NAME_MAPPINGS = {"img_res_latent": "image ratio latent"}
