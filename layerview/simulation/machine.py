"""RepRap FDM machine abstraction."""
from __future__ import annotations

from functools import lru_cache
from typing import Callable, Dict, Optional, Tuple, Type

from panda3d.core import Point3D

from layerview.gcode import commands
from layerview.gcode.commands import (
    ArcMove,
    Command,
    LineMove,
    Move,
    SetTemperatureExtruder,
)


class UnknownCommandError(Exception):
    """Thrown when an unknown (unsupported) command is provided to Machine."""


class Machine:
    """FDM Machine abstraction."""

    def __init__(self, skip_unknown: Optional[bool] = False):
        """
        Parameters
        ----------
        skip_unknown : Optional[bool]
            If True, unknown provided commands will be skipped.
            Otherwise, providing an unknown command will raise an exception.
        """
        self._skip_unknown: bool = skip_unknown

        self.state_previous: MachineState = MachineState()
        self.state_current: MachineState = MachineState()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.state_current.__dict__})"

    @property
    @lru_cache(1)
    def _command_type_to_handler(self) -> Dict[Type, Callable]:
        """Return dict mapping Command types to handler callables.

        Returns
        -------
        Callable
            Dict mapping Command types to handler callables.
        """
        command_type_to_handler: Dict[Type, Callable] = {
            commands.G20: self._set_units_to_inches,
            commands.G21: self._set_units_to_millis,
            commands.G28: self._move_to_origin,
            commands.G90: self._set_abs_positioning,
            commands.G91: self._set_rel_positioning,
            commands.M82: self._set_extruder_abs_mode,
            commands.M83: self._set_extruder_rel_mode,
            commands.G92: self._set_position,
        }
        command_type_to_handler.update(
            dict.fromkeys(commands.COMMANDS_MOVE, self._handle_move)
        )
        command_type_to_handler.update(
            dict.fromkeys(
                [commands.M104, commands.M109], self._set_temperature_extruder
            )
        )

        return command_type_to_handler

    def _get_handler(self, command: Command) -> Optional[Callable]:
        """Return handler callable for specified command.

        Returned callable expects NO parameters.

        Parameters
        ----------
        command : str
            G-code command token.

        Returns
        -------
        Callable
        """
        return self._command_type_to_handler.get(command.__class__)

    def handle_command(self, command: Command):
        """Handle command.

        Parameters
        ----------
        command : Command
            Command to handle.

        Raises
        ------
        UnknownCommandError
            If command is unknown and self._skip_unknown is False.
        """
        # Save current state as previous state, before handling the command

        # Handle command
        command_handler = self._get_handler(command)
        if command_handler:
            self.state_previous.update(self.state_current)
            command_handler(command)
        elif not self._skip_unknown:
            raise UnknownCommandError(f"Unknown command: {repr(command)}.")

    # Machine state modifiers

    def _handle_move(self, command: Move):
        """Handle Move commands.

        Parameters
        ----------
        command : Move
            The Move command to handle.
        """
        # Handle feedrate
        if command.f is not None:
            self.state_current.feedrate = command.f

        # Handle extruder
        if command.e is not None:
            if self.state_previous.is_rel_extruder:
                # Relative
                self.state_current.extruder = self.state_previous.extruder + command.e
            else:
                # Absolute
                self.state_current.extruder = command.e

        # Handle position change
        if self.state_previous.is_rel_positioning:
            # Relative
            position_delta = Point3D(
                *[val or 0 for val in get_xyz_from_command(command)]
            )
            self.state_current.position = self.state_previous.position + position_delta
            # Round to 3 decimal places, to compensate for computation errors
            self.state_current.position.x = round(self.state_current.position.x, 3)
            self.state_current.position.y = round(self.state_current.position.y, 3)
            self.state_current.position.z = round(self.state_current.position.z, 3)

        else:
            # Absolute
            if command.x is not None:
                self.state_current.position.x = (
                    command.x * self.state_previous.unit_multiplier
                )
            if command.y is not None:
                self.state_current.position.y = (
                    command.y * self.state_previous.unit_multiplier
                )
            if isinstance(command, LineMove) and command.z is not None:
                self.state_current.position.z = (
                    command.z * self.state_previous.unit_multiplier
                )

    def _set_units_to_inches(self, *args, **kwargs):
        """Set input units to inches."""
        self.state_current.is_imperial = True

    def _set_units_to_millis(self, *args, **kwargs):
        """Set input units to millimeters."""
        self.state_current.is_imperial = False

    def _set_abs_positioning(self, *args, **kwargs):
        """Set nozzle positioning mode to absolute."""
        self.state_current.is_rel_positioning = False

    def _set_rel_positioning(self, *args, **kwargs):
        """Set effector positioning mode to relative."""
        self.state_current.is_rel_positioning = True

    def _set_extruder_abs_mode(self, *args, **kwargs):
        """Set effector positioning mode to absolute."""
        self.state_current.is_rel_extruder = False

    def _set_extruder_rel_mode(self, *args, **kwargs):
        """Set extruder positioning mode to relative."""
        self.state_current.is_rel_extruder = True

    def _move_to_origin(self, command: commands.G28):
        """Perform effector homing.

        Parameters
        ----------
        command: commands.G28
            G28 command.
        """
        if not any([command.x, command.y, command.z]):
            # No axes specified, home all axes
            self.state_current.offset_position = Point3D(0, 0, 0)
            self.state_current.position = Point3D(0, 0, 0)
            return

        # Selective axis homing
        if command.x:
            self.state_current.offset_position.x = 0
            self.state_current.position.x = 0
        if command.y:
            self.state_current.offset_position.y = 0
            self.state_current.position.y = 0
        if command.z:
            self.state_current.offset_position.z = 0
            self.state_current.position.z = 0

    def _set_position(self, command: commands.G92):
        """Set effector position.

        Parameters
        ----------
        command : commands.G92
            Input command.
        """
        if command.x:
            self.state_current.offset_position.x = (
                self.state_previous.position.x - command.x
            )
        if command.y:
            self.state_current.offset_position.y = (
                self.state_previous.position.y - command.y
            )
        if command.z:
            self.state_current.offset_position.z = (
                self.state_previous.position.z - command.z
            )
        if command.e:
            self.state_current.offset_extruder = (
                self.state_previous.extruder - command.e
            )

    def _set_temperature_extruder(self, command: SetTemperatureExtruder):
        """Set extruder (nozzle) temperature.

        Parameters
        ----------
        command : SetTemperatureExtruder
            Input command.
        """
        self.state_current.temp_extruder = command.s


class MachineState:
    """FDM machine's state abstraction."""

    def __init__(
        self,
        position: Point3D = Point3D(0, 0, 0),
        offset_position: Point3D = Point3D(0, 0, 0),
        extruder: float = 0,
        offset_extruder: float = 0,
        feedrate: float = 40,
        temp_extruder: float = 0,
        is_positioning_rel: bool = False,
        is_extruder_rel: bool = False,
        is_imperial: bool = False,
    ):
        """
        Parameters
        ----------
        position : Point3D, optional
            Absolute effector position, relative to origin.
        offset_position : Point3D, optional
            Offset from origin.
        extruder : float, optional
            Extruder value (E axis position).
        offset_extruder : float, optional
            Extruder value (E axis position) offset.
        feedrate : float, optional
            Effector translation feedrate in mm/s.
        temp_extruder : float, optional
            Extruder temperature (degrees C).
        is_positioning_rel : bool, optional
            Defines whether relative effector positioning is enabled.
        is_extruder_rel : bool, optional
            Defines whether relative extruder value is enabled.
        is_imperial : bool, optional
            Defines whether the used unit system is imperial (inches).

        Default values are based on RepRapFirmware defaults.
        """
        self.position = position
        self.offset_position = offset_position
        self.extruder = extruder
        self.offset_extruder = offset_extruder
        self.feedrate = feedrate
        self.temp_extruder = temp_extruder
        self.is_rel_positioning = is_positioning_rel
        self.is_rel_extruder = is_extruder_rel
        self.is_imperial = is_imperial

    def __repr__(self):
        return str(self.__dict__)

    def update(self, state: MachineState):
        """Update this state.

        Parameters
        ----------
        state : MachineState
            The new state to update this state with.
        """
        self.position = Point3D(state.position)
        self.offset_position = Point3D(state.offset_position)
        self.extruder = state.extruder
        self.offset_extruder = state.offset_extruder
        self.feedrate = state.feedrate
        self.temp_extruder = state.feedrate
        self.is_rel_positioning = state.is_rel_positioning
        self.is_rel_extruder = state.is_rel_extruder
        self.is_imperial = state.is_imperial

    @property
    def position_abs(self) -> Point3D:
        """Return absolute effector position.

        Returns
        -------
        Point3D
            Absolute effector position.
        """
        return self.position - self.offset_position

    @property
    def extruder_abs(self) -> float:
        """Return absolute extruder value.

        Returns
        -------
        float
            Absolute extruder position (E axis).
        """
        return self.extruder - self.offset_extruder

    @property
    def unit_multiplier(self) -> float:
        """Return unit multiplier for incoming length values.

        Returned value depends on imperial mode flag state (inches).

        Returns
        -------
        float
            Unit multiplier.
        """
        if self.is_imperial:
            return 25.4
        return 1.0


def get_xyz_from_command(
    command: Move,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Extract X, Y, Z values from the provided Move command.

    Parameters
    ----------
    command: Move
        A Move command.

    Returns
    -------
    tuple
        Tuple containing (X, Y, Z) values extracted from the provided command.
        Axis values that are not present in the provided Move command default
        to None.

    Raises
    ------
    TypeError
        If `command` is not an instance of Move (G0, G1, G2 or G3).
    """
    if isinstance(command, LineMove):
        return command.x, command.y, command.z
    elif isinstance(command, ArcMove):
        return command.x, command.y, None
    else:
        raise TypeError("Command must be a move command (G0, G1, G2, G3).")
