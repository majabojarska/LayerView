"""G-code command tokens."""

from typing import Tuple

GcodeToken = Tuple[str, str]  # Pair of letter and optional number literal

# Commands without parameters
G20_SET_UNITS_TO_INCHES: GcodeToken = ("g", "20")
G21_SET_UNITS_TO_MILLIS: GcodeToken = ("g", "21")
G90_SET_ABS_POSITIONING: GcodeToken = ("g", "90")
G91_SET_REL_POSITIONING: GcodeToken = ("g", "91")
M82_SET_EXTRUDER_ABS_MODE: GcodeToken = ("m", "82")
M83_SET_EXTRUDER_REL_MODE: GcodeToken = ("m", "83")

# Commands with parameters
G0_RAPID_MOVE = ("g", "0")
G1_LINEAR_MOVE = ("g", "1")
G2_CLOCKWISE_ARC_MOVE = ("g", "2")
G3_COUNTERCLOCKWISE_ARC_MOVE = ("g", "3")
G28_MOVE_TO_ORIGIN = ("g", "28")
G92_SET_POSITION = ("g", "92")
M104_SET_EXTRUDER_TEMP = ("m", "104")
M109_SET_EXTRUDER_TEMP_AND_WAIT = ("m", "109")
