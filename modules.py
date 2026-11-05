"""Prüfmodule: Register aller Prüfungen, gruppiert. Die Oberfläche wird daraus erzeugt.

Ein neues Modul braucht hier einen Eintrag und eine Prüffunktion (checker.py / ai_check.py).
Optionstypen: "mehrfach" (mehrere Werte wählbar), "auswahl" (ein Wert), "zahl", "text".
Art eines Moduls ("art"): "offline" (nur „Prüfen“), "ki" (nur „KI-Prüfung“), "beide".
"""
from checker import PERSPEKTIVEN, STANDARD_ZEITEN, ZEITEN

GRUPPEN = [
    {
        "id": "erzaehlung",
        "farbe": 300,
        "name": "Erzählung",
        "module": [
            {
                "id": "zeit",
                "art": "beide",
                "name": "Erzählzeit",
                "hilfe": "Erlaubte Zeiten im Erzähltext. Alles andere wird rot markiert.",
                "standard": False,
                "optionen": [{
                    "id": "zeiten", "typ": "mehrfach",
                    "werte": [[z, beispiel] for z, beispiel in ZEITEN.items()],
                    "standard": list(STANDARD_ZEITEN),
                }],
            },
            {
                "id": "perspektive",
                "art": "beide",
                "name": "Erzählperspektive",
                "hilfe": "Prüft Personalformen und Gedanken fremder Figuren.",
                "standard": False,
                "optionen": [{
                    "id": "perspektive", "typ": "auswahl",
                    "werte": [[p, ""] for p in PERSPEKTIVEN[1:]],
                    "standard": next(p for p in PERSPEKTIVEN if "personal" in p),
                }],
            },
        ],
    },
    {
        "id": "satzbau",
        "farbe": 190,
        "name": "Satzbau",
        "module": [
            {
                "id": "satzlaenge",
                "name": "Satzlänge",
                "hilfe": "Markiert sehr lange Sätze.",
                "standard": False,
                "optionen": [{"id": "max", "typ": "zahl", "label": "Warnen ab mehr als", "einheit": "Wörtern",
                              "min": 5, "max": 80, "standard": 25}],
            },
            {
                "id": "kurze_saetze",
                "name": "Kurze Sätze in Folge",
                "hilfe": "Viele sehr kurze Sätze hintereinander wirken abgehackt.",
                "standard": False,
                "optionen": [
                    {"id": "ab", "typ": "zahl", "label": "Warnen ab", "einheit": "Sätzen in Folge",
                     "min": 3, "max": 12, "standard": 4},
                    {"id": "max", "typ": "zahl", "label": "Ein Satz gilt als kurz bis", "einheit": "Wörter",
                     "min": 1, "max": 10, "standard": 5},
                ],
            },
            {
                "id": "satzanfang",
                "name": "Satzanfänge",
                "hilfe": "Mehrere Sätze hintereinander beginnen gleich.",
                "standard": False,
                "optionen": [{"id": "ab", "typ": "zahl", "label": "Warnen ab", "einheit": "Sätzen in Folge",
                              "min": 2, "max": 10, "standard": 3}],
            },
            {
                "id": "schachtel",
                "name": "Schachtelsätze",
                "art": "beide",
                "hilfe": "Nebensätze, die tief ineinander stecken (Stufe 1 = ein Nebensatz, 2 = Nebensatz im Nebensatz). Mit der KI-Prüfung beurteilt die KI die gefundenen Sätze und schlägt eine Aufteilung vor.",
                "standard": False,
                "optionen": [{"id": "ab", "typ": "zahl", "label": "Warnen ab Stufe", "einheit": "",
                              "min": 2, "max": 6, "standard": 3}],
            },
            {
                "id": "passiv",
                "name": "Passiv",
                "hilfe": "Vorgangspassiv („wurde gesehen“) als Vorschlag, aktiv zu formulieren.",
                "standard": False,
                "optionen": [],
            },
            {
                "id": "konstruktion",
                "art": "ki",
                "name": "Unübersichtliche Konstruktionen",
                "hilfe": "Unklare Bezüge, zu viele Einschübe, Satzbrüche. Mit Vorschlag.",
                "standard": False,
                "optionen": [],
            },
        ],
    },
    {
        "id": "wortwahl",
        "farbe": 345,
        "name": "Wortwahl",
        "module": [
            {
                "id": "fuellwort",
                "name": "Füllwörter",
                "hilfe": "Wörter wie „eigentlich“, „irgendwie“, „ziemlich“, „sehr“, „halt“, „einfach“.",
                "standard": False,
                "optionen": [{"id": "eigene", "typ": "text", "label": "Eigene Wörter (mit Komma trennen)",
                              "standard": "", "liste": "fuellwoerter_eigene"}],
            },
            {
                "id": "redebegleitung",
                "name": "Redebegleitung",
                "hilfe": "Adverb bei „sagte er wütend“. Zeigen statt benennen?",
                "standard": False,
                "optionen": [{"id": "eigene", "typ": "text", "label": "Eigene Sprechverben (mit Komma trennen)",
                              "platzhalter": "z. B. raunte, knurrte", "standard": "", "liste": "sprechverben_eigene"}],
            },
            {
                "id": "tellverb",
                "name": "Gefühle benannt",
                "hilfe": "„war traurig“, „hatte Angst“, „fühlte sich einsam“ (Show, don't tell).",
                "standard": False,
                "optionen": [{"id": "eigene", "typ": "text", "label": "Eigene Gefühlswörter (mit Komma trennen)",
                              "standard": "", "liste": "gefuehle_eigene"}],
            },
        ],
    },
    {
        "id": "wiederholung",
        "farbe": 140,
        "name": "Wiederholungen",
        "module": [
            {
                "id": "wortwiederholung",
                "name": "Wortwiederholungen",
                "hilfe": "Dasselbe Wort kommt in kurzem Abstand mehrfach vor (Namen und Hilfsverben nicht).",
                "standard": False,
                "optionen": [
                    {"id": "abstand", "typ": "zahl", "label": "Abstand höchstens", "einheit": "Wörter",
                     "min": 5, "max": 200, "standard": 30},
                    {"id": "ausnahmen", "typ": "text", "label": "Ausnahmen (Grundformen, mit Komma trennen)",
                     "standard": "", "liste": "wiederholung_ausnahmen_eigene"},
                ],
            },
            {
                "id": "wortfolge",
                "name": "Wortfolgen",
                "hilfe": "Gleiche Wortfolge, zum Beispiel „schüttelte den Kopf“, mehrfach in kurzem Abstand.",
                "standard": False,
                "optionen": [
                    {"id": "laenge", "typ": "zahl", "label": "Mindestens", "einheit": "Wörter lang",
                     "min": 3, "max": 8, "standard": 3},
                    {"id": "abstand", "typ": "zahl", "label": "Abstand höchstens", "einheit": "Wörter",
                     "min": 10, "max": 500, "standard": 100},
                ],
            },
        ],
    },
    {
        "id": "stil",
        "farbe": 60,
        "name": "Stil und Fluss",
        "module": [
            {
                "id": "uebergang",
                "art": "ki",
                "name": "Übergänge",
                "hilfe": "Sprünge in Zeit, Ort oder Blickwinkel ohne Signal, mechanische Verknüpfungen.",
                "standard": False,
                "optionen": [],
            },
            {
                "id": "formulierung",
                "art": "ki",
                "name": "Komplizierte Formulierungen",
                "hilfe": "Umständliches, Hauptwort-Stil, Wortballast. Mit einfacherer Fassung.",
                "standard": False,
                "optionen": [],
            },
            {
                "id": "zeigen",
                "art": "ki",
                "name": "Show, don't tell",
                "hilfe": "Gefühle und Eigenschaften, die nur behauptet statt gezeigt werden.",
                "standard": False,
                "optionen": [],
            },
        ],
    },
    {
        "id": "sprache",
        "farbe": 270,
        "name": "Sprachrichtigkeit",
        "module": [
            {
                "id": "sprache_lt",
                "name": "Rechtschreibung und Grammatik",
                "hilfe": "Rechtschreibung, Grammatik und Zeichensetzung (LanguageTool). Namen, die mehrfach vorkommen, gelten nicht als Fehler.",
                "standard": False,
                "optionen": [
                    {"id": "dialog", "typ": "schalter", "label": "Auch in direkter Rede prüfen", "standard": True},
                    {"id": "eigene", "typ": "text", "label": "Wörter, die nie als Fehler gelten (Namen, erfundene Wörter), mit Komma trennen",
                     "platzhalter": "z. B. Luca, Thomas, Zarkon", "standard": "", "liste": "namen_eigene"},
                ],
            },
            {
                "id": "konsistenz",
                "name": "Einheitliche Schreibweisen",
                "hilfe": "Namen fast gleich geschrieben, Schreibvarianten, gemischte Anführungszeichen und Striche, Leerzeichen.",
                "standard": False,
                "optionen": [],
            },
            {
                "id": "sprache_ki",
                "art": "ki",
                "name": "Rechtschreibung und Grammatik (KI)",
                "hilfe": "Rechtschreibung, Grammatik, Zeichensetzung mit Blick auf den Zusammenhang, auch echte Wörter am falschen Platz.",
                "standard": False,
                "optionen": [
                    {"id": "dialog", "typ": "schalter", "label": "Auch in direkter Rede prüfen", "standard": True},
                    {"id": "eigene", "typ": "text", "label": "Wörter, die nie als Fehler gelten (Namen, erfundene Wörter), mit Komma trennen",
                     "platzhalter": "z. B. Luca, Thomas, Zarkon", "standard": "", "liste": "namen_eigene"},
                ],
            },
        ],
    },
]

for _g in GRUPPEN:
    for _m in _g["module"]:
        _m.setdefault("art", "offline")

# Module, die nur offline laufen („Prüfen“)
OFFLINE = tuple(m["id"] for g in GRUPPEN for m in g["module"] if m["art"] == "offline")
# Module, die nur mit der KI-Prüfung laufen
KI_NUR = tuple(m["id"] for g in GRUPPEN for m in g["module"] if m["art"] == "ki")
# Module mit eigener Offline-Prüfung, die zusätzlich eine KI-Variante haben (Zeit und Perspektive laufen getrennt)
OFFLINE_UND_KI = tuple(m["id"] for g in GRUPPEN for m in g["module"]
                       if m["art"] == "beide" and m["id"] not in ("zeit", "perspektive"))
NAMEN = {m["id"]: m["name"] for g in GRUPPEN for m in g["module"]}
# Farbton (OKLCH-Winkel) je Modul: der seiner Gruppe. Dient nur der Orientierung in Liste und Filtern.
FARBEN = {m["id"]: g["farbe"] for g in GRUPPEN for m in g["module"]}


def gewaehlt(modules, ids):
    """Welche der Module `ids` in der Anfrage angehakt sind (Reihenfolge wie im Register)."""
    modules = modules if isinstance(modules, dict) else {}
    return [i for i in ids if isinstance(modules.get(i), dict)]

def _wert(raw, opt):
    if opt["typ"] == "schalter":
        return bool(raw) if isinstance(raw, bool) else opt["standard"]
    if opt["typ"] == "text":
        return raw[:300].strip() if isinstance(raw, str) else opt["standard"]
    try:
        z = int(raw)
    except (TypeError, ValueError):
        z = opt["standard"]
    return max(opt["min"], min(opt["max"], z))


def lese_offline(modules):
    """Gewählte Offline-Module mit geprüften Werten: {Modul-ID: {Option: Wert}}."""
    modules = modules if isinstance(modules, dict) else {}
    out = {}
    for g in GRUPPEN:
        for m in g["module"]:
            if (m["id"] in OFFLINE or m["id"] in OFFLINE_UND_KI) and isinstance(modules.get(m["id"]), dict):
                werte = modules[m["id"]]
                out[m["id"]] = {o["id"]: _wert(werte.get(o["id"]), o) for o in m["optionen"]}
    return out


def lese_einstellungen(modules):
    """Wandelt die gewählten Module aus der Anfrage in (zeit_aktiv, erlaubte Zeiten, Perspektive) um."""
    modules = modules if isinstance(modules, dict) else {}
    zeit = modules.get("zeit")
    zeit_aktiv = isinstance(zeit, dict)
    gewaehlt = zeit.get("zeiten", []) if zeit_aktiv else []
    gewaehlt = gewaehlt if isinstance(gewaehlt, list) else []
    erlaubt = [z for z in ZEITEN if z in gewaehlt]
    pers = modules.get("perspektive")
    p = pers.get("perspektive") if isinstance(pers, dict) else None
    perspektive = p if isinstance(p, str) and p in PERSPEKTIVEN[1:] else PERSPEKTIVEN[0]
    return zeit_aktiv, erlaubt, perspektive
