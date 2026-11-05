# Änderungen

Format nach [Keep a Changelog](https://keepachangelog.com/de/), Versionen nach [Semantic Versioning](https://semver.org/lang/de/).

## 0.1.1 – 2026-11-05
- Der Editor ist während einer Prüfung gesperrt, damit Änderungen beim Eintreffen des Ergebnisses nicht überschrieben werden.
- Schutz vor fremden Webseiten im Browser: Die App nimmt nur Anfragen an `127.0.0.1` und `localhost` an. Zusätzliche Kopfzeilen gegen Einbettung.
- Eingaben werden geprüft (Typ, Größe). Wörter für „Rechtschreibung (KI)“ werden gefiltert. Sehr lange „Sätze“ gehen nicht an die KI.
- KI-Vorschlag direkt übernehmbar, Hinweise zur Prüfung eingeklappt. Eingefügter Text über einer Markierung behält deren Farbe nicht mehr.
- KI-Anfragen brechen nach 5 Minuten ab, mit klarer Meldung. Warnung beim Start, wenn `ANTHROPIC_BASE_URL` gesetzt ist.
- Beim Start prüft die App, ob der Port frei ist, und öffnet sonst den Browser nicht. **Geändert:** Die Port-Variable heißt jetzt `FEINSCHLIFF_PORT` (vorher `PORT`).
- Unbekannte Großwörter gelten erst ab dreimaligem Vorkommen als Name.
- Tastenkürzel werden je nach System als ⌘ und ⌥ oder als Strg und Alt angezeigt.
- Mindestversionen der Abhängigkeiten, README überarbeitet (Installation, Voraussetzungen, Lizenzen), Code aufgeräumt.

## 0.1.0 – 2026-11-05 – Erste veröffentlichte Version
- Prüfmodule in sechs Gruppen: Erzählung, Satzbau, Wortwahl, Wiederholungen, Stil und Fluss, Sprachrichtigkeit.
- Offline-Prüfung (spaCy, LanguageTool, eigene Regeln) und optionale KI-Prüfung mit Claude (Haiku, Sonnet, Opus).
- Funde direkt im Text markiert (Rot, Gelb, Blau, Grau für Dialog), mit Filtern und Fundliste.
- „In Ordnung“ für bestätigte Funde, KI-Vorschlag übernehmen, Satz umformulieren (KI).
- Eigene Wortlisten im Ordner `eigene-listen/`.
