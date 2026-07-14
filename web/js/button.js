import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "your_suite.my_node_button",

    async nodeCreated(node) {
        if (node.comfyClass !== "MyNode") {
            return;
        }

        node.addWidget(
            "button",
            "Run action",
            "Run action",
            () => {
                console.log("Button clicked on:", node);

                // Example: update a regular serialized widget.
                const promptWidget = node.widgets?.find(
                    (widget) => widget.name === "prompt"
                );

                if (promptWidget) {
                    promptWidget.value = "Button-generated prompt";
                    node.setDirtyCanvas(true, true);
                }
            },
            { serialize: false }
        );
    },
});