import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// #region Notifications
// Disable notifications
const SHOW_NOTIFICATIONS = false; // set to true to re-enable toast pop-ups

function notify(message, isError = false) {
  if (!SHOW_NOTIFICATIONS) return;
  if (isError) {
    app.extensionManager.toast.addAlert(message);
  } else {
    app.extensionManager.toast.add({ severity: "success", summary: message, life: 2500 });
  }
}

// #endregion
// #region API Calls
const NODE_NAMES = ["Checkpoint_w_Settings"];
const NODE_NAME = "Checkpoint_w_Settings";

app.registerExtension({
  name: "checkpoint.settings.buttons",

  async nodeCreated(node) {
    if (node.comfyClass !== NODE_NAME) return;

    const getWidget = (name) => node.widgets.find((w) => w.name === name);
    const trackedFields = ["steps", "cfg", "sampler_name", "scheduler", "positive Prompt", "negative Prompt", "setting Name"];
    // #region Settings
    const collectSettings = () => {
      const out = {};
      trackedFields.forEach((n) => {
        const w = getWidget(n);
        if (w) out[n] = w.value;
      });
      return out;
    };
    // #endregion
    // #region Apply Settings
    const applySettings = (settings) => {
      Object.entries(settings).forEach(([k, v]) => {
        const w = getWidget(k);
        if (w) w.value = v;
      });
      node.setDirtyCanvas(true, true);
    };
    // #endregion
    //------------------------------------------------------------------------------
    // #region Preset Management
    //------------------------------------------------------------------------------
    // Text field for naming a preset before saving
    const presetNameWidget = node.addWidget("text", "preset_name", "default", () => {});

    // Dropdown ("toggle list") of existing presets for the current checkpoint
    const presetSelectWidget = node.addWidget("combo", "preset_select", "", () => {}, { values: [] });

    const refreshPresetList = async () => {
      const ckptWidget = getWidget("ckpt_name");
      const res = await fetch("/checkpoint_settings/list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value }),
      });
      const data = await res.json();
      const presets = data.presets || [];
      presetSelectWidget.options.values = presets;
      presetSelectWidget.value = presets.includes(presetSelectWidget.value) ? presetSelectWidget.value : (presets[0] || "");
      node.setDirtyCanvas(true, true);
    };
    // Refresh dropdown whenever the checkpoint dropdown itself changes
    const ckptWidget = getWidget("ckpt_name");
    const originalCallback = ckptWidget.callback;
    ckptWidget.callback = function (...args) {
      if (originalCallback) originalCallback.apply(this, args);
      refreshPresetList();
    };

    //#endregion    
    //------------------------------------------------------------------------------
    // #region Buttons
    //------------------------------------------------------------------------------
    node.addWidget("button", "💾 Save Preset", null, async () => {
      const name = (presetNameWidget.value || "").trim();
      if (!name) {
        notify("Preset name cannot be empty.", true);
        return;
      }
      const res = await fetch("/checkpoint_settings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: name, settings: collectSettings() }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        await refreshPresetList();
        presetSelectWidget.value = name;
        notify(`Preset "${name}" saved.`);
      } else {
        notify("Save failed: " + data.error, true);
      }
    });
    node.addWidget("button", "📂 Load Preset", null, async () => {
      const name = presetSelectWidget.value;
      if (!name) {
        notify("No preset selected.", true);
        return;
      }
      const res = await fetch("/checkpoint_settings/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: name }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        applySettings(data.settings);
        // Event for Ksampler
        api.dispatchEvent(new CustomEvent("checkpoint_settings.loaded", {
          detail: { ckpt_name: ckptWidget.value, settings: data.settings },
        }));
        notify(`Preset "${name}" loaded.`);
      } else {
        notify("Load failed: " + data.error, true);
      }
    });


    refreshPresetList();
  },
});