"""Eigene Wortlisten des Nutzers: Dateien im Ordner eigene-listen/.

Die mitgelieferten Startlisten (listen/*.txt) bleiben unberührt. Wörter, die du in der App mit
„In Liste übernehmen“ speicherst, landen hier und gelten bei jeder Prüfung, ohne Neustart.
Der Ordner kann Namen aus deinem Text enthalten und gehört deshalb nicht in ein öffentliches Repo.
Zum Sichern genügt es, den ganzen Ordner zu kopieren. Die Dateinamen dürfen nicht geändert werden.
"""
import logging
import re
import shutil
from pathlib import Path

ORDNER = "eigene-listen"
LISTEN = Path(__file__).parent / ORDNER
ALT = Path(__file__).parent / "listen"  # frühere Ablage: listen/*_eigene.txt
log = logging.getLogger("erzaehlcheck.listen")

# Schlüssel (aus modules.py) -> Dateiname. Nur diese Dateien dürfen geschrieben werden.
DATEIEN = {
    "fuellwoerter_eigene": "fuellwoerter.txt",
    "sprechverben_eigene": "sprechverben.txt",
    "gefuehle_eigene": "gefuehle.txt",
    "wiederholung_ausnahmen_eigene": "wiederholung_ausnahmen.txt",
    "namen_eigene": "namen.txt",
}

KOPF = ("# Deine eigenen Wörter. Ein Wort pro Zeile, Kleinbuchstaben.\n"
        "# Diese Datei wird von der App geschrieben (Knopf „In Liste übernehmen“) und kann von Hand bearbeitet werden.\n"
        "# Sie kann Namen aus deinem Text enthalten: nicht veröffentlichen.\n")
WORT = re.compile(r"^[\w'’-]{1,40}$")
MAX_ZEILEN = 2000
MAX_NEU = 50


def _umziehen():
    """Alte Dateien aus listen/*_eigene.txt einmalig in den neuen Ordner verschieben."""
    for schluessel, name in DATEIEN.items():
        alt, neu = ALT / f"{schluessel}.txt", LISTEN / name
        if alt.exists() and not neu.exists():
            LISTEN.mkdir(exist_ok=True)
            shutil.move(str(alt), str(neu))
            log.info("Eigene Liste umgezogen: %s -> %s/%s", alt.name, ORDNER, name)


def _pfad(schluessel):
    if schluessel not in DATEIEN:
        raise ValueError("Unbekannte Liste.")
    _umziehen()
    return LISTEN / DATEIEN[schluessel]


def _zeilen(pfad):
    try:
        text = pfad.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return [z.strip().lower() for z in text.splitlines() if z.strip() and not z.lstrip().startswith("#")]


def lesen(schluessel):
    """Die gespeicherten eigenen Wörter als Menge (leer, wenn es die Datei noch nicht gibt)."""
    return set(_zeilen(_pfad(schluessel)))


def woerter_aus(eingabe):
    """Wörter aus einem Eingabefeld (Komma oder Zeilenumbruch getrennt) als Menge, Kleinbuchstaben."""
    return {w.strip().lower() for w in re.split(r"[,\n]", eingabe or "") if w.strip()}


def hinzufuegen(schluessel, eingabe):
    """Hängt neue Wörter an die Datei an. Gibt (Anzahl neu, Anzahl schon vorhanden) zurück.

    Raises ValueError mit einer Meldung für den Nutzer bei ungültigen Wörtern oder zu vielen Einträgen.
    """
    pfad = _pfad(schluessel)
    neue = woerter_aus(eingabe)
    if not neue:
        raise ValueError("Das Feld ist leer.")
    if len(neue) > MAX_NEU:
        raise ValueError(f"Zu viele Wörter auf einmal (höchstens {MAX_NEU}).")
    ungueltig = sorted(w for w in neue if not WORT.match(w))
    if ungueltig:
        raise ValueError("Nicht übernommen, ungültige Zeichen oder zu lang: " + ", ".join(ungueltig[:5]))
    vorhanden = set(_zeilen(pfad))
    dazu = sorted(neue - vorhanden)
    if len(vorhanden) + len(dazu) > MAX_ZEILEN:
        raise ValueError("Die Liste ist voll.")
    if dazu:
        LISTEN.mkdir(exist_ok=True)
        neu_datei = not pfad.exists()
        with pfad.open("a", encoding="utf-8") as f:
            if neu_datei:
                f.write(KOPF)
            f.write("".join(w + "\n" for w in dazu))
    log.info("Liste %s: %d neu, %d schon vorhanden", schluessel, len(dazu), len(neue) - len(dazu))
    return len(dazu), len(neue) - len(dazu)
