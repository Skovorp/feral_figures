"""Build figure 2 via the HTML+CSS pipeline.

Steps:
  1. Render each panel as an SVG (in figure2/panels/).
  2. Invoke headless Chrome to rasterize figure2.html into figure2_html.png.

Use --force-device-scale-factor=3 so the PNG comes out at ~300 DPI even
though the HTML layout is in CSS pixels.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if path and os.path.exists(path):
            return path
    raise RuntimeError("could not find Chrome/Chromium")


def render_html(scale: int = 3, only: list[str] | None = None,
                out_name: str = "figure2_html.png") -> str:
    sys.path.insert(0, HERE)
    from _panels import render_all, SIZES  # noqa: E402

    # Determine final canvas size from the HTML's body width/height.
    # If you change the body size in figure2.html, update CANVAS_PX here.
    CANVAS_PX = (780, 820)

    print("rendering panels…")
    render_all(only=only)

    html_path = os.path.join(HERE, "figure2.html")
    out_path = os.path.join(HERE, out_name)
    chrome = find_chrome()

    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        f"--screenshot={out_path}",
        f"--window-size={CANVAS_PX[0]},{CANVAS_PX[1]}",
        f"--force-device-scale-factor={scale}",
        f"--default-background-color=ffffff",
        f"file://{html_path}",
    ]
    print(f"running chrome (scale {scale}x) …")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=int, default=3,
                   help="device pixel ratio (3 ≈ 300dpi for 100dpi CSS)")
    p.add_argument("--panels", nargs="*", default=None,
                   help="optional subset of panels to re-render (e.g. a c h)")
    p.add_argument("--out", default="figure2_html.png")
    args = p.parse_args()
    render_html(scale=args.scale, only=args.panels, out_name=args.out)
