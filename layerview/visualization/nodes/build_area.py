"""Build area node generation."""
import math
from pathlib import Path
from typing import Optional

from direct.showbase.Loader import Loader
from panda3d.core import (
    Filename,
    Geom,
    GeomLines,
    GeomLinestrips,
    GeomNode,
    GeomPrimitive,
    GeomTristrips,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    LVecBase3d,
    LVector2d,
    LVector3d,
    NodePath,
    Texture,
    TextureStage,
    TransparencyAttrib,
)

from layerview.visualization.nodes.builder import NodeBuilder


class BuildAreaNodeBuilder(NodeBuilder):
    """Build area node builder."""

    @staticmethod
    def build_node(
        loader: Loader,
        size: LVector3d = None,
        size_min: Optional[LVector3d] = None,
        name: str = "build_area",
    ) -> NodePath:
        """Build build area NodePath.

        Parameters
        ----------
        loader : Loader
            Panda3D asset loader.
        size : LVector3D
            Build area size.
        size_min : Optional[LVector3D]
            Minimum allowed builder area size.
            Serves as bottom limit on a selective, per-axis basis.
        name : str
            Name for the returned NodePath.

        Returns
        -------
        NodePath
            Built build area NodePath.
        """
        if size_min:
            size_sanitized = BuildAreaNodeBuilder._size_max_elem_wise(
                size=size, size_min=size_min
            )
        else:
            size_sanitized = size

        # Child nodes
        bounding_box_node: GeomNode = BoundingBoxNodeBuilder.build_node(
            size=size_sanitized, name="bounding_box"
        )
        build_plate_node: GeomNode = BuildPlateNodeBuilder.build_node(
            loader=loader, build_plate_size=size_sanitized.xy, name="build_plate"
        )

        # Group together
        node_path: NodePath = NodePath(top_node_name=name)
        build_plate_node.reparentTo(node_path)
        bounding_box_node.reparentTo(node_path)

        return node_path

    @staticmethod
    def _size_max_elem_wise(size: LVector3d, size_min: LVector3d) -> LVector3d:
        """Returns element-wise maximum between `size` and `size_min`."""
        return LVector3d(*[max([size[i], size_min[i]]) for i in range(3)])


class BuildPlateNodeBuilder(NodeBuilder):
    """Build plate node builder."""

    # noinspection PyTypeChecker
    _PATH_TEXTURE = Filename.fromOsSpecific(
        str(
            (Path(__file__).parent / "assets/textures/layerview.png")
            .absolute()
            .as_posix()
        )
    )
    _TEXTURE_OPACITY = 0.3
    _TEXTURE_SCALE = 0.75
    # noinspection PyArgumentList
    _GEOM_VERTEX_FORMAT_GRID = GeomVertexFormat.get_v3c4()
    # noinspection PyArgumentList
    _VERTEX_FORMAT_PLATE = GeomVertexFormat.get_v3n3c4()

    _GRID_SPACING = 10  # mm
    _GRID_COLOR = (0, 0, 0, 1)

    @classmethod
    def build_node(
        cls,
        loader: Loader,
        build_plate_size: LVector2d,
        grid_spacing: float = _GRID_SPACING,
        name: str = "",
    ) -> NodePath:
        """Build build area NodePath.

        Parameters
        ----------
        loader : Loader
            Panda3D asset loader.
        build_plate_size : LVector2D
            Build plate size.
        grid_spacing: float
            Build plate grid spacing.
            Defaults to _GRID_SPACING.
        name : str
            Name for the returned NodePath.

        Returns
        -------
        NodePath
            Built build plate NodePath.
        """
        # X
        geom_data_x = cls._get_geom_data_grid_x(build_plate_size)
        primitive_x = cls._get_primitive_linestrips(
            line_count=int(build_plate_size.x / grid_spacing) - 1
        )
        geom_x = Geom(geom_data_x)
        geom_x.addPrimitive(primitive_x)

        # Y
        geom_data_y = cls._get_geom_data_grid_y(build_plate_size)
        primitive_y = cls._get_primitive_linestrips(
            line_count=int(build_plate_size.y / grid_spacing) - 1
        )
        geom_y = Geom(geom_data_y)
        geom_y.addPrimitive(primitive_y)

        # Assemble into one NodePath
        node_path = NodePath(top_node_name="")

        geom_node_x = GeomNode(f"{name}_x")
        geom_node_x.addGeom(geom_x)
        node_path.attachNewNode(geom_node_x)

        geom_node_y = GeomNode(f"{name}_y")
        geom_node_y.addGeom(geom_y)
        node_path.attachNewNode(geom_node_y)

        node_path_plate = cls._get_node_plate(
            loader=loader, build_plate_size=build_plate_size
        )
        node_path_plate.reparentTo(node_path)

        return node_path

    @staticmethod
    def _get_primitive_linestrips(line_count: int) -> GeomPrimitive:
        """Generate GeomLinestrips primitive for build plate grid.

        Parameters
        ----------
        line_count : int
            Line count for the generated GeomLinestrips primitive.

        Returns
        -------
        GeomLinestrips
            Generated primitive.
        """
        primitive = GeomLinestrips(Geom.UHStatic)

        for i in range(line_count):
            primitive.addVertices(2 * i, 2 * i + 1)
            primitive.closePrimitive()

        return primitive

    @classmethod
    def _get_geom_data_grid_x(
        cls,
        build_plate_size: LVector2d,
        grid_spacing: float = _GRID_SPACING,
        name: str = "",
    ) -> GeomVertexData:
        """Generate GeomVertexData for build plate grid in X axis.

        Parameters
        ----------
        build_plate_size : LVector2d
            Build plate size.
        grid_spacing : float
            Grid spacing; distance between successive grid lines.
        name : str
            Generated GeomVertexData name.
        """
        geom_data = GeomVertexData(name, cls._GEOM_VERTEX_FORMAT_GRID, Geom.UHStatic)
        geom_data.setNumRows(int(math.ceil(build_plate_size.x / grid_spacing)))

        writer_vertex = GeomVertexWriter(geom_data, "vertex")
        writer_color = GeomVertexWriter(geom_data, "color")

        current_x = grid_spacing
        while current_x <= build_plate_size.x:
            writer_vertex.addData3d(LVecBase3d(current_x, 0, 0))
            writer_vertex.addData3d(LVecBase3d(current_x, build_plate_size.y, 0))

            for _ in range(2):
                writer_color.addData4(cls._GRID_COLOR)

            current_x += grid_spacing

        return geom_data

    @classmethod
    def _get_geom_data_grid_y(
        cls,
        build_plate_size: LVector2d,
        grid_spacing: float = _GRID_SPACING,
        name: str = "",
    ) -> GeomVertexData:
        """Generate GeomVertexData for build plate grid in Y axis.

        Parameters
        ----------
        build_plate_size : LVector2d
            Build plate size.
        grid_spacing : float
            Grid spacing; distance between successive grid lines.
        name : str
            Generated GeomVertexData name.
        """
        geom_data = GeomVertexData(name, cls._GEOM_VERTEX_FORMAT_GRID, Geom.UHStatic)
        geom_data.setNumRows(int(math.ceil(build_plate_size.y / grid_spacing)))

        writer_vertex = GeomVertexWriter(geom_data, "vertex")
        writer_color = GeomVertexWriter(geom_data, "color")

        current_y = grid_spacing
        while current_y < build_plate_size.y:
            writer_vertex.addData3d(LVecBase3d(0, current_y, 0))
            writer_vertex.addData3d(LVecBase3d(build_plate_size.x, current_y, 0))

            for _ in range(2):
                writer_color.addData4(cls._GRID_COLOR)

            current_y += grid_spacing

        return geom_data

    @classmethod
    def _get_node_plate(
        cls, loader: Loader, build_plate_size: LVector2d, name: str = ""
    ) -> NodePath:
        """Generate the textured build plate NodePath.

        This NodePath's only purpose is to display the app's logo.

        Parameters
        ----------
        loader : Loader
            Panda3D asset loader.
        build_plate_size : LVector2d
            Builder plate size.
        name : str
            Name for the generated NodePath.
        """
        # Geom data
        geom_data = cls._get_geom_data_plate(build_plate_size)

        # Primitive
        primitive = GeomTristrips(Geom.UHStatic)
        primitive.addVertices(0, 1, 3, 2)
        primitive.closePrimitive()

        # Geom, GeomNode
        geom = Geom(geom_data)
        geom.addPrimitive(primitive)
        geom_node = GeomNode("")
        geom_node.addGeom(geom)

        # NodePath
        node_path = NodePath(top_node_name=name)
        node_path.attachNewNode(geom_node)

        # Texture
        tex = loader.loadTexture(cls._PATH_TEXTURE)
        ts = TextureStage("ts")
        node_path.setTexture(ts, tex)
        tex.setBorderColor((0, 0, 0, 0))
        tex.setWrapU(Texture.WMBorderColor)
        tex.setWrapV(Texture.WMBorderColor)

        node_path.setTransparency(TransparencyAttrib.MAlpha)
        node_path.setAlphaScale(cls._TEXTURE_OPACITY)

        texture_scale = cls._TEXTURE_SCALE

        width, height = build_plate_size
        ratio = width / height
        if ratio >= 1:  # Landscape or square
            scale_v = 1 / texture_scale
            scale_u = scale_v * ratio
        else:  # Portrait
            scale_u = 1 / texture_scale
            scale_v = scale_u / ratio

        node_path.setTexScale(ts, scale_u, scale_v)
        node_path.setTexOffset(ts, -0.5 * (scale_u - 1), -0.5 * (scale_v - 1))

        return node_path

    @staticmethod
    def _get_geom_data_plate(
        build_plate_size: LVector2d, name: str = ""
    ) -> GeomVertexData:
        """Generate build plate GeomVertexData.

        Parameters
        ----------
        build_plate_size : LVector2d
            Build plate size.
        name : str
            Name for the generated GeomVertexData.
        """
        # noinspection PyArgumentList
        geom_data = GeomVertexData(name, GeomVertexFormat.get_v3t2(), Geom.UHStatic)
        geom_data.setNumRows(4)

        writer_vertex = GeomVertexWriter(geom_data, "vertex")
        writer_texture = GeomVertexWriter(geom_data, "texcoord")

        # Add build plate vertices
        writer_vertex.addData3d(0, 0, 0)
        writer_vertex.addData3d(build_plate_size.x, 0, 0)
        writer_vertex.addData3d(build_plate_size.x, build_plate_size.y, 0)
        writer_vertex.addData3d(0, build_plate_size.y, 0)

        for uv in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            writer_texture.addData2(*uv)

        return geom_data


class BoundingBoxNodeBuilder(NodeBuilder):
    """Build area bounding box node builder"""

    _COLOR_BOUNDING_BOX_DEFAULT = (0.3, 0.3, 0.3, 1)
    # noinspection PyArgumentList
    _GEOM_VERTEX_FORMAT = GeomVertexFormat.get_v3c4()
    _COLOR_AXIS_X = (1, 0, 0, 1)
    _COLOR_AXIS_Y = (0, 1, 0, 1)
    _COLOR_AXIS_Z = (0, 0, 1, 1)

    _AXIS_VECTOR_LENGTH_RATIO = 0.25
    _AXIS_VECTOR_LINE_THICKNESS = 5

    @classmethod
    def build_node(
        cls,
        size: LVector3d,
        name: str,
    ) -> NodePath:
        """Build build area bounding box NodePath.

        Parameters
        ----------
        size : LVector3d
            Build area size.
        name : str
            Name for the returned NodePath.

        Returns
        -------
        NodePath
            Built build plate NodePath.
        """
        geom_data = cls._get_geom_vertex_data(size, name)
        primitive = cls._get_primitive()

        # Prepare Geom
        geom = Geom(geom_data)
        geom.addPrimitive(primitive)

        # Prepare GeomNode
        geom_node_bbox = GeomNode(name)
        geom_node_bbox.addGeom(geom)

        geom_node_axis_vectors = cls._get_geom_node_axis_vectors(size)

        node_path = NodePath(top_node_name="bounding_box")
        node_path.attachNewNode(geom_node_bbox)
        node_path.attachNewNode(geom_node_axis_vectors)

        return node_path

    @staticmethod
    def _get_primitive() -> GeomLines:
        """Generate GeomLines primitive for bounding box lines."""
        primitive = GeomLinestrips(Geom.UHStatic)
        # 0, 1, 2, 3, 4, 5, 6, 7 - bounding box grey vertices

        # Bounding box
        for i in [0, 4]:
            for j in [0, 1, 2, 3, 0]:
                primitive.addVertex(i + j)
            primitive.closePrimitive()
        for i in range(4):
            primitive.addVertices(i, i + 4)
            primitive.closePrimitive()

        return primitive

    @classmethod
    def _get_geom_vertex_data(cls, size: LVector3d, name: str) -> GeomVertexData:
        """Generate GeomVertexData for the bounding box.

        Parameters
        ----------
        size : LVector3d
            Bounding box size.
        name : str
            Name for generated GeomVertexData.

        Returns
        -------
        GeomVertexData
            Bounding box GeomVertexData.
        """
        geom_data = GeomVertexData(name, cls._GEOM_VERTEX_FORMAT, Geom.UHStatic)
        geom_data.setNumRows(8)  # 8 cube vertices

        writer_color = GeomVertexWriter(geom_data, "color")
        writer_vertex = GeomVertexWriter(geom_data, "vertex")

        # VERTEX COLORS
        for i in range(8):
            writer_color.addData4(cls._COLOR_BOUNDING_BOX_DEFAULT)

        # VERTEX COORDS

        # Bounding box
        writer_vertex.addData3d(0, 0, 0)
        writer_vertex.addData3d(size.x, 0, 0)
        writer_vertex.addData3d(size.x, 0, size.z)
        writer_vertex.addData3d(0, 0, size.z)
        writer_vertex.addData3d(0, size.y, 0)
        writer_vertex.addData3d(size.x, size.y, 0)
        writer_vertex.addData3d(size.x, size.y, size.z)
        writer_vertex.addData3d(0, size.y, size.z)

        return geom_data

    @classmethod
    def _get_geom_node_axis_vectors(
        cls, size: LVector3d, length_ratio: float = _AXIS_VECTOR_LENGTH_RATIO
    ) -> GeomNode:
        """Generate Geom

        Parameters
        ----------
        size : LVector3d
            Bounding box size.
        length_ratio : float
            Length ratio of colored lines to respective bounding box lengths.

        Returns
        -------
        GeomNode
            GeomNode for colored axis vectors LineSegs.
        """
        line_segs = LineSegs("axis_vectors")
        line_segs.setThickness(4)

        # X axis vector
        line_segs.setColor(cls._COLOR_AXIS_X)
        line_segs.moveTo(0, 0, 0)
        line_segs.drawTo(size.x * length_ratio, 0, 0)

        # Y axis vector
        line_segs.setColor(cls._COLOR_AXIS_Y)
        line_segs.moveTo(0, 0, 0)
        line_segs.drawTo(0, size.y * length_ratio, 0)

        # Z axis vector
        line_segs.setColor(cls._COLOR_AXIS_Z)
        line_segs.moveTo(0, 0, 0)
        line_segs.drawTo(0, 0, size.z * length_ratio)

        # noinspection PyArgumentList
        return line_segs.create()
