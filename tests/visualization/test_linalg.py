"""Unit tests for `linalg` module."""

import math

import pytest
from panda3d.core import LVecBase2d, LVector2d

from layerview.visualization.linalg import angle_inner, angle_signed, vec_rotated


@pytest.mark.parametrize(
    "a, b, expected_angle",
    [
        (LVector2d(1, 0), LVector2d(0, 1), math.pi / 2),
        (LVector2d(0, 1), LVector2d(0, 1), 0),
        (LVector2d(0, 1), LVector2d(0, -1), math.pi),
        (LVector2d(0, 1), LVector2d(100, 0), math.pi / 2),
        (LVector2d(1, 0), LVector2d(1, 1), math.pi / 4),
        (LVector2d(-1, 0), LVector2d(1, 1), math.pi * 0.75),
    ],
)
def test_angle_inner(a: LVecBase2d, b: LVecBase2d, expected_angle: float):
    """Test angle_inner function."""
    actual_angle = angle_inner(a, b)

    assert math.isclose(actual_angle, expected_angle, abs_tol=0.1)


@pytest.mark.parametrize(
    "a, b, expected_angle",
    [
        (LVector2d(1, 0), LVector2d(0, 1), math.pi / 2),
        (LVector2d(0, 1), LVector2d(1, 0), -math.pi / 2),
    ],
)
def test_angle_signed(a: LVecBase2d, b: LVecBase2d, expected_angle: float):
    """Test angle_signed function."""
    actual_angle = angle_signed(a, b)

    assert math.isclose(actual_angle, expected_angle, abs_tol=0.1)


@pytest.mark.parametrize(
    "vector, pivot, angle, rotated_expected",
    [
        (LVector2d(1, 0), LVector2d(0, 0), math.pi / 2, LVector2d(0, 1)),
        (LVector2d(3, 4), LVector2d(3, 3), -math.pi / 2, LVector2d(4, 3)),
    ],
)
def test_vector_rotated(
    vector: LVector2d, pivot: LVector2d, angle: float, rotated_expected: LVector2d
):
    """Test vec_rotated function."""
    rotated_actual = vec_rotated(vector, pivot, angle)

    assert all(
        [
            math.isclose([*rotated_actual][i], [*rotated_expected][i], rel_tol=1)
            for i in range(2)
        ]
    )
