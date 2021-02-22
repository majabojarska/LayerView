"""Abstraction of model in point cloud."""
from __future__ import annotations

from functools import cached_property, lru_cache, reduce
from statistics import mean
from typing import Dict, List, Optional, Tuple

from panda3d.core import LVector2d, LVector3d

from layerview.gcode import commands
from layerview.gcode.gcode import Gcode
from layerview.simulation.machine import Machine
from layerview.visualization.point_cloud.boundaries import BoundingBox3D
from layerview.visualization.point_cloud.errors import (
    LateEffectorDescentError,
    PostPrimingDescentError,
)
from layerview.visualization.point_cloud.interpolation import CircularArcInterpolator
from layerview.visualization.point_cloud.layer import Layer
from layerview.visualization.point_cloud.path import Path


class Model:
    """Represents a point cloud model."""

    def __init__(
        self,
        layer_to_z: Dict[Layer, float],
        nozzle_diam: float,
        priming_layer: Optional[Layer] = None,
        priming_layer_z: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        layer_to_z : Dict[Layer, float]
            Dictionary mapping each layer to a Z position.
        nozzle_diam : float
            Nozzle diameter.
        priming_layer : Optional[Layer]
            Priming layer.
        priming_layer_z : Optional[float]
            Z position of priming layer.
        """
        self._layer_to_z: Dict[Layer, float] = layer_to_z
        self.index_to_layer: Dict[int, Layer] = {
            index + 1: layer
            for index, layer in enumerate(
                [k for k, v in sorted(layer_to_z.items(), key=lambda item: item[1])]
            )
        }
        self._nozzle_diam: float = nozzle_diam
        self._priming_layer_z: Optional[float] = priming_layer_z
        self._priming_layer: Optional[Layer] = priming_layer

    def get_layer_z(self, index: int) -> float:
        """Return Z position of layer at specified index.

        Parameters
        ----------
        index : int
            Index of layer to return the Z position for.

        Returns
        -------
        float
            Z position of layer at specified index.
        """
        return self._layer_to_z[self.index_to_layer[index]]

    def get_layer_height(self, index: int) -> float:
        """Return height (top-bottom) of layer at specified index.

        The calculated height is rounded to 3 decimal places.

        Parameters
        ----------
        index : int
            Index of layer to return the height for.

        Returns
        -------
        float
            Height of layer at specified index.
        """
        target_layer_z = self._layer_to_z[self.index_to_layer[index]]
        if index == 1:
            return target_layer_z
        diff = (
            self._layer_to_z[self.index_to_layer[index]]
            - self._layer_to_z[self.index_to_layer[index - 1]]
        )
        # Round to 3 decimal places
        return round(diff, 3)

    def get_boundaries(self, with_priming: bool) -> BoundingBox3D:
        """Return this Model's boundaries.

        Parameters
        ----------
        with_priming : bool
            If True, the priming layer is taken into account (if present).
            Otherwise, the priming layer is ignored.

        Returns
        -------
        BoundingBox3D
            This Model's boundaries.
        """
        if with_priming:
            return self._boundaries_with_priming
        return self._boundaries_without_priming

    @cached_property
    def _boundaries_with_priming(self) -> BoundingBox3D:
        """Return this Model's boundaries with the priming layer."""

        if not self._priming_layer:
            return self._boundaries_without_priming

        # Calc new boundaries with priming layer in mind
        point_min = self._boundaries_without_priming.point_min.fmin(
            LVector3d(self._priming_layer.boundaries.point_min, 0)
        )
        point_max = self._boundaries_without_priming.point_max.fmax(
            LVector3d(self._priming_layer.boundaries.point_max, 0)
        )
        return BoundingBox3D(point_min=point_min, point_max=point_max)

    @cached_property
    def _boundaries_without_priming(self) -> BoundingBox3D:
        """Return this Model's boundaries without the priming layer."""
        if self.index_to_layer:
            layer_points_min, layer_points_max = zip(
                *[
                    (layer.boundaries.point_min, layer.boundaries.point_max)
                    for layer in self._layer_to_z.keys()
                ]
            )

            layers_min = reduce(lambda a, b: a.fmin(b), layer_points_min)
            layers_max = reduce(lambda a, b: a.fmax(b), layer_points_max)

            point_min = LVector3d(
                x=layers_min.x,
                y=layers_min.y,
                z=0,
            )

            point_max = LVector3d(
                x=layers_max.x,
                y=layers_max.y,
                z=max(self._layer_to_z.values()),
            )

            return BoundingBox3D(point_min=point_min, point_max=point_max)

        # No layers
        return BoundingBox3D.null_object()

    @cached_property
    def info(self) -> ModelInfo:
        """Return ModelInfo for this Model."""
        return ModelInfo.from_model(model=self)

    @property
    def priming_layer(self) -> Optional[Layer]:
        """Return priming layer for this Model."""
        return self._priming_layer

    @property
    def nozzle_diam(self) -> float:
        """Return nozzle diameter for this Model."""
        return self._nozzle_diam

    @property
    def priming_layer_z(self) -> Optional[float]:
        """Return priming layer Z position for this Model."""
        return self._priming_layer_z


class LayerInfo:
    """Represents information about a layer."""

    def __init__(self):
        self.temperature_min: Optional[float] = None
        self.temperature_max: Optional[float] = None
        self.feedrate_min: Optional[float] = None
        self.feedrate_max: Optional[float] = None


class ModelInfo:
    """Represents information about a model."""

    def __init__(self):
        self._index_to_layer_info: Dict[int, LayerInfo] = {}
        self._index_to_z: Dict[int, float] = {}

        self.boundaries: Optional[BoundingBox3D] = None
        self.boundaries_without_priming: Optional[BoundingBox3D] = None

    @staticmethod
    def from_model(model: Model) -> ModelInfo:
        """Builds ModelInfo from specified Model instance.

        Parameters
        ----------
        model : Model
            Model for which the ModelInfo is built.

        Returns
        -------
        ModelInfo
            Built ModelInfo instance.
        """
        info = ModelInfo()

        # Fill layer info
        for index, layer in model.index_to_layer.items():
            layer_info = LayerInfo()

            layer_info.temperature_min = layer.temperature_min
            layer_info.temperature_max = layer.temperature_max
            layer_info.feedrate_min = layer.feedrate_min
            layer_info.feedrate_max = layer.feedrate_max

            info._index_to_layer_info[index] = layer_info

        # Fill model info
        info.boundaries = model.get_boundaries(with_priming=True)
        info.boundaries_without_priming = model.get_boundaries(with_priming=False)
        info._index_to_z = {
            index: model.get_layer_z(index) for index in model.index_to_layer.keys()
        }

        return info

    @property
    def index_to_layer_info(self) -> Dict[int, LayerInfo]:
        """Return dict that maps layer index to corresponding LayerInfo instance.

        Returns
        -------
        LayerInfo
            Maps layer index to corresponding LayerInfo instance.
        """
        return self._index_to_layer_info

    def get_layer_info(self, index: int) -> LayerInfo:
        """Return LayerInfo for layer at specified index.

        Parameters
        ----------
        index : int
            Index of layer to return the LayerInfo for.

        Returns
        -------
        LayerInfo
            LayerInfo for layer at specified index.
        """
        return self._index_to_layer_info[index]

    def get_layer_z(self, index: int) -> float:
        """Return Z position of layer at specified index.

        Parameters
        ----------
        index : int
            Index of layer to return the Z position for.

        Returns
        -------
        float
            Z position of layer at specified index.
        """
        return self._index_to_z[index]

    def get_layer_height(self, index: int) -> float:
        """Return height (aka thickness) of layer at specified index.

        Parameters
        ----------
        index : int
            Index of layer to return the height for.

        Returns
        -------
        float
            Height of layer at specified index.
        """
        if index == 1:
            return self._index_to_z[index]
        return self._index_to_z[index] - self._index_to_z[index - 1]

    @property
    def layer_count(self) -> int:
        """Return total layer count."""
        return len(self._index_to_layer_info)

    @property
    def layer_num_min(self) -> int:
        """Return minimum layer number (index)."""
        return min(self._index_to_layer_info.keys())

    @property
    def layer_num_max(self) -> int:
        """Return maximum layer number (index)."""
        return max(self._index_to_layer_info.keys())

    @property
    def layer_range(self) -> Tuple[int, int]:
        """Return available layer number (index) range, inclusive."""
        return self.layer_num_min, self.layer_num_max

    @property
    def feedrate_min(self) -> float:
        """Return minimum feedrate."""
        return min(
            [
                layer_info.feedrate_min
                for layer_info in self._index_to_layer_info.values()
            ]
        )

    @property
    def feedrate_max(self) -> float:
        """Return maximum feedrate."""
        return max(
            [
                layer_info.feedrate_max
                for layer_info in self._index_to_layer_info.values()
            ]
        )

    @property
    def temperature_min(self) -> float:
        """Return maximum nozzle temperature."""
        return min(
            [
                layer_info.temperature_min
                for layer_info in self._index_to_layer_info.values()
            ]
        )

    @property
    def temperature_max(self) -> float:
        """Return maximum nozzle temperature."""
        return max(
            [
                layer_info.temperature_max
                for layer_info in self._index_to_layer_info.values()
            ]
        )

    @property
    def layer_height_min(self) -> float:
        """Return minimum layer height (aka thickness)."""
        return min(self._heights)

    @property
    def layer_height_max(self) -> float:
        """Return maximum layer height (aka thickness)."""
        return max(self._heights)

    @property
    def _heights(self) -> List[float]:
        """Return list of layer heights (aka thicknesses)."""
        return [
            self.get_layer_height(index) for index in self._index_to_layer_info.keys()
        ]


class ModelBuilder:
    """Point cloud model builder."""

    def __init__(self):
        self.machine = Machine(skip_unknown=True)

        self.z_to_layer: Dict[float, Layer] = {}
        self._last_layer_z: float = 0
        self._is_after_post_priming_descent: bool = False
        self.priming_layer: Optional[Layer] = None
        self.priming_layer_z: Optional[float] = None
        self.layer_to_feedrates: Dict[Layer, List[float]] = {}
        self.layer_to_temperatures: Dict[Layer, List[float]] = {}

    @staticmethod
    def build_model(gcode: Gcode, nozzle_diam: float) -> Model:
        """Build 3D model, based on the provided Gcode and nozzle diameter.

        Parameters
        ----------
        gcode : Gcode
            Gcode object to generate the point_cloud model from.
        nozzle_diam : float
            Nozzle diameter.

        Returns
        -------
        model : Model
            Generated point_cloud Model.
        """
        builder = ModelBuilder()

        for command in gcode:
            builder.machine.handle_command(command=command)

            if isinstance(command, commands.Move):
                builder._handle_move(command)

        for path in [
            path for layer in builder.z_to_layer.values() for path in layer.paths
        ]:
            path.add_padding(length=nozzle_diam / 2)

        # Calc and set layer statistics
        for layer in builder.z_to_layer.values():
            temperatures = builder.layer_to_temperatures[layer]
            layer.temperature_min = min(temperatures)
            layer.temperature_max = max(temperatures)
            layer.temperature_avg = mean(temperatures)

            feedrates = builder.layer_to_feedrates[layer]
            layer.feedrate_min = min(feedrates)
            layer.feedrate_max = max(feedrates)
            layer.feedrate_avg = mean(temperatures)

        model = Model(
            layer_to_z={layer: z for z, layer in builder.z_to_layer.items()},
            nozzle_diam=nozzle_diam,
            priming_layer=builder.priming_layer,
            priming_layer_z=builder.priming_layer_z,
        )

        return model

    def handle_command(self, command: commands.Command):
        """Handle command.

        Parameters
        ----------
        command : commands.Command
            Command to handle.
        """
        self.machine.handle_command(command)
        if isinstance(command, commands.Move):
            self._handle_move(command)

    def _handle_move(self, command: commands.Move):
        """Handle Move command.

        Parameters
        ----------
        command : commands.Move
            Move command to handle.

        Raises
        ------
        TypeError
            If `command` is not a Move instance.
        """
        # Get position
        pos_prev = self.machine.state_previous.position_abs
        pos_cur = self.machine.state_current.position_abs

        if not isinstance(command, commands.Move):
            raise TypeError(
                f"Expected instance of {commands.Move}, got {type(command)}."
            )

        # Check if command is a layer printing move
        if (
            # Stayed on layer during move?
            pos_prev.z == pos_cur.z
            # Extruder value increased?
            and self.machine.state_current.extruder_abs
            > self.machine.state_previous.extruder_abs
            # Provided X or Y value?
            and any([command.x, command.y])
        ):
            # Add points
            target_layer_z = pos_cur.z
            target_layer = self.get_layer_at_z(layer_z=target_layer_z)
            self._last_layer_z = target_layer_z

            source = pos_prev.xy
            destination = pos_cur.xy

            if isinstance(command, commands.LineMove):
                self.add_segment_to_layer(
                    layer=target_layer, source=source, destination=destination
                )
            elif isinstance(command, commands.ArcMove):
                pivot = LVector2d(command.i, command.j)
                is_clockwise = isinstance(command, commands.G2)
                points_interpolated = CircularArcInterpolator.interpolate(
                    src=source,
                    dst=destination,
                    pivot=pivot,
                    is_clockwise=is_clockwise,
                    max_err=0.05,
                )
                for i in range(len(points_interpolated) - 1):
                    self.add_segment_to_layer(
                        layer=target_layer,
                        source=points_interpolated[i],
                        destination=points_interpolated[i + 1],
                    )

            # Save feedrate and temperature
            self.layer_to_temperatures[target_layer].append(
                self.machine.state_current.temp_extruder
            )
            self.layer_to_feedrates[target_layer].append(
                self.machine.state_current.feedrate
            )

    @lru_cache(maxsize=128)
    def get_layer_at_z(self, layer_z: float) -> Layer:
        """Return layer at specified Z position.

        Parameters
        ----------
        layer_z : float
            Z position of layer to return.

        Returns
        -------
        Layer
            Layer at specified Z position.

        Raises
        ------
        PostPrimingDescentError
            If a post priming effector descent occurs.
        LateEffectorDescentError
            If a late effector descent occurs.
        """
        target_layer = self.z_to_layer.get(layer_z)

        if not target_layer:
            if layer_z < self._last_layer_z:
                # Z Descent occurred
                if self._is_after_post_priming_descent:
                    # Is after post priming descent.
                    raise PostPrimingDescentError(
                        cur_layer_z=layer_z, prev_layer_z=self._last_layer_z
                    )
                elif len(self.z_to_layer) > 1:
                    # Is NOT after post priming descent, but descended after layer>1
                    raise LateEffectorDescentError(
                        cur_layer_z=layer_z,
                        prev_layer_z=self._last_layer_z,
                        prev_layer_count=len(self.z_to_layer),
                    )

                # Set layer at _max_layer_z as priming layer.
                self.priming_layer = self.z_to_layer.pop(self._last_layer_z)
                self.priming_layer_z = self._last_layer_z
                self._is_after_post_priming_descent = True

            # Create new layer
            target_layer = Layer()
            self.z_to_layer[layer_z] = target_layer
            # Statistics collection
            self.layer_to_temperatures[target_layer] = []
            self.layer_to_feedrates[target_layer] = []

        return target_layer

    @staticmethod
    def add_segment_to_layer(layer: Layer, source: LVector2d, destination: LVector2d):
        """Add segment to specified layer.

        If layer does not contain any previous paths or the last path's point is not
        equal to the provided source point, a new path is initialized.
        Otherwise the destination point is appended to the end of layer's last path.

        Parameters
        ----------
        layer : Layer
            Layer to add the segment to.
        source : LVector2d
            Segment's source point.
        destination : LVector2d
            Segment's destination point.
        """
        if not layer.paths or source != layer.paths[-1][-1]:
            # Create new path
            layer.paths.append(Path(point_first=source, point_second=destination))
        else:
            # Continue last path
            layer.paths[-1].append(destination)
