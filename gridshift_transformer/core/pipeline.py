"""Parsing and validation of PROJ pipeline strings. No GUI code here."""
import os
import re
from dataclasses import dataclass, field

_GRID_RE = re.compile(r"\+(?:grids|file)=(\S+)")
_STEP_RE = re.compile(r"\+proj=(\w+)")


class PipelineError(ValueError):
    pass


@dataclass
class PipelineInfo:
    text: str
    operations: list = field(default_factory=list)
    grids: list = field(default_factory=list)


def parse_pipeline(text):
    """Return the operations and grid names used by a pipeline string."""
    text = " ".join((text or "").split())
    if not text.startswith("+proj=pipeline"):
        raise PipelineError("Pipeline must start with '+proj=pipeline'.")
    ops = _STEP_RE.findall(text)[1:]
    if not ops:
        raise PipelineError("Pipeline has no steps.")
    grids = []
    for value in _GRID_RE.findall(text):
        grids.extend(g.lstrip("@") for g in value.split(","))
    return PipelineInfo(text=text, operations=ops, grids=grids)


def search_paths():
    """Directories PROJ searches for grids (QGIS-reported, else PROJ_DATA)."""
    try:
        from qgis.core import QgsProjUtils
        paths = list(QgsProjUtils.searchPaths())
    except Exception:
        paths = []
    for var in ("PROJ_DATA", "PROJ_LIB"):
        paths.extend(p for p in os.environ.get(var, "").split(os.pathsep) if p)
    return list(dict.fromkeys(paths))


def find_grid(name, paths=None):
    """Return the full path of a grid, or None if PROJ would not find it."""
    if os.path.isabs(name) and os.path.isfile(name):
        return name
    for folder in paths if paths is not None else search_paths():
        candidate = os.path.join(folder, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def validate_pipeline(text, paths=None):
    """Parse the pipeline and check all grids exist. Returns (info, problems)."""
    info = parse_pipeline(text)
    searched = paths if paths is not None else search_paths()
    problems = []
    for grid in info.grids:
        if find_grid(grid, searched) is None:
            problems.append(
                f"Grid '{grid}' not found. Searched: {', '.join(searched) or '(no paths)'}. "
                "Copy it into one of these folders (for example from https://cdn.proj.org)."
            )
    return info, problems
