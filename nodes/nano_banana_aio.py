"""NanoBananaAIO -- Aiorbust image and video generation (licensed).

The node you see; not the node that does the work. Widgets, sockets and pixels
are here because they have to be -- ComfyUI hands this process torch tensors
and expects them back. Everything that decides anything runs on the Aiorbust
service: which provider serves the model you picked, under which endpoint, with
which prompt, polled how often and for how long.

That split is not obfuscation. There is nothing here to deobfuscate.

Licence key, first hit wins:
    AIORBUST_LICENSE_KEY in the environment
    a file named by AIORBUST_LICENSE_FILE
    /workspace/aiorbust/license.key
    ComfyUI/user/aiorbust/license.key
    license.key beside this pack
    ~/.aiorbust/license.key
    the license_key widget -- last, because widget values are saved into the
    workflow JSON and travel with any copy of it

Your provider API keys are your own and are used for your calls only. They are
forwarded for the duration of one request, never logged and never stored.
"""
import base64
import io
import json
import os
import subprocess
import tempfile

import numpy as np
import requests
import torch
from PIL import Image

import folder_paths

DEFAULT_API_URL = "https://aiorbust-h3-ir.onrender.com"
API_URL = os.environ.get("AIORBUST_API_URL", "").strip() or DEFAULT_API_URL
NODE_ID = "NanoBananaAIO"
CLIENT_VERSION = "0.3.0"

# Video generation legitimately runs to ~16 minutes on Seedance at 1080p, so
# this is the provider's ceiling plus room to hand the result back -- not a
# guess. A shorter timeout would kill renders that were about to succeed.
TIMEOUT = 1200

# Generated from the engine's INPUT_TYPES. If this does not match the service,
# the service says so instead of quietly misreading your widget values.
CONTRACT_SHA = 'facba949d1d3c4c6'

_MODEL_LABELS = [
    'Nano Banana Pro',
    'Nano Banana 2',
    'Seedream 4.5',
    'Seedream 5 Pro',
    'GPT Image 2.0',
    'Veo 3.1 Lite',
    'Veo 3.1',
    'Veo 3.1 Fast',
    'Kling 2.6',
    'Kling 3.0',
    'Kling 3.0 Motion Control',
    'Seedance 2.0',
    'Seedance 2.5',
    'Omni Flash',
]


IMAGE_SLOTS = ["image_1", "image_2", "image_3", "image_4", "image_5"]
API_KEY_WIDGETS = ["gemini_api_key", "wavespeed_api_key", "kie_api_key", "fal_api_key"]


# ---------------------------------------------------------------------------
# Licence
# ---------------------------------------------------------------------------

def _license_file_candidates():
    paths = []
    env_file = os.environ.get("AIORBUST_LICENSE_FILE", "").strip()
    if env_file:
        paths.append(env_file)
    paths.append("/workspace/aiorbust/license.key")
    try:
        paths.append(os.path.join(folder_paths.base_path, "user", "aiorbust", "license.key"))
    except Exception:
        pass
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "license.key"))
    paths.append(os.path.join(os.path.expanduser("~"), ".aiorbust", "license.key"))
    return paths


def _read_key_file(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    except Exception:
        pass
    return ""


def _license_key(widget_value):
    """Read fresh every call, so dropping a key in works without a restart."""
    key = os.environ.get("AIORBUST_LICENSE_KEY", "").strip()
    if key:
        return key
    for path in _license_file_candidates():
        key = _read_key_file(path)
        if key:
            return key
    return (widget_value or "").strip()


def _pod_fingerprint():
    for var in ("RUNPOD_POD_ID", "VAST_CONTAINERLABEL", "HOSTNAME"):
        v = os.environ.get(var)
        if v:
            return v
    return "unknown"


# ---------------------------------------------------------------------------
# Media. These run here because tensors only exist here.
# ---------------------------------------------------------------------------

def _png_b64(tensor):
    arr = (tensor[0].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _b64_png_to_tensor(b64):
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    if img.mode != "RGB":
        img = img.convert("RGB")
    return torch.from_numpy(np.asarray(img).astype(np.float32) / 255.0)[None,]


def _wav_b64(audio):
    """ComfyUI AUDIO -> base64 WAV. The service re-reads it as an array."""
    import wave

    wf = audio["waveform"].detach().cpu()
    if wf.dim() == 3:
        wf = wf[0]
    if wf.dim() == 1:
        wf = wf.unsqueeze(0)
    pcm = (np.clip(wf.numpy().T, -1.0, 1.0) * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(int(wf.shape[0]))
        w.setsampwidth(2)
        w.setframerate(int(audio.get("sample_rate", 44100)))
        w.writeframes(pcm.tobytes())
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _vertex_service_accounts(folder):
    """Read the service-account JSONs so the service can rotate Vertex quota.

    Sent only when the graph actually selects a Vertex path. If you would
    rather these never leave the pod, leave vertex_json_folder empty and use
    the Gemini API key instead -- every model here has a non-Vertex route.
    """
    folder = (folder or "").strip()
    if not folder or not os.path.isdir(folder):
        return []
    out = []
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".json"):
            continue
        try:
            with open(os.path.join(folder, name), "r", encoding="utf-8") as fh:
                out.append(json.load(fh))
        except Exception as e:
            print("\u26a0\ufe0f  [NB AIO] Skipping %s: %s" % (name, e))
    return out


def _first_frame(video_path):
    """One frame for the graph's preview, decoded from the file we just wrote.

    The service never sends frames back -- shipping a few hundred decoded
    frames to display one thumbnail would dwarf the video itself.
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        ok, frame = cap.read()
        cap.release()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            return torch.from_numpy(rgb)[None,]
    except Exception as e:
        print("\u26a0\ufe0f  [NB AIO] No preview frame (%s)." % e)
    return torch.zeros(1, 64, 64, 3)


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class NanoBananaAIO:
    @classmethod
    def INPUT_TYPES(cls):
        # On déclare la liste complète (image + vidéo) pour que la
        # validation côté serveur ComfyUI accepte les valeurs
        # "Veo 3", "Veo 3.1", etc. quand le JS bascule en mode vidéo.
        # Le frontend JS réduit l'affichage au sous-ensemble pertinent.
        model_names = (
            _MODEL_LABELS
        )
        return {
            "required": {
                "provider": (["GOOGLE", "WAVESPEED", "KIE", "FAL", "VERTEX"], {"default": "GOOGLE"}),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default":   "A futuristic nano banana dish",
                    "tooltip":   "Generation / transformation prompt",
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   "Negative prompt — elements to avoid in the image.\n⚠️ Supported by: FAL, WaveSpeed (NB2), KIE.\nIgnored by Google / Vertex (Gemini does not support negative prompts).",
                }),
                # Liste étendue pour inclure les resolutions vidéo
                # ("720p", "1080p") : le JS restreint l'affichage selon
                # le mode actif, mais la validation serveur a besoin de
                # la liste complète.
                "image_size": (["1K", "2K", "4K", "8K", "480p", "720p", "1080p"], {
                    "default": "2K",
                    "tooltip": "Output resolution (image: 1K/2K/4K/8K · video: 480p/720p/1080p)\n8K disponible uniquement sur Nano Banana Pro via WaveSpeed (edit-ultra).",
                }),
            },
            "optional": {
                # ── API KEYS ──────────────────────────────────────────
                "gemini_api_key": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "[GOOGLE] Google AI Studio API key.",
                }),
                "wavespeed_api_key": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "[WAVESPEED] WaveSpeed API key.",
                }),
                "kie_api_key": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "[KIE] Kie.ai API key.",
                }),
                "fal_api_key": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "[FAL] Fal.ai API key.",
                }),
                "vertex_json_folder": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "[VERTEX] Path to the folder containing service account JSON files (1 .json file = 1 project = 1 batch slot).",
                }),
                # vertex_location : hardcodé "us-central1" — masqué du node
                # vertex_gcs_bucket : valeur vide par défaut — masqué du node
                "disable_safety_threshold": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Disable the safety filter.",
                }),
                "model": (model_names, {
                    "default": model_names[0],
                    "tooltip": "Model to use.",
                }),
                "batch_size": ("INT", {
                    "default": 1, "min": 1, "max": 10, "step": 1,
                    "tooltip": "Number of images to generate in parallel",
                }),
                "use_search": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "[GOOGLE / VERTEX] Enable Google Search grounding",
                }),
                "system_instructions": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip":   "[GOOGLE / VERTEX] System instructions",
                }),
                "video_duration": ("INT", {
                    "default": 8,
                    "min": 3,
                    "max": 15,
                    "step": 1,
                }),
                "video_generate_audio": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "[Video] Generate audio track. Supported by all Veo providers.",
                }),
                "aspect_ratio": (
                    ["auto", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4",
                     "9:16", "16:9", "21:9"],
                    {"default": "auto",
                     "tooltip": "auto = détecte l'aspect ratio des images en input "
                                "et sélectionne le plus proche parmi les ratios supportés. "
                                "Fallback 1:1 si aucune image en input."},
                ),
                "temperature": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1,
                    "tooltip": "[GOOGLE / VERTEX] Model creativity",
                }),
                "top_p": ("FLOAT", {
                    "default": 0.95, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "[GOOGLE / VERTEX] Nucleus sampling",
                }),
                "fal_safety_tolerance": (["1", "2", "3", "4", "5", "6"], {
                    "default": "4",
                    "tooltip": "[FAL NB] 1 = strict | 6 = permissive",
                }),
                "fal_enable_web_search": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[FAL NB] Enable web search",
                }),
                "gpt2_image_quality": (["high", "medium", "low"], {
                    "default": "high",
                    "tooltip": "[GPT Image 2.0 / FAL] Generation quality. Ignored on other models.",
                }),
                "image_1": ("IMAGE", {"tooltip": "Main source image"}),
                "image_2": ("IMAGE", {"tooltip": "Image source 2"}),
                "image_3": ("IMAGE", {"tooltip": "Image source 3"}),
                "image_4": ("IMAGE", {"tooltip": "Image source 4"}),
                "image_5": ("IMAGE", {"tooltip": "Image source 5"}),
                "video_reference": ("AB_VIDEO", {
                    "tooltip": "[Kling 3.0 Motion Control] Connect an 'Aiorbust Video Loader' node.\n"
                               "The duration of the generated video will match the reference.\n"
                               "[Seedance 2.0 / Reference mode] Also accepted as a motion reference "
                               "(max 15s). Rejected in First & Last Frame mode.\n"
                               "[Omni Flash / Edit mode] The video to edit. Required in that mode, "
                               "refused in the other two — Omni does accept a video reference in its "
                               "schema, but the model does not actually process it yet.",
                }),
                "audio_reference": ("AUDIO", {
                    "tooltip": "[Seedance 2.0 / Reference mode] Audio reference — drives rhythm, or "
                               "lip-sync when the prompt asks for it. Max 15s.\n"
                               "Rejected in First & Last Frame mode, and ignored by every other model.\n"
                               "[Omni Flash] Never accepted — the API takes no audio input at all. "
                               "Omni generates its own soundtrack; describe it in the prompt instead.",
                }),
                "video_input_mode": (['First & Last Frame', 'Reference', 'Edit (video, Omni)'], {
                    "default": 'First & Last Frame',
                    "tooltip": "[Seedance 2.0 / Omni Flash] These modes are mutually exclusive in the "
                               "APIs themselves — you cannot mix them.\n\n"
                               "First & Last Frame\n"
                               "  Seedance: image_1 becomes the first frame, image_2 the last.\n"
                               "  Omni Flash: image_1 becomes the first frame. A second image is "
                               "refused — Omni has no frame interpolation.\n"
                               "  Video and audio inputs are refused.\n\n"
                               "Reference\n"
                               "  Seedance: up to 5 images, 1 video and 1 audio guide style, motion "
                               "and rhythm freely.\n"
                               "  Omni Flash: up to 6 images. No video, no audio.\n"
                               "  No guarantee on the first/last frame.\n\n"
                               "Edit (video, Omni)\n"
                               "  Omni Flash only: send an existing video plus an edit instruction "
                               "(\"make the phone invisible\"). Keep the prompt simple and add "
                               "\"Keep everything else the same\". Refused by every other model.",
                }),
                # ── Video mode controls (managed by JS DOM widget) ───────────────
                "video_mode_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[Video] Enabled by JS toggle — do not modify manually.",
                }),
                # ── Automation Face Swap controls (managed by JS DOM widget) ──────
                "face_swap_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[Automation] Enabled by JS block — do not modify manually.",
                }),
                "breast_refiner_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[Automation] Enabled by JS block — do not modify manually.",
                }),
                "low_neck_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[Automation] Enabled by JS block — do not modify manually.",
                }),
                "amateur_mode_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "[Automation] Amateur, Low quality input match — overrides the default face swap prompt.",
                }),
                "face_expression": ("STRING", {
                    "default": "Neutral",
                    "tooltip": "[Automation] Facial expression — managed by JS block — do not modify manually.",
                }),
                "face_swap_custom_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "[Automation] Extra prompt appended to the face swap prompt — managed by JS block — do not modify manually.",
                }),
                # DERNIER widget, et il doit le rester. ComfyUI serialise les
                # valeurs de widgets par POSITION : en inserer un au milieu decale
                # tout ce qui suit dans les workflows deja sauvegardes, et les
                # reglages se retrouvent sur les mauvais champs.
                "max_black_retries": ("INT", {
                    "default": 0, "min": 0, "max": 10, "step": 1,
                    "tooltip": "Replay the generation when the provider returns a black image "
                               "(a failed generation). 0 disables it.\n\n"
                               "The retry has to happen here, not in a downstream check node: "
                               "ComfyUI's graph is acyclic, so nothing that receives the black "
                               "image can re-trigger what produced it. Retrying in-process also "
                               "keeps a batch loader in step — it never sees the failed attempt.\n\n"
                               "The whole call is replayed, so a partly-black batch re-generates "
                               "its good images too. Each attempt is billed.",
                }),
                "license_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Optional. Prefer AIORBUST_LICENSE_KEY or a key "
                               "file -- a value typed here is saved into the "
                               "workflow JSON and travels with any copy of it.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("images", "video", "grounding_sources")
    OUTPUT_NODE = False
    FUNCTION = "generate_unified"
    CATEGORY = "Aiorbust/NanoBanana"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def generate_unified(self, **kw):
        key = _license_key(kw.pop("license_key", ""))
        if not key:
            raise RuntimeError(
                "[NB AIO] No Aiorbust licence key found.\n"
                "-> Set AIORBUST_LICENSE_KEY, drop the key in "
                "/workspace/aiorbust/license.key, or fill the license_key widget."
            )

        images = [{"slot": s, "data": _png_b64(kw.pop(s))}
                  for s in IMAGE_SLOTS if kw.get(s) is not None]
        for s in IMAGE_SLOTS:
            kw.pop(s, None)

        audio_in = kw.pop("audio_reference", None)
        audio = ({"sample_rate": int(audio_in.get("sample_rate", 44100)),
                  "data": _wav_b64(audio_in)} if audio_in else None)

        # A reference video the provider must fetch has to be reachable from
        # outside this pod, which it never is. A URL passes through; a local
        # file goes up once and the service uploads it with your own key.
        vid = kw.pop("video_reference", None)
        video_url = video_b64 = ""
        video_name = "reference.mp4"
        if isinstance(vid, str) and vid.startswith(("http://", "https://")):
            video_url = vid
        elif isinstance(vid, str) and vid and os.path.isfile(vid):
            with open(vid, "rb") as fh:
                video_b64 = base64.b64encode(fh.read()).decode("ascii")
            video_name = os.path.basename(vid)
        elif vid:
            print("\u26a0\ufe0f  [NB AIO] video_reference %r is neither a URL nor a "
                  "readable file \u2014 ignored." % (vid,))

        credentials = {w: (kw.pop(w, "") or "").strip() for w in API_KEY_WIDGETS}
        credentials["vertex_service_accounts"] = _vertex_service_accounts(
            kw.get("vertex_json_folder", ""))
        kw["vertex_json_folder"] = ""    # the pod's path means nothing remotely

        payload = {
            "contract_sha": CONTRACT_SHA,
            "params": kw,
            "credentials": credentials,
            "images": images,
            "audio": audio,
            "video_url": video_url,
            "video_b64": video_b64,
            "video_name": video_name,
        }

        print("\U0001f3a8 [NB AIO] %s via %s | %d image(s)%s%s"
              % (kw.get("model", "?"), kw.get("provider", "?"), len(images),
                 " + audio" if audio else "",
                 " + video" if (video_url or video_b64) else ""))

        try:
            resp = requests.post(
                "%s/v1/nodes/%s" % (API_URL.rstrip("/"), NODE_ID),
                json={"license_key": key, "client_version": CLIENT_VERSION,
                      "payload": payload},
                timeout=TIMEOUT,
                headers={"X-Pod-Fingerprint": _pod_fingerprint()},
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                "[NB AIO] Could not reach the Aiorbust service at %s (%s).\n"
                "-> Check the pod has outbound internet." % (API_URL, e))

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail") or resp.text[:400]
            except Exception:
                detail = resp.text[:400]
            raise RuntimeError(detail)

        data = resp.json()
        for notice in data.get("notices", []):
            print("\u26a0\ufe0f  [NB AIO] %s" % notice)
        out = data.get("outputs", {})

        if out.get("video_b64"):
            raw = base64.b64decode(out["video_b64"])
            path = os.path.join(folder_paths.get_temp_directory(),
                                out.get("video_name") or "VID.mp4")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(raw)
            print("\u2705 [NB AIO] Video %.1f MB \u2192 %s" % (len(raw) / 1e6, path))
            return (_first_frame(path), path, out.get("grounding_sources", ""))

        tensors = [_b64_png_to_tensor(b) for b in out.get("images", [])]
        if not tensors:
            print("\u26a0\ufe0f  [NB AIO] Nothing returned.")
            return (torch.zeros(1, 64, 64, 3), "", out.get("grounding_sources", ""))
        print("\u2705 [NB AIO] %d image(s)." % len(tensors))
        return (torch.cat(tensors, dim=0), "", out.get("grounding_sources", ""))


NODE_CLASS_MAPPINGS = {"NanoBananaAIO": NanoBananaAIO}
NODE_DISPLAY_NAME_MAPPINGS = {"NanoBananaAIO": "Aiorbust Image and Video Edit AIO"}


# ---------------------------------------------------------------------------
# Presets. Local to this pod: the slots are the user's own saved widget values,
# stored beside the pack and served to the node's JS over ComfyUI's server. The
# whitelist below is what makes a preset file safe to share -- API keys and
# images are deliberately not in it.
#
# Nothing here talks to the Aiorbust service.
# ---------------------------------------------------------------------------
try:
    from aiohttp import web
    from server import PromptServer

    # Presets — fichier JSON stocké à côté du node
    # ─────────────────────────────────────────────────────────────────────────────
    _PRESETS_FILE = os.path.join(os.path.dirname(__file__), "nb_aio_presets.json")

    # Paramètres sauvegardés (jamais les clés API ni les images)
    _PRESET_KEYS = [
        "preset_name",
        "provider",
        "prompt",
        "image_size",
        "model",
        "batch_size",
        "use_search",
        "system_instructions",
        "video_duration",
        "aspect_ratio",
        "temperature",
        "top_p",
        "fal_safety_tolerance",
        "fal_enable_web_search",
        "disable_safety_threshold",
        "video_mode_enabled",
    ]

    def _load_presets() -> dict:
        """Charge les presets depuis le fichier JSON."""
        if not os.path.isfile(_PRESETS_FILE):
            return {}
        try:
            with open(_PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"⚠️  [Presets] Unable to load : {e}")
            return {}

    def _save_presets(presets: dict) -> bool:
        """Sauvegarde les presets dans le fichier JSON."""
        try:
            data = {str(k): v for k, v in presets.items()}
            with open(_PRESETS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ [Presets] Saved → {_PRESETS_FILE}")
            return True
        except Exception as e:
            print(f"❌ [Presets] Error sauvegarde : {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────────
    # Endpoint REST  /nb_aio/save_preset   (appelé par le JS du bouton)
    # /nb_aio/load_presets                 (appelé au chargement du node)
    #
    # Guard sys.modules : évite le double-enregistrement si une copie backup
    # du fichier (.py) est présente dans le même dossier custom_nodes.
    # ─────────────────────────────────────────────────────────────────────────────
    if not getattr(PromptServer.instance, "_nb_aio_routes_registered", False):
        PromptServer.instance._nb_aio_routes_registered = True

        @PromptServer.instance.routes.post("/nb_aio/save_preset")
        async def api_save_preset(request):
            try:
                body     = await request.json()
                slot     = int(body.get("slot", 1))
                params   = body.get("params", {})

                if slot < 1 or slot > 10:
                    return web.json_response(
                        {"success": False, "error": "Invalid slot (1-10)"},
                        status=400,
                    )

                # Filtrer uniquement les clés autorisées
                filtered = {k: v for k, v in params.items() if k in _PRESET_KEYS}

                presets = _load_presets()
                presets[slot] = filtered
                ok = _save_presets(presets)

                if ok:
                    print(f"💾 [Presets] Slot {slot} saved via JS button")
                    return web.json_response({
                        "success": True,
                        "slot":    slot,
                        "params":  filtered,
                    })
                else:
                    return web.json_response(
                        {"success": False, "error": "File write failed"},
                        status=500,
                    )
            except Exception as e:
                return web.json_response(
                    {"success": False, "error": str(e)},
                    status=500,
                )

        @PromptServer.instance.routes.get("/nb_aio/load_presets")
        async def api_load_presets(request):
            try:
                presets = _load_presets()
                # Convertit les clés int → str pour JSON
                data = {str(k): v for k, v in presets.items()}
                return web.json_response({"success": True, "presets": data})
            except Exception as e:
                return web.json_response(
                    {"success": False, "error": str(e)},
                    status=500,
                )
    else:
        print("⚠️ [NanaBanana] Routes /nb_aio already registered — second load ignored.")

    # ─────────────────────────────────────────────────────────────────────────────
except Exception as _e:            # pragma: no cover - ComfyUI is always there
    print("[NB AIO] Preset buttons unavailable (%s). The node still works." % _e)
