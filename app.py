"""Feinschliff – bringt deinen Text in Form. Lokale Prüfung von Erzählzeit, Perspektive, Satzbau, Wortwahl und mehr.
Start: python app.py  (öffnet http://127.0.0.1:8765)

Der Text steht in einer bearbeitbaren Box, Funde werden direkt darin markiert.
Prüfmodule: modules.py. Oberfläche: templates/index.html, static/app.css, static/app.js

Logging: Meldungen im Terminal, Stufe über LOG_LEVEL (DEBUG, INFO, WARNING). Es werden nie Textinhalte
und nie der API-Key protokolliert, nur Längen, Modul-Namen, Zeiten und Fehlerarten.
"""
import logging
import os
import platform
import socket
import shutil
import threading
import time
import webbrowser

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

import eigene_listen
from ai_check import KIFehler, MODELLE, ai_check, ai_schachtel, summe, umformulieren
from checker import PERSPEKTIVEN, SPACY_MODEL, STANDARD_ZEITEN, ZEITEN, check_text, get_nlp
from grundlagen import mask_dialog
from satzbau import MAX_KANDIDAT, schachtel_kandidaten
from modules import FARBEN, GRUPPEN, KI_NUR, NAMEN, OFFLINE, gewaehlt, lese_einstellungen, lese_offline

VERSION = "0.1.1"  # Versionsnummer: bei jeder Veröffentlichung hier und in CHANGELOG.md anpassen
try:
    PORT = int(os.environ.get("FEINSCHLIFF_PORT", 8765))  # per Umgebungsvariable änderbar
    if not 1 <= PORT <= 65535:
        raise ValueError
except ValueError:
    raise SystemExit("Die Umgebungsvariable FEINSCHLIFF_PORT muss eine Zahl zwischen 1 und 65535 sein, "
                     "zum Beispiel FEINSCHLIFF_PORT=8770.")
MAX_OFFLINE = 150_000  # Zeichen; längere Texte bitte abschnittsweise prüfen

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s", datefmt="%H:%M:%S",
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # eigene Meldungen reichen
log = logging.getLogger("erzaehlcheck")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Bytes; größer als jeder erlaubte Text

ERLAUBTE_HOSTS = {"127.0.0.1", "localhost", "[::1]"}  # nur diese Adressen darf der Browser ansprechen


class Eingabefehler(Exception):
    """Falsche oder fehlende Eingabe; die Meldung wird dem Nutzer direkt angezeigt."""


@app.errorhandler(Eingabefehler)
def _eingabe(e):
    log.info("Anfrage abgelehnt: %s", e)
    return jsonify(error=str(e)), 400


@app.errorhandler(KIFehler)
def _ki(e):
    log.warning("KI-Prüfung fehlgeschlagen: %s", e)
    return jsonify(error=str(e)), 400


@app.errorhandler(413)
def _zu_gross(e):
    return jsonify(error="Die Anfrage ist zu groß. Bitte den Text in Abschnitten prüfen."), 413


@app.before_request
def _nur_lokal():
    """Schützt vor fremden Webseiten im selben Browser (auch vor DNS-Rebinding): Die Anfrage muss an
    127.0.0.1 oder localhost gehen, und ein vorhandener Origin muss zu genau diesem Host gehören."""
    roh = request.host or ""
    host = roh.split("]")[0] + "]" if roh.startswith("[") else roh.split(":")[0]
    if host not in ERLAUBTE_HOSTS:
        log.warning("Anfrage mit fremdem Host abgelehnt: %s", host[:60].encode("ascii", "replace").decode())
        return jsonify(error="Anfrage mit fremdem Host abgelehnt. Die App ist nur über 127.0.0.1 oder localhost erreichbar."), 403
    herkunft = request.headers.get("Origin")
    if herkunft and herkunft.split("://", 1)[-1] != request.host:
        log.warning("Anfrage von fremder Herkunft abgelehnt")
        return jsonify(error="Anfrage von einer fremden Seite abgelehnt."), 403


@app.after_request
def _kopfzeilen(antwort):
    antwort.headers["X-Frame-Options"] = "DENY"
    antwort.headers["X-Content-Type-Options"] = "nosniff"
    antwort.headers["Referrer-Policy"] = "no-referrer"
    return antwort


@app.errorhandler(Exception)
def _unerwartet(e):
    if isinstance(e, HTTPException):
        return e
    log.exception("Unerwarteter Fehler bei %s", request.path)
    return jsonify(error=f"Unerwarteter Fehler ({type(e).__name__}). Die Einzelheiten stehen im "
                         "Terminal, in dem die App läuft."), 500


@app.get("/")
def index():
    cfg = {"zeiten": ZEITEN, "standard": list(STANDARD_ZEITEN), "module": NAMEN, "farben": FARBEN, "reihenfolge": [m["id"] for g in GRUPPEN for m in g["module"]],
           "gruppen": [{"name": g["name"], "farbe": g["farbe"]} for g in GRUPPEN]}
    return render_template("index.html", gruppen=GRUPPEN, modelle=list(MODELLE), cfg=cfg, version=VERSION)


def _json():
    """Der Body muss ein JSON-Objekt sein. Alles andere gilt als leere Anfrage."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _modell(data):
    m = data.get("model", "")
    return m if isinstance(m, str) else ""


def _sprache_ki(mods):
    """Einstellungen von „Rechtschreibung (KI)“, bereinigt: nur gültige Wörter, höchstens 50, Schalter als Wahrheitswert."""
    roh = mods.get("sprache_ki") if isinstance(mods, dict) else None
    if not isinstance(roh, dict):
        return None
    woerter = [w for w in sorted(eigene_listen.woerter_aus(roh.get("eigene", "") if isinstance(roh.get("eigene"), str) else ""))
               if eigene_listen.WORT.match(w)][:eigene_listen.MAX_NEU]
    dialog = roh.get("dialog")
    return {"dialog": dialog if isinstance(dialog, bool) else True, "eigene": ", ".join(woerter)}


def _lesen():
    data = _json()
    mods = data.get("modules")
    text = data.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise Eingabefehler("Bitte zuerst einen Text einfügen.")
    zeit_aktiv, allowed, perspektive = lese_einstellungen(mods)
    return data, mods, text, zeit_aktiv, allowed, perspektive


def _namen(ids):
    return ", ".join(f"„{NAMEN[i]}“" for i in ids)


def _lauf(ids):
    return "laufen" if len(ids) > 1 else "läuft"


def _ids(mods):
    return ",".join(i for i in mods if i in NAMEN) if isinstance(mods, dict) else "-"  # nur bekannte Namen ins Log


@app.post("/check")
def check():
    t0 = time.perf_counter()
    data, mods, text, zeit_aktiv, allowed, perspektive = _lesen()
    offline = lese_offline(mods)
    ki_gewaehlt = gewaehlt(mods, KI_NUR)
    if not (zeit_aktiv or perspektive != PERSPEKTIVEN[0] or offline):
        if ki_gewaehlt:
            raise Eingabefehler(f"{_namen(ki_gewaehlt)} {_lauf(ki_gewaehlt)} nur mit der KI-Prüfung.")
        raise Eingabefehler("Bitte mindestens eine Prüfung auswählen.")
    if len(text) > MAX_OFFLINE:
        raise Eingabefehler(f"Der Text ist zu lang ({len(text)} Zeichen, erlaubt sind {MAX_OFFLINE}). "
                            "Bitte in Abschnitten prüfen.")
    findings, spans, notes = check_text(text, perspektive, allowed, check_tense=zeit_aktiv, offline=offline)
    if ki_gewaehlt:
        notes.append(f"Nicht geprüft (nur mit KI-Prüfung): {_namen(ki_gewaehlt)}.")
    log.info("Prüfen (offline): Module=%s Zeichen=%d Wörter=%d Funde=%d Dauer=%.1fs",
             _ids(mods), len(text), len(text.split()), len(findings), time.perf_counter() - t0)
    return jsonify(findings=[vars(f) for f in findings], spans=spans, notes=notes)


@app.post("/check-ai")
def check_ai():
    t0 = time.perf_counter()
    data, mods, text, zeit_aktiv, allowed, perspektive = _lesen()
    stil = gewaehlt(mods, KI_NUR)
    uebersprungen = gewaehlt(mods, OFFLINE)
    schachtel = lese_offline(mods).get("schachtel")  # Offline-Modul mit KI-Variante
    haupt = zeit_aktiv or perspektive != PERSPEKTIVEN[0] or bool(stil)
    if not (haupt or schachtel):
        if uebersprungen:
            raise Eingabefehler(f"{_namen(uebersprungen)} {_lauf(uebersprungen)} nur mit „Prüfen“ (offline).")
        raise Eingabefehler("Bitte mindestens eine Prüfung auswählen.")
    modell = _modell(data)
    log.info("KI-Prüfung gestartet: Modell=%s Module=%s Zeichen=%d", modell if modell in MODELLE else "?", _ids(mods), len(text))
    findings, notes, usage = [], [], None
    if haupt:
        findings, spans, notes, usage = ai_check(
            text, perspektive, allowed or list(STANDARD_ZEITEN), modell, mit_zeit=zeit_aktiv, stil=stil,
            sprache=_sprache_ki(mods))
    else:
        spans = mask_dialog(text)[1]
    if schachtel:
        if len(text) > MAX_OFFLINE:
            raise Eingabefehler(f"Der Text ist zu lang ({len(text)} Zeichen, erlaubt sind {MAX_OFFLINE}). "
                                "Bitte in Abschnitten prüfen.")
        kand, gesamt, zu_lang = schachtel_kandidaten(text, schachtel["ab"])
        log.info("Schachtelsätze: %d Kandidaten ab Stufe %d, %d an die KI, %d zu lang", gesamt, schachtel["ab"], len(kand), zu_lang)
        if zu_lang:
            notes.append(f"Schachtelsätze (KI): {zu_lang} sehr lange „Sätze“ (über {MAX_KANDIDAT} Zeichen) wurden nicht an die KI geschickt. "
                         "Vermutlich fehlen dort Satzzeichen.")
        f2, n2, u2 = ai_schachtel(kand, modell)
        findings += f2
        notes += n2
        if gesamt > len(kand) + zu_lang:
            notes.append(f"Schachtelsätze (KI): Nur die {len(kand)} am tiefsten verschachtelten von {gesamt} "
                         "Sätzen wurden bewertet. Stufe in den Einstellungen erhöhen oder Text kürzen.")
        usage = summe(usage, u2) if usage or u2 else None
        findings.sort(key=lambda f: (f.start, -f.end))
    if uebersprungen:
        notes.append(f"Nicht geprüft (nur offline mit „Prüfen“): {_namen(uebersprungen)}.")
    usage = usage or {"input": 0, "output": 0, "usd": 0}
    log.info("KI-Prüfung fertig: Funde=%d Tokens=%d+%d ca. %s $ Dauer=%.1fs", len(findings),
             usage["input"], usage["output"], usage["usd"], time.perf_counter() - t0)
    return jsonify(findings=[vars(f) for f in findings], spans=spans, notes=notes, usage=usage)


@app.post("/umformulieren")
def umformulieren_route():
    """KI-Umformulierung eines einzelnen Satzes. Gesendet wird nur der Satz mit etwas Kontext."""
    t0 = time.perf_counter()
    data = _json()
    satz = data.get("satz", "")
    if not isinstance(satz, str) or not satz.strip():
        raise Eingabefehler("Kein Satz zum Umformulieren übergeben.")
    zeit_aktiv, allowed, perspektive = lese_einstellungen(data.get("modules"))
    modell = _modell(data)
    log.info("Umformulierung gestartet: Modell=%s Satzlänge=%d", modell if modell in MODELLE else "?", len(satz))
    fassungen, usage = umformulieren(satz, str(data.get("davor", ""))[-2000:], str(data.get("danach", ""))[:2000],
                                     str(data.get("hinweis", ""))[:500], perspektive, allowed, zeit_aktiv, modell)
    log.info("Umformulierung fertig: %d Fassungen Tokens=%d+%d ca. %s $ Dauer=%.1fs", len(fassungen),
             usage["input"], usage["output"], usage["usd"], time.perf_counter() - t0)
    return jsonify(fassungen=fassungen, usage=usage)


@app.post("/liste-uebernehmen")
def liste_uebernehmen():
    """Speichert Wörter aus einem Eingabefeld dauerhaft in der eigenen Liste (listen/*_eigene.txt)."""
    # Host und Herkunft prüft _nur_lokal() für alle Anfragen
    data = _json()
    liste = data.get("liste", "")
    try:
        neu, schon = eigene_listen.hinzufuegen(liste if isinstance(liste, str) else "", str(data.get("woerter", ""))[:5000])
    except ValueError as e:
        raise Eingabefehler(str(e))
    return jsonify(neu=neu, schon=schon, datei=f"{eigene_listen.ORDNER}/{eigene_listen.DATEIEN[liste]}")


def _start_info():
    java = shutil.which("java")
    log.info("Feinschliff %s startet (Python %s, %s)", VERSION, platform.python_version(), platform.system())
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    log.info("spaCy-Modell: %s | Port: %d | KI-Key gesetzt: %s | Java gefunden: %s",
             SPACY_MODEL, PORT, "ja" if key else "nein",
             "ja" if java else "nein (Rechtschreibung offline nicht verfügbar)")
    if os.environ.get("ANTHROPIC_BASE_URL"):
        log.warning("ANTHROPIC_BASE_URL ist gesetzt: KI-Anfragen gehen NICHT an die Anthropic-API, sondern an diesen Endpunkt. "
                    "Entferne die Variable, wenn das nicht gewollt ist.")


def _port_frei():
    """True, wenn auf 127.0.0.1 noch niemand an diesem Port lauscht."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", PORT)) != 0


if __name__ == "__main__":
    _start_info()
    if not _port_frei():
        raise SystemExit(f"Port {PORT} ist belegt, vermutlich läuft Feinschliff schon oder ein anderes Programm "
                         f"nutzt ihn. Mit anderem Port starten, zum Beispiel: FEINSCHLIFF_PORT={PORT + 5} python app.py")
    get_nlp()  # Modell vorab laden
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    log.info("Bereit unter http://127.0.0.1:%d (Beenden mit Strg+C)", PORT)
    app.run(host="127.0.0.1", port=PORT)
