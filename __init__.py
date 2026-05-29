"""
public-aiorbust-pack
=====================
A minimal, self-contained subset of the Aiorbust nodes — only the four nodes
used by the public face-swap workflow:

    - Aiorbust Image Batch Loader   (AiorbustImageBatchLoader)
    - Aiorbust Metadata Bypass      (MetadataBypassNode)
    - Aiorbust Renoise              (Aiorbust_Renoise)
    - Aiorbust Apply LUT            (Aiorbust_Apply_LUT)
    - Aiorbust Film Grain           (aiorbustfilmgrain)
"""

from .nodes.aiorbust_image_batch_loader import (
    NODE_CLASS_MAPPINGS as _batch_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _batch_disp,
)
from .nodes.aiorbust_renoise import (
    NODE_CLASS_MAPPINGS as _renoise_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _renoise_disp,
)
from .nodes.aiorbust_apply_lut import (
    NODE_CLASS_MAPPINGS as _lut_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _lut_disp,
)
from .nodes.film_grain import (
    NODE_CLASS_MAPPINGS as _grain_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _grain_disp,
)
from .nodes.metadata_bypass import MetadataBypassNode

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Modules that already expose their own mappings
for _cls, _disp in (
    (_batch_cls, _batch_disp),
    (_renoise_cls, _renoise_disp),
    (_lut_cls, _lut_disp),
    (_grain_cls, _grain_disp),
):
    NODE_CLASS_MAPPINGS.update(_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_disp)

# metadata_bypass exposes only the class
NODE_CLASS_MAPPINGS["MetadataBypassNode"] = MetadataBypassNode
NODE_DISPLAY_NAME_MAPPINGS["MetadataBypassNode"] = "Aiorbust Metadata Bypass"

# JS UI assets (used by the Image Batch Loader node)
WEB_DIRECTORY = "./js"

print(f"[public-aiorbust-pack] Loaded {len(NODE_CLASS_MAPPINGS)} nodes: "
      f"{', '.join(NODE_CLASS_MAPPINGS.keys())}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
