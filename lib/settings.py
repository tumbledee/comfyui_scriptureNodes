import json
import os

# Navigate from this file up to ComfyUI root, then into user/default/
_UTILS_DIR  = os.path.dirname(os.path.abspath(__file__))
_NODE_DIR   = os.path.dirname(_UTILS_DIR)
_COMFY_ROOT = os.path.normpath(os.path.join(_NODE_DIR, "..", ".."))
_SETTINGS_FILE = os.path.join(_COMFY_ROOT, "user", "default", "comfy.settings.json")

# Fallback: use folder_paths if available (more robust across installs)
#try:
#    import folder_paths
#    _SETTINGS_FILE = os.path.join(folder_paths.base_path, "user", "default", "comfy.settings.json")
#except ImportError:
#    pass

_settings_cache: dict = {}

def _load_settings(force_reload: bool = False) -> dict:
    """Load and cache the ComfyUI settings JSON."""
    global _settings_cache
    if _settings_cache and not force_reload:
        return _settings_cache
    if os.path.isfile(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                _settings_cache = json.load(f)
        except Exception as e:
            print(f"[CharacterSystem] Could not read settings: {e}")
            _settings_cache = {}
    return _settings_cache

def get_character_setting(key: str, default="None"):
    """
    Read a single setting by its full JS key.
    Example: get_character_setting("CharacterSystem.RootDirectory", "/my/path")
    Always reloads fresh so nodes see updates without restart.
    """
    settings = _load_settings(force_reload=True)
    return settings.get(key, default)

def get_root_directory() -> str:
    """Convenience: returns the configured root directory or empty string."""
    return get_character_setting("CharacterSystem.RootDirectory", "")

def get_segment_order(segment_type: str = "positive") -> list[dict]:
    """
    Returns the ordered, filtered list of enabled segments.
    segment_type: "positive" | "negative" | "character"
    Returns: [{"id": "quality", "label": "Quality Tags", "enabled": True}, ...]
    """
    key_map = {
        "positive":  "CharacterSystem.SegmentOrderPositive",
        "negative":  "CharacterSystem.SegmentOrderNegative",
        "character": "CharacterSystem.SegmentOrderCharacter",
    }
    raw = get_character_setting(key_map.get(segment_type, ""), "[]")
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []

def get_enabled_segment_ids(segment_type: str = "positive") -> list[str]:
    """Returns only the IDs of enabled segments, in order."""
    return [s["id"] for s in get_segment_order(segment_type) if s.get("enabled", True)]
