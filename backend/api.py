from server import PromptServer
from aiohttp import web
import folder_paths
from ..lib.datastorage import compute_hash, load_all_settings, save_all_settings, find_entry_key
# Saves and Stores settings per checkpoint


# region Settings Save Load 
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

@routes.post("/checkpoint_settings/delete_preset")
async def delete_preset(request):
    body = await request.json()
    ckpt_name = body.get("ckpt_name")
    preset_name = body.get("preset_name", "").strip()

    if not preset_name:
        return web.json_response({"error": "preset_name missing"}, status=400)

    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    file_hash = compute_hash(ckpt_path) if ckpt_path else None

    data = load_all_settings()
    key = find_entry_key(data, ckpt_name, file_hash)

    if key is None or preset_name not in data[key]["presets"]:
        return web.json_response({"error": "preset not found"}, status=404)

    del data[key]["presets"][preset_name]
    save_all_settings(data)
    return web.json_response({"status": "ok", "deleted": preset_name})

# endregion
# ---------------------------------------------------------------------------------------------
# region Settings Backup

@routes.post("/checkpoint_settings/backup_now")
async def backup_now(request):
    body = await request.json()
    method = body.get("method", "single")
    filename = perform_backup(method)
    if filename is None:
        return web.json_response({"error": "no settings file to back up yet"}, status=404)
    return web.json_response({"status": "ok", "filename": filename})


@routes.post("/checkpoint_settings/maybe_backup")
async def maybe_backup(request):
    body = await request.json()
    enabled = body.get("enabled", True)
    timeframe = body.get("timeframe", "once_per_save")
    method = body.get("method", "single")

    if not enabled:
        return web.json_response({"status": "skipped", "reason": "disabled"})

    if not is_backup_due(timeframe):
        return web.json_response({"status": "skipped", "reason": "not due yet"})

    filename = perform_backup(method)
    if filename:
        mark_backup_done(timeframe)
        return web.json_response({"status": "ok", "filename": filename})

    return web.json_response({"status": "skipped", "reason": "nothing to back up"})


@routes.get("/checkpoint_settings/list_backups")
async def list_backups_route(request):
    return web.json_response({"status": "ok", "backups": list_backups()})


@routes.post("/checkpoint_settings/restore_backup")
async def restore_backup_route(request):
    body = await request.json()
    filename = body.get("filename")
    if not filename:
        return web.json_response({"error": "filename missing"}, status=400)

    success = restore_backup(filename)
    if success:
        return web.json_response({"status": "ok", "restored": filename})
    return web.json_response({"error": "backup file not found"}, status=404)

# endregion
# ---------------------------------------------------------------------------------------------
# region Hash

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

from ..lib.backup_manager import (
    perform_backup, list_backups, restore_backup, is_backup_due, mark_backup_done
)


