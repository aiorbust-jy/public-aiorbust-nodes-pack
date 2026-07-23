# -*- coding: utf-8 -*-
"""
ComfyUI node - Aiorbust Grok Prompt Generator.
Calls the xAI Grok API directly (api.x.ai) - no OpenRouter middleman.
Get your API key at: https://console.x.ai
Same image+text message format as GeminiPromptNode._call_grok() in gemini_prompt.py,
kept consistent so both nodes talk to the API the same way.
"""

import base64
import io
import logging

import numpy as np
import requests
from PIL import Image


# Vision-capable models (support image input) first, text-only models after.
# Same list as _GROK_MODELS in gemini_prompt.py for consistency across the pack.
_GROK_MODELS = [
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
    "grok-4-1-fast-reasoning",
    "grok-4-1-fast-non-reasoning",
    "grok-2-vision-1212",
    "grok-3",
    "grok-3-fast",
    "grok-3-mini",
    "grok-3-mini-fast",
]

_XAI_URL = "https://api.x.ai/v1/chat/completions"


class GrokPromptNode:

    _cached_api_key = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "The prompt/instruction to send to the model.",
                }),
                "model": (_GROK_MODELS, {
                    "default": "grok-4.20-0309-reasoning",
                    "tooltip": "xAI Grok model. Vision-capable models are listed first - use one of those if you connect an image.",
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "Optional image (e.g. from the Aiorbust Image Batch Loader for batch runs). Sent alongside the prompt to vision-capable models.",
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "xAI API key (console.x.ai). Cached after first use.",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.05,
                    "tooltip": "Creativity of the response (0 = deterministic, 2 = very creative).",
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "tooltip": "Maximum number of tokens in the response.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_prompt",)
    FUNCTION = "generate"
    OUTPUT_NODE = False
    CATEGORY = "Aiorbust/Prompt"
    DESCRIPTION = (
        "Send a text prompt (and optionally an image) to Grok and get a generated prompt back.\n"
        "Plug an Aiorbust Image Batch Loader into 'image' + Queue All to run one request per image in the batch."
    )

    def generate(
        self,
        prompt,
        model="grok-4.20-0309-reasoning",
        image=None,
        api_key="",
        temperature=0.7,
        max_tokens=1024,
    ):
        # Cache key across executions
        key = api_key.strip()
        if key:
            GrokPromptNode._cached_api_key = key
        else:
            key = GrokPromptNode._cached_api_key

        if not key:
            raise RuntimeError(
                "[Aiorbust Grok] API key is required. Get yours at https://console.x.ai"
            )

        if not prompt.strip():
            raise RuntimeError("[Aiorbust Grok] Prompt cannot be empty.")

        # Build the user message content — a list of image_url parts (one per
        # image in the batch) followed by the text part, same shape as
        # GeminiPromptNode._call_grok() in gemini_prompt.py.
        user_content = []
        if image is not None:
            for i in range(image.shape[0]):
                img_np = (255.0 * image[i].cpu().numpy()).clip(0, 255).astype(np.uint8)
                pil = Image.fromarray(img_np)
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
        user_content.append({"type": "text", "text": prompt.strip()})

        messages = [{"role": "user", "content": user_content}]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
        }
        headers = {
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        }

        logging.info(
            "[Aiorbust Grok] Calling %s (model=%s, image=%s, temp=%.2f, max_tokens=%d)",
            _XAI_URL, model, "yes" if image is not None else "no", temperature, max_tokens,
        )

        try:
            resp = requests.post(_XAI_URL, json=payload, headers=headers, timeout=180)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            msg = "[Aiorbust Grok] API error " + str(e.response.status_code)
            try:
                body = e.response.json()
                if "error" in body:
                    msg += " - " + str(body["error"])
            except Exception:
                msg += " - " + e.response.text[:300]
            raise RuntimeError(msg)
        except requests.exceptions.RequestException as e:
            raise RuntimeError("[Aiorbust Grok] Request error: " + str(e))

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("[Aiorbust Grok] Empty response - no choices returned.")

        text = choices[0].get("message", {}).get("content", "").strip()
        if not text:
            raise RuntimeError("[Aiorbust Grok] Empty content returned by API.")

        logging.info("[Aiorbust Grok] Done - %d chars returned.", len(text))
        return (text,)


NODE_CLASS_MAPPINGS = {
    "GrokPromptNode": GrokPromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GrokPromptNode": "Aiorbust Grok Prompt Generator",
}
