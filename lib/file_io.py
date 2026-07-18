import os
import json
import shutil
from pathlib import Path

# ──────WIP───── SAVE to file ──────────────────────────────────────────────────────
def save_path(save_file_path, customDict):
    save_path = save_file_path.strip()
    if save_path:
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True) \
                if os.path.dirname(save_path) else None
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(customDict, f, indent=2, ensure_ascii=False)
            print(f"[narrative_Character_node] Saved character to: {save_path}")
        except Exception as e:
            print(f"[narrative_Character_node] WARNING: Failed to save '{save_path}': {e}")

        return (customDict,)



# ──────WIP────── Save a JSON file, creating parent dirs automatically ───
def save_json(filepath: str, data: dict) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ──────WIP────── Load a JSON file, returning a default if missing ───
def load_json(filepath: str, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────WIP────── Save plain text, creating parent dirs automatically ───
def save_text(filepath: str, content: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# ──────WIP────── Load plain text, returning empty string if missing ───
def load_text(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# ──────WIP────── Recursively load all .txt files from a folder into a dict ───
def load_wildcard_folder(folder_path: str) -> dict[str, list[str]]:
    wildcards = {}
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".txt"):
                key = Path(root, filename).stem
                lines = load_text(os.path.join(root, filename)).splitlines()
                wildcards[key] = [line.strip() for line in lines if line.strip()]
    return wildcards

# ──────WIP────── Copy a file safely ───
def copy_file(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
# --- new
def save_json(path: str, data: dict) -> None:
    """Save a dict as formatted JSON, auto-creating missing directories."""
    dir_part = os.path.dirname(path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str) -> dict | None:
    """Load JSON from path, returns None if file missing or parse fails."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CharacterSystem] WARNING: Failed to load JSON '{path}': {e}")
        return None

def save_text(path: str, content: str) -> None:
    """Write a plain text string to a file."""
    dir_part = os.path.dirname(path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def load_text_lines(path: str) -> list[str]:
    """Read a .txt file into a list of non-empty, non-comment lines."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]