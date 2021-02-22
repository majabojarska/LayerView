"""Model (print) node generation."""
import math
from typing import Dict, Optional, Tuple

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTristrips,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LVecBase2d,
    LVecBase3d,
    LVector2d,
    NodePath,
)

from layerview.visualization.linalg import angle_signed, vec_rotated
from layerview.visualization.nodes.builder import NodeBuilder
from layerview.visualization.point_cloud.layer import Layer as Layer
from layerview.visualization.point_cloud.model import Model as Model
from layerview.visualization.point_cloud.model import ModelInfo
from layerview.visualization.point_cloud.path import Path


class ModelManager:
    """Model manager."""

    _model_node: NodePath
    index_to_layer_node: Dict[int, NodePath]
    priming_layer_node: Optional[NodePath]
    _model_info: Optional[ModelInfo]

    def __init__(self):
        self._model_node: Optional[NodePath] = None
        self.index_to_layer_node: Dict[int, NodePath] = {}
        self.priming_layer_node: Optional[NodePath] = None
        self._model_info: Optional[ModelInfo] = None

    def __del__(self):
        # noinspection PyArgumentList
        self.model_node.remove_node()

    @property
    def model_node(self) -> Optional[NodePath]:
        """Returns NodePath for the managed Model."""
        return self._model_node

    @property
    def model_info(self) -> Optional[ModelInfo]:
        """Returns ModelInfo for the managed Model."""
        return self._model_info

    def set_layer_color(self, index: int, color: Tuple[float, float, float, float]):
        """Set color of layer at specified index.

        Parameters
        ----------
        index : int
            Target layer index.
        color : Tuple[float, float, float, float]
            RGBA color to set.
        """
        self.index_to_layer_node[index].setColor(color)

    def show_layer(self, index: int):
        """Show layer at specified index.

        Parameters
        ----------
        index : int
            Target layer index.
        """
        # noinspection PyArgumentList
        self.index_to_layer_node[index].show()

    def hide_layer(self, index: int):
        """Hide layer at specified index.

        Parameters
        ----------
        index : int
            Target layer index.
        """
        # noinspection PyArgumentList
        self.index_to_layer_node[index].hide()

    def show_all_layers(self):
        """Show all layers."""
        for layer_node in self.index_to_layer_node.values():
            # noinspection PyArgumentList
            layer_node.show()

    def hide_all_layers(self):
        """Hide all layers."""
        for layer_node in self.index_to_layer_node.values():
            # noinspection PyArgumentList
            layer_node.hide()

    def show_layer_range_only(self, start: int, end: int):
        """Show specified layer range, exclusively.

        Range [start; end] is inclusive.
        All layers in specified range are shown, others are hidden.

        Parameters
        ----------
        start : int
            Range start layer number, inclusive.
        end : int
            Range end layer number, inclusive.
        """
        to_show = [i for i in self.index_to_layer_node.keys() if start <= i <= end]
        to_hide = [i for i in self.index_to_layer_node.keys() if i not in to_show]

        for i in to_hide:
            self.hide_layer(i)
        for i in to_show:
            self.show_layer(i)


class ModelManagerBuilder:
    """Creates root G-code model node."""

    @staticmethod
    def build_manager(model: Model, name: Optional[str] = "") -> ModelManager:
        """Get new ModelManager.

        Parameters
        ----------
        model : Model
        name : Optional[str]
            Model NodePath name.

        Returns
        -------
        model_node_manager : ModelManager
        """
        model_node_manager = ModelManager()

        model_node: NodePath = NodePath(top_node_name=name)
        model_node_manager._model_node = model_node
        model_node_manager._model_info = model.info

        for index, layer in model.index_to_layer.items():
            layer_node: NodePath = LayerNodeBuilder.build_node(
                layer=layer,
                nozzle_diam=model.nozzle_diam,
                height=model.get_layer_height(index),
                name=f"{name}L{index}",
            )
            layer_node.reparentTo(model_node)
            layer_node.setPos(0, 0, model.get_layer_z(index))

            model_node_manager.index_to_layer_node[index] = layer_node

        if model.priming_layer:
            priming_layer_node: NodePath = LayerNodeBuilder.build_node(
                layer=model.priming_layer,
                nozzle_diam=model.nozzle_diam,
                height=model.priming_layer_z,
                name=f"{name}_priming",
            )
            priming_layer_node.reparentTo(model_node)
            priming_layer_node.setPos(0, 0, model.priming_layer_z)

            model_node_manager.priming_layer_node = priming_layer_node

        return model_node_manager


class LayerNodeBuilder(NodeBuilder):
    """Layer node builder"""

    # noinspection PyArgumentList
    _GEOM_VERTEX_FORMAT = GeomVertexFormat.get_v3n3c4()  # coords + normals + RGBA
    _COLOR_DEFAULT = (0, 60 / 255, 200 / 255, 1)

    @classmethod
    def build_node(
        cls,
        layer: Layer,
        height: float,
        nozzle_diam: float,
        name: str,
    ) -> NodePath:
        """Build layer node.

        Parameters
        ----------
        layer : Layer
            Layer for which the data should be generated and written.
        nozzle_diam : float
            Nozzle diameter.
        height : float
            Layer height, thickness.
        name : str
            Name for generated NodePath.

        Returns
        -------
        NodePath
            Generated NodePath.
        """
        geom_data = cls._get_geom_vertex_data(
            layer=layer, nozzle_diam=nozzle_diam, height=height, name=name
        )
        primitive = cls._get_primitive(layer=layer)

        # Prepare Geom
        geom = Geom(geom_data)
        geom.addPrimitive(primitive)

        # Prepare GeomNode
        geom_node = GeomNode(name)
        geom_node.addGeom(geom)

        # Create NodePath from GeomNode
        node_path = NodePath(geom_node)

        return node_path

    @classmethod
    def _get_geom_vertex_data(
        cls, layer: Layer, nozzle_diam: float, height: float, name: str
    ) -> GeomVertexData:
        """Generate GeomVertexData for the provided Layer.

        Parameters
        ----------
        layer : Layer
            Layer for which the data should be generated and written.
        nozzle_diam : float
            Nozzle diameter.
        height : float
            Layer height, thickness.
        name : str
            Name for generated GeomVertexData

        Returns
        -------
        GeomVertexData
            Generated GeomVertexData.
        """
        geom_vertex_count = sum([len(path) * 4 for path in layer.paths])

        geom_data = GeomVertexData(name, cls._GEOM_VERTEX_FORMAT, Geom.UHStatic)
        geom_data.setNumRows(geom_vertex_count)

        cls._write_geom_data(
            geom_data=geom_data, layer=layer, width=nozzle_diam, height=height
        )

        return geom_data

    @classmethod
    def _write_geom_data(
        cls,
        geom_data: GeomVertexData,
        layer: Layer,
        width: float,
        height: float,
    ):
        """Write layer geom data into the provided GeomVertexData.

        Parameters
        ----------
        geom_data : GeomVertexData
            GeomVertexData to write data into.
        layer : Layer
            Layer for which the data should be generated and written.
        width : float
            Segment width (nozzle diameter).
        height : float
            Segment height (layer height, thickness).
        """
        # Write colors
        cls._write_geom_data_colors(
            geom_data=geom_data,
            layer_vertex_count=cls._get_layer_vertex_count(layer),
        )

        # Write vertex coords and normals
        cls._write_geom_data_coords_and_normals(
            geom_data=geom_data, layer=layer, width=width, height=height
        )

    @classmethod
    def _write_geom_data_coords_and_normals(
        cls,
        geom_data: GeomVertexData,
        layer: Layer,
        width: float,
        height: float,
    ):
        """Write vertex coords and normals into the provided GeomVertexData.

        Parameters
        ----------
        geom_data : GeomVertexData
            GeomVertexData to write coords and normals into.
        layer : Layer
            Layer for which the coords and normals should be generated and written.
        width : float
            Segment width (nozzle diameter).
        height : float
            Segment height (layer height, thickness)
        """
        writer_vertex = GeomVertexWriter(geom_data, "vertex")
        writer_normal = GeomVertexWriter(geom_data, "normal")

        for toolpath in layer.paths:
            for index, path_point in enumerate(toolpath):
                wall_tilt_angle = cls._get_wall_tilt_angle(toolpath, index)
                width_scale_factor = cls._get_wall_width_scale_factor(toolpath, index)

                # VERTEX COORDS

                # Calculate 2D points, rotated
                x_shift = LVector2d(width / 2, 0) * width_scale_factor
                v0_2d = path_point
                v1_2d = vec_rotated(
                    vector=v0_2d - x_shift, pivot=v0_2d, angle=wall_tilt_angle
                )
                v3_2d = vec_rotated(
                    vector=v0_2d + x_shift, pivot=v0_2d, angle=wall_tilt_angle
                )

                # Create 3D vertices. Take Z into account.
                v0_3d = LVecBase3d(*v0_2d, 0)  # v0 3D
                v1_3d = LVecBase3d(*v1_2d, -height / 2)  # v1 3D
                v2_3d = LVecBase3d(*v0_2d, -height)  # v2 3D
                v3_3d = LVecBase3d(*v3_2d, -height / 2)  # v3_3D

                for vertex_coords in [v0_3d, v1_3d, v2_3d, v3_3d]:
                    writer_vertex.addData3d(vertex_coords)

                # VERTEX NORMALS
                if 0 < index < len(toolpath) - 1:  # Intermediate wall
                    n0 = LVecBase3d(0, 0, 1)
                    n1 = LVecBase3d(
                        *(
                            (toolpath[index] - toolpath[index - 1]).normalized()
                            + (toolpath[index] - toolpath[index + 1]).normalized()
                        ),
                        0,
                    ).normalized()
                    n2 = -n0
                    n3 = -n1
                else:  # Start or end wall
                    if index == 0:  # Start wall
                        # v[0] - v[1]
                        ref_vec: LVecBase2d = LVecBase2d(*(toolpath[1] - toolpath[0]))
                        normal_rot_angle = math.pi / -4
                    else:  # index == toolpath_point_count-1: # End wall
                        # v[-1] - v[-2]
                        ref_vec: LVecBase2d = LVecBase2d(*(toolpath[-1] - toolpath[-2]))
                        normal_rot_angle = math.pi / 4

                    ref_vec.normalize()

                    # Top and bottom
                    n0 = LVecBase3d(*ref_vec, 1).normalized()
                    n2 = LVecBase3d(*ref_vec, -1).normalized()

                    # Sides
                    n1 = LVecBase3d(
                        *vec_rotated(
                            vector=ref_vec, pivot=v1_2d, angle=normal_rot_angle
                        ),
                        0,
                    )
                    n3 = LVecBase3d(
                        *vec_rotated(
                            vector=ref_vec, pivot=v1_2d, angle=normal_rot_angle
                        ),
                        0,
                    )

                for normal in [n0, n1, n2, n3]:
                    writer_normal.addData3d(normal)

    @classmethod
    def _write_geom_data_colors(
        cls,
        geom_data: GeomVertexData,
        layer_vertex_count: int,
        color: Tuple[float, float, float, float] = _COLOR_DEFAULT,
    ):
        """Write color data into the provided GeomVertexData.

        Parameters
        ----------
        geom_data : GeomVertexData
            GeomVertexData to write color data into.
        layer_vertex_count : int
            Total vertex count in layer.
        color : Tuple[float, float, float, float]
            Target vertex color.
        """
        writer_color = GeomVertexWriter(geom_data, "color")

        for _ in range(layer_vertex_count):
            writer_color.addData4(color)

    @classmethod
    def _get_primitive(cls, layer: Layer) -> GeomTristrips:
        """Generate GeomTristrips primitive for provided layer."""
        primitive = GeomTristrips(Geom.UHStatic)

        cur_point_num_in_layer = 0

        # Iterate over paths in layer
        for path in layer.paths:
            segment_count = len(path) - 1
            path_start_point_index = (
                cur_point_num_in_layer * 4
            )  # Relative to first point in first path in layer

            # Start cap
            primitive.addVertices(*[path_start_point_index + i for i in [0, 1, 3, 2]])
            primitive.closePrimitive()

            # Segment walls
            for segment_index in range(segment_count):
                v_start_index = path_start_point_index + segment_index * 4

                # Zigzag around segment walls: 0, 4, 1, 5, 2, 6, 3, 7, 0, 4
                for i in range(v_start_index, v_start_index + 4):
                    primitive.addVertex(i)
                    primitive.addVertex(i + 4)

                primitive.addVertex(v_start_index)
                primitive.addVertex(v_start_index + 4)

                primitive.closePrimitive()

            # End cap
            end_wall_start_index = (cur_point_num_in_layer + segment_count) * 4
            primitive.addVertices(*[end_wall_start_index + i for i in [0, 3, 1, 2]])
            primitive.closePrimitive()

            cur_point_num_in_layer += len(path)

        return primitive

    @classmethod
    def _get_wall_width_scale_factor(cls, toolpath: Path, i: int) -> float:
        """Return wall width scale factor.

        Parameters
        ----------
        toolpath : Path
            Toolpath.
        i : int
            Index of wall in toolpath.

        Returns
        -------
        float
            Wall width scale factor for i-th wall in toolpath.
        """
        if 0 < i < len(toolpath) - 1:  # Intermediate point
            angle_delta = angle_signed(
                toolpath[i] - toolpath[i - 1],
                toolpath[i + 1] - toolpath[i],
            )
            return 1.0 + abs(math.sin(angle_delta)) * (math.sqrt(2) - 1)
        return 1.0

    @classmethod
    def _get_wall_tilt_angle(cls, toolpath: Path, i: int) -> float:
        """Returns wall tilt angle for specified point_cloud point.

        Positive angles are counterclockwise, negative are clockwise.

        Parameters
        ----------
        toolpath : Path
            2D point_cloud
        i : int
            Wall index (path vertex index).

        Returns
        -------
        rotation_angle : float
            Wall rotation angle for segment wall corresponding to vertex v.
        """
        # Aliases
        v_count = len(toolpath)
        v = toolpath

        if 0 < i < v_count - 1:  # Intermediate point, most probable case
            target_vec = (v[i] - v[i - 1]).normalized() + (v[i + 1] - v[i]).normalized()
        elif i == 0:  # Start point
            target_vec = v[1] - v[0]
        elif i == v_count - 1:  # End point
            target_vec = v[i] - v[i - 1]
        else:  # Out of range
            raise IndexError("Index is out of vertices range.")

        base_vec = LVecBase2d(0, 1)

        tilt_angle = angle_signed(base_vec, target_vec)

        return tilt_angle

    @classmethod
    def _get_layer_point_count(cls, layer: Layer) -> int:
        """Return total point count in provided layer."""
        return sum([len(path) for path in layer.paths])

    @classmethod
    def _get_layer_vertex_count(cls, layer: Layer) -> int:
        """Return expected total vertex count in provided layer."""
        return cls._get_layer_point_count(layer) * 4
