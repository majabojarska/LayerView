from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFocusEvent
from QPanda3D.QPanda3DWidget import QPanda3DWidget


class VisualizationWidget(QPanda3DWidget):
    focus_out: pyqtSignal = pyqtSignal(QFocusEvent)

    def focusOutEvent(self, event: QFocusEvent):
        self.focus_out.emit(event)
        super().focusOutEvent(event)
