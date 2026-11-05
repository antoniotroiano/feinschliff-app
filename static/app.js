(() => {
  const cfg = JSON.parse(document.getElementById('cfg').textContent);
  const $ = (s) => document.querySelector(s);

  const MODULE = cfg.module;  // Modul-ID -> Anzeigename
  const FARBEN = cfg.farben;  // Modul-ID -> Farbton der Gruppe

  // Etikett mit dem Namen des Moduls und einem Quadrat in der Farbe seiner Gruppe
  function modTag(id) {
    const t = el('span', 'mod');
    const q = el('i', 'msq');
    q.style.setProperty('--gh', FARBEN[id] ?? 265);
    t.append(q, document.createTextNode(MODULE[id] || id));
    return t;
  }

  const editor = $('#editor');
  const work = $('.work');
  const goBtn = $('#go');
  const aiBtn = $('#goai');
  const statusEl = $('#status');
  const wordsEl = $('#words');
  const chipsEl = $('#chips');
  const listEl = $('#list');
  const notesEl = $('#notes');
  const countEl = $('#count');
  const okToggle = $('#ok-toggle');
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  let findings = [];
  let showOk = false;  // „In Ordnung“ bestätigte Funde anzeigen?

  // Bestätigte Funde („In Ordnung“): gemerkt wird ein Fingerabdruck aus Modul, Wort und Satz. Ändert sich der Satz,
  // kommt der Hinweis wieder. Im Browser gespeichert, nur als Fingerabdruck, nicht als Text.
  function fnv(str) {
    let h = 0x811c9dc5;
    for (let k = 0; k < str.length; k++) { h ^= str.charCodeAt(k); h = Math.imul(h, 0x01000193) >>> 0; }
    return `${h.toString(16)}-${str.length}`;
  }
  const okKey = (modul, wort, satz) => fnv(`${modul}\u0001${wort}\u0001${satz}`);
  let okSet = new Set();
  try { okSet = new Set(JSON.parse(localStorage.getItem('zp-ok') || '[]')); } catch (e) { /* ohne Speicher weiter */ }
  function saveOk() {
    try { localStorage.setItem('zp-ok', JSON.stringify([...okSet].slice(-2000))); } catch (e) { /* ignorieren */ }
  }
  let lastNotes = [];
  let current = -1;
  const hidden = new Set();

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };

  // Tastenbeschriftung nach Betriebssystem (Mac: ⌘ und ⌥, sonst Strg und Alt)
  const MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || '');
  const TASTE = { pruefen: MAC ? '⌘↵' : 'Strg+↵', weiter: MAC ? '⌥J' : 'Alt+J', zurueck: MAC ? '⌥K' : 'Alt+K' };
  document.querySelectorAll('#go kbd').forEach((k) => { k.textContent = TASTE.pruefen; });
  $('#prev').title = `Vorheriger Fund (${TASTE.zurueck})`;
  $('#next').title = `Nächster Fund (${TASTE.weiter})`;

  // ---- Editor ----------------------------------------------------------
  try { editor.contentEditable = 'plaintext-only'; } catch (e) { /* älterer Browser */ }
  const plain = editor.contentEditable === 'plaintext-only';
  if (!plain) editor.contentEditable = 'true';

  const getText = () => (plain ? editor.textContent : editor.innerText).replace(/ /g, ' ');

  function updateWords() {
    const n = getText().trim().split(/\s+/).filter(Boolean).length;
    wordsEl.textContent = n.toLocaleString('de-DE') + (n === 1 ? ' Wort' : ' Wörter');
  }

  function render(text, spans, list) {
    const chars = Array.from(text);  // Codepoints wie in Python
    // Längere Bereiche (Sätze) zuerst, damit Wörter darin verschachtelt werden können
    const marks = [
      ...spans.map(([s, e]) => ({ s, e, kind: 'dialog', tip: 'Direkte Rede (nicht geprüft)' })),
      ...list.map((f, i) => ({ s: f.start, e: f.end, kind: f.level + (f.ki ? ' ki' : '') + (f.ok ? ' okay' : ''), tip: f.message, i, mod: f.module })),
    ].sort((a, b) => a.s - b.s || b.e - a.e);
    marks.forEach((m) => { m.long = ['satzlaenge', 'schachtel', 'kurze_saetze'].includes(m.mod); });  // ganze Sätze: dezentere Fläche

    editor.textContent = '';
    const stack = [{ e: Infinity, node: editor }];  // offene Markierungen
    let pos = 0;
    const put = (to) => {
      if (to > pos) stack[stack.length - 1].node.append(chars.slice(pos, to).join(''));
      pos = Math.max(pos, to);
    };
    for (const m of marks) {
      while (stack.length > 1 && stack[stack.length - 1].e <= m.s) { put(stack[stack.length - 1].e); stack.pop(); }
      put(m.s);
      const top = stack[stack.length - 1];
      const end = Math.min(m.e, top.e);  // teilweise Überlappung: am Rand des umgebenden Bereichs kappen
      if (end <= m.s) continue;
      const sp = el('span', 'm ' + m.kind + (m.long ? ' span' : ''));
      sp.title = m.tip;
      if (m.i !== undefined) { sp.dataset.i = m.i; sp.dataset.mod = m.mod; }
      top.node.append(sp);
      stack.push({ e: end, node: sp });
    }
    while (stack.length > 1) { put(stack[stack.length - 1].e); stack.pop(); }
    put(chars.length);
  }

  // ---- Einstellungen (Module) -------------------------------------------------
  const modules = () => [...document.querySelectorAll('.module')];
  const modOn = (m) => m.querySelector('.mod-on').checked;
  const allowed = () => [...document.querySelectorAll('[data-opt=zeiten] input:checked')].map((i) => i.value);

  function optValue(o) {
    if (o.dataset.typ === 'mehrfach') return [...o.querySelectorAll('input:checked')].map((i) => i.value);
    if (o.dataset.typ === 'schalter') return o.checked;
    return o.value;
  }

  // Gewählte Module mit ihren Optionen, so wie der Server sie erwartet
  function collect() {
    const out = {};
    for (const m of modules()) {
      if (!modOn(m)) continue;
      const opts = {};
      m.querySelectorAll('[data-opt]').forEach((o) => {
        opts[o.dataset.opt] = optValue(o);
      });
      out[m.dataset.module] = opts;
    }
    return out;
  }

  function syncModule(m) { m.classList.toggle('on', modOn(m)); }

  function saveSettings() {
    try {
      const state = {};
      for (const m of modules()) {
        const opts = {};
        m.querySelectorAll('[data-opt]').forEach((o) => {
          opts[o.dataset.opt] = optValue(o);
        });
        state[m.dataset.module] = { on: modOn(m), opts };
      }
      localStorage.setItem('zp-settings3', JSON.stringify({ modules: state, model: $('#model').value }));
    } catch (e) { /* ohne Speicher weiter */ }
  }

  function loadSettings() {
    try {
      const s = JSON.parse(localStorage.getItem('zp-settings3') || 'null');
      if (!s) return;
      for (const m of modules()) {
        const st = s.modules && s.modules[m.dataset.module];
        if (!st) continue;
        m.querySelector('.mod-on').checked = !!st.on;
        m.querySelectorAll('[data-opt]').forEach((o) => {
          const v = st.opts && st.opts[o.dataset.opt];
          if (v === undefined) return;
          if (o.dataset.typ === 'mehrfach') o.querySelectorAll('input').forEach((i) => { i.checked = v.includes(i.value); });
          else if (o.dataset.typ === 'schalter') o.checked = !!v;
          else if (o.dataset.typ === 'zahl' || o.dataset.typ === 'text') o.value = v;
          else if ([...o.options].some((x) => x.value === v)) o.value = v;
        });
      }
      if (s.model) $('#model').value = s.model;
    } catch (e) { /* ignorieren */ }
  }

  function setFontSize(delta) {
    const cur = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--editor-size')) || 1.2;
    const next = Math.min(1.8, Math.max(0.95, Math.round((cur + delta) * 100) / 100));
    document.documentElement.style.setProperty('--editor-size', next + 'rem');
    try { localStorage.setItem('zp-size', String(next)); } catch (e) { /* ignorieren */ }
  }

  try {
    const sz = localStorage.getItem('zp-size');
    if (sz) document.documentElement.style.setProperty('--editor-size', sz + 'rem');
  } catch (e) { /* ignorieren */ }

  // ---- Legende --------------------------------------------------------------
  function effect(z, ok) {
    if (!ok.has(z)) return 'Rot: im Erzähltext nicht erlaubt.';
    if (z === 'Plusquamperfekt') return 'Gelb: erlaubt, nur ein Hinweis – stimmt die Vorzeitigkeit?';
    if (z === 'Perfekt' && ok.has('Präsens') && !ok.has('Präteritum')) return 'Gelb: erlaubt, Hinweis auf Vorzeitigkeit.';
    if (z === 'Präteritum' && ok.has('Plusquamperfekt')) return 'Erlaubt. Gelb nur, wenn ein Zeitwort wie „gestern“ oder „zuvor“ im Satz steht.';
    if (z === 'Präsens' && ok.has('Perfekt')) return 'Erlaubt. Gelb nur, wenn ein Zeitwort wie „gestern“ oder „zuvor“ im Satz steht.';
    return 'Erlaubt, nicht markiert.';
  }

  function updateLegend() {
    const ok = new Set(allowed());
    const body = $('#legend-body');
    body.textContent = '';
    const section = (titel, items) => {
      body.append(el('h3', '', titel));
      const dl = el('dl', 'tenses');
      for (const [label, cls, text] of items) {
        const dt = el('dt');
        dt.append(cls === null ? document.createTextNode(label) : el('span', cls, label));
        dl.append(dt, el('dd', '', text));
      }
      body.append(dl);
    };
    section('Farben im Text', [
      ['Rot', 'sw m rot', 'Verstoß gegen deine Einstellung oder ein sicherer Fehler, zum Beispiel eine nicht erlaubte Zeit oder ein Rechtschreibfehler. Ändern.'],
      ['Gelb', 'sw m gelb', 'Bitte prüfen, zum Beispiel Vorzeitigkeit, ein langer Satz, ein Füllwort oder eine Wiederholung.'],
      ['Blau', 'sw m blau', 'Vorschlag, kein Fehler, zum Beispiel Passiv oder ein nur benanntes Gefühl.'],
      ['Grau', 'sw m dialog', 'Direkte Rede. Sie wird nicht geprüft.'],
    ]);
    section('Zeichen im Text', [
      ['Blasse Fläche', null, 'Ein ganzer Satz (zum Beispiel zu lang). Kräftig darin: ein einzelnes Wort.'],
      ['Gestrichelt', null, 'Fund der KI-Prüfung. In der Liste steht dazu „KI“.'],
    ]);
    const gruppen = el('dl', 'tenses');
    for (const g of cfg.gruppen) {
      const dt = el('dt');
      const q = el('i', 'msq');
      q.style.setProperty('--gh', g.farbe);
      dt.append(q, document.createTextNode(g.name));
      gruppen.append(dt);
    }
    body.append(el('h3', '', 'Gruppen in Liste und Filtern'), el('p', 'help', 'Das farbige Quadrat vor dem Modulnamen zeigt die Gruppe des Moduls. Es steht nur in der Liste rechts und in den Filtern, nicht im Text.'), gruppen);
    section('Welche Prüfung läuft wo?', [
      ['Offline', 'tag', 'Läuft nur mit „Prüfen“, auf deinem Rechner und ohne Kosten.'],
      ['KI', 'tag ki', 'Läuft nur mit „KI-Prüfung“. Der Text geht an die Anthropic-API.'],
      ['Offline + KI', 'tag', 'Läuft mit beiden Knöpfen.'],
    ]);
    body.append(el('p', 'help', 'Wählst du beides gemischt, läuft bei jedem Knopf, was passt. Der Rest steht als Hinweis rechts.'));
    const dl = el('dl', 'tenses');
    body.append(el('h3', '', 'Erzählzeiten'));
    for (const [z, beispiel] of Object.entries(cfg.zeiten)) {
      dl.append(el('dt', ok.has(z) ? '' : 'off', `${z} – ${beispiel}`), el('dd', '', effect(z, ok)));
    }
    body.append(dl);
    section('Bedienung', [
      [TASTE.pruefen, null, 'Offline prüfen.'],
      [`${TASTE.weiter} / ${TASTE.zurueck}`, null, 'Nächster oder vorheriger Fund.'],
      ['Klick', null, 'Auf eine Markierung oder einen Fund springt zur Gegenstelle. Bearbeitete Stellen werden abgehakt.'],
      ['In Ordnung', null, 'Am Fund: Du hast die Stelle geprüft, sie stimmt so. Die App merkt es sich für diesen Satz und blendet den Fund aus, bis sich der Satz ändert.'],
      ['Umformulieren', null, 'Am Fund (KI): schlägt für den Satz zwei Fassungen vor. „Übernehmen“ ersetzt den Satz im Text.'],
    ]);
  }

  // ---- Ergebnisse -------------------------------------------------------------
  function showEmpty() {
    listEl.textContent = '';
    const box = el('div', 'empty');
    box.append(el('p', '', 'Noch keine Prüfung.'));
    const ol = el('ol');
    ['Text in die Mitte einfügen.', 'Links die gewünschten Prüfungen wählen.', `„Prüfen“ klicken (${TASTE.pruefen}). Funde erscheinen hier und im Text.`]
      .forEach((t) => ol.append(el('li', '', t)));
    box.append(ol);
    listEl.append(box);
  }

  function showSkeleton() {
    listEl.textContent = '';
    for (let i = 0; i < 4; i++) listEl.append(el('div', 'sk'));
  }

  function renderChips() {
    chipsEl.textContent = '';
    const counts = {};
    findings.forEach((f) => { if (!f.ok || showOk) counts[f.module] = (counts[f.module] || 0) + 1; });
    for (const k of cfg.reihenfolge.filter((id) => counts[id])) {  // in der Reihenfolge der Gruppen
      const b = el('button', 'chip');
      b.type = 'button';
      b.dataset.mod = k;
      b.setAttribute('aria-pressed', String(!hidden.has(k)));
      const q = el('i');
      q.style.setProperty('--gh', FARBEN[k] ?? 265);
      b.append(q, document.createTextNode(`${MODULE[k] || k} ${counts[k]}`));
      chipsEl.append(b);
    }
  }

  function applyHidden() {
    document.querySelectorAll('[data-i]').forEach((n) => {
      const f = findings[Number(n.dataset.i)];
      n.classList.toggle('hid', !!f && hidden.has(f.module));
    });
  }

  function renderResults(error) {
    notesEl.textContent = '';
    if (error) notesEl.append(Object.assign(el('div', 'note error', error), { role: 'alert' }));
    if (lastNotes.length) {  // Hinweise gesammelt und eingeklappt, damit die Funde oben bleiben
      const box = el('details', 'notes');
      const kopf = el('summary', '', lastNotes.length === 1 ? '1 Hinweis zur Prüfung' : `${lastNotes.length} Hinweise zur Prüfung`);
      box.append(kopf);
      lastNotes.forEach((t) => box.append(el('div', 'note', t)));
      notesEl.append(box);
    }
    updateOkUi(false);
    renderChips();
    listEl.textContent = '';
    if (!findings.length) {
      if (!error) listEl.append(el('div', 'ok', 'Keine Auffälligkeiten gefunden.'));
      return;
    }
    findings.forEach((f, i) => {
      const row = el('div', 'row ' + f.level + (f.ok ? ' okay' : ''));
      row.setAttribute('role', 'button');
      row.tabIndex = 0;
      row.dataset.i = i;
      row.append(el('span', 'dot'));
      const head = el('span', 'head');
      head.append(el('span', 'w', f.word.length > 40 ? f.word.slice(0, 36).trimEnd() + ' …' : f.word), el('span', 't', f.tense), modTag(f.module));
      if (f.ki) head.append(el('span', 'kitag', 'KI'));
      row.append(head, el('span', 'msg', f.message));
      if (f.vorschlag) row.append(el('span', 'vs', f.vorschlag));
      row.append(rowActions(i));
      listEl.append(row);
    });
  }

  function select(i, fromText) {
    current = i;
    document.querySelectorAll('.m.sel, .row.sel').forEach((n) => n.classList.remove('sel'));
    const m = editor.querySelector(`.m[data-i="${i}"]`);
    const r = listEl.querySelector(`.row[data-i="${i}"]`);
    if (m) m.classList.add('sel');
    if (r) r.classList.add('sel');
    const behavior = reduceMotion ? 'auto' : 'smooth';
    if (fromText) { if (r) r.scrollIntoView({ block: 'nearest', behavior }); }
    else if (m) m.scrollIntoView({ block: 'center', behavior });
  }

  function step(dir) {
    const visible = findings.map((f, i) => i).filter((i) => !hidden.has(findings[i].module) && (showOk || !findings[i].ok));
    if (!visible.length) return;
    const pos = visible.indexOf(current);
    const next = pos < 0 ? (dir > 0 ? 0 : visible.length - 1) : (pos + dir + visible.length) % visible.length;
    select(visible[next], false);
  }

  // Kurze rote Warnung in der Statuszeile (und am betroffenen Bereich), danach wieder grau
  let warnTimer = 0;
  function warn(msg, target) {
    statusEl.textContent = msg;
    statusEl.classList.add('warn');
    if (target) target.classList.add('warn');
    clearTimeout(warnTimer);
    warnTimer = setTimeout(() => {
      statusEl.classList.remove('warn');
      document.querySelectorAll('.warn').forEach((n) => n.classList.remove('warn'));
    }, 3500);
  }

  // ---- Prüfen ---------------------------------------------------------------------
  function busy(on) {
    // Editor währenddessen sperren: Sonst würden Änderungen beim Eintreffen des Ergebnisses überschrieben
    editor.contentEditable = on ? 'false' : (plain ? 'plaintext-only' : 'true');
    editor.setAttribute('aria-busy', String(on));
    [goBtn, aiBtn].forEach((b) => { b.disabled = on; });
    goBtn.setAttribute('aria-busy', String(on));
  }

  async function run(url) {
    const text = getText();
    if (!text.trim()) { warn('Bitte zuerst einen Text einfügen.'); return; }
    const mods = collect();
    if (!Object.keys(mods).length) { warn('Bitte mindestens eine Prüfung auswählen.', $('.quick')); return; }
    if (mods.zeit && !mods.zeit.zeiten.length) { warn('Bitte mindestens eine Erzählzeit auswählen.', $('[data-module=zeit]')); return; }
    const isAi = url === '/check-ai';
    busy(true);
    showSkeleton();
    statusEl.classList.remove('warn', 'err');
    statusEl.textContent = isAi ? 'KI prüft … das kann etwas dauern' : 'Analysiere …';
    try {
      let r;
      try {
        r = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, modules: mods, model: $('#model').value }),
        });
      } catch (e) {
        throw new Error('Keine Verbindung zur App. Läuft sie noch im Terminal? Starte sie dort mit „python app.py“ neu.');
      }
      let d = null;
      try { d = await r.json(); } catch (e) { /* keine JSON-Antwort */ }
      if (!r.ok) throw new Error((d && d.error) || `Der Server meldet einen Fehler (Code ${r.status}). Einzelheiten stehen im Terminal.`);
      if (!d) throw new Error('Unerwartete Antwort der App. Einzelheiten stehen im Terminal.');
      const chars = Array.from(text);
      const idx16 = [];  // Codepoint-Position -> Position im JavaScript-Text (UTF-16)
      for (let k = 0, acc = 0; k <= chars.length; k++) { idx16.push(acc); if (k < chars.length) acc += chars[k].length; }
      findings = d.findings.map((f) => {
        const word = chars.slice(f.start, f.end).join('');
        const key = okKey(f.module, word, satzAus(text, idx16[f.start], idx16[f.start] + word.length).satz);
        return { ...f, word, key, ok: okSet.has(key) };
      });
      lastNotes = d.notes;
      hidden.clear();
      current = -1;
      render(text, d.spans, findings);
      renderResults();
      applyHidden();
      const u = d.usage
        ? ` · ${(d.usage.input + d.usage.output).toLocaleString('de-DE')} Tokens · ca. ${d.usage.usd.toLocaleString('de-DE', { maximumFractionDigits: 4 })} $`
        : '';
      statusEl.textContent = (isAi ? `KI-Prüfung (${$('#model').value.split(' (')[0]})` : 'Offline-Prüfung') + u;
    } catch (e) {
      console.error(e);
      statusEl.textContent = 'Fehler – Einzelheiten rechts';
      statusEl.classList.add('err');
      renderResults(e.message);
    } finally {
      busy(false);
    }
  }

  // ---- Umformulierung eines Satzes (KI) -----------------------------------------------------
  const ABKUERZUNGEN = new Set(['usw', 'bzw', 'ca', 'vgl', 'dr', 'nr', 'hr', 'fr', 'prof', 'etc', 'evtl', 'ggf', 'inkl', 'zzgl']);
  const SCHLIESSER = '“”«"\')';

  // Endet an Position k ein Satz? (Punkt nach Abkürzung, einzelnem Buchstaben oder Zahl zählt nicht.)
  function endetBei(t, k) {
    const c = t[k];
    if (!'.!?…'.includes(c)) return false;
    if (c === '.') {
      const w = (t.slice(Math.max(0, k - 8), k).match(/(\S+)$/) || [''])[0];
      if (/\d$/.test(w)) return false;
      if (w.length === 1 && /\p{L}/u.test(w)) return false;
      if (ABKUERZUNGEN.has(w.toLowerCase())) return false;
    }
    let j = k + 1;
    while (j < t.length && SCHLIESSER.includes(t[j])) j++;
    return j >= t.length || /\s/.test(t[j]);
  }

  function nachEnde(t, k) {
    let j = k + 1;
    while (j < t.length && SCHLIESSER.includes(t[j])) j++;
    while (j < t.length && /[ \t]/.test(t[j])) j++;
    return j;
  }

  // Satz um einen Fund herum, mit Kontext davor und danach. Maßgeblich ist der AKTUELLE Text im Editor:
  // Die Position des Fundes kommt aus seiner Markierung, so zählen Änderungen seit der letzten Prüfung mit.
  function satzAus(t, s16, e16) {
    let a = s16;
    while (a > 0 && t[a - 1] !== '\n' && !endetBei(t, a - 1)) a--;
    if (a > 0 && t[a - 1] !== '\n') a = nachEnde(t, a - 1);
    let b = e16;
    if (e16 > 0 && endetBei(t, e16 - 1)) {
      b = e16 - 1;  // der Fund reicht schon bis zum Satzzeichen am Ende
    } else {
      while (b < t.length && t[b] !== '\n' && !endetBei(t, b)) b++;
    }
    if (b < t.length && t[b] !== '\n') b = nachEnde(t, b);
    const satz = t.slice(a, b).trim();
    return { satz, hint: a, davor: t.slice(Math.max(0, a - 600), a), danach: t.slice(b, b + 600) };
  }

  // Satz um den Fund i im AKTUELLEN Editor-Text (Position aus der Markierung des Fundes)
  function satzUm(i) {
    const span = editor.querySelector(`.m[data-i="${i}"]`);
    if (!span) return null;
    const t = getText();
    const r = document.createRange();
    r.selectNodeContents(editor);
    r.setEnd(span, 0);
    const s16 = r.toString().length;
    return satzAus(t, s16, s16 + span.textContent.length);
  }

  // Bereich im Editor zu Zeichenpositionen (nur im Klartext-Modus, wo textContent = Text)
  function bereich(von, bis) {
    const w = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
    const r = document.createRange();
    let pos = 0, started = false;
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const len = n.nodeValue.length;
      if (!started && von <= pos + len) { r.setStart(n, von - pos); started = true; }
      if (started && bis <= pos + len) { r.setEnd(n, bis - pos); return r; }
      pos += len;
    }
    return null;
  }

  function uebernehmen(satz, neu, hint, meldung) {
    const cur = getText();
    let idx = cur.indexOf(satz, Math.max(0, hint - 200));
    if (idx < 0) idx = cur.indexOf(satz);
    const r = idx >= 0 && plain ? bereich(idx, idx + satz.length) : null;
    if (!r) { meldung('Der Satz steht so nicht mehr im Text. Bitte neu prüfen oder die Fassung kopieren.', true); return; }
    editor.focus();
    const sel = getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    document.execCommand('insertText', false, neu);
    updateWords();
    meldung('Fassung übernommen. Du kannst jederzeit erneut prüfen.', false);
  }

  // Zeigt oder versteckt die als „In Ordnung“ bestätigten Funde und passt Zähler und Umschalter an
  function updateOkUi() {
    const ok = findings.filter((f) => f.ok).length;
    const offen = findings.length - ok;
    countEl.textContent = findings.length ? `(${showOk ? findings.length : offen})` : '';
    okToggle.hidden = ok === 0;
    okToggle.textContent = showOk ? `${ok} als „In Ordnung“ markierte werden angezeigt · ausblenden`
      : `${ok} als „In Ordnung“ ausgeblendet · anzeigen`;
    work.classList.toggle('show-ok', showOk);
  }

  function toggleOk(i, btn) {
    const f = findings[i];
    const span = editor.querySelector(`.m[data-i="${i}"]`);
    const um = satzUm(i);  // aktueller Satz, falls die Markierung noch im Text steht
    const key = um ? okKey(f.module, span.textContent, um.satz) : f.key;
    if (f.ok) { okSet.delete(f.key); okSet.delete(key); f.ok = false; }
    else { okSet.add(key); f.key = key; f.ok = true; }
    saveOk();
    btn.closest('.row').classList.toggle('okay', f.ok);
    if (span) span.classList.toggle('okay', f.ok);
    btn.textContent = f.ok ? 'Rückgängig' : 'In Ordnung';
    updateOkUi();
    renderChips();
    statusEl.classList.remove('warn', 'err');
    statusEl.textContent = f.ok
      ? 'Gemerkt: In diesem Satz ist die Stelle in Ordnung. Zurücknehmen über „anzeigen“ oben rechts bei den Funden.'
      : 'Wieder als offener Fund markiert.';
  }

  // KI-Vorschlag: ersetzt die markierte Stelle im aktuellen Text
  function vorschlagUebernehmen(i, meldung, wrap) {
    const span = editor.querySelector(`.m[data-i="${i}"]`);
    if (!span || span.classList.contains('done')) {
      meldung('Die Stelle ist im Text nicht mehr markiert (geändert?). Bitte neu prüfen oder den Vorschlag kopieren.', true);
      return;
    }
    const r = document.createRange();
    r.selectNodeContents(span);
    editor.focus();
    const sel = getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    document.execCommand('insertText', false, findings[i].vorschlag);
    erledigt(i);
    updateWords();
    meldung('Vorschlag übernommen. Du kannst jederzeit erneut prüfen.', false);
    wrap.closest('.row').classList.add('offen');
  }

  function rowActions(i) {
    const wrap = el('span', 'row-aktion');
    const btn = el('button', 'link', 'Umformulieren (KI)');
    btn.type = 'button';
    btn.title = 'Schickt diesen Satz mit etwas Text davor und danach an die KI';
    const out = el('span', 'fassungen');
    const meldung = (t, fehler) => { const m = el('span', fehler ? 'rw-fehler' : 'rw-ok', t); out.prepend(m); };
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const f = findings[i];
      const um = satzUm(i);
      if (!um) { out.textContent = ''; meldung('Der Fund ist im Text nicht mehr markiert. Bitte neu prüfen.', true); return; }
      const { satz, hint, davor, danach } = um;
      if (!satz) { out.textContent = ''; meldung('Kein Satz gefunden.', true); return; }
      btn.disabled = true;
      btn.textContent = 'KI schreibt …';
      out.textContent = '';
      try {
        const r = await fetch('/umformulieren', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ satz, davor, danach, hinweis: `${f.tense}: ${f.message}`, modules: collect(), model: $('#model').value }),
        });
        const d = await r.json().catch(() => null);
        if (!r.ok) throw new Error((d && d.error) || `Der Server meldet einen Fehler (Code ${r.status}). Einzelheiten stehen im Terminal.`);
        d.fassungen.forEach((fa) => {
          const box = el('span', 'fassung');
          box.append(el('span', 'fa', fa.art), el('span', 'ft', fa.text));
          const knoepfe = el('span', 'fk');
          const ueb = el('button', 'link', 'Übernehmen');
          ueb.type = 'button';
          ueb.addEventListener('click', (ev) => { ev.stopPropagation(); uebernehmen(satz, fa.text, hint, meldung); });
          const kop = el('button', 'link', 'Kopieren');
          kop.type = 'button';
          kop.addEventListener('click', async (ev) => {
            ev.stopPropagation();
            try { await navigator.clipboard.writeText(fa.text); meldung('Kopiert.', false); } catch (x) { meldung('Kopieren nicht möglich.', true); }
          });
          knoepfe.append(ueb, kop);
          box.append(knoepfe);
          out.append(box);
        });
        statusEl.classList.remove('warn', 'err');
        statusEl.textContent = `Umformulierung · ${(d.usage.input + d.usage.output).toLocaleString('de-DE')} Tokens · ca. ${d.usage.usd.toLocaleString('de-DE', { maximumFractionDigits: 4 })} $`;
      } catch (err) {
        console.error(err);
        meldung(err.message, true);
        statusEl.classList.add('err');
        statusEl.textContent = 'Fehler bei der Umformulierung';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Noch einmal umformulieren';
      }
      wrap.closest('.row').classList.add('offen');
    });
    const okBtn = el('button', 'link', findings[i].ok ? 'Rückgängig' : 'In Ordnung');
    okBtn.type = 'button';
    okBtn.title = 'Du hast die Stelle geprüft, sie stimmt so. Die App merkt es sich für diesen Satz.';
    okBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleOk(i, okBtn); });
    const f0 = findings[i];
    if (f0.vorschlag) {
      const ueb = el('button', 'link', 'Vorschlag übernehmen');
      ueb.type = 'button';
      ueb.title = 'Ersetzt die markierte Stelle im Text durch den Vorschlag';
      ueb.addEventListener('click', (e) => { e.stopPropagation(); vorschlagUebernehmen(i, meldung, wrap); });
      const kop = el('button', 'link', 'Kopieren');
      kop.type = 'button';
      kop.addEventListener('click', async (e) => {
        e.stopPropagation();
        try { await navigator.clipboard.writeText(f0.vorschlag); meldung('Kopiert.', false); } catch (x) { meldung('Kopieren nicht möglich.', true); }
      });
      wrap.append(ueb, kop);
    }
    wrap.append(okBtn, btn, out);
    return wrap;
  }

  // Wörter aus einem Eingabefeld dauerhaft in die eigene Liste schreiben
  async function saveList(btn) {
    const input = btn.closest('.module').querySelector(`input[data-opt="${btn.dataset.opt}"]`);
    if (!input.value.trim()) { warn('Das Feld ist leer.', input); return; }
    try {
      const r = await fetch('/liste-uebernehmen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ liste: btn.dataset.liste, woerter: input.value }),
      });
      const d = await r.json().catch(() => null);
      if (!r.ok) throw new Error((d && d.error) || `Fehler ${r.status}`);
      input.value = '';
      saveSettings();
      statusEl.classList.remove('warn', 'err');
      statusEl.textContent = `${d.neu} neu in ${d.datei}` + (d.schon ? `, ${d.schon} schon vorhanden` : '');
    } catch (e) {
      console.error(e);
      statusEl.classList.add('err');
      statusEl.textContent = e.message;
    }
  }

  // ---- Ereignisse ---------------------------------------------------------------------
  goBtn.addEventListener('click', () => run('/check'));
  aiBtn.addEventListener('click', () => run('/check-ai'));
  $('#prev').addEventListener('click', () => step(-1));
  $('#next').addEventListener('click', () => step(1));
  $('#fs-minus').addEventListener('click', () => setFontSize(-0.1));
  $('#fs-plus').addEventListener('click', () => setFontSize(0.1));

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); run('/check'); }
    else if (e.altKey && e.code === 'KeyJ') { e.preventDefault(); step(1); }
    else if (e.altKey && e.code === 'KeyK') { e.preventDefault(); step(-1); }
  });

  $('.side-scroll').addEventListener('change', (e) => {
    const m = e.target.closest('.module');
    if (m) syncModule(m);
    updateLegend();
    saveSettings();
  });
  $('#model').addEventListener('change', saveSettings);
  document.querySelectorAll('.save-list').forEach((b) => b.addEventListener('click', () => saveList(b)));

  // Schnellwahl: alle Prüfungen an oder aus
  document.querySelectorAll('[data-quick]').forEach((b) => b.addEventListener('click', () => {
    const on = b.dataset.quick === 'all';
    modules().forEach((m) => { m.querySelector('.mod-on').checked = on; syncModule(m); });
    saveSettings();
  }));

  okToggle.addEventListener('click', () => { showOk = !showOk; updateOkUi(); renderChips(); });

  chipsEl.addEventListener('click', (e) => {
    const b = e.target.closest('.chip');
    if (!b) return;
    const k = b.dataset.mod;
    if (hidden.has(k)) hidden.delete(k); else hidden.add(k);
    b.setAttribute('aria-pressed', String(!hidden.has(k)));
    applyHidden();
  });

  listEl.addEventListener('click', (e) => {
    if (e.target.closest('.row-aktion')) return;
    const row = e.target.closest('.row');
    if (row) select(Number(row.dataset.i), false);
  });
  listEl.addEventListener('keydown', (e) => {
    const row = e.target.classList && e.target.classList.contains('row') ? e.target : null;
    if (row && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); select(Number(row.dataset.i), false); }
  });

  editor.addEventListener('click', (e) => {
    const m = e.target.closest('.m[data-i]');
    if (m) select(Number(m.dataset.i), true);
  });

  // Vor jeder Änderung merken, welche Markierungen die Auswahl ganz oder am Rand überdeckt (Einfügen über markiertem Text)
  let ueberschrieben = [];
  editor.addEventListener('beforeinput', () => {
    ueberschrieben = [];
    const sel = getSelection();
    if (!sel || !sel.rangeCount || sel.isCollapsed) return;
    const r = sel.getRangeAt(0);
    editor.querySelectorAll('.m[data-i]').forEach((m) => {
      if (!r.intersectsNode(m)) return;
      const mr = document.createRange();
      mr.selectNodeContents(m);
      const mittendrin = r.compareBoundaryPoints(Range.START_TO_START, mr) > 0 && r.compareBoundaryPoints(Range.END_TO_END, mr) < 0;
      if (!mittendrin) ueberschrieben.push(m.dataset.i);
    });
  });

  // Fund als erledigt kennzeichnen (Markierung im Text und Zeile in der Liste)
  function erledigt(i) {
    editor.querySelectorAll(`.m[data-i="${i}"]`).forEach((m) => { m.classList.add('done'); m.removeAttribute('title'); });
    const row = listEl.querySelector(`.row[data-i="${i}"]`);
    if (row) row.classList.add('done');
  }

  // Beim Überschreiben einer Markierung übernimmt der Browser deren Farbe als eingebettetes Format. Das entfernen,
  // damit eingefügter oder übernommener Text wirklich unmarkiert bleibt (Cursorposition bleibt erhalten).
  function bereinigen() {
    const fremd = [...editor.querySelectorAll('span:not(.m), [style]')];
    if (!fremd.length) return;
    const sel = getSelection();
    let pos = null;
    if (sel && sel.rangeCount && editor.contains(sel.anchorNode)) {
      const r = document.createRange();
      r.selectNodeContents(editor);
      r.setEnd(sel.anchorNode, sel.anchorOffset);
      pos = r.toString().length;
    }
    fremd.forEach((n) => {
      if (!editor.contains(n)) return;
      if (n.matches('.m')) n.removeAttribute('style');
      else if (n.tagName === 'SPAN') n.replaceWith(...n.childNodes);
      else n.removeAttribute('style');
    });
    editor.normalize();
    if (pos !== null) {
      const r = bereich(pos, pos);
      if (r) { r.collapse(true); sel.removeAllRanges(); sel.addRange(r); }
    }
  }

  editor.addEventListener('input', () => {
    bereinigen();
    updateWords();
    ueberschrieben.forEach(erledigt);
    ueberschrieben = [];
    // Bearbeitete Stelle: Markierung entfernen, Fund abhaken
    const sel = getSelection();
    const node = sel && sel.anchorNode;
    const target = node && (node.nodeType === 3 ? node.parentElement : node);
    const m = target && target.closest && target.closest('.m[data-i]');
    if (m && editor.contains(m)) erledigt(m.dataset.i);
    // Markierung ganz überschrieben (verschwunden): Fund ebenfalls abhaken
    listEl.querySelectorAll('.row[data-i]:not(.done)').forEach((row) => {
      if (!editor.querySelector(`.m[data-i="${row.dataset.i}"]`)) erledigt(row.dataset.i);
    });
  });

  // Einfügen immer als reiner Text
  editor.addEventListener('paste', (e) => {
    e.preventDefault();
    document.execCommand('insertText', false, e.clipboardData.getData('text/plain'));
  });

  loadSettings();
  modules().forEach(syncModule);
  updateLegend();
  updateWords();
  showEmpty();
})();
