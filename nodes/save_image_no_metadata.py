"""
Aiorbust Save Image (No Metadata)
Saves images to the ComfyUI output folder as PNG **without** embedding any
metadata -- no prompt, no workflow JSON, no EXIF/XMP/ICC/C2PA chunks. A clean
drop-in replacement for the default Save Image node when you need bare files.
"""

import os

import numpy as np
from PIL import Image

import folder_paths


class SaveImageWithNoMetadata:
    """Save Image variant that writes PNGs with zero embedded metadata."""

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save with no metadata."}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Aiorbust/Automation"
    DESCRIPTION = "Saves the input images to the output directory as PNG with all metadata stripped."

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])

        results = []
        for batch_number, image in enumerate(images):
            # Tensor [H, W, 3] float32 0-1 -> uint8 PIL
            np_img = (image.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(np_img, mode="RGB")

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"

            # No pnginfo argument -> no metadata chunks are written.
            pil_img.save(
                os.path.join(full_output_folder, file),
                format="PNG",
                compress_level=self.compress_level,
            )
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type,
            })
            counter += 1

        print(f"[Save Image No Metadata] Saved {len(results)} image(s) to {full_output_folder}")
        return {"ui": {"images": results}}


NODE_CLASS_MAPPINGS = {
    "SaveImageWithNoMetadata": SaveImageWithNoMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWithNoMetadata": "Aiorbust Save Image (No Metadata)",
}
