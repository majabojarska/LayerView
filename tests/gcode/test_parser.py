"""Unit tests for `parser` module."""

from pathlib import Path

import pytest

from layerview.gcode.parser import GcodeParser, GcodeSyntaxError

_GCODE_DIR = Path(__file__).parent.parent / "assets/gcode"


class TestGcodeParser:
    """Unit tests for GcodeParser class."""

    @pytest.mark.parametrize("path_gcode", [_GCODE_DIR / "cube_10mm.gcode"])
    def test_parse_gcode_valid_sanity(self, path_gcode):
        """Test sanity of parse method.

        Parameters
        ----------
        path_gcode : Path
            Path to valid G-code file.
        """
        GcodeParser.parse(path_gcode, skip_unknown=True)

    @pytest.mark.parametrize("path_gcode", [_GCODE_DIR / "simple_bad.gcode"])
    def test_parse_gcode_invalid_syntax(self, path_gcode):
        """Test parse method against an gcode file with invalid syntax.

        Parameters
        ----------
        path_gcode : Path
            Path to G-code file with invalid syntax.
        """
        with pytest.raises(GcodeSyntaxError):
            GcodeParser.parse(path_gcode, skip_unknown=True)
