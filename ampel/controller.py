"""Zustandsautomat der Fußgängerampel.

Die Phasenlogik kennt keine GPIO-Pins, sondern arbeitet nur mit einer kleinen
Hardware-Schnittstelle (set_car, set_pedestrian, wait_for_button). Dadurch
lässt sie sich mit einem Fake testen und später unverändert auf dem Pi nutzen.
"""

import logging
import time

from . import config

logger = logging.getLogger(__name__)


class Controller:
    """Steuert den Phasenablauf der Fußgängerampel."""

    def __init__(self, hardware):
        self._hardware = hardware

    def show_ground_state(self):
        """Grundzustand (Phase 0): Auto Grün, Fußgänger Rot."""
        self._phase("0", "green", "red", 0)

    def run_cycle(self):
        """Führt einen Anforderungszyklus (Phasen 1–5) aus und endet in Phase 0."""
        self._phase("1", "yellow", "red", config.DURATION_CAR_YELLOW)
        self._phase("2", "red", "red", config.DURATION_CAR_RED)
        self._phase("3", "red", "green", config.DURATION_PEDESTRIAN_GREEN)
        self._phase("4", "red", "red", config.DURATION_PEDESTRIAN_RED)
        self._phase("5", "red_yellow", "red", config.DURATION_CAR_RED_YELLOW)
        self.show_ground_state()

    def run(self):
        """Endlosschleife für den echten Betrieb.

        Wartet auf einen Tastendruck und führt dann einen Zyklus aus.
        Drücke während des Zyklus werden nicht abgefragt und daher ignoriert.
        """
        self.show_ground_state()
        while True:
            self._hardware.wait_for_button()
            self.run_cycle()

    def run_demo(self):
        """Führt einen einzelnen Zyklus für den Mock-Betrieb aus."""
        self.show_ground_state()
        logger.info("Taster (simuliert) gedrückt – Zyklus startet.")
        self.run_cycle()

    def _phase(self, number, car, pedestrian, duration):
        """Zeigt eine Phase an, loggt sie und wartet die Dauer ab."""
        self._hardware.set_car(car)
        self._hardware.set_pedestrian(pedestrian)
        logger.info("Phase %s: Auto=%-10s Fußgänger=%-5s (%ss)",
                    number, car, pedestrian, duration)
        if duration > 0:
            time.sleep(duration)
