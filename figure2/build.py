"""Build figure 2 via the HTML+CSS pipeline.

Steps:
  1. Render each panel as an SVG (figure2/panels/).
  2. Run Chrome headless with --dump-dom to detect any overflow.
     (figure2.html contains a tiny JS overflow checker that writes a
      report into a hidden #overflow-report div.)
  3. Run Chrome a second time to rasterize the page into figure2_html.png.

Step 2 fails the build (returns non-zero) if any panel overflows the page
or each other in unexpected ways.
"""
from __future__ import annotations

import argparse
import os
import re
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


def _check_overflow(chrome: str, html_path: str, canvas_px) -> list[str]:
    """Run Chrome with --dump-dom, parse <div id='overflow-report'> contents."""
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={canvas_px[0]},{canvas_px[1]}",
        "--virtual-time-budget=2000",
        "--dump-dom",
        f"file://{html_path}",
    ]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    html = res.stdout
    # Find the overflow report text
    m = re.search(
        r'<div[^>]*id="overflow-report"[^>]*>(.*?)</div>',
        html, re.DOTALL,
    )
    if not m:
        return ["overflow-report div not found in dumped DOM"]
    contents = m.group(1).strip()
    if contents == "OVERFLOW_OK" or contents == "":
        return []
    if contents.startswith("OVERFLOW_FOUND"):
        return [s.strip() for s in contents[len("OVERFLOW_FOUND"):].split("|")
                if s.strip()]
    return [f"unexpected report: {contents}"]


def render_html(scale: int = 3, only: list[str] | None = None,
                out_name: str = "figure2_html.png",
                strict: bool = True) -> str:
    sys.path.insert(0, HERE)
    from _panels import render_all  # noqa: E402

    # Match this to <body width/height> in figure2.html.
    CANVAS_PX = (780, 820)

    print("rendering panels…")
    render_all(only=only)

    html_path = os.path.join(HERE, "figure2.html")
    chrome = find_chrome()

    print("checking layout overflow…")
    issues = _check_overflow(chrome, html_path, CANVAS_PX)
    if issues:
        print("  OVERFLOW ISSUES:")
        for i in issues:
            print(f"    - {i}")
        if strict:
            print("  build aborted (rerun with --no-strict to ignore)")
            sys.exit(1)
    else:
        print("  no overflow")

    out_path = os.path.join(HERE, out_name)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        f"--screenshot={out_path}",
        f"--window-size={CANVAS_PX[0]},{CANVAS_PX[1]}",
        f"--force-device-scale-factor={scale}",
        "--default-background-color=ffffff",
        f"file://{html_path}",
    ]
    print(f"rasterizing (scale {scale}x) …")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=int, default=3,
                   help="device pixel ratio (3 ≈ 300dpi for a 100dpi CSS layout)")
    p.add_argument("--panels", nargs="*", default=None,
                   help="optional subset of panels to re-render (e.g. a c h)")
    p.add_argument("--out", default="figure2_html.png")
    p.add_argument("--no-strict", action="store_true",
                   help="render even if overflow is detected")
    args = p.parse_args()
    render_html(scale=args.scale, only=args.panels, out_name=args.out,
                strict=not args.no_strict)
