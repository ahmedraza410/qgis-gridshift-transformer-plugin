import pytest
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem

from gridshift_transformer.core.controlpoints import residuals, load_csv
from gridshift_transformer.core.report import build_report
from gridshift_transformer.core.transform import build_transform
from gridshift_transformer.processing.provider import GridShiftProvider
from conftest import DLAT_ARCSEC, DLON_ARCSEC

SRC = QgsCoordinateReferenceSystem("EPSG:4326")
DST = QgsCoordinateReferenceSystem("EPSG:4258")



def test_residuals_zero_for_correct_expected(pipeline_text, tmp_path):
    t = build_transform(SRC, DST, pipeline_text)
    pts = [(19.0, 52.0, 19.0 + DLON_ARCSEC / 3600, 52.0 + DLAT_ARCSEC / 3600)]
    r = residuals(t, pts)
    assert r.count == 1 and r.max_m < 1e-6


def test_residuals_detect_wrong_expected(pipeline_text):
    t = build_transform(SRC, DST, pipeline_text)
    r = residuals(t, [(19.0, 52.0, 19.0, 52.0)], units_to_m=111_000)
    assert r.max_m > 50  # ~3.6" is >100 m: no shift applied would be caught


def test_load_csv(tmp_path):
    f = tmp_path / "cp.csv"
    f.write_text("src_x,src_y,exp_x,exp_y\n1,2,3,4\n")
    assert load_csv(f) == [(1.0, 2.0, 3.0, 4.0)]


def test_report_has_grid_hash(pipeline_text):
    rep = build_report(pipeline_text, SRC, DST)
    assert rep["grids"][0]["sha256"] and rep["operations"][1] == "hgridshift"


def test_processing_algorithm(pipeline_text):
    import processing
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer
    from processing.core.Processing import Processing
    Processing.initialize()
    prov = GridShiftProvider()
    QgsApplication.processingRegistry().addProvider(prov)
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "pts", "memory")
    f = QgsFeature(); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(19, 52)))
    layer.dataProvider().addFeatures([f])
    out = processing.run("gridshift:applypipeline", {
        "INPUT": layer, "PIPELINE": pipeline_text, "TARGET_CRS": DST, "OUTPUT": "memory:"})
    p = next(out["OUTPUT"].getFeatures()).geometry().asPoint()
    assert p.x() == pytest.approx(19 + DLON_ARCSEC / 3600, abs=1e-9)


