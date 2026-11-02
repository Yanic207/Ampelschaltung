"""Zentrale Konfiguration der Fußgängerampel.

Hier stehen alle Pins (BCM-Nummerierung), Zeiten und der Mock-Schalter.
Hardware-Aufbau und Phasenlogik lesen ihre Werte ausschließlich von hier —
nirgends sonst werden Pins oder Zeiten hartkodiert.
"""

# --- Mock-Betrieb -----------------------------------------------------------
# Über die Umgebungsvariable AMPEL_MOCK=1 (oder das Flag --mock) startet die
# Ampel ohne Raspberry Pi und ohne echte Hardware.
MOCK_ENV_VAR = "AMPEL_MOCK"

# --- Pinbelegung (BCM-Nummerierung) ----------------------------------------
PIN_CAR_RED = 17           # Auto Rot
PIN_CAR_YELLOW = 27        # Auto Gelb
PIN_CAR_GREEN = 22         # Auto Grün
PIN_PEDESTRIAN_RED = 23    # Fußgänger Rot
PIN_PEDESTRIAN_GREEN = 24  # Fußgänger Grün
PIN_BUTTON = 5             # Taster (gegen GND, Pull-Up aktiv -> active low)

# --- Zeiten (Sekunden) -----------------------------------------------------
# Standardwerte laut Projektbeschreibung; dürfen für Tests/Demo angepasst werden.
DURATION_CAR_YELLOW = 2.0        # Phase 1: Auto Gelb
DURATION_CAR_RED = 1.0           # Phase 2: Auto Rot (Räumzeit)
DURATION_PEDESTRIAN_GREEN = 8.0  # Phase 3: Fußgänger Grün
DURATION_PEDESTRIAN_RED = 1.0    # Phase 4: Fußgänger Rot
DURATION_CAR_RED_YELLOW = 2.0    # Phase 5: Auto Rot+Gelb

# --- Taster -----------------------------------------------------------------
BOUNCE_TIME = 0.3  # Entprellzeit des Tasters in Sekunden
