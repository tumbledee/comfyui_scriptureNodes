import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

const SYNCED_FIELDS = ["steps", "cfg", "sampler_name", "scheduler"];

app.registerExtension({
  name: "ksampler.checkpoint.sync",

  async setup() {
    api.addEventListener("checkpoint_settings.loaded", (event) => {
      const { settings } = event.detail;

      for (const node of app.graph.nodes) {
        if (node.comfyClass !== "KSamplerFromCheckpointDB") continue;

        SYNCED_FIELDS.forEach((fieldName) => {
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