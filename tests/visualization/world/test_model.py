"""Unit tests for `model` module."""
from layerview.visualization.nodes.model import ModelManagerBuilder
from layerview.visualization.point_cloud.model import Model as PointCloudModel


class TestModelManagerBuilder:
    """Unit tests for ModelManagerBuilder."""

    def test_build_manager_sanity(self, point_cloud_model_valid: PointCloudModel):
        """Test sanity of build_manager method.

        Parameters
        ----------
        point_cloud_model_valid : PointCloudModel
            A valid PointCloudModel instance.
        """
        ModelManagerBuilder.build_manager(
            model=point_cloud_model_valid, name="test_model"
        )
