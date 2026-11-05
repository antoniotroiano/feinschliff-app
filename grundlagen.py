"""Grundbausteine, die alle Prüfmodule brauchen: der Fund (Finding) und die Erkennung direkter Rede.

Steht in einer eigenen Datei, damit checker.py und die Prüfmodule einander nicht gegenseitig importieren müssen.
"""
import re
from dataclasses import dataclass

QUOTE_PATTERN = re.compile(r'„[^“”"]*[“”"]|»[^«]*«|«[^»]*»|"[^"]*"|“[^”]*”')


@dataclass
class Finding:
    start: int
    end: int
    level: str     # Dringlichkeit: "rot" (Verstoß) | "gelb" (prüfen) | "blau" (Vorschlag)
    module: str    # Modul-ID, siehe modules.py
    tense: str     # kurze Bezeichnung des Fundes
    message: str
    ki: bool = False
    vorschlag: str = ""   # KI: Ersatztext für genau die markierte Stelle (leer = keiner)


def mask_dialog(text: str):
    """Ersetzt Dialoge durch Leerzeichen gleicher Länge (Offsets bleiben erhalten)."""
    spans = [(m.start(), m.end()) for m in QUOTE_PATTERN.finditer(text)]
    masked = list(text)
    for s, e in spans:
        for i in range(s, e):
            if masked[i] != "\n":
                masked[i] = " "
    return "".join(masked), spans
