"""Point cloud generation errors."""
from abc import ABC

from layerview.common.mixins import MixinMarkdown


class EffectorDescentError(Exception, MixinMarkdown, ABC):
    """Generic effector descent error."""

    def __init__(self, cur_layer_z: float, prev_layer_z: float):
        """
        Parameters
        ----------
        cur_layer_z : float
            Current layer Z position (after the invalid descent).
        prev_layer_z : float
            Previous layer Z position (before the invalid descent).
        """
        self._cur_layer_z: float = cur_layer_z
        self._prev_layer_z: float = prev_layer_z

        super().__init__()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"cur_layer_z={self.cur_layer_z}, "
            f"prev_layer_z={self.prev_layer_z}"
            f")"
        )

    @property
    def cur_layer_z(self) -> float:
        return self._cur_layer_z

    @property
    def prev_layer_z(self) -> float:
        return self._prev_layer_z


class LateEffectorDescentError(EffectorDescentError):
    """Late effector descent error."""

    def __init__(self, cur_layer_z: float, prev_layer_z: float, prev_layer_count: int):
        """
        Parameters
        ----------
        cur_layer_z : float
            Current layer Z position (after the invalid descent).
        prev_layer_z : float
            Previous layer Z position (before the invalid descent).
        prev_layer_count : int
            Layer count before the invalid effector descent.
        """
        super(LateEffectorDescentError, self).__init__(
            cur_layer_z=cur_layer_z, prev_layer_z=prev_layer_z
        )

        self._prev_layer_count: int = prev_layer_count

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"cur_layer_z={self.cur_layer_z}, "
            f"prev_layer_z={self.prev_layer_z}, "
            f"prev_layer_count={self.prev_layer_count}"
            f")"
        )

    def __str__(self) -> str:
        return (
            f"Effector descended after printing "
            f"{self.prev_layer_count} layers "
            f"(from {self.prev_layer_z}mm to {self.cur_layer_z}mm)."
        )

    def as_markdown(self) -> str:
        return str(self)

    @property
    def prev_layer_count(self) -> int:
        return self._prev_layer_count


class PostPrimingDescentError(EffectorDescentError):
    """Post-priming effector descent error."""

    def __str__(self) -> str:
        return (
            f"Effector descended after post priming descent "
            f"(from {self.prev_layer_z}mm to {self.cur_layer_z}mm)."
        )

    def as_markdown(self) -> str:
        return str(self)
