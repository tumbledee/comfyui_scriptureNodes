import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
// import from py for names of synced fields, so we don't have to hardcode them here


// all
const KSAMPLER_SYNCED_FIELDS = ["steps", "cfg", "sampler_name", "scheduler"];
const KSAMPLER_NODE_NAMES = ["KSampler_Sync",""]; 
const KSAMPLER_NODE_NAME = "KSampler_Sync";
const KSAMPLER_SYNC_WIDGET_NAME = "enable_sync";  

app.registerExtension({
  name: "ksampler.checkpoint.sync",

  async nodeCreated(node) {
    if (node.comfyClass !== KSAMPLER_NODE_NAME) return;
    const syncWidget = node.widgets.find((w) => w.name === KSAMPLER_SYNC_WIDGET_NAME);
    if (!syncWidget) return;

    const originalCallback = syncWidget.callback;
    syncWidget.callback = function (...args) {
      if (originalCallback) originalCallback.apply(this, args);
      node.bgcolor = syncWidget.value ? undefined : "#553333"; // reddish tint when sync is off
      node.setDirtyCanvas(true, true);
    };
  },


  async setup() {
    api.addEventListener("checkpoint_settings.loaded", (event) => {
      const { settings } = event.detail;

      for (const node of app.graph.nodes) {
        if (node.comfyClass !== KSAMPLER_NODE_NAME) continue;

        const syncWidget = node.widgets.find((w) => w.name === KSAMPLER_SYNC_WIDGET_NAME);
        if (!syncWidget || syncWidget.value !== true) continue; // skip unchecked nodes

        KSAMPLER_SYNCED_FIELDS.forEach((fieldName) => {
          const widget = node.widgets.find((w) => w.name === fieldName);
          if (widget && settings[fieldName] !== undefined) {
            widget.value = settings[fieldName];
          }
        });

        node.setDirtyCanvas(true, true);
      }
    });
  },
});