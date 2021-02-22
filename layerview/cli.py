"""Console script for layerview."""
import argparse
import sys
from pathlib import Path
from typing import Optional

from panda3d.core import PStatClient

from layerview.app.app import App

_PSTAT_PORT_DEFAULT = 5185


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--gcode",
        type=str,
        help="Path to G-code file to load on start.",
        dest="gcode_path",
    )
    parser.add_argument(
        "--pstat-host",
        type=str,
        help="Network address of host running PStats",
        dest="pstat_host",
    )
    parser.add_argument(
        "--pstat-port", type=int, help="pstat port number", dest="pstat_port"
    )

    return parser


def main():
    """Console script for LayerView."""
    args = _get_parser().parse_args()

    # PStats
    pstat_host: str = args.pstat_host
    if pstat_host:
        if args.pstat_port:
            pstat_port: int = args.pstat_port
        else:
            pstat_port: int = _PSTAT_PORT_DEFAULT
            print(f"PStats port not specified, falling back to {pstat_port}")

        print(f"Connecting to PStats server at {pstat_host}:{pstat_port}")
        # noinspection PyArgumentList
        PStatClient.connect(pstat_host, pstat_port)
    elif not pstat_host and args.pstat_port:
        print("--pstats-port was specified without --pstats-host")
        return 1

    gcode_path: Optional[Path] = None
    if args.gcode_path:
        gcode_path = Path(args.gcode_path).absolute()

    # Run app
    app = App(argv=sys.argv, gcode_path=gcode_path)
    app.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
