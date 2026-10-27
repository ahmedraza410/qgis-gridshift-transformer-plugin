import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DLAT_ARCSEC = 1.0
DLON_ARCSEC = 2.0


def make_shift_grid(path, dlat=DLAT_ARCSEC, dlon=DLON_ARCSEC):
    """Write a small PROJ GeoTIFF horizontal-offset grid with a constant shift."""
    import numpy as np
    from osgeo import gdal, osr

    ds = gdal.GetDriverByName("GTiff").Create(str(path), 21, 13, 2, gdal.GDT_Float32)
    ds.SetGeoTransform((14.0, 0.5, 0, 55.0, 0, -0.5))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetMetadataItem("TYPE", "HORIZONTAL_OFFSET")
    for i, (desc, val) in enumerate((("latitude_offset", dlat), ("longitude_offset", dlon)), 1):
        band = ds.GetRasterBand(i)
        band.SetDescription(desc)
        band.SetUnitType("arc-second")
        band.WriteArray(np.full((13, 21), val, dtype="float32"))
    ds.FlushCache()
    ds = None
    return str(path)


@pytest.fixture(scope="session")
def shift_grid(tmp_path_factory):
    return make_shift_grid(tmp_path_factory.mktemp("grids") / "synthetic_shift.tif")


@pytest.fixture(scope="session")
def pipeline_text(shift_grid):
    return (
        "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
        f"+step +proj=hgridshift +grids={shift_grid.replace(os.sep, '/')} "
        "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )


@pytest.fixture(scope="session", autouse=True)
def qgis_app():
    from qgis.core import QgsApplication
    app = QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()

