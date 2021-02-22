from typing import Dict

from PyQt5 import QtGui
from PyQt5.QtCore import QMimeData, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFocusEvent
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QShortcut
from QPanda3D.Panda3DWorld import Panda3DWorld

from layerview.app.main_window.dto import (
    ColoringGroupDTO,
    IntRangeDTO,
    LayerInfoDTO,
    ModelInfoDTO,
    StatusBarMessageDTO,
)
from layerview.app.main_window.model import Model
from layerview.app.main_window.visualization import VisualizationWidget
from layerview.app.pyuic.main_window import Ui_MainWindow
from layerview.visualization.point_cloud.model import LayerInfo
from layerview.visualization.world.world import CameraMode, ColoringMode


class View(QMainWindow):
    """Abstract View """

    # Widgets
    changed_camera_mode: pyqtSignal = pyqtSignal(CameraMode)
    changed_coloring_mode: pyqtSignal = pyqtSignal(ColoringMode)
    changed_visible_range_start: pyqtSignal = pyqtSignal(int)
    changed_visible_range_end: pyqtSignal = pyqtSignal(int)
    changed_layer_info_number: pyqtSignal = pyqtSignal(int)
    changed_gradient_pixmap_size: pyqtSignal = pyqtSignal(tuple)

    pressed_focus: pyqtSignal = pyqtSignal()

    resized_window: pyqtSignal = pyqtSignal()

    # Actions
    requested_file_open: pyqtSignal = pyqtSignal()
    requested_clear: pyqtSignal = pyqtSignal()
    requested_quit: pyqtSignal = pyqtSignal()
    requested_about: pyqtSignal = pyqtSignal()
    requested_manual: pyqtSignal = pyqtSignal()

    # Events
    dropped_file: pyqtSignal = pyqtSignal(QDropEvent)
    visualization_lost_focus = pyqtSignal(QFocusEvent)


class ConcreteView(View):
    def __init__(self, model: Model):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.model: Model = model

        # Connect model's signals to own slots
        self._setup_slots()

        # Setup output signals
        self._setup_signals()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self.resized_window.emit()
        self._emit_gradient_pixmap_size()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._emit_gradient_pixmap_size()

    def _emit_gradient_pixmap_size(self):
        gradient_label_frame_width = self.ui.labelColorGradient.frameWidth()
        gradient_label_pixmap_size = (
            self.ui.labelColorGradient.width() - 2 * gradient_label_frame_width,
            self.ui.labelColorGradient.height() - 2 * gradient_label_frame_width,
        )
        self.changed_gradient_pixmap_size.emit(gradient_label_pixmap_size)

    def _setup_slots(self):
        """Connects Model's output signals to this View's slots."""
        # Model
        self.model.update_camera_mode.connect(self._on_update_camera_mode)
        self.model.update_coloring_group.connect(self._on_update_coloring_group)
        self.model.update_layer_range.connect(self._on_update_layer_range)
        self.model.update_visible_layer_range_start.connect(
            self._on_update_visible_layer_range_start
        )
        self.model.update_visible_layer_range_end.connect(
            self._on_update_visible_layer_range_end
        )
        self.model.update_layer_info.connect(self._on_update_layer_info)
        self.model.update_model_info.connect(self._on_update_model_info)
        self.model.update_panda_3d_world.connect(self._on_update_panda_3d_world)
        self.model.update_status_bar.connect(self._on_update_status_bar)
        self.model.update_model_controls_enabled_state.connect(
            self._on_update_model_controls_enabled_state
        )

    def _setup_signals(self):
        """Connects this View's signals to Abstract View's signals.

        Essentially propagates signals to a common interface.
        """
        # Camera Mode
        self.ui.radioButtonCameraModeSpherical.toggled.connect(
            lambda: self.changed_camera_mode.emit(CameraMode.SPHERICAL)
            if self.ui.radioButtonCameraModeSpherical.isChecked()
            else None
        )
        self.ui.radioButtonCameraModeFree.toggled.connect(
            lambda: self.changed_camera_mode.emit(CameraMode.FREE)
            if self.ui.radioButtonCameraModeFree.isChecked()
            else None
        )
        self.ui.pushButtonCameraModeFocus.pressed.connect(self.pressed_focus.emit)

        # Coloring Mode
        self.ui.radioButtonColoringDefault.toggled.connect(
            lambda: self.changed_coloring_mode.emit(ColoringMode.CONSTANT)
            if self.ui.radioButtonColoringDefault.isChecked()
            else None
        )
        self.ui.radioButtonColoringFeedrate.toggled.connect(
            lambda: self.changed_coloring_mode.emit(ColoringMode.FEEDRATE)
            if self.ui.radioButtonColoringFeedrate.isChecked()
            else None
        )
        self.ui.radioButtonColoringTemperature.toggled.connect(
            lambda: self.changed_coloring_mode.emit(ColoringMode.TEMPERATURE)
            if self.ui.radioButtonColoringTemperature.isChecked()
            else None
        )
        self.ui.radioButtonColoringThickness.toggled.connect(
            lambda: self.changed_coloring_mode.emit(ColoringMode.THICKNESS)
            if self.ui.radioButtonColoringThickness.isChecked()
            else None
        )

        # Start layer index
        self.ui.spinBoxVisibleLayerRangeStart.valueChanged.connect(
            self.changed_visible_range_start.emit
        )
        self.ui.sliderVisibleLayerRangeStart.valueChanged.connect(
            self.changed_visible_range_start.emit
        )

        # End layer index
        self.ui.spinBoxVisibleLayerRangeEnd.valueChanged.connect(
            self.changed_visible_range_end.emit
        )

        self.ui.sliderVisibleLayerRangeEnd.valueChanged.connect(
            # Handles QSlider's inverted appearance
            lambda x: self.changed_visible_range_end.emit(
                self.ui.sliderVisibleLayerRangeEnd.maximum() - x + 1
            )
        )

        # Info layer index
        self.ui.spinBoxInfoLayerIndex.valueChanged.connect(
            self.changed_layer_info_number.emit
        )
        self.ui.sliderInfoLayerIndex.valueChanged.connect(
            self.changed_layer_info_number.emit
        )

        # Actions
        self.ui.actionOpenFile.triggered.connect(self.requested_file_open.emit)
        self.ui.actionClear.triggered.connect(self.requested_clear.emit)
        self.ui.actionQuit.triggered.connect(self.requested_quit.emit)
        self.ui.actionManual.triggered.connect(self.requested_manual.emit)
        self.ui.actionAbout.triggered.connect(self.requested_about.emit)
        QShortcut("Shift+F", self).activated.connect(self.pressed_focus.emit)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        super().dragEnterEvent(event)

        # Accept only files
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        mime_data: QMimeData = event.mimeData()

        # Accept only one file
        if mime_data.hasUrls() and len(mime_data.urls()) == 1:
            event.accept()
            self.dropped_file.emit(event)
        else:
            event.ignore()

    # Slots for signals incoming from Model
    @pyqtSlot(CameraMode)
    def _on_update_camera_mode(self, camera_mode: CameraMode):
        mode_to_radiobutton: Dict[CameraMode, QRadioButton] = {
            CameraMode.SPHERICAL: self.ui.radioButtonCameraModeSpherical,
            CameraMode.FREE: self.ui.radioButtonCameraModeFree,
        }

        target_radiobutton: QRadioButton = mode_to_radiobutton.get(camera_mode)

        if target_radiobutton:
            for radiobutton in mode_to_radiobutton.values():
                is_checked = radiobutton == target_radiobutton
                radiobutton.setChecked(is_checked)
        else:
            raise NotImplementedError(
                f"Camera mode {camera_mode.name} is currently unsupported."
            )

    @pyqtSlot(ColoringGroupDTO)
    def _on_update_coloring_group(self, dto: ColoringGroupDTO):
        # Radio buttons
        mode_to_radiobutton: Dict[ColoringMode, QRadioButton] = {
            ColoringMode.CONSTANT: self.ui.radioButtonColoringDefault,
            ColoringMode.FEEDRATE: self.ui.radioButtonColoringFeedrate,
            ColoringMode.THICKNESS: self.ui.radioButtonColoringThickness,
            ColoringMode.TEMPERATURE: self.ui.radioButtonColoringTemperature,
        }

        target_radiobutton: QRadioButton = mode_to_radiobutton.get(dto.coloring_mode)

        if target_radiobutton:
            for radiobutton in mode_to_radiobutton.values():
                is_checked = radiobutton == target_radiobutton
                radiobutton.setChecked(is_checked)
        else:
            raise NotImplementedError(
                f"Coloring mode {dto.coloring_mode.name} is currently unsupported."
            )

        # Gradient pixmap
        self.ui.labelColorGradient.setPixmap(dto.pixmap)

        # Gradient captions
        self.ui.labelColorGradientLeft.setText(dto.text_left)
        self.ui.labelColorGradientCenter.setText(dto.text_center)
        self.ui.labelColorGradientRight.setText(dto.text_right)

    @pyqtSlot(IntRangeDTO)
    def _on_update_layer_range(self, value: IntRangeDTO):
        # Start layer index
        self.ui.spinBoxVisibleLayerRangeStart.setRange(*value)
        self.ui.sliderVisibleLayerRangeStart.setRange(*value)

        # End layer
        self.ui.spinBoxVisibleLayerRangeEnd.setRange(*value)
        self.ui.sliderVisibleLayerRangeEnd.setRange(*value)

        # Info layer
        self.ui.spinBoxInfoLayerIndex.setRange(*value)
        self.ui.sliderInfoLayerIndex.setRange(*value)

    @pyqtSlot(int)
    def _on_update_visible_layer_range_start(self, value: int):
        self.ui.spinBoxVisibleLayerRangeStart.setValue(value)
        self.ui.sliderVisibleLayerRangeStart.setValue(value)

    @pyqtSlot(int)
    def _on_update_visible_layer_range_end(self, value: int):
        self.ui.spinBoxVisibleLayerRangeEnd.setValue(value)
        # Handle QSlider's inverted appearance
        self.ui.sliderVisibleLayerRangeEnd.setValue(
            self.ui.sliderVisibleLayerRangeEnd.maximum() - value + 1
        )

    @pyqtSlot(ModelInfoDTO)
    def _on_update_model_info(self, dto: ModelInfoDTO):
        """Update Model Info section.

        Parameters
        ----------
        dto: ModelInfoDTO
        """
        self.ui.lineEditModelInfoLayerCount.setText(dto.text_layer_count)
        self.ui.lineEditModelInfoHeight.setText(dto.text_height)
        self.ui.lineEditModelInfoWidth.setText(dto.text_width)
        self.ui.lineEditModelInfoDepth.setText(dto.text_depth)

    @pyqtSlot(LayerInfo)
    def _on_update_layer_info(self, dto: LayerInfoDTO):
        """Update Layer Info section.

        Parameters
        ----------
        dto : LayerInfoDTO
        """
        # Layer number
        self.ui.sliderInfoLayerIndex.setValue(dto.layer_number)
        self.ui.spinBoxInfoLayerIndex.setValue(dto.layer_number)

        # Layer info fields
        self.ui.lineEditLayerInfoZPos.setText(dto.text_z_pos)
        self.ui.lineEditLayerInfoThickness.setText(dto.text_thickness)
        self.ui.lineEditLayerInfoTemp.setText(dto.text_temperature)
        self.ui.lineEditLayerInfoFeedrate.setText(dto.text_feedrate)

    @pyqtSlot(StatusBarMessageDTO)
    def _on_update_status_bar(self, dto: StatusBarMessageDTO):
        """Update status bar message.

        Parameters
        ----------
        dto: StatusBarMessageDTO
        """
        self.ui.statusbar.showMessage(*dto)

    @pyqtSlot(bool)
    def _on_update_model_controls_enabled_state(self, is_enabled: bool):
        self.ui.groupBoxVisibleLayers.setEnabled(is_enabled)
        self.ui.tabWidgetInfo.setEnabled(is_enabled)

    @pyqtSlot(Panda3DWorld)
    def _on_update_panda_3d_world(self, panda_3d_world: Panda3DWorld):
        new_widget = VisualizationWidget(panda3DWorld=panda_3d_world)

        # Remove any existing dialog_info in visualizationFrame
        for i in reversed(self.ui.visualizationFrame.layout().children()):
            self.ui.visualizationFrame.layout().removeItem(i)

        self.ui.visualizationFrame.layout().addWidget(new_widget)
        new_widget.focus_out.connect(self.visualization_lost_focus.emit)
