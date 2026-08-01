from server import PromptServer
from aiohttp import web
import folder_paths
from ..sampling.CheckpointLoaderWithSettings import compute_hash, load_all_settings, save_all_settings
#from ..lib.datastorage import compute_hash, load_all_settings, save_all_settings
# Saves and Stores settings per checkpoint

routes = PromptServer.instance.routes


@routes.post("/checkpoint_settings/save")
async def save_checkpoint_settings(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    settings = body.get("settings", {})
    if not ckpt_name:
        return web.json_response({"error": "ckpt_name missing"}, status=400)

    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    file_hash = compute_hash(ckpt_path) if ckpt_path else None

    data = load_all_settings()
    key = file_hash if file_hash else ckpt_name
    data[key] = {"name": ckpt_name, "hash": file_hash, "settings": settings}
    save_all_settings(data)
    return web.json_response({"status": "ok", "key": key})


@routes.post("/checkpoint_settings/load")
async def load_checkpoint_settings(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    file_hash = compute_hash(ckpt_path) if ckpt_path else None

    data = load_all_settings()
    entry = None
    matched_by = None

    if file_hash and file_hash in data:
        entry = data[file_hash]
        matched_by = "hash"
    else:
        for v in data.values():
            if v.get("name") == ckpt_name:
                entry = v
                matched_by = "name"
                break

    if entry is None:
        return web.json_response({"error": "no saved settings found"}, status=404)

    return web.json_response({"status": "ok", "settings": entry["settings"], "matched_by": matched_by})