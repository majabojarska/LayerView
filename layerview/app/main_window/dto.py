from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Generator, Optional, Union

from panda3d.core import LVector3d
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap

from layerview.app.constants import UNIT_DEGREES_CELSIUS, UNIT_MM, UNIT_MM_PER_MIN
from layerview.visualization.point_cloud.model import LayerInfo, ModelInfo
from layerview.visualization.world.world import ColoringMode

round_2 = partial(round, ndigits=2)


class IntRangeDTO:
    def __init__(self, start: int, stop: int):
        if not all(
            isinstance(elem, int) or isinstance(elem, float) for elem in [start, stop]
        ):
            raise TypeError(
                f"Expecting start and stop to be of type "
                f"{int} or {float}, got {type(start)}, {type(stop)}."
            )
        if stop < start:
            raise ValueError(f"Start ({start}) must not be greater than stop ({stop}).")

        self.start = start
        self.stop = stop

    def __iter__(self) -> Generator[int, Any, None]:
        return (elem for elem in (self.start, self.stop))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start}, stop={self.stop})"


@dataclass
class ModelInfoDTO:
    text_layer_count: str
    text_height: str
    text_width: str
    text_depth: str

    @staticmethod
    def null_object() -> ModelInfoDTO:
        return ModelInfoDTO(
            text_layer_count="", text_height="", text_width="", text_depth=""
        )

    @staticmethod
    def from_model_info(model_info: ModelInfo) -> ModelInfoDTO:
        text_layer_count = str(model_info.layer_count)

        size: LVector3d = model_info.boundaries.size
        text_height: str = f"{round_2(size.z)}{UNIT_MM}"
        text_width: str = f"{round_2(size.x)}{UNIT_MM}"
        text_depth: str = f"{round_2(size.y)}{UNIT_MM}"

        dto = ModelInfoDTO(
            text_layer_count=text_layer_count,
            text_height=text_height,
            text_width=text_width,
            text_depth=text_depth,
        )

        return dto


@dataclass
class LayerInfoDTO:
    layer_number: int
    text_z_pos: str
    text_thickness: str
    text_temperature: str
    text_feedrate: str

    @staticmethod
    def null_object() -> LayerInfoDTO:
        dto: LayerInfoDTO = LayerInfoDTO(
            layer_number=0,
            text_z_pos="",
            text_thickness="",
            text_temperature="",
            text_feedrate="",
        )

        return dto

    @staticmethod
    def from_layer_info(
        layer_info: LayerInfo, layer_num: int, z_position: float, height: float
    ) -> LayerInfoDTO:

        # Prepare DTO fields
        text_z_pos: str = (
            f"{round_2(z_position)}{UNIT_MM}" if z_position is not None else ""
        )
        text_thickness: str = (
            f"{round_2(height)}{UNIT_MM}" if height is not None else ""
        )

        if (
            layer_info.temperature_max is not None
            and layer_info.temperature_min is not None
        ):
            text_temp_min: str = str(round_2(layer_info.temperature_min))
            text_temp_max: str = str(round_2(layer_info.temperature_max))
            text_temperature: str = (
                f"{text_temp_min}"
                if text_temp_min == text_temp_max
                else f"{text_temp_min}-{text_temp_max}"
            ) + UNIT_DEGREES_CELSIUS
        else:
            text_temperature: str = ""

        if layer_info.feedrate_min is not None and layer_info is not None:
            text_feedrate_min: str = str(round_2(layer_info.feedrate_min))
            text_feedrate_max: str = str(round_2(layer_info.feedrate_max))

            text_feedrate: str = (
                f"{text_feedrate_min}"
                if text_feedrate_min == text_feedrate_max
                else f"{text_feedrate_min}-{text_feedrate_max}"
            ) + UNIT_MM_PER_MIN
        else:
            text_feedrate: str = ""

        # Compose DTO
        dto = LayerInfoDTO(
            layer_number=layer_num,
            text_z_pos=text_z_pos,
            text_thickness=text_thickness,
            text_temperature=text_temperature,
            text_feedrate=text_feedrate,
        )

        return dto


@dataclass
class ColoringGroupDTO:
    coloring_mode: ColoringMode
    pixmap: QPixmap
    text_left: str = ""
    text_center: str = ""
    text_right: str = ""

    def __init__(
        self,
        coloring_mode: ColoringMode,
        pixmap: Optional[QPixmap] = None,
        text_left: Optional[str] = "",
        text_center: Optional[str] = "",
        text_right: Optional[str] = "",
    ):
        self.coloring_mode: ColoringMode = coloring_mode

        if not pixmap:
            q_image = ImageQt(
                Image.new(mode="RGBA", size=(1, 1), color=(255, 255, 255, 255))
            )
            pixmap = QPixmap.fromImage(q_image)
        self.pixmap: QPixmap = pixmap

        self.text_left = text_left
        self.text_center = text_center
        self.text_right = text_right


class StatusBarMessageDTO:
    def __init__(self, text: str, duration: int = 0):
        """
        Parameters
        ----------
        text : str
            The text to display on status bar
        duration : int
            Text display duration. Set 0 for infinite duration.
        """
        self.text = text

        if not isinstance(duration, int):
            raise TypeError(
                f"Expected duration to be of type {int}, got {type(duration)}."
            )
        if duration < 0:
            raise ValueError(f"Duration must be a non-negative int, got {duration}.")

        self.duration = duration

    def __iter__(self) -> Generator[Union[str, int], Any, None]:
        return (elem for elem in (self.text, self.duration))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(text={self.text}, duration={self.duration})"
