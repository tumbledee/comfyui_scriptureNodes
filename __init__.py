
# my_nodes/__init__.py
# ─── Main entry point: registers nodes, API routes, and serves JS ───

import os
import json

from .sampling.CheckpointLoaderWithSettings import NODE_CLASS_MAPPINGS as ckptSL, NODE_DISPLAY_NAME_MAPPINGS as ckptSL2
from .sampling.ksampler_loader import NODE_CLASS_MAPPINGS as ksmpSL, NODE_DISPLAY_NAME_MAPPINGS as ksmpSL2
from .scrolls.Scroll_of_Character           import NODE_CLASS_MAPPINGS as A, NODE_DISPLAY_NAME_MAPPINGS as A2
from .scrolls.Scroll_of_Character_simple    import NODE_CLASS_MAPPINGS as AA, NODE_DISPLAY_NAME_MAPPINGS as AA2
from .scrolls.Scroll_of_Many_Faces          import NODE_CLASS_MAPPINGS as B, NODE_DISPLAY_NAME_MAPPINGS as B2
from .scrolls.Scroll_of_Sceneries           import NODE_CLASS_MAPPINGS as C, NODE_DISPLAY_NAME_MAPPINGS as C2
from .scrolls.Scroll_of_Beauty              import NODE_CLASS_MAPPINGS as D, NODE_DISPLAY_NAME_MAPPINGS as D2
from .scrolls.Scroll_of_Stories             import NODE_CLASS_MAPPINGS as E, NODE_DISPLAY_NAME_MAPPINGS as E2
from .scrolls.Scroll_of_Quality             import NODE_CLASS_MAPPINGS as F, NODE_DISPLAY_NAME_MAPPINGS as F2
from .scrolls.Scroll_of_Binding             import NODE_CLASS_MAPPINGS as G, NODE_DISPLAY_NAME_MAPPINGS as G2
from .backend import api  # importing this runs api.py, which registers the routes


NODE_CLASS_MAPPINGS        = {**ckptSL, **ksmpSL, **A, **AA, **B, **C, **D, **E, **F, **G}
NODE_DISPLAY_NAME_MAPPINGS = {**ckptSL2, **ksmpSL2, **A2, **AA2, **B2, **C2, **D2, **E2, **F2, **G2}


# At the bottom of your __init__.py, after all NODE_CLASS_MAPPINGS merges:
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]