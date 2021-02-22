"""Axis-aligned bounding box abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod

from panda3d.core import LVector2d, LVector3d


class BoundingBox(ABC):
    """Generic axis-aligned bounding box."""

    def __init__(self, point_min, point_max):
        self.point_min = point_min
        self.point_max = point_max

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(point_min={self.point_min}, point_max={self.point_max})"
        )

    @property
    def center(self):
        return (self.point_max + self.point_min) / 2

    @property
    def size(self):
        return self.point_max - self.point_min

    @staticmethod
    @abstractmethod
    def from_origin(point_max) -> BoundingBox:
        pass

    @staticmethod
    @abstractmethod
    def null_object() -> BoundingBox:
        pass


class BoundingBox3D(BoundingBox):
    """3D axis-aligned bounding box."""

    def __init__(self, point_min: LVector3d, point_max: LVector3d):
        super().__init__(point_min=point_min, point_max=point_max)

    @staticmethod
    def from_origin(point_max: LVector3d) -> BoundingBox3D:
        return BoundingBox3D(point_min=LVector3d(0, 0, 0), point_max=point_max)

    @property
    def size(self) -> LVector3d:
        return self.point_max - self.point_min

    @staticmethod
    def null_object() -> BoundingBox3D:
        return BoundingBox3D(point_min=LVector3d(0, 0, 0), point_max=LVector3d(0, 0, 0))


class BoundingBox2D(BoundingBox):
    """2D axis-aligned bounding box."""

    def __init__(self, point_min: LVector2d, point_max: LVector2d):
        super().__init__(point_min=point_min, point_max=point_max)

    @staticmethod
    def from_origin(point_max: LVector2d) -> BoundingBox2D:
        return BoundingBox2D(point_min=LVector2d(0, 0), point_max=point_max)

    @property
    def size(self) -> LVector2d:
        return self.point_max - self.point_min

    @staticmethod
    def null_object() -> BoundingBox2D:
        return BoundingBox2D(point_min=LVector2d(0, 0), point_max=LVector2d(0, 0))
