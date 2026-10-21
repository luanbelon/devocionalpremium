// Paginador executado dentro do documento do livro (preview no navegador e
// Chromium headless no servidor). Monta as páginas a partir do JSON embutido,
// medindo o layout real: parágrafos fluem entre páginas sem nunca cortar texto,
// com no mínimo 2 linhas em cada lado de uma quebra, e os cards do dia ficam no
// pé da última página. Ao final publica o relatório em window.__BOOK_REPORT__.
//
// É JavaScript puro (sem transpilação), por isso fica como string.
export const PAGINATOR_JS = String.raw`
(function () {
  'use strict';
  var DATA = JSON.parse(document.getElementById('book-data').textContent);
  var book = DATA.book, S = DATA.settings, L = DATA.labels, G = DATA.geometry, ICONS = DATA.icons;
  var TIERS = DATA.gutterTiers, MIN_OUT = DATA.minOutside;
  var root = document.getElementById('book');
  var docEl = document.documentElement;
  var MIN_LINES = 2;
  var state;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  function img(src) {
    var i = document.createElement('img');
    i.src = src;
    i.alt = '';
    return i;
  }

  function minGutter(pages) {
    for (var i = 0; i < TIERS.length; i++) {
      if (pages >= TIERS[i].minPages && pages <= TIERS[i].maxPages) return TIERS[i].gutter;
    }
    return pages < TIERS[0].minPages ? TIERS[0].gutter : TIERS[TIERS.length - 1].gutter;
  }

  function setVars(p) {
    var s = docEl.style;
    s.setProperty('--fs', p.fs + 'pt');
    s.setProperty('--lh', String(p.lh));
    s.setProperty('--pad-inside', p.inside + 'in');
    s.setProperty('--pad-outside', (p.outside + G.bleedPad) + 'in');
    s.setProperty('--pad-top', (p.top + G.bleedPad) + 'in');
    s.setProperty('--pad-bottom', (p.bottom + G.bleedPad) + 'in');
    s.setProperty('--footer-bottom', (Math.max(0.3, p.bottom - 0.2) + G.bleedPad) + 'in');
  }

  // ---------- páginas ----------

  function newPage(kind, chrome) {
    state.pageNo++;
    var n = state.pageNo;
    var page = el('section', 'page ' + (n % 2 === 1 ? 'recto' : 'verso') + ' ' + kind);
    page.setAttribute('data-page', String(n));
    if (chrome) {
      var rh = el('header', 'running-header');
      rh.appendChild(el('div', 'rh-text', book.title));
      rh.appendChild(el('div', 'rh-line'));
      page.appendChild(rh);
    }
    var body = el('div', 'page-body');
    page.appendChild(body);
    if (chrome) page.appendChild(el('footer', 'page-footer', String(n)));
    root.appendChild(page);
    return { page: page, body: body, n: n };
  }

  function blankPage() { return newPage('blank', false); }

  function ensureRecto() {
    if ((state.pageNo + 1) % 2 === 0) blankPage();
  }

  function bottomOf(node) {
    var b = node.getBoundingClientRect().bottom;
    var cap = node.querySelector ? node.querySelector('.dropcap') : null;
    if (cap) b = Math.max(b, cap.getBoundingClientRect().bottom);
    return b;
  }

  function overflows(body) {
    var last = body.lastElementChild;
    if (!last) return false;
    return bottomOf(last) > body.getBoundingClientRect().bottom + 0.5;
  }

  // ---------- texto corrido ----------

  function makePara(words, o) {
    var p = el('p', 'para' + (o.cls ? ' ' + o.cls : '') + (o.split ? ' split' : '') + (o.cont ? ' cont' : ''));
    if (o.dropcap && !o.cont && words.length) {
      var m = /^([\u201C\u2018"'(\[\u00AB]*)(.)([\s\S]*)$/.exec(words[0]);
      if (m) {
        p.appendChild(el('span', 'dropcap', m[1] + m[2]));
        p.appendChild(document.createTextNode(m[3] + (words.length > 1 ? ' ' + words.slice(1).join(' ') : '')));
      }
    }
    if (!p.firstChild) p.textContent = words.join(' ');
    p.__words = words;
    p.__opt = o;
    return p;
  }

  function lineHeightOf(p) {
    var lh = parseFloat(getComputedStyle(p).lineHeight);
    return lh > 0 ? lh : 16;
  }

  function linesOf(p, lh) {
    return Math.round(p.getBoundingClientRect().height / lh);
  }

  // Maior prefixo (em palavras) que cabe no corpo da página, opcionalmente
  // limitado a maxLines linhas.
  function maxFitBy(body, n, build, maxLines, lh, textOf) {
    var lo = 1, hi = n - 1, best = 0;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      var part = build(mid);
      body.appendChild(part);
      var ok = !overflows(body) && (!maxLines || linesOf(textOf(part), lh) <= maxLines);
      body.removeChild(part);
      if (ok) { best = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return best;
  }

  function maxFit(body, words, o, maxLines, lh) {
    return maxFitBy(body, words.length, function (k) { return makePara(words.slice(0, k), o); }, maxLines, lh, function (e) { return e; });
  }

  function placeText(cur, text, opt, nextPage) {
    var words = String(text).split(/\s+/).filter(Boolean);
    var cont = false;
    var guard = 0;
    while (words.length && guard++ < 100) {
      var whole = { dropcap: opt.dropcap, cls: opt.cls, cont: cont, split: false };
      var full = makePara(words, whole);
      cur.body.appendChild(full);
      if (!overflows(cur.body)) return cur;

      var lh = lineHeightOf(full);
      var fullLines = linesOf(full, lh);
      cur.body.removeChild(full);

      var part = { dropcap: opt.dropcap, cls: opt.cls, cont: cont, split: true };
      var k = 0;
      if (fullLines >= MIN_LINES * 2) {
        k = maxFit(cur.body, words, part, 0, lh);
        if (k > 0) {
          var probe = makePara(words.slice(0, k), part);
          cur.body.appendChild(probe);
          var l1 = linesOf(probe, lh);
          cur.body.removeChild(probe);
          if (l1 < MIN_LINES) k = 0;
          else if (fullLines - l1 < MIN_LINES) k = maxFit(cur.body, words, part, fullLines - MIN_LINES, lh);
        }
      }

      if (k > 0) {
        cur.body.appendChild(makePara(words.slice(0, k), part));
        words = words.slice(k);
        cont = true;
      } else if (!cur.body.children.length) {
        cur.body.appendChild(full);
        state.warnings.push('Um bloco de texto é maior que a página e foi cortado na página ' + cur.n + '.');
        return cur;
      }
      cur = nextPage();
    }
    return cur;
  }

  function placeBlock(cur, node, nextPage) {
    cur.body.appendChild(node);
    if (!overflows(cur.body)) return cur;
    if (cur.body.children.length === 1) return cur;
    cur.body.removeChild(node);
    cur = nextPage();
    cur.body.appendChild(node);
    return cur;
  }

  // ---------- pré-textuais ----------

  function renderFrontMatter() {
    var fm = book.frontMatter;
    var c;
    var fmPage = function (kind) { return newPage('fm ' + kind, false); };

    c = fmPage('center half-title');
    c.body.appendChild(el('div', 'fm-half-title', book.title));
    blankPage();

    c = fmPage('center title-page');
    c.body.appendChild(el('div', 'fm-title', book.title));
    if (book.subtitle) c.body.appendChild(el('div', 'fm-subtitle', book.subtitle));
    var orn = el('div', 'fm-ornament');
    orn.appendChild(img(ICONS.ramo));
    c.body.appendChild(orn);
    if (book.author) c.body.appendChild(el('div', 'fm-author', book.author));

    c = fmPage('center copyright');
    fm.copyright.forEach(function (t, i) {
      c.body.appendChild(el('p', i === 0 ? 'fm-copy fm-copy-head' : 'fm-copy', t));
    });

    if (fm.dedication) {
      ensureRecto();
      c = fmPage('center dedication');
      c.body.appendChild(el('div', 'fm-dedication', '\u201C' + fm.dedication + '\u201D'));
    }

    if (fm.epigraph && fm.epigraph.text) {
      ensureRecto();
      c = fmPage('center epigraph');
      c.body.appendChild(el('div', 'fm-epigraph', '\u201C' + fm.epigraph.text + '\u201D'));
      if (fm.epigraph.reference) c.body.appendChild(el('div', 'fm-epigraph-ref', fm.epigraph.reference));
    }

    var textPage = function () { return fmPage('text'); };
    if (fm.intro.length) {
      ensureRecto();
      c = textPage();
      c.body.appendChild(el('h2', 'fm-heading', fm.introTitle));
      fm.intro.forEach(function (t) { c = placeText(c, t, { cls: 'fm-para' }, textPage); });
    }

    if (fm.guidance.length) {
      c = textPage();
      c.body.appendChild(el('h2', 'fm-heading', fm.guidanceTitle));
      if (fm.guidanceIntro) c = placeText(c, fm.guidanceIntro, { cls: 'fm-para' }, textPage);
      fm.guidance.forEach(function (g) {
        var p = el('p', 'para fm-para fm-guidance');
        p.appendChild(document.createTextNode('\u2022 '));
        if (g.title) p.appendChild(el('strong', null, g.title + ': '));
        p.appendChild(document.createTextNode(g.text));
        c = placeBlock(c, p, textPage);
      });
    }

    ensureRecto();
    var tocPage = function () { return fmPage('toc'); };
    c = tocPage();
    c.body.appendChild(el('h2', 'toc-heading', L.contents));
    book.days.forEach(function (d) {
      var row = el('div', 'toc-item');
      var left = el('span', 'toc-left');
      left.appendChild(el('span', 'toc-day', L.day + ' ' + d.day + ':'));
      left.appendChild(el('span', 'toc-title', d.title));
      var num = el('span', 'toc-page', '000');
      row.appendChild(left);
      row.appendChild(num);
      c = placeBlock(c, row, tocPage);
      state.tocRefs.push(num);
    });

    ensureRecto();
    c = fmPage('center divider');
    var dv = el('div', 'fm-divider');
    var dvo = el('div', 'fm-divider-ornament');
    dvo.appendChild(img(ICONS.ramo));
    dv.appendChild(dvo);
    dv.appendChild(el('div', 'fm-divider-label', fm.journeyLabel));
    dv.appendChild(el('div', 'fm-divider-title', book.title));
    c.body.appendChild(dv);
    blankPage();
  }

  // ---------- dias ----------

  function openingBlock(day) {
    var w = el('div', 'day-open');
    var bw = el('div', 'day-badge-wrap');
    bw.appendChild(el('span', 'day-badge', L.day + ' ' + day.day));
    w.appendChild(bw);
    w.appendChild(el('h1', 'day-title', day.title));
    var orn = el('div', 'ornament');
    orn.appendChild(img(ICONS.ramo));
    w.appendChild(orn);
    if (day.verse && (day.verse.text || day.verse.reference)) {
      var sc = el('div', 'scripture');
      if (day.verse.text) sc.appendChild(el('div', 'scripture-text', '\u201C' + day.verse.text + '\u201D'));
      if (day.verse.reference) sc.appendChild(el('div', 'scripture-ref', day.verse.reference));
      w.appendChild(sc);
    }
    return w;
  }

  function dayCards(day) {
    return [['heart', ICONS.ramo, day.heart], ['prayer', ICONS.maos, day.prayer]].filter(function (c) {
      return c[2] && c[2].text;
    });
  }

  // o: { cont, split, flow }. Continuações (cont) não repetem ícone nem título.
  function makeCard(c, words, o) {
    var card = el('div', 'card card-' + c[0] + (o.flow ? ' flow' : '') + (o.cont ? ' cont' : ''));
    if (!o.cont) {
      var ic = el('div', 'card-icon');
      ic.appendChild(img(c[1]));
      card.appendChild(ic);
    }
    var tx = el('div', 'card-body');
    if (!o.cont) tx.appendChild(el('div', 'card-title', c[2].title));
    tx.appendChild(el('div', 'card-text' + (o.split ? ' split' : ''), words.join(' ')));
    card.appendChild(tx);
    return card;
  }

  function cardsBlock(day) {
    var list = dayCards(day);
    if (!list.length) return null;
    var w = el('div', 'cards');
    list.forEach(function (c) { w.appendChild(makeCard(c, c[2].text.split(/\s+/), {})); });
    return w;
  }

  // Card em fluxo contínuo: entra logo após o conteúdo anterior e, se não
  // couber, quebra o texto com as mesmas regras de viúvas e órfãs.
  function placeCard(cur, c, nextPage) {
    var words = c[2].text.split(/\s+/).filter(Boolean);
    var cont = false;
    var guard = 0;
    var textOf = function (e) { return e.querySelector('.card-text'); };
    while (words.length && guard++ < 50) {
      var full = makeCard(c, words, { flow: true, cont: cont });
      cur.body.appendChild(full);
      if (!overflows(cur.body)) return cur;
      var lh = lineHeightOf(textOf(full));
      var fullLines = linesOf(textOf(full), lh);
      cur.body.removeChild(full);

      var o = { flow: true, cont: cont, split: true };
      var build = function (k) { return makeCard(c, words.slice(0, k), o); };
      var k = 0;
      if (fullLines >= MIN_LINES * 2) {
        k = maxFitBy(cur.body, words.length, build, 0, lh, textOf);
        if (k > 0) {
          var probe = build(k);
          cur.body.appendChild(probe);
          var l1 = linesOf(textOf(probe), lh);
          cur.body.removeChild(probe);
          if (l1 < MIN_LINES) k = 0;
          else if (fullLines - l1 < MIN_LINES) k = maxFitBy(cur.body, words.length, build, fullLines - MIN_LINES, lh, textOf);
        }
      }
      if (k > 0) {
        cur.body.appendChild(build(k));
        words = words.slice(k);
        cont = true;
      } else if (!cur.body.children.length) {
        cur.body.appendChild(full);
        return cur;
      }
      cur = nextPage();
    }
    return cur;
  }

  function renderDay(day) {
    if (S.openingRule === 'recto') ensureRecto();
    var pages = [];
    var open = function () {
      var c = newPage('day', true);
      pages.push(c);
      return c;
    };
    var cur = open();
    cur.body.appendChild(openingBlock(day));
    day.paragraphs.forEach(function (t, i) {
      cur = placeText(cur, t, { dropcap: i === 0 }, open);
    });

    // Cards inteiros cabem: ficam no pé da última página. Senão seguem o
    // fluxo do texto, para nunca deixar espaço vazio no pé de uma página.
    var cardsStartNewPage = false;
    var block = cardsBlock(day);
    if (block) {
      cur.body.appendChild(block);
      if (overflows(cur.body)) {
        cur.body.removeChild(block);
        var before = cur.n;
        dayCards(day).forEach(function (c) { cur = placeCard(cur, c, open); });
        var firstCard = root.querySelector('.page[data-page="' + before + '"] .card');
        cardsStartNewPage = !firstCard;
      }
    }

    var first = pages[0], last = pages[pages.length - 1];
    state.days.push({ day: day.day, title: day.title, start: first.n, end: last.n, pages: pages.length, cardsAlone: cardsStartNewPage });
  }

  // ---------- montagem ----------

  function layout(p) {
    root.innerHTML = '';
    setVars(p);
    state = { pageNo: 0, tocRefs: [], days: [], warnings: [] };
    if (S.includeFrontMatter) renderFrontMatter();
    var fmPages = state.pageNo;
    book.days.forEach(renderDay);
    state.tocRefs.forEach(function (n, i) { n.textContent = String(state.days[i].start); });
    var trailingBlank = false;
    if (state.pageNo % 2 === 1) { blankPage(); trailingBlank = true; }

    var maxDay = 0, overflow = [];
    state.days.forEach(function (d) {
      if (d.pages > maxDay) maxDay = d.pages;
      if (d.pages > S.targetPagesPerDay) overflow.push(d.day);
    });
    return {
      totalPages: state.pageNo,
      frontMatterPages: fmPages,
      trailingBlank: trailingBlank,
      fontSizePt: p.fs,
      lineHeight: p.lh,
      margins: { inside: p.inside, outside: p.outside, top: p.top, bottom: p.bottom },
      days: state.days,
      maxDayPages: maxDay,
      overflowDays: overflow,
      warnings: state.warnings
    };
  }

  function candidates() {
    var list = [];
    var fsSteps = S.autoFit ? [0, 0.3, 0.6] : [0];
    var lhSteps = S.autoFit ? [0, 0.06, 0.12, 0.18, 0.24] : [0];
    fsSteps.forEach(function (fd) {
      lhSteps.forEach(function (ld) {
        var fs = Math.round((S.fontSizePt - fd) * 100) / 100;
        var lh = Math.round((S.lineHeight - ld) * 100) / 100;
        if (fs >= 9 && lh >= 1.25) list.push({ fs: fs, lh: lh });
      });
    });
    return list.length ? list : [{ fs: S.fontSizePt, lh: S.lineHeight }];
  }

  function run() {
    var t0 = performance.now();
    var minOut = S.bleed ? MIN_OUT.bleed : MIN_OUT.noBleed;
    var base = {
      inside: Math.max(S.marginInside, minGutter(24)),
      outside: Math.max(S.marginOutside, minOut),
      top: Math.max(S.marginTop, minOut),
      bottom: Math.max(S.marginBottom, minOut)
    };
    var passes = 0;
    var best = null, params = null, rep = null;
    var list = candidates();
    for (var i = 0; i < list.length; i++) {
      var p = Object.assign({}, base, list[i]);
      rep = layout(p);
      passes++;
      if (!best || rep.overflowDays.length < best.overflowDays.length) { best = rep; params = p; }
      if (!rep.overflowDays.length) break;
    }

    if (rep !== best) { rep = layout(params); passes++; }

    // Convergência da calha: a margem interna mínima depende do total de páginas.
    for (var g = 0; g < 4; g++) {
      var req = minGutter(rep.totalPages);
      if (req <= params.inside + 1e-9) break;
      params = Object.assign({}, params, { inside: req });
      rep = layout(params);
      passes++;
    }

    rep.layoutPasses = passes;
    rep.elapsedMs = Math.round(performance.now() - t0);
    if (rep.overflowDays.length) {
      rep.warnings.push(rep.overflowDays.length + ' dia(s) passaram de ' + S.targetPagesPerDay + ' páginas: ' + rep.overflowDays.join(', ') + '.');
    }
    return rep;
  }

  function publish(rep) {
    window.__BOOK_REPORT__ = rep;
    docEl.setAttribute('data-ready', '1');
    if (window.parent && window.parent !== window) window.parent.postMessage({ type: 'book-report', report: rep }, '*');
  }

  function fail(err) {
    var msg = (err && err.stack) || String(err);
    window.__BOOK_ERROR__ = msg;
    if (window.parent && window.parent !== window) window.parent.postMessage({ type: 'book-error', error: msg }, '*');
  }

  window.addEventListener('message', function (ev) {
    var d = ev.data || {};
    var target = null;
    if (d.type === 'goto-day') target = root.querySelector('.page[data-page="' + d.page + '"]');
    if (d.type === 'goto-page') target = root.querySelector('.page[data-page="' + d.page + '"]');
    if (target) target.scrollIntoView({ block: 'start' });
  });

  var fontLoads = [];
  document.fonts.forEach(function (f) { fontLoads.push(f.load().catch(function () {})); });
  Promise.all(fontLoads)
    .then(function () { return document.fonts.ready; })
    .then(function () {
      var rep = run();
      var imgs = Array.prototype.slice.call(document.images);
      return Promise.all(imgs.map(function (i) { return i.decode ? i.decode().catch(function () {}) : null; }))
        .then(function () { publish(rep); });
    })
    .catch(fail);
})();
`;
