"""Offline-Prüfungen zur Wortwahl (spaCy). Direkte Rede ist im Doc maskiert, die Funde liegen nur im Erzähltext."""
from pathlib import Path

import eigene_listen
from checker import Finding

LISTEN = Path(__file__).parent / "listen"


def _liste(name):
    """Liest eine Wortliste aus listen/<name>: ein Wort pro Zeile, Zeilen mit # sind Kommentare."""
    zeilen = (LISTEN / name).read_text(encoding="utf-8").splitlines()
    return {z.strip().lower() for z in zeilen if z.strip() and not z.lstrip().startswith("#")}


FUELLWOERTER = _liste("fuellwoerter.txt")        # oft ohne Verlust streichbar
SPRECHVERBEN = _liste("sprechverben.txt")        # Verben der Redebegleitung
GEFUEHLS_ADJ = _liste("gefuehle_adjektive.txt")  # für „Tell“-Sätze
GEFUEHLS_NOMEN = _liste("gefuehle_nomen.txt")
SEIN_VERBEN = {"sein", "werden", "bleiben", "wirken", "scheinen", "fühlen"}
HABEN_VERBEN = {"haben", "fühlen", "spüren", "empfinden", "verspüren", "überkommen"}


def fuellwoerter(doc, eigene):
    """Füllwörter und Verstärker (nur als Adverb/Partikel, nicht als anderes Wort gleicher Schreibung)."""
    woerter = FUELLWOERTER | eigene
    out = []
    for tok in doc:
        if tok.dep_ == "pd":
            continue  # „Das Buch ist einfach“: Prädikatsadjektiv, kein Füllwort
        if tok.lower_ in woerter and (tok.pos_ in ("ADV", "PART", "INTJ") or tok.lower_ in eigene):
            out.append(Finding(tok.idx, tok.idx + len(tok.text), "gelb", "fuellwort", "streichen?",
                               f"„{tok.text}“ – Füllwort oder Verstärker. Streichen oder ein genaueres Wort wählen?"))
    return out


def redebegleitung(doc, text, spans, eigene=frozenset()):
    """Adverb oder Adjektiv bei der Redebegleitung: „…“, sagte er wütend."""
    out = []
    for tok in doc:
        if (tok.lemma_.lower() not in SPRECHVERBEN and tok.lower_ not in eigene) or tok.pos_ not in ("VERB", "AUX"):
            continue
        end = tok.idx + len(tok.text)
        davor = any(e <= tok.idx and text[e:tok.idx].strip(" ,") == "" for _, e in spans)
        danach = any(s >= end and ":" in text[end:s] and len(text[end:s]) < 60 and "." not in text[end:s]
                     for s, _ in spans)
        if not (davor or danach):
            continue
        for c in tok.children:
            if c.dep_ in ("mo", "mnr", "pd", "oc") and c.pos_ in ("ADV", "ADJ") and c.i > tok.i - 4 \
                    and c.lower_ not in ("dann", "da", "nun", "auch", "noch", "doch", "nur", "so", "dabei", "darauf"):
                out.append(Finding(c.idx, c.idx + len(c.text), "blau", "redebegleitung", "Adverb",
                                   f"„{tok.text} … {c.text}“ – die Stimmung als Adverb zu nennen, erzählt nur. "
                                   "Zeigen? Die Rede oder eine Geste kann sie tragen."))
    return out


def tell_verben(doc, eigene):
    """Sätze, die ein Gefühl nur benennen: „er war traurig“, „sie hatte Angst“."""
    out = []
    for tok in doc:
        head = tok.head
        hl = head.lemma_.lower()
        if tok.lower_ in eigene and (hl in SEIN_VERBEN or hl in HABEN_VERBEN):
            out.append(Finding(tok.idx, tok.idx + len(tok.text), "blau", "tellverb", "zeigen?",
                               f"„{head.text} … {tok.text}“ nennt das Gefühl nur. "
                               "Zeigen: durch Körper, Handlung oder Wahrnehmung?"))
        elif tok.lower_ in GEFUEHLS_ADJ and tok.pos_ in ("ADJ", "ADV", "VERB") and hl in SEIN_VERBEN:
            out.append(Finding(tok.idx, tok.idx + len(tok.text), "blau", "tellverb", "zeigen?",
                               f"„{head.text} … {tok.text}“ nennt das Gefühl nur. "
                               "Zeigen: durch Körper, Handlung oder Wahrnehmung?"))
        elif tok.lower_ in GEFUEHLS_NOMEN and tok.pos_ == "NOUN" and hl in HABEN_VERBEN:
            out.append(Finding(tok.idx, tok.idx + len(tok.text), "blau", "tellverb", "zeigen?",
                               f"„{head.text} … {tok.text}“ nennt das Gefühl nur. "
                               "Zeigen: durch Körper, Handlung oder Wahrnehmung?"))
    return out


def _eigene(einst, modul, datei):
    """Eigene Wörter des Moduls: aus dem Eingabefeld und aus der gespeicherten Liste."""
    return eigene_listen.woerter_aus(einst[modul].get("eigene", "")) | eigene_listen.lesen(datei)


def pruefen(doc, text, spans, einst):
    """Führt die gewählten Wortwahl-Module aus. einst: {Modul-ID: {Option: Wert}}."""
    out = []
    if "fuellwort" in einst:
        out += fuellwoerter(doc, _eigene(einst, "fuellwort", "fuellwoerter_eigene"))
    if "redebegleitung" in einst:
        out += redebegleitung(doc, text, spans, _eigene(einst, "redebegleitung", "sprechverben_eigene"))
    if "tellverb" in einst:
        out += tell_verben(doc, _eigene(einst, "tellverb", "gefuehle_eigene"))
    return out
