# public-aiorbust-pack

A self-contained subset of the Aiorbust nodes — the Aiorbust custom nodes used
by the public Aiorbust workflows.

## Nodes included

| Node type | Display name | Category | Notes |
|---|---|---|---|
| `AiorbustImageBatchLoader` | Aiorbust Image Batch Loader | Aiorbust | Sequential drag-and-drop batch loader (has JS UI + upload routes) |
| `MetadataBypassNode` | Aiorbust Metadata Bypass | Aiorbust/Automation | Strips EXIF/XMP/ICC/C2PA metadata from images |
| `SaveImageWithNoMetadata` | Aiorbust Save Image (No Metadata) | Aiorbust/Automation | Saves PNGs to the output folder with **no** prompt/workflow/EXIF metadata |
| `SaveImageNoMetadataNode` | Aiorbust Save Image No Metadata | Aiorbust/Image | Saves PNG/JPEG with no workflow/prompt metadata embedded |
| `Aiorbust_Renoise` | 🎞️ Aiorbust Renoïse | Aiorbust/Post-Processing | Adds realistic sensor noise (requires `kornia`) |
| `Aiorbust_Apply_LUT` | 🎨 Aiorbust Apply LUT | Aiorbust/Post-Processing | Applies a `.cube` LUT (requires `colour-science`) |
| `aiorbustfilmgrain` | Aiorbust Film Grain | Aiorbust/Post-Processing | Adds photographic film grain |
| `Aiorbust_Camera_Look` | Aiorbust Camera Look | Aiorbust/Post-Processing | Camera pipeline: sensor noise → demosaic → motion blur → JPEG (numpy + PIL only) |
| `GrokPromptNode` | Aiorbust Grok Prompt Generator | Aiorbust/Prompt | Sends a prompt (+optional image) to the xAI Grok API (requires `requests` + an xAI API key) |
| `GeminiPromptNode` | Aiorbust Prompt Generator | Aiorbust/Prompt | Analyzes images / writes prompts via Gemini, Vertex AI or Grok; built-in JSON-analysis, style-transfer and Seedream-edit modes (has JS UI) — see note below |
| `AiorbustSpeedHDSampler` | Aiorbust Speed HD Sampler | Aiorbust/Sampling | Spectral progressive-diffusion SAMPLER (feed into SamplerCustomAdvanced); requires `scipy`, plus `PyWavelets` only for `transform=dwt` |
| `VideoFrameExtractorNode` | Aiorbust Video Frame Extractor | image | Extracts one frame from a video file in `input/`, or from a connected IMAGE batch (which replaces the file dropdown entirely); requires `av` |
| `NanoBananaAIO` | Aiorbust Image and Video Edit AIO | Aiorbust/NanoBanana | Multi-provider image & video generation (Vertex, Google, WaveSpeed, KIE, FAL). Needs `google-genai`, your own provider keys, **and an Aiorbust licence** |
| `AiorbustLicense` | Aiorbust License | Aiorbust | One key for the whole graph; wire its output into any licensed node's `license_key` input |
| `AiorbustEyeBBoxDetectorProvider` | Aiorbust HD Ultralytic BBox Loader | Aiorbust/Detailer | Ultralytics BBox loader with forced `imgsz=1280` for small objects (eyes) — see note below |
| `AiorbustDetailer` | Aiorbust Detailer | Aiorbust/Detailer | FaceDetailer clone with selectable paste-back interpolation, sharpness & color-match — see note below |

### Prompt Generator — API keys & providers

`GeminiPromptNode` talks to three providers, picked with the `provider` widget:

- **Gemini** — needs a Google AI Studio key in `gemini_api_key`
  ([aistudio.google.com](https://aistudio.google.com/apikey)). Only `requests`.
- **Grok** — needs an xAI key in `grok_api_key` ([console.x.ai](https://console.x.ai)).
  Only `requests`.
- **Vertex** — needs `vertex_json_folder` pointed at a folder of GCP service
  account `.json` files (one per project; successive runs rotate through them to
  spread the per-project quota). This provider additionally needs
  `google-genai` + `google-auth`, imported lazily — without them the node still
  loads and the other two providers still work.

The `model` dropdown lists both Gemini and Grok ids; the JS narrows what is
shown to the selected provider, and the node re-checks the pairing at run time
so an API-driven workflow cannot silently call the wrong vendor.

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
│   ├── aiorbust_image_batch_loader.js
│   └── ofm_prompt_generator.js
├── luts/
│   └── *.cube
└── nodes/
    ├── __init__.py
    ├── aiorbust_image_batch_loader.py
    ├── metadata_bypass.py
    ├── save_image_no_metadata.py         # SaveImageWithNoMetadata
    ├── save_image_no_metadata_node.py    # SaveImageNoMetadataNode
    ├── aiorbust_renoise.py
    ├── aiorbust_apply_lut.py
    ├── film_grain.py
    ├── aiorbust_camera_look.py
    ├── grok_prompt.py
    ├── gemini_prompt.py               # GeminiPromptNode (Gemini / Vertex / Grok)
    ├── aiorbust_speed_hd_sampler.py
    ├── speed_hd_core.py               # framework-agnostic math (SPEED, MIT)
    ├── speed_hd_spectral_utils.py     # spectral transforms (SPEED, MIT)
    └── aiorbust_eye_detailer.py
```
