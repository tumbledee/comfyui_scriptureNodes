# Narration Node
#A node containing a positive and negative prompt where a simple action is stated and used as a base to unfold a story, based on the number of lines contained

#input:
#- Positive
#- Negative
#- subIterations - the count of how many batches will be cooked per narrative line
#- Save File Path
#- Load FIle Path

#output:
#- narrative slot

# Future Ideas:
# - new random seed only after certain iterations 
# 
# 
# 
# 
# 
# 
# 
# 

import json
import os
import math
import random
from ..lib.file_io import save_json, load_json, load_text_lines
from ..lib.settings import get_root_directory
# ---------------------------------------------------------------------------
# Persistent state store keyed by node unique_id.
# Survives re-execution within the same ComfyUI session.
# ---------------------------------------------------------------------------
root_dir = get_root_directory()
_narrative_state: dict[str, dict] = {}


class Scroll_of_Stories:
    """
    Manages a multi-line positive/negative script.
    Each line = one generation step. Supports sub-iterations per line.
    Iteration and sub-iteration are persistent across queue runs.
    """

    CATEGORY = "Scrolls"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive_script": ("STRING", {
                    "multiline": True,
                    "default": ":char1: walking in :sceneKey:\n:char1: waving to :char2: approaching in the distance\n:char1: hugging :char2: as greeding\n:char1: and :char2: preparing picknic on a grass\n:char1: and :char2: preparing picknic together on grass",
                    "tooltip": "One prompt line per image-group. Total images = lines x sub_iterations\nuse identifier to call variables",
                }),
                "negative_script": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Negative lines matched by index. Excess lines ignored, missing lines repeat last.",
                }),
                "sub_iterations": ("INT", {
                    "default": 1, "min": 1, "max": 64, "step": 1,
                    "display": "slider",
                    "tooltip": "How many images to generate per line before advancing to the next line.",
                }),
                "auto_advance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Automatically advance iteration/sub_iteration on each execution.",
                }),
                "seed_modes": (["Random", "Random iterative", "Random per Story Line"], {
                    "tooltip": "True random, generates a new seed every generation \nRandom once and adds each iteration up to the seed\nGenerates a new seed with each new line and iterates up until the next line",
                }),
                "seed": ("INT", {
                    "default": -1, "min": -1, "max": 2**32,
                    "tooltip": "-1 = random each run, ≥0 = deterministic",
                }),
            },
            "optional": {
                "selected_line": ("INT", {
                    "default": 0, "min": 0, "max": 999, "step": 1,
                    "display": "slider",
                    "tooltip": "Manual line selector (hidden when auto_advance=True)",
                    "forceInput": False,  # Hidden when not connected
                }),
                "save_file_path": ("STRING", {
                    "default": "",
                    "tooltip": "Save script text (not counters) to this path as JSON.",
                }),
                "load_file_path": ("STRING", {
                    "default": "",
                    "tooltip": "Load script text from this path. Populates positive/negative fields.",
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STORY", "STRING", "INT", "INT")
    RETURN_NAMES = ("story","preview", "iteration", "total_count")
    FUNCTION = "extecute"
    OUTPUT_IS_LIST = (True, True, True, True)  # ← KEY FIX: Expands ALL outputs, leads to multi generations although 1 run is set

    @classmethod
    def IS_CHANGED(cls, positive_script, negative_script, sub_iterations, auto_advance, **kwargs):
    #def IS_CHANGED(cls, positive_script, negative_script, iteration ,sub_iterations, auto_advance, save_file_path="", load_file_path="" ,unique_id=None):
        # Always re-run when auto_advance is on (NaN != NaN)
        if auto_advance:
            return float("NaN")
        # Otherwise, check content changes
        return (positive_script, negative_script, sub_iterations)

    def extecute(
        self,
        positive_script,
        negative_script,
        sub_iterations,
        seed_modes,
        seed,
        auto_advance,
        selected_line=0,
        save_file_path="",
        load_file_path="",
        unique_id=None,
    ):
        # ── LOAD script text from file (overwrites widget text) ───────────────


        # ── Parse lines ───────────────────────────────────────────────────────
        pos_lines = [line for line in positive_script.splitlines() if line.strip()]
        neg_lines = [line for line in negative_script.splitlines() if line.strip()]
        total_lines = max(len(pos_lines), 1)
        total_iterations = total_lines * sub_iterations


        # ── Determine start line ────────────────────────────────────────────
        start_line = 0
        if not auto_advance:
            # Manual mode: use selected_line slider
            start_line = selected_line % total_lines
        else:
            # Auto mode: always start from 0
            uid = str(unique_id) if unique_id else "default"
            state = _narrative_state.setdefault(uid, {"start_line": 0})
            start_line = state.get("start_line", 0)

        # ── Generate ALL combinations from start_line ───────────────────────
        stories = []
        debugs = []
        current_iters = []
        total_iters = [total_iterations] * total_iterations  # constant
        

        rng = seed if seed >= 0 else random.randint(0, 2**32)
        iteration_counter = 0
        for line_id in range(start_line, total_lines):
            for sub_id in range(sub_iterations):
                # Resolve current prompts for this (line, sub) pair
                current_positive = pos_lines[line_id % len(pos_lines)]
                neg_id = min(line_id, len(neg_lines) - 1)
                current_negative = neg_lines[neg_id] if neg_lines and neg_id < len(neg_lines) else ""
                
                # ── Parse lines ───────────────────────────────────────────────────────
                # ── Resolve effective seed ────────────────────────────────────────────
                if(seed_modes == "Random"):
                    rng = seed if seed >= 0 else random.randint(0, 2**32)
                if(seed_modes == "Random iterative"):
                    rng += 1
                if(seed_modes == "Random per Story Line"):
                    rng = rng+1 if seed >= 0 & rng + iteration_counter <= rng + sub_iterations else random.randint(0, 2**32)

                story_dict = {
                    "positive_script":   positive_script,
                    "negative_script":   negative_script,
                    "current_positive":  current_positive,
                    "current_negative":  current_negative,
                    "line_index":        line_id,
                    "sub_index":         sub_id,
                    "sub_iterations":    sub_iterations,
                    "total_lines":       total_lines,
                    "total_iterations":  total_iterations,
                    "iteration":         iteration_counter,  # 0,1,2,... for downstream use
                    "seed_modes":        seed_modes,
                    "seed":              rng
                }
                
                debug = self._render_debug(story_dict)
                
                stories.append(story_dict)
                debugs.append(debug)
                current_iters.append(iteration_counter)
                iteration_counter += 1
        
        # ── Update state for next manual run ────────────────────────────────
        if not auto_advance and len(stories) > 0:
            uid = str(unique_id) if unique_id else "default"
            _narrative_state[uid] = {"start_line": start_line + 1}
        
        print(f"[NarrativeScript] Generated {len(stories)} / {total_iterations} iterations "
              f"(lines={total_lines}, subs={sub_iterations})")
        
        return (
            stories,        # Single STORY dict per iteration
            debugs,
            current_iters,  # 0,1,2,3,... 
            total_iters,
        )
    @staticmethod
    def _render_debug(d: dict) -> str:
        sep = "─" * 48
        progress = f"Iter {d['iteration']} | L{d['line_index']+1}/{d['total_lines']} S{d['sub_index']+1}/{d['sub_iterations']}"
        return "\n".join([
            f"╔ STORY [{progress}]",
            sep,
            f"  ► POS: {d['current_positive'][:80]}...",
            f"  ► NEG: {d['current_negative'][:80]}...",
            f"  Total iterations: {d['total_iterations']}",
            "╚" + sep,
        ])

NODE_CLASS_MAPPINGS    = {"scroll_of_stories": Scroll_of_Stories}
NODE_DISPLAY_NAME_MAPPINGS = {"scroll_of_stories": "Scroll of Stories 📜"}
