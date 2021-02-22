"""Abstraction of layer in point cloud."""
from typing import List, Optional

from panda3d.core import Point2D

from layerview.visualization.point_cloud.boundaries import BoundingBox2D
from layerview.visualization.point_cloud.path import Path


class Layer:
    """Represents a point cloud layer."""

    def __init__(self):
        self.paths: List[Path] = []

        self.temperature_min: Optional[float] = None
        self.temperature_max: Optional[float] = None
        self.temperature_avg: Optional[float] = None
        self.feedrate_min: Optional[float] = None
        self.feedrate_max: Optional[float] = None
        self.feedrate_avg: Optional[float] = None

    @property
    def boundaries(self) -> BoundingBox2D:
        """Return this layer's axis-aligned bounding box."""
        if not self.paths:
            raise ValueError("Boundaries calculation requires at least one path.")

        vertices = [vertex for path in self.paths for vertex in path]

        # Assuming all added vertices have the same z value.
        point_min = Point2D(
            x=min([v.x for v in vertices]),
            y=min([v.y for v in vertices]),
        )
        point_max = Point2D(
            x=max([v.x for v in vertices]),
            y=max([v.y for v in vertices]),
        )

        return BoundingBox2D(point_min=point_min, point_max=point_max)
