from server import PromptServer
from aiohttp import web
import folder_paths
from ..lib.datastorage import compute_hash, load_all_settings, save_all_settings, find_entry_key
# Saves and Stores settings per checkpoint


# Routes reading messages from the frontend and trigger save/loading
routes = PromptServer.instance.routes

@routes.post("/checkpoint_settings/save")
async def save_checkpoint_settings(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    preset_name = body.get("preset_name", "").strip()
    settings = body.get("settings", {})
    if not ckpt_name or not preset_name:
        return web.json_response({"error": "ckpt_name or preset_name missing"}, status=400)

    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    file_hash = compute_hash(ckpt_path) if ckpt_path else None
    # Implement Check to make sure hash doesn't exist yet

    data = load_all_settings()
    #key = ckpt_name if ckpt_name else file_hash
    key = find_entry_key(data, ckpt_name, file_hash) or file_hash or ckpt_name
    if key not in data:
        data[key] = {"name": ckpt_name, "hash": file_hash, "presets": {}}

    data[key]["presets"][preset_name] = settings
    save_all_settings(data)
    return web.json_response({"status": "ok", "key": key})


@routes.post("/checkpoint_settings/load")
async def load_checkpoint_settings(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    preset_name = body.get("preset_name")

    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    # Disable filehash for second improvement
    file_hash = compute_hash(ckpt_path) if ckpt_path else None

    data = load_all_settings()
    key = find_entry_key(data, ckpt_name, file_hash)
    if key is None or preset_name not in data[key]["presets"]:
        return web.json_response({"error": "preset not found"}, status=404)

    return web.json_response({"status": "ok", "settings": data[key]["presets"][preset_name]})

@routes.post("/checkpoint_settings/list")
async def list_checkpoint_presets(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    file_hash = compute_hash(ckpt_path) if ckpt_path else None

    data = load_all_settings()
    key = find_entry_key(data, ckpt_name, file_hash)

    presets = list(data[key]["presets"].keys()) if key else []
    return web.json_response({"status": "ok", "presets": presets})
