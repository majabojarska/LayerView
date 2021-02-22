from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QAction, QDialog

from layerview.app.dialog_load.worker import GcodeLoaderWorker
from layerview.app.pyuic.dialog_load import Ui_Dialog


class GcodeLoadingDialog(QDialog):
    data_out: pyqtSignal = pyqtSignal(GcodeLoaderWorker.DataOutPayload)

    _request_worker_stop: pyqtSignal = pyqtSignal()

    def __init__(self, gcode_path: Path, nozzle_diam: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self._gcode_path: Path = gcode_path
        self._nozzle_diam: float = nozzle_diam

        self.setWindowTitle("Loading G-code")
        self.ui.labelStatus.setText("")
        self.ui.progressBar.setValue(0)

        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[QObject] = None

        self._setup_input()

    # Overrides

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)

        self._run_worker()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
        self._on_cancel()

    # Slots

    @pyqtSlot()
    def _on_thread_finished(self):
        self._worker_thread.deleteLater()
        self.hide()

    @pyqtSlot(float)
    def _on_update_progress(self, progress: float):
        self.ui.progressBar.setValue(int(progress * 100))

    @pyqtSlot(str)
    def _on_update_status(self, text: str):
        self.ui.labelStatus.setText(text)

    @pyqtSlot()
    def _on_cancel(self):
        self._request_worker_stop.emit()

    # Private methods

    def _setup_input(self):
        self.ui.buttonCancel.clicked.connect(self._on_cancel)
        finish = QAction("Quit", self)
        finish.triggered.connect(self._on_cancel)

    def _run_worker(self):
        # Init worker and thread
        self._worker_thread = QThread()
        self._worker = GcodeLoaderWorker(
            gcode_path=self._gcode_path, nozzle_diam=self._nozzle_diam
        )
        self._worker.moveToThread(self._worker_thread)

        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.finished.connect(self._on_thread_finished)

        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.data_out.connect(self.data_out.emit)
        self._worker.update_status.connect(self._on_update_status)
        self._worker.update_progress.connect(self._on_update_progress)

        self._request_worker_stop.connect(lambda: self._worker.request_stop())

        # Start
        self._worker_thread.start(priority=QThread.HighestPriority)
