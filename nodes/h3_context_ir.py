"""H3 Context-IR — remote stub.

THIS FILE SHIPS TO CUSTOMERS. Assume every line is read. Nothing here is
proprietary: it turns tensors into bytes, forwards them, and prints what comes
back. The grounding schema, the compilation rules and the MiniMax guides live
on the service and are never delivered to a pod.

Node identity is unchanged — same node_id, same inputs, same outputs — so
existing workflows keep working with no edits.
"""
from __future__ import annotations

import base64
import io
import json
import os
import wave

import numpy as np
import requests
from PIL import Image

# The live service. Not a secret — it is a public HTTPS endpoint, and every
# request to it is licence-checked. Overridable so you can point a pod at a
# staging deployment without shipping a different client.
DEFAULT_API_URL = "https://aiorbust-h3-ir.onrender.com"
API_URL = os.environ.get("AIORBUST_API_URL", "").strip() or DEFAULT_API_URL
TIMEOUT = 600
CLIENT_VERSION = "0.2.0"
NODE_ID = "H3ContextIR"

ROLE_REFERENCE = "reference"
ROLES = [ROLE_REFERENCE, "first_frame", "last_frame"]
PROVIDERS = ["Gemini", "Vertex", "Grok"]
MODELS = ["gemini-3.6-flash", "gemini-3.6-pro", "grok-4-vision"]

VIDEO_KEYFRAMES = 8
AUDIO_SR = 16000    # mono 16-bit at 16 kHz: speech-grade, small enough inline


# ---------------------------------------------------------------------------
# Tensor -> bytes. This must stay client-side; torch tensors only exist here.
# ---------------------------------------------------------------------------

def _tensor_to_png_b64(frame) -> str:
    arr = (255.0 * frame.cpu().numpy()).clip(0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _audio_to_wav_b64(audio) -> str:
    """ComfyUI AUDIO -> mono 16-bit PCM WAV at 16 kHz, base64.

    Mono 16-bit is what actually populates the soundscape with dated events
    rather than a generic sentence: the model needs a waveform it can
    transcribe, not a high-fidelity stereo mix. 16 kHz keeps 15 s near 480 KB.
    """
    import torch

    wav = audio["waveform"]
    sr = int(audio["sample_rate"])
    if wav.ndim == 3:
        wav = wav[0]
    if wav.ndim == 2:
        wav = wav.mean(dim=0)
    wav = wav.detach().cpu().float()

    if sr != AUDIO_SR:
        n_out = max(1, int(round(wav.shape[0] * AUDIO_SR / float(sr))))
        wav = torch.nn.functional.interpolate(
            wav.view(1, 1, -1), size=n_out, mode="linear", align_corners=False
        ).view(-1)

    peak = float(wav.abs().max()) if wav.numel() else 0.0
    if peak > 1.0:
        wav = wav / peak
    pcm = (wav.clamp(-1.0, 1.0) * 32767.0).to(torch.int16).numpy()

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(AUDIO_SR)
        wf.writeframes(pcm.tobytes())
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _sample_keyframes(frames, fps: float, count: int = VIDEO_KEYFRAMES) -> list:
    total = int(frames.shape[0])
    if total == 0:
        return []
    count = min(count, total)
    idxs = [int(round(i * (total - 1) / max(1, count - 1))) for i in range(count)] \
        if count > 1 else [0]
    return [{"t": i / float(fps or 24.0), "data": _tensor_to_png_b64(frames[i])}
            for i in idxs]


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def _vertex_credential(folder: str) -> dict:
    """Mint a short-lived OAuth token locally and forward only that.

    The service-account JSON never leaves this machine. A token is good for
    about an hour, so a leak costs an hour of access rather than a permanent
    key — which is why this is worth the extra dependency over just POSTing
    the file contents.
    """
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import service_account

    folder = (folder or "").strip()
    if not folder or not os.path.isdir(folder):
        raise RuntimeError(
            "[H3 Context-IR] vertex_json_folder not found: %r\n"
            "-> Put your Vertex service-account JSON in that folder, or switch "
            "`provider` to Gemini and paste a key into gemini_api_key." % folder
        )
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder)
                   if f.lower().endswith(".json"))
    if not files:
        raise RuntimeError("[H3 Context-IR] No .json in %s" % folder)

    with open(files[0], "r", encoding="utf-8") as fh:
        project_id = json.load(fh).get("project_id", "")
    creds = service_account.Credentials.from_service_account_file(
        files[0], scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(GoogleRequest())
    return {"kind": "vertex_token", "access_token": creds.token,
            "project_id": project_id}


def _license_file_candidates():
    """Where a key file may live, most specific first.

    Several entries because this node runs in two very different places: a
    RunPod pod with a /workspace volume, and a Windows portable install where
    that path does not exist. Rather than make the customer configure which,
    look in all the plausible spots — it is a handful of stat() calls.
    """
    paths = []

    explicit = os.environ.get("AIORBUST_LICENSE_FILE", "").strip()
    if explicit:
        paths.append(explicit)

    # Pod: the network volume, which start.sh seeds and which survives restarts.
    paths.append("/workspace/aiorbust/license.key")

    # ComfyUI's own user directory. The idiomatic place for per-install config,
    # and it survives updating or reinstalling this node pack.
    try:
        import folder_paths
        user_dir = folder_paths.get_user_directory()
        paths.append(os.path.join(user_dir, "aiorbust", "license.key"))
    except Exception:
        pass

    # Next to the node pack — the first place someone looks locally.
    pack_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths.append(os.path.join(pack_dir, "license.key"))

    # Home directory, for a key shared across several ComfyUI installs.
    paths.append(os.path.join(os.path.expanduser("~"), ".aiorbust", "license.key"))

    return paths


def _read_key_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Tolerate "AIORBUST_LICENSE_KEY=..." from someone pasting an
                # env-var line into the file.
                return line.split("=")[-1].strip()
    except OSError:
        pass
    return ""


def _license_key(widget_value: str) -> str:
    """First hit wins: environment, then a key file, then the widget.

    Order is about leak risk, not convenience. A widget value is saved INTO the
    workflow JSON, so a customer who types their key there and then shares the
    graph — which people do constantly — ships a working licence with it. The
    env var and the files never travel.

    Files are read on every call rather than cached, so dropping a key in works
    on the next queue with no ComfyUI restart.
    """
    key = os.environ.get("AIORBUST_LICENSE_KEY", "").strip()
    if key:
        return key

    for path in _license_file_candidates():
        key = _read_key_file(path)
        if key:
            return key

    return (widget_value or "").strip()


def _pod_fingerprint() -> str:
    for var in ("RUNPOD_POD_ID", "VAST_CONTAINERLABEL", "HOSTNAME"):
        v = os.environ.get(var)
        if v:
            return v
    return "unknown"


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class H3ContextIR:
    """Two-pass H3 prompt compiler. Runs on the Aiorbust service."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "intent": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Keep this SHORT, and write only what must CHANGE. "
                               "The media are read for everything else.",
                }),
                "duration_seconds": ("FLOAT", {
                    "default": 8.0, "min": 2.0, "max": 15.0, "step": 0.1}),
                "aspect_ratio": ("STRING", {
                    "default": "adaptive", "multiline": False,
                    "tooltip": "adaptive, 16:9, 9:16, 1:1, 4:3, 3:4, 21:9, 3:2, "
                               "2:3, 5:4, 4:5. Connect Aiorbust Resolution (MP)'s "
                               "aspect_ratio output to keep it in sync."}),
                "provider": (PROVIDERS, {"default": "Gemini"}),
                "model": (MODELS, {"default": "gemini-3.6-flash"}),
                "max_tokens": ("INT", {
                    "default": 8192, "min": 512, "max": 65536, "step": 512}),
            },
            "optional": {
                # Six discrete slots plus a batch, matching the node this
                # replaces. Roles exist only on the first two: first_frame /
                # last_frame are positional ideas that stop being meaningful
                # once you are on your fifth reference.
                "image_1": ("IMAGE",),
                "image_1_role": (ROLES, {"default": ROLE_REFERENCE}),
                "image_2": ("IMAGE",),
                "image_2_role": (ROLES, {"default": ROLE_REFERENCE}),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "image_6": ("IMAGE",),
                "images_batch": ("IMAGE",),
                "video": ("IMAGE",),
                "video_fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 120.0}),
                "video_keyframes": ("INT", {
                    "default": VIDEO_KEYFRAMES, "min": 1, "max": 32}),
                "media_resolution": (
                    ["default", "low", "medium", "high"], {"default": "low"}),
                "video_audio": ("AUDIO",),
                "ref_audio_1": ("AUDIO",),
                "ref_audio_2": ("AUDIO",),
                "gemini_api_key": ("STRING", {"default": "", "multiline": False}),
                "grok_api_key": ("STRING", {"default": "", "multiline": False}),
                "vertex_json_folder": ("STRING", {"default": "", "multiline": False}),
                "license_key": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "LAST RESORT. A key typed here is saved into the "
                               "workflow JSON and travels with every copy you share. "
                               "Prefer AIORBUST_LICENSE_KEY in the pod environment, or "
                               "put the key in /workspace/aiorbust/license.key."}),
                "grounding_override": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("h3_prompt", "grounding_json")
    FUNCTION = "run"
    CATEGORY = "Aiorbust/Prompt"

    def run(self, intent, duration_seconds, aspect_ratio, provider, model,
            max_tokens, image_1=None, image_1_role=ROLE_REFERENCE,
            image_2=None, image_2_role=ROLE_REFERENCE,
            image_3=None, image_4=None, image_5=None, image_6=None,
            images_batch=None, video=None, video_fps=24.0, video_keyframes=VIDEO_KEYFRAMES,
            media_resolution="low", video_audio=None,
            ref_audio_1=None, ref_audio_2=None,
            gemini_api_key="", grok_api_key="", vertex_json_folder="",
            license_key="", grounding_override=""):

        key = _license_key(license_key)

        if provider == "Vertex":
            credential = _vertex_credential(vertex_json_folder)
        else:
            token = (grok_api_key if provider == "Grok" else gemini_api_key).strip()
            if not token:
                raise RuntimeError(
                    "[H3 Context-IR] %s needs an API key in the %s_api_key widget."
                    % (provider, provider.lower()))
            credential = {"kind": "api_key", "value": token}

        # Connection order decides labelling: the first supplied slot becomes
        # <Picture 1>. Skipping image_3 never leaves a gap in the numbering.
        images = []
        for slot, tensor, role in (("image_1", image_1, image_1_role),
                                   ("image_2", image_2, image_2_role),
                                   ("image_3", image_3, ROLE_REFERENCE),
                                   ("image_4", image_4, ROLE_REFERENCE),
                                   ("image_5", image_5, ROLE_REFERENCE),
                                   ("image_6", image_6, ROLE_REFERENCE)):
            if tensor is None:
                continue
            images.append({"slot": slot, "role": role,
                           "data": _tensor_to_png_b64(tensor[0])})

        # A batch arrives as one IMAGE tensor of N frames; each becomes its own
        # labelled picture, after the discrete slots.
        if images_batch is not None:
            for i in range(int(images_batch.shape[0])):
                images.append({"slot": "images_batch_%d" % (i + 1),
                               "role": ROLE_REFERENCE,
                               "data": _tensor_to_png_b64(images_batch[i])})

        audio = []
        for slot, clip in (("video_audio", video_audio),
                           ("ref_audio_1", ref_audio_1),
                           ("ref_audio_2", ref_audio_2)):
            if clip is not None:
                audio.append({"slot": slot, "data": _audio_to_wav_b64(clip),
                              "enabled": True})

        payload = {
            "provider": provider,
            "credential": credential,
            "model": model,
            "max_tokens": int(max_tokens),
            "media_resolution": media_resolution,
            "intent": intent,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": float(duration_seconds),
            "fps": float(video_fps),
            "images": images,
            "video": ({"slot": "video", "fps": float(video_fps),
                       "frames": _sample_keyframes(video, video_fps,
                                                   int(video_keyframes))}
                      if video is not None else None),
            "audio": audio,
            "grounding_override": grounding_override,
        }

        n_img = len(images) + (len(payload["video"]["frames"]) if payload["video"] else 0)
        print("🔍 [H3 Context-IR] %s/%s | %d image(s), %d audio | media_resolution=%s"
              % (provider, model, n_img, len(audio), media_resolution))

        # Generic envelope: the service routes on node id, so every licensed
        # node speaks the same outer shape and only `payload` differs.
        envelope = {
            "license_key": key,
            "client_version": CLIENT_VERSION,
            "payload": payload,
        }

        try:
            resp = requests.post(
                "%s/v1/nodes/%s" % (API_URL.rstrip("/"), NODE_ID),
                json=envelope, timeout=TIMEOUT,
                headers={"X-Pod-Fingerprint": _pod_fingerprint()},
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                "[H3 Context-IR] Could not reach the Aiorbust service at %s (%s).\n"
                "-> Check the pod has outbound internet, then check status." % (API_URL, e))

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail") or resp.text[:400]
            except Exception:
                detail = resp.text[:400]
            raise RuntimeError(detail)

        data = resp.json()
        for notice in data.get("notices", []):
            print("⚠️  [H3 Context-IR] %s" % notice)

        outputs = data.get("outputs", {})
        usage = data.get("usage", {})
        if usage.get("grounding_cached"):
            print("♻️  [H3 Context-IR] Grounding served from cache — no vision call.")
        print("✅ [H3 Context-IR] Done — prompt %d chars, grounding %d chars"
              % (usage.get("prompt_chars", 0), usage.get("grounding_chars", 0)))

        return (outputs["h3_prompt"], outputs["grounding_json"])


NODE_CLASS_MAPPINGS = {"H3ContextIR": H3ContextIR}
NODE_DISPLAY_NAME_MAPPINGS = {"H3ContextIR": "H3 Context-IR (Aiorbust)"}
