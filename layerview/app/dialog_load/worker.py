import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional

from panda3d.core import NodePath
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from layerview.gcode.parser import GcodeParser, GcodeSyntaxError
from layerview.visualization.nodes.model import LayerNodeBuilder, ModelManager
from layerview.visualization.point_cloud.errors import EffectorDescentError
from layerview.visualization.point_cloud.model import Model as PointCloudModel
from layerview.visualization.point_cloud.model import (
    ModelBuilder as PointCloudModelBuilder,
)


class WorkerStopRequestedError(Exception):
    pass


class GcodeLoaderWorker(QObject):
    @dataclass
    class DataOutPayload:
        model_node_manager: Optional[ModelManager] = None
        error: Optional[Exception] = None

    # Signals
    finished: pyqtSignal = pyqtSignal()
    data_out: pyqtSignal = pyqtSignal(DataOutPayload)
    update_status: pyqtSignal = pyqtSignal(str)
    update_progress: pyqtSignal = pyqtSignal(float)  # 0.0-1.0

    def __init__(
        self,
        gcode_path: Path,
        nozzle_diam: float,
        parent: typing.Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self.gcode_path: Path = gcode_path
        self.nozzle_diam: float = nozzle_diam

        self._is_stop_requested: bool = False
        self._progress: float = 0.0

    @pyqtSlot()
    def request_stop(self):
        self._is_stop_requested = True

    @pyqtSlot()
    def run(self) -> None:
        self._set_progress(0)

        try:
            # Count lines in G-code file
            with open(self.gcode_path, "r") as file:
                gcode_line_count: int = len(file.readlines())

            # Parse Gcode and build point cloud model
            with open(self.gcode_path, "r") as file:
                command_generator = GcodeParser.command_generator(
                    file, skip_unknown=True
                )
                point_cloud_model = self._build_point_cloud_model(
                    command_generator=command_generator,
                    gcode_line_count=gcode_line_count,
                )

            # Build model node manager
            model_node_name: str = self.gcode_path.stem
            manager: ModelManager = self._build_model_node_manager(
                point_cloud_model=point_cloud_model, name=model_node_name
            )

            self.data_out.emit(
                self.DataOutPayload(model_node_manager=manager, error=None)
            )
        except WorkerStopRequestedError:
            self.data_out.emit(self.DataOutPayload(model_node_manager=None, error=None))
        except (
            GcodeSyntaxError,
            EffectorDescentError,
            Exception,
        ) as error:
            self.data_out.emit(
                self.DataOutPayload(model_node_manager=None, error=error)
            )

        self.finished.emit()

    # Private methods

    def _build_point_cloud_model(
        self, command_generator: Generator, gcode_line_count: int
    ) -> PointCloudModel:
        builder = PointCloudModelBuilder()

        # Handle commands
        # Constitutes 40% of progress
        self.update_status.emit("Parsing G-code and running simulation...")
        parsing_progress_update_step = gcode_line_count // 40 or gcode_line_count
        parsing_progress_increase_val = 0.4 / (
            gcode_line_count / parsing_progress_update_step
        )
        for command_num, command in enumerate(command_generator):
            if self._is_stop_requested:
                raise WorkerStopRequestedError()

            builder.handle_command(command)

            if (command_num + 1) % parsing_progress_update_step == 0:
                self._increase_progress(parsing_progress_increase_val)

        self._set_progress(0.4)

        # Add padding to paths
        for path in [
            path for layer in builder.z_to_layer.values() for path in layer.paths
        ]:
            if self._is_stop_requested:
                raise WorkerStopRequestedError()

            path.add_padding(length=self.nozzle_diam / 2)

        self._increase_progress(0.05)

        # Calc and set layer statistics
        # Constitutes 5% of progress
        self.update_status.emit("Calculating model statistics...")
        for index, layer in enumerate(builder.z_to_layer.values()):
            if self._is_stop_requested:
                raise WorkerStopRequestedError()

            temperatures = builder.layer_to_temperatures[layer]
            layer.temperature_min = min(temperatures)
            layer.temperature_max = max(temperatures)

            feedrates = builder.layer_to_feedrates[layer]
            layer.feedrate_min = min(feedrates)
            layer.feedrate_max = max(feedrates)

        self._increase_progress(0.05)

        model: PointCloudModel = PointCloudModel(
            layer_to_z={layer: z for z, layer in builder.z_to_layer.items()},
            nozzle_diam=self.nozzle_diam,
            priming_layer=builder.priming_layer,
            priming_layer_z=builder.priming_layer_z,
        )

        self._set_progress(0.5)

        if self._is_stop_requested:
            raise WorkerStopRequestedError()

        return model

    def _build_model_node_manager(
        self, point_cloud_model: PointCloudModel, name: str
    ) -> ModelManager:
        model_node_manager = ModelManager()

        model_node: NodePath = NodePath(top_node_name=name)
        model_node_manager._model_node = model_node
        model_node_manager._model_info = point_cloud_model.info
        self._increase_progress(0.05)

        self.update_status.emit("Generating 3D model...")
        # Layer node generation
        # Constitutes 40% of progress
        layer_count: int = len(point_cloud_model.index_to_layer)
        for index, layer in point_cloud_model.index_to_layer.items():
            if self._is_stop_requested:
                raise WorkerStopRequestedError()

            layer_node: NodePath = LayerNodeBuilder.build_node(
                layer=layer,
                nozzle_diam=point_cloud_model._nozzle_diam,
                height=point_cloud_model.get_layer_height(index),
                name=f"{name}L{index}",
            )
            layer_node.reparentTo(model_node)
            layer_node.setPos(0, 0, point_cloud_model.get_layer_z(index))

            model_node_manager.index_to_layer_node[index] = layer_node

            self._increase_progress(0.40 * 1 / layer_count)

        self._set_progress(0.95)

        if point_cloud_model._priming_layer:
            priming_layer_node: NodePath = LayerNodeBuilder.build_node(
                layer=point_cloud_model._priming_layer,
                nozzle_diam=point_cloud_model._nozzle_diam,
                height=point_cloud_model._priming_layer_z,
                name=f"{name}_priming",
            )
            priming_layer_node.reparentTo(model_node)
            priming_layer_node.setPos(0, 0, point_cloud_model._priming_layer_z)

            model_node_manager.priming_layer_node = priming_layer_node

        self._set_progress(1)

        if self._is_stop_requested:
            raise WorkerStopRequestedError()

        return model_node_manager

    def _increase_progress(self, value: float):
        self._set_progress(self._progress + value)

    def _set_progress(self, value: float):
        self._progress = value
        self.update_progress.emit(self._progress)
