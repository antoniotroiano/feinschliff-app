"""Offline-Prüfungen zum Satzbau (spaCy). Direkte Rede ist im übergebenen Doc bereits maskiert."""
from grundlagen import Finding, mask_dialog


def _tokens(sent):
    return [t for t in sent if not t.is_space]


def _bereich(toks):
    return toks[0].idx, toks[-1].idx + len(toks[-1].text)


def satzlaenge(doc, maximum):
    """Sätze mit mehr als `maximum` Wörtern (Satzzeichen zählen nicht, Dialoge sind ausgenommen)."""
    out = []
    for sent in doc.sents:
        toks = _tokens(sent)
        n = sum(1 for t in toks if not t.is_punct)
        if n > maximum:
            s, e = _bereich(toks)
            out.append(Finding(s, e, "gelb", "satzlaenge", f"{n} Wörter",
                               f"Langer Satz mit {n} Wörtern (Grenze: {maximum}). Teilen oder kürzen?"))
    return out


def kurze_saetze(doc, ab, maximum):
    """Mindestens `ab` Sätze in Folge mit höchstens `maximum` Wörtern (abgehackter Rhythmus)."""
    out, lauf = [], []

    def abschluss():
        if len(lauf) >= ab:
            s, e = lauf[0][0], lauf[-1][1]
            out.append(Finding(s, e, "blau", "kurze_saetze", f"{len(lauf)} kurze Sätze",
                               f"{len(lauf)} Sätze in Folge mit höchstens {maximum} Wörtern. "
                               "Wirkt abgehackt, falls nicht gewollt. Verbinden oder variieren?"))

    for sent in doc.sents:
        toks = _tokens(sent)
        # Sätze, die mit einem Satzzeichen beginnen („…“, sagte er.), gehören zum Dialog und unterbrechen die Folge
        if toks and not toks[0].is_punct and sum(1 for t in toks if not t.is_punct) <= maximum:
            lauf.append(_bereich(toks))
        else:
            abschluss()
            lauf = []
    abschluss()
    return out


def satzanfaenge(doc, ab):
    """Mindestens `ab` Sätze in Folge, die mit demselben Wort beginnen."""
    out, run = [], []

    def flush():
        if len(run) >= ab:
            for i, tok in enumerate(run, 1):
                out.append(Finding(tok.idx, tok.idx + len(tok.text), "gelb", "satzanfang", f"{i}. von {len(run)}",
                                   f"{len(run)} Sätze in Folge beginnen mit „{tok.text}“ – "
                                   "Anfang variieren?"))

    for sent in doc.sents:
        toks = _tokens(sent)
        first = toks[0] if toks and toks[0].is_alpha else None  # Satz nach Dialog („…“, sagte er) bricht ab
        if first is not None and run and run[-1].lower_ == first.lower_:
            run.append(first)
        else:
            flush()
            run = [first] if first is not None else []
    flush()
    return out


def _finit(tok):
    return tok.pos_ in ("VERB", "AUX") and tok.morph.to_dict().get("VerbForm") == "Fin"


def _stufe(verb):
    """Schachtelungstiefe eines finiten Verbs: Zahl der umgebenden Teilsätze (Hauptsatz = 0)."""
    tiefe, x = 0, verb
    while x.head.i != x.i:
        h = x.head
        if x.dep_ not in ("cj", "cd") and _finit(h):  # Koordination (und/aber) schachtelt nicht
            tiefe += 1
        x = h
    return tiefe


def kandidaten(doc, ab):
    """Sätze, in denen Nebensätze mindestens bis Stufe `ab` ineinander stecken: [(start, ende, stufe)]."""
    out = []
    for sent in doc.sents:
        toks = _tokens(sent)
        if not toks:
            continue
        tiefe = max((_stufe(t) for t in toks if _finit(t)), default=0)
        if tiefe >= ab:
            s, e = _bereich(toks)
            out.append((s, e, tiefe))
    return out


def schachtelsaetze(doc, ab):
    """Offline-Fund für verschachtelte Sätze."""
    return [Finding(s, e, "gelb", "schachtel", f"Stufe {t}",
                    f"Verschachtelter Satz: Nebensätze stecken {t} Stufen tief ineinander. Aufteilen?")
            for s, e, t in kandidaten(doc, ab)]


MAX_KANDIDAT = 1500  # Zeichen; längere „Sätze“ (meist ohne Satzzeichen) gehen nicht an die KI


def schachtel_kandidaten(text, ab, limit=25):
    """Für die KI: die am tiefsten verschachtelten Sätze samt Wortlaut.

    Gibt (Liste, Gesamtzahl der Kandidaten, Zahl der zu langen, nicht gesendeten Sätze) zurück.
    """
    from checker import get_nlp  # erst hier: checker.py lädt dieses Modul selbst erst bei der Prüfung
    masked, _ = mask_dialog(text)
    alle = kandidaten(get_nlp()(masked), ab)
    passend = [k for k in alle if k[1] - k[0] <= MAX_KANDIDAT]
    auswahl = sorted(sorted(passend, key=lambda k: -k[2])[:limit])
    return ([{"start": s, "end": e, "stufe": t, "satz": text[s:e]} for s, e, t in auswahl],
            len(passend), len(alle) - len(passend))


def passiv(doc):
    """Vorgangspassiv (werden + Partizip). Zustandspassiv („war geöffnet“) zählt nicht."""
    out = []
    for tok in doc:
        if tok.lemma_.lower() != "werden":
            continue
        for c in tok.children:
            if c.dep_ == "oc" and c.morph.to_dict().get("VerbForm") == "Part" and c.lemma_.lower() != "werden":
                out.append(Finding(c.idx, c.idx + len(c.text), "blau", "passiv", "Passiv",
                                   f"Passiv („{c.text}“). Wer handelt? Aktiv kann direkter wirken."))
    return out


def pruefen(doc, einst):
    """Führt die gewählten Satzbau-Module aus. einst: {Modul-ID: {Option: Wert}}."""
    out = []
    if "satzlaenge" in einst:
        out += satzlaenge(doc, einst["satzlaenge"]["max"])
    if "kurze_saetze" in einst:
        out += kurze_saetze(doc, einst["kurze_saetze"]["ab"], einst["kurze_saetze"]["max"])
    if "satzanfang" in einst:
        out += satzanfaenge(doc, einst["satzanfang"]["ab"])
    if "schachtel" in einst:
        out += schachtelsaetze(doc, einst["schachtel"]["ab"])
    if "passiv" in einst:
        out += passiv(doc)
    return out
