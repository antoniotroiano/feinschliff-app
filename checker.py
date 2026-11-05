"""Feinschliff, Kern für Romantext: Erzählzeit(en) (Standard Präteritum + Plusquamperfekt) und Erzählperspektive.

Direkte Rede (in Anführungszeichen) wird nicht geprüft.
"""
import logging
import os
import re
import time

import spacy

from grundlagen import Finding, mask_dialog  # noqa: F401 (von hier aus weiter erreichbar)

# Anführungszeichen-Paare: („…“, »…«, "…", ‚…‘ bewusst nicht, wegen Apostrophen)

# Zeitwörter, die oft auf Vorzeitigkeit hindeuten
VORZEITIG_HINWEISE = {
    "gestern", "zuvor", "früher", "damals", "bereits", "schon", "vorher",
    "einst", "längst", "vorhin", "zuerst", "anfangs",
}

# Zeitformen mit Beispiel (Reihenfolge = Anzeige)
ZEITEN = {
    "Präteritum": "er ging, sie sagte",
    "Plusquamperfekt": "er hatte gesagt, sie war gegangen",
    "Perfekt": "er hat gesagt, sie ist gegangen",
    "Präsens": "er geht, sie sagt",
    "Futur I": "er wird gehen",
    "Futur II": "er wird gegangen sein",
}
STANDARD_ZEITEN = ("Präteritum", "Plusquamperfekt")
# Zu welcher Erzählzeit gehört welche vorzeitige Zeit
VORZEITIGE_ZEIT = {"Präteritum": "Plusquamperfekt", "Präsens": "Perfekt"}

# Erzählperspektiven (erste Option = nicht prüfen)
PERSPEKTIVEN = [
    "Nicht prüfen",
    "Ich-Perspektive",
    "Du-Perspektive",
    "Wir-Perspektive",
    "Er/Sie – personal (eine Figur)",
    "Er/Sie – auktorial (allwissend)",
    "Er/Sie – neutral (Kamera, ohne Innensicht)",
]

# Verben für Gedanken/Gefühle: Innensicht einer Figur
INNENSICHT_VERBEN = {
    "denken", "fühlen", "wissen", "glauben", "hoffen", "wünschen", "fürchten",
    "ahnen", "spüren", "merken", "wollen", "ärgern", "freuen", "überlegen",
    "beschließen", "vermuten", "begreifen", "verstehen", "erinnern", "sehnen",
    "sorgen", "bereuen", "zweifeln", "erkennen",
}

# Formen, die der Lemmatizer falsch zurückführt
INNENSICHT_FORMEN = {"wusste", "wussten"}

# spaCy-Modell: per Umgebungsvariable änderbar, z. B. SPACY_MODEL=de_core_news_md
SPACY_MODEL = os.environ.get("SPACY_MODEL", "de_core_news_lg")

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            t0 = time.perf_counter()
            _nlp = spacy.load(SPACY_MODEL)
            logging.getLogger("erzaehlcheck.nlp").info("spaCy-Modell %s geladen (%.1fs)",
                                                       SPACY_MODEL, time.perf_counter() - t0)
        except OSError as e:
            raise SystemExit(
                f"spaCy-Modell „{SPACY_MODEL}“ ist nicht installiert.\n"
                f"Installieren mit: python -m spacy download {SPACY_MODEL}"
            ) from e
    return _nlp


def _in_spans(pos, spans):
    return any(s <= pos < e for s, e in spans)


def classify_sentence(sent):
    """Liefert Liste (token, tense) für finite Verben eines Satzes."""
    result = []
    for tok in sent:
        if tok.pos_ not in ("VERB", "AUX"):
            continue
        morph = tok.morph.to_dict()
        # Am Nebensatzende ("..., wann sie sich treffen können") wird die Form von
        # spaCy oft als Infinitiv getaggt, obwohl sie finites Präsens ist.
        verkappt_finit = (
            morph.get("VerbForm") == "Inf"
            and any(c.dep_ == "sb" for c in tok.children)
            and any(c.pos_ == "SCONJ" or any(g.pos_ == "SCONJ" for g in c.children)
                    for c in tok.children)
        )
        if verkappt_finit:
            morph = {**morph, "VerbForm": "Fin", "Tense": "Pres"}
        if morph.get("VerbForm") != "Fin" or morph.get("Mood") == "Sub":
            continue  # nur finite Indikativ-Formen bewerten
        # Ersatzinfinitiv ("hätte formulieren sollen"): spaCy taggt "sollen" als
        # finites Präsens. Ohne eigenes Subjekt, als Ergänzung eines anderen Verbs: Infinitiv.
        if (tok.dep_ == "oc" and tok.head != tok and tok.head.pos_ in ("VERB", "AUX")
                and not any(c.dep_ == "sb" for c in tok.children)):
            continue
        tense = morph.get("Tense")  # Past / Pres
        lemma = tok.lemma_.lower()
        # Perfekt: haben/sein + Partizip als Verbteil (oc). Ein Partizip als Prädikativ (pd)
        # ist Zustandspassiv/Adjektiv ("Die Tür war geöffnet", "Luca war überrascht").
        perf_part = any(
            c.morph.to_dict().get("VerbForm") == "Part" and c.dep_ == "oc"
            for c in tok.children
        )
        inf_child = next((c for c in tok.children if c.morph.to_dict().get("VerbForm") == "Inf"), None)
        if lemma == "werden" and inf_child is not None:
            # "wird gegangen sein": Infinitiv haben/sein mit Partizip = Futur II
            futur2 = inf_child.lemma_.lower() in ("haben", "sein") and any(
                c.morph.to_dict().get("VerbForm") == "Part" for c in inf_child.children)
            result.append((tok, "Futur II" if futur2 else "Futur I"))
        elif lemma in ("haben", "sein") and perf_part:
            result.append((tok, "Plusquamperfekt" if tense == "Past" else "Perfekt"))
        elif tense == "Pres":
            result.append((tok, "Präsens"))
        elif tense == "Past":
            result.append((tok, "Präteritum"))
    return result


def check_text(text: str, perspective: str = PERSPEKTIVEN[0], allowed=None, check_tense: bool = True, offline=None):
    """Prüft den Text, gibt (Findings, Dialog-Spans, Hinweise) zurück.

    allowed: erlaubte Zeitformen im Erzähltext (Standard: Präteritum + Plusquamperfekt).
    check_tense: False schaltet die Zeitenprüfung ab (Modul „Erzählzeit“ aus).
    offline: gewählte Offline-Module (Satzbau, Wortwahl) mit Werten, siehe modules.lese_offline.
    """
    allowed = set(allowed) if allowed else set(STANDARD_ZEITEN)
    erlaubt_text = ", ".join(z for z in ZEITEN if z in allowed)
    masked, spans = mask_dialog(text)
    doc = get_nlp()(masked)
    findings = []

    for sent in doc.sents:
        if not sent.text.strip():
            continue
        for tok, tense in (classify_sentence(sent) if check_tense else []):
            start, end = tok.idx, tok.idx + len(tok.text)
            if tense not in allowed:
                findings.append(Finding(start, end, "rot", "zeit", tense,
                    f"{tense} im Erzähltext („{tok.text}“). Erlaubt: {erlaubt_text}."))
                continue
            vorzeitig = VORZEITIGE_ZEIT.get(tense)
            hints = [t.text for t in sent
                     if t.text.lower() in VORZEITIG_HINWEISE
                     and not _in_spans(t.idx, spans)]
            if tense == "Plusquamperfekt" or (
                    tense == "Perfekt" and "Präsens" in allowed and "Präteritum" not in allowed):
                findings.append(Finding(start, end, "gelb", "zeit", tense,
                    f"{tense} – Vorzeitigkeit korrekt? Prüfen, ob das Ereignis "
                    "wirklich vor der Erzählgegenwart liegt."))
            elif vorzeitig in allowed and hints:
                findings.append(Finding(start, end, "gelb", "zeit", tense,
                    f"{tense} mit Zeitwort „{', '.join(hints)}“ – "
                    f"evtl. {vorzeitig} nötig, falls vorzeitig."))
    pf, notes = check_perspective(doc, perspective)
    findings += pf
    if offline:
        import satzbau, sprachrichtigkeit, wiederholung, wortwahl  # erst hier: diese Module brauchen get_nlp aus dieser Datei
        findings += satzbau.pruefen(doc, offline)
        findings += wortwahl.pruefen(doc, text, spans, offline)
        findings += wiederholung.pruefen(doc, offline)
        findings += sprachrichtigkeit.pruefen(doc, text, spans, offline, notes)
    findings.sort(key=lambda f: (f.start, -f.end))
    return findings, spans, notes


def _person_tokens(doc, person):
    """Pronomen/Possessiva der gegebenen Person (1, 2, 3) außerhalb von Dialogen."""
    for tok in doc:
        if tok.pos_ in ("PRON", "DET") and tok.morph.to_dict().get("Person") == person:
            yield tok


def _innensicht(tok):
    return tok.lemma_.lower() in INNENSICHT_VERBEN or tok.text.lower() in INNENSICHT_FORMEN


def _subject_key(tok):
    """Schlüssel der Figur, die Subjekt des Verbs ist (None, wenn unklar)."""
    for c in tok.children:
        if c.dep_ == "sb":
            m = c.morph.to_dict()
            if c.pos_ == "PROPN":
                return ("name", c.lemma_.lower())
            if c.pos_ == "PRON" and m.get("Number") == "Plur":
                return None  # "sie wollten": Gruppe, keine einzelne Figur
            if c.pos_ == "PRON" and m.get("Person") == "3":
                return ("pron", m.get("Gender") or c.text.lower())
            return None
    return None


def check_perspective(doc, perspective):
    """Heuristische Prüfung der Erzählperspektive. Gibt (Findings, Hinweise) zurück."""
    findings, notes = [], []
    if perspective == PERSPEKTIVEN[0]:
        return findings, notes

    def flag(tok, msg, level="gelb"):
        findings.append(Finding(tok.idx, tok.idx + len(tok.text), level, "perspektive", "Perspektive", msg))

    ich = list(_person_tokens(doc, "1"))
    du = list(_person_tokens(doc, "2"))
    ich_sg = [t for t in ich if t.morph.to_dict().get("Number") == "Sing"]
    wir = [t for t in ich if t.morph.to_dict().get("Number") == "Plur"]

    if perspective.startswith("Er/Sie"):
        for t in ich:
            flag(t, f"„{t.text}“ ist 1. Person – passt nicht zur Er/Sie-Perspektive.", "rot")
        for t in du:
            flag(t, f"„{t.text}“ ist 2. Person – passt nicht zur Er/Sie-Perspektive.", "rot")
        if "personal" in perspective:
            first = first_tok = None
            for tok in doc:
                if not _innensicht(tok):
                    continue
                key = _subject_key(tok)
                if key is None:
                    continue
                if first is None:
                    first, first_tok = key, tok
                elif key != first and key[0] == first[0]:
                    subj = next(c.text for c in tok.children if c.dep_ == "sb")
                    first_subj = next(c.text for c in first_tok.children if c.dep_ == "sb")
                    flag(tok, f"Innensicht einer anderen Figur („{subj} {tok.text}“) – "
                              f"zuerst kam „{first_subj} {first_tok.text}“. "
                              "Perspektivbruch? Bei personalem Erzählen nur eine Figur.")
            if first is None:
                notes.append("Keine Gedanken-/Gefühlsverben mit klarem Subjekt gefunden – "
                             "Innensicht konnte nicht geprüft werden.")
        elif "neutral" in perspective:
            for tok in doc:
                if _innensicht(tok) and _subject_key(tok):
                    flag(tok, f"Innensicht („{tok.text}“) – bei neutralem Erzählen wird nur "
                              "Äußeres beschrieben, keine Gedanken oder Gefühle.")
    elif perspective == "Ich-Perspektive":
        if not ich_sg:
            notes.append("Keine Ich-Form im Erzähltext gefunden.")
        for t in du:
            flag(t, f"„{t.text}“ ist 2. Person im Erzähltext – bewusst?")
        for tok in doc:
            if _innensicht(tok) and _subject_key(tok):
                flag(tok, f"Innensicht einer fremden Figur („{tok.text}“) – "
                          "ein Ich-Erzähler kann fremde Gedanken nicht wissen (nur vermuten).")
    elif perspective == "Du-Perspektive":
        if not du:
            notes.append("Keine Du-Form im Erzähltext gefunden.")
        for t in ich_sg:
            flag(t, f"„{t.text}“ ist 1. Person Singular – passt nicht zur Du-Perspektive.", "rot")
    elif perspective == "Wir-Perspektive":
        if not wir:
            notes.append("Keine Wir-Form im Erzähltext gefunden.")
        for t in ich_sg:
            flag(t, f"„{t.text}“ ist 1. Person Singular – passt nicht zur Wir-Perspektive.", "rot")
    return findings, notes
