"""Main module."""

import signal
import typing
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QApplication

from layerview.app.main_window.controller import Controller
from layerview.app.main_window.model import Model
from layerview.app.main_window.view import ConcreteView, View


class App(QApplication):
    def __init__(self, argv: typing.List[str], gcode_path: Optional[Path] = None):
        super().__init__(argv)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self._model: Model = Model()
        self._view: View = ConcreteView(self._model)
        self._controller: Controller = Controller(
            self._model, self._view, initial_gcode=gcode_path
        )

    def __del__(self):
        self.teardown()

    def teardown(self):
        self._controller.teardown()

    def show(self):
        self._controller.show()
