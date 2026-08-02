import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";



//#endregion

//#region Register in Comfy
// ── Register all settings ────────────────────────────────────────────────────
app.registerExtension({
    name: "Scripture.Settings",

    async setup() {

        // 1. Root directory ──────────────────────────────────────────────────
        app.ui.settings.addSetting({
            id:           KEY_ROOT_DIR,
            name:         "🗂 Root Directory",
            category:     ["AntiPyrus Settings", "Paths", "Root Directory"],
            type:         "text",
            defaultValue: "",
            tooltip:      "Root folder for wildcards, text files and saved characters. " +
                          "All nodes will resolve paths relative to this.",
        });

        // 2. Setup directories button ─────────────────────────────────────────
        app.ui.settings.addSetting({
            id:           KEY_SETUP_BTN,
            name:         "📁 Setup Folder Layout",
            category:     ["AntiPyrus Settings", "Paths", "Setup"],
            defaultValue: null,
            type:         (name, setter, value, attrs) => {
                const wrapper = document.createElement("div");
                wrapper.style.cssText = "display:flex; align-items:center; gap:12px; flex-wrap:wrap;";

                const btn = document.createElement("button");
                btn.textContent = "⚙ Create Directory Layout";
                btn.style.cssText = `
                    padding: 6px 14px; background:#3a6e3a; color:#fff;
                    border:none; border-radius:5px; cursor:pointer; font-size:13px;
                `;

                const status = document.createElement("span");
                status.style.cssText = "font-size:12px; color:#aaa;";

                btn.addEventListener("click", async () => {
                    const rootDir = app.ui.settings.getSettingValue(KEY_ROOT_DIR, "");
                    if (!rootDir) {
                        status.textContent = "⚠ Set a root directory first.";
                        status.style.color = "#e88";
                        return;
                    }
                    btn.disabled    = true;
                    status.textContent = "Creating...";
                    status.style.color = "#aaa";

                    try {
                        const resp = await api.fetchApi("/character_system/setup_directories", {
                            method:  "POST",
                            headers: { "Content-Type": "application/json" },
                            body:    JSON.stringify({ root_dir: rootDir }),
                        });
                        const result = await resp.json();
                        status.textContent = result.message || "Done!";
                        status.style.color = result.status === "ok" ? "#8e8" : "#e88";
                    } catch (err) {
                        status.textContent = `Error: ${err.message}`;
                        status.style.color = "#e88";
                    } finally {
                        btn.disabled = false;
                    }
                });

                wrapper.appendChild(btn);
                wrapper.appendChild(status);
                return wrapper;
            },
        });
    },
});
//#endregion