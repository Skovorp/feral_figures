"""Build figure 4 via the HTML+CSS pipeline.

See figure2/build.py for the equivalent for figure 2.
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
    m = re.search(
        r'<div[^>]*id="overflow-report"[^>]*>(.*?)</div>',
        html, re.DOTALL,
    )
    if not m:
        return ["overflow-report div not found in dumped DOM"]
    contents = m.group(1).strip()
    if contents in ("OVERFLOW_OK", ""):
        return []
    if contents.startswith("OVERFLOW_FOUND"):
        return [s.strip() for s in contents[len("OVERFLOW_FOUND"):].split("|")
                if s.strip()]
    return [f"unexpected report: {contents}"]


def render_html(scale: int = 3, only: list[str] | None = None,
                out_name: str = "figure4_html.png",
                strict: bool = True) -> str:
    sys.path.insert(0, HERE)
    from _panels import render_all  # noqa: E402

    CANVAS_PX = (830, 1140)

    print("rendering panels…")
    render_all(only=only)

    html_path = os.path.join(HERE, "figure4.html")
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
    p.add_argument("--scale", type=int, default=3)
    p.add_argument("--panels", nargs="*", default=None)
    p.add_argument("--out", default="figure4_html.png")
    p.add_argument("--no-strict", action="store_true")
    args = p.parse_args()
    render_html(scale=args.scale, only=args.panels, out_name=args.out,
                strict=not args.no_strict)
