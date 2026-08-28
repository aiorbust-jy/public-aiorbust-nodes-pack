"""Aiorbust License -- one key, wired into every licensed node.

Put this node once at the top of a graph and connect its output to the
license_key input of H3 Context-IR, the AIO node, and anything else licensed.
Beats retyping the key into each node, and beats forgetting to.

It also checks the key before anything else runs. Without it a bad key is
discovered by whichever licensed node happens to execute first, which on a
video graph can be twenty minutes in. Here it is a red node at the top, with
the reason on it, before a single provider call has been paid for.

The key itself is resolved the same way every licensed node resolves it, and in
the same order, so adding this node never changes which key is used:

    AIORBUST_LICENSE_KEY in the environment
    a file named by AIORBUST_LICENSE_FILE
    /workspace/aiorbust/license.key
    ComfyUI/user/aiorbust/license.key
    license.key beside this pack
    ~/.aiorbust/license.key
    the license_key widget -- last, deliberately

The widget is last because ComfyUI saves widget values into the workflow JSON.
A key typed there travels with every copy of that graph the user shares, and
people share graphs constantly. The environment variable and the files do not
travel, which is why they win.
"""
import os
import time

import requests

import folder_paths

DEFAULT_API_URL = "https://aiorbust-h3-ir.onrender.com"
API_URL = os.environ.get("AIORBUST_API_URL", "").strip() or DEFAULT_API_URL
CLIENT_VERSION = "0.3.0"

# Verification is cached so a graph with eight licensed nodes in it does not
# make eight round trips per queue. The service tells us how long its answer is
# good for; this is only the fallback when it does not say.
_DEFAULT_TTL = 30 * 60
_cache = {}


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


def resolve_key(widget_value=""):
    """First hit wins. Files are re-read every call, so dropping a key in
    works on the next queue with no ComfyUI restart."""
    key = os.environ.get("AIORBUST_LICENSE_KEY", "").strip()
    if key:
        return key, "AIORBUST_LICENSE_KEY"
    for path in _license_file_candidates():
        key = _read_key_file(path)
        if key:
            return key, path
    return (widget_value or "").strip(), "license_key widget"


def _pod_fingerprint():
    for var in ("RUNPOD_POD_ID", "VAST_CONTAINERLABEL", "HOSTNAME"):
        v = os.environ.get(var)
        if v:
            return v
    return "unknown"


class AiorbustLicense:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "license_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Leave empty if AIORBUST_LICENSE_KEY is set",
                    "tooltip": "Checked LAST. Prefer AIORBUST_LICENSE_KEY or a "
                               "key file: a value typed here is saved into the "
                               "workflow JSON and travels with any copy of it.",
                }),
                "verify": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Check the key with the Aiorbust service before "
                               "the graph runs, so a bad key stops here rather "
                               "than part-way through a render. Turn off only "
                               "if the pod has no outbound internet.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("license_key",)
    FUNCTION = "load"
    CATEGORY = "Aiorbust"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always re-run: a key revoked between queues must be caught, and the
        # TTL cache below is what stops that costing a round trip every time.
        return float("nan")

    def load(self, license_key="", verify=True):
        key, source = resolve_key(license_key)
        if not key:
            raise RuntimeError(
                "[Aiorbust License] No licence key found.\n"
                "-> Set AIORBUST_LICENSE_KEY in the pod environment, drop the "
                "key in /workspace/aiorbust/license.key, or fill the "
                "license_key widget on this node."
            )

        shown = key[:8] + "..." if len(key) > 8 else key
        if not verify:
            print("[Aiorbust License] %s from %s (not verified)" % (shown, source))
            return (key,)

        hit = _cache.get(key)
        if hit and time.time() < hit["expires"]:
            print("[Aiorbust License] %s OK - plan %s (cached)" % (shown, hit["plan"]))
            return (key,)

        try:
            resp = requests.post(
                "%s/v1/verify" % API_URL.rstrip("/"),
                json={"license_key": key, "client_version": CLIENT_VERSION},
                timeout=30,
                headers={"X-Pod-Fingerprint": _pod_fingerprint()},
            )
        except requests.exceptions.RequestException as e:
            # An outage on our side must not stop a render that is already paid
            # for. A key that verified recently keeps working on its cached
            # answer; one that never verified here has nothing to fall back on.
            if hit:
                print("[Aiorbust License] Service unreachable (%s) - continuing "
                      "on the last good answer for %s." % (e, shown))
                return (key,)
            raise RuntimeError(
                "[Aiorbust License] Could not reach the Aiorbust service at %s "
                "(%s).\n-> Check the pod has outbound internet, or set "
                "verify=false to skip this check." % (API_URL, e))

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail") or resp.text[:300]
            except Exception:
                detail = resp.text[:300]
            raise RuntimeError("[Aiorbust License] %s\n-> Key read from: %s"
                               % (detail, source))

        data = resp.json()
        ttl = int(data.get("ttl_seconds") or _DEFAULT_TTL)
        _cache[key] = {"expires": time.time() + ttl, "plan": data.get("plan", "?")}
        ent = data.get("entitlements") or []
        print("[Aiorbust License] %s OK - plan %s, grants %s (from %s)"
              % (shown, data.get("plan", "?"),
                 "everything" if "*" in ent else ", ".join(ent) or "nothing",
                 source))
        if data.get("note"):
            print("[Aiorbust License] %s" % data["note"])
        return (key,)


NODE_CLASS_MAPPINGS = {"AiorbustLicense": AiorbustLicense}
NODE_DISPLAY_NAME_MAPPINGS = {"AiorbustLicense": "Aiorbust License"}
