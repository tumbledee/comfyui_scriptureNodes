import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { maybeAutoBackup } from "./backup_settings.js";
//import { Synced_Fields } from "/scripts/ksampler_sync.js";
// import from py for names of synced fields, so we don't have to hardcode them here

/**
 * - Save Load interaction
 * - Settings collection
 * - Preset Management
 * - Find Sync data for Ksampler
 */

// #region Notifications
// Disable notifications
const SHOW_NOTIFICATIONS = false; // set to true to re-enable toast pop-ups

function notify(message, isError = false) {
  if (!SHOW_NOTIFICATIONS || !message.includes("Delete")) return;
  if (isError) {
    app.extensionManager.toast.addAlert(message);
  } else {
    app.extensionManager.toast.add({ severity: "success", summary: message, life: 2500 });
  }
}

// #endregion
// #region Setting load/save
const NODE_NAMES = ["Checkpoint_w_Settings","Checkpoint_w_prompts", "Checkpoint_KSampler_Piped", "Checkpoint_simple", "Checkpoint_minimal"];
const NODE_NAME = "Checkpoint_w_Settings";
const TRACKED_FIELDS = ["steps", "cfg", "sampler_name", "scheduler", "positive_quality_Prompt", "negative_quality_Prompt"];
const KSAMPLER_NAME = "KSampler_Sync";

app.registerExtension({
  name: "checkpoint.settings.buttons",

  async nodeCreated(node) {
    //if (node.comfyClass !== NODE_NAME) return;
    if (!NODE_NAMES.includes(node.comfyClass)) return;

    const getWidget = (name) => node.widgets.find((w) => w.name === name);
    // #region collect Settings
    const collectSettings = () => {
      const out = {};
      TRACKED_FIELDS.forEach((n) => {
        const what = getWidget(n);
        if (what) out[n] = what.value;
      });
      return out;
    };
    // #endregion
    // #region Apply Settings
    const applySettings = (settings) => {
      Object.entries(settings).forEach(([key, value]) => {
        const what = getWidget(key);
        if (what) what.value = value;
      });
      node.setDirtyCanvas(true, true);
    };

    const broadcastCurrentSettings = () => {
      api.dispatchEvent(new CustomEvent("checkpoint_settings.loaded", {
        detail: { ckpt_name: ckptWidget.value, settings: collectSettings() },
      }));
    };

    TRACKED_FIELDS.forEach((fieldName) => {
      const widget = getWidget(fieldName);
      if (!widget) return;

      const originalCallback = widget.callback;
      widget.callback = function (...args) {
        if (originalCallback) originalCallback.apply(this, args);
        broadcastCurrentSettings();
      };
    });
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

    // Safety mechanism to guarantee that a ckpt change is always detected
    let internalCkptValue = ckptWidget.value;
    Object.defineProperty(ckptWidget, "value", {
      get() {
        return internalCkptValue;
      },
      set(newValue) {
        const changed = newValue !== internalCkptValue;
        internalCkptValue = newValue;
        if (changed) {
          // Fires for ANY change source: user click, workflow load, or LoRA Manager's send action
          refreshPresetList().then(autoLoadPreset);
        }
      },
    });

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
        presetNameWidget.value = presetName;
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
      const typedname = (presetNameWidget.value || "").trim();
      const selectedPresetName = presetSelectWidget.value;

      if (!typedname) {
        if(!selectedPresetName){
          notify("Preset name cannot be empty.", true);
          return;
        }
        if (!confirm(`Delete preset "${selectedPresetName}"? This cannot be undone.`)) return;
        // Delete Preset
        const res = await fetch("/checkpoint_settings/delete_preset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: selectedPresetName }),
        });
        const data = await res.json();
        if (data.status === "ok") {
          await refreshPresetList();
          autoLoadPreset();
          notify(`Preset "${data.deleted}" deleted.`);
        } else {
          notify("Delete failed: " + data.error, true);
        }
      }

      // Layer 1: whatever the synced KSampler currently holds
      const ksamplerSettings = findSyncedKSamplerData(node, KSAMPLER_NAME, "enable_sync");
      // Layer 2: Quality prompts from Quality nodes
      //const qualityPrompts = findQualityPrompts(node, "Quality_Sync", "enable_sync");
      // Layer 3: whatever the checkpoint node itself holds (only relevant fields it actually has)
      const ownSettings = collectSettings(); // your existing helper, reads this node's own widgets

      // Merge — own settings overwrite ksampler settings on key conflicts
      // const mergedSettings = { ...ksamplerSettings, ...qualityPrompts, ...ownSettings };
      const mergedSettings = { ...ksamplerSettings, ...ownSettings };

      const res = await fetch("/checkpoint_settings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value, preset_name: typedname, settings: mergedSettings }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        await refreshPresetList();
        presetSelectWidget.value = typedname;
        notify(`Preset "${typedname}" saved.`);
        maybeAutoBackup(); // backup_settings.js
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
// ------------------------------------------------------------------------------
// #region Find Sync Data
// ------------------------------------------------------------------------------
// root function
function findSyncedData(currentCkptNode, nodeName, enableSyncField, retrievefields = ["steps", "cfg", "sampler_name", "scheduler", "positive_quality_Prompt", "negative_quality_Prompt"]) {
  const collected = {};

  for (const node of app.graph.nodes) {
    if (node.comfyClass !== nodeName) continue;

    const syncWidget = node.widgets.find((w) => w.name === enableSyncField);
    if (!syncWidget || syncWidget.value !== true) continue; // only pull from synced nodes

    retrievefields.forEach((fieldName) => {
      const widget = node.widgets.find((w) => w.name === fieldName);
      if (widget) collected[fieldName] = widget.value;
    });

    break; // stop at the first synced KSampler found; remove this line to merge multiple
  }

  return collected;
}
// KSampler-specific wrapper
function findSyncedKSamplerData(currentCkptNode, KSamplerNodeName, enableSyncField) {
  const ksamplerFields = ["steps", "cfg", "sampler_name", "scheduler"];
  const collected = {};
  return findSyncedData(currentCkptNode, KSamplerNodeName, enableSyncField, ksamplerFields);
}
// Quality-specific wrapper
function findQualityPrompts(currentCkptNode, QualityNodeName, enableSyncField) {
  const qualityFields = ["positive_quality_Prompt", "negative_quality_Prompt"];
  return findSyncedData(currentCkptNode, QualityNodeName, enableSyncField, qualityFields);
}
// #endregion