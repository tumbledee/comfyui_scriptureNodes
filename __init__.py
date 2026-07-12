
# my_nodes/__init__.py
# ─── Main entry point: registers nodes, API routes, and serves JS ───

import os
import json

from .narrative_Character_node        import NODE_CLASS_MAPPINGS as A, NODE_DISPLAY_NAME_MAPPINGS as A2
from .narrative_Character_Collector_node   import NODE_CLASS_MAPPINGS as B, NODE_DISPLAY_NAME_MAPPINGS as B2
from .narrative_Scene_Builder_node            import NODE_CLASS_MAPPINGS as C, NODE_DISPLAY_NAME_MAPPINGS as C2
from .narrative_Visuals_node            import NODE_CLASS_MAPPINGS as D, NODE_DISPLAY_NAME_MAPPINGS as D2
from .narrative_Story_Script_node import NODE_CLASS_MAPPINGS as E, NODE_DISPLAY_NAME_MAPPINGS as E2
from .narrative_Quality_node          import NODE_CLASS_MAPPINGS as F, NODE_DISPLAY_NAME_MAPPINGS as F2
from .narrative_Story_solver    import NODE_CLASS_MAPPINGS as G, NODE_DISPLAY_NAME_MAPPINGS as G2


NODE_CLASS_MAPPINGS        = {**A, **B, **C, **D, **E, **F, **G}
NODE_DISPLAY_NAME_MAPPINGS = {**A2, **B2, **C2, **D2, **E2, **F2, **G2}


# At the bottom of your __init__.py, after all NODE_CLASS_MAPPINGS merges:
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]