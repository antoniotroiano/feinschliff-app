"""Sprachrichtigkeit: Rechtschreibung/Grammatik (LanguageTool, offline) und einheitliche Schreibweisen.

LanguageTool braucht Java. Das Paket language_tool_python lädt LanguageTool beim ersten Start einmalig
herunter (ca. 260 MB, im Benutzer-Cache). Der Start der Java-Hilfe dauert einige Sekunden und erfolgt
erst bei der ersten Prüfung.
"""
import atexit
import logging
import re
import shutil
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import eigene_listen
from checker import QUOTE_PATTERN, Finding

LISTEN = Path(__file__).parent / "listen"
log = logging.getLogger("erzaehlcheck.lt")

# LanguageTool-Kategorien, die wir nicht melden (Stil prüfen wir mit eigenen Modulen)
STIL_KATEGORIEN = {"STYLE", "REDUNDANCY", "PLAIN_ENGLISH", "GENDER_NEUTRALITY", "CREATIVE_WRITING", "COLLOQUIALISMS"}

_tool = None


def _lt():
    """Startet LanguageTool beim ersten Aufruf und behält es für die weiteren."""
    global _tool
    if _tool is None:
        import language_tool_python
        log.info("LanguageTool startet (beim ersten Mal wird es heruntergeladen, das kann dauern) …")
        t0 = time.perf_counter()
        _tool = language_tool_python.LanguageTool("de-DE")
        atexit.register(_tool.close)
        log.info("LanguageTool bereit (%.1fs)", time.perf_counter() - t0)
    return _tool


def _woerter(eingabe):
    return {w.strip().lower() for w in eingabe.split(",") if w.strip()}


def languagetool(text, spans, einst, notes):
    """Rechtschreibung (Rot) sowie Grammatik und Zeichensetzung (Gelb)."""
    dialog_mit = einst.get("dialog", True)
    eigene = _woerter(einst.get("eigene", "")) | eigene_listen.lesen("namen_eigene")
    try:
        treffer = _lt().check(text)
    except Exception as e:  # fehlendes Java, Download gescheitert, Prozessfehler …
        log.exception("LanguageTool nicht verfügbar")
        if shutil.which("java") is None:
            grund = "Java wurde nicht gefunden. Bitte Java installieren (siehe README)."
        else:
            grund = ("LanguageTool konnte nicht starten oder herunterladen. Beim ersten Mal braucht der "
                     "Download Internet. Einzelheiten stehen im Terminal.")
        notes.append(f"Rechtschreibung und Grammatik konnten nicht geprüft werden: {grund} ({type(e).__name__})")
        return []
    gross = Counter(re.findall(r"\b[A-ZÄÖÜ]\w+\b", text))  # mehrfach genannte Großwörter gelten als Namen
    out, uebersprungen = [], set()
    for m in treffer:
        start, laenge = m.offset, max(m.error_length, 1)
        wort = text[start:start + laenge]
        kategorie = (m.category or "").upper()
        regel = m.rule_id or ""
        if kategorie in STIL_KATEGORIEN:
            continue
        if not dialog_mit and any(a <= start < b for a, b in spans):
            continue
        rechtschreibung = kategorie == "TYPOS" or "SPELLER" in regel or "MORFOLOGIK" in regel
        # Eigenname: vom Nutzer genannt, oder ein unbekanntes Großwort, das mehrfach im Text steht.
        # Gezielte Regeln („seid“ statt „seit“) bleiben davon unberührt.
        unbekannt = "SPELLER_RULE" in regel or "MORFOLOGIK" in regel
        if rechtschreibung and (wort.lower() in eigene or (unbekannt and wort[:1].isupper() and gross[wort] >= 2)):
            uebersprungen.add(wort)
            continue
        if rechtschreibung:
            stufe, art = "rot", "Rechtschreibung"
        elif "KOMMA" in kategorie or "KOMMA" in regel or kategorie == "PUNCTUATION":
            stufe, art = "gelb", "Zeichensetzung"
        elif kategorie in ("TYPOGRAPHY", "CASING"):
            stufe, art = "gelb", "Schreibung"
        else:
            stufe, art = "gelb", "Grammatik"
        vorschlag = f" Vorschlag: {', '.join(m.replacements[:3])}" if m.replacements else ""
        out.append(Finding(start, start + laenge, stufe, "sprache_lt", art, f"{m.message}{vorschlag}"))
    if uebersprungen:
        liste = ", ".join(sorted(uebersprungen)[:8]) + (" …" if len(uebersprungen) > 8 else "")
        notes.append(f"Als Namen oder eigene Wörter nicht gemeldet: {liste}.")
    return out


def kommafolgen(doc):
    """Mehrere Wörter hintereinander mit Komma dazwischen, die keine Aufzählung sein können.

    LanguageTool kennt nur bestimmte Komma-Regeln (dass, ob, Doppelzeichen …), aber keine sinnlosen
    Kommas. Eine Aufzählung („Äpfel, Birnen, Nüsse“) besteht aus Nomen, Adjektiven, Adverbien oder Zahlen.
    """
    out, lauf = [], []

    def abschluss():
        if len(lauf) >= 3 and any(t.pos_ not in ("NOUN", "PROPN", "ADJ", "ADV", "NUM") for t in lauf):
            a, b = lauf[0], lauf[-1]
            out.append(Finding(a.idx, b.idx + len(b.text), "gelb", "sprache_lt", "Zeichensetzung",
                               "Komma nach fast jedem Wort. Hier gehören vermutlich keine Kommas hin."))

    for t in doc:
        if t.is_punct or t.is_space:
            continue
        nach = doc[t.i + 1] if t.i + 1 < len(doc) else None
        if nach is not None and nach.text == ",":
            lauf.append(t)
        else:
            if lauf:
                lauf.append(t)  # das letzte Wort nach dem Komma gehört noch dazu
            abschluss()
            lauf = []
    abschluss()
    return out


# ---- Einheitliche Schreibweisen ---------------------------------------------------------

def _nah(a, b):
    """True, wenn sich a und b um genau ein Zeichen unterscheiden (Einfügen, Löschen, Ersetzen)."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    if len(a) == len(b):
        return a[i + 1:] == b[i + 1:]
    return a[i:] == b[i + 1:]


def namen(doc):
    """Namen, die fast gleich geschrieben sind („Luca“ und „Lucca“): die seltenere Schreibung wird markiert."""
    orte = {}
    for t in doc:
        if t.pos_ == "PROPN" and t.is_alpha and len(t.text) >= 4:
            orte.setdefault(t.text, []).append(t)
    out = []
    for a, b in combinations(list(orte), 2):
        if a + "s" == b or b + "s" == a or not _nah(a, b):
            continue
        na, nb = len(orte[a]), len(orte[b])
        for w, n, haupt, nh in ((a, na, b, nb), (b, nb, a, na)):
            if n <= nh:
                for t in orte[w]:
                    out.append(Finding(t.idx, t.idx + len(t.text), "gelb", "konsistenz", "Name?",
                                       f"„{w}“ ({n}×) sieht aus wie „{haupt}“ ({nh}×). "
                                       "Tippfehler oder bewusst anders?"))
    return out


def _varianten():
    paare = []
    for z in (LISTEN / "schreibvarianten.txt").read_text(encoding="utf-8").splitlines():
        z = z.strip()
        if z and not z.startswith("#") and "|" in z:
            a, b = (x.strip().lower() for x in z.split("|", 1))
            paare.append((a, b))
    return paare


def varianten(text):
    """Beide Schreibweisen eines Paares (z. B. „Foto“ und „Photo“) im Text: die seltenere wird markiert."""
    def muster(w):  # „platzier*“: Wortanfang, bis zu vier weitere Buchstaben (Beugung)
        if w.endswith("*"):
            return rf"\b{re.escape(w[:-1])}\w{{0,4}}\b"
        return rf"\b{re.escape(w)}\b"

    out = []
    for a, b in _varianten():
        ma = list(re.finditer(muster(a), text, re.IGNORECASE))
        mb = list(re.finditer(muster(b), text, re.IGNORECASE))
        if ma and mb:
            selten, haupt = (ma, b.rstrip("*")) if len(ma) <= len(mb) else (mb, a.rstrip("*"))
            for m in selten:
                out.append(Finding(m.start(), m.end(), "gelb", "konsistenz", "Schreibweise",
                                   f"„{m.group()}“ und „{haupt}“ kommen beide vor. Einheitlich schreiben?"))
    return out


def zeichen(text, spans):
    """Gemischte Anführungszeichen und Gedankenstriche, offene Zitate, doppelte Leerzeichen."""
    out = []

    def stelle(m, art, msg):
        out.append(Finding(m.start(), m.end(), "gelb", "konsistenz", art, msg))

    stile = {"„": "deutsche Anführungszeichen („…“)", "»": "Guillemets (»…«)", "«": "Guillemets («…»)",
             '"': 'gerade Anführungszeichen ("…")'}
    treffer = {z: list(re.finditer(re.escape(z), text)) for z in stile}
    vorhanden = [z for z in stile if treffer[z]]
    if len(vorhanden) > 1:
        haupt = max(vorhanden, key=lambda z: len(treffer[z]))
        for z in vorhanden:
            if z != haupt:
                for m in treffer[z]:
                    stelle(m, "Anführungszeichen",
                           f"{stile[z].capitalize()}, sonst meist {stile[haupt]}. Vereinheitlichen?")
    for z in ("„", "»", '"'):  # offener Zitatbeginn ohne passendes Ende
        for m in treffer[z]:
            if not any(a <= m.start() < b for a, b in spans):
                stelle(m, "Anführungszeichen", "Anführungszeichen wird nicht geschlossen.")

    striche = {"–": list(re.finditer(r" – ", text)), "-": list(re.finditer(r" - ", text)),
               "—": list(re.finditer(r" — ", text))}
    vorhanden = [z for z in striche if striche[z]]
    if len(vorhanden) > 1:
        haupt = max(vorhanden, key=lambda z: len(striche[z]))
        for z in vorhanden:
            if z != haupt:
                for m in striche[z]:
                    stelle(m, "Gedankenstrich",
                           f"Gedankenstrich „{z}“, sonst meist „{haupt}“. Vereinheitlichen?")
    for m in re.finditer(r"(?<=\S) {2,}(?=\S)", text):
        stelle(m, "Leerzeichen", "Mehrere Leerzeichen hintereinander.")
    for m in re.finditer(r"(?<=\w) +(?=[,.;:!?])", text):
        stelle(m, "Leerzeichen", "Leerzeichen vor Satzzeichen.")
    return out


ZAHLWORTE = ("zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf")
ZIFFERN = re.compile(r"(?<![\w.,:/\-])([2-9]|1[0-2])(?![\w.,:/\-%°€]|\s*(?:Uhr|Prozent|Euro|%))")


def zahlen(text, spans):
    """Zahlen von 2 bis 12 mal als Ziffer, mal ausgeschrieben: die seltenere Schreibung wird markiert.

    Im Dialog und bei Uhrzeiten, Daten, Prozent- und Geldangaben wird nichts gemeldet.
    """
    def draussen(m):
        return not any(a <= m.start() < b for a, b in spans)

    worte = [m for m in re.finditer(r"\b(" + "|".join(ZAHLWORTE) + r")\b", text, re.IGNORECASE) if draussen(m)]
    ziffern = [m for m in ZIFFERN.finditer(text) if draussen(m)]
    if not worte or not ziffern:
        return []
    selten, art, haupt = (ziffern, "Ziffer", "ausgeschrieben") if len(ziffern) <= len(worte) \
        else (worte, "ausgeschrieben", "als Ziffer")
    return [Finding(m.start(), m.end(), "gelb", "konsistenz", "Zahl",
                    f"Zahl „{m.group()}“ steht {art}, sonst meist {haupt}. Einheitlich schreiben?")
            for m in selten]


def pruefen(doc, text, spans, einst, notes):
    """Führt die gewählten Module der Gruppe Sprachrichtigkeit aus."""
    lt = []
    if "sprache_lt" in einst:
        lt = languagetool(text, spans, einst["sprache_lt"], notes)
        eigene = [f for f in kommafolgen(doc) if not any(f.start < g.end and g.start < f.end for g in lt)]
        lt += eigene
    kons = namen(doc) + varianten(text) + zeichen(text, spans) + zahlen(text, spans) \
        if "konsistenz" in einst else []
    # Was LanguageTool schon an derselben Stelle meldet, nicht doppelt melden
    kons = [k for k in kons if not any(k.start < f.end and f.start < k.end for f in lt)]
    return lt + kons
