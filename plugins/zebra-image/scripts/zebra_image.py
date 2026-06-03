#!/usr/bin/env python3
"""Apply a zebra-style black-and-white stripe effect to an image.

This demo intentionally avoids third-party Python packages. On macOS it uses
`sips` only as a format converter for non-PNG inputs, then handles PNG pixels in
standard-library Python.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Iterable


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_COLOR_CHANNELS = {
    0: 1,
    2: 3,
    3: 1,
    4: 2,
    6: 4,
}


class ImageError(ValueError):
    """Raised when the demo cannot decode or encode the requested image."""


def read_chunks(data: bytes) -> Iterable[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise ImageError("Input is not a PNG file.")

    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        if offset + 8 > len(data):
            raise ImageError("PNG chunk header is truncated.")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        offset += 8
        chunk_data = data[offset : offset + length]
        offset += length
        if offset + 4 > len(data):
            raise ImageError("PNG chunk CRC is truncated.")
        offset += 4
        yield chunk_type, chunk_data
        if chunk_type == b"IEND":
            break


def paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def unfilter_scanline(filter_type: int, scanline: bytearray, previous: bytes, bytes_per_pixel: int) -> bytes:
    for index, value in enumerate(scanline):
        left = scanline[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        up = previous[index] if previous else 0
        upper_left = previous[index - bytes_per_pixel] if previous and index >= bytes_per_pixel else 0

        if filter_type == 0:
            reconstructed = value
        elif filter_type == 1:
            reconstructed = value + left
        elif filter_type == 2:
            reconstructed = value + up
        elif filter_type == 3:
            reconstructed = value + ((left + up) // 2)
        elif filter_type == 4:
            reconstructed = value + paeth_predictor(left, up, upper_left)
        else:
            raise ImageError(f"Unsupported PNG filter type: {filter_type}")

        scanline[index] = reconstructed & 0xFF
    return bytes(scanline)


def read_png(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    data = path.read_bytes()
    width = height = bit_depth = color_type = compression = filter_method = interlace = None
    palette: list[tuple[int, int, int]] = []
    transparency: bytes = b""
    compressed_parts: list[bytes] = []

    for chunk_type, chunk_data in read_chunks(data):
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"PLTE":
            palette = [
                tuple(chunk_data[index : index + 3])  # type: ignore[arg-type]
                for index in range(0, len(chunk_data), 3)
            ]
        elif chunk_type == b"tRNS":
            transparency = chunk_data
        elif chunk_type == b"IDAT":
            compressed_parts.append(chunk_data)

    if None in {width, height, bit_depth, color_type, compression, filter_method, interlace}:
        raise ImageError("PNG is missing an IHDR chunk.")
    if bit_depth != 8:
        raise ImageError("This demo supports 8-bit PNG inputs only.")
    if color_type not in PNG_COLOR_CHANNELS:
        raise ImageError(f"Unsupported PNG color type: {color_type}")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ImageError("This demo supports non-interlaced PNG images only.")

    channels = PNG_COLOR_CHANNELS[color_type]
    row_length = width * channels
    raw = zlib.decompress(b"".join(compressed_parts))
    pixels: list[tuple[int, int, int, int]] = []
    previous = b"\x00" * row_length
    offset = 0

    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        scanline = bytearray(raw[offset : offset + row_length])
        offset += row_length
        reconstructed = unfilter_scanline(filter_type, scanline, previous, channels)
        previous = reconstructed

        for x in range(width):
            base = x * channels
            if color_type == 0:
                gray = reconstructed[base]
                pixels.append((gray, gray, gray, 255))
            elif color_type == 2:
                pixels.append((reconstructed[base], reconstructed[base + 1], reconstructed[base + 2], 255))
            elif color_type == 3:
                palette_index = reconstructed[base]
                if palette_index >= len(palette):
                    raise ImageError("PNG palette index is out of range.")
                red, green, blue = palette[palette_index]
                alpha = transparency[palette_index] if palette_index < len(transparency) else 255
                pixels.append((red, green, blue, alpha))
            elif color_type == 4:
                gray = reconstructed[base]
                pixels.append((gray, gray, gray, reconstructed[base + 1]))
            elif color_type == 6:
                pixels.append(
                    (
                        reconstructed[base],
                        reconstructed[base + 1],
                        reconstructed[base + 2],
                        reconstructed[base + 3],
                    )
                )

    return width, height, pixels


def png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(chunk_data, crc)
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    if len(pixels) != width * height:
        raise ImageError("Pixel count does not match image dimensions.")

    rows = []
    for y in range(height):
        row = bytearray([0])
        for red, green, blue, alpha in pixels[y * width : (y + 1) * width]:
            row.extend((red, green, blue, alpha))
        rows.append(bytes(row))

    path.parent.mkdir(parents=True, exist_ok=True)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=6))
        + png_chunk(b"IEND", b"")
    )


def convert_to_png_with_sips(input_path: Path) -> Path:
    sips = shutil.which("sips")
    if not sips:
        raise ImageError("This input is not a supported PNG, and macOS 'sips' is unavailable for conversion.")

    temp_dir = Path(tempfile.mkdtemp(prefix="zebra-image-"))
    converted = temp_dir / "input.png"
    result = subprocess.run(
        [sips, "-s", "format", "png", str(input_path), "--out", str(converted)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ImageError(result.stderr.strip() or result.stdout.strip() or "sips could not convert the image.")
    return converted


def read_image(input_path: Path) -> tuple[int, int, list[tuple[int, int, int, int]], str]:
    try:
        width, height, pixels = read_png(input_path)
        return width, height, pixels, "png"
    except Exception as png_error:
        converted = convert_to_png_with_sips(input_path)
        try:
            width, height, pixels = read_png(converted)
            return width, height, pixels, f"{input_path.suffix.lstrip('.').lower() or 'image'} via sips"
        except Exception as converted_error:
            raise ImageError(f"Could not decode image: {converted_error}") from png_error


def clamp_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def apply_zebra_effect(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int, int]],
    stripe_width: int,
    strength: float,
) -> list[tuple[int, int, int, int]]:
    stripe_width = max(4, stripe_width)
    strength = max(0.0, min(1.0, strength))
    output: list[tuple[int, int, int, int]] = []

    for y in range(height):
        curve = math.sin(y * 0.095) * stripe_width * 0.9
        for x in range(width):
            red, green, blue, alpha = pixels[y * width + x]
            luminance = 0.299 * red + 0.587 * green + 0.114 * blue
            wave = x + y * 0.42 + curve + math.sin((x + y) * 0.035) * stripe_width * 0.3
            white_band = int(math.floor(wave / stripe_width)) % 2 == 0

            if white_band:
                target = 218 + luminance * 0.14
            else:
                target = luminance * 0.18

            zebra = clamp_channel(target)
            output.append(
                (
                    clamp_channel(red * (1.0 - strength) + zebra * strength),
                    clamp_channel(green * (1.0 - strength) + zebra * strength),
                    clamp_channel(blue * (1.0 - strength) + zebra * strength),
                    alpha,
                )
            )

    return output


def create_sample(path: Path) -> dict[str, object]:
    width, height = 180, 120
    pixels: list[tuple[int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            red = int(40 + 170 * x / (width - 1))
            green = int(60 + 150 * y / (height - 1))
            blue = int(210 - 80 * x / (width - 1))
            pixels.append((red, green, blue, 255))
    write_png(path, width, height, pixels)
    return {"sample": str(path), "width": width, "height": height}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Input image path.")
    parser.add_argument("--output", help="Output PNG path.")
    parser.add_argument("--summary", help="Optional output summary JSON path.")
    parser.add_argument("--stripe-width", type=int, default=18, help="Stripe width in pixels.")
    parser.add_argument("--strength", type=float, default=0.95, help="Effect strength from 0 to 1.")
    parser.add_argument("--create-sample", help="Create a small sample input PNG at this path.")
    args = parser.parse_args()

    if args.create_sample:
        summary = create_sample(Path(args.create_sample))
        print(json.dumps(summary, ensure_ascii=False))
        return

    if not args.input or not args.output:
        parser.error("--input and --output are required unless --create-sample is used.")

    input_path = Path(args.input)
    output_path = Path(args.output)
    width, height, pixels, decoded_as = read_image(input_path)
    output_pixels = apply_zebra_effect(width, height, pixels, args.stripe_width, args.strength)
    write_png(output_path, width, height, output_pixels)

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "width": width,
        "height": height,
        "decoded_as": decoded_as,
        "stripe_width": max(4, args.stripe_width),
        "strength": max(0.0, min(1.0, args.strength)),
        "effect": "zebra black-white stripes",
    }

    if args.summary:
        summary_path = Path(args.summary)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
