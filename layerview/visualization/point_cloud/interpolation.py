"""Toolpath interpolation tools."""

import math
from abc import ABC, abstractmethod
from typing import List

import numpy as np
from panda3d.core import Point2D

from layerview.visualization.linalg import angle_signed


class Interpolator(ABC):
    """Generic toolpath interpolator."""

    @classmethod
    @abstractmethod
    def interpolate(cls, src: Point2D, dst: Point2D, *args, **kwargs) -> List[Point2D]:
        """Interpolate move from `src` to `dst`.

        Parameters
        ----------
        src : Point2D
            Source point.
        dst : Point2D
            Destination point.
        *args
        **kwargs

        Returns
        -------
        List[Point2D]
            List of intermediate, interpolated points, between source and destination.
        """
        pass


class CircularArcInterpolator(Interpolator):
    """Circular arc move interpolator."""

    _MAX_ERROR_DEFAULT: float = 0.1

    # noinspection PyMethodOverriding
    @classmethod
    def interpolate(
        cls,
        src: Point2D,
        dst: Point2D,
        pivot: Point2D,
        is_clockwise: bool,
        max_err: float = _MAX_ERROR_DEFAULT,
        *args,
        **kwargs,
    ) -> List[Point2D]:
        """Interpolate circular arc from `src` to `dst`.

        Expects both `src` and `dst` to be equidistant from `pivot`.

        Parameters
        ----------
        src : Point2D
            Source point.
        dst : Point2D
            Destination point.
        pivot : Point2D
            Pivot point. Arc's circle center point.
        is_clockwise : bool
            Defines whether the arc is clockwise or counterclockwise.
        max_err : float
            Max allowed distance between arc chord and radius.

        Returns
        -------
        List[Point2D]
            Interpolated points. Includes source and destination points.

        Raises
        ------
        ValueError
            If src and dst points are not equidistant from pivot.
        """
        radius = (src - pivot).length

        # Validate src and dst points' distance from pivot.
        if math.isclose(a=radius, b=(dst - pivot).length(), rel_tol=0.01):
            raise ValueError(
                f"Points (src={src}, dst={dst}) are not equidistant "
                f"from pivot={pivot}."
            )

        angle_step = cls._get_angle_step(radius, max_err, is_clockwise)
        angle_total = cls._get_angle_abs(src, dst, pivot, is_clockwise)
        step_num = math.ceil(angle_total / angle_step)
        # Calc angles
        angles = np.linspace(
            start=angle_step, stop=angle_total, num=step_num, endpoint=False
        )

        # Calc rotation matrix for each angle
        rot_cos, rot_sin = np.cos(angles), np.sin(angles)
        rot_mat = np.array(((rot_cos, -rot_sin), (rot_sin, rot_cos)))

        # Calc intermediate points
        src_unbound = np.array([*(src - pivot)])
        pivot_np = np.array([*pivot])
        points_inter = (src_unbound @ rot_mat.T) + pivot_np

        points_all: List[Point2D] = [
            src,
            *[Point2D(*p) for p in points_inter],
            dst,
        ]

        return points_all

    @classmethod
    def _get_angle_abs(
        cls, src: Point2D, dst: Point2D, pivot: Point2D, is_clockwise: bool
    ):
        """Return absolute rotation angle from `src` to `dst`, around `pivot`.

        Takes rotation direction (clockwise, counterclockwise) into account.

        Parameters
        ----------
        src : Point2D
        dst: Point2D
        pivot : Point2D
        is_clockwise : bool

        Returns
        -------
        angle_abs : float
            Rotation angle from source to destination, around pivot
            in the specified direction (clockwise, counterclockwise).
        """
        vec_pivot_to_src = src - pivot
        vec_pivot_to_dst = dst - pivot

        angle_abs = angle_signed(vec_pivot_to_src, vec_pivot_to_dst)
        if not is_clockwise:  # Counterclockwise
            angle_abs += math.pi * 2

        return angle_abs

    @classmethod
    def _get_angle_step(
        cls, radius: float, max_error: float, is_clockwise: bool
    ) -> float:
        """Return rotation angle step, based on specified constraints.

        Rotation by the calculated angle step results in at most `max_error`
        absolute interpolation error.

        Parameters
        ----------
        radius : float
            Arc radius.
        max_error : float
            Maximum allowed absolute error.
        is_clockwise : bool
            If True, the rotation is treated as clockwise.
            Otherwise, the rotation is treated as counterclockwise.

        Returns
        -------
        float
            Angle step.
        """
        step_abs = 2 * math.acos(1 - (max_error / radius))
        if is_clockwise:
            return -step_abs
        return step_abs

    @classmethod
    def _get_radius(cls, point_on_arc: Point2D, pivot: Point2D) -> float:
        """Calc arc radius, based on point on arc and pivot.

        Parameters
        ----------
        point_on_arc : Point2D
            Point on arc.
        pivot : Point2D
            Rotation pivot, aka arc center.

        Returns
        -------
        float
            Radius of the arc.
        """
        return (pivot - point_on_arc).length()
