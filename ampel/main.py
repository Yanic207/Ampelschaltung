"""Einstiegspunkt der Fußgängerampel.

Mock-Betrieb (ohne Raspberry Pi):
    python -m ampel.main --mock
oder:
    AMPEL_MOCK=1 python -m ampel.main

Echter Betrieb auf dem Raspberry Pi:
    python -m ampel.main
"""

import argparse
import logging
import os
import sys

from . import config
from .controller import Controller
from .hardware import Hardware

logger = logging.getLogger(__name__)


def parse_args(argv=None):
    """Liest die Kommandozeilen-Argumente ein."""
    parser = argparse.ArgumentParser(description="Fußgängerampel")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Mock-Betrieb ohne Raspberry Pi/Hardware",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    mock = args.mock or (os.environ.get(config.MOCK_ENV_VAR) == "1")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    hardware = Hardware(mock=mock)
    controller = Controller(hardware)

    try:
        if mock:
            logger.info("Start im Mock-Betrieb (ohne Hardware).")
            controller.run_demo()
        else:
            logger.info("Start auf dem Raspberry Pi (echtes GPIO).")
            controller.run()
    except KeyboardInterrupt:
        logger.info("Beendet durch Ctrl+C.")
    finally:
        hardware.all_off()
        logger.info("Alle LEDs ausgeschaltet.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
