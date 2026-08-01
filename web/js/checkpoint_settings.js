import { app } from "/scripts/app.js";

app.registerExtension({
  name: "checkpoint.settings.buttons",

  async nodeCreated(node) {
    if (node.comfyClass !== "CheckpointLoaderWithSettings") return;

    const getWidget = (name) => node.widgets.find((w) => w.name === name);
    const trackedFields = ["steps", "cfg", "sampler_name", "scheduler", "width", "height"];

    const collectSettings = () => {
      const out = {};
      trackedFields.forEach((n) => {
        const w = getWidget(n);
        if (w) out[n] = w.value;
      });
      return out;
    };

    const applySettings = (settings) => {
      Object.entries(settings).forEach(([k, v]) => {
        const w = getWidget(k);
        if (w) w.value = v;
      });
      node.setDirtyCanvas(true, true);
    };

    node.addWidget("button", "💾 Save Settings", null, async () => {
      const ckptWidget = getWidget("ckpt_name");
      const res = await fetch("/checkpoint_settings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value, settings: collectSettings() }),
      });
      const data = await res.json();
      alert(data.status === "ok" ? "Settings saved." : "Save failed: " + data.error);
    });

    node.addWidget("button", "📂 Load Settings", null, async () => {
      const ckptWidget = getWidget("ckpt_name");
      const res = await fetch("/checkpoint_settings/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ckpt_name: ckptWidget.value }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        applySettings(data.settings);
        alert("Settings loaded (matched by " + data.matched_by + ").");
      } else {
        alert("Load failed: " + data.error);
      }
    });
  },
});