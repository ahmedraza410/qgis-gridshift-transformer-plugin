# Grid Shift Transformer (QGIS plugin)

Applies an **explicit PROJ pipeline** (e.g. `hgridshift` / `vgridshift`) to a vector layer in QGIS and checks that the
grid is really used instead of a silent ballpark fallback.

> Status: small sample project (v0.1.0, experimental). Everything described below is covered by the tests in `tests/`,
> except the dialog, which was smoke-tested headless and manually in QGIS.

## Features
- Dialog (Vector menu) and a Processing algorithm (`gridshift:applypipeline`) sharing one core.
- Pre-flight validation: pipeline syntax, grid files present in the PROJ search paths (the searched folders are listed in the error).
- Transformation registered through `QgsCoordinateTransformContext.addCoordinateOperation(..., allowFallback=False)`.
- Control-point check: CSV `src_x,src_y,exp_x,exp_y` -> max / RMS residual.
- JSON report: pipeline, operations, QGIS/PROJ versions, grid paths + SHA-256, residuals.

## Requirements
- QGIS 3.28 or newer (developed against 3.30.2 and 3.42.1)
- For running the tests: a Python environment with PyQGIS, GDAL and `pytest`
  (for example a conda env: `conda create -n pyqgis -c conda-forge qgis pytest`)

## Run the tests
Windows, from the project folder (the one containing `gridshift_transformer/` and `tests/`):

```bash
conda activate pyqgis
python -m pytest -q tests
```

Expected: `13 passed`. A GDAL `FutureWarning` about exceptions is harmless.

The tests generate a tiny synthetic GeoTIFF grid (constant +1" lat / +2" lon), so no downloads are needed.

## Install into QGIS
Copy the `gridshift_transformer` folder (not the outer project folder) into your QGIS profile:

```bash
xcopy /E /I /Y gridshift_transformer "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\gridshift_transformer"
```

Linux / macOS equivalents:

```bash
cp -r gridshift_transformer ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/              # Linux
cp -r gridshift_transformer ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/  # macOS
```

Then start QGIS and open **Plugins > Manage and Install Plugins > Installed**, tick **Grid Shift Transformer**
(it is marked experimental, so enable experimental plugins in the Settings tab if it is not listed).
After editing the code, copy the folder again and restart QGIS, or use the *Plugin Reloader* plugin.

## Try it with the sample grid
1. Create a folder and the synthetic test grid (run from the project folder, in the `pyqgis` env):

```bash
mkdir C:\temp
python -c "import sys; sys.path.insert(0,'tests'); from conftest import make_shift_grid; print(make_shift_grid(r'C:\temp\synthetic_shift.tif'))"
```

2. In QGIS add a point layer in EPSG:4326 with a point inside lon 14-24, lat 49-55 (for example 19, 52).
3. Open **Vector > Grid Shift Transformer...**, choose the layer, set the target CRS to `EPSG:4258`, and paste:

```
+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=hgridshift +grids=C:/temp/synthetic_shift.tif +step +proj=unitconvert +xy_in=rad +xy_out=deg
```

4. Click **Validate** (operations and grids are listed, no problem reported), then **Run**.
   A new layer `<name> (grid shift)` is added. The point should move to about `19.000556, 52.000278` (+2" lon, +1" lat).
5. Failure check: change the grid name to one that does not exist and click **Validate**. The error lists the folders searched.

### Control points (optional)
Create a CSV with this header and select it in the dialog before clicking Validate:

```
src_x,src_y,exp_x,exp_y
19,52,19.000556,52.000278
```

The dialog shows the number of points and the max / RMS residual (in target CRS units).

### Report (optional)
Choose a `.json` path in the *Report* field before clicking Run to write the transformation report.

## Use from the Processing Toolbox or Python console
Toolbox: **Grid Shift Transformer > Apply PROJ pipeline (grid shift)**.

From the QGIS Python console:

```python
import processing
processing.run("gridshift:applypipeline", {
    "INPUT": "my_layer_name",
    "PIPELINE": "+proj=pipeline +step ...",
    "TARGET_CRS": "EPSG:4258",
    "OUTPUT": "memory:",
})
```

## Real grids
Real grids can be downloaded from https://cdn.proj.org and must be placed in a PROJ search path
(the dialog error message lists the folders searched), or referenced in the pipeline by absolute path.
Check the licence of each grid before redistributing it. Grids are not stored in this repository.

## Project layout
```
gridshift_transformer/   the plugin (core/ has all GUI-free logic, gui/ the dialog, processing/ the algorithm)
tests/                   pytest suite (needs PyQGIS)
.github/workflows/       CI (QGIS docker image)
```

## Limits
Vertical (`vgridshift`) support is passed through to PROJ but not yet covered by a test. GML/XSD validation is not part of this plugin.

## License
GPL-2.0-or-later. See [LICENSE](LICENSE).
