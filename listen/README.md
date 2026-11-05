# Wortlisten

Mehrere Offline-Module von [Feinschliff](../README.md) arbeiten mit Wortlisten. Die Listen sind einfache
Textdateien, die du selbst anpassen kannst.

> **Herkunft:** Die Listen wurden von der KI Claude als **Startwerte** zusammengestellt und anschließend
> nach festen Kriterien überarbeitet (siehe unten). Sie stammen nicht aus einem amtlichen Verzeichnis und
> sind nicht vollständig. Behandle sie als Vorschlag für deinen eigenen Text.

## Format

- **Ein Wort pro Zeile**, in Kleinbuchstaben.
- Zeilen mit `#` am Anfang sind Kommentare und werden ignoriert, genauso leere Zeilen.
- Nach einer Änderung die App **neu starten** (Ctrl+C, dann `python app.py`).
- Die Dateien müssen UTF-8 sein, damit Umlaute funktionieren.

## Die Listen

| Datei | Modul | Inhalt | Wirkung |
|---|---|---|---|
| [fuellwoerter.txt](fuellwoerter.txt) | Füllwörter | Füllwörter und Verstärker (zum Beispiel „eigentlich“, „sehr“) | Wird nur als Adverb oder Partikel im Erzähltext markiert, nicht als anderes Wort gleicher Schreibung. |
| [sprechverben.txt](sprechverben.txt) | Redebegleitung | Verben der Rede, Grundformen („sagen“, „fragen“ …) | Hängt ein Adverb am Verb direkt vor oder nach wörtlicher Rede, wird es markiert. |
| [gefuehle_adjektive.txt](gefuehle_adjektive.txt) | Gefühle benannt | Gefühlsadjektive („traurig“, „wütend“ …) | Treffer bei „war/wurde/fühlte sich + Adjektiv“. |
| [gefuehle_nomen.txt](gefuehle_nomen.txt) | Gefühle benannt | Gefühlsnomen („Angst“, „Wut“ …) | Treffer bei „hatte/spürte/empfand + Nomen“. |
| [wiederholung_ausnahmen.txt](wiederholung_ausnahmen.txt) | Wortwiederholungen | Grundformen, die oft vorkommen dürfen („sein“, „dann“, „auch“ …) | Diese Wörter zählen nicht als Wiederholung. |
| [schreibvarianten.txt](schreibvarianten.txt) | Einheitliche Schreibweisen | Paare, mit senkrechtem Strich getrennt, zum Beispiel `foto\|photo` | Kommen beide Schreibweisen vor, wird die seltenere markiert. Groß- und Kleinschreibung egal. |

## Wie die Listen entstanden sind (Kriterien und Quellen)

Eine Websuche ergab **keine** fertige Fachliste, die man übernehmen könnte. Belegt ist nur ein Teil, der Rest
beruht auf Wissen der KI und ist als solcher gekennzeichnet.

| Liste | Kriterium | Belegt durch | Auf Wissen der KI beruhend |
|---|---|---|---|
| `fuellwoerter.txt` | Ein Füllwort trägt keine eigene Bedeutung. Wörter, die Ort oder Zeit nennen („irgendwo“, „irgendwann“), gehören nicht dazu. | „eigentlich“, „irgendwie“, „einfach“, „eher“, „allerdings“ stehen in einer [Quelle der Universität Göttingen](https://www.phon-paed-psychologie.uni-goettingen.de/Essays/2023_Eye_Was_%20machst_Der%20Sprachdienst.pdf). | Übrige Einträge. „zwar“ steht dort ebenfalls, wurde aber wegen der festen Verbindung „zwar … aber“ bewusst weggelassen. |
| `sprechverben.txt` | Verben des Sprechens (lateinisch *verba dicendi*), in der Grundform. | „flüstern“, „raunen“, „wispern“, „tuscheln“ als zusammengehörige Gruppe: [core.ac.uk](https://core.ac.uk/download/83654274.pdf), [core.ac.uk](https://core.ac.uk/download/83653445.pdf). | Übrige Verben. |
| `gefuehle_adjektive.txt`, `gefuehle_nomen.txt` | Die sechs Basisemotionen nach Paul Ekman (Freude, Trauer, Wut, Furcht, Ekel, Überraschung) und häufige Nebenemotionen, jeweils als Adjektiv und als Nomen. | Nur das Prinzip „Gefühl zeigen statt benennen“ ist durch Schreibratgeber belegt, keine Wortliste. | Alle Einträge. **Bewusst nicht dabei:** „Glück“, „Überraschung“, „Ärger“, weil „hatte Glück“, „hatte eine Überraschung“ und „hatte Ärger“ meist etwas anderes bedeuten. |
| `wiederholung_ausnahmen.txt` | Hilfs-, Modal- und Funktionsverben sowie Allerweltsadverbien, die oft vorkommen dürfen. Die Stoppwortliste von spaCy wurde **absichtlich nicht** genommen, weil sie „ging“, „kam“, „sah“, „sagte“, „Zeit“ und „Jahr“ enthält, also gerade die Wörter, deren Wiederholung auffallen soll. | Prüfung gegen die spaCy-Stoppwörter (lokal). | Alle Einträge. |
| `schreibvarianten.txt` | Paare, die laut Rechtschreibreform beide oder nur nach alter Regel möglich sind. Nur Paare, bei denen ich mir sicher war. | Keine amtliche Liste gefunden, Quellen widersprechen sich zum Teil (zum Beispiel Delfin und Delphin). | Alle Paare. **Bitte gegen den aktuellen Duden gegenlesen.** |

**Platzhalter bei Schreibvarianten:** Ein `*` am Wortende erlaubt Endungen, zum Beispiel findet
`platzier*|plazier*` auch „platziert“ und „plazierte“.

## Eigene Wörter in der App

Manche Module haben in der App ein **Eingabefeld** („Eigene Wörter“, „Eigene Sprechverben“, „Ausnahmen“,
„Wörter, die nie als Fehler gelten“). Was du dort einträgst, gilt zunächst nur für die Prüfung und bleibt im
Browser gespeichert.

Mit dem Knopf **In Liste übernehmen** unter dem Feld speicherst du die Wörter **dauerhaft** in einer
eigenen Datei im Ordner **`eigene-listen/`** (neben `app.py`, nicht in diesem Ordner). Ordner und Datei
werden beim ersten Speichern angelegt, das Feld wird danach geleert, und die Wörter gelten ab sofort bei
jeder Prüfung, ohne Neustart. Die Startlisten oben bleiben dabei unverändert.

| Eigene Datei | Gehört zu | Enthält |
|---|---|---|
| `eigene-listen/fuellwoerter.txt` | Füllwörter | Wörter, die immer als Füllwort gelten |
| `eigene-listen/sprechverben.txt` | Redebegleitung | Weitere Sprechverben (auch gebeugte Formen wie „raunte“) |
| `eigene-listen/gefuehle.txt` | Gefühle benannt | Weitere Gefühlswörter |
| `eigene-listen/wiederholung_ausnahmen.txt` | Wortwiederholungen | Wörter, die oft vorkommen dürfen |
| `eigene-listen/namen.txt` | Rechtschreibung und Grammatik (Offline und KI) | Namen und erfundene Wörter, die nie als Fehler gelten |

Die eigenen Dateien kannst du von Hand bearbeiten. Dasselbe Format: ein Wort pro Zeile, Kleinbuchstaben.
Sie können **Namen aus deinem Text** enthalten (zum Beispiel Figurennamen). Veröffentliche sie nicht,
zum Beispiel nicht in einem öffentlichen Repository.

**Sichern:** Kopiere den ganzen Ordner `eigene-listen/` weg, bevor du das Projekt löschst, und lege ihn nach
dem neuen Herunterladen wieder neben `app.py`. Ordner- und Dateinamen müssen gleich bleiben.

## Tipps

- Findet ein Modul zu viel, entferne mehrdeutige Wörter (zum Beispiel „ganz“ oder „mal“ bei den Füllwörtern).
- Fehlt dir etwas, ergänze es einfach am Dateiende.
- Behalte eine Kopie der ursprünglichen Datei, wenn du viel änderst.
