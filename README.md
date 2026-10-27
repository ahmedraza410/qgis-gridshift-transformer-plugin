# Grid Shift Transformer (QGIS plugin)

Applies an **explicit PROJ pipeline** (e.g. `hgridshift` / `vgridshift`) to a vector layer in QGIS and checks that the
grid is really used instead of a silent ballpark fallback.

> Status: small sample project (v0.1.0, experimental). Everything described below is covered by the tests in `tests/`.

## Features
- Dialog (Vector menu) and a Processing algorithm (`gridshift:applypipeline`) sharing one core.
- Pre-flight validation: pipeline syntax, grid files present in the PROJ search paths (the searched folders are listed in the error).
- Transformation registered through `QgsCoordinateTransformContext.addCoordinateOperation(..., allowFallback=False)`.
- Control-point check: CSV `src_x,src_y,exp_x,exp_y` -> max / RMS residual.
- JSON report: pipeline, operations, QGIS/PROJ versions, grid paths + SHA-256, residuals.

## Development
```bash
conda activate pyqgis   # any env with QGIS >= 3.28 and pytest
python -m pytest tests
```
Tests generate a tiny synthetic GeoTIFF grid (constant +1" lat / +2" lon), so no large downloads are needed.
Real grids can be obtained from https://cdn.proj.org and must be placed in a PROJ search path.

## Install
Copy the `gridshift_transformer` folder to your QGIS profile `python/plugins` directory and enable it in the Plugin Manager.

## Limits
Vertical (`vgridshift`) support is passed through to PROJ but not yet covered by a test. GML/XSD validation is not part of this plugin.

License: GPL-2.0-or-later.
