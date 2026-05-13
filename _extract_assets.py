"""Extract embedded photos from the source PNGs so the recreated panels
can drop them straight in. Run once.

Crop boxes measured against the source PNGs by pixel-edge detection.
Each crop is the photo content only — labels/dots that belong on the
matplotlib side are stripped.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))


def crop_save(src: str, box: tuple[int, int, int, int], dst: str):
    im = Image.open(os.path.join(HERE, src)).convert("RGBA")
    out = im.crop(box)
    os.makedirs(os.path.dirname(os.path.join(HERE, dst)), exist_ok=True)
    out.save(os.path.join(HERE, dst))
    print(f"{dst}  {out.size}")


def crop_circle(src: str, box: tuple[int, int, int, int], dst: str,
                center: tuple[float, float] | None = None,
                radius: float | None = None):
    """Crop, then mask to a circle so a panel can drop it on any background."""
    im = Image.open(os.path.join(HERE, src)).convert("RGBA")
    out = im.crop(box)
    w, h = out.size
    cx, cy = center if center else (w / 2, h / 2)
    r = radius if radius else min(cx, cy, w - cx, h - cy)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse(
        (cx - r, cy - r, cx + r, cy + r), fill=255
    )
    out.putalpha(mask)
    os.makedirs(os.path.dirname(os.path.join(HERE, dst)), exist_ok=True)
    out.save(os.path.join(HERE, dst))
    print(f"{dst}  {out.size} (circular mask r={int(r)})")


def main():
    # --- Figure 2 ---
    # Mouse cage photo (panel a) — full photo, no surrounding legend.
    # Photo content (dark-bordered rectangle) measured at x=68..771, y=115..499.
    crop_save("figure2/ORIG_figure_2.png", (60, 110, 780, 510),
              "figure2/assets/mouse_cage.png")

    # --- Figure 4 ---
    # Panel a — three example-frame thumbnails. Each ~250x250.
    # In-photo yellow timestamps + green dots are part of the source photo
    # overlay; they are intentionally kept.
    crop_save("figure4/ORIG_figure_4.png", (42, 154, 292, 405),
              "figure4/assets/thumb_no_label.png")
    crop_save("figure4/ORIG_figure_4.png", (314, 154, 564, 405),
              "figure4/assets/thumb_vigilant.png")
    crop_save("figure4/ORIG_figure_4.png", (585, 154, 835, 405),
              "figure4/assets/thumb_out_of_sight.png")
    # Panel e — 3x3 behavior grid as ONE asset (per user instruction).
    # Includes baked-in colored label dots per cell. Row 1 photos start ~y=900;
    # row 3 labels end ~y=1830.
    crop_save("figure4/ORIG_figure_4.png", (1070, 900, 2335, 1935),
              "figure4/assets/behavior_grid.png")

    # --- Figure 5 ---
    # Panel a — rounded boxes only, no "no raiding"/"raiding" label dots
    # (those are re-drawn in matplotlib so the labels stay editable).
    crop_save("figure5/ORIG_figure_5.png", (70, 160, 765, 500),
              "figure5/assets/petri_no_raiding.png")
    crop_save("figure5/ORIG_figure_5.png", (70, 615, 765, 970),
              "figure5/assets/petri_raiding.png")
    # Panel c — single-petri example thumbnails flanking the confusion matrix.
    # Circular mask cleans an arrow-tip artifact that overlaps the left dish.
    # Centers + radii measured from the source by pixel-edge detection.
    crop_circle(
        "figure5/ORIG_figure_5.png", (855, 660, 1125, 925),
        "figure5/assets/petri_c_left.png",
        center=(990 - 855, 790 - 660), radius=124,
    )
    crop_circle(
        "figure5/ORIG_figure_5.png", (2075, 615, 2325, 880),
        "figure5/assets/petri_c_right.png",
        center=(2200 - 2075, 743 - 615), radius=124,
    )


if __name__ == "__main__":
    main()
