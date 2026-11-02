# Ampelschaltung

Eine einfache Fußgängerampel mit Raspberry Pi (Berufsschulprojekt).

## Überblick

- **Autoampel**: Rot, Gelb, Grün
- **Fußgängerampel**: Rot, Grün
- **Taster** als Fußgänger-Knopf

Grundzustand: Auto **Grün**, Fußgänger **Rot**. Ein Tastendruck startet den
Ablauf: Auto Gelb → Auto Rot → Fußgänger Grün → Fußgänger Rot → Auto Rot+Gelb
→ zurück zu Auto Grün.

## Projektstruktur

```
ampel/
  __init__.py
  config.py       # Pins, Zeiten, Mock-Schalter
  hardware.py     # LED-/Button-Aufbau, Mock vs. echtes GPIO
  controller.py   # Zustandsautomat / Phasenlogik
  main.py         # Einstiegspunkt, --mock, sauberes Beenden
tests/
  test_controller.py
requirements.txt
```

## Einrichtung

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Start im Mock-Betrieb (ohne Raspberry Pi)

```
.venv/bin/python -m ampel.main --mock
```

oder über die Umgebungsvariable:

```
AMPEL_MOCK=1 .venv/bin/python -m ampel.main
```

Der Phasenablauf wird mit Zeitstempeln im Terminal geloggt. Beenden mit
`Ctrl+C` schaltet alle LEDs aus.

## Start auf dem Raspberry Pi (später)

```
python -m ampel.main
```

Die Pinbelegung (BCM-Nummerierung) und die Zeiten stehen zentral in
`ampel/config.py`.

## Tests

```
.venv/bin/pytest
```

Die Tests laufen ohne Hardware — sie verwenden einen Fake statt echtem GPIO.
