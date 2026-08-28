"""
ComfyUI node - Aiorbust Load API Keys.

Enter each provider key once and wire the outputs into the nodes that need
them. The point is not convenience: a key typed directly into a generator node
is saved into the workflow JSON, so sharing that workflow ships the key with
it. Kept in one node, there is a single widget to clear before a workflow
leaves the machine.
"""


class ApiKeysLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "gemini_api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Gemini API Key - aistudio.google.com",
                }),
                "wavespeed_api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "WaveSpeed API Key - wavespeed.ai",
                }),
                "fal_api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "fal.ai API Key - fal.ai/dashboard/keys",
                }),
                "kie_api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Kie.ai API Key - kie.ai",
                }),
            },
        }

    RETURN_TYPES  = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES  = ("gemini_api_key", "wavespeed_api_key", "fal_api_key", "kie_api_key")
    FUNCTION      = "load"
    CATEGORY      = "Aiorbust/NanoBanana"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always dirty: a key edited between runs must reach the downstream node
        # rather than being served from a cached execution.
        return float("nan")

    def load(self, gemini_api_key="", wavespeed_api_key="", fal_api_key="", kie_api_key=""):
        return (
            gemini_api_key.strip(),
            wavespeed_api_key.strip(),
            fal_api_key.strip(),
            kie_api_key.strip(),
        )


# Kept as an alias: the registered node id is LoadAPIKeysNode, and existing
# workflows reference it by that name.
LoadAPIKeysNode = ApiKeysLoaderNode

NODE_CLASS_MAPPINGS = {"LoadAPIKeysNode": ApiKeysLoaderNode}
NODE_DISPLAY_NAME_MAPPINGS = {"LoadAPIKeysNode": "Aiorbust Load API Keys"}
