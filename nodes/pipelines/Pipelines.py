
import folder_paths
import comfy.samplers
import comfy.sd
import nodes as comfy_nodes  # gives access to built-in CLIPTextEncode

class AnyType(str):
    """Wildcard type that bypasses ComfyUI's strict type checking, needed
    so PIPELINE can absorb heterogeneous state without triggering
    connection-mismatch errors on the frontend."""
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False

ANY = AnyType("*")


class PipeIn:
    """
    Collects every common state slot into a single PIPELINE dict.
    Supports chaining: if an upstream 'pipeline' is connected, its keys
    are merged first (state persistence), then overwritten only by
    whatever this node explicitly provides (recursive injection).

        - pipe              : PIPE_LINE type supports easy use packs 
    - model             : MODEL object (comfy.sd loaded checkpoint)
    - clip              : CLIP object
    - vae               : VAE object
    - pos_text          : str, raw positive prompt text
    - pos               : CONDITIONING, encoded via CLIPTextEncode
    - neg_text          : str, raw negative prompt text
    - neg               : CONDITIONING, encoded via CLIPTextEncode
    - latent            : dict {"samples": torch.Tensor} shaped [batch, 4, height//8, width//8]
    - width             : int, final pixel width (multiple of 8)
    - height            : int, final pixel height (multiple of 8)
    - steps             : int
    - cfg               : float
    - sampler_name      : str, one of comfy.samplers.KSampler.SAMPLERS
    - scheduler         : str, one of comfy.samplers.KSampler.SCHEDULERS
    - seed              : int
    - img               : IMAGE type
    - xyPlot            : XYPLOT
    - controlnet        : CONTROL_NET
        Additional types for this node suite
    - ckpt_name         : str, original checkpoint filename
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "pipe": ("PIPE_LINE",),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "pos_text": ("STRING",),
                "pos": ("CONDITIONING",),
                "neg_text": ("STRING",),
                "neg": ("CONDITIONING",),
                "latent": ("LATENT",),
                "width": ("INT", {"default": 0, "min": 0, "max": 16384}),
                "height": ("INT", {"default": 0, "min": 0, "max": 16384}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler_name": ("STRING", {"default": ""}),
                "scheduler": ("STRING", {"default": ""}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "xyPlot": ("XYPLOT",),
                "controlnet": ("CONTROL_NET",),
            },
        }

    RETURN_TYPES = ("PIPE_LINE",)
    RETURN_NAMES = ("pipe",)
    FUNCTION = "pack"
    CATEGORY = "pipeline"

    def pack(self, pipeline=None, **kwargs):
        state = dict(pipeline) if isinstance(pipeline, dict) else {}
        for key, value in kwargs.items():
            # Only overwrite when a real connection/non-default value is passed.
            # Widgets always send *some* value, so treat empty string / zero
            # as "unset" for the string fields to avoid clobbering upstream state.
            if value == "" or value is None:
                continue
            state[key] = value
        return (state,)


class PipeOut:
    """
    Unpacks a PIPELINE dict back into typed sockets.
    Missing keys resolve to None rather than raising, so partial pipes
    (e.g. only MODEL+CLIP set) don't break downstream graphs.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"pipe": ("PIPE_LINE",)}}

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "CONDITIONING", "CONDITIONING",
                     "LATENT", "IMAGE", "MASK", "INT", "INT", "FLOAT",
                     "STRING", "STRING", "FLOAT", "INT", "INT")
    RETURN_NAMES = ("model", "clip", "vae", "positive", "negative",
                     "latent", "image", "mask", "seed", "steps", "cfg",
                     "sampler_name", "scheduler", "denoise", "width", "height")
    FUNCTION = "unpack"
    CATEGORY = "pipeline"

    def unpack(self, pipeline):
        p = pipeline if isinstance(pipeline, dict) else {}
        return (
            p.get("model"), p.get("clip"), p.get("vae"),
            p.get("positive"), p.get("negative"), p.get("latent"),
            p.get("image"), p.get("mask"), p.get("seed", 0),
            p.get("steps", 20), p.get("cfg", 7.0),
            p.get("sampler_name", ""), p.get("scheduler", ""),
            p.get("denoise", 1.0), p.get("width", 0), p.get("height", 0),
        )


class PipeGetAny:
    """
    Escape hatch for keys not covered by PipeOut's fixed sockets — reads
    an arbitrary key by name and returns it as a wildcard ANY type.
    Use this for custom keys you inject via a Python-based extension node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipe": ("PIPE_LINE",),
                "key": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("value",)
    FUNCTION = "get"
    CATEGORY = "pipeline"

    def get(self, pipeline, key):
        p = pipeline if isinstance(pipeline, dict) else {}
        return (p.get(key),)


NODE_CLASS_MAPPINGS = {
    "PipeIn": PipeIn,
    "PipeOut": PipeOut,
    "PipeGetAny": PipeGetAny,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PipeIn": "Pipe In",
    "PipeOut": "Pipe Out",
    "PipeGetAny": "Pipe Get (Any Key)",
}










class pipeIn:
    def __init__(self):
        pass
    """
    PIPE_LINE schema reference (not a functional node — do not add to workflows).

    Produced by: CheckpointLoaderPipeline

    Dict keys and types:
    - model          : MODEL object (comfy.sd loaded checkpoint)
    - clip           : CLIP object
    - vae            : VAE object
    - ckpt_name      : str, original checkpoint filename
    - pos_text  : str, raw positive prompt text
    - pos_cond  : CONDITIONING, encoded via CLIPTextEncode
    - neg_text  : str, raw negative prompt text
    - neg_cond  : CONDITIONING, encoded via CLIPTextEncode
    - latent         : dict {"samples": torch.Tensor} shaped [batch, 4, height//8, width//8]
    - width          : int, final pixel width (multiple of 8)
    - height         : int, final pixel height (multiple of 8)
    - seed           : int
    - steps          : int
    - cfg            : float
    - sampler_name   : str, one of comfy.samplers.KSampler.SAMPLERS
    - scheduler      : str, one of comfy.samplers.KSampler.SCHEDULERS
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
             "required": {},
             "optional": {
                "pipe": ("PIPE_LINE",),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "pos_text": ("STRING",),
                "pos": ("CONDITIONING",),
                "neg_text": ("STRING",),
                "neg": ("CONDITIONING",),
                "latent": ("LATENT",),
                "width": ("INT"),
                "height": ("INT"),
                "steps": ("INT"),
                "cfg": ("INT"),
                "sampler_name": ("COMBO"),
                "scheduler": ("COMBO"),
                "seed": ("INT"),
                "img": ("IMAGE",),
                "xyPlot": ("XYPLOT",)
            },
            "hidden": {"my_unique_id": "UNIQUE_ID"},
        }


    RETURN_TYPES = ("PIPE_LINE",)
    RETURN_NAMES = ("pipe",)
    FUNCTION = "flush"

    CATEGORY = "Pipeline"

    def flush(self, pipe=None, model=None, clip=None, vae=None, pos_text=None, pos=None, neg_text=None, neg=None, latent=None, width=None, height=None, steps=None, cfg=None, sampler_name=None, scheduler=None, seed=None, img=None, xyplot=None, my_unique_id=None):

        model = model if model is not None else pipe.get("model")
        # Logs are a custom lib not existing yet
        #if model is None:
            # log_node_warn(f'pipeIn[{my_unique_id}]', "Model missing from pipeLine")
        clip = clip if clip is not None else pipe.get("clip") if pipe is not None and "clip" in pipe else None
        # if clip is None:
        #     log_node_warn(f'pipeIn[{my_unique_id}]', "Clip missing from pipeLine")
        vae = vae if vae is not None else pipe.get("vae")
        #if vae is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "VAE missing from pipeLine")

        pos_text = pos_text if pos_text is not None else pipe.get("positive_text")
        pos = pos if pos is not None else pipe.get("positive")
        #if pos is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "Pos Conditioning missing from pipeLine")
        neg_text = neg_text if neg_text is not None else pipe.get("negative_text") 
        neg = neg if neg is not None else pipe.get("negative")
        #if neg is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "Neg Conditioning missing from pipeLine")
        
        if latent is not None:
            samples = latent
        elif image is None:
            samples = pipe.get("samples") if pipe is not None else None
            image = pipe.get("images") if pipe is not None else None
        elif image is not None:
            if pipe is None:
                batch_size = 1
            else:
                batch_size = pipe["loader_settings"]["batch_size"] if "batch_size" in pipe["loader_settings"] else 1
            samples = {"samples": vae.encode(image[:, :, :, :3])}
            samples = RepeatLatentBatch().repeat(samples, batch_size)[0]
        width = width if width is not None else pipe.get("width")
        height = height if height is not None else pipe.get("height")
        steps = steps if steps is not None else pipe.get("steps")
        cfg = cfg if cfg is not None else pipe.get("cfg")
        sampler_name = sampler_name if sampler_name is not None else pipe.get("sampler_name")
        scheduler = scheduler if scheduler is not None else pipe.get("scheduler")
        seed = seed if seed is not None else pipe.get("seed")


        if pipe is None:
            pipe = {"loader_settings": {"positive": "", "negative": "", "xyplot": None}}

        xyplot = xyplot if xyplot is not None else pipe['loader_settings']['xyplot'] if xyplot in pipe['loader_settings'] else None

        new_pipe = {
            **pipe,
            "model": model,
            "positive": pos,
            "negative": neg,
            "vae": vae,
            "clip": clip,

            "samples": samples,
            "images": image,
            "seed": pipe.get('seed') if pipe is not None and "seed" in pipe else None,

            "loader_settings": {
                **pipe["loader_settings"],
                "xyplot": xyplot
            }
        }
        del pipe

        return (new_pipe,)



class pipeOut:
    def __init__(self):
        pass
    """
    PIPE_LINE schema reference (not a functional node — do not add to workflows).

    Produced by: CheckpointLoaderPipeline

    Dict keys and types:
    - model          : MODEL object (comfy.sd loaded checkpoint)
    - clip           : CLIP object
    - vae            : VAE object
    - ckpt_name      : str, original checkpoint filename
    - pos_text  : str, raw positive prompt text
    - pos_cond  : CONDITIONING, encoded via CLIPTextEncode
    - neg_text  : str, raw negative prompt text
    - neg_cond  : CONDITIONING, encoded via CLIPTextEncode
    - latent         : dict {"samples": torch.Tensor} shaped [batch, 4, height//8, width//8]
    - width          : int, final pixel width (multiple of 8)
    - height         : int, final pixel height (multiple of 8)
    - seed           : int
    - steps          : int
    - cfg            : float
    - sampler_name   : str, one of comfy.samplers.KSampler.SAMPLERS
    - scheduler      : str, one of comfy.samplers.KSampler.SCHEDULERS
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
             "required": {},
             "optional": {
                "pipe": ("PIPE_LINE",),
            },
            "hidden": {"my_unique_id": "UNIQUE_ID"},
        }


    RETURN_TYPES = ("PIPE_LINE", "MODEL", "CLIP", "VAE", "STRING", "CONDITIONING", "STRING", "CONDITIONING", "LATENT", "INT", "INT", "INT", "FLOAT", "COMBO", "COMBO", "FLOAT", "IMAGE", "xy" )
    RETURN_NAMES = ("pipe", "model", "clip", "vae", "pos_text", "pos", "neg_text", "neg", "latent", "width", "height", "steps", "cfg", "sampler_name", "scheduler", "seed", "img", "xyplot")
    FUNCTION = "flush"

    CATEGORY = "Pipeline"

    def flush(self, pipe=None, model=None, clip=None, vae=None, pos_text=None, pos=None, neg_text=None, neg=None, latent=None, width=None, height=None, steps=None, cfg=None, sampler_name=None, scheduler=None, seed=None, img=None, xyplot=None, my_unique_id=None):

        model = model if model is not None else pipe.get("model")
        # Logs are a custom lib not existing yet
        #if model is None:
            # log_node_warn(f'pipeIn[{my_unique_id}]', "Model missing from pipeLine")
        clip = clip if clip is not None else pipe.get("clip") if pipe is not None and "clip" in pipe else None
        # if clip is None:
        #     log_node_warn(f'pipeIn[{my_unique_id}]', "Clip missing from pipeLine")
        vae = vae if vae is not None else pipe.get("vae")
        #if vae is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "VAE missing from pipeLine")

        pos_text = pos_text if pos_text is not None else pipe.get("positive_text")
        pos = pos if pos is not None else pipe.get("positive")
        #if pos is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "Pos Conditioning missing from pipeLine")
        neg_text = neg_text if neg_text is not None else pipe.get("negative_text") 
        neg = neg if neg is not None else pipe.get("negative")
        #if neg is None:
        #    log_node_warn(f'pipeIn[{my_unique_id}]', "Neg Conditioning missing from pipeLine")
        
        if latent is not None:
            samples = latent
        elif image is None:
            samples = pipe.get("samples") if pipe is not None else None
            image = pipe.get("images") if pipe is not None else None
        elif image is not None:
            if pipe is None:
                batch_size = 1
            else:
                batch_size = pipe["loader_settings"]["batch_size"] if "batch_size" in pipe["loader_settings"] else 1
            samples = {"samples": vae.encode(image[:, :, :, :3])}
            samples = RepeatLatentBatch().repeat(samples, batch_size)[0]
        width = width if width is not None else pipe.get("width")
        height = height if height is not None else pipe.get("height")
        steps = steps if steps is not None else pipe.get("steps")
        cfg = cfg if cfg is not None else pipe.get("cfg")
        sampler_name = sampler_name if sampler_name is not None else pipe.get("sampler_name")
        scheduler = scheduler if scheduler is not None else pipe.get("scheduler")
        seed = seed if seed is not None else pipe.get("seed")


        if pipe is None:
            pipe = {"loader_settings": {"positive": "", "negative": "", "xyplot": None}}

        xyplot = xyplot if xyplot is not None else pipe['loader_settings']['xyplot'] if xyplot in pipe['loader_settings'] else None

        new_pipe = {
            **pipe,
            "model": model,
            "positive": pos,
            "negative": neg,
            "vae": vae,
            "clip": clip,

            "samples": samples,
            "images": image,
            "seed": pipe.get('seed') if pipe is not None and "seed" in pipe else None,

            "loader_settings": {
                **pipe["loader_settings"],
                "xyplot": xyplot
            }
        }
        del pipe

        return (new_pipe,)



NODE_CLASS_MAPPINGS = {"ExampleUnpackNode": ExampleUnpackNode}
NODE_DISPLAY_NAME_MAPPINGS = {"ExampleUnpackNode": "Unpack Pipeline"}
