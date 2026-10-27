"""Control-point residuals: CSV columns src_x, src_y, exp_x, exp_y."""
import csv
import math
from dataclasses import dataclass


@dataclass
class Residuals:
    count: int
    max_m: float
    rms_m: float
    per_point: list


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [tuple(float(row[k]) for k in ("src_x", "src_y", "exp_x", "exp_y"))
                for row in csv.DictReader(fh)]


def residuals(transform, points, units_to_m=1.0):
    """Compare transform(src) to expected coordinates; units_to_m converts CRS units to metres."""
    from .transform import transform_point
    dists = []
    for sx, sy, ex, ey in points:
        x, y = transform_point(transform, sx, sy)
        dists.append(math.hypot(x - ex, y - ey) * units_to_m)
    if not dists:
        return Residuals(0, 0.0, 0.0, [])
    rms = math.sqrt(sum(d * d for d in dists) / len(dists))
    return Residuals(len(dists), max(dists), rms, dists)
