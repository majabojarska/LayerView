from pathlib import Path
from typing import List, Optional, Union

from PyQt5.QtCore import QMimeData, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDropEvent, QFocusEvent
from PyQt5.QtWidgets import QFileDialog

from layerview.app.dialog_info.dialog import InfoDialog
from layerview.app.dialog_load.dialog import GcodeLoadingDialog
from layerview.app.dialog_load.worker import GcodeLoaderWorker
from layerview.app.main_window.dto import StatusBarMessageDTO
from layerview.app.main_window.model import Model
from layerview.app.main_window.view import View
from layerview.common.mixins import MixinMarkdown
from layerview.visualization.nodes.model import ModelManager
from layerview.visualization.world.world import CameraMode, ColoringMode


class Controller(QObject):
    _GCODE_FILE_EXTENSIONS: List[str] = ["gcode", "GCODE", "gco", "g"]

    _recv_worker_data_out_payload: pyqtSignal = pyqtSignal(
        GcodeLoaderWorker.DataOutPayload
    )

    def __init__(self, model: Model, view: View, initial_gcode: Optional[Path] = None):
        super().__init__()

        self.model: Model = model
        self.view: View = view
        self._initial_gcode: Optional[Path] = initial_gcode

        self._recv_worker_data_out_payload.connect(
            self._on_gcode_loader_data_out_payload
        )

        # Connect view's signals to own slots
        self._setup_slots()

        # Set App to initial state
        self.model.init_visualization()

        self.model.set_camera_mode(CameraMode.SPHERICAL)
        self.model.set_coloring_mode(ColoringMode.CONSTANT)

        self._reset()

    def show(self):
        self.view.show()

        if self._initial_gcode is not None:
            # Load initial G-code
            self._load_gcode_file(gcode_path=self._initial_gcode)
            self._initial_gcode = None

    def teardown(self):
        self.view.close()

    def _setup_slots(self):
        # Widgets
        self.view.changed_camera_mode.connect(self._on_change_camera_mode)
        self.view.pressed_focus.connect(self._on_press_focus)
        self.view.changed_coloring_mode.connect(self._on_change_coloring_mode)
        self.view.changed_visible_range_start.connect(
            self._on_change_visible_range_start
        )
        self.view.changed_visible_range_end.connect(self._on_change_visible_range_end)
        self.view.changed_layer_info_number.connect(self._on_change_layer_info_number)
        self.view.changed_gradient_pixmap_size.connect(
            self._on_change_gradient_pixmap_size
        )
        self.view.resized_window.connect(self._on_window_resize)

        # Actions
        self.view.requested_file_open.connect(self._on_request_file_open)
        self.view.requested_clear.connect(self._on_request_clear)
        self.view.requested_quit.connect(self._on_request_quit)
        self.view.requested_about.connect(self._on_request_about)
        self.view.requested_manual.connect(self._on_request_manual)

        # Events
        self.view.dropped_file.connect(self._on_drop_file)
        self.view.visualization_lost_focus.connect(self._on_visualization_focus_out)

    def _reset(self):
        """Reset application to initial state."""
        # Disable controls
        self.model.update_model_controls_enabled_state.emit(False)

        # Reset model
        self.model.reset()

    # Slots

    @pyqtSlot(CameraMode)
    def _on_change_camera_mode(self, camera_mode: CameraMode):
        self.model.set_camera_mode(camera_mode)

    @pyqtSlot()
    def _on_press_focus(self):
        self.model.focus_on_model()

    @pyqtSlot(ColoringMode)
    def _on_change_coloring_mode(self, coloring_mode: ColoringMode):
        self.model.set_coloring_mode(coloring_mode)

    @pyqtSlot(int)
    def _on_change_visible_range_start(self, layer_num: int):
        # Use current value by default
        new_visible_range_start = self.model.visible_range_start

        if layer_num <= self.model.visible_range_end:
            try:
                self._validate_layer_num(layer_num)
                new_visible_range_start = layer_num
            except ValueError:
                pass

        self.model.set_visible_range_start(new_visible_range_start)

    @pyqtSlot(int)
    def _on_change_visible_range_end(self, layer_num: int):
        # Use current value by default
        new_visible_range_end = self.model.visible_range_end

        if layer_num >= self.model.visible_range_start:
            try:
                self._validate_layer_num(layer_num)
                new_visible_range_end = layer_num
            except ValueError:
                pass

        self.model.set_visible_range_end(new_visible_range_end)

    @pyqtSlot(int)
    def _on_change_layer_info_number(self, layer_num: int):
        try:
            self._validate_layer_num(layer_num)
            self.model.set_layer_info_number(layer_num)
        except ValueError:
            self.model.set_layer_info_number(self.model.layer_info_number)

    @pyqtSlot(tuple)
    def _on_change_gradient_pixmap_size(self, size: tuple):
        self.model.set_gradient_pixmap_size(size=size)

    @pyqtSlot()
    def _on_window_resize(self):
        self.model.handle_window_resize()

    # Action signal slots

    @pyqtSlot()
    def _on_request_file_open(self):
        gcode_path: Optional[Path] = self._gcode_file_dialog()

        if gcode_path:
            self._load_gcode_file(gcode_path=gcode_path)

    @pyqtSlot()
    def _on_request_clear(self):
        self._reset()

    @pyqtSlot()
    def _on_request_quit(self):
        self.teardown()

    @pyqtSlot()
    def _on_request_manual(self):
        dlg = InfoDialog.from_md_file(
            parent=self.view,
            title="Manual",
            path_md=(
                Path(__file__).parent / "../dialog_info/res/md/manual.md"
            ).absolute(),
            width=900,
            height=600,
        )
        dlg.show()

    @pyqtSlot()
    def _on_request_about(self):
        dlg = InfoDialog.from_md_file(
            parent=self.view,
            title="About",
            path_md=(
                Path(__file__).parent / "../dialog_info/res/md/about.md"
            ).absolute(),
            width=500,
            height=400,
        )
        dlg.show()

    @pyqtSlot(QDropEvent)
    def _on_drop_file(self, event: QDropEvent):
        mime_data: QMimeData = event.mimeData()
        path: str = mime_data.urls()[0].toLocalFile()

        if any(path.endswith(ext) for ext in self._GCODE_FILE_EXTENSIONS):
            self._load_gcode_file(gcode_path=path)

    @pyqtSlot(QFocusEvent)
    def _on_visualization_focus_out(self, event: QFocusEvent):
        self.model.handle_visualization_focus_out()

    # Other slots - controller scope only

    @pyqtSlot(GcodeLoaderWorker.DataOutPayload)
    def _on_gcode_loader_data_out_payload(self, dto: GcodeLoaderWorker.DataOutPayload):
        self.model.update_status_bar.emit(StatusBarMessageDTO(text=""))

        if dto.model_node_manager and not dto.error:
            manager: ModelManager = dto.model_node_manager

            # Update model
            self.model.set_model_node_manager(manager)
            self.model.update_status_bar.emit(
                StatusBarMessageDTO(text="Done!", duration=3000)
            )
            self.model.update_model_controls_enabled_state.emit(True)

        elif not dto.model_node_manager and dto.error:
            markdown: str = (
                dto.error.as_markdown()
                if isinstance(dto.error, MixinMarkdown)
                else str(dto.error)
            )

            dlg = InfoDialog(
                title="Error",
                markdown=markdown,
                width=200,
                height=100,
                parent=self.view,
            )
            dlg.setModal(True)
            dlg.show()
        elif not dto.model_node_manager and not dto.error:
            self.model.update_status_bar.emit(
                StatusBarMessageDTO(text="G-code loading cancelled.", duration=3000)
            )

    # Helper methods

    def _load_gcode_file(self, gcode_path: Union[Path, str]):
        gcode_path: Path = Path(gcode_path).absolute()

        self.model.set_status_bar_message(StatusBarMessageDTO(text="Loading G-code..."))

        loading_dialog = GcodeLoadingDialog(
            gcode_path=gcode_path,
            nozzle_diam=self.model.NOZZLE_DIAM_DEFAULT,
            parent=self.view,
        )
        loading_dialog.data_out.connect(
            lambda payload: self._recv_worker_data_out_payload.emit(payload)
        )
        loading_dialog.show()

    def _validate_layer_num(self, layer_num: int):
        """Validate layer number.

        Validation is omitted if self.model.model_info is None.

        Parameters
        ----------
        layer_num : int
            Layer number to validate.

        Raises
        ------
        ValueError
            If self.model.model_info is not None and layer_num is not
            present in model_info.
        """
        if self.model.model_info and not (
            self.model.model_info.layer_num_min
            <= layer_num
            <= self.model.model_info.layer_num_max
        ):
            raise ValueError(
                f"Layer number {layer_num} is not present in {self.model.model_info}."
            )

    def _gcode_file_dialog(self) -> Optional[Path]:
        """Open file dialog for G-code files.

        Returns
        -------
        file_path : Path or None
            Path if a file was chosen via the file dialog.
            None if the file dialog was cancelled.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        caption = "Open G-code file"
        ext_filter = (
            f"G-code files "
            f"({' '.join([f'*.{ext}' for ext in self._GCODE_FILE_EXTENSIONS])})"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            parent=self.view.centralWidget(),
            caption=caption,
            filter=ext_filter,
            options=options,
        )

        if file_path:
            return Path(file_path).absolute()
        return None
