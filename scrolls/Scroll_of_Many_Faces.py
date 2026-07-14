import json
from collections import defaultdict
from ..lib.file_io import save_json, load_json, load_text_lines
from ..lib.settings import get_character_setting

# ── Gender normalisation map ───────────────────────────────────────────────────
# Maps raw gender values from CharacterBuilder to canonical singular / plural tags
GENDER_MAP = {
    # singular → (singular_tag)
    "female": ("girl"),
    "girl":   ("girl"),
    "male":   ("boy"),
    "boy":    ("boy"),
    "other":  ("other"),
}


class Scroll_of_Many_Faces:
    """
    Collects up to 10 CHARACTER dictionaries from CharacterBuilder nodes.

    Output — CHAR_COLLECTION dict:
    {
        "characters":    [ <char_dict>, ... ],          # all connected dicts in order
        "by_id":         { identifier: <char_dict> },   # quick lookup by identifier
        "gender_prompt": "2girls, 1boy",                # resolved count-aware gender string
        "gender_counts": { "girl": 2, "boy": 1 },       # singular-key counts
        "total_count":   3                              # sum of all character counts
    }
    """

    CATEGORY = "Scrolls"

    @classmethod
    def INPUT_TYPES(cls):
        # Build 10 optional CHARACTER slots, all forceInput so they only accept
        # connections from CharacterBuilder (or compatible) nodes.
        optional_inputs = {
            f"character_{i}": ("CHARACTER", {"forceInput": True})
            for i in range(1, 11)
        }
        return {
            "required": {},
            "optional": optional_inputs,
        }

    RETURN_TYPES  = ("CHARACTER_COLLECTOR", "STRING")
    RETURN_NAMES  = ("character_collector", "debug")
    FUNCTION      = "collect_character"

    def collect_character(self, **kwargs):
        # ── Gather all connected CHARACTER dicts in slot order ─────────────────
        connected_chars = []
        for i in range(1, 11):
            slot_key = f"character_{i}"
            char = kwargs.get(slot_key)
            if char is not None:
                connected_chars.append(char)

        # ── Build by_id index ──────────────────────────────────────────────────
        by_id = {}
        for char in connected_chars:
            identifier = char.get("identifier", f"unknown_{len(by_id)}")
            by_id[identifier] = char

        # ── Resolve gender counts ──────────────────────────────────────────────
        # Each character contributes its "count" value toward its gender bucket.
        # gender_counts uses the SINGULAR tag as the key (e.g. "girl", "boy").
        gender_counts: dict[str, int] = defaultdict(int)
        for char in connected_chars:
            raw_gender  = str(char.get("gender", "empty"))
            char_count  = int(char.get("count", 0))
            singular = GENDER_MAP.get(raw_gender, raw_gender)
            gender_counts[singular] += char_count

        # ── Build the gender prompt string ─────────────────────────────────────
        # Order: girls first, boys second, others last for natural prompt flow.

        gender_prompt_parts = []
        for singular_key, total in gender_counts.items():
            # Add "s" suffix when total > 1; use the GENDER_MAP plural if defined
            # otherwise fall back to appending "s".
            tag = singular_key
            test = gender_counts.get(tag)
            if total > 1:
                tag = singular_key + "s"
            gender_prompt_parts.append(f"{total}{tag}")

        gender_prompt = ", ".join(gender_prompt_parts)  # e.g. "2girls, 1boy"

        # ── Total character count (sum of all count fields) ────────────────────
        total_count = sum(int(c.get("count", 1)) for c in connected_chars)

        # ── Assemble output collection ─────────────────────────────────────────
        collection = {
            "characters":    connected_chars,
            "by_id":         by_id,
            "gender_prompt": gender_prompt,
            "gender_counts": dict(gender_counts),  # plain dict for JSON safety
            "total_count":   total_count,
        }
        debug = "test"
        return (collection, debug)


# ── Registration ───────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "scroll_of_many_faces": Scroll_of_Many_Faces,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "scroll_of_many_faces": "Scroll of Many Faces 🗂️",
}
