"""Provides machine's toolpath abstraction."""
from panda3d.core import LVector2d


class Path(list):
    """Represents a single, continuous path in the XY plane."""

    def __init__(self, point_first: LVector2d, point_second: LVector2d):
        """

        Parameters
        ----------
        point_first : LVector2d
        point_second : LVector2d
        """
        super().__init__()
        self.extend([point_first, point_second])

    def add_padding(self, length: float):
        """Shift first and last path points to take nozzle diameter into account.

        Parameters
        ----------
        length : float
            Padding length, half of the nozzle diameter.
        """
        # Start
        self[0] = LVector2d(*(self[0] + (self[0] - self[1]).normalized() * length))

        # End
        self[-1] = LVector2d(*(self[-1] + (self[-1] - self[-2]).normalized() * length))
