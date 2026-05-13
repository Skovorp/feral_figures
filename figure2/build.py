"""Build figure 2 via the HTML+CSS pipeline.

Steps:
  1. Render each panel as an SVG (figure2/panels/).
  2. Use Chrome --dump-dom to detect overflow (fails the build if any).
  3. Rasterize figure2.html → figure2_html.png at scale×96 DPI.

Shared helpers live in `figures/_render.py`.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from _render import check_html_overflow, rasterize_html  # noqa: E402

# Must match <body width/height> in figure2.html
CANVAS_PX = (780, 820)


def render_html(scale: int = 3, only: list[str] | None = None,
                out_name: str = "figure2_html.png",
                strict: bool = True) -> str:
    from _panels import render_all  # noqa: E402

    print("rendering panels…")
    render_all(only=only)

    html_path = os.path.join(HERE, "figure2.html")

    print("checking layout overflow…")
    issues = check_html_overflow(html_path, CANVAS_PX)
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
    print(f"rasterizing (scale {scale}x) …")
    rasterize_html(html_path, CANVAS_PX, out_path, scale=scale)
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
