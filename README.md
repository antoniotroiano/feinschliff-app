# Feinschliff

**Bringt deinen Text in Form.**

Eine kleine Anwendung für Autorinnen und Autoren, die einen Romantext prüfen wollen: Erzählzeit,
Erzählperspektive, Satzbau, Wortwahl, Wiederholungen, Stil und Rechtschreibung. Du fügst einen Absatz
oder ein Kapitel ein, wählst die Prüfungen aus, und die Funde werden **direkt im Text markiert**. Du
korrigierst in derselben Box und prüfst erneut.

Die App läuft auf deinem Rechner und öffnet sich im Browser. Die meisten Prüfungen laufen **offline**.
Einige brauchen zusätzlich die **KI-Prüfung** (Claude von Anthropic), die du freiwillig mit einem eigenen
API-Key einschaltest.

> Die App ist ein Hilfsmittel und kein Lektorat. Sie arbeitet mit Regeln und Wortlisten, die irren
> können, und die KI kann sich ebenfalls täuschen. Entscheiden musst du.

## Inhalt

- [Was geprüft wird](#was-geprüft-wird)
- [Farben und Zeichen im Text](#farben-und-zeichen-im-text)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Start](#start)
- [Funde als „In Ordnung“ bestätigen](#funde-als-in-ordnung-bestätigen)
- [KI-Vorschlag übernehmen](#ki-vorschlag-übernehmen)
- [Satz umformulieren (KI)](#satz-umformulieren-ki)
- [KI-Prüfung einrichten](#ki-prüfung-einrichten)
- [Einstellungen und Umgebungsvariablen](#einstellungen-und-umgebungsvariablen)
- [Anderes spaCy-Modell verwenden](#anderes-spacy-modell-verwenden)
- [Wortlisten anpassen](#wortlisten-anpassen)
- [Meldungen im Terminal (Logging)](#meldungen-im-terminal-logging)
- [Bedienung](#bedienung)
- [Datenschutz](#datenschutz)
- [Grenzen](#grenzen)
- [Fehlerbehebung](#fehlerbehebung)
- [Projektaufbau](#projektaufbau)
- [Lizenz und verwendete Komponenten](#lizenz-und-verwendete-komponenten)

## Was geprüft wird

Jede Prüfung ist ein **Modul** mit Schalter. Am Anfang ist **nichts** ausgewählt, und alle Gruppen sind
zugeklappt. Ein Etikett hinter dem Namen zeigt, wo das Modul läuft:

- **Offline**: läuft nur mit dem Knopf „Prüfen“, auf deinem Rechner und ohne Kosten.
- **KI**: läuft nur mit dem Knopf „KI-Prüfung“. Der Text wird dabei an die Anthropic-API gesendet.
- **Offline + KI**: läuft mit beiden Knöpfen.

Wählst du Module gemischt aus, läuft bei jedem Knopf, was passt. Der Rest steht als Hinweis in der
rechten Spalte („Nicht geprüft …“).

| Gruppe | Modul | Etikett | Was es findet |
|---|---|---|---|
| **Erzählung** | Erzählzeit | Offline + KI | Zeitformen, die du nicht erlaubt hast (Rot). Dazu Hinweise zur Vorzeitigkeit (Gelb): Steht ein Rückblick im Plusquamperfekt? Wähle die erlaubten Zeiten selbst aus (Präteritum, Plusquamperfekt, Perfekt, Präsens, Futur I, Futur II). Direkte Rede bleibt unberührt. |
| | Erzählperspektive | Offline + KI | Ich-, Du-, Wir-Perspektive, Er/Sie personal, auktorial oder neutral. Offline: falsche Personalformen und Gedanken fremder Figuren. Die KI versteht auch, wer mit „er“ gemeint ist. |
| **Satzbau** | Satzlänge | Offline | Sätze mit mehr als X Wörtern (Standard 25). |
| | Kurze Sätze in Folge | Offline | Mindestens X Sätze hintereinander mit höchstens Y Wörtern, wirkt abgehackt (Standard 4 Sätze mit höchstens 5 Wörtern, Blau). |
| | Satzanfänge | Offline | X Sätze hintereinander beginnen gleich (Standard 3). |
| | Schachtelsätze | Offline + KI | Nebensätze, die tief ineinander stecken (Standard ab Stufe 3). Offline markiert der Parser diese Sätze. Mit der **KI-Prüfung** beurteilt die KI nur diese gefundenen Sätze (höchstens 25, die am tiefsten verschachtelten zuerst), meldet nur die wirklich unübersichtlichen und schlägt eine geteilte Fassung vor. |
| | Passiv | Offline | Vorgangspassiv („wurde gesehen“) als Vorschlag. |
| | Unübersichtliche Konstruktionen | KI | Unklare Bezüge, zu viele Einschübe, Satzbrüche, mit geglätteter Fassung. |
| **Wortwahl** | Füllwörter | Offline | „eigentlich“, „irgendwie“, „ziemlich“, „sehr“ … Wortliste, eigene Wörter möglich. |
| | Redebegleitung | Offline | Adverb bei „sagte er wütend“. |
| | Gefühle benannt | Offline | „war traurig“, „hatte Angst“ (Show, don't tell). Wortliste, eigene Wörter möglich. |
| **Wiederholungen** | Wortwiederholungen | Offline | Dasselbe Wort in kurzem Abstand (Standard 30 Wörter). |
| | Wortfolgen | Offline | Dieselbe Wortfolge („schüttelte den Kopf“) in kurzem Abstand. |
| **Stil und Fluss** | Übergänge | KI | Sprünge in Zeit, Ort oder Blickwinkel ohne Signal, mechanische Verknüpfungen. |
| | Komplizierte Formulierungen | KI | Umständliches, mit einfacherer Fassung. |
| | Show, don't tell | KI | Gefühle, die nur behauptet werden, mit einem Beispiel. |
| **Sprachrichtigkeit** | Rechtschreibung und Grammatik | Offline | Rechtschreibung, Grammatik und Zeichensetzung mit LanguageTool. Dazu eine eigene Regel gegen Kommas nach fast jedem Wort. |
| | Einheitliche Schreibweisen | Offline | Fast gleiche Namen („Luca“, „Lucca“), Schreibvarianten („Foto“, „Photo“), gemischte Anführungszeichen und Striche, offene Anführungszeichen, doppelte Leerzeichen, Zahlen von 2 bis 12 mal als Ziffer und mal ausgeschrieben. |
| | Rechtschreibung und Grammatik (KI) | KI | Dasselbe mit Blick auf den Zusammenhang, auch echte Wörter am falschen Platz („Wahl“ statt „Wal“). |

Bei den Modulen **Rechtschreibung und Grammatik** (offline und KI) gibt es einen Schalter, ob auch die
**direkte Rede** geprüft werden soll (am Anfang an), und ein Feld für **Wörter, die nie als Fehler
gelten**, zum Beispiel Namen deiner Figuren oder erfundene Wörter. Großwörter, die LanguageTool nicht
kennt und die **mindestens dreimal** im Text stehen, gelten automatisch als Namen. Zwei Treffer reichen nicht,
damit ein zweimal falsch geschriebenes Hauptwort nicht unbemerkt bleibt. Welche Wörter so übersprungen
wurden, steht als Hinweis rechts.

## Farben und Zeichen im Text

Die **Farbe** sagt, wie dringlich ein Fund ist. **Welches Modul** den Fund erzeugt hat, steht in der Liste
rechts neben dem Fund. Die Filter oben in der Liste gelten pro Modul.

| Farbe | Bedeutung | Beispiele |
|---|---|---|
| **Rot** | Verstoß gegen deine Einstellung oder sicherer Fehler. Ändern. | nicht erlaubte Zeit, falsche Personalform, Rechtschreibfehler |
| **Gelb** | Bitte prüfen. Verdacht, vielleicht in Ordnung. | Vorzeitigkeit, langer Satz, Füllwort, Wiederholung, fehlendes Komma |
| **Blau** | Vorschlag, kein Fehler. | Passiv, nur benanntes Gefühl, Stilvorschläge der KI |
| **Grau** | Direkte Rede. Wird bei den meisten Prüfungen nicht geprüft. | |

**Farbiges Quadrat vor dem Modulnamen:** Jede Gruppe hat eine eigene Farbe (Erzählung Violett, Satzbau
Türkis, Wortwahl Rosa, Wiederholungen Grün, Stil und Fluss Orange, Sprachrichtigkeit Blauviolett). Das Quadrat
steht links vor den Gruppen, in der Fundliste rechts neben dem Modulnamen und in den Filtern über der Liste.
So erkennst du auf einen Blick, aus welcher Gruppe ein Fund kommt. Es steht **nicht** im Text, damit der Text
ruhig bleibt. Die Quadratfarbe hat nichts mit Rot, Gelb und Blau zu tun, die zeigen die Dringlichkeit.

Weitere Zeichen:

- **Blasse Fläche** = ganzer Satz (zum Beispiel zu lang). Ein **kräftiger** Wortfund darin liegt darüber.
- **Gestrichelte Linie** = Fund der KI-Prüfung, in der Liste mit „KI“ gekennzeichnet.
- Stellen, die du **bearbeitest**, verlieren ihre Markierung, und der Fund in der Liste wird abgehakt.

Bei den KI-Modulen für Stil und Konstruktionen vergibt die KI pro Fund selbst, ob er Gelb oder Blau ist.
Dieselbe Erklärung steht in der App unter **Legende**.

## Voraussetzungen

- **Betriebssystem:** Feinschliff wurde nur auf **macOS** getestet. Auf Linux sollte es genauso gehen. Auf Windows ist es
  ungetestet: Die Befehle unten sind für ein Unix-Terminal geschrieben (unter Windows heißt die Aktivierung
  `.venv\Scripts\activate`, und Umgebungsvariablen setzt du anders).
- **Git**, um das Repository zu laden (alternativ lädst du es auf GitHub als ZIP herunter)
- **Python 3** und `pip`. Getestet wurde mit **3.13**, andere Versionen sind nicht geprüft.
- **Java** für das Modul „Rechtschreibung und Grammatik“ (LanguageTool), getestet mit **Java 21**. Prüfen:
  `java -version`. Installieren zum Beispiel auf dem Mac mit `brew install openjdk` oder von <https://adoptium.net>.
  Ohne Java läuft die App trotzdem, nur dieses Modul meldet einen Hinweis.
- Ein Browser
- Für die KI-Prüfung: ein **Anthropic-API-Key** (optional, siehe [KI-Prüfung einrichten](#ki-prüfung-einrichten))
- Speicherplatz: das spaCy-Modell `de_core_news_lg` belegt etwa **610 MB**, LanguageTool etwa **400 MB**
  im Benutzer-Cache (`~/.cache/language_tool_python`), dazu die Python-Pakete. Beides wurde auf einem
  Mac gemessen.
- Internet nur für die Installation, den ersten LanguageTool-Download und die KI-Prüfung.

## Installation

```bash
git clone https://github.com/antoniotroiano/feinschliff-app.git
cd feinschliff-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download de_core_news_lg
```

Nach `source .venv/bin/activate` genügt `python` (statt `python3`). Die Installation lädt mehrere hundert Megabyte
und dauert einige Minuten.

Das deutsche spaCy-Modell wird einmalig geladen. Wie du ein anderes verwendest, steht
[weiter unten](#anderes-spacy-modell-verwenden).

**LanguageTool** (Rechtschreibung offline) lädt sich beim **ersten Prüfen** mit dem Modul „Rechtschreibung
und Grammatik“ automatisch herunter (etwa 400 MB). Das dauert je nach Verbindung eine Weile. Der Start danach dauert
einige Sekunden, weitere Prüfungen sind schnell. Auch der **Start der App** braucht einige Sekunden, weil das
spaCy-Modell vor dem Öffnen des Browsers geladen wird.

## Start

```bash
cd feinschliff-app
source .venv/bin/activate
python app.py
```

Der Browser öffnet sich unter <http://127.0.0.1:8765>. Zum Beenden im Terminal **Ctrl+C**.

1. Text in die mittlere Box einfügen (wird immer als reiner Text eingefügt).
2. Links die gewünschten Prüfungen auswählen.
3. **Prüfen** (auf dem Mac ⌘↵, sonst Strg+Enter) für Offline-Module, **KI-Prüfung** für die KI-Module.
4. Funde in der Liste rechts anklicken, im Text korrigieren, erneut prüfen.

## Funde als „In Ordnung“ bestätigen

Gelbe Funde heißen „bitte prüfen“, nicht „Fehler“. Manche Hinweise erscheinen immer wieder, auch wenn die Stelle
richtig ist, zum Beispiel der Hinweis zur Vorzeitigkeit bei **jedem Plusquamperfekt**. Unter jedem Fund steht deshalb
der Knopf **In Ordnung** (sichtbar, sobald du den Fund anklickst oder mit der Maus darüberfährst).

- Die App **merkt sich** die Bestätigung für diese Stelle **in diesem Satz** und blendet den Fund bei jeder weiteren
  Prüfung aus, in der Liste und im Text.
- Ändert sich der Satz, kommt der Hinweis wieder, denn die Bestätigung gilt nur für genau diesen Satz.
- Über der Liste steht „n als ‚In Ordnung‘ ausgeblendet · anzeigen“. Dort holst du die bestätigten Funde zurück
  und kannst sie mit **Rückgängig** wieder zu offenen Funden machen.
- Die Zähler und das Weiterschalten mit ⌥J und ⌥K (Alt+J und Alt+K) überspringen bestätigte Funde.
- Gespeichert wird **im Browser** und nur als **Fingerabdruck** (eine kurze Zeichenfolge aus Modul, Wort und Satz),
  nicht als Text. Wie die übrigen Einstellungen gilt das pro Browser und geht verloren, wenn du den Browser-Speicher leerst.

## KI-Vorschlag übernehmen

Macht die KI bei einem Fund einen konkreten Vorschlag, steht er in einem eigenen Kasten unter dem Fund. Die Knöpfe
**Vorschlag übernehmen** und **Kopieren** erscheinen, sobald du den Fund anklickst oder mit der Maus darüberfährst.
„Übernehmen“ ersetzt genau die markierte Stelle im Text. Ist sie inzwischen geändert, meldet die App das.
Die **Hinweise zur Prüfung** (Gesamteindruck, nicht geprüfte Module) stehen gesammelt in einem eingeklappten Kasten
über den Funden.

## Satz umformulieren (KI)

Unter jedem Fund (sichtbar, sobald du ihn anklickst oder mit der Maus darüberfährst) steht **Umformulieren (KI)**.
Die App schickt dann genau **den Satz, in dem der Fund liegt**, mit dem Grund des Fundes und bis zu 600 Zeichen
Text davor und danach als Kontext an die KI. Du bekommst zwei bis drei Fassungen mit einer Kurzbeschreibung
(zum Beispiel „in zwei Sätze geteilt“, „knapper“).

- **Übernehmen** ersetzt den Satz im Text. Die Markierungen der anderen Funde bleiben stehen. Steht der Satz nicht
  mehr genau so im Text (du hast ihn inzwischen geändert), meldet die App das und du kannst die Fassung kopieren.
- **Kopieren** legt die Fassung in die Zwischenablage.
- Die KI soll Inhalt, Ton, Namen und **wörtliche Rede** unverändert lassen und die gewählten **Zeitformen** und die
  **Perspektive** beibehalten, soweit du sie im Modul gewählt hast.
- Es wird das **KI-Modell** verwendet, das links gewählt ist. Die Kosten (einige hundert Tokens) stehen oben in der Mitte.
- Dafür ist ein API-Key nötig, siehe unten. Es geht nur dieser eine Satz mit Kontext an die API, nicht der ganze Text.
- Die Satzerkennung ist einfach gehalten und kennt gängige Abkürzungen wie „z. B.“ oder „usw.“. Bei ungewöhnlichen
  Satzzeichen kann der erkannte Satz zu kurz oder zu lang sein. Prüfe den Vorschlag vor dem Übernehmen.

## KI-Prüfung einrichten

Die KI-Prüfung ist **optional**. Du brauchst dafür einen API-Key von Anthropic (in der
[Anthropic Console](https://console.anthropic.com) anlegen) und ein Guthaben dort.

Der Key wird **nur über eine Umgebungsvariable** gelesen und nie in einer Datei gespeichert:

```bash
export ANTHROPIC_API_KEY="dein-key"
python app.py
```

Tipp: Ein Key, den du direkt in den Befehl tippst, steht danach in der Verlaufsliste deiner Shell. Ohne Spuren geht
es mit einer Abfrage (in `zsh`, dem Standard auf dem Mac; in `bash` heißt sie `read -s -p "API-Key: " ANTHROPIC_API_KEY`):

```bash
read -s "ANTHROPIC_API_KEY?API-Key: " && export ANTHROPIC_API_KEY
python app.py
```

Eine `.env`-Datei liest die App **nicht**.

Die Variable gilt nur für dieses Terminalfenster. Setze oder ändere sie **vor** dem Start der App. Teile
den Key nicht und lege ihn nicht im Projektordner ab.

- **Modell** wählbar im Fenster links: Haiku 5.5 (günstig), Sonnet 5.5 (ausgewogen), Opus 5.5 (am
  gründlichsten). Für den Anfang reicht meist Haiku. Wenn dir die Hinweise zu oberflächlich oder
  unsicher sind, probiere Sonnet.
- **Kosten**: Oben in der Mitte zeigt die App nach jeder KI-Prüfung Tokens und einen **geschätzten**
  Preis. Die dafür hinterlegten Preise sind grob. Verbindlich ist die Preisliste von Anthropic.
  Mehr gewählte KI-Module bedeuten eine längere Antwort und höhere Kosten.
- **Länge**: Die KI-Prüfung nimmt höchstens 60 000 Zeichen auf einmal. Prüfe längere Texte abschnittsweise.
  Antwortet die KI nicht innerhalb von **5 Minuten**, bricht die App ab und meldet es.
- **Datenschutz**: siehe [unten](#datenschutz).

## Einstellungen und Umgebungsvariablen

| Variable | Wirkung | Standard |
|---|---|---|
| `ANTHROPIC_API_KEY` | API-Key für die KI-Prüfung | nicht gesetzt |
| `ANTHROPIC_AUTH_TOKEN` | Alternative zum Key (Token-Anmeldung des SDK) | nicht gesetzt |
| `ANTHROPIC_BASE_URL` | Adresse eines **anderen Zugangs zu denselben Anthropic-Modellen**, zum Beispiel ein Gateway oder Proxy der Firma. Gesetzt gehen deine Texte **nicht** direkt an Anthropic, sondern an diese Adresse. Das ist **keine Möglichkeit, eine andere KI** (OpenAI, Gemini …) zu benutzen. Ob ein bestimmtes Gateway mit Feinschliff funktioniert, ist nicht getestet. Die App warnt beim Start. Normalerweise **nicht setzen**. | nicht gesetzt |
| `SPACY_MODEL` | Name des spaCy-Modells | `de_core_news_lg` |
| `FEINSCHLIFF_PORT` | Port des lokalen Servers (Zahl von 1 bis 65535). Ist er belegt, beendet sich die App mit einer Meldung, ohne den Browser zu öffnen. | `8765` |
| `LOG_LEVEL` | Ausführlichkeit der Terminal-Meldungen: `DEBUG`, `INFO`, `WARNING` | `INFO` |

Beispiel: `FEINSCHLIFF_PORT=8770 python app.py`.

Deine Auswahl in der App (Module, Zahlenwerte, Felder, KI-Modell, Schriftgröße) merkt sich der **Browser**.
Das gilt pro Browser und geht verloren, wenn du den Browser-Speicher leerst.

**Eigene Wörter:** Was du in ein Feld wie „Eigene Wörter“ oder „Wörter, die nie als Fehler gelten“
schreibst, gilt zunächst nur für die Prüfung. Mit dem Knopf **In Liste übernehmen** unter dem Feld speicherst
du die Wörter dauerhaft in einer eigenen Datei im Ordner **`eigene-listen/`** (zum Beispiel `namen.txt`).
Sie gelten dann bei jeder Prüfung, ohne Neustart. Die mitgelieferten Startlisten in `listen/` bleiben dabei
unverändert. Der Ordner wird beim ersten Speichern angelegt.

**Eigene Listen sichern und wiederherstellen:** Kopiere den ganzen Ordner `eigene-listen/` an einen sicheren
Ort, bevor du das Projekt löschst oder neu herunterlädst. Danach legst du ihn in den neuen Projektordner
zurück, direkt neben `app.py`. Die App benutzt die Dateien sofort. Der Ordnername `eigene-listen` und die
Dateinamen darin müssen **genau so bleiben**, sonst erkennt die App sie nicht. Der Ordner kann Namen aus
deinem Buch enthalten und gehört deshalb nicht in ein öffentliches Repository (er steht in der
`.gitignore` und wird deshalb nicht mit hochgeladen).

## Anderes spaCy-Modell verwenden

Standard ist `de_core_news_lg`, das größte der „core“-Pakete. Kleinere Modelle brauchen weniger Platz,
erkennen aber in der Regel weniger genau. Getestet wurde nur das Standardmodell. Die Auswahl findest du auf
<https://spacy.io/models/de>.

```bash
# Modell installieren (im aktivierten .venv)
python -m spacy download de_core_news_md

# App mit diesem Modell starten
SPACY_MODEL=de_core_news_md python app.py
```

Ist das Modell nicht installiert, nennt die App beim Start den passenden Installationsbefehl.
Die Offline-Prüfungen zur Erzählzeit, zum Satzbau und zur Perspektive hängen von der Qualität des Modells ab.

## Wortlisten anpassen

Mehrere Offline-Module arbeiten mit Wortlisten in Textdateien. Du kannst sie ohne Programmierkenntnisse
ändern. Die Übersicht mit Erklärung jeder Liste steht auf der Unterseite
**[listen/README.md](listen/README.md)**:

- [listen/fuellwoerter.txt](listen/fuellwoerter.txt)
- [listen/sprechverben.txt](listen/sprechverben.txt)
- [listen/gefuehle_adjektive.txt](listen/gefuehle_adjektive.txt)
- [listen/gefuehle_nomen.txt](listen/gefuehle_nomen.txt)
- [listen/wiederholung_ausnahmen.txt](listen/wiederholung_ausnahmen.txt)
- [listen/schreibvarianten.txt](listen/schreibvarianten.txt)

Die Listen wurden von der KI Claude als Startwerte zusammengestellt und stammen **nicht** aus einer
Fachquelle. Sie sind ausdrücklich zum Anpassen gedacht.

Deine **eigenen** Wörter liegen getrennt im Ordner `eigene-listen/` (siehe die Unterseite und den Abschnitt
zu den Einstellungen). Sie können Namen aus deinem Text enthalten. Veröffentliche diesen Ordner nicht.

## Meldungen im Terminal (Logging)

Die App schreibt im Terminal mit, was sie tut. Das hilft bei der Fehlersuche:

```
23:52:48 INFO    erzaehlcheck: spaCy-Modell: de_core_news_lg | Port: 8765 | KI-Key gesetzt: nein | Java gefunden: ja
23:53:10 INFO    erzaehlcheck: Prüfen (offline): Module=zeit,passiv Zeichen=1840 Wörter=290 Funde=12 Dauer=0.4s
23:53:42 INFO    erzaehlcheck: KI-Prüfung fertig: Funde=7 Tokens=620+410 ca. 0.0003 $ Dauer=6.1s
```

- Beim Start siehst du Python-Version, spaCy-Modell, Port, ob ein API-Key gesetzt ist (nur ja oder nein) und ob Java gefunden wurde.
- Pro Prüfung stehen Module, Länge, Anzahl der Funde, Dauer und bei der KI Tokens und geschätzte Kosten.
- Fehler stehen mit Ursache im Terminal. Unerwartete Fehler zeigen dort die ganze Fehlerspur.
- Mit `LOG_LEVEL=DEBUG python app.py` gibt es mehr Einzelheiten, mit `LOG_LEVEL=WARNING` nur Warnungen und Fehler.
- **Der Text wird nicht protokolliert**, ebenso wenig der API-Key. Es stehen nur Längen, Modul-Namen und Zeiten
  im Log. Die Fehlerspur eines unerwarteten Fehlers kann in seltenen Fällen Teile der Fehlermeldung einer
  Bibliothek enthalten. Teile Logauszüge trotzdem nur, nachdem du sie durchgesehen hast.

Fehler zeigt die App außerdem **in der Oberfläche**: oben in der Mitte erscheint „Fehler – Einzelheiten
rechts“ in Rot, und die Meldung mit dem Lösungshinweis steht in der rechten Spalte. Vorherige Funde bleiben
dabei erhalten.

## Bedienung

| Aktion | Wirkung |
|---|---|
| ⌘↵ / Strg+Enter | Offline prüfen |
| ⌥J / ⌥K (unter Windows und Linux Alt+J / Alt+K) | Nächster / vorheriger Fund |
| Klick auf Markierung oder Fund | Springt zur Gegenstelle |
| In Ordnung am Fund | Du bestätigst, dass die Stelle so stimmt. Der Fund wird ausgeblendet |
| Vorschlag übernehmen am Fund | Ersetzt die markierte Stelle durch den Vorschlag der KI |
| Umformulieren (KI) am Fund | Schlägt für den Satz zwei Fassungen vor, „Übernehmen“ ersetzt ihn im Text |
| A− / A+ | Schriftgröße im Text |
| Legende | Erklärung der Farben, Zeichen und Etiketten |
| Alle / Keine | Alle Prüfungen an- oder abwählen |
| Chips über der Liste | Funde eines Moduls ein- oder ausblenden |

## Datenschutz

- Der Server lauscht nur auf **127.0.0.1**, ist also von außen nicht erreichbar. Zusätzlich lehnt die App Anfragen ab,
  die nicht an `127.0.0.1` oder `localhost` gehen oder von einer fremden Webseite stammen. So kann keine andere Seite
  in deinem Browser die App ansprechen (zum Beispiel auf Kosten deines Keys).
- **Offline-Prüfungen** verlassen deinen Rechner nicht. Internet braucht nur die Installation und der
  einmalige Download von LanguageTool.
- Bei der **KI-Prüfung** wird dein Text an die **Anthropic-API** gesendet. Sende nichts, was du nicht
  senden darfst. Es werden nur der Text und die Einstellungen der gewählten Module übertragen. Beim
  Modul „Schachtelsätze“ gehen **nur die gefundenen Sätze** an die API, nicht der ganze Text (es sei denn,
  du wählst zusätzlich andere KI-Module).
- Beim Modul **Rechtschreibung (KI)** gehen außerdem die Wörter aus dem Feld „Eigene Wörter“ und aus
  `eigene-listen/namen.txt` (zum Beispiel **Figurennamen**) mit an die API, damit sie nicht als Fehler gelten.
- Bei **Umformulieren** gehen nur der eine Satz, der Grund des Fundes und etwas Kontext davor und danach an die API.
- Der API-Key liegt nur in der Umgebungsvariable. Eine `.env`-Datei liest die App **nicht**.

## Grenzen

- Die Offline-Prüfungen sind **Heuristiken**. Sie erkennen zum Beispiel nicht, wer mit „er“ gemeint ist,
  und können nicht beurteilen, ob ein Rückblick inhaltlich wirklich vorzeitig ist. Dafür gibt es die KI.
- Die **Satzbau-Erkennung** (zum Beispiel Schachtelsätze) hängt vom Parser ab und kann bei sehr langen
  oder umgangssprachlichen Sätzen danebenliegen. Bei den Schachtelsätzen prüft die KI deshalb auf Wunsch
  nach, ob ein gefundener Satz wirklich unübersichtlich ist. Sie sieht aber nur die vom Parser gefundenen
  Sätze, nicht solche, die der Parser übersehen hat.
- Das KI-Modul „Unübersichtliche Konstruktionen“ und die KI-Prüfung der Schachtelsätze können denselben Satz
  melden. Das ist gewollt: Das erste liest den ganzen Text, das zweite bewertet gezielt die Kandidaten.
- **LanguageTool** ist vorsichtig und meldet nur, was zu seinen Regeln passt. Er findet Tippfehler und
  typische Grammatik- und Kommafehler, aber längst nicht jeden Fehler.
- Die **KI** ist breiter, aber nicht fehlerfrei und kann zu eifrig melden. Das hängt vom Modell ab.
- Die Standardwerte (Satzlänge, Abstände, Wortlisten) sind Startwerte. Passe sie an deinen Text an.
- Die App ist für **deutschen Fließtext** gedacht.

## Fehlerbehebung

| Problem | Ursache und Lösung |
|---|---|
| „spaCy-Modell … ist nicht installiert“ | `python -m spacy download de_core_news_lg` im aktivierten `.venv` ausführen. |
| Rechtschreibung meldet „… konnten nicht geprüft werden“ | LanguageTool konnte nicht starten. Läuft Java (`java -version`)? Beim ersten Mal braucht der Download Internet. |
| „Der Text ist zu lang“ | Offline sind bis 150 000 Zeichen erlaubt, bei der KI 60 000. Prüfe längere Texte abschnittsweise. |
| „Kein API-Key gefunden“ | `export ANTHROPIC_API_KEY="…"` im selben Terminal setzen, App beenden (Ctrl+C) und neu starten. |
| „Der API-Key wurde abgelehnt“ | Key in der Anthropic Console prüfen. |
| „Port 8765 ist belegt“ beim Start | Feinschliff läuft vielleicht schon, oder ein anderes Programm nutzt den Port. Mit anderem Port starten: `FEINSCHLIFF_PORT=8770 python app.py`. |
| „… läuft nur mit der KI-Prüfung“ / „nur offline“ | Du hast Module gewählt, die zum Knopf nicht passen. Siehe die Etiketten in der Liste links. |
| Oben steht „Fehler – Einzelheiten rechts“ | Die genaue Meldung steht rechts über der Liste, die Ursache im Terminal. |
| Offline findet nichts, die KI viel | Normal: LanguageTool ist vorsichtig, die KI breiter. Prüfe, welche Hinweise stimmen. |
| Derselbe gelbe Hinweis kommt immer wieder | Wenn die Stelle stimmt, den Knopf **In Ordnung** am Fund klicken. |
| Auswahl vergessen oder falsch | Der Browser speichert sie pro Browser. Mit „Keine“ setzt du alles zurück. |

## Projektaufbau

```
app.py                  Webserver (Flask) und Einstiegspunkt
modules.py              Register aller Prüfmodule (Gruppen, Optionen, Etiketten)
checker.py              Erzählzeit und Erzählperspektive (offline, spaCy)
grundlagen.py           Gemeinsame Bausteine (Fund, Erkennung direkter Rede)
satzbau.py              Satzlänge, Kurze Sätze, Satzanfänge, Schachtelsätze, Passiv
wortwahl.py             Füllwörter, Redebegleitung, Gefühle benannt
wiederholung.py         Wortwiederholungen, Wortfolgen
eigene_listen.py        Eigene Wortlisten lesen und speichern (Ordner eigene-listen/)
sprachrichtigkeit.py    LanguageTool, einheitliche Schreibweisen, Kommafolgen
ai_check.py             KI-Prüfung über die Claude-API
listen/                 Startlisten als Textdateien (siehe listen/README.md)
eigene-listen/          Deine eigenen Wörter (wird angelegt; nicht veröffentlichen)
templates/index.html    Oberfläche (Seitenaufbau)
static/app.css          Oberfläche (Gestaltung, hell und dunkel)
static/app.js           Oberfläche (Verhalten)
requirements.txt        Python-Abhängigkeiten
CHANGELOG.md            Änderungen pro Version
LICENSE                 MIT-Lizenz
.gitignore              Was nicht ins Repository gehört (.venv, eigene-listen/, Keys)
```

## Lizenz und verwendete Komponenten

Der Code von Feinschliff steht unter der **MIT-Lizenz** (siehe Datei `LICENSE`). Du darfst ihn nutzen, ändern und
weitergeben, der Copyright-Hinweis muss erhalten bleiben. Die App funktioniert ohne Gewähr.

Feinschliff liefert die folgenden Komponenten **nicht mit**. Sie werden bei der Installation geladen und haben
jeweils ihre **eigene Lizenz** (Stand der Prüfung: Angaben in den installierten Paketen, bitte bei Bedarf nachlesen):

| Komponente | Wofür | Lizenz laut Paket |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | lokaler Webserver | BSD-3-Clause |
| [spaCy](https://spacy.io/) mit Modell `de_core_news_lg` | Satz- und Wortanalyse offline | MIT |
| [LanguageTool](https://languagetool.org/) über [language_tool_python](https://github.com/jxmorris12/language_tool_python) | Rechtschreibung und Grammatik offline | Paket: GPL-3.0; LanguageTool selbst: LGPL |
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | optionale KI-Prüfung | Apache-2.0 |

**Hinweis zu GPL:** Das Paket `language_tool_python` steht unter der GPL. Feinschliff nutzt es nur als Bibliothek und
liefert es nicht aus. Wer Feinschliff **zusammen mit** diesem Paket weitergibt (zum Beispiel als fertiges Installationspaket),
sollte die Bedingungen der GPL prüfen. Das ist keine Rechtsberatung.
