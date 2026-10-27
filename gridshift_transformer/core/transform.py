"""Apply a PROJ pipeline to QGIS geometries, making sure the grid is used."""
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsCoordinateTransformContext, QgsPointXY, QgsProject,
)

from .pipeline import PipelineError, validate_pipeline


def build_transform(src_crs, dst_crs, pipeline, project=None):
    """Return a QgsCoordinateTransform bound to the explicit pipeline.

    allowFallback is False, so QGIS fails instead of silently using a
    ballpark operation when the grid cannot be loaded.
    """
    _, problems = validate_pipeline(pipeline)
    if problems:
        raise PipelineError("\n".join(problems))
    context = QgsCoordinateTransformContext()
    if not context.addCoordinateOperation(src_crs, dst_crs, pipeline, False):
        raise PipelineError("QGIS rejected the pipeline for this CRS pair.")
    transform = QgsCoordinateTransform(src_crs, dst_crs, context)
    if not transform.isValid():
        raise PipelineError("Transform is not valid for this CRS pair.")
    return transform


def transform_point(transform, x, y):
    p = transform.transform(QgsPointXY(x, y))
    return p.x(), p.y()


def grid_is_applied(src_crs, dst_crs, pipeline, x, y, tol=1e-12):
    """True if the explicit pipeline gives a different result than QGIS's default."""
    explicit = transform_point(build_transform(src_crs, dst_crs, pipeline), x, y)
    default = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())
    base = default.transform(QgsPointXY(x, y))
    return abs(explicit[0] - base.x()) > tol or abs(explicit[1] - base.y()) > tol
