from pathlib import Path

import pytest

from layerview.gcode.gcode import Gcode
from layerview.gcode.parser import GcodeParser
from layerview.visualization.point_cloud.model import Model as ToolpathModel
from layerview.visualization.point_cloud.model import (
    ModelBuilder as ToolpathModelFactory,
)

_PATH_GCODE_CUBE = (Path(__file__).parent / "assets/gcode/cube_10mm.gcode").absolute()


@pytest.fixture
def nozzle_diam() -> float:
    return 0.4


@pytest.fixture
def path_gcode_valid() -> Path:
    return _PATH_GCODE_CUBE


@pytest.fixture
def gcode_valid(path_gcode_valid) -> Gcode:
    return GcodeParser.parse(path_gcode_valid, skip_unknown=True)


@pytest.fixture
def point_cloud_model_valid(gcode_valid, nozzle_diam: float) -> ToolpathModel:
    return ToolpathModelFactory.build_model(gcode=gcode_valid, nozzle_diam=nozzle_diam)
