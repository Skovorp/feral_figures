"""Build figure 4 via the HTML+CSS pipeline. See figure2/build.py."""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from _render import check_html_overflow, rasterize_html  # noqa: E402

CANVAS_PX = (830, 1140)


def render_html(scale: int = 3, only: list[str] | None = None,
                out_name: str = "figure4_html.png",
                strict: bool = True) -> str:
    from _panels import render_all  # noqa: E402

    print("rendering panels…")
    render_all(only=only)

    html_path = os.path.join(HERE, "figure4.html")

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
    p.add_argument("--scale", type=int, default=3)
    p.add_argument("--panels", nargs="*", default=None)
    p.add_argument("--out", default="figure4_html.png")
    p.add_argument("--no-strict", action="store_true")
    args = p.parse_args()
    render_html(scale=args.scale, only=args.panels, out_name=args.out,
                strict=not args.no_strict)
