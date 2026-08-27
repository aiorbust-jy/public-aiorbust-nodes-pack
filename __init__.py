"""
public-aiorbust-pack
=====================
A self-contained subset of the Aiorbust nodes — the Aiorbust custom nodes used
by the public Aiorbust workflows:

    - Aiorbust Image Batch Loader        (AiorbustImageBatchLoader)
    - Aiorbust Metadata Bypass           (MetadataBypassNode)
    - Aiorbust Renoise                   (Aiorbust_Renoise)
    - Aiorbust Apply LUT                 (Aiorbust_Apply_LUT)
    - Aiorbust Film Grain                (aiorbustfilmgrain)
    - Aiorbust Camera Look               (Aiorbust_Camera_Look)
    - Aiorbust Grok Prompt Generator     (GrokPromptNode)
    - Aiorbust Prompt Generator          (GeminiPromptNode)
    - Aiorbust Save Image (No Metadata)  (SaveImageWithNoMetadata)
    - Aiorbust Save Image No Metadata    (SaveImageNoMetadataNode)
    - Aiorbust Speed HD Sampler          (AiorbustSpeedHDSampler)**
    - Aiorbust Resolution (MP)           (AiorbustResolutionMP)
    - Aiorbust H3 Frame Snap             (AiorbustH3FrameSnap)
    - Aiorbust Audio Switch              (AiorbustAudioSwitch)
    - Aiorbust Group Toggle              (AiorbustGroupToggle)
    - Aiorbust Image Black Check         (ImageBlackCheckNode)
    - H3 Context-IR (Gemini)             (H3ContextIR)
    - Aiorbust HD Ultralytic BBox Loader (AiorbustEyeBBoxDetectorProvider)*
    - Aiorbust Detailer                  (AiorbustDetailer)*

    * The two Detailer nodes require ComfyUI-Impact-Pack and
      ComfyUI-Impact-Subpack to be installed (resolved lazily at run time).
    ** The Speed HD Sampler needs scipy (and PyWavelets only for transform=dwt).
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
from .nodes.aiorbust_camera_look import (
    NODE_CLASS_MAPPINGS as _camera_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _camera_disp,
)
from .nodes.grok_prompt import (
    NODE_CLASS_MAPPINGS as _grok_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _grok_disp,
)
from .nodes.gemini_prompt import (
    NODE_CLASS_MAPPINGS as _gemini_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _gemini_disp,
)
from .nodes.save_image_no_metadata import (
    NODE_CLASS_MAPPINGS as _savenm_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _savenm_disp,
)
from .nodes.save_image_no_metadata_node import (
    NODE_CLASS_MAPPINGS as _savenometa_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _savenometa_disp,
)
from .nodes.aiorbust_resolution_mp import (
    NODE_CLASS_MAPPINGS as _resmp_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _resmp_disp,
)
from .nodes.aiorbust_h3_frame_snap import (
    NODE_CLASS_MAPPINGS as _framesnap_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _framesnap_disp,
)
from .nodes.aiorbust_audio_switch import (
    NODE_CLASS_MAPPINGS as _audiosw_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _audiosw_disp,
)
from .nodes.h3_context_ir import (
    NODE_CLASS_MAPPINGS as _ctxir_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _ctxir_disp,
)
from .nodes.aiorbust_group_toggle import (
    NODE_CLASS_MAPPINGS as _grouptoggle_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _grouptoggle_disp,
)
from .nodes.metadata_bypass import MetadataBypassNode
from .nodes.image_black_check import ImageBlackCheckNode

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Modules that already expose their own mappings
for _cls, _disp in (
    (_batch_cls, _batch_disp),
    (_renoise_cls, _renoise_disp),
    (_lut_cls, _lut_disp),
    (_grain_cls, _grain_disp),
    (_camera_cls, _camera_disp),
    (_grok_cls, _grok_disp),
    (_gemini_cls, _gemini_disp),
    (_savenm_cls, _savenm_disp),
    (_savenometa_cls, _savenometa_disp),
    (_resmp_cls, _resmp_disp),
    (_framesnap_cls, _framesnap_disp),
    (_audiosw_cls, _audiosw_disp),
    (_grouptoggle_cls, _grouptoggle_disp),
    (_ctxir_cls, _ctxir_disp),
):
    NODE_CLASS_MAPPINGS.update(_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_disp)

# These two modules expose only the class
NODE_CLASS_MAPPINGS["MetadataBypassNode"] = MetadataBypassNode
NODE_DISPLAY_NAME_MAPPINGS["MetadataBypassNode"] = "Aiorbust Metadata Bypass"

NODE_CLASS_MAPPINGS["ImageBlackCheckNode"] = ImageBlackCheckNode
NODE_DISPLAY_NAME_MAPPINGS["ImageBlackCheckNode"] = "Aiorbust Image Black Check"

# The two Detailer nodes depend on Impact Pack / Impact Subpack. Load them
# defensively so a missing dependency never takes the whole pack down — the
# other nodes stay available and only the Detailer nodes are skipped.
try:
    from .nodes.aiorbust_eye_detailer import (
        NODE_CLASS_MAPPINGS as _detailer_cls,
        NODE_DISPLAY_NAME_MAPPINGS as _detailer_disp,
    )
    NODE_CLASS_MAPPINGS.update(_detailer_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_detailer_disp)
except Exception as _e:
    print(f"[public-aiorbust-pack] Detailer nodes not loaded "
          f"(needs ComfyUI-Impact-Pack + Impact-Subpack): {_e}")

# The Speed HD Sampler needs scipy (imported at module load). Load it
# defensively so a missing scipy never takes the whole pack down.
try:
    from .nodes.aiorbust_speed_hd_sampler import (
        NODE_CLASS_MAPPINGS as _speedhd_cls,
        NODE_DISPLAY_NAME_MAPPINGS as _speedhd_disp,
    )
    NODE_CLASS_MAPPINGS.update(_speedhd_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_speedhd_disp)
except Exception as _e:
    print(f"[public-aiorbust-pack] Speed HD Sampler not loaded "
          f"(needs scipy): {_e}")

# JS UI assets (Image Batch Loader + Prompt Generator + Group Toggle)
WEB_DIRECTORY = "./js"

print(f"[public-aiorbust-pack] Loaded {len(NODE_CLASS_MAPPINGS)} nodes: "
      f"{', '.join(NODE_CLASS_MAPPINGS.keys())}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
