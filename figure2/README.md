# Figure 2 — HTML+CSS composition pipeline

Each panel is an independent SVG; the final figure is composed in
`figure2.html` with CSS absolute positioning; Chrome headless rasterizes
the HTML to a PNG.

## Files

| file | purpose |
|---|---|
| `figure2.py` | matplotlib panel functions (`panel_a` … `panel_h`) |
| `_panels.py` | per-panel SVG renderers (sizes, axes margins) |
| `figure2.html` | layout — CSS coordinates for each panel |
| `build.py` | orchestrator: builds SVGs, invokes Chrome |
| `panels/*.svg` | generated; one per panel |
| `figure2_html.png` | final composite output |
| `ORIG_figure_2.png` | source figure to match |
| `figure2_remade.png` | older matplotlib-gridspec output (kept for diff) |

## Typical edits

| change | edit |
|---|---|
| Move panel C right by 20 px | `figure2.html`: `#c { left: 20px; ... }` |
| Make panel H taller | `figure2.html`: `#h { height: 260px; ... }` AND `_panels.py`: `SIZES["h"] = (200, 260)` |
| Add another bar to panel C | `figure2.py`: edit `panel_c()` data list |
| Change a tick color | `figure2.py`: relevant `panel_*` function |
| Re-render after data change | `python3 build.py` (full) or `python3 build.py --panels c` (just C) |

## Render

```bash
# full rebuild
python3 build.py

# faster: only rebuild specific panels (HTML re-composes from existing SVGs)
python3 build.py --panels c h

# higher resolution
python3 build.py --scale 4
```

Output: `figure2_html.png`. At `--scale 3` the PNG is ~2340×2460 px (≈300 DPI for a 7.8×8.2 in figure).
