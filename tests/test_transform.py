import pytest
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem

from gridshift_transformer.core.pipeline import PipelineError
from gridshift_transformer.core.transform import (
    build_transform, grid_is_applied, transform_point,
)
from conftest import DLAT_ARCSEC, DLON_ARCSEC

SRC = QgsCoordinateReferenceSystem("EPSG:4326")
DST = QgsCoordinateReferenceSystem("EPSG:4258")



def test_grid_shift_matches_known_offset(pipeline_text):
    t = build_transform(SRC, DST, pipeline_text)
    lon, lat = transform_point(t, 19.0, 52.0)
    assert lon - 19.0 == pytest.approx(DLON_ARCSEC / 3600, abs=1e-9)
    assert lat - 52.0 == pytest.approx(DLAT_ARCSEC / 3600, abs=1e-9)


def test_grid_is_applied_vs_default(pipeline_text):
    assert grid_is_applied(SRC, DST, pipeline_text, 19.0, 52.0)


def test_missing_grid_raises():
    bad = "+proj=pipeline +step +proj=hgridshift +grids=missing_grid.tif"
    with pytest.raises(PipelineError):
        build_transform(SRC, DST, bad)

