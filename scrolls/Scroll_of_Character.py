# Character Node
# A node with several character input fields to setup a intricate character for narrative purpose

#input
#- Identifier - Character name
#	any action or interaction with that key is will be assigned to only this character
#- Gender
#- Count - if a generic character, tries to randomize different character
#- Character - if any, also Lora can be used 
#- Character Type - tsundere, mesugaki, slut
#- character value - dynamic character value to influence outputs
#- bodytype
#- nude
#- undearwear
#- Clothing
#- negative
#- save file path
#- load file path

#output:
#- Character Connector
#- file save path 


import os, re
from ..lib.file_io import save_json, load_json, load_text_lines
from ..lib.settings import get_character_setting, get_root_directory
root_dir = get_root_directory()

class Scroll_of_Character:
    """
    Assembles a character definition dictionary and optionally
    saves to / loads from a JSON file.
    """

    CATEGORY = "Scrolls"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "identifier": ("STRING", {"default": "char_01", "multiline": False}),
                "gender": (["female", "male", "other"], {}),
                "count": ("INT", {"default": 1, "min": 1, "max": 20}),
            },
            "optional": {
                "character": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Character name, known character, or LoRA trigger"}),
                "character_type": ("STRING", {"default": "", "multiline": False,
                    "tooltip": "e.g. tsundere, delinquent, kuudere"}),
                "character_value": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Dynamic value to influence wildcard selection and keyword weights"}),
                "hair": ("STRING", {"default": "", "multiline": True}),
                "face": ("STRING", {"default": "", "multiline": True}),
                "bodytype": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Add basic bodyfeatures, everything too detailed and usually covered by clothes should be put into nude"}),
                "nude": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "Nude appearance when no clothing is prompted"}),
                "underwear": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "underwear appearance when no clothing is prompted"}),
                "clothing": ("STRING", {"default": "", "multiline": True}),
                "positive_additional": ("STRING", {"default": "", "multiline": True}),
                "negative_additional": ("STRING", {"default": "", "multiline": True}),
                "save_file_path": ("STRING", {"default": "",
                    "tooltip": "Full path to save character JSON. Leave empty to skip."}),
                "load_file_path": ("STRING", {"default": "",
                    "tooltip": "Full path to load character JSON. Overrides all inputs above if set."}),
            }
        }

    RETURN_TYPES = ("CHARACTER", "STRING")
    RETURN_NAMES = ("character_connector", "character_preview")
    FUNCTION = "build_character"


    def build_character(
        self,
        identifier,
        gender,
        count,
        character="",
        character_type="",
        character_value=0.0,
        hair="",
        face="",
        bodytype="",
        nude="",
        underwear="",
        clothing="",
        positive_additional="",
        negative_additional="",
        save_file_path="",
        load_file_path="",
    ):
        # ── LOAD from file (overrides all widget inputs) ──────────────────────


        # ── BUILD dictionary from widget inputs ───────────────────────────────
        char_dict = {
            "identifier":          identifier,
            "gender":              gender,
            "count":               count,
            "character":           character,
            "character_type":      character_type,
            "character_value":     character_value,
            "hair":                hair,
            "face":                face,
            "bodytype":            bodytype,
            "nude":                nude,
            "underwear":           underwear,
            "clothing":            clothing,
            "positive_additional": positive_additional,
            "negative_additional": negative_additional,
        }

        # ── SAVE to file ──────────────────────────────────────────────────────


# ── Registration ───────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "scroll_of_character": Scroll_of_Character,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "scroll_of_character": "Scroll of Character 🎭",
}
