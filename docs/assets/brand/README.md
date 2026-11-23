# Brand assets

| File | Use |
|---|---|
| `endo-twin-banner.png` | README header (1600x500). The mark is embedded on the left, so the banner stands alone |
| `endo-twin-banner.svg` | editable source for the banner |
| `endo-twin-logo.png` | the mark on its own (1024x1024), for an avatar, favicon or slide corner |
| `endo-twin-logo.svg` | editable source for the mark |

The README links the PNG, not the SVG: both SVGs set
`font-family="DejaVu Sans, sans-serif"`, which is absent on many machines, so
their text would reflow. The PNGs have it rasterised.

Neither SVG contains scripts, event handlers or external references; the only
`href`s are internal fragment references to their own gradient and pattern
definitions.
