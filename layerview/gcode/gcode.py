"""Data structures for representing a G-code command sequence."""

from layerview.gcode.commands import Command


class Gcode(list):
    """Data structure for representing a command sequence."""

    def append(self, command: Command) -> None:
        super(Gcode, self).append(command)
