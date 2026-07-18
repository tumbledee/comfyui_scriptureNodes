import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ── Setting key constants ────────────────────────────────────────────────────
const KEY_ROOT_DIR        = "CharacterSystem.RootDirectory";
const KEY_SETUP_BTN       = "CharacterSystem.SetupDirectoriesButton";
const KEY_SEG_ORDER_POS   = "CharacterSystem.SegmentOrderPositive";
const KEY_SEG_ORDER_NEG   = "CharacterSystem.SegmentOrderNegative";
const KEY_SEG_ORDER_CHAR  = "CharacterSystem.SegmentOrderCharacter";

// ── Default segment lists ────────────────────────────────────────────────────
// Each list is stored as a JSON string: [{id, label, enabled}, ...]
const DEFAULT_POSITIVE_SEGMENTS = JSON.stringify([
    { id: "quality",    label: "Quality Tags",        enabled: true },
    { id: "style",      label: "Style + Gender Count", enabled: true },
    { id: "scene",      label: "Scene Environment",    enabled: true },
    { id: "narrative",  label: "Narrative Line",       enabled: true },
    { id: "characters", label: "Character Blocks",     enabled: true },
    { id: "lighting",   label: "Lighting + Camera",    enabled: true },
    { id: "vfx",        label: "VFX",                  enabled: true },
    { id: "loras",      label: "LoRAs + Additions",    enabled: true },
]);

const DEFAULT_NEGATIVE_SEGMENTS = JSON.stringify([
    { id: "quality_neg",   label: "Quality Negative",    enabled: true },
    { id: "narrative_neg", label: "Narrative Negative",  enabled: true },
    { id: "scene_neg",     label: "Scene Negative",      enabled: true },
    { id: "char_neg",      label: "Character Negatives", enabled: true },
    { id: "extra_neg",     label: "Extra Negative",      enabled: true },
]);

const DEFAULT_CHAR_SEGMENTS = JSON.stringify([
    { id: "char_description", label: "Character Description", enabled: true },
    { id: "char_type",        label: "Character Type",        enabled: true },
    { id: "hair",             label: "Hair",                  enabled: true },
    { id: "face",             label: "Face",                  enabled: true },
    { id: "bodytype",         label: "Body Type",             enabled: true },
    { id: "clothing",         label: "Clothing",              enabled: true },
    { id: "actions",          label: "Actions / Modifiers",   enabled: true },
]);

// ── Helper: build a draggable toggle list DOM element ───────────────────────
function buildSegmentList(settingKey, defaultJson, currentValue) {
    let segments;
    try {
        segments = JSON.parse(currentValue || defaultJson);
    } catch {
        segments = JSON.parse(defaultJson);
    }

    const container = document.createElement("div");
    container.style.cssText = "display:flex; flex-direction:column; gap:4px; min-width:280px;";

    const saveList = () => {
        const updated = [...container.querySelectorAll(".seg-item")].map(item => ({
            id:      item.dataset.id,
            label:   item.dataset.label,
            enabled: item.querySelector("input[type=checkbox]").checked,
        }));
        app.ui.settings.setSettingValue(settingKey, JSON.stringify(updated));
    };

    const rebuildItems = (segs) => {
        container.innerHTML = "";
        segs.forEach((seg, index) => {
            const row = document.createElement("div");
            row.className = "seg-item";
            row.dataset.id    = seg.id;
            row.dataset.label = seg.label;
            row.draggable = true;
            row.style.cssText = `
                display:flex; align-items:center; gap:8px; padding:4px 8px;
                background:#2a2a2a; border-radius:4px; cursor:grab;
                border: 1px solid #444; user-select:none;
            `;

            // Drag handle
            const handle = document.createElement("span");
            handle.textContent = "⠿";
            handle.style.cssText = "color:#888; font-size:16px; cursor:grab;";

            // Toggle checkbox
            const checkbox = document.createElement("input");
            checkbox.type    = "checkbox";
            checkbox.checked = seg.enabled;
            checkbox.addEventListener("change", saveList);

            // Label
            const label = document.createElement("span");
            label.textContent = seg.label;
            label.style.cssText = "flex:1; font-size:13px;";

            // Up / Down buttons
            const btnUp = document.createElement("button");
            btnUp.textContent = "↑";
            btnUp.style.cssText = "padding:1px 6px; cursor:pointer; background:#333; border:1px solid #555; border-radius:3px; color:#ccc;";
            btnUp.addEventListener("click", () => {
                if (index > 0) {
                    [segs[index - 1], segs[index]] = [segs[index], segs[index - 1]];
                    rebuildItems(segs);
                    saveList();
                }
            });

            const btnDown = document.createElement("button");
            btnDown.textContent = "↓";
            btnDown.style.cssText = "padding:1px 6px; cursor:pointer; background:#333; border:1px solid #555; border-radius:3px; color:#ccc;";
            btnDown.addEventListener("click", () => {
                if (index < segs.length - 1) {
                    [segs[index], segs[index + 1]] = [segs[index + 1], segs[index]];
                    rebuildItems(segs);
                    saveList();
                }
            });

            row.appendChild(handle);
            row.appendChild(checkbox);
            row.appendChild(label);
            row.appendChild(btnUp);
            row.appendChild(btnDown);
            container.appendChild(row);
        });
    };

    rebuildItems(segments);
    return container;
}

// ── Register all settings ────────────────────────────────────────────────────
app.registerExtension({
    name: "CharacterSystem.Settings",

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

        // 3. Positive segment order ───────────────────────────────────────────
        app.ui.settings.addSetting({
            id:           KEY_SEG_ORDER_POS,
            name:         "🟢 Positive Prompt Segment Order",
            category:     ["AntiPyrus Settings", "Segment Order", "Positive"],
            defaultValue: DEFAULT_POSITIVE_SEGMENTS,
            tooltip:      "Drag to reorder, toggle to enable/disable each section in the final positive prompt.",
            type:         (name, setter, value) => {
                return buildSegmentList(KEY_SEG_ORDER_POS, DEFAULT_POSITIVE_SEGMENTS, value);
            },
        });

        // 4. Negative segment order ───────────────────────────────────────────
        app.ui.settings.addSetting({
            id:           KEY_SEG_ORDER_NEG,
            name:         "🔴 Negative Prompt Segment Order",
            category:     ["AntiPyrus Settings", "Segment Order", "Negative"],
            defaultValue: DEFAULT_NEGATIVE_SEGMENTS,
            tooltip:      "Drag to reorder, toggle to enable/disable each section in the final negative prompt.",
            type:         (name, setter, value) => {
                return buildSegmentList(KEY_SEG_ORDER_NEG, DEFAULT_NEGATIVE_SEGMENTS, value);
            },
        });

        // 5. Character block segment order ────────────────────────────────────
        app.ui.settings.addSetting({
            id:           KEY_SEG_ORDER_CHAR,
            name:         "🟣 Character Block Segment Order",
            category:     ["AntiPyrus Settings", "Segment Order", "Character Blocks"],
            defaultValue: DEFAULT_CHAR_SEGMENTS,
            tooltip:      "Drag to reorder the fields assembled per-character in the prompt.",
            type:         (name, setter, value) => {
                return buildSegmentList(KEY_SEG_ORDER_CHAR, DEFAULT_CHAR_SEGMENTS, value);
            },
        });
    },
});
