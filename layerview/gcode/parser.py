"""Raw G-code text parsing logic."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Generator, Iterable, List, Optional, Union

from layerview.common.mixins import MixinMarkdown
from layerview.gcode.commands import Command, CommandParseError, CommandParser
from layerview.gcode.gcode import Gcode
from layerview.gcode.tokens import GcodeToken


class GcodeSyntaxError(Exception, MixinMarkdown):
    def __init__(self, line_num: int = None, line_raw: str = None, error: Any = None):
        super().__init__()

        self.line_number = line_num
        self.line_raw = line_raw
        self.error = error

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"line_number={self.line_number}, "
            f"line_raw={repr(self.line_raw)}, "
            f"error={repr(self.error)})"
        )

    def as_markdown(self) -> str:
        return (
            f"G-code syntax error at line {self.line_number}:\n\n"
            f"`{self.line_raw}`\n\n"
            f"{str(self.error)}"
        )


class GcodeParser:
    """Gcode parser."""

    _LINE_LENGTH_MAX: int = 256

    @staticmethod
    def parse(path: Union[str, Path], skip_unknown: Optional[bool] = False) -> Gcode:
        """Parses Gcode file at specified path.

        Parameters
        ----------
        path: str or Path
            Path to Gcode file.
        skip_unknown : Optional[bool]
            If True, unknown commands are skipped.

        Returns
        -------
        Gcode
        """
        gcode = Gcode()

        with open(path, "r") as file:
            for command in GcodeParser.command_generator(
                data=file, skip_unknown=skip_unknown
            ):
                gcode.append(command)

        return gcode

    @staticmethod
    def command_generator(
        data: Iterable, skip_unknown: Optional[bool] = False
    ) -> Generator:
        """

        Parameters
        ----------
        data : Iterable
            G-code text data.
        skip_unknown : Optional[bool]
            If True, unknown commands are skipped.

        Yields
        ------
        Command
            Parsed Gcode command.
        """
        line_number = 0
        command_parser = CommandParser(skip_unknown=skip_unknown)

        for line_raw in data:
            line_number += 1

            # Check line length
            line_length = len(line_raw)
            if line_length > GcodeParser._LINE_LENGTH_MAX:
                raise GcodeSyntaxError(
                    line_num=line_number,
                    line_raw=line_raw,
                    error=(
                        f"Line length must not be greater than "
                        f"{GcodeParser._LINE_LENGTH_MAX} (is {line_length})."
                    ),
                )

            # Parse line
            try:
                tokens: List[GcodeToken] = GcodeScanner.analyze(line_raw)
                commands: List[Command] = command_parser.parse(tokens=tokens)
            except (CommandParseError, ValueError) as e:
                raise GcodeSyntaxError(
                    line_num=line_number, line_raw=line_raw.strip(), error=e
                )
            if not commands:
                # No significant information in current line
                continue

            for command in commands:
                command.line_number = line_number
                yield command


class GcodeScanner:
    # Matches comments, N commands and whitespace
    _PATTERN_INSIGNIFICANT = re.compile(r"\(.*\)|;.*|\s+")

    # Matches G-code fields.
    # Capture groups: 0 - letter, 1 - optional number literal
    _PATTERN_GCODE_TOKEN = re.compile(r"([a-z])([-+]?\d*\.?\d*)")

    @staticmethod
    def analyze(line: str) -> List[GcodeToken]:
        """Performs lexical analysis on single line of G-code.

        Parameters
        ----------
        line : str
            Raw G-code line string.

        Raises
        ------
        GcodeSyntaxError
            If G-code syntax is invalid.

        Returns
        -------
        List[GcodeToken]
            List of G-code tokens in form [(command_or_param_letter, number_literal)],
            e.g. [('G', '1'), ('X', '20')].
        """
        # Split command text into list of lexeme pairs ()
        return GcodeScanner._PATTERN_GCODE_TOKEN.findall(GcodeScanner._sanitize(line))

    @staticmethod
    def _sanitize(line: str) -> str:
        """Strips comments, whitespace and converts text to lowercase.

        Parameters
        ----------
        line : str
            Gcode line to sanitize.

        Returns
        -------
        str
            Sanitized Gcode line.
        """
        return GcodeScanner._PATTERN_INSIGNIFICANT.sub("", line).lower()
