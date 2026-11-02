"""Tests für die Weboberfläche (VirtualHardware und Seite)."""

from ampel.controller import Controller
from ampel.web import PAGE, VirtualHardware


def test_virtual_hardware_snapshot():
    hw = VirtualHardware()
    hw.set_car("green")
    hw.set_pedestrian("red")
    assert hw.snapshot() == {"car": "green", "pedestrian": "red"}


def test_virtual_hardware_all_off():
    hw = VirtualHardware()
    hw.set_car("red_yellow")
    hw.set_pedestrian("green")
    hw.all_off()
    assert hw.snapshot() == {"car": "off", "pedestrian": "off"}


def test_controller_drives_virtual_hardware(monkeypatch):
    """Der Zustandsautomat arbeitet auch mit der virtuellen Hardware."""
    monkeypatch.setattr("ampel.controller.time.sleep", lambda seconds: None)
    hw = VirtualHardware()
    ctrl = Controller(hw)
    ctrl.show_ground_state()
    assert hw.snapshot() == {"car": "green", "pedestrian": "red"}
    ctrl.run_cycle()
    assert hw.snapshot() == {"car": "green", "pedestrian": "red"}


def test_page_contains_expected_markers():
    assert "Fußgängerampel" in PAGE
    assert "/state" in PAGE
