"""Shared SVG rendering + Chrome helpers for the figure pipelines.

Every per-figure `_panels.py` calls `save_svg` so the no-crop / no-clip
contract is identical across figure 2, 4, and 5. Every per-figure
`build.py` calls `find_chrome`, `check_html_overflow`, and
`rasterize_html` so the Chrome orchestration is consistent.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from matplotlib.figure import Figure


CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]


def find_chrome() -> str:
    """Return the path to a usable Chrome/Chromium binary, or raise."""
    for path in CHROME_CANDIDATES:
        if path and os.path.exists(path):
            return path
    raise RuntimeError("could not find Chrome/Chromium")


def check_html_overflow(html_path: str,
                        canvas_px: tuple[int, int]) -> list[str]:
    """Run Chrome with --dump-dom, parse <div id='overflow-report'>.

    Returns a list of human-readable issue strings. Empty list = clean.
    Requires the HTML to include a JS-populated `#overflow-report` div
    (see any figureN.html).
    """
    chrome = find_chrome()
    cmd = [
        chrome,
        "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={canvas_px[0]},{canvas_px[1]}",
        "--virtual-time-budget=2000",
        "--dump-dom",
        f"file://{html_path}",
    ]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    m = re.search(
        r'<div[^>]*id="overflow-report"[^>]*>(.*?)</div>',
        res.stdout, re.DOTALL,
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


def rasterize_html(html_path: str,
                   canvas_px: tuple[int, int],
                   out_path: str,
                   *,
                   scale: int = 3) -> str:
    """Rasterize an HTML page to PNG via headless Chrome.

    --force-device-scale-factor=`scale` upscales the device-pixel
    output so the same CSS layout renders at ~scale×96 DPI.
    """
    chrome = find_chrome()
    cmd = [
        chrome,
        "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars",
        f"--screenshot={out_path}",
        f"--window-size={canvas_px[0]},{canvas_px[1]}",
        f"--force-device-scale-factor={scale}",
        "--default-background-color=ffffff",
        f"file://{html_path}",
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def force_no_crop(fig: Figure) -> None:
    """Make every text/tick artist participate in tight-bbox layout and
    not be clipped by its axes.

    Why: matplotlib's `bbox_inches='tight'` only counts artists with
    `set_in_layout(True)`. Annotations with `annotation_clip=False` and
    rotated tick labels that overhang the axes can be omitted from the
    tight bbox unless we mark them explicitly.
    """
    for ax in fig.axes:
        for t in list(ax.texts):
            try:
                t.set_clip_on(False)
                t.set_in_layout(True)
            except Exception:
                pass
        for axis in (ax.xaxis, ax.yaxis):
            for t in axis.get_majorticklabels() + axis.get_minorticklabels():
                try:
                    t.set_clip_on(False)
                    t.set_in_layout(True)
                except Exception:
                    pass


def save_svg(fig: Figure, out_path: str, *,
             pad_inches: float = 0.10,
             check: bool = True,
             skip_text_collisions: bool = True) -> str:
    """Save `fig` as SVG with NO cropping, optionally running layout checks.

    1. `force_no_crop` ensures every artist counts in the tight bbox.
    2. `bbox_inches='tight'` expands the SVG canvas to fit them.
    3. `pad_inches` adds breathing room for descenders / antialiased edges.
    4. If `check=True`, runs `_layout_check.check_figure` and prints any
       errors to stderr (does NOT raise — many panels intentionally have
       rotated labels that near-touch).

    `skip_text_collisions` defaults to True because rotated-label panels
    (mAP comparisons, per-class bars) routinely have small overlaps that
    are visually OK at print size. Pass False for explicit checking.

    Returns `out_path` (which always wins — the check is informational).
    """
    force_no_crop(fig)
    if check:
        import sys as _sys
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in _sys.path:
            _sys.path.insert(0, _here)
        from _layout_check import check_figure  # noqa: WPS433
        rep = check_figure(fig, raise_on_error=False,
                           print_report=False,
                           skip_text_collisions=skip_text_collisions)
        if not rep.ok:
            # Print issues to stderr so build.py can collect them; never raise.
            import sys
            print(f"  ⚠ layout issues in {os.path.basename(out_path)}:",
                  file=sys.stderr)
            for i in rep.issues:
                print(f"      [{i.severity}] {i.kind}: {i.detail}",
                      file=sys.stderr)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight",
                pad_inches=pad_inches, facecolor="white")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return out_path
