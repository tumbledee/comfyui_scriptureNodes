
class PIPE_LINE_Schema_Documentation:
    """
    PIPE_LINE schema reference (not a functional node — do not add to workflows).

    Produced by: CheckpointLoaderPipeline

    Dict keys and types:
    - model             : MODEL object (comfy.sd loaded checkpoint)
    - clip              : CLIP object
    - vae               : VAE object
    - positive_text     : str, raw positive prompt text
    - positive          : CONDITIONING, encoded via CLIPTextEncode
    - negative_text     : str, raw negative prompt text
    - negative          : CONDITIONING, encoded via CLIPTextEncode
    - latent            : dict {"samples": torch.Tensor} shaped [batch, 4, height//8, width//8]
    - width             : int, final pixel width (multiple of 8)
    - height            : int, final pixel height (multiple of 8)
    - seed              : int
    - steps             : int
    - cfg               : float
    - sampler_name      : str, one of comfy.samplers.KSampler.SAMPLERS
    - scheduler         : str, one of comfy.samplers.KSampler.SCHEDULERS
    Additional types for this node suite
    - ckpt_name         : str, original checkpoint filename
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "noop"
    CATEGORY = "documentation/do_not_use"

    def noop(self):
        return ()