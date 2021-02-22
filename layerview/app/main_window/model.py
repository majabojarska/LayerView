from typing import Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from QPanda3D.Panda3DWorld import Panda3DWorld

from layerview.app.constants import UNIT_DEGREES_CELSIUS, UNIT_MM, UNIT_MM_PER_MIN
from layerview.app.main_window.dto import (
    ColoringGroupDTO,
    IntRangeDTO,
    LayerInfoDTO,
    ModelInfoDTO,
    StatusBarMessageDTO,
)
from layerview.app.main_window.errors import VisualizationInitError
from layerview.visualization.nodes.model import ModelManager
from layerview.visualization.point_cloud.model import ModelInfo
from layerview.visualization.world.color import ModelColorizer
from layerview.visualization.world.world import CameraMode, ColoringMode, Visualization


class Model(QObject):
    NOZZLE_DIAM_DEFAULT: float = 0.4

    MODEL_COLOR_DEFAULT = (30 / 255, 30 / 255, 255 / 255, 1)
    COLOR_GRADIENT_START = (30 / 255, 30 / 255, 1, 1)
    COLOR_GRADIENT_END = (1, 30 / 255, 30 / 255, 1)

    CAMERA_MODE_DEFAULT = CameraMode.SPHERICAL

    # Signals

    # Camera
    update_camera_mode: pyqtSignal = pyqtSignal(CameraMode)
    # Coloring
    update_coloring_group: pyqtSignal = pyqtSignal(ColoringGroupDTO)
    # Visible layer range
    update_layer_range: pyqtSignal = pyqtSignal(IntRangeDTO)
    update_visible_layer_range_start: pyqtSignal = pyqtSignal(int)
    update_visible_layer_range_end: pyqtSignal = pyqtSignal(int)
    # Info
    update_layer_info: pyqtSignal = pyqtSignal(LayerInfoDTO)
    update_model_info: pyqtSignal = pyqtSignal(ModelInfoDTO)
    # Other
    update_panda_3d_world: pyqtSignal = pyqtSignal(Panda3DWorld)
    update_status_bar: pyqtSignal = pyqtSignal(StatusBarMessageDTO)
    update_model_controls_enabled_state: pyqtSignal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.model_color_default = self.MODEL_COLOR_DEFAULT

        self._coloring_mode: ColoringMode = ColoringMode.CONSTANT
        self._visible_range_start: int = 1
        self._visible_range_end: int = 1
        self._layer_info_number: int = 1

        self._gradient_pixmap_size: Tuple[int, int] = (1, 1)

        self._visualization: Optional[Visualization] = None
        self._model_colorizer: ModelColorizer = ModelColorizer(
            color_default=self.MODEL_COLOR_DEFAULT,
            color_gradient_start=self.COLOR_GRADIENT_START,
            color_gradient_end=self.COLOR_GRADIENT_END,
        )

    # Properties

    @property
    def model_node_manager(self) -> Optional[ModelManager]:
        return self._visualization.model_node_manager

    @property
    def model_info(self) -> Optional[ModelInfo]:
        return self._visualization.model_info

    @property
    def visible_range_end(self) -> int:
        return self._visible_range_end

    @property
    def visible_range_start(self) -> int:
        return self._visible_range_start

    @property
    def layer_info_number(self) -> int:
        return self._layer_info_number

    @property
    def camera_mode(self) -> CameraMode:
        return self._visualization.camera_mode

    # Initialization

    def reset(self):
        self._reset_visualization()
        self.set_model_node_manager(None)

    def init_visualization(self):
        if self._visualization:
            raise VisualizationInitError("Visualization already initialized.")

        self._visualization = Visualization(camera_mode=self.CAMERA_MODE_DEFAULT)

        # Emit panda 3d world to view.
        self.update_panda_3d_world.emit(self._visualization)

        # Visualization can be started only after it has been
        # placed in a QPanda3DWidget
        self._reset_visualization()

    def _reset_visualization(self):
        if self._visualization:
            self._visualization.reset()

    # State modifiers

    def set_camera_mode(self, camera_mode: CameraMode):
        # Propagate change to visualization
        if self._visualization:
            self._visualization.set_camera_mode(camera_mode)

        self.update_camera_mode.emit(self.camera_mode)

    def focus_on_model(self):
        self._visualization.focus_on_model()

    def set_coloring_mode(self, coloring_mode: ColoringMode):
        self._coloring_mode = coloring_mode

        if self.model_node_manager:
            self._colorize_model_layers()

        self.update_coloring_group.emit(self._get_coloring_group_dto())

    def set_layer_range(self, layer_range: IntRangeDTO):
        self.update_layer_range.emit(layer_range)

    def set_visible_range_start(self, layer_num: int):
        self._visible_range_start = layer_num

        if self.model_node_manager:
            self._show_current_layer_range_only()

        self.update_visible_layer_range_start.emit(self._visible_range_start)

    def set_visible_range_end(self, layer_num: int):
        self._visible_range_end = layer_num

        if self.model_node_manager:
            self._show_current_layer_range_only()

        self.update_visible_layer_range_end.emit(self._visible_range_end)

    def set_layer_info_number(self, layer_num: int):
        if self.model_info:
            self._layer_info_number = layer_num

            dto = LayerInfoDTO.from_layer_info(
                layer_info=self.model_info.get_layer_info(layer_num),
                layer_num=layer_num,
                z_position=self.model_info.get_layer_z(layer_num),
                height=self.model_info.get_layer_height(layer_num),
            )
        else:
            dto = LayerInfoDTO.null_object()

        self.update_layer_info.emit(dto)

    def set_gradient_pixmap_size(self, size: Tuple[int, int]):
        self._gradient_pixmap_size = size
        self.update_coloring_group.emit(self._get_coloring_group_dto())

    def set_status_bar_message(self, message: StatusBarMessageDTO):
        self.update_status_bar.emit(message)

    def set_model_node_manager(self, manager: Optional[ModelManager]):
        self._visualization.set_model_node_manager(manager=manager)

        if manager:
            # Load new manager
            self.update_layer_range.emit(IntRangeDTO(*manager.model_info.layer_range))
            self.set_visible_range_start(manager.model_info.layer_num_min)
            self.set_visible_range_end(manager.model_info.layer_num_max)
            self.set_layer_info_number(1)
            self.update_coloring_group.emit(self._get_coloring_group_dto())
            self._colorize_model_layers()

            self.update_model_info.emit(
                ModelInfoDTO.from_model_info(model_info=manager.model_info)
            )
        else:
            # Reset state
            self.set_layer_range(IntRangeDTO(1, 1))
            self.update_model_info.emit(ModelInfoDTO.null_object())
            self.update_layer_info.emit(LayerInfoDTO.null_object())
            self.update_coloring_group.emit(self._get_coloring_group_dto())

            self.set_status_bar_message(StatusBarMessageDTO(text="Open G-code file"))

    def handle_window_resize(self):
        pass

    def handle_visualization_focus_out(self):
        self._visualization.handle_focus_out()

    # Protected

    def _show_current_layer_range_only(self):
        self.model_node_manager.show_layer_range_only(
            start=self._visible_range_start, end=self._visible_range_end
        )

    def _colorize_model_layers(self):
        self._model_colorizer.colorize(
            model_node_manager=self.model_node_manager,
            coloring_mode=self._coloring_mode,
        )

    def _get_coloring_group_dto(self) -> ColoringGroupDTO:
        model_info = self.model_info
        coloring_mode = self._coloring_mode
        color_gradient_dto: ColoringGroupDTO = ColoringGroupDTO(
            coloring_mode=coloring_mode
        )

        if model_info:
            val_min: Optional[float] = None
            val_max: Optional[float] = None

            if coloring_mode == ColoringMode.CONSTANT:
                color_gradient_dto.text_center = "Constant color mode"
            elif coloring_mode == ColoringMode.FEEDRATE:
                val_min = model_info.feedrate_min
                val_max = model_info.feedrate_max
                color_gradient_dto.text_center = UNIT_MM_PER_MIN

            elif coloring_mode == ColoringMode.THICKNESS:
                val_min = model_info.layer_height_min
                val_max = model_info.layer_height_max
                color_gradient_dto.text_center = UNIT_MM

            elif coloring_mode == ColoringMode.TEMPERATURE:
                val_min = model_info.temperature_min
                val_max = model_info.temperature_max
                color_gradient_dto.text_center = UNIT_DEGREES_CELSIUS
            else:
                raise TypeError(f"Unsupported coloring mode: {coloring_mode}")

            # Text left and right
            color_gradient_dto.text_left = (
                str(round(val_min, 3)) if val_min is not None else ""
            )
            color_gradient_dto.text_right = (
                str(round(val_max, 3)) if val_max is not None else ""
            )

            # Gradient pixmap
            if val_min == val_max:
                color_gradient_dto.pixmap = self._model_colorizer.get_gradient_pixmap(
                    size=self._gradient_pixmap_size, coloring_mode=ColoringMode.CONSTANT
                )
            else:
                color_gradient_dto.pixmap = self._model_colorizer.get_gradient_pixmap(
                    size=self._gradient_pixmap_size, coloring_mode=coloring_mode
                )

        else:
            color_gradient_dto.text_center = "No model"

        return color_gradient_dto
