# public-aiorbust-pack

A minimal, self-contained subset of the Aiorbust nodes — containing **only** the
Aiorbust nodes used by the public face-swap workflow.

## Nodes included

| Node type | Display name | Category | Notes |
|---|---|---|---|
| `AiorbustImageBatchLoader` | Aiorbust Image Batch Loader | Aiorbust | Sequential drag-and-drop batch loader (has JS UI + upload routes) |
| `MetadataBypassNode` | Aiorbust Metadata Bypass | Aiorbust/Automation | Strips EXIF/XMP/ICC/C2PA metadata from images |
| `SaveImageWithNoMetadata` | Aiorbust Save Image (No Metadata) | Aiorbust/Automation | Saves PNGs to the output folder with **no** prompt/workflow/EXIF metadata |
| `Aiorbust_Renoise` | 🎞️ Aiorbust Renoïse | Aiorbust/Post-Processing | Adds realistic sensor noise (requires `kornia`) |
| `Aiorbust_Apply_LUT` | 🎨 Aiorbust Apply LUT | Aiorbust/Post-Processing | Applies a `.cube` LUT (requires `colour-science`) |
| `aiorbustfilmgrain` | Aiorbust Film Grain | Aiorbust/Post-Processing | Adds photographic film grain |

## Installation

1. Place this `public-aiorbust-pack` folder in `ComfyUI/custom_nodes/`.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (For the ComfyUI portable build, use its embedded python:
   `..\..\python_embeded\python.exe -m pip install -r requirements.txt`)
3. Restart ComfyUI.

## LUT files

Drop your `.cube` files into the `luts/` folder at the pack root. One sample LUT
is included. The `Aiorbust Apply LUT` node lists every `.cube` found there.

## Structure

```
public-aiorbust-pack/
├── __init__.py                 # registers the 4 nodes
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
    ├── save_image_no_metadata.py
    ├── aiorbust_renoise.py
    ├── aiorbust_apply_lut.py
    └── film_grain.py
```
