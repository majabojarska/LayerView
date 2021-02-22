"""Model color manipulation."""

from typing import Dict, Tuple

import numpy as np
from PIL import Image
from PIL.ImageDraw import ImageDraw
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap

from layerview.visualization.nodes.model import ModelManager
from layerview.visualization.world.world import ColoringMode

# Type alias
TupleFloat4 = Tuple[float, float, float, float]


def gradient_pixmap(
    color_start: TupleFloat4,
    color_end: TupleFloat4,
    size: Tuple[int, int],
) -> QPixmap:
    """Generate color gradient pixmap.

    Parameters
    ----------
    color_start : Tuple[float, float, float]
        RGBA color tuple, values [0;1].
    color_end : Tuple[float, float, float]
        RGBA color tuple, values [0;1].
    size : Tuple[int, int]
        Size in pixels (width, height).

    Returns
    -------
    pixmap : QPixmap
    """
    width, height = size

    gradient_colors = np.linspace(
        np.array(color_start), np.array(color_end), num=width, endpoint=True
    )
    gradient_colors *= 255
    gradient_colors = np.round(gradient_colors, 0).astype(int)
    image = Image.new(mode="RGBA", size=size, color="white")
    draw = ImageDraw(image)

    for x in range(width):
        draw.line(xy=[(x, 0), (x, height - 1)], fill=tuple(gradient_colors[x]), width=1)

    q_image = ImageQt(image)
    pixmap = QPixmap.fromImage(q_image)
    return pixmap


class ModelColorizer:
    """Model coloring tool."""

    _GRADIENT_RESOLUTION = 100

    def __init__(
        self,
        color_default: TupleFloat4,
        color_gradient_start: TupleFloat4,
        color_gradient_end: TupleFloat4,
    ):
        """
        Parameters
        ----------
        color_default : Color4
        color_gradient_start : Color4
        color_gradient_end : Color4
        """
        self.color_constant = color_default
        self.color_gradient_start = color_gradient_start
        self.color_gradient_end = color_gradient_end

        self._gradient_resolution = self._GRADIENT_RESOLUTION

    def colorize(self, model_node_manager: ModelManager, coloring_mode: ColoringMode):
        """Colorize model's layers based on current ColoringMode.

        Parameters
        ----------
        model_node_manager : ModelManager
            Manager of the model to colorize.
        coloring_mode : ColoringMode
            Current coloring mode.

        Raises
        ------
        TypeError
            If the specified coloring mode is not supported.
        """
        if not isinstance(model_node_manager, ModelManager):
            raise ValueError(
                f"Expected model_node_manager to be instance of "
                f"{ModelManager}, got {type(model_node_manager)}."
            )

        if coloring_mode == ColoringMode.CONSTANT:
            self._colorize_default(model_node_manager=model_node_manager)
        elif coloring_mode == ColoringMode.FEEDRATE:
            self._colorize_feedrate(model_node_manager=model_node_manager)
        elif coloring_mode == ColoringMode.THICKNESS:
            self._colorize_thickness(model_node_manager=model_node_manager)
        elif coloring_mode == ColoringMode.TEMPERATURE:
            self._colorize_temperature(model_node_manager=model_node_manager)
        else:
            raise TypeError(f"Unsupported coloring mode: {coloring_mode}")

    def _colorize_default(self, model_node_manager: ModelManager):
        """Colorize the model with a constant, default color"""
        for layer_node in model_node_manager.index_to_layer_node.values():
            layer_node.setColor(self.color_constant)

    def _colorize_feedrate(self, model_node_manager: ModelManager):
        """Colorize the model based on feedrate."""
        model_info = model_node_manager.model_info

        layer_index_to_val = {
            i: (layer_info.feedrate_min + layer_info.feedrate_max) / 2
            for i, layer_info in model_info.index_to_layer_info.items()
        }
        self._colorize_layers(model_node_manager, layer_index_to_val)

    def _colorize_thickness(self, model_node_manager: ModelManager):
        """Colorize the model based on layer thickness."""
        model_info = model_node_manager.model_info

        layer_index_to_val = {
            i: model_info.get_layer_height(i)
            for i, layer_info in model_info.index_to_layer_info.items()
        }
        self._colorize_layers(model_node_manager, layer_index_to_val)

    def _colorize_temperature(self, model_node_manager: ModelManager):
        """Colorize the model based on nozzle temperature."""
        model_info = model_node_manager.model_info

        layer_index_to_val = {
            i: (layer_info.temperature_min + layer_info.temperature_max) / 2
            for i, layer_info in model_info.index_to_layer_info.items()
        }
        self._colorize_layers(model_node_manager, layer_index_to_val)

    def _colorize_layers(
        self,
        model_node_manager: ModelManager,
        layer_index_to_val: Dict[int, float],
    ):
        """Colorize layers based on their corresponding generic value."""
        values = np.array(list(layer_index_to_val.values()))

        # Color gradient
        gradient = self._color_gradient(
            start=self.color_gradient_start,
            end=self.color_gradient_end,
            num_steps=self._gradient_resolution,
        )

        val_min = values.min(initial=values[0])
        val_max = values.max(initial=values[0])

        values_shifted = values - val_min
        if val_min == val_max:
            values_shifted_scaled = values_shifted
        else:
            values_shifted_scaled = values_shifted / (val_max - val_min)

        # Gradient index for each value in values
        gradient_indices = np.round(
            values_shifted_scaled * (self._gradient_resolution - 1)
        ).astype(int)

        for enum_index, layer_index in enumerate(layer_index_to_val.keys()):
            model_node_manager.set_layer_color(
                layer_index, tuple(gradient[gradient_indices[enum_index]])
            )

    @staticmethod
    def _color_gradient(
        start: TupleFloat4, end: TupleFloat4, num_steps: int
    ) -> np.ndarray:
        """Generate array with color gradient.

        Parameters
        ----------
        start : Tuple4
            Gradient start color.
        end : Tuple4
            Gradient end color, included in the returned gradient array.
        num_steps : int
            Total number of gradient steps.

        Returns
        -------
        np.ndarray
            Array containing color gradient.
        """
        gradient_colors = np.linspace(
            np.array(start),
            np.array(end),
            num=num_steps,
            endpoint=True,
        )
        return gradient_colors

    def get_gradient_pixmap(
        self, size: Tuple[int, int], coloring_mode: ColoringMode
    ) -> QPixmap:
        """Returns color gradient pixmap for the specified coloring mode.

        Parameters
        ----------
        size : Tuple[int, int]
            Size in pixels (width, height).
        coloring_mode : ColoringMode

        Returns
        -------
        pixmap : QPixmap
            Color gradient pixmap for the specified coloring mode.
        """
        width, height = size

        if coloring_mode == ColoringMode.CONSTANT:
            color_linspace = self._color_gradient(
                start=self.color_constant, end=self.color_constant, num_steps=width
            )
        else:
            color_linspace = self._color_gradient(
                start=self.color_gradient_start,
                end=self.color_gradient_end,
                num_steps=width,
            )

        gradient_colors_8bit = np.round(color_linspace * 255, 0).astype(int)
        image = Image.new(mode="RGBA", size=size, color="white")
        draw = ImageDraw(image)

        for x in range(width):
            draw.line(
                xy=[(x, 0), (x, height - 1)],
                fill=tuple(gradient_colors_8bit[x]),
                width=1,
            )

        q_image = ImageQt(image)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap
