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

## Quickstart (first-time setup)

```bash
# 1. Create + activate env (see "Stack" below for what gets installed)
conda create -n feral_figures python=3.13 -y
conda activate feral_figures
pip install matplotlib pillow numpy scikit-learn

# 2. Confirm headless Chrome is on the macOS default path
ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Linux users: install chromium or google-chrome on PATH; _render.find_chrome
# will pick whichever it finds first (see CHROME_CANDIDATES in _render.py).

# 3. From the repo root, build any figure
cd figures
python3 figure4/build.py
```

Output lands at `figureN/figureN_html.png`. Open it side-by-side with
`figureN/ORIG_figure_N.png` to compare.

## Build commands

Always run from the `figures/` directory (paths are relative to it).
`build.py` does three things in order: render every panel's SVG → run
Chrome to layout-check the HTML → run Chrome again to rasterize to PNG.

```bash
# Full rebuild of one figure
python3 figureN/build.py

# Just rebuild specific panels (faster — HTML reuses other SVGs)
python3 figureN/build.py --panels c h

# Higher DPI for print (default 3 ≈ 288 DPI)
python3 figureN/build.py --scale 4

# Custom output filename
python3 figureN/build.py --out figureN_draft.png

# Allow build to finish even when the HTML overflow check fails (debug)
python3 figureN/build.py --no-strict
```

Render just one panel's SVG without the Chrome composite (useful for
isolating layout issues):

```bash
python3 figureN/_panels.py d        # writes figureN/panels/d.svg only
```

## Per-figure summary

| figure | canvas (CSS px) | required data files | notes |
|---|---|---|---|
| `figure2` | `780 × 820`  | `data/calms.json` | CalMS21 ethogram + mAP bars |
| `figure4` | `830 × 1140` | `data/zebra.json`, `data/monkeys.json` | zebra + monkey behavior panels |
| `figure5` | `790 × 660`  | `data/{collective_ants,ants,calms,zebra,monkeys,worms,mabe}.json` | cross-species generalization |

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
- Every `_panels.py::_save_svg` calls `_render.save_svg(tight=False)`.
  We rely on `constrained_layout`'s auto-padding rather than
  `bbox_inches='tight'`. The two **fight each other** — tight crops
  away the padding constrained_layout just added — so we pick one and
  stick with it. See the `matplotlib-tight-bbox-vs-constrained-layout`
  skill in the vault for the full retro.
- HTML `.panel img` uses `object-fit: contain; object-position:
  center;` so the SVG keeps its aspect ratio when scaled into the CSS
  slot. Whitespace > distortion. The SVG dimensions in `_panels.py
  SIZES` must match the CSS slot's `width`/`height` in `figureN.html`
  to avoid letterboxing.

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
  - Figure 4 panel d: `ylim=(-1300, 20000)`
- The top of `ylim` must run **above the data max**, not equal to it.
  If `ylim_top == data_max`, the top whisker caps and topmost scatter
  dots sit flush against the top spine and read as cropped — even
  though no tick label is being clipped. The fix is a data-side
  ylim bump (e.g. data max ≈ 18000 → `ylim_top = 20000`), not a
  figure-padding change. Figure 4 panel d was bitten by this in
  2026-05; see `$FERAL_SHARED_DOCS/raw/learnings/2026-05-13-panel-d-data-flush-against-ylim-top.md`.
- Pick `ylim_top` ≈ next-tick-after-data-max (round data max up to a
  tick boundary, then add one tick). Keep the highest LABELED tick at
  a round number (`17500`) — that's still the topmost tick the reader
  sees; the extra space above it is intentional whitespace.

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

### Python deps (all pip-installed above)

| package | min version | used for |
|---|---|---|
| `matplotlib`   | 3.10+ | all panel rendering; `layout="constrained"` on `plt.figure` |
| `numpy`        | any   | data manipulation in `figureN.py` |
| `Pillow` (PIL) | any   | `_extract_assets.py` photo crops, circular thumbnail masks |
| `scikit-learn` | any   | `sklearn.metrics.average_precision_score` (figure 4 panel h, figure 2 mAP) |

Standard library: `json`, `re`, `os`, `subprocess`, `shutil`,
`argparse`, `dataclasses` — no extra installs.

### Fonts (Arial)

`_style.apply_rcparams` sets `font.family = "Arial"`. macOS ships with
Arial in `/Library/Fonts`. On Linux, install it explicitly or
matplotlib falls back to DejaVu Sans (will break visual parity with
the published figure):

```bash
sudo apt-get install ttf-mscorefonts-installer
# or copy Arial.ttf into ~/.fonts/ and run `fc-cache -fv`
```

### Headless Chrome

`_render.find_chrome` probes `CHROME_CANDIDATES` in order:

- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- macOS (Chromium): `/Applications/Chromium.app/Contents/MacOS/Chromium`
- Linux/`$PATH`: `google-chrome`, `chromium`, `chrome`

Used twice per build: once with `--dump-dom` to read the JS-populated
`#overflow-report`, once with `--screenshot` + `--force-device-scale-factor`
to rasterize the HTML to PNG.

## constrained_layout

Each `_panels.py::_new_fig` calls `plt.figure(layout="constrained")`.
That means:

- Use `fig.subplots()` or `fig.add_gridspec(...)` for axes —
  **NEVER** `fig.add_axes([...])` (constrained_layout doesn't manage
  manually positioned axes, so they get clipped).
- Don't pass `left=`, `right=`, `top=`, `bottom=` to `add_gridspec` —
  constrained_layout sets margins automatically based on the actual
  rendered text bboxes.
- Save with `tight=False` (the default in `save_svg`). Do **not** add
  `bbox_inches='tight'` — see "Aspect / no-squish" above.
- Tune the padding with `fig.get_layout_engine().set(h_pad=…, w_pad=…)`
  in `_new_fig` (inches). Current default: `h_pad=0.15`, `w_pad=0.08`.
