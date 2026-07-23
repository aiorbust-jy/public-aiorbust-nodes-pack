# public-aiorbust-pack

A self-contained subset of the Aiorbust nodes — the Aiorbust custom nodes used
by the public Aiorbust workflows.

## Nodes included

| Node type | Display name | Category | Notes |
|---|---|---|---|
| `AiorbustImageBatchLoader` | Aiorbust Image Batch Loader | Aiorbust | Sequential drag-and-drop batch loader (has JS UI + upload routes) |
| `MetadataBypassNode` | Aiorbust Metadata Bypass | Aiorbust/Automation | Strips EXIF/XMP/ICC/C2PA metadata from images |
| `Aiorbust_Renoise` | 🎞️ Aiorbust Renoïse | Aiorbust/Post-Processing | Adds realistic sensor noise (requires `kornia`) |
| `Aiorbust_Apply_LUT` | 🎨 Aiorbust Apply LUT | Aiorbust/Post-Processing | Applies a `.cube` LUT (requires `colour-science`) |
| `Aiorbust_Camera_Look` | Aiorbust Camera Look | Aiorbust/Post-Processing | Camera pipeline: sensor noise → demosaic → motion blur → JPEG (numpy + PIL only) |
| `GrokPromptNode` | Aiorbust Grok Prompt Generator | Aiorbust/Prompt | Sends a prompt (+optional image) to the xAI Grok API (requires `requests` + an xAI API key) |
| `SaveImageNoMetadataNode` | Aiorbust Save Image No Metadata | Aiorbust/Image | Saves PNG/JPEG with no workflow/prompt metadata embedded |
| `AiorbustEyeBBoxDetectorProvider` | Aiorbust HD Ultralytic BBox Loader | Aiorbust/Detailer | Ultralytics BBox loader with forced `imgsz=1280` for small objects (eyes) — see note below |
| `AiorbustDetailer` | Aiorbust Detailer | Aiorbust/Detailer | FaceDetailer clone with selectable paste-back interpolation, sharpness & color-match — see note below |

### Detailer nodes — extra dependency

`AiorbustEyeBBoxDetectorProvider` and `AiorbustDetailer` are patched copies of
Impact Pack / Impact Subpack nodes. They require these custom node packs to be
installed and enabled:

- **ComfyUI-Impact-Pack**
- **ComfyUI-Impact-Subpack**

They also need `opencv-python`. The Impact modules are resolved lazily at run
time, so if they are missing the two Detailer nodes are simply skipped at
startup (a message is printed) and the rest of the pack still loads.

## Installation

1. Place this `public-aiorbust-pack` folder in `ComfyUI/custom_nodes/`.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (For the ComfyUI portable build, use its embedded python:
   `..\..\python_embeded\python.exe -m pip install -r requirements.txt`)
3. For the Detailer nodes, also install **ComfyUI-Impact-Pack** and
   **ComfyUI-Impact-Subpack** (e.g. via ComfyUI-Manager).
4. Restart ComfyUI.

## LUT files

Drop your `.cube` files into the `luts/` folder at the pack root. One sample LUT
is included. The `Aiorbust Apply LUT` node lists every `.cube` found there.

## Structure

```
public-aiorbust-pack/
├── __init__.py                 # registers the nodes
├── requirements.txt
├── README.md
├── js/
│   └── aiorbust_image_batch_loader.js
├── luts/
│   └── *.cube
└── nodes/
    ├── __init__.py
    ├── aiorbust_image_batch_loader.py
    ├── metadata_bypass.py
    ├── aiorbust_renoise.py
    ├── aiorbust_apply_lut.py
    ├── aiorbust_camera_look.py
    ├── grok_prompt.py
    ├── save_image_no_metadata.py
    └── aiorbust_eye_detailer.py
```
