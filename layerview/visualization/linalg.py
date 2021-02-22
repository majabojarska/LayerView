"""Linear algebra utilities."""

from __future__ import annotations

import logging
import math
from decimal import Decimal

from panda3d.core import LVecBase2d


def angle_inner(a: LVecBase2d, b: LVecBase2d):
    """Return angle between vector 1 and vector 2, expressed in radians.

    Does NOT take vector ordering into account.

    Examples
    --------
    Vector order does NOT matter.
    >>> a = LVecBase2d(1, 0)
    >>> b = LVecBase2d(0, 1)
    >>> angle_inner(a, b) == angle_inner(b, a)
    >>> True

    Parameters
    ----------
    a : LVecBase2d
    b : LVecBase2d
    Returns
    -------
    float
        Angle between a and b, expressed in radians.
    """
    dot = a.normalized().dot(b.normalized())
    clamped = max(min(dot, 1.0), -1.0)
    return math.acos(clamped)


def determinant(a: LVecBase2d, b: LVecBase2d):
    return a.x * b.y - a.y * b.x


def angle_signed(a: LVecBase2d, b: LVecBase2d):
    """Return angle between vector a and vector b, expressed in radians.

    Takes angle signedness (positive/negative) into account

    Examples
    --------
    Reversing vector order
    >>> a = LVecBase2d(1, 0)
    >>> b = LVecBase2d(0, 1)
    >>> angle_signed(a, b)
    >>> 1.5707963267948966
    >>> angle_signed(b, a)
    >>> -1.5707963267948966
    >>> angle_signed(a, b) == - angle_signed(b, a)
    >>> True

    Parameters
    ----------
    a : LVecBase2d
    b : LVecBase2d

    Returns
    -------
    float
        Inner angle between a and b, expressed in radians.
    """
    inner_angle = angle_inner(a, b)
    det = determinant(a, b)
    if det < 0:
        return -inner_angle
    return inner_angle


def vec_rotated(vector: LVecBase2d, pivot: LVecBase2d, angle: float):
    """Return vector rotated by angle around pivot.

    Parameters
    ----------
    vector : LVecBase2d
        The point to rotate.
    pivot : LVecBase2d
        The point to rotate about.
    angle : float
        Rotation angle, expressed in radians.

    Returns
    -------
    rotated : LVecBase2d
        Point rotated about pivot by the specified angle.
    """
    if Decimal(angle) % Decimal(math.pi * 2) == Decimal(0):
        logging.debug(f"Skipping point rotation: angle={angle}")
        return vector

    angle_sin = math.sin(angle)
    angle_cos = math.cos(angle)

    point_unbound = vector - pivot

    x_new = point_unbound.x * angle_cos - point_unbound.y * angle_sin
    y_new = point_unbound.x * angle_sin + point_unbound.y * angle_cos

    rotated = LVecBase2d(x_new + pivot.x, y_new + pivot.y)

    return rotated
