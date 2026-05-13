# Figure pipeline — project notes

A SVG-per-panel + HTML/CSS composition + headless-Chrome rasterizer for
publication figures. Built to make figures easy for Claude to iterate on:
each panel is a small file you can edit in isolation, the overall layout
is one HTML file with absolute positions, and a programmatic check fails
the build on overflow or text collisions.

This file is the index. Per-figure READMEs live in `figureN/README.md`.

## Layout

```
figures/
├── _style.py             shared rcParams: Arial regular, axis weights, font config
├── _layout_check.py      programmatic checks (overlap, squish, text-collision)
├── _extract_assets.py    crops embedded photos out of the ORIG_figure_N.png
├── data/                 *.json — gt/pred per dataset (calms, zebra, monkeys, …)
├── figure2/              ┐
├── figure4/              ├── one folder per published figure
└── figure5/              ┘
    ├── ORIG_figure_N.png   source figure (flattened to RGB white bg)
    ├── figureN.py          matplotlib panel functions (panel_a … panel_h)
    ├── _panels.py          standalone SVG renderer per panel
    ├── figureN.html        layout — CSS absolute positions + dot/letter overlays
    ├── build.py            orchestrator: renders panels, runs Chrome, checks overflow
    ├── panels/*.svg        generated; one SVG per panel
    ├── assets/*.png        cropped photos from the source figure
    └── figureN_html.png    final rasterized output
```

## Build commands

```bash
# Full rebuild of one figure
python3 figureN/build.py

# Just rebuild specific panels (faster — HTML reuses other SVGs)
python3 figureN/build.py --panels c h

# Higher DPI for print
python3 figureN/build.py --scale 4

# Allow build to finish even when overflow check fails (debug)
python3 figureN/build.py --no-strict
```

## How edits work

| Edit | Where |
|---|---|
| Move a panel | `figureN.html` `#x { left: ...; top: ...; }` |
| Resize a panel | `figureN.html` CSS + matching `SIZES[...]` in `_panels.py` |
| Change a bar value, color, axis range | `figureN.py` `panel_X()` |
| Move a curved arrow (fig 5) | `figureN.html` inline `<svg>` path `d="..."` |
| Reposition an HTML dot/legend | `figureN.html` `<div style="...">` |
| Re-crop a source photo | `_extract_assets.py` boxes, then run it |

`build.py` re-renders only the panels listed in `--panels`. Editing CSS
alone needs no Python — Chrome will pick up the new HTML on the next
rasterize, even if `--panels` is `[]`.

## Conventions / decisions

### Font
- **Arial regular**, everywhere. Enforced by `_style.apply_rcparams`.
- Bold reserved for **panel letters** (a/b/c/…) and the percentages in
  ethogram titles ("Example video 1: accuracy **97.8%**"). Italic only
  where the source figure clearly uses it (binomial species names,
  citation subscripts).

### Panel letters (a, b, c, …) live in HTML
- Drawn as `<div class="letter">x</div>` per panel. Reason: matplotlib
  often places them at negative axes coords (`x=-0.08, y=1.02`), where
  they get clipped by the SVG bbox. The HTML overlay sits at `top: 0;
  left: 2px;` inside each `.panel` and is therefore never clipped.
- `_style.panel_label` is monkey-patched to a no-op in each `_panels.py`
  so the function calls inside `panel_X()` still work but emit nothing.

### Circles / dots live in HTML
- Matplotlib's `patches.Circle` renders as an ellipse whenever the host
  axes has unequal x/y aspect — which is most of the time. CSS
  `border-radius: 50%` is always a true circle and stays crisp at any
  zoom.
- Used for: figure 2's "behavior labels" legend, figure 4's panel-a
  legend dots, figure 5's panel-a "no raiding"/"raiding" headers.
- The matplotlib panel functions accept `show_legend=False` /
  `show_headers=False` to skip drawing the circles; HTML draws them
  instead.

### Arrows (figure 5)
- The two curved arrows from confusion-matrix cells to the petri
  thumbnails are **inline SVG `<path>`** inside `figure5.html`. Edit
  `d="M sx sy Q cx cy ex ey"` to re-route — coords are in body CSS px.
- Tried matplotlib `FancyArrowPatch` first; positioning across axes
  was fragile and needed draw-event handlers that don't work with the
  SVG canvas backend.

### Aspect / no-squish
- `_save_svg` in every `_panels.py` uses `bbox_inches="tight",
  pad_inches=0.02` so matplotlib auto-expands the SVG to include every
  rotated tick label, citation, twin-axis title, etc. — nothing gets
  clipped at the SVG edge by construction.
- HTML `.panel img` uses `object-fit: contain; object-position:
  center;` so the SVG keeps its aspect ratio when scaled into the CSS
  slot. Whitespace > distortion.

### Layout safety
- `_layout_check.check_figure(fig)` runs after every matplotlib panel
  render and reports:
  - `aspect_squish` — embedded `imshow` images stretched > 3 %
  - `axes_overlap` — two `Axes` rectangles intersect (excluding
    twins/colorbars/explicit ignores)
  - `text_intrudes_into_axes` — text from one axis spills into the
    interior of another
  - `text_collision` — any two text artists share > 2 px of bbox
- HTML pages include a `<script>` that walks every `.panel` and the
  `#legend` / `.dot-header` overlays, checks each against the body
  `clientWidth/clientHeight`, and writes the result to a hidden
  `#overflow-report` div. `build.py` runs Chrome with `--dump-dom` and
  parses the report; non-empty issues fail the build (override with
  `--no-strict`).

### Auto-spacing where needed
- Figure 2 panel c (mAP comparison bars with long citations) runs a
  loop that increments bar spacing in 0.15-unit steps until
  `check_text_collisions` reports clean. Saves manually tweaking
  numbers when fonts/citations change.

### Box-plot baselines
- All box plots have `ax.set_ylim(-X, ymax)` with a small negative
  bottom so the `0` tick label sits above the axis line (matches the
  published typography). Examples:
  - Figure 2 panel f: `ylim=(-0.4, 10)`
  - Figure 4 panel d: `ylim=(-700, 17500)`

### Assets are cropped, not generated
- `_extract_assets.py` crops photos out of `ORIG_figure_N.png` (the
  paper figure flattened to white background). Crop boxes were measured
  by pixel-edge detection — see comments inside the file.
- Circular thumbnails (figure 5 panel c) use `crop_circle` which paints
  an alpha mask so the round dish sits on transparent background and
  doesn't pick up surrounding arrow-tip artifacts.

## Workflow tips

- **Iterate on one panel only**: `python3 figureN/build.py --panels c`.
  The rest reuse existing SVGs.
- **Inspect a panel SVG directly**: Chrome can open it
  (`file://.../figureN/panels/c.svg`) — useful when the composite
  rendering hides the issue.
- **Adjust a panel's pixel slot AND the matplotlib size together**:
  `SIZES["c"] = (W, H)` in `_panels.py` and `#c { width: Wpx; height:
  Hpx; }` in `figureN.html`. Mismatched values trigger `object-fit:
  contain` whitespace.
- **Side-by-side compare** the rasterized output with the source:
  `open figureN/figureN_html.png figureN/ORIG_figure_N.png`.

## Git

- Repo: <https://github.com/Skovorp/feral_figures>
- Commit message convention: `iterating to match` (kept short — the diff
  speaks for itself, churn is high).
- `.gitignore` drops `__pycache__/`, `.DS_Store`, IDE dirs.

## Stack

Conda env `feral_figures` — create + activate before any build:

```bash
conda create -n feral_figures python=3.13 -y
conda activate feral_figures
pip install matplotlib pillow numpy scikit-learn
```

- Python 3.13 · **matplotlib 3.10+** (needed for `layout="constrained"`
  on `plt.figure` — auto-pads margins so no tick label, legend, or
  twin-axis label can get clipped at the SVG edge)
- Pillow · numpy · scikit-learn (`average_precision_score` for figure 4
  panel h)
- Headless Chrome at `/Applications/Google Chrome.app/Contents/MacOS/`
  via `--screenshot` + `--force-device-scale-factor=3` (≈ 300 DPI)

## constrained_layout

Each `_panels.py::_new_fig` calls `plt.figure(layout="constrained")`.
That means:

- Use `fig.subplots()` or `fig.add_gridspec(...)` for axes —
  **NEVER** `fig.add_axes([...])` (constrained_layout doesn't manage
  manually positioned axes, so they get clipped).
- Don't pass `left=`, `right=`, `top=`, `bottom=` to `add_gridspec` —
  constrained_layout sets margins automatically based on the actual
  rendered text bboxes.
- `bbox_inches='tight'` (in `save_svg`) is still used; the two cooperate
  fine and the result is "no crops, no overlaps, no manual fiddling."
