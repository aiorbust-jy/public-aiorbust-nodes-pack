"""Aiorbust Prompt Writer — a reference photo in, a render prompt out.

A skin, deliberately. The node sends a picture and a licence key; the
instruction that turns one into the other lives on the Aiorbust service and is
never shipped. Same arrangement as the H3 Context-IR node, for the same two
reasons.

The first forced it. The older Grok node takes an api_key widget, and a widget
value is saved into the workflow JSON — so a key typed there travels with every
graph anyone shares. There is no api_key here at all: the call is made by the
service, and the pod never holds a provider credential.

The second is that the instruction is the work. Getting a caption that
describes a scene, a pose and clothing while saying nothing about the person's
face, hair or build took tuning, and it matters because the person comes from a
LoRA — anything the caption says about them fights the character and returns a
blend of two faces. A customer who can read that instruction can paste it
anywhere. Behind a licence it stays a reason to hold one.

Use it where the old Grok node sat: batch loader or LoadImage into `image`,
output into a CLIP Text Encode.
"""

import base64
import io
import json
import os
import urllib.error
import urllib.request

import numpy as np
from PIL import Image

try:
    from .aiorbust_license import check as _license_check
except Exception:  # pragma: no cover - the pack may be vendored without it
    _license_check = None

# The live service. Not a secret: it is a public HTTPS endpoint and every
# request to it is licence-checked. Overridable so a pod can be pointed at a
# staging deployment without shipping a different client.
DEFAULT_API_URL = "https://api.aineo.studio"
API_URL = os.environ.get("AIORBUST_API_URL", "").strip() or DEFAULT_API_URL
TIMEOUT = 180
CLIENT_VERSION = "0.1.0"
NODE_ID = "AiorbustPromptWriter"

# Sent at this size rather than whatever the graph is working at. The captioner
# reads composition and clothing, not eyelashes, and a 4K frame is megabytes of
# detail billed by the token to no effect.
MAX_SIDE = 1280


def _first_real_frame(image):
    """The first frame that is not the batch loader's empty placeholder.

    An empty pool yields a 64x64 black frame rather than nothing, and sending
    that costs a vision call to caption a black square.
    """
    for i in range(image.shape[0]):
        frame = image[i]
        h, w = frame.shape[0], frame.shape[1]
        if h <= 64 and w <= 64 and float(frame.max()) < 0.02:
            continue
        return frame
    return None


def _encode(frame) -> str:
    array = (255.0 * frame.cpu().numpy()).clip(0, 255).astype(np.uint8)
    pil = Image.fromarray(array)
    if max(pil.size) > MAX_SIDE:
        pil.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    buf = io.BytesIO()
    # JPEG rather than PNG: a photograph at quality 90 is a fraction of the
    # bytes and the captioner cannot tell the difference.
    pil.convert("RGB").save(buf, format="JPEG", quality=90, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class AiorbustPromptWriter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "The reference photo. Its scene, pose and clothing "
                               "are described; the person in it is not.",
                }),
            },
            "optional": {
                "trigger_word": ("STRING", {
                    "default": "",
                    "tooltip": "Your character's LoRA token. It is placed at the "
                               "start of the prompt. Leave empty for the default.",
                }),
                # Last, matching the other Aiorbust nodes. Reordering widgets
                # silently breaks graphs already saved against this node.
                "license_key": ("STRING", {
                    "default": "",
                    "tooltip": "Your Aiorbust licence. Better set as "
                               "AIORBUST_LICENSE_KEY in the pod environment: a "
                               "widget value is saved into the workflow and "
                               "travels with any graph you share.",
                }),
            },
            "hidden": {"aiorbust_graph": "PROMPT"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "write"
    CATEGORY = "Aiorbust/Prompt"
    DESCRIPTION = (
        "Writes a render prompt from a reference photo. Describes the scene, "
        "pose and clothing; never the person, so your character LoRA is not "
        "fighting a description of somebody else. Needs an Aiorbust licence."
    )

    def write(self, image, trigger_word="", license_key="", aiorbust_graph=None):
        if _license_check is not None:
            key = _license_check(
                "prompt_writer", license_key,
                label="Aiorbust Prompt Writer", prompt=aiorbust_graph,
            )
        else:
            key = (
                os.environ.get("AIORBUST_LICENSE_KEY", "").strip()
                or (license_key or "").strip()
            )
        if not key:
            raise RuntimeError(
                "[Aiorbust Prompt Writer] No licence key. Set AIORBUST_LICENSE_KEY "
                "in the pod environment, or paste one into the node."
            )

        frame = _first_real_frame(image) if image is not None else None
        if frame is None:
            raise RuntimeError(
                "[Aiorbust Prompt Writer] No image. Connect a loader, and check "
                "the batch pool is not empty."
            )

        body = json.dumps({
            "license_key": key,
            "image": _encode(frame),
            "trigger_word": (trigger_word or "").strip(),
            "client_version": CLIENT_VERSION,
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{API_URL}/api/caption",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # The service says why -- an inactive licence, an image it could not
            # read. Passing that through beats a status code the customer then
            # has to ask about.
            detail = ""
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("detail", "")
            except Exception:
                pass
            raise RuntimeError(
                f"[Aiorbust Prompt Writer] {detail or exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"[Aiorbust Prompt Writer] Could not reach the Aiorbust service: "
                f"{exc.reason}"
            ) from exc

        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            raise RuntimeError(
                "[Aiorbust Prompt Writer] The service returned no prompt."
            )
        print(f"[Aiorbust Prompt Writer] {len(prompt)} chars written.")
        return (prompt,)


NODE_CLASS_MAPPINGS = {"AiorbustPromptWriter": AiorbustPromptWriter}
NODE_DISPLAY_NAME_MAPPINGS = {"AiorbustPromptWriter": "Aiorbust Prompt Writer"}
