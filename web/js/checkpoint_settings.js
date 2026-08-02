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
const NODE_NAMES = ["Checkpoint_w_Settings","Checkpoint_w_prompts", "Checkpoint_simple"];
const NODE_NAME = "Checkpoint_w_Settings";
const TRACKED_FIELDS = ["steps", "cfg", "sampler_name", "scheduler", "positive quality Prompt", "negative quality Prompt", "setting Name"];


app.registerExtension({
  name: "checkpoint.settings.buttons",

  async nodeCreated(node) {
    //if (node.comfyClass !== NODE_NAME) return;
    if (!NODE_NAMES.includes(node.comfyClass)) return;

    const getWidget = (name) => node.widgets.find((w) => w.name === name);
    // #region Settings
    const collectSettings = () => {
      const out = {};
      TRACKED_FIELDS.forEach((n) => {
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

    // Store the current checkpoint name to find the setting data
    const ckptWidget = getWidget("ckpt_name");

    // Auto-load the selected preset when the checkpoint changes or when the node is configured
    const autoLoadPreset = async () => {
      const presetName = presetSelectWidget.value;
      if (!presetName) return;  // if no presets exist for this checkpoint yet
      const res = await fetch("/checkpoint_settings/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: presetName }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        applySettings(data.settings);
        // Event for Ksampler
        api.dispatchEvent(new CustomEvent("checkpoint_settings.loaded", {
          detail: { ckpt_name: ckptWidget.value, settings: data.settings },
        }));
        notify(`Preset "${presetName}" auto-loaded.`);
      }
    };

    // refreshes the preset dropdown list based on the current checkpoint selection
    const refreshPresetList = async () => {
      const res = await fetch("/checkpoint_settings/list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value }),
      });
      const data = await res.json();
      const presets = data.presets || [];
      presetSelectWidget.options.values = presets;

      // Keep current selection if still valid, else fall back to first available preset
      if (!presets.includes(presetSelectWidget.value)) {
        presetSelectWidget.value = presets[0] || "";
      }
      node.setDirtyCanvas(true, true);
    };
    // #endregion
    // ------------------------------------------------------------------------------
    // #region Load Settings Auto
    // ------------------------------------------------------------------------------
    // Load Settings Refresh dropdown whenever the checkpoint dropdown itself changes
    const originalCallback = ckptWidget.callback;
    ckptWidget.callback = function (...args) {
      if (originalCallback) originalCallback.apply(this, args);
      refreshPresetList().then(autoLoadPreset); // auto-load the first preset if available
    };

    // Auto-load whenever the preset dropdown itself changes
    const originalPresetCallback = presetSelectWidget.callback;
    presetSelectWidget.callback = function (...args) {
      if (originalPresetCallback) originalPresetCallback.apply(this, args);
      autoLoadPreset();
    };

    //#endregion    

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
    // -------------- Load button is obsolete now -------------
    //
    // node.addWidget("button", "📂 Load Preset", null, async () => {
    //   const name = presetSelectWidget.value;
    //   if (!name) {
    //     notify("No preset selected.", true);
    //     return;
    //   }
    //   const res = await fetch("/checkpoint_settings/load", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: name }),
    //   });
    //   const data = await res.json();
    //   if (data.status === "ok") {
    //     applySettings(data.settings);
    //     // Event for Ksampler
    //     api.dispatchEvent(new CustomEvent("checkpoint_settings.loaded", {
    //       detail: { ckpt_name: ckptWidget.value, settings: data.settings },
    //     }));
    //     notify(`Preset "${name}" loaded.`);
    //   } else {
    //     notify("Load failed: " + data.error, true);
    //   }
    // });

        //------------------------------------------------------------------------------
    // #region reload presets on node configure 
    const origOnConfigure = node.onConfigure;
    node.onConfigure = function (info) {
      const result = origOnConfigure ? origOnConfigure.apply(this, arguments) : undefined;
      // Widget values are already restored at this point, so ckptWidget.value is correct
      refreshPresetList().then(() => {
        autoLoadPreset();
      });
      return result;
    };
    // #endregion

    // Initial population for freshly-added nodes (not from a saved workflow
    refreshPresetList().then(autoLoadPreset);
  },
});