"""Camera controllers."""
from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from functools import reduce
from typing import Dict, List, Optional

from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    GraphicsBuffer,
    LPoint2f,
    LVecBase3,
    LVecBase3f,
    LVector3d,
    MouseWatcher,
    NodePath,
)


class KeyCombo(enum.Enum):
    """Represents a keyboard key combination (aka key combo)."""

    W = enum.auto()
    A = enum.auto()
    S = enum.auto()
    D = enum.auto()

    SPACE = enum.auto()
    SHIFT_SPACE = enum.auto()

    @staticmethod
    def get_wasd_keys() -> List[KeyCombo]:
        """Return list containing W, A, S, D KeyCombos."""
        return [
            KeyCombo.W,
            KeyCombo.A,
            KeyCombo.S,
            KeyCombo.D,
        ]


class MouseButton(enum.Enum):
    """Represents a mouse button"""

    LEFT = enum.auto()
    MIDDLE = enum.auto()
    RIGHT = enum.auto()


class Direction(enum.Enum):
    """Represents a direction vector."""

    LEFT = LVector3d(-1, 0, 0)
    RIGHT = LVector3d(1, 0, 0)
    FORWARD = LVector3d(0, 1, 0)
    BACKWARD = LVector3d(0, -1, 0)
    UP = LVector3d(0, 0, 1)
    DOWN = LVector3d(0, 0, -1)


class CameraController(DirectObject, ABC):
    """Generic camera controller."""

    def __init__(
        self,
        camera: NodePath,
        camera_anchor: NodePath,
        focal_point,
        render: NodePath,
        mouse_watcher_node: MouseWatcher,
        win: GraphicsBuffer,
        speed: float,
    ):
        """
        Parameters
        ----------
        camera : NodePath
            Camera NodePath.
        camera_anchor : NodePath
            Camera anchor NodePath.
        focal_point
            Camera's focal point.
        render : NodePath
            Render NodePath.
        mouse_watcher_node : MouseWatcher
            Mouse watcher node.
        win : GraphicsBuffer
            Panda3D window.
        speed : float
            Camera movement/rotation speed.
        """
        super().__init__()

        self._camera: NodePath = camera
        self._camera_anchor: NodePath = camera_anchor
        self._focal_point = focal_point
        self._render: NodePath = render
        self._mouse_watcher_node: NodePath = mouse_watcher_node
        self._win = win
        self._speed = speed

        self._continue_tasks: bool = True

        self._key_combo_to_is_pressed: Dict[KeyCombo, bool] = {}
        self._mouse_button_to_is_pressed: Dict[MouseButton, bool] = {}

    # Public

    def activate(self):
        """Activate this controller.

        Starts relevant tasks.
        """
        self._setup_tasks()

    def deactivate(self):
        """Deactivate this controller.

        Stops any ongoing camera movement.
        Stops any running tasks.
        """
        self.stop_movement()
        self.ignoreAll()
        self._continue_tasks = False

    def stop_movement(self):
        """Stop any ongoing camera movement."""
        for dict_obj in [
            self._key_combo_to_is_pressed,
            self._mouse_button_to_is_pressed,
        ]:
            for key in dict_obj:
                dict_obj[key] = False

    @abstractmethod
    def look_at_focal_point(self):
        """Focus the camera at focal point."""
        raise NotImplementedError

    # Protected

    @property
    def _camera_anchor_parent(self) -> NodePath:
        """Return camera anchor's parent."""
        return self._camera_anchor.getParent()

    @abstractmethod
    def _handle_mouse_pos_delta(self, delta_px_x: int, delta_px_y: int):
        """Handle mouse position delta (change)."""
        raise NotImplementedError

    # Inputs

    def _setup_input(self):
        """Setup keyboard event listeners."""
        # Mouse buttons
        self.accept("mouse1", self._on_mouse_button, [MouseButton.LEFT, True])
        self.accept("mouse1-up", self._on_mouse_button, [MouseButton.LEFT, False])
        self.accept("mouse2", self._on_mouse_button, [MouseButton.MIDDLE, True])
        self.accept("mouse2-up", self._on_mouse_button, [MouseButton.MIDDLE, False])
        self.accept("mouse3", self._on_mouse_button, [MouseButton.RIGHT, True])
        self.accept("mouse3-up", self._on_mouse_button, [MouseButton.RIGHT, False])

        # Scroll wheel
        self.accept("wheel_up", self._on_scroll, [True])
        self.accept("wheel_down", self._on_scroll, [False])

        # WASD
        self.accept("w", self._on_key, [KeyCombo.W, True])
        self.accept("shift-w", self._on_key, [KeyCombo.W, True])
        self.accept("w-up", self._on_key, [KeyCombo.W, False])
        self.accept("shift-w-up", self._on_key, [KeyCombo.W, False])
        self.accept("a", self._on_key, [KeyCombo.A, True])
        self.accept("shift-a", self._on_key, [KeyCombo.A, True])
        self.accept("a-up", self._on_key, [KeyCombo.A, False])
        self.accept("shift-a-up", self._on_key, [KeyCombo.A, False])
        self.accept("s", self._on_key, [KeyCombo.S, True])
        self.accept("shift-s", self._on_key, [KeyCombo.S, True])
        self.accept("s-up", self._on_key, [KeyCombo.S, False])
        self.accept("shift-s-up", self._on_key, [KeyCombo.S, False])
        self.accept("d", self._on_key, [KeyCombo.D, True])
        self.accept("shift-d", self._on_key, [KeyCombo.D, True])
        self.accept("d-up", self._on_key, [KeyCombo.D, False])
        self.accept("shift-d-up", self._on_key, [KeyCombo.D, False])

        # Space
        self.accept("space", self._on_key, [KeyCombo.SPACE, True])
        self.accept("space-up", self._on_key, [KeyCombo.SPACE, False])
        self.accept("shift-space", self._on_key, [KeyCombo.SHIFT_SPACE, True])
        self.accept("shift-space-up", self._on_key, [KeyCombo.SHIFT_SPACE, False])

    def _on_key(self, key_combo: KeyCombo, is_pressed: bool):
        """Handle keypress event."""
        self._key_combo_to_is_pressed[key_combo] = is_pressed

        if key_combo in [KeyCombo.SPACE, KeyCombo.SHIFT_SPACE]:
            if is_pressed:
                if key_combo == KeyCombo.SPACE:
                    self._key_combo_to_is_pressed[KeyCombo.SHIFT_SPACE] = False
                else:
                    self._key_combo_to_is_pressed[KeyCombo.SPACE] = False
            else:
                self._key_combo_to_is_pressed[KeyCombo.SPACE] = False
                self._key_combo_to_is_pressed[KeyCombo.SHIFT_SPACE] = False

    def _on_scroll(self, is_scroll_up: bool):
        """Handle scroll event."""
        pass

    def _on_mouse_button(self, mouse_button: MouseButton, is_pressed: bool):
        """Handle mouse button event."""
        if not any(self._mouse_button_to_is_pressed.values()):
            # No mouse buttons are pressed. Clear last saved position.
            self._mouse_pos_prev = None

        self._mouse_button_to_is_pressed[mouse_button] = is_pressed

    # Tasks

    def _setup_tasks(self):
        """Setup this controller's tasks."""
        self.addTask(self._task_handle_key, "task_handle_key")
        self.addTask(self._task_handle_mouse, "task_handle_mouse")

    def _task_handle_key(self, task):
        """Handle keypress event.

        This is a task function.
        """
        # Calc translation vector, based on pressed keys
        rel_translate_vec: LVector3d = reduce(
            lambda x, y: x + y,
            [
                self._key_combo_to_direction[key]
                for key, is_pressed in self._key_combo_to_is_pressed.items()
                if is_pressed and key in self._key_combo_to_direction
            ],
            LVector3d(0, 0, 0),
        )

        hpr_backup = self._camera_anchor.getHpr()
        self._camera_anchor.setP(0)
        self._camera_anchor.setR(0)
        self._camera_anchor.setPos(self._camera_anchor, *(rel_translate_vec * 0.75))
        self._camera_anchor.setHpr(hpr_backup)

        if self._continue_tasks:
            return task.cont

    def _task_handle_mouse(self, task):
        """Handle mouse move event.

        This is a task function.
        """
        if self._mouse_watcher_node.hasMouse():
            mouse_pos_cur = self._mouse_watcher_node.getMouse()

            # No previous mouse position recorded
            if not self._mouse_pos_prev:
                self._mouse_pos_prev = LPoint2f(mouse_pos_cur)
                if self._continue_tasks:
                    return task.cont

            # Mouse hasn't moved since last task execution
            if mouse_pos_cur == self._mouse_pos_prev:
                if self._continue_tasks:
                    return task.cont

            # Mouse moved
            mouse_pos_delta = mouse_pos_cur - self._mouse_pos_prev
            width, height = self._win.fb_size
            delta_px_x, delta_px_y = (
                width * mouse_pos_delta.x,
                height * mouse_pos_delta.y,
            )

            self._handle_mouse_pos_delta(delta_px_x=delta_px_x, delta_px_y=delta_px_y)

            self._mouse_pos_prev = LPoint2f(mouse_pos_cur)

        if self._continue_tasks:
            return task.cont

    # Other

    @property
    @abstractmethod
    def _key_combo_to_direction(self) -> Dict[KeyCombo, LVector3d]:
        """Return dict that maps KeyCombo to Direction."""
        pass

    def _print_camera_status(self):
        """Print camera (and camera anchor's) position and HPR."""
        print(
            f"=============================================\n"
            f"Anchor         ={self._camera_anchor}\n"
            f"Anchor POS ABS ={self._camera_anchor.getPos()}\n"
            f"Anchor HPR     ={self._camera_anchor.getHpr()}\n"
            f"Camera         ={self._camera}\n"
            f"Camera POS     ={self._camera.getPos()}\n"
            f"Camera POS ABS ={self._camera.getPos(self._camera_anchor.getParent())}\n"
            f"Camera HPR     ={self._camera.getHpr()}\n"
            f"=============================================\n"
        )

    @staticmethod
    def _limit_hpr(val: float) -> float:
        """Sanitize the provided heading/pitch/rotation value."""
        return (val + 180) % 360 - 180


class OrbitCameraController(CameraController):
    """Orbit camera controller (spherical).

    Allows for rotation around a distant focal point.
    The camera is always focused on the focal point.
    """

    _KEY_COMBO_TO_DIRECTION: Dict[KeyCombo, LVector3d] = {
        KeyCombo.W: -Direction.FORWARD.value,
        KeyCombo.A: -Direction.LEFT.value,
        KeyCombo.S: -Direction.BACKWARD.value,
        KeyCombo.D: -Direction.RIGHT.value,
        KeyCombo.SPACE: Direction.UP.value,
        KeyCombo.SHIFT_SPACE: Direction.DOWN.value,
    }

    def __init__(
        self,
        camera: NodePath,
        camera_anchor: NodePath,
        focal_point: LVector3d,
        render: NodePath,
        mouse_watcher_node: MouseWatcher,
        win,
        speed: Optional[float] = 1.0,
        distance_min: Optional[float] = 1,
        distance_max: Optional[float] = 2000,
    ):
        """
        Parameters
        ----------
        camera : NodePath
            Camera NodePath.
        camera_anchor : NodePath
            Camera anchor NodePath.
        focal_point
            Camera's focal point.
        render : NodePath
            Render NodePath.
        mouse_watcher_node : MouseWatcher
            Mouse watcher node.
        win : GraphicsBuffer
            Panda3D window.
        speed : float
            Camera movement/rotation speed.
        """
        super().__init__(
            camera=camera,
            camera_anchor=camera_anchor,
            focal_point=focal_point,
            render=render,
            mouse_watcher_node=mouse_watcher_node,
            win=win,
            speed=speed,
        )

        # Attributes
        self._dist_min = distance_min
        self._dist_max = distance_max

        # State
        self._mouse_pos_prev: Optional[LPoint2f] = None
        self._is_mouse_1_pressed: bool = False

        # Setup
        self._setup_camera(focal_point=focal_point)

    def activate(self):
        self._setup_tasks()
        self._setup_input()

    # Setup

    def _setup_camera(self, focal_point: LVector3d):
        """Setup camera for this camera controller."""
        node_render: NodePath = self._camera_anchor.getParent()
        focal_point = LVector3d(*focal_point)
        last_camera_pos_abs = LVector3d(*self._camera.getPos(node_render))

        # Place anchor at focal point
        self._camera_anchor.setPos(*focal_point)

        # Place camera in front of anchor
        dist_anchor_to_camera: float = (
            last_camera_pos_abs - LVector3d(*self._camera_anchor.getPos())
        ).length()
        self._camera.setPos(0, dist_anchor_to_camera, 0)
        self._camera.setHpr(180, 0, 0)

        # Anchor look at camera abs position from before setup
        self._camera_anchor.lookAt(node_render, *last_camera_pos_abs)

    # Input callbacks

    def _on_scroll(self, is_scroll_up: bool):
        delta_y = (-self._speed if is_scroll_up else self._speed) * 10
        pos = self._camera.getPos()
        new_y = pos.y + delta_y

        if self._dist_min <= abs(new_y) <= self._dist_max:
            pos.y = new_y
            self._camera.setPos(pos)

    # Other

    @property
    def _key_combo_to_direction(self) -> Dict[KeyCombo, LVector3d]:
        return self._KEY_COMBO_TO_DIRECTION

    def _handle_mouse_pos_delta(self, delta_px_x: int, delta_px_y: int):
        if self._mouse_button_to_is_pressed.get(MouseButton.LEFT):
            delta_h = -delta_px_x * self._speed / 20
            delta_p = -delta_px_y * self._speed / 20

            cur_h = self._camera_anchor.getH()
            cur_p = self._camera_anchor.getP()

            new_h = self._limit_hpr(cur_h + delta_h)
            new_p = self._limit_hpr(cur_p + delta_p)

            self._camera_anchor.setH(new_h)
            self._camera_anchor.setP(new_p)

    def look_at_focal_point(self):
        # In this mode the camera is always focused on the model.
        self.stop_movement()
        self._camera_anchor.setPos(*self._focal_point)


class FreeCameraController(CameraController):
    """Free camera controller.

    Allows rotation around the camera's position.
    """

    _KEY_COMBO_TO_DIRECTION: Dict[KeyCombo, LVector3d] = {
        KeyCombo.W: Direction.FORWARD.value,
        KeyCombo.A: Direction.LEFT.value,
        KeyCombo.S: Direction.BACKWARD.value,
        KeyCombo.D: Direction.RIGHT.value,
        KeyCombo.SPACE: Direction.UP.value,
        KeyCombo.SHIFT_SPACE: Direction.DOWN.value,
    }

    def __init__(
        self,
        camera: NodePath,
        camera_anchor: NodePath,
        focal_point: LVector3d,
        render: NodePath,
        mouse_watcher_node: MouseWatcher,
        win,
        speed: Optional[float] = 1.0,
    ):
        """
        Parameters
        ----------
        camera : NodePath
            Camera NodePath.
        camera_anchor : NodePath
            Camera anchor NodePath.
        focal_point
            Camera's focal point.
        render : NodePath
            Render NodePath.
        mouse_watcher_node : MouseWatcher
            Mouse watcher node.
        win : GraphicsBuffer
            Panda3D window.
        speed : float
            Camera movement/rotation speed.
        """
        super().__init__(
            camera=camera,
            camera_anchor=camera_anchor,
            focal_point=focal_point,
            render=render,
            mouse_watcher_node=mouse_watcher_node,
            win=win,
            speed=speed,
        )

        # State
        self._mouse_pos_prev: Optional[LPoint2f] = None

        # Setup
        self._setup_camera()
        self._setup_tasks()
        self._setup_input()

    def activate(self):
        self._setup_tasks()
        self._setup_input()

    # Setup

    def _setup_camera(self):
        """Setup camera for this camera controller."""
        last_camera_pos_abs = LVector3d(
            *self._camera.getPos(self._camera_anchor_parent)
        )
        target_anchor_hpr: LVecBase3 = self._camera.getHpr(self._camera_anchor_parent)

        # Place camera at anchor, reset camera's hpr
        self._camera.setPos(0, 0, 0)
        self._camera.setHpr(0, 0, 0)

        # Place anchor at last camera abs pos
        self._camera_anchor.setPos(
            self._camera_anchor_parent, LVecBase3f(*last_camera_pos_abs)
        )
        self._camera_anchor.setHpr(self._camera_anchor_parent, target_anchor_hpr)

    # Input callbacks

    def _on_scroll(self, is_scroll_up: bool):
        delta_y = (self._speed if is_scroll_up else -self._speed) * 10
        self._camera_anchor.setPos(self._camera_anchor, 0, delta_y, 0)

    # Other

    @property
    def _key_combo_to_direction(self) -> Dict[KeyCombo, LVector3d]:
        return self._KEY_COMBO_TO_DIRECTION

    def _handle_mouse_pos_delta(self, delta_px_x: int, delta_px_y: int):
        if self._mouse_button_to_is_pressed.get(MouseButton.LEFT):
            delta_h = -delta_px_x * self._speed / 40
            delta_p = delta_px_y * self._speed / 40

            cur_h = self._camera_anchor.getH()
            cur_p = self._camera_anchor.getP()

            new_h = self._limit_hpr(cur_h + delta_h)
            new_p = self._limit_hpr(cur_p + delta_p)

            self._camera_anchor.setH(new_h)
            self._camera_anchor.setP(new_p)

    def look_at_focal_point(self):
        self.stop_movement()
        self._camera_anchor.lookAt(*self._focal_point)
