"""Aufbau der Hardware (LEDs und Taster).

Unterstützt echten Betrieb auf dem Raspberry Pi sowie Mock-Betrieb auf einem
Rechner ohne Hardware (gpiozero MockFactory).
"""

from gpiozero import Button, Device, LED
from gpiozero.pins.mock import MockFactory

from . import config


class Hardware:
    """Kapselt die fünf LEDs und den Taster.

    Die Phasenlogik arbeitet nur über die Methoden dieser Klasse und kennt
    daher keine GPIO-Pins. Dadurch läuft derselbe Code unverändert auf dem Pi
    und im Mock-Betrieb.
    """

    # Autoampel: (rot, gelb, grün)
    _CAR_STATES = {
        "green": (False, False, True),
        "yellow": (False, True, False),
        "red": (True, False, False),
        "red_yellow": (True, True, False),
        "off": (False, False, False),
    }

    # Fußgängerampel: (rot, grün)
    _PEDESTRIAN_STATES = {
        "red": (True, False),
        "green": (False, True),
        "off": (False, False),
    }

    def __init__(self, mock=False):
        """Baut die GPIO-Objekte auf.

        Args:
            mock: True -> simulierte Pins (MockFactory), kein Raspberry Pi nötig.
        """
        if mock:
            Device.pin_factory = MockFactory()

        self.car_red = LED(config.PIN_CAR_RED)
        self.car_yellow = LED(config.PIN_CAR_YELLOW)
        self.car_green = LED(config.PIN_CAR_GREEN)
        self.pedestrian_red = LED(config.PIN_PEDESTRIAN_RED)
        self.pedestrian_green = LED(config.PIN_PEDESTRIAN_GREEN)
        # Taster gegen GND, interner Pull-Up -> active low (Pin siehe config).
        self.button = Button(config.PIN_BUTTON, pull_up=True,
                             bounce_time=config.BOUNCE_TIME)

    def set_car(self, state):
        """Setzt die Autoampel auf einen benannten Zustand."""
        red, yellow, green = self._CAR_STATES[state]
        self.car_red.value = red
        self.car_yellow.value = yellow
        self.car_green.value = green

    def set_pedestrian(self, state):
        """Setzt die Fußgängerampel auf einen benannten Zustand."""
        red, green = self._PEDESTRIAN_STATES[state]
        self.pedestrian_red.value = red
        self.pedestrian_green.value = green

    def all_off(self):
        """Schaltet alle LEDs aus (sauberes Beenden)."""
        self.set_car("off")
        self.set_pedestrian("off")

    def wait_for_button(self):
        """Wartet auf einen frischen Tastendruck.

        Ein ggf. noch gedrückter Taster (z. B. während des laufenden Zyklus)
        wird zuerst wieder losgelassen, damit er nicht sofort erneut zählt.
        Die Entprellung übernimmt der Button selbst (bounce_time).
        """
        self.button.wait_for_release()
        self.button.wait_for_press()
