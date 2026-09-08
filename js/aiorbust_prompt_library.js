/**
 * Aiorbust Prompt Library — Save button and thumbnail gallery.
 *
 * The gallery writes into the node's ordinary multiline `prompt` widget rather
 * than holding a reference to a library entry. That matters: the value is then
 * serialised with the workflow, so a graph shared with someone else — or opened
 * after the library folder has moved — still carries its prompt.
 */

import { app } from "../../scripts/app.js";

const API = "/aiorbust/prompt_library";

function widget(node, name) {
    return node.widgets?.find(w => w.name === name);
}

function setPrompt(node, text) {
    const w = widget(node, "prompt");
    if (!w) return;
    w.value = text;
    if (w.callback) w.callback(text);
    if (w.inputEl) w.inputEl.value = text;
    app.graph.setDirtyCanvas(true, true);
}

async function readJson(resp) {
    // Lu en texte d'abord : une route absente renvoie "404: Not Found", que
    // JSON.parse signale comme un caractere inattendu en position 3 — un
    // message qui cache completement la vraie cause.
    const raw = await resp.text();
    try {
        return JSON.parse(raw);
    } catch (_) {
        throw new Error(resp.status === 404
            ? "route missing — restart ComfyUI (a browser refresh reloads this button "
              + "but not the Python side)"
            : `HTTP ${resp.status} — ${raw.slice(0, 140)}`);
    }
}

// ── Save ─────────────────────────────────────────────────────────────────────

function addSaveButton(node) {
    if (node._promptSaverReady) return;
    node._promptSaverReady = true;

    const btn = node.addWidget("button", "💾  Save prompt to library", null, async () => {
        const prompt = (widget(node, "prompt")?.value || "").trim();
        if (!prompt) {
            alert("Prompt Saver: the prompt field is empty.");
            return;
        }
        btn.name = "⏳  Saving...";
        node.setDirtyCanvas(true);
        try {
            const resp = await fetch(`${API}/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: String(node.id),
                    prompt,
                    name: widget(node, "name")?.value || "",
                    tags: widget(node, "tags")?.value || "",
                }),
            });
            const data = await readJson(resp);
            if (!data.success) throw new Error(data.error || resp.statusText);
            const e = data.entry;
            alert(`Saved: "${e.name}"\n\n${e.chars} characters` +
                  (e.thumb ? "\nThumbnail included."
                           : "\nNo thumbnail — run the graph once with an image connected, " +
                             "then save again."));
        } catch (e) {
            alert("Save failed: " + e.message);
            console.error("[Prompt Library]", e);
        } finally {
            btn.name = "💾  Save prompt to library";
            node.setDirtyCanvas(true);
        }
    });
    btn.serialize = false;
}

// ── Gallery ──────────────────────────────────────────────────────────────────

function styleOnce() {
    if (document.getElementById("aiorbust-pl-style")) return;
    const css = document.createElement("style");
    css.id = "aiorbust-pl-style";
    css.textContent = `
.apl-back{position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:10000;
  display:flex;align-items:center;justify-content:center}
.apl-box{background:#1c1209;border:1px solid #3d2008;border-radius:10px;
  width:min(1100px,92vw);height:min(760px,88vh);display:flex;flex-direction:column;
  color:#eee;font:13px sans-serif;box-shadow:0 12px 48px rgba(0,0,0,.6)}
.apl-head{display:flex;gap:10px;align-items:center;padding:12px 14px;
  border-bottom:1px solid #3d2008}
.apl-head h3{margin:0;color:#f5a623;font-size:15px;flex:0 0 auto}
.apl-head input{flex:1;background:#0d0906;border:1px solid #3d2008;border-radius:6px;
  color:#eee;padding:7px 10px;font:13px sans-serif}
.apl-head button{background:#3d2008;border:1px solid #e87a20;color:#f5a623;
  border-radius:6px;padding:7px 14px;cursor:pointer;font:13px sans-serif}
.apl-grid{flex:1;overflow:auto;padding:14px;display:grid;gap:12px;
  grid-template-columns:repeat(auto-fill,minmax(190px,1fr));align-content:start}
.apl-card{background:#0d0906;border:1px solid #3d2008;border-radius:8px;
  overflow:hidden;cursor:pointer;display:flex;flex-direction:column;position:relative}
.apl-card:hover{border-color:#e87a20}
.apl-card img,.apl-noimg{width:100%;height:150px;object-fit:cover;display:block;background:#000}
.apl-noimg{display:flex;align-items:center;justify-content:center;color:#5a4a3a;font-size:11px}
.apl-name{padding:7px 9px;font-weight:600;color:#f5a623;font-size:12px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.apl-prev{padding:0 9px 8px;color:#9a8a7a;font-size:11px;line-height:1.35;
  max-height:48px;overflow:hidden}
.apl-tags{padding:0 9px 8px;color:#e87a20;font-size:10px}
.apl-del{position:absolute;top:6px;right:6px;background:rgba(0,0,0,.75);
  border:1px solid #663;color:#f88;border-radius:5px;width:24px;height:24px;
  cursor:pointer;line-height:1;font-size:13px}
.apl-empty{padding:40px;text-align:center;color:#7a6a5a;grid-column:1/-1}
`;
    document.head.appendChild(css);
}

async function openGallery(node) {
    styleOnce();
    let entries = [];
    try {
        entries = (await readJson(await fetch(`${API}/list`))).entries || [];
    } catch (e) {
        alert("Could not read the library: " + e.message);
        return;
    }

    const back = document.createElement("div");
    back.className = "apl-back";
    back.innerHTML = `
<div class="apl-box">
  <div class="apl-head">
    <h3>Prompt library</h3>
    <input placeholder="search — name, tag or prompt text" />
    <button data-close>Close</button>
  </div>
  <div class="apl-grid"></div>
</div>`;
    document.body.appendChild(back);

    const grid = back.querySelector(".apl-grid");
    const search = back.querySelector("input");
    const close = () => back.remove();

    back.addEventListener("click", e => { if (e.target === back) close(); });
    back.querySelector("[data-close]").addEventListener("click", close);
    // Escape ferme aussi : une modale sans sortie clavier est un piege.
    const onKey = e => { if (e.key === "Escape") { close(); document.removeEventListener("keydown", onKey); } };
    document.addEventListener("keydown", onKey);

    function render() {
        const q = search.value.trim().toLowerCase();
        const shown = entries.filter(e => !q
            || e.name.toLowerCase().includes(q)
            || e.prompt.toLowerCase().includes(q)
            || (e.tags || []).some(t => t.toLowerCase().includes(q)));

        grid.innerHTML = "";
        if (!shown.length) {
            grid.innerHTML = `<div class="apl-empty">${entries.length
                ? "Nothing matches that search."
                : "The library is empty. Use a Prompt Saver node to add to it."}</div>`;
            return;
        }
        for (const e of shown) {
            const card = document.createElement("div");
            card.className = "apl-card";
            const when = new Date(e.created * 1000).toLocaleDateString();
            card.innerHTML =
                (e.thumb ? `<img loading="lazy" src="${API}/thumb?id=${e.id}">`
                         : `<div class="apl-noimg">no thumbnail</div>`) +
                `<div class="apl-name" title="${e.name.replace(/"/g, "&quot;")}">${e.name}</div>` +
                `<div class="apl-prev">${e.prompt.slice(0, 150).replace(/</g, "&lt;")}…</div>` +
                `<div class="apl-tags">${(e.tags || []).join(" · ")}${e.tags?.length ? " — " : ""}${when} — ${e.chars} ch.</div>` +
                `<button class="apl-del" title="Delete">🗑</button>`;

            card.addEventListener("click", ev => {
                if (ev.target.classList.contains("apl-del")) return;
                setPrompt(node, e.prompt);
                close();
                document.removeEventListener("keydown", onKey);
            });
            card.querySelector(".apl-del").addEventListener("click", async ev => {
                ev.stopPropagation();
                if (!confirm(`Delete "${e.name}" from the library?\nThis cannot be undone.`)) return;
                await fetch(`${API}/delete`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: e.id }),
                });
                entries = entries.filter(x => x.id !== e.id);
                render();
            });
            grid.appendChild(card);
        }
    }

    search.addEventListener("input", render);
    render();
    search.focus();
}

function addGalleryButton(node) {
    if (node._promptGalleryReady) return;
    node._promptGalleryReady = true;
    const btn = node.addWidget("button", "🖼  Browse library", null, () => openGallery(node));
    btn.serialize = false;
}

app.registerExtension({
    name: "aiorbust.PromptLibrary",

    nodeCreated(node) {
        if (node.comfyClass === "AiorbustPromptSaver") {
            setTimeout(() => addSaveButton(node), 200);
        } else if (node.comfyClass === "AiorbustPromptGallery") {
            setTimeout(() => addGalleryButton(node), 200);
        }
    },
});
