import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const KEY_AUTOBACKUP_ENABLED = "BackupSettings.AutoBackupEnabled";
const KEY_BACKUP_TIMEFRAME = "BackupSettings.BackupTimeframe";
const KEY_BACKUP_METHOD = "BackupSettings.BackupMethod";

export async function maybeAutoBackup() {
  const enabled = app.ui.settings.getSettingValue(KEY_AUTOBACKUP_ENABLED, true);
  const timeframe = app.ui.settings.getSettingValue(KEY_BACKUP_TIMEFRAME, "once_per_save");
  const method = app.ui.settings.getSettingValue(KEY_BACKUP_METHOD, "single");

  await api.fetchApi("/checkpoint_settings/maybe_backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled, timeframe, method }),
  });
}

function buildBackupRestoreControl() {
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "display:flex; align-items:center; gap:8px; flex-wrap:wrap;";

  const select = document.createElement("select");
  select.style.cssText = "padding:4px 8px; background:#2a2a2a; color:#ddd; border:1px solid #555; border-radius:4px; min-width:220px;";

  const refreshBtn = document.createElement("button");
  refreshBtn.textContent = "⟳";
  refreshBtn.title = "Refresh backup list";
  refreshBtn.style.cssText = "padding:4px 10px; cursor:pointer; background:#333; border:1px solid #555; border-radius:4px; color:#ccc;";

  const restoreBtn = document.createElement("button");
  restoreBtn.textContent = "♻ Retrieve";
  restoreBtn.style.cssText = "padding:6px 14px; background:#3a5e8e; color:#fff; border:none; border-radius:5px; cursor:pointer; font-size:13px;";

  const status = document.createElement("span");
  status.style.cssText = "font-size:12px; color:#aaa;";

  const populate = async () => {
    select.innerHTML = "";
    const resp = await api.fetchApi("/checkpoint_settings/list_backups");
    const data = await resp.json();
    (data.backups || []).forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
  };

  refreshBtn.addEventListener("click", populate);

  restoreBtn.addEventListener("click", async () => {
    const filename = select.value;
    if (!filename) {
      status.textContent = "⚠ No backup selected.";
      status.style.color = "#e88";
      return;
    }
    if (!confirm(`Restore "${filename}"? This will overwrite your current checkpoint_settings.json.`)) return;

    restoreBtn.disabled = true;
    status.textContent = "Restoring...";
    status.style.color = "#aaa";

    try {
      const resp = await api.fetchApi("/checkpoint_settings/restore_backup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      const result = await resp.json();
      if (result.status === "ok") {
        status.textContent = `Restored "${result.restored}".`;
        status.style.color = "#8e8";
      } else {
        status.textContent = `Error: ${result.error}`;
        status.style.color = "#e88";
      }
    } catch (err) {
      status.textContent = `Error: ${err.message}`;
      status.style.color = "#e88";
    } finally {
      restoreBtn.disabled = false;
    }
  });

  populate();

  wrapper.appendChild(select);
  wrapper.appendChild(refreshBtn);
  wrapper.appendChild(restoreBtn);
  wrapper.appendChild(status);
  return wrapper;
}

// ------------------------------------------------------------------------------------------------------------
//#region Register in Settings
app.registerExtension({
  name: "BackupSettings.Backup",

  async setup() {
    app.ui.settings.addSetting({
      id: KEY_AUTOBACKUP_ENABLED,
      name: "💾 Enable Auto-Backup",
      category: ["Calibrate Inscriptions", "Backup", "Enable"],
      type: "boolean",
      defaultValue: true,
      tooltip: "Automatically back up checkpoint_settings.json based on the timeframe and method below.",
    });

    app.ui.settings.addSetting({
      id: KEY_BACKUP_TIMEFRAME,
      name: "⏱ Backup Timeframe",
      category: ["Calibrate Inscriptions", "Backup", "Timeframe"],
      type: "combo",
      options: [
        { value: "once_per_save", text: "Once per save" },
        { value: "on_start", text: "Once on ComfyUI start" },
        { value: "daily", text: "Once per day" },
        { value: "weekly", text: "Once per week" },
      ],
      defaultValue: "once_per_save",
      tooltip: "How often an automatic backup should be attempted.",
    });

    app.ui.settings.addSetting({
      id: KEY_BACKUP_METHOD,
      name: "📦 Backup Method",
      category: ["Calibrate Inscriptions", "Backup", "Method"],
      type: "combo",
      options: [
        { value: "single", text: "Single duplicate (overwrite each time)" },
        { value: "rotating_3", text: "Rotating 3 files (oldest overwritten)" },
        { value: "incremental", text: "Incremental (keep every backup)" },
      ],
      defaultValue: "rotating_3",
      tooltip: "Which backup strategy to use when a backup is triggered.",
    });

    app.ui.settings.addSetting({
      id: "BackupSettings.BackupRestore",
      name: "♻ Restore From Backup",
      category: ["Calibrate Inscriptions", "Backup", "Restore"],
      defaultValue: null,
      type: () => buildBackupRestoreControl(),
    });

    // Trigger "on_start" backup check once, shortly after ComfyUI finishes loading
    setTimeout(() => maybeAutoBackup(), 1500);
  },
});
//#endregion