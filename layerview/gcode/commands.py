"""G-code commands and command parsing logic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Type

import layerview.gcode.tokens as gcode_tokens
from layerview.gcode import utils
from layerview.gcode.lexemes import LETTERS_COMMAND, LETTERS_PARAM
from layerview.gcode.tokens import GcodeToken

# Exceptions


class CommandParseError(Exception):
    pass


class CommandTokenError(CommandParseError):
    pass


class CommandMissingParamError(CommandParseError):
    pass


class CommandInvalidParamError(CommandParseError):
    pass


# Commands


class Command(ABC):
    """Generic G-code command."""

    __slots__ = ("line_number", "__dict__")

    def __init__(self, line_number: int = None):
        self.line_number: int = line_number

    @abstractmethod
    @lru_cache
    def __repr__(self):
        pass


class CommandWithParams(Command, ABC):
    """Generic G-code command with params."""

    @property
    @abstractmethod
    def param_letters(self) -> List[str]:
        pass


class CommandWithoutParams(Command):
    """Generic G-code command without params."""

    def __repr__(self):
        return f"{self.__class__.__name__}(line_number={self.line_number})"


class Move(CommandWithParams, ABC):
    """Move command base class."""

    __slots__ = utils.str_to_chars("xyef")

    def __init__(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        e: Optional[float] = None,
        f: Optional[float] = None,
        line_number: int = None,
    ):
        super().__init__(line_number)

        self.x: Optional[float] = x
        self.y: Optional[float] = y
        self.e: Optional[float] = e
        self.f: Optional[float] = f


class LineMove(Move):
    """Generic Line Move """

    param_letters = utils.str_to_chars("xyzefhrs")

    __slots__ = utils.str_to_chars("zhrs")

    def __init__(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        e: float = None,
        f: float = None,
        h: float = None,
        r: float = None,
        s: float = None,
        line_number: int = None,
    ):
        if not any([elem is not None for elem in [x, y, z, e, f, h, r, s]]):
            raise CommandMissingParamError(
                "At least one G-code parameter must be specified."
            )

        super().__init__(x=x, y=y, e=e, f=f, line_number=line_number)

        self.z = z
        self.h = h
        self.r = r
        self.s = s

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"x={self.x}, y={self.y}, z={self.z}, e={self.e}, "
            f"f={self.f}, h={self.h}, r={self.r}, s={self.s})"
        )


class G0(LineMove):
    """Rapid Move."""

    pass


class G1(LineMove):
    """Linear Move."""

    pass


class ArcMove(Move):
    """Generic Arc Move."""

    param_letters = utils.str_to_chars("xyijef")

    def __init__(
        self,
        x: float = None,
        y: float = None,
        i: float = None,
        j: float = None,
        e: float = None,
        f: float = None,
        line_number: int = None,
    ):
        params_mandatory = {"x": x, "y": y, "i": i, "j": j, "e": e}
        if not all([elem is not None for elem in params_mandatory.values()]):
            raise CommandMissingParamError(
                f"The following parameters must be specified: "
                f"{', '.join(params_mandatory.keys())}."
            )

        super().__init__(x=x, y=y, e=e, f=f, line_number=line_number)

        self.i = i
        self.j = j

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"x={self.x}, y={self.y}, i={self.i}, "
            f"j={self.j}, e={self.e}, f={self.f})"
        )


class G2(ArcMove):
    """Clockwise Arc."""

    pass


class G3(ArcMove):
    """Counter-Clockwise Arc."""

    pass


class SetTemperatureExtruder(CommandWithParams, ABC):
    """Generic set temperature command."""

    def __init__(self, s: float, r: float = None, line_number: int = None):
        super().__init__(line_number=line_number)

        self.s = s
        self.r = r


class M104(SetTemperatureExtruder):
    """Set Extruder Temperature """

    param_letters = utils.str_to_chars("srd")

    def __init__(
        self, s: float, r: float = None, d: float = None, line_number: int = None
    ):
        super().__init__(s=s, r=r, line_number=line_number)

        self.d = d

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"s={self.s}, r={self.r}, d={self.d})"
        )


class M109(SetTemperatureExtruder):
    """Set Extruder Temperature and Wait """

    param_letters = utils.str_to_chars("srt")

    def __init__(
        self, s: float, r: float = None, t: int = None, line_number: int = None
    ):
        super().__init__(s=s, r=r, line_number=line_number)

        self.t = t

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"s={self.s}, r={self.r}, t={self.t})"
        )


class G28(CommandWithParams):
    """Move to origin (home)."""

    param_letters = utils.str_to_chars("xyz")

    def __init__(self, x: bool, y: bool, z: bool, line_number: int = None):
        super().__init__(line_number=line_number)
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"x={self.x}, y={self.y}, z={self.z})"
        )


class G92(CommandWithParams):
    """Set position."""

    param_letters = utils.str_to_chars("xyze")

    def __init__(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        e: float = None,
        line_number: int = None,
    ):
        if not any([elem is not None for elem in [x, y, z, e]]):
            raise CommandMissingParamError("At least one axis must be specified.")

        super().__init__(line_number=line_number)
        self.x = x
        self.y = y
        self.z = z
        self.e = e

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(line_number={self.line_number}, "
            f"x={self.x}, y={self.y}, z={self.z})"
        )


# Commands without parameters


class G20(CommandWithoutParams):
    """Set units to inches."""

    pass


class G21(CommandWithoutParams):
    """Set units to millis."""

    pass


class G90(CommandWithoutParams):
    """Set absolute positioning."""

    pass


class G91(CommandWithoutParams):
    """Set relative positioning."""

    pass


class M82(CommandWithoutParams):
    """Set extruder absolute mode."""

    pass


class M83(CommandWithoutParams):
    """Set extruder relative mode."""

    pass


COMMANDS_LINE_MOVE = (G0, G1)
COMMANDS_ARC_MOVE = (G2, G3)
COMMANDS_MOVE = (*COMMANDS_LINE_MOVE, *COMMANDS_ARC_MOVE)

COMMANDS_SET_TEMPERATURE = [M104, M109]


class CommandParser:
    def __init__(self, skip_unknown: Optional[bool] = False):
        """
        Parameters
        ----------
        skip_unknown : Optional[bool]
            If True, parsing unknown commands will not raise an error.
        """
        self._skip_unknown: bool = skip_unknown

        self._command_token_to_handler: Dict[GcodeToken, Callable] = {
            gcode_tokens.G0_RAPID_MOVE: CommandParser._create_g0,
            gcode_tokens.G1_LINEAR_MOVE: CommandParser._create_g1,
            gcode_tokens.G2_CLOCKWISE_ARC_MOVE: CommandParser._create_g2,
            gcode_tokens.G3_COUNTERCLOCKWISE_ARC_MOVE: CommandParser._create_g3,
            gcode_tokens.G28_MOVE_TO_ORIGIN: CommandParser._create_g28,
            gcode_tokens.G92_SET_POSITION: CommandParser._create_g92,
            gcode_tokens.M104_SET_EXTRUDER_TEMP: CommandParser._create_m104,
            gcode_tokens.M109_SET_EXTRUDER_TEMP_AND_WAIT: CommandParser._create_m109,
            gcode_tokens.G20_SET_UNITS_TO_INCHES: CommandParser._create_g20,
            gcode_tokens.G21_SET_UNITS_TO_MILLIS: CommandParser._create_g21,
            gcode_tokens.G90_SET_ABS_POSITIONING: CommandParser._create_g90,
            gcode_tokens.G91_SET_REL_POSITIONING: CommandParser._create_g91,
            gcode_tokens.M82_SET_EXTRUDER_ABS_MODE: CommandParser._create_m82,
            gcode_tokens.M83_SET_EXTRUDER_REL_MODE: CommandParser._create_m83,
        }

    def parse(self, tokens: List[GcodeToken]) -> List[Command]:
        """
        Parameters
        ----------
        tokens : List[GcodeToken]
            List of G-code tokens, representing G-code fields.
            Expecting [(param, value), (param, value)].
            E.g. [('g', '1'), ('x', '10.25'), ('y', '22')].

        Returns
        -------
        commands : List[Command]
            Parsed commands.
            May be empty if no tokens are present.

        Raises
        ------
        CommandParseError
            If tokens contain unknown commands and skip_unknown is False.
        """
        tokens_grouped: List[List[GcodeToken]] = CommandParser._group_tokens_by_command(
            tokens=tokens
        )
        commands: List[Command] = []

        for token_group in tokens_grouped:
            command_token: GcodeToken = token_group[0]
            handler = self._get_handler(command_token)

            if handler:
                commands.append(handler(token_group))
            elif not self._skip_unknown:
                raise CommandParseError(f"Unsupported command: {token_group}")

        return commands

    def _get_handler(self, command_token: GcodeToken) -> Callable:
        """Get factory method for G-code command.

        Parameters
        ----------
        command_token : GcodeToken
            Command GcodeToken for which the factory method is to be returned.

        Returns
        -------
        Callable
            Factory method for specific G-code command.
        """
        return self._command_token_to_handler.get(command_token)

    @staticmethod
    def _group_tokens_by_command(tokens: List[GcodeToken]) -> List[List[GcodeToken]]:
        """Groups tokens by the command they correspond to.

        Parameters
        ----------
        tokens : List[GcodeToken]
            List of G-code tokens to group by the command they correspond to.

        Returns
        -------
        groups : List[List[GcodeToken]]
            List of lists of G-code tokens.
        """
        groups: List[List[GcodeToken]] = []
        current_group: List[GcodeToken] = []

        for field in tokens:
            letter = field[0]

            if letter in LETTERS_COMMAND:
                # Start of a new command
                if current_group:
                    groups.append(current_group)
                current_group = []
            elif letter in LETTERS_PARAM:
                if not current_group:
                    raise CommandTokenError(
                        "Parameter field specified without a previous command field."
                    )
            else:
                raise CommandTokenError(
                    f"Unrecognized G-code field letter {repr(letter)}."
                )

            current_group.append(field)

        # Command finished with line end
        if current_group:
            groups.append(current_group)

        return groups

    @staticmethod
    def _create_from_float_params(tokens: List[GcodeToken], command_type: Type) -> Any:
        param_to_value = {}
        param_tokens = tokens[1:]

        for token_letter, value_str in param_tokens:
            if token_letter not in command_type.param_letters:
                # Unrecognized parameter for current command
                raise CommandInvalidParamError(
                    f"Unrecognized parameter letter for "
                    f"{command_type}: {repr(token_letter)}"
                )

            param_to_value[token_letter] = float(value_str)

        return command_type(**param_to_value)

    @staticmethod
    def _create_g0(tokens: List[GcodeToken]) -> G0:
        return CommandParser._create_from_float_params(tokens, G0)

    @staticmethod
    def _create_g1(tokens: List[GcodeToken]) -> G1:
        return CommandParser._create_from_float_params(tokens, G1)

    @staticmethod
    def _create_g2(tokens: List[GcodeToken]) -> G2:
        return CommandParser._create_from_float_params(tokens, G2)

    @staticmethod
    def _create_g3(tokens: List[GcodeToken]) -> G3:
        return CommandParser._create_from_float_params(tokens, G3)

    @staticmethod
    def _create_g28(tokens: List[GcodeToken]) -> G28:
        param_to_value: Dict[str, bool] = {}
        param_to_value.update(dict.fromkeys(G28.param_letters, False))

        for param_token, _ in tokens:
            if param_token in G28.param_letters:
                param_to_value[param_token] = True

        return G28(**param_to_value)

    @staticmethod
    def _create_g92(tokens: List[GcodeToken]) -> G92:
        return CommandParser._create_from_float_params(tokens, G92)

    @staticmethod
    def _create_m104(tokens: List[GcodeToken]) -> M104:
        return CommandParser._create_from_float_params(tokens, M104)

    @staticmethod
    def _create_m109(tokens: List[GcodeToken]) -> M109:
        return CommandParser._create_from_float_params(tokens, M109)

    # Commands without params

    @staticmethod
    def _create_g20(_: List[GcodeToken]) -> G20:
        return G20()

    @staticmethod
    def _create_g21(_: List[GcodeToken]) -> G21:
        return G21()

    @staticmethod
    def _create_g90(_: List[GcodeToken]) -> G90:
        return G90()

    @staticmethod
    def _create_g91(_: List[GcodeToken]) -> G91:
        return G91()

    @staticmethod
    def _create_m82(_: List[GcodeToken]) -> M82:
        return M82()

    @staticmethod
    def _create_m83(_: List[GcodeToken]) -> M83:
        return M83()
