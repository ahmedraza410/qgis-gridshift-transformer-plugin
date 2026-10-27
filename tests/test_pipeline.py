import pytest

from gridshift_transformer.core.pipeline import (
    PipelineError, find_grid, parse_pipeline, validate_pipeline,
)


def test_parse_extracts_ops_and_grids(pipeline_text):
    info = parse_pipeline(pipeline_text)
    assert info.operations == ["unitconvert", "hgridshift", "unitconvert"]
    assert info.grids[0].endswith("synthetic_shift.tif")


def test_parse_rejects_non_pipeline():
    with pytest.raises(PipelineError):
        parse_pipeline("+proj=utm +zone=33")


def test_validate_ok(pipeline_text):
    _, problems = validate_pipeline(pipeline_text)
    assert problems == []


def test_validate_reports_missing_grid(tmp_path):
    text = "+proj=pipeline +step +proj=hgridshift +grids=nope.tif"
    _, problems = validate_pipeline(text, paths=[str(tmp_path)])
    assert len(problems) == 1 and "nope.tif" in problems[0]


def test_find_grid_in_search_path(shift_grid):
    import os
    folder, name = os.path.split(shift_grid)
    assert find_grid(name, [folder]) == shift_grid
