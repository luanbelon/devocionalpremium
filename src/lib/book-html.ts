import { GUTTER_TIERS, MIN_OUTSIDE_MARGIN, pageGeometry } from "./kdp";
import { LABELS } from "./i18n";
import { PAGINATOR_JS } from "./paginator";
import type { Settings } from "./settings";
import { themeDef } from "./themes";
import type { Book, Theme } from "./types";

export interface BuildHtmlOptions {
  theme: Theme;
  mode: "print" | "preview";
  fontCss: string;
}

const BOOK_CSS = `
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #FFFFFF; }
body {
  font-family: 'EB Garamond', Garamond, Georgia, serif;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  font-kerning: normal;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
#book { width: var(--page-w); }

.page {
  width: var(--page-w);
  height: var(--page-h);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  padding-top: var(--pad-top);
  padding-bottom: var(--pad-bottom);
  break-after: page;
  page-break-after: always;
  contain: strict;
}
.page:last-child { break-after: auto; page-break-after: auto; }
.page.recto { padding-left: var(--pad-inside); padding-right: var(--pad-outside); }
.page.verso { padding-left: var(--pad-outside); padding-right: var(--pad-inside); }

.page-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.page-body > * { flex: none; }

/* CabeÃ§alho corrido e rodapÃ© */
.running-header { flex: none; text-align: center; margin-bottom: 22px; }
.rh-text {
  font-family: 'Cinzel', serif;
  font-size: 7.5pt;
  font-weight: 500;
  letter-spacing: 0.28em;
  padding-left: 0.28em;
  color: var(--header-text);
  text-transform: uppercase;
  padding-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rh-line { height: 0.5pt; background: var(--header-line); }
.page-footer {
  position: absolute;
  bottom: var(--footer-bottom);
  text-align: center;
  font-family: 'EB Garamond', serif;
  font-size: 10pt;
  color: var(--footer);
}
.page.recto .page-footer { left: var(--pad-inside); right: var(--pad-outside); }
.page.verso .page-footer { left: var(--pad-outside); right: var(--pad-inside); }

/* Abertura do dia */
.day-badge-wrap { text-align: center; margin: 2px 0 10px; }
.day-badge {
  display: inline-block;
  padding: 3px 20px 2px calc(20px + 0.2em);
  border: 0.85pt solid var(--badge-border);
  border-radius: 9px;
  background: var(--badge-bg);
  font-family: 'Cinzel', serif;
  font-size: 8.5pt;
  font-weight: 600;
  letter-spacing: 0.2em;
  color: var(--badge-text);
  text-transform: uppercase;
}
.day-title {
  text-align: center;
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 25pt;
  font-weight: 600;
  line-height: 1.15;
  color: var(--ink-strong);
  margin-bottom: 11px;
  letter-spacing: -0.01em;
}
.ornament { text-align: center; margin-bottom: 16px; line-height: 0; }
.ornament img { width: var(--ornament); height: auto; aspect-ratio: 512 / 300; display: inline-block; }

.scripture {
  background: var(--card-bg);
  border: 0.5pt solid var(--card-border);
  border-radius: 8px;
  padding: 15px 22px 13px;
  margin-bottom: 20px;
  text-align: center;
}
.scripture-text {
  font-family: 'EB Garamond', serif;
  font-style: italic;
  font-size: 11.5pt;
  line-height: 1.48;
  color: var(--ink-strong);
  margin-bottom: 7px;
}
.scripture-ref {
  font-family: 'Cinzel', serif;
  font-size: 8pt;
  font-weight: 600;
  letter-spacing: 0.22em;
  color: var(--ref);
  text-transform: uppercase;
}

/* Corpo do texto */
.para {
  font-size: var(--fs);
  line-height: var(--lh);
  text-align: justify;
  text-justify: inter-word;
  hyphens: manual;
  color: var(--ink);
}
.para + .para { margin-top: 0.95em; }
.para.split { text-align-last: justify; }
.dropcap {
  float: left;
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 3.6em;
  line-height: 0.72;
  padding-top: 6px;
  padding-right: 9px;
  padding-bottom: 1px;
  color: var(--ink-strong);
  font-weight: 500;
}

/* Cards do fim do dia */
.cards { margin-top: auto; padding-top: 16px; display: flex; flex-direction: column; gap: 14px; }
.card.flow { margin-top: 14px; }
.para + .card.flow { margin-top: 0.95em; }
.page-body > .card.flow:first-child { margin-top: 0; }
.card {
  background: var(--card-bg);
  border: 0.5pt solid var(--card-border);
  border-radius: 8px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.card-icon { flex: none; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; }
.card-icon img { width: 26px; height: 26px; object-fit: contain; display: block; }
.card-body { flex: 1; min-width: 0; }
.card-title {
  font-family: 'Cinzel', serif;
  font-size: 8.2pt;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--card-title);
  text-transform: uppercase;
  margin-bottom: 4px;
}
.card-text {
  font-family: 'EB Garamond', serif;
  font-size: 10.6pt;
  line-height: 1.5;
  color: var(--ink);
  text-align: justify;
  text-justify: inter-word;
}

/* PrÃ©-textuais */
.fm.center .page-body { justify-content: center; align-items: center; text-align: center; }
.fm-half-title {
  font-family: 'Cinzel', serif;
  font-size: 16pt;
  letter-spacing: 0.25em;
  padding-left: 0.25em;
  color: var(--ink-strong);
  text-transform: uppercase;
  line-height: 1.5;
}
.fm-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28pt;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--ink-strong);
  text-transform: uppercase;
  line-height: 1.15;
  margin-bottom: 14px;
}
.fm-subtitle {
  font-family: 'EB Garamond', serif;
  font-style: italic;
  font-size: 12.5pt;
  line-height: 1.4;
  color: var(--header-text);
  max-width: 88%;
}
.fm-ornament { margin: 30px 0 40px; line-height: 0; }
.fm-ornament img { width: var(--ornament); height: auto; aspect-ratio: 512 / 300; }
.fm-author {
  font-family: 'Cinzel', serif;
  font-size: 11pt;
  letter-spacing: 0.22em;
  padding-left: 0.22em;
  color: var(--header-text);
  text-transform: uppercase;
}
.fm-copy {
  font-family: 'EB Garamond', serif;
  font-size: 8.8pt;
  line-height: 1.6;
  color: var(--header-text);
  max-width: 92%;
}
.fm-copy + .fm-copy { margin-top: 10px; }
.fm-copy-head { font-weight: 600; font-size: 9.5pt; color: var(--ink-strong); }
.fm-dedication, .fm-epigraph {
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 14pt;
  line-height: 1.6;
  color: var(--ink-strong);
  max-width: 80%;
}
.fm-epigraph-ref {
  font-family: 'Cinzel', serif;
  font-size: 8.5pt;
  letter-spacing: 0.15em;
  color: var(--ref);
  text-transform: uppercase;
  margin-top: 14px;
}
.fm-heading, .toc-heading {
  font-family: 'Cinzel', serif;
  font-size: 15pt;
  font-weight: 400;
  letter-spacing: 0.22em;
  padding-left: 0.22em;
  color: var(--ink-strong);
  text-align: center;
  text-transform: uppercase;
  margin: 0.25in 0 26px;
}
.para.fm-para { font-size: 10.8pt; line-height: 1.55; }
.para.fm-para + .para.fm-para { margin-top: 0.8em; }
.fm-guidance strong { font-weight: 600; color: var(--ink-strong); }

.toc-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  padding: 7px 0 6px;
  border-bottom: 0.5pt dotted var(--rule);
}
.toc-left { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.toc-day {
  font-family: 'Cinzel', serif;
  font-size: 7.6pt;
  color: var(--muted);
  text-transform: uppercase;
  white-space: nowrap;
  flex: none;
}
.toc-title { font-family: 'EB Garamond', serif; font-size: 10.2pt; color: var(--ink-strong); line-height: 1.3; }
.toc-page { font-family: 'EB Garamond', serif; font-size: 10.2pt; font-weight: 600; color: var(--ink-strong); flex: none; }

.fm-divider-ornament { line-height: 0; }
.fm-divider-ornament img { width: calc(var(--ornament) * 1.4); height: auto; aspect-ratio: 512 / 300; }
.fm-divider-label {
  font-family: 'Cinzel', serif;
  font-size: 13pt;
  letter-spacing: 0.25em;
  padding-left: 0.25em;
  color: var(--ink-strong);
  text-transform: uppercase;
  margin-top: 18px;
}
.fm-divider-title { font-family: 'EB Garamond', serif; font-style: italic; font-size: 11pt; color: var(--header-text); margin-top: 8px; }

/* Preview no navegador */
html.mode-preview, html.mode-preview body { background: #E7E1D8; }
html.mode-preview body { padding: 24px 16px 48px; }
html.mode-preview #book { margin: 0 auto; }
html.mode-preview .page { margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,.08), 0 6px 18px rgba(60,40,20,.12); }
html.mode-preview .page::after {
  content: attr(data-page);
  position: absolute; top: 6px; right: 8px;
  font: 9px/1 system-ui, sans-serif; color: #b3a89c;
}
`;

function escapeJsonForHtml(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
}

const escapeHtml = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export function buildBookHtml(book: Book, settings: Settings, opts: BuildHtmlOptions): string {
  const geo = pageGeometry(settings.trimSize, settings.editionType, settings.bleed);
  const theme = themeDef(opts.theme, settings.colorPalette);
  const labels = LABELS[book.language];

  const rootVars = {
    ...theme.vars,
    "--page-w": `${geo.pageWidth}in`,
    "--page-h": `${geo.pageHeight}in`,
    "--ornament": `${settings.ornamentPx}px`,
  };
  const varsCss = `:root{${Object.entries(rootVars)
    .map(([k, v]) => `${k}:${v};`)
    .join("")}}`;

  const data = {
    book,
    settings,
    labels,
    geometry: geo,
    icons: theme.icons,
    gutterTiers: GUTTER_TIERS,
    minOutside: MIN_OUTSIDE_MARGIN,
  };

  const htmlLang = book.language === "pt" ? "pt-BR" : "en-US";
  return `<!DOCTYPE html>
<html lang="${htmlLang}" class="mode-${opts.mode} theme-${opts.theme}">
<head>
<meta charset="utf-8">
<title>${escapeHtml(book.title)}</title>
<style>${opts.fontCss}</style>
<style>@page { size: ${geo.pageWidth}in ${geo.pageHeight}in; margin: 0; }
${varsCss}
${BOOK_CSS}</style>
</head>
<body>
<main id="book"></main>
<script type="application/json" id="book-data">${escapeJsonForHtml(data)}</script>
<script>${PAGINATOR_JS}</script>
</body>
</html>`;
}
