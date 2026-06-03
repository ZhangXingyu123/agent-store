---
name: zebra-image
description: Use when the user wants to convert, stylize, recolor, or transform an input image into a zebra-style black-and-white striped image. Trigger on zebra image, zebra color, zebra stripes, black-white stripe effect, 图片斑马色, 斑马纹, 斑马条纹, 图片处理, and 把图片改成斑马色.
---

# Zebra Image

Use this skill to help the user turn an input image into a zebra-style black-and-white striped image.

## What this demo skill does

- Accepts common image files such as PNG, JPG, JPEG, TIFF, GIF, BMP, HEIC, and other formats readable by macOS `sips`.
- Generates a PNG output with curved black-and-white zebra stripes.
- Preserves the input image size and alpha channel when available.
- Writes an optional JSON summary containing dimensions and effect settings.

This minimal demo does not use AI image generation. It applies a deterministic local image filter. In a production version, this step could be replaced by a cloud image API or an MCP image runtime.

## Workflow

1. Confirm the user supplied an input image path and wants a zebra-style output.
2. Choose an output path ending in `.png`.
3. Run the helper script from the plugin root:

```bash
python3 scripts/zebra_image.py --input <input-image> --output <output.png> --summary <summary.json>
```

When running from inside the plugin skill directory, the script is at `../../scripts/zebra_image.py`.

4. Return the output image path and the summary details.

## Options

- `--stripe-width 18` controls stripe thickness in pixels.
- `--strength 0.95` controls how strongly the zebra effect overrides the original image.

## Output

Return:

- the zebra-style PNG path
- optional `summary.json`
- image dimensions and effect settings

