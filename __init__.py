
# my_nodes/__init__.py
# ─── Main entry point: registers nodes, API routes, and serves JS ───

import os
import json

from .sampling.Checkpoint_Loader import NODE_CLASS_MAPPINGS as ckptSL, NODE_DISPLAY_NAME_MAPPINGS as ckptSL2
from .sampling.ksampler_sync import NODE_CLASS_MAPPINGS as ksmpSL, NODE_DISPLAY_NAME_MAPPINGS as ksmpSL2
from .nodes.utils.latent_nodes import NODE_CLASS_MAPPINGS as latent, NODE_DISPLAY_NAME_MAPPINGS as latent2
from .backend import api


NODE_CLASS_MAPPINGS        = {**ckptSL, **ksmpSL, **latent}
NODE_DISPLAY_NAME_MAPPINGS = {**ckptSL2, **ksmpSL2, **latent2}


WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]