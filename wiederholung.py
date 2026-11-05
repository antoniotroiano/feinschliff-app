"""Offline-Prüfungen zu Wiederholungen (spaCy). Direkte Rede ist im Doc maskiert."""
import eigene_listen
from checker import Finding
from wortwahl import _liste

AUSNAHMEN = _liste("wiederholung_ausnahmen.txt")
INHALT = ("NOUN", "VERB", "ADJ", "ADV")  # Wortarten, die als Inhaltswörter zählen


def _woerter(doc):
    """Alle Wörter ohne Satzzeichen und Leerraum, in Textreihenfolge."""
    return [t for t in doc if not t.is_punct and not t.is_space]


def wortwiederholungen(doc, abstand, eigene):
    """Gleiches Inhaltswort (Grundform) mehrfach im Abstand von höchstens `abstand` Wörtern."""
    ausnahmen = AUSNAHMEN | eigene
    woerter = _woerter(doc)
    letzte = {}   # Grundform -> Position des letzten Vorkommens
    treffer = {}  # Position -> (Token, Anzahl im Abstand)
    for pos, tok in enumerate(woerter):
        if tok.pos_ not in INHALT:
            continue
        lemma = tok.lemma_.lower()
        if len(lemma) < 3 or lemma in ausnahmen or tok.lower_ in ausnahmen:
            continue
        # Der Lemmatizer ist nicht immer konsequent („schüttelte“ -> „schütteln“ und „schüttelen“),
        # deshalb zählt auch die gleiche Schreibweise als Wiederholung.
        schluessel = {lemma, tok.lower_}
        for k in schluessel:
            if k in letzte and pos - letzte[k][0] <= abstand:
                vor = letzte[k][1]
                treffer[vor[0]] = vor[1]
                treffer[pos] = tok
        for k in schluessel:
            letzte[k] = (pos, (pos, tok))
    out = []
    for pos in sorted(treffer):
        tok = treffer[pos]
        out.append(Finding(tok.idx, tok.idx + len(tok.text), "gelb", "wortwiederholung", "wiederholt",
                           f"„{tok.text}“ kommt in kurzem Abstand (höchstens {abstand} Wörter) mehrfach vor. "
                           "Variieren oder streichen?"))
    return out


def wortfolgen(doc, laenge, abstand):
    """Gleiche Wortfolge (mindestens `laenge` Wörter) mehrfach im Abstand von höchstens `abstand` Wörtern."""
    woerter = _woerter(doc)
    n = len(woerter)
    schluessel = [tuple(w.lower_ for w in woerter[i:i + laenge]) for i in range(n - laenge + 1)]

    def inhalt(i):  # mindestens zwei Inhaltswörter, sonst sind es nur Füllfloskeln („in dem Haus“)
        return sum(1 for w in woerter[i:i + laenge] if w.pos_ in INHALT and w.lemma_.lower() not in AUSNAHMEN) >= 2

    belegt = set()  # Wortpositionen, die in einer wiederholten Folge liegen
    letzte = {}
    for i, k in enumerate(schluessel):
        if k in letzte and i - letzte[k] <= abstand and inhalt(i):
            for j in (letzte[k], i):
                belegt.update(range(j, j + laenge))
        letzte[k] = i

    out, i = [], 0
    pos = sorted(belegt)
    while i < len(pos):  # zusammenhängende Positionen zu einem Fund verbinden
        j = i
        while j + 1 < len(pos) and pos[j + 1] == pos[j] + 1:
            j += 1
        a, b = woerter[pos[i]], woerter[pos[j]]
        start, ende = a.idx, b.idx + len(b.text)
        text = doc.text[start:ende]
        out.append(Finding(start, ende, "gelb", "wortfolge", "wiederholt",
                           f"„{text}“ steht mehrfach in kurzem Abstand (höchstens {abstand} Wörter). "
                           "Variieren?"))
        i = j + 1
    return out


def pruefen(doc, einst):
    """Führt die gewählten Wiederholungs-Module aus. einst: {Modul-ID: {Option: Wert}}."""
    folgen = []
    if "wortfolge" in einst:
        e = einst["wortfolge"]
        folgen = wortfolgen(doc, e["laenge"], e["abstand"])
    woerter = []
    if "wortwiederholung" in einst:
        e = einst["wortwiederholung"]
        eigene = eigene_listen.woerter_aus(e.get("ausnahmen", "")) | eigene_listen.lesen("wiederholung_ausnahmen_eigene")
        woerter = wortwiederholungen(doc, e["abstand"], eigene)
        # Wörter, die schon in einer wiederholten Wortfolge stecken, nicht doppelt melden
        woerter = [w for w in woerter if not any(f.start <= w.start and w.end <= f.end for f in folgen)]
    return folgen + woerter
