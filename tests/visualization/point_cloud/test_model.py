"""Unit tests for `model` module."""
from layerview.gcode.gcode import Gcode
from layerview.visualization.point_cloud.model import ModelBuilder


class TestModelBuilder:
    """Unit tests for ModelBuilder class."""

    def test_build_model_sanity(self, gcode_valid: Gcode):
        """Test sanity of build_model method.

        Parameters
        ----------
        gcode_valid : Gcode
            Valid and non-empty Gcode instance.
        """
        ModelBuilder.build_model(gcode_valid, nozzle_diam=0.4)
