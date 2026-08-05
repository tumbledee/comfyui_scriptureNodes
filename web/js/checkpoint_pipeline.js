import { app } from "/scripts/app.js";


/**
 * Data for Pipeline setup
 */


const NODE_NAMES = ["Checkpoint_KSampler_Piped"]

function hideWidget(node, widget) {
  if (widget.hidden) return;
  widget.hidden = true;
  widget.origType = widget.type;
  widget.origComputeSize = widget.computeSize;
  widget.type = "hidden_widget";
  widget.computeSize = () => [0, -4]; // collapses widget space to zero
  node.setDirtyCanvas(true, true);
}

function showWidget(node, widget) {
  if (!widget.hidden) return;
  widget.hidden = false;
  widget.type = widget.origType;
  widget.computeSize = widget.origComputeSize;
  node.setDirtyCanvas(true, true);
}

app.registerExtension({
  name: "checkpoint.pipeline.customratio",

  async nodeCreated(node) {
    if (!NODE_NAMES.includes(node.comfyClass)) return;

    const getWidget = (name) => node.widgets.find((w) => w.name === name);
    const ratioWidget = getWidget("aspect_ratio");
    const widthScaleWidget = getWidget("custom_width_scale");
    const heightScaleWidget = getWidget("custom_height_scale");

    const updateVisibility = () => {
      const isCustom = ratioWidget.value === "Custom";
      if (isCustom) {
        showWidget(node, widthScaleWidget);
        showWidget(node, heightScaleWidget);
      } else {
        hideWidget(node, widthScaleWidget);
        hideWidget(node, heightScaleWidget);
      }
      node.computeSize();
    };

    const originalCallback = ratioWidget.callback;
    ratioWidget.callback = function (...args) {
      if (originalCallback) originalCallback.apply(this, args);
      updateVisibility();
    };

    updateVisibility(); // run once on creation

    const origOnConfigure = node.onConfigure;
    node.onConfigure = function (info) {
      const result = origOnConfigure ? origOnConfigure.apply(this, arguments) : undefined;
      updateVisibility(); // also re-check after workflow reload
      return result;
    };
  },
});