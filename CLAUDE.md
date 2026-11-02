# CLAUDE.md — Fußgängerampel mit Raspberry Pi

Diese Datei ist die verbindliche Projektbeschreibung. Claude Code soll sich bei
allen Änderungen an dieses Dokument halten. Abweichungen oder Erweiterungen
vorher mit mir absprechen.

## Projektziel

Eine einfache Fußgängerampel mit Raspberry Pi:

- **Autoampel**: Rot, Gelb, Grün
- **Fußgängerampel**: Rot, Grün
- **Taster** als Fußgänger-Knopf, mit dem Fußgänger Grün anfordern

Kontext: Berufsschulprojekt. Der Code soll einfach lesbar und nachvollziehbar
sein — keine überengineeringte Lösung.

## Wichtige Randbedingung: noch keine Hardware

Ich besitze **noch keinen Raspberry Pi und keine Bauteile**. Deshalb gilt:

- Der Code muss **auf macOS ohne angeschlossene Hardware lauffähig sein**.
- Es darf keine Bibliothek benötigt werden, die nur auf dem Pi installiert ist
  (kein direktes `RPi.GPIO`).
- Standardweg: `gpiozero`, das mit der `MockFactory` simulierte Pins bietet.
- Ein Start ohne Pi (Mock-Betrieb) muss über einen Schalter möglich sein
  (z. B. `--mock` oder `AMPEL_MOCK=1`), damit die Phasen ohne Hardware im
  Terminal nachvollziehbar ablaufen (Zustandswechsel loggen).
- Die Pinbelegung und die Logik müssen so getrennt sein, dass derselbe Code
  später unverändert auf dem Pi läuft.

## Hardware

| Bauteil                    | Anzahl |
| -------------------------- | ------ |
| Raspberry Pi (GPIO)        | 1      |
| LED rot, gelb, grün (Auto) | 3      |
| LED rot, grün (Fußgänger)  | 2      |
| Taster                     | 1      |
| Widerstände 220 Ω          | 5      |
| Breadboard + Jumper-Kabel  | –      |

### Pinbelegung (BCM-Nummerierung)

| Funktion        | GPIO |
| --------------- | ---- |
| Auto Rot        | 17   |
| Auto Gelb       | 27   |
| Auto Grün       | 22   |
| Fußgänger Rot   | 23   |
| Fußgänger Grün  | 24   |
| Taster          | 5    |

- Jede LED über einen 220-Ω-Widerstand an Masse.
- Taster zwischen GPIO 5 und GND, interner Pull-Up aktiv
  (`Button(..., pull_up=True)`, Logik also **active low**).
- Die Pins stehen zentral in der Konfiguration und werden nirgends im Code
  hartkodiert.

## Verhalten / Zustandsautomat

Grundzustand: Auto **Grün**, Fußgänger **Rot**.

| # | Phase           | Auto        | Fußgänger | Dauer (Standard) | Übergang                     |
| - | --------------- | ----------- | --------- | ---------------- | ---------------------------- |
| 0 | Warten          | Grün        | Rot       | –                | Taster gedrückt → Phase 1    |
| 1 | Auto Gelb       | Gelb        | Rot       | 2 s              | automatisch → Phase 2        |
| 2 | Auto Rot        | Rot         | Rot       | 1 s (Räumzeit)   | automatisch → Phase 3        |
| 3 | Fußgänger Grün  | Rot         | Grün      | 8 s              | automatisch → Phase 4        |
| 4 | Fußgänger Rot   | Rot         | Rot       | 1 s              | automatisch → Phase 5        |
| 5 | Auto Rot-Gelb   | Rot + Gelb  | Rot       | 2 s              | automatisch → Phase 0        |

```
        [0] Auto Grün / Fuß Rot
             │ Taster
             ▼
        [1] Auto Gelb  (2 s)
             ▼
        [2] Auto Rot   (1 s)
             ▼
        [3] Fuß Grün   (8 s)
             ▼
        [4] Fuß Rot    (1 s)
             ▼
        [5] Auto Rot-Gelb (2 s)
             └──────────────► zurück zu [0]
```

### Regeln

- Die Autoampel zeigt **immer genau eine** der Kombinationen
  `Grün`, `Gelb`, `Rot`, `Rot+Gelb` — nie zwei „Fahr“-Signale gleichzeitig.
- Autoampel und Fußgängerampel sind **niemals gleichzeitig Grün**.
- Der Taster wird entprellt (`bounce_time ≈ 0.3 s`).
- Drücke während eines laufenden Anforderungszyklus (Phasen 1–5) werden
  **ignoriert** — es wird kein zweiter Zyklus vorgemerkt.
- Nach Phase 5 beginnt wieder Phase 0; der nächste Tastendruck startet einen
  neuen Zyklus.
- Beim Start und bei Programmende sind alle LEDs aus (bzw. Grundzustand).

### Timing

Alle Zeiten gehören in die Konfiguration (z. B. `config.py`) als benannte
Konstanten — keine Magic Numbers im Ablaufcode. Die Werte oben sind
Standardwerte und dürfen für Tests/Demo angepasst werden.

## Software-Vorgaben

- **Sprache**: Python 3
- **Bibliotheken**: `gpiozero` (LED, Button, MockFactory), `pytest` für Tests.
  Keine weiteren Abhängigkeiten ohne Rückfrage; `requirements.txt` pflegen.
- **Struktur** (Vorschlag, darf sinnvoll angepasst werden):

  ```
  ampel/
    __init__.py
    config.py       # Pins, Zeiten, Mock-Schalter
    hardware.py     # Aufbau der LED-/Button-Objekte, Mock vs. echtes GPIO
    controller.py   # Zustandsautomat / Phasenlogik
    main.py         # Einstiegspunkt, --mock, sauberes Beenden
  tests/
    test_controller.py
  requirements.txt
  README.md
  ```

- **Trennung**: Die Phasenlogik darf keine GPIO-Pins direkt kennen. Sie
  arbeitet mit einer kleinen Hardware-Schnittstelle (z. B. Methoden wie
  `set_car("green")`, `pedestrian_button_pressed()`), damit sie mit einem Fake
  getestet werden kann.
- **Ablauf**: Ein einfacher, sequenzieller Ablauf (eine Funktion pro Phase) ist
  ausdrücklich in Ordnung und gegenüber einer Event-Loop bevorzugt, solange er
  lesbar bleibt.
- **Beenden**: `Ctrl+C` muss die LEDs sauber ausschalten (try/finally).
- **Logging**: Jeder Phasenwechsel wird mit Zeitstempel geloggt, damit man im
  Mock-Betrieb den Ablauf sieht.
- **Kommentare und Docstrings auf Deutsch**, Bezeichner im Code auf Englisch.
- Tests müssen auf macOS **ohne Hardware** laufen (`pytest`).

## Nicht-Ziele (nur nach ausdrücklicher Anforderung)

- Kein Blinken der Fußgängerampel, kein Signalton, keine Anzeige der
  Restzeit, keine Verkehrssensoren, keine zweite Fahrspur.
- Keine Weboberfläche, keine Datenbank, kein Docker.
- Keine Klassenhierarchie oder Abstraktionsebene, die über das oben
  beschriebene Maß hinausgeht.

## Abnahmekriterien

- [ ] `python -m ampel.main --mock` läuft ohne Pi und zeigt den kompletten
      Zyklus im Terminal.
- [ ] Ohne Tastendruck bleibt die Anlage in Phase 0 (Auto Grün, Fuß Rot).
- [ ] Ein Tastendruck führt exakt den Zyklus 1 → 5 → 0 aus.
- [ ] Zu keinem Zeitpunkt sind Auto- und Fußgängerampel gleichzeitig Grün.
- [ ] Pins und Zeiten sind nur in der Konfiguration definiert.
- [ ] `pytest` läuft auf macOS ohne Hardware fehlerfrei durch.
- [ ] `Ctrl+C` schaltet alle LEDs aus.
- [ ] `README.md` beschreibt Start im Mock-Betrieb und (später) auf dem Pi.

## Arbeitsweise für Claude Code

- Vor dem Coden kurz den Plan nennen, dann umsetzen — kein ungefragtes
  Erweitern des Funktionsumfangs.
- Bei widersprüchlichen oder fehlenden Angaben fragen, statt Annahmen still
  einzubauen.
- Keine echten GPIO-Zugriffe im Test; immer Fakes/Mock verwenden.
- Änderungen am Verhalten immer hier in dieser Datei nachziehen.
