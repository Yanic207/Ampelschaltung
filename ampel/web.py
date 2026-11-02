"""Kleine Weboberfläche mit Live-Simulation der Fußgängerampel.

Start:
    python -m ampel.web

Danach im Browser öffnen: http://localhost:8000

Die Simulation läuft ohne Hardware: Der bestehende Zustandsautomat wird in
einem Hintergrund-Thread ausgeführt, ein virtueller Hardware-Ersatz merkt sich
den aktuellen Zustand, und ein einfacher HTTP-Server aus der Python-
Standardbibliothek liefert ihn als JSON an die Seite aus.
"""

import argparse
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config
from .controller import Controller

logger = logging.getLogger(__name__)


class VirtualHardware:
    """Virtueller Hardware-Ersatz für die Weboberfläche (kein echtes GPIO).

    Erfüllt dieselbe Schnittstelle wie ``hardware.Hardware``, merkt sich aber
    nur den aktuellen Zustand in einem Thread-sicheren Feld.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._car = "off"
        self._pedestrian = "off"

    def set_car(self, state):
        with self._lock:
            self._car = state

    def set_pedestrian(self, state):
        with self._lock:
            self._pedestrian = state

    def all_off(self):
        with self._lock:
            self._car = "off"
            self._pedestrian = "off"

    def wait_for_button(self):
        # Simulation: nach einer kurzen Pause "drückt" ein Fußgänger.
        time.sleep(config.SIMULATION_BUTTON_DELAY)

    def snapshot(self):
        """Liefert den aktuellen Zustand als dict (für die JSON-Ausgabe)."""
        with self._lock:
            return {"car": self._car, "pedestrian": self._pedestrian}


# Die HTML-Seite zeigt zwei Ampeln und holt den Zustand per Polling.
PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fußgängerampel – Simulation</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    margin: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    padding: 1rem;
  }
  h1 { margin: 0; font-size: 1.4rem; }
  .signals { display: flex; gap: 3rem; flex-wrap: wrap; justify-content: center; }
  .signal { text-align: center; }
  .signal h2 { margin: 0 0 .6rem; font-size: 1rem; }
  .housing {
    display: inline-flex;
    flex-direction: column;
    gap: .6rem;
    padding: .8rem;
    background: #2a2a2a;
    border-radius: .7rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, .3);
  }
  .bulb {
    width: 3.2rem;
    height: 3.2rem;
    border-radius: 50%;
    background: #3c3c3c;
    transition: background .15s, box-shadow .15s;
  }
  .bulb.red    { background: #e21; box-shadow: 0 0 14px #e21; }
  .bulb.yellow { background: #ec0; box-shadow: 0 0 14px #ec0; }
  .bulb.green  { background: #1c1; box-shadow: 0 0 14px #1c1; }
  #status { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
</style>
</head>
<body>
  <h1>Fußgängerampel – Simulation</h1>
  <div class="signals">
    <div class="signal">
      <h2>Auto</h2>
      <div class="housing">
        <div class="bulb" id="car-red"></div>
        <div class="bulb" id="car-yellow"></div>
        <div class="bulb" id="car-green"></div>
      </div>
    </div>
    <div class="signal">
      <h2>Fußgänger</h2>
      <div class="housing">
        <div class="bulb" id="ped-red"></div>
        <div class="bulb" id="ped-green"></div>
      </div>
    </div>
  </div>
  <div id="status">Verbinde …</div>

<script>
  // Zustand -> welche Lampen leuchten: (rot, gelb, grün)
  var CAR = {
    green:      [0, 0, 1],
    yellow:     [0, 1, 0],
    red:        [1, 0, 0],
    red_yellow: [1, 1, 0],
    off:        [0, 0, 0]
  };
  // Zustand -> (rot, grün)
  var PED = {
    red:   [1, 0],
    green: [0, 1],
    off:   [0, 0]
  };
  // Deutsche Beschriftung für den Status-Text
  var LABEL = {
    green: "grün", yellow: "gelb", red: "rot",
    red_yellow: "rot+gelb", off: "aus"
  };

  var carIds = ["car-red", "car-yellow", "car-green"];
  var pedIds = ["ped-red", "ped-green"];

  function applyBulbs(ids, states) {
    ids.forEach(function (id, i) {
      var el = document.getElementById(id);
      var color = id.split("-")[1];  // "red", "yellow", "green"
      el.className = "bulb" + (states[i] ? " " + color : "");
    });
  }

  function refresh() {
    fetch("/state")
      .then(function (r) { return r.json(); })
      .then(function (s) {
        applyBulbs(carIds, CAR[s.car] || CAR.off);
        applyBulbs(pedIds, PED[s.pedestrian] || PED.off);
        document.getElementById("status").textContent =
          "Auto: " + (LABEL[s.car] || s.car) +
          "  ·  Fußgänger: " + (LABEL[s.pedestrian] || s.pedestrian);
      })
      .catch(function () {
        document.getElementById("status").textContent = "Keine Verbindung";
      });
  }

  refresh();
  setInterval(refresh, 250);
</script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    """Beantwortet Anfragen: ``/`` liefert die Seite, ``/state`` den Zustand."""

    hardware = None  # wird in serve() gesetzt

    def do_GET(self):
        if self.path == "/state":
            self._send(json.dumps(self.hardware.snapshot()),
                       "application/json; charset=utf-8")
        elif self.path in ("/", "/index.html"):
            self._send(PAGE, "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def _send(self, body, content_type):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        logger.info("Web: " + fmt % args)


def _run_simulation(hardware):
    """Führt den Zustandsautomaten in einer Endlosschleife aus."""
    Controller(hardware).run()


def serve(host="127.0.0.1", port=8000):
    """Startet die Simulation (Hintergrund-Thread) und den HTTP-Server."""
    hardware = VirtualHardware()
    _Handler.hardware = hardware

    thread = threading.Thread(target=_run_simulation, args=(hardware,),
                              name="ampel-simulation", daemon=True)
    thread.start()

    server = ThreadingHTTPServer((host, port), _Handler)
    logger.info("Weboberfläche läuft: http://%s:%s (Beenden mit Ctrl+C)", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Weboberfläche beendet.")
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fußgängerampel – Weboberfläche")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Adresse, auf der der Server lauscht (Standard: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port (Standard: 8000)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    serve(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    main()
