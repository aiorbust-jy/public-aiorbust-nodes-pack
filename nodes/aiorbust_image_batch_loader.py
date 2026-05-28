"""
Aiorbust Image Batch Loader
Sequential image batch loader with drag-and-drop UI.
Loads images one at a time in order, cycling through the uploaded list.
"""

import os
import json
import uuid
import hashlib
import torch
import numpy as np
from PIL import Image
from aiohttp import web
import folder_paths
from server import PromptServer

# ─────────────────────────────────────────────────────────────────────────────
_POOL_SUBDIR = "Aiorbust_ImagePool"
_THUMB_PREFIX = "thumb_"


def _pool_dir() -> str:
    d = os.path.join(folder_paths.get_input_directory(), _POOL_SUBDIR)
    os.makedirs(d, exist_ok=True)
    return d


# ─────────────────────────────────────────────────────────────────────────────
class AiorbustImageBatchLoader:
    """
    Aiorbust Image Batch Loader
    Upload images via the node UI and process them sequentially.
    Each execution loads the next image in the list.
    Click «Queue All» to process every image.
    """

    _states: dict = {}  # state_key → {"current_index": int}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Managed entirely by the JS widget — hidden from the user via JS.
                "batch_data": ("STRING", {"default": "{}"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES  = ("IMAGE",)
    RETURN_NAMES  = ("image",)
    OUTPUT_NODE   = False
    FUNCTION      = "load_next"
    CATEGORY      = "Aiorbust"
    DESCRIPTION   = (
        "Sequential batch image loader.\n"
        "Upload images via the node UI, then click Queue All.\n"
        "Each queue run outputs the next image in the list."
    )

    # ─────────────────────────────────────────────────────────────────────────
    def load_next(self, batch_data: str = "{}", unique_id=None):
        # ── Parse data ────────────────────────────────────────────────────────
        try:
            data = json.loads(batch_data) if batch_data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}

        images_meta = [
            x for x in data.get("images", [])
            if isinstance(x, dict) and x.get("id")
        ]
        order = [x for x in data.get("order", []) if isinstance(x, str)]

        empty = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        if not images_meta or not order:
            return (empty,)

        # Build ordered flat list
        flat = []
        for img_id in order:
            meta = next((m for m in images_meta if m["id"] == img_id), None)
            if meta:
                flat.append(meta)

        total = len(flat)
        if total == 0:
            return (empty,)

        # ── Sequential state ──────────────────────────────────────────────────
        state_key = f"{unique_id}_{hashlib.md5(batch_data.encode()).hexdigest()[:8]}"
        if state_key not in self._states:
            self._states[state_key] = {"current_index": 0}

        idx   = self._states[state_key]["current_index"] % total
        meta  = flat[idx]
        _next = (idx + 1) % total
        self._states[state_key]["current_index"] = _next

        # ── Load image ────────────────────────────────────────────────────────
        pool = _pool_dir()
        img_path = os.path.join(pool, meta["filename"])

        if not os.path.exists(img_path):
            print(f"[Aiorbust Batch] Image not found: {img_path}")
            self._notify(unique_id, idx, total)
            return (empty,)

        try:
            pil_img = Image.open(img_path).convert("RGB")
            arr     = np.array(pil_img).astype(np.float32) / 255.0
            tensor  = torch.from_numpy(arr).unsqueeze(0)
            name    = meta.get("original_name", meta["filename"])
            print(f"[Aiorbust Batch] ✅ [{idx + 1}/{total}] {name}")
        except Exception as e:
            print(f"[Aiorbust Batch] ❌ Error loading {meta['filename']}: {e}")
            self._notify(unique_id, idx, total)
            return (empty,)

        self._notify(unique_id, idx, total)
        return (tensor,)

    @staticmethod
    def _notify(node_id, current_index: int, total: int):
        try:
            PromptServer.instance.send_sync(
                "aiorbust_batch_loader_update",
                {"node_id": str(node_id), "current_index": current_index, "total": total},
            )
        except Exception:
            pass

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")  # Always re-execute


# ─────────────────────────────────────────────────────────────────────────────
# API Routes
#
# Guard : evite le crash "Cannot register a resource into frozen router"
# quand ComfyUI re-importe le module au restart. Sans ce guard, les
# decorateurs ci-dessous sont re-executes -> aiohttp leve une exception ->
# shutdown bloque -> port 8190 + DB lock restent detenus -> nouveau ComfyUI
# ne peut pas demarrer. Pattern identique a celui utilise dans nano_banana_aio.
# ─────────────────────────────────────────────────────────────────────────────

if not getattr(PromptServer.instance, "_aiorbust_batch_routes_registered", False):
    PromptServer.instance._aiorbust_batch_routes_registered = True

    @PromptServer.instance.routes.post("/aiorbust/batch_upload")
    async def _aiorbust_batch_upload(request):
        """Upload one or more images to the shared pool."""
        try:
            reader  = await request.multipart()
            pool    = _pool_dir()
            results = []

            async for field in reader:
                if field.name != "files":
                    continue
                raw_name = field.filename or "image.jpg"
                data     = await field.read()

                file_id  = str(uuid.uuid4())
                ext      = os.path.splitext(raw_name)[1].lower() or ".jpg"
                safe     = f"{file_id}{ext}"
                path     = os.path.join(pool, safe)

                with open(path, "wb") as fh:
                    fh.write(data)

                try:
                    img  = Image.open(path)
                    w, h = img.size

                    # Generate thumbnail
                    thumb      = img.copy()
                    thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    thumb_name = f"{_THUMB_PREFIX}{safe}"
                    thumb.save(os.path.join(pool, thumb_name))

                    results.append({
                        "id":            file_id,
                        "filename":      safe,
                        "original_name": raw_name,
                        "thumbnail":     thumb_name,
                        "width":         w,
                        "height":        h,
                    })
                except Exception as e:
                    print(f"[Aiorbust Batch] Error processing {raw_name}: {e}")
                    if os.path.exists(path):
                        os.remove(path)

            return web.json_response({"success": True, "images": results})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)


    @PromptServer.instance.routes.delete("/aiorbust/batch_delete/{image_id}")
    async def _aiorbust_batch_delete(request):
        """Delete an image (and its thumbnail) from the pool."""
        image_id = request.match_info["image_id"]
        try:
            pool    = _pool_dir()
            deleted = []
            for fn in os.listdir(pool):
                if image_id in fn:
                    os.remove(os.path.join(pool, fn))
                    deleted.append(fn)
            return web.json_response({"success": True, "deleted": deleted})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)


    @PromptServer.instance.routes.get("/aiorbust/view/{filename}")
    async def _aiorbust_view(request):
        """Serve an image from the pool via ComfyUI's standard /view endpoint."""
        filename = request.match_info["filename"]
        pool     = _pool_dir()
        if os.path.exists(os.path.join(pool, filename)):
            return web.HTTPFound(
                f"/view?filename={filename}&type=input&subfolder={_POOL_SUBDIR}"
            )
        return web.Response(status=404, text=f"Image not found: {filename}")


# ─────────────────────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "AiorbustImageBatchLoader": AiorbustImageBatchLoader,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AiorbustImageBatchLoader": "Aiorbust Image Batch Loader",
}
