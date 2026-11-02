"""Tests für den Zustandsautomaten der Fußgängerampel.

Die Tests laufen ohne Hardware: Statt echtem GPIO wird eine Fake-Klasse
verwendet, die alle Aufrufe aufzeichnet. ``time.sleep`` wird deaktiviert.
"""

import pytest

from ampel.controller import Controller


class FakeHardware:
    """Zeichnet alle Zustandsänderungen auf, statt echte Pins anzusteuern."""

    def __init__(self):
        self.car = "off"
        self.pedestrian = "off"
        # (auto, fußgänger) nach jeder set_pedestrian-/all_off-Änderung
        self.committed = []
        # (auto, fußgänger) nach jeder einzelnen Änderung (inkl. Zwischenschritte)
        self.all_states = []
        self.wait_calls = 0

    def set_car(self, state):
        self.car = state
        self.all_states.append((self.car, self.pedestrian))

    def set_pedestrian(self, state):
        self.pedestrian = state
        self.all_states.append((self.car, self.pedestrian))
        self.committed.append((self.car, self.pedestrian))

    def all_off(self):
        self.car = "off"
        self.pedestrian = "off"
        self.all_states.append((self.car, self.pedestrian))
        self.committed.append((self.car, self.pedestrian))

    def wait_for_button(self):
        self.wait_calls += 1


@pytest.fixture
def controller(monkeypatch):
    """Liefert einen Controller mit Fake-Hardware und deaktiviertem sleep."""
    monkeypatch.setattr("ampel.controller.time.sleep", lambda seconds: None)
    hardware = FakeHardware()
    return Controller(hardware), hardware


# Erwartete Phasenfolge eines kompletten Zyklus (Auto, Fußgänger).
EXPECTED_CYCLE = [
    ("green", "red"),       # Phase 0: Grundzustand
    ("yellow", "red"),      # Phase 1: Auto Gelb
    ("red", "red"),         # Phase 2: Auto Rot (Räumzeit)
    ("red", "green"),       # Phase 3: Fußgänger Grün
    ("red", "red"),         # Phase 4: Fußgänger Rot
    ("red_yellow", "red"),  # Phase 5: Auto Rot+Gelb
    ("green", "red"),       # zurück zu Phase 0
]


def test_ground_state(controller):
    """Der Grundzustand ist Auto Grün / Fußgänger Rot."""
    ctrl, hw = controller
    ctrl.show_ground_state()
    assert hw.committed[-1] == ("green", "red")


def test_cycle_sequence(controller):
    """Ein Tastendruck führt exakt die Phasen 0 → 1 → … → 5 → 0 aus."""
    ctrl, hw = controller
    ctrl.run_demo()
    assert hw.committed == EXPECTED_CYCLE


def test_never_both_green(controller):
    """Auto- und Fußgängerampel sind zu keinem Zeitpunkt gleichzeitig Grün."""
    ctrl, hw = controller
    ctrl.run_demo()
    for car, pedestrian in hw.all_states:
        assert not (car == "green" and pedestrian == "green")


def test_car_signal_always_valid(controller):
    """Die Autoampel zeigt immer genau eine erlaubte Kombination."""
    allowed = {"green", "yellow", "red", "red_yellow", "off"}
    ctrl, hw = controller
    ctrl.run_demo()
    for car, _ in hw.all_states:
        assert car in allowed


def test_press_during_cycle_ignored(controller):
    """Während eines Zyklus wird der Taster nicht abgefragt.

    Die Phasen 1–5 laufen sequenziell ab; ein Druck dazwischen wird nicht
    vorgemerkt und startet keinen zweiten Zyklus.
    """
    ctrl, hw = controller
    ctrl.run_cycle()
    assert hw.wait_calls == 0


class _StopRun(Exception):
    """Bricht die Endlosschleife in ``run`` kontrolliert ab."""


def test_run_waits_before_each_cycle(monkeypatch):
    """``run`` wartet vor jedem Zyklus erneut auf den Taster."""
    monkeypatch.setattr("ampel.controller.time.sleep", lambda seconds: None)
    hw = FakeHardware()
    ctrl = Controller(hw)

    calls = []

    def wait_for_button():
        calls.append(1)
        if len(calls) == 2:
            raise _StopRun()

    hw.wait_for_button = wait_for_button

    with pytest.raises(_StopRun):
        ctrl.run()

    # Erster Durchlauf: warten -> Zyklus -> erneut warten (abgebrochen).
    assert len(calls) == 2
    assert hw.committed == EXPECTED_CYCLE
