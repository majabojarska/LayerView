"""Integration tests for LayerView application."""

from PyQt5.QtCore import QTimer

from layerview.app.app import App


def test_app_sanity(path_gcode_valid):
    """Test app sanity.

    Start the app with an initial gcode path.
    Trigger app teardown 1 second after loading finishes.
    App should close with exit code 0.
    """
    app = App(argv=[], gcode_path=path_gcode_valid)
    app._controller._recv_worker_data_out_payload.connect(
        lambda _: QTimer.singleShot(1000, app.teardown)
    )
    app.show()
    assert app.exec_() == 0
