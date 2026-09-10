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
    - Aiorbust Prompt Writer             (AiorbustPromptWriter)
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
    - Aiorbust Load API Keys             (LoadAPIKeysNode)
    - Aiorbust Video Frame Extractor     (VideoFrameExtractorNode)
    - Aiorbust License                   (AiorbustLicense)
    - Aiorbust Image and Video Edit AIO  (NanoBananaAIO)***
    - Aiorbust HD Ultralytic BBox Loader (AiorbustEyeBBoxDetectorProvider)*
    - Aiorbust Detailer                  (AiorbustDetailer)*

    * The two Detailer nodes require ComfyUI-Impact-Pack and
      ComfyUI-Impact-Subpack to be installed (resolved lazily at run time).
    ** The Speed HD Sampler needs scipy (and PyWavelets only for transform=dwt).
    *** The AIO node needs google-genai, and a licence: it verifies with the
        Aiorbust service before it will run.
    Drop an Aiorbust License node anywhere in the graph and every licensed
    node picks the key up from it -- no wire needed, though its output is
    still there for anyone who wants one. Or set AIORBUST_LICENSE_KEY and
    leave them all alone.

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
from .nodes.aiorbust_prompt_writer import (
    NODE_CLASS_MAPPINGS as _writer_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _writer_disp,
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
from .nodes.api_keys import (
    NODE_CLASS_MAPPINGS as _apikeys_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _apikeys_disp,
)
from .nodes.video_frame_extractor import (
    NODE_CLASS_MAPPINGS as _vfx_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _vfx_disp,
)
from .nodes.aiorbust_license import (
    NODE_CLASS_MAPPINGS as _lic_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _lic_disp,
)
from .nodes.aiorbust_segment_cache import (
    NODE_CLASS_MAPPINGS as _segcache_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _segcache_disp,
)
from .nodes.aiorbust_rife_batched import (
    NODE_CLASS_MAPPINGS as _rife_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _rife_disp,
)
from .nodes.aiorbust_save_video_no_metadata import (
    NODE_CLASS_MAPPINGS as _savevid_cls,
    NODE_DISPLAY_NAME_MAPPINGS as _savevid_disp,
)
from .nodes.metadata_bypass import MetadataBypassNode
from .nodes.image_black_check import ImageBlackCheckNode
from .nodes.imageUtils import PreviewImageWithoutMetadata
from .nodes.aiorbust_image_blur_batched import (
    AiorbustImageBlurBatched, AiorbustImageCompositeMaskedBatched,
)
from .nodes.aiorbust_images_to_video import AiorbustImagesToVideo
from .nodes.aiorbust_prompt_library import AiorbustPromptSaver, AiorbustPromptGallery
from .nodes.aiorbust_video_chain import (
    AiorbustVideoChainSegment, AiorbustVideoChainJoin,
    AiorbustVideoChainPrepare, AiorbustVideoChainCommit,
)

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
    (_writer_cls, _writer_disp),
    (_gemini_cls, _gemini_disp),
    (_savenm_cls, _savenm_disp),
    (_savenometa_cls, _savenometa_disp),
    (_resmp_cls, _resmp_disp),
    (_framesnap_cls, _framesnap_disp),
    (_audiosw_cls, _audiosw_disp),
    (_grouptoggle_cls, _grouptoggle_disp),
    (_ctxir_cls, _ctxir_disp),
    (_apikeys_cls, _apikeys_disp),
    (_vfx_cls, _vfx_disp),
    (_lic_cls, _lic_disp),
    (_segcache_cls, _segcache_disp),
    (_rife_cls, _rife_disp),
    (_savevid_cls, _savevid_disp),
):
    NODE_CLASS_MAPPINGS.update(_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_disp)

# These two modules expose only the class
NODE_CLASS_MAPPINGS["MetadataBypassNode"] = MetadataBypassNode
NODE_DISPLAY_NAME_MAPPINGS["MetadataBypassNode"] = "Aiorbust Metadata Bypass"

NODE_CLASS_MAPPINGS["ImageBlackCheckNode"] = ImageBlackCheckNode
NODE_DISPLAY_NAME_MAPPINGS["ImageBlackCheckNode"] = "Aiorbust Image Black Check"

# imageUtils also defines SaveImageWithoutMetadata, but that is a base class the
# private pack does not register either -- only the Preview subclass is a node.
NODE_CLASS_MAPPINGS["PreviewImageWithoutMetadata"] = PreviewImageWithoutMetadata
NODE_DISPLAY_NAME_MAPPINGS["PreviewImageWithoutMetadata"] = "Aiorbust Preview No Metadata"

# The V14 video-chain, prompt-library and batched-image nodes expose only
# their classes, like the two above.
NODE_CLASS_MAPPINGS["AiorbustImageBlurBatched"] = AiorbustImageBlurBatched
NODE_DISPLAY_NAME_MAPPINGS["AiorbustImageBlurBatched"] = "Aiorbust Image Blur (batched)"
NODE_CLASS_MAPPINGS["AiorbustImageCompositeMaskedBatched"] = AiorbustImageCompositeMaskedBatched
NODE_DISPLAY_NAME_MAPPINGS["AiorbustImageCompositeMaskedBatched"] = "Aiorbust Image Composite Masked (batched)"
NODE_CLASS_MAPPINGS["AiorbustImagesToVideo"] = AiorbustImagesToVideo
NODE_DISPLAY_NAME_MAPPINGS["AiorbustImagesToVideo"] = "Aiorbust Images to Video (AB_VIDEO)"
NODE_CLASS_MAPPINGS["AiorbustPromptSaver"] = AiorbustPromptSaver
NODE_DISPLAY_NAME_MAPPINGS["AiorbustPromptSaver"] = "Aiorbust Prompt Saver"
NODE_CLASS_MAPPINGS["AiorbustPromptGallery"] = AiorbustPromptGallery
NODE_DISPLAY_NAME_MAPPINGS["AiorbustPromptGallery"] = "Aiorbust Prompt Gallery"
NODE_CLASS_MAPPINGS["AiorbustVideoChainSegment"] = AiorbustVideoChainSegment
NODE_DISPLAY_NAME_MAPPINGS["AiorbustVideoChainSegment"] = "Aiorbust Video Chain — Segment"
NODE_CLASS_MAPPINGS["AiorbustVideoChainJoin"] = AiorbustVideoChainJoin
NODE_DISPLAY_NAME_MAPPINGS["AiorbustVideoChainJoin"] = "Aiorbust Video Chain — Join"
NODE_CLASS_MAPPINGS["AiorbustVideoChainPrepare"] = AiorbustVideoChainPrepare
NODE_DISPLAY_NAME_MAPPINGS["AiorbustVideoChainPrepare"] = "Aiorbust Video Chain — Prepare"
NODE_CLASS_MAPPINGS["AiorbustVideoChainCommit"] = AiorbustVideoChainCommit
NODE_DISPLAY_NAME_MAPPINGS["AiorbustVideoChainCommit"] = "Aiorbust Video Chain — Commit"

# The two Detailer nodes depend on Impact Pack / Impact Subpack. Load them
# defensively so a missing dependency never takes the whole pack down — the
# other nodes stay available and only the Detailer nodes are skipped.
try:
    # The module registers nothing itself -- it says so at the bottom of the
    # file -- so the two classes are named and mapped here.
    from .nodes.aiorbust_eye_detailer import (
        AiorbustEyeBBoxDetectorProvider, AiorbustDetailer,
    )
    NODE_CLASS_MAPPINGS["AiorbustEyeBBoxDetectorProvider"] = AiorbustEyeBBoxDetectorProvider
    NODE_CLASS_MAPPINGS["AiorbustDetailer"] = AiorbustDetailer
    NODE_DISPLAY_NAME_MAPPINGS["AiorbustEyeBBoxDetectorProvider"] = "Aiorbust HD Ultralytic BBox Loader"
    NODE_DISPLAY_NAME_MAPPINGS["AiorbustDetailer"] = "Aiorbust Detailer"
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

# The AIO node imports google.genai and aiohttp at module load. Load it
# defensively for the same reason as the two above: a missing dependency should
# cost one node, not the whole pack.
try:
    from .nodes.nano_banana_aio import (
        NODE_CLASS_MAPPINGS as _aio_cls,
        NODE_DISPLAY_NAME_MAPPINGS as _aio_disp,
    )
    NODE_CLASS_MAPPINGS.update(_aio_cls)
    NODE_DISPLAY_NAME_MAPPINGS.update(_aio_disp)
except Exception as _e:
    print(f"[public-aiorbust-pack] Image and Video Edit AIO not loaded "
          f"(needs google-genai): {_e}")

# ---------------------------------------------------------------------------
# Stand down against the private pack.
#
# This pack is a subset of aiorbust-ofm-pack and shares most of its node ids.
# ComfyUI keeps one global registry, so on a machine carrying both, the pack
# that imports last wins -- and that order is alphabetical, so this one wins.
# On a customer pod that is correct and this code does nothing. On a development
# machine carrying both it is backwards: the licensed stub of H3 Context-IR
# would shadow the full local node it is a stub OF.
#
# The private pack writes .aiorbust-private naming what it owns; anything on
# that list is dropped here. Set AIORBUST_IGNORE_PRIVATE=1 to suppress this and
# force the public build to register -- which is how you test the licensed path
# on a machine that also has the private pack.
def _private_pack_node_ids():
    import json
    import os

    if os.environ.get("AIORBUST_IGNORE_PRIVATE", "").strip():
        return None, "AIORBUST_IGNORE_PRIVATE"

    custom_nodes = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        siblings = sorted(os.listdir(custom_nodes))
    except OSError:
        return None, None

    here = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    for name in siblings:
        if name == here:
            continue
        marker = os.path.join(custom_nodes, name, ".aiorbust-private")
        if not os.path.isfile(marker):
            continue
        try:
            with open(marker, "r", encoding="utf-8") as fh:
                ids = json.load(fh).get("node_ids") or []
            # An empty list means the private pack imported but registered
            # nothing -- a broken install, not a claim of ownership. Deferring
            # to it would leave the user with no nodes from either pack.
            if ids:
                return set(ids), name
        except (OSError, ValueError) as exc:
            print(f"[public-aiorbust-pack] Ignoring unreadable {marker}: {exc}")
    return None, None


_owned, _owner = _private_pack_node_ids()
if _owner == "AIORBUST_IGNORE_PRIVATE":
    print("[public-aiorbust-pack] AIORBUST_IGNORE_PRIVATE set — registering "
          "everything, including ids the private pack may also claim.")
elif _owned:
    _dropped = sorted(set(NODE_CLASS_MAPPINGS) & _owned)
    for _node_id in _dropped:
        NODE_CLASS_MAPPINGS.pop(_node_id, None)
        NODE_DISPLAY_NAME_MAPPINGS.pop(_node_id, None)
    if _dropped:
        print(f"[public-aiorbust-pack] {_owner} is installed and owns "
              f"{len(_dropped)} of these nodes — leaving them to it: "
              f"{', '.join(_dropped)}")
        print("[public-aiorbust-pack] Set AIORBUST_IGNORE_PRIVATE=1 to register "
              "them here instead (e.g. to test the licensed nodes).")

# JS UI assets (Image Batch Loader + Prompt Generator + Group Toggle)
WEB_DIRECTORY = "./js"

print(f"[public-aiorbust-pack] Loaded {len(NODE_CLASS_MAPPINGS)} nodes: "
      f"{', '.join(NODE_CLASS_MAPPINGS.keys())}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
