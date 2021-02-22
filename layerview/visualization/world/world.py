"""Visualization scene."""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    LVecBase2i,
    LVecBase3f,
    LVector3d,
    NodePath,
    VBase4,
)
from QPanda3D.Panda3DWorld import Panda3DWorld

from layerview.visualization.nodes.build_area import BuildAreaNodeBuilder
from layerview.visualization.nodes.model import ModelManager
from layerview.visualization.point_cloud.boundaries import BoundingBox3D
from layerview.visualization.point_cloud.model import ModelInfo
from layerview.visualization.world.camera import (
    CameraController,
    FreeCameraController,
    OrbitCameraController,
)


class CameraMode(Enum):
    """Camera mode."""

    SPHERICAL = auto()
    FREE = auto()


class ColoringMode(Enum):
    """Model coloring mode."""

    CONSTANT = auto()
    FEEDRATE = auto()
    THICKNESS = auto()
    TEMPERATURE = auto()


class Visualization(Panda3DWorld):
    """3D Visualization scene."""

    _BACKGROUND_COLOR: VBase4 = VBase4(0.9, 0.9, 0.9, 1)
    _BUILD_AREA_BOUNDARIES_DEFAULT: BoundingBox3D = BoundingBox3D.from_origin(
        LVector3d(200, 200, 200)
    )
    _FOCAL_POINT_DEFAULT: LVector3d = LVector3d(
        _BUILD_AREA_BOUNDARIES_DEFAULT.center.xy,
        _BUILD_AREA_BOUNDARIES_DEFAULT.size.z * 0.1,
    )

    def __init__(
        self, camera_mode: CameraMode = CameraMode.SPHERICAL, debug: bool = False
    ):
        """
        Parameters
        ----------
        camera_mode : CameraMode
            Initial CameraMode.
        debug : bool
            Debug flag.
        """
        Panda3DWorld.__init__(self)

        self._is_debug: bool = debug

        # Children
        self._model_node_manager: Optional[ModelManager] = None
        self._build_area_node: Optional[NodePath] = None

        # Light
        self._dir_light_top_np: Optional[DirectionalLight] = None
        self._dir_light_bot_np: Optional[DirectionalLight] = None
        self._ambient_light_np: Optional[AmbientLight] = None
        self._init_lights()

        # Controls
        self.disableMouse()  # Disable default camera mouse controls

        # Background color
        self.buff.setClearColorActive(True)
        self.buff.setClearColor(self._BACKGROUND_COLOR)

        # Camera
        self._camera_mode: CameraMode = camera_mode
        self._camera_controller: Optional[CameraController] = None
        self._focal_point: LVector3d = self._FOCAL_POINT_DEFAULT

        # Tasks
        self._setup_tasks()

        # Misc
        self.disableAllAudio()
        self.disableParticles()

        self._frame_buffer_size: Optional[LVecBase2i] = None

        if self._is_debug:
            self.messenger.toggleVerbose()

    def reset(self):
        """Reset scene to initial state."""
        self._remove_model_node()
        new_build_area = self._get_new_build_area(
            size=self._BUILD_AREA_BOUNDARIES_DEFAULT.size,
            size_min=self._BUILD_AREA_BOUNDARIES_DEFAULT.size * 0.9,
        )
        self._set_build_area(new_build_area)

        x, y, z = self._BUILD_AREA_BOUNDARIES_DEFAULT.size
        new_camera_pos = LVecBase3f(x / 2, -y * 1.2, z * 1.2)

        # Place camera at the same pos as anchor.
        self.cam.setPos(0, 0, 0)
        self.camera.setPos(new_camera_pos)
        self.camera.lookAt(*self._FOCAL_POINT_DEFAULT)

        if self._camera_controller:
            self._camera_controller.deactivate()

        self.set_focal_point(focal_point=self._FOCAL_POINT_DEFAULT)
        self._set_camera_controller(self._get_new_camera_controller(activate=True))

    def handle_focus_out(self):
        self._camera_controller.stop_movement()

    # Properties

    @property
    def model_node_manager(self) -> Optional[ModelManager]:
        return self._model_node_manager

    @property
    def model_info(self) -> Optional[ModelInfo]:
        if self.model_node_manager:
            return self._model_node_manager.model_info
        return None

    @property
    def model_node(self) -> Optional[NodePath]:
        if self.model_node_manager:
            return self._model_node_manager.model_node
        return None

    @property
    def camera_mode(self):
        return self._camera_mode

    @property
    def focal_point(self) -> Optional[LVector3d]:
        return self._focal_point

    # Events

    def _setup_tasks(self):
        """Initializes Panda3D tasks for this Visualization."""
        self.addTask(
            self._task_update_frame_buffer_size, "task_update_frame_buffer_size"
        )

    def _task_update_frame_buffer_size(self, task):
        """Panda3D task, checks for frame buffer size changes.

        If frame buffer size changes, self._on_resize is called.
        This task runs indefinitely.
        """
        if self._frame_buffer_size != self.win.fb_size:
            self._frame_buffer_size = self.win.fb_size
            self._on_resize()
        return task.cont

    def _on_resize(self):
        """Perform operations required after frame buffer resize."""
        self._camera_controller.stop_movement()

    # Model

    def _remove_model_node(self):
        """Remove current model node, if it exists."""
        if self.model_node:
            self.model_node.removeNode()

    def set_model_node_manager(self, manager: Optional[ModelManager]):
        """Set new model.

        Removes current model node, if it exists.
        Creates new build area.

        Parameters
        ----------
        manager: ModelManager
        """
        if manager:
            # Create new build area
            self._set_build_area(
                self._get_new_build_area(
                    size=manager.model_info.boundaries.point_max * 1.05,
                    size_min=self._BUILD_AREA_BOUNDARIES_DEFAULT.size,
                )
            )

            # Remove current model
            self._remove_model_node()
            # Add new model node
            manager.model_node.reparentTo(self.render)

            self.set_focal_point(
                focal_point=manager.model_info.boundaries_without_priming.center
            )

            # Create new camera controller
            self._set_camera_controller(self._get_new_camera_controller(activate=True))

        self._model_node_manager = manager

    # Camera

    def set_camera_mode(self, camera_mode: CameraMode):
        """Set camera mode.

        If camera_mode is the same as current camera mode, nothing changes.
        Otherwise camera_mode is set as current camera mode and appriopriate
        CameraController is setup in place of the current one.

        Parameters
        ----------
        camera_mode : CameraMode
            Target camera mode to set.
        """
        if self._camera_mode != camera_mode:
            self._camera_mode = camera_mode
            self._set_camera_controller(self._get_new_camera_controller(activate=True))

    def _remove_camera_controller(self):
        if self._camera_controller:
            self._camera_controller.deactivate()
        self._camera_controller = None

    def _set_camera_controller(self, controller: CameraController):
        """Set active camera controller"""
        self._remove_camera_controller()
        self._camera_controller = controller

    def _get_new_camera_controller(
        self, speed: Optional[float] = 2.0, activate: Optional[bool] = False
    ) -> CameraController:
        """Create camera controller for current camera mode.

        Parameters
        ----------
        speed : Optional[float]
            Camera movement and rotation speed.
        activate : Optional[bool]
            If True, the new controller is activated before returning.
            Otherwise the returned controller is inactive.

        Returns
        -------
        controller : CameraController
            Created camera controller.
        """
        if self._camera_mode == CameraMode.SPHERICAL:
            if not self.focal_point:
                raise ValueError(
                    f"Focal point must be specified when using camera mode "
                    f"{self._camera_mode.name}."
                )

            controller = OrbitCameraController(
                camera=self.cam,
                camera_anchor=self.camera,
                render=self.render,
                mouse_watcher_node=self.mouseWatcherNode,
                win=self.win,
                focal_point=self.focal_point,
                speed=speed,
            )
        elif self._camera_mode == CameraMode.FREE:
            controller = FreeCameraController(
                camera=self.cam,
                camera_anchor=self.camera,
                render=self.render,
                mouse_watcher_node=self.mouseWatcherNode,
                win=self.win,
                focal_point=self.focal_point,
                speed=speed,
            )
        else:
            raise NotImplementedError(
                f"Camera mode {self._camera_mode.name} is currently not supported."
            )

        if activate:
            controller.activate()

        return controller

    def focus_on_model(self):
        """Focus the camera on model's center point."""
        self._camera_controller.look_at_focal_point()

    def set_focal_point(self, focal_point: LVector3d):
        """Set this Visualization's focal point.

        Parameters
        ----------
        focal_point : LVector3d
            New focal point.
        """
        self._focal_point = focal_point

    # Build Area

    def _remove_build_area(self):
        """Remove build area node, if it exists."""
        if self._build_area_node:
            self._build_area_node.removeNode()
        self._build_area_node = None

    def _set_build_area(self, node: NodePath):
        """Set build area node.

        If a build area node already exists, it is removed.

        Parameters
        ----------
        node : NodePath
            Build area NodePath.
        """
        self._remove_build_area()

        self._build_area_node = node
        self._build_area_node.reparentTo(self.render)

    def _get_new_build_area(
        self, size: LVector3d, size_min: Optional[LVector3d] = None
    ) -> NodePath:
        """Create a new build area node.

        Parameters
        ----------
        size : LVector3d
        size_min : Optional[LVector3d]

        Returns
        -------
        build_area_node : NodePath
        """
        build_area_node = BuildAreaNodeBuilder.build_node(
            loader=self.loader, size=size, size_min=size_min
        )
        return build_area_node

    # Lighting

    def _init_lights(self):
        """Initialize scene lighting.

        Creates three light sources:
            - ambient,
            - directional from top (pitch=-90),
            - directional from bottom (pitch=90).
        """
        # Ambient
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor((0.3, 0.3, 0.3, 1))
        self._ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(self._ambient_light_np)

        # Directional from top
        dir_light_top = DirectionalLight("dir_light_top")
        dir_light_top.setColor((1, 1, 1, 1))
        self._dir_light_top_np = self.render.attachNewNode(dir_light_top)
        self._dir_light_top_np.setHpr(0, -90, 0)
        self.render.setLight(self._dir_light_top_np)

        # Directional from top
        dir_light_bot = DirectionalLight("dir_light_bot")
        dir_light_bot.setColor((1, 1, 1, 1))
        self._dir_light_bot_np = self.render.attachNewNode(dir_light_bot)
        self._dir_light_bot_np.setHpr(0, 90, 0)
        self.render.setLight(self._dir_light_bot_np)
