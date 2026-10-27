"""Transformation report (JSON) documenting what was applied."""
import hashlib
import json
import os
from datetime import datetime, timezone

from .pipeline import find_grid, parse_pipeline


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_report(pipeline, src_crs, dst_crs, residual=None):
    from qgis.core import Qgis, QgsProjUtils
    info = parse_pipeline(pipeline)
    grids = []
    for name in info.grids:
        path = find_grid(name)
        grids.append({"name": name, "path": path,
                      "sha256": _sha256(path) if path and os.path.isfile(path) else None})
    report = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "qgis": Qgis.version(),
        "proj": QgsProjUtils.projVersion() if hasattr(QgsProjUtils, "projVersion") else None,
        "source_crs": src_crs.authid(), "target_crs": dst_crs.authid(),
        "pipeline": info.text, "operations": info.operations, "grids": grids,
    }
    if residual is not None:
        report["control_points"] = {"count": residual.count, "max_m": residual.max_m,
                                    "rms_m": residual.rms_m}
    return report


def write_report(report, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
