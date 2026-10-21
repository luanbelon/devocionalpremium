"use client";

import JSZip from "jszip";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SAMPLE_FILES } from "@/generated/assets";
import { buildBookHtml } from "@/lib/book-html";
import { buildEpub, epubFileName } from "@/lib/epub";
import { fontFaceCss } from "@/lib/fonts";
import { KDP_RULES_VERSION, pageGeometry, TRIM_SIZES } from "@/lib/kdp";
import { normalizeBookJson, type NormalizeResult } from "@/lib/normalize";
import { editionSummary, type EditionSummary } from "@/lib/report";
import { DEFAULT_SETTINGS, sanitizeSettings, type Settings } from "@/lib/settings";
import type { Book, BookReport, Theme } from "@/lib/types";

const STORAGE_KEY = "devocional-premium:v3";
const LEGACY_STORAGE_KEYS = ["devocional-premium:v2", "devocional-premium:v1"];
const ZOOMS = [
  { value: 0, label: "Ajustar à largura" },
  { value: 0.5, label: "50%" },
  { value: 0.75, label: "75%" },
  { value: 1, label: "100%" },
  { value: 1.25, label: "125%" },
];

type ExportKey = "color" | "bw" | "epub" | "zip";
type Overrides = Partial<Record<"title" | "subtitle" | "author", string>>;

function download(data: Blob, name: string) {
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

async function requestPdf(book: Book, settings: Settings, theme: Theme): Promise<Blob> {
  const res = await fetch("/api/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ book, settings, theme }),
  });
  if (!res.ok) {
    const info = await res.json().catch(() => null);
    const details = info?.details?.length ? ` (${info.details.join("; ")})` : "";
    throw new Error(`${info?.error ?? `Erro ${res.status} ao gerar o PDF`}${details}`);
  }
  return res.blob();
}

function parseSource(rawText: string, overrides: Overrides, year: string): NormalizeResult | null {
  if (!rawText.trim()) return null;
  let obj: unknown;
  try {
    obj = JSON.parse(rawText);
  } catch (e) {
    return { book: null, errors: [`JSON inválido: ${(e as Error).message}`], warnings: [], settings: {} };
  }
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    const patch: Record<string, string> = {};
    for (const [k, v] of Object.entries(overrides)) if (v) patch[k] = v;
    obj = { ...(obj as object), ...patch };
  }
  return normalizeBookJson(obj, { year });
}

const inches = (v: number) => `${v.toFixed(3)}″ (${(v * 25.4).toFixed(1)} mm)`;

function NumberField(props: {
  label: string;
  value: number;
  step: number;
  min?: number;
  max?: number;
  suffix?: string;
  onChange: (v: number) => void;
}) {
  const [text, setText] = useState(String(props.value));
  useEffect(() => setText(String(props.value)), [props.value]);
  const commit = () => {
    const n = Number(text.replace(",", "."));
    if (Number.isFinite(n)) props.onChange(n);
    else setText(String(props.value));
  };
  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="field-input">
        <input
          type="number"
          inputMode="decimal"
          step={props.step}
          min={props.min}
          max={props.max}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === "Enter" && commit()}
        />
        {props.suffix && <em>{props.suffix}</em>}
      </div>
    </label>
  );
}

function EditionCard({ title, summary }: { title: string; summary: EditionSummary }) {
  const { validation, cover } = summary;
  return (
    <div className={`edition ${validation.ok ? "ok" : "bad"}`}>
      <div className="edition-head">
        <strong>{title}</strong>
        <span className="pill">{validation.ok ? "Dentro das regras KDP" : "Fora das regras KDP"}</span>
      </div>
      <dl>
        <dt>Tinta / papel</dt>
        <dd>
          {summary.ink.replace(/_/g, " ")} · {summary.paper === "cream" ? "creme" : "branco"}
        </dd>
        <dt>Lombada</dt>
        <dd>{inches(cover.spineWidth)}</dd>
        <dt>Capa aberta</dt>
        <dd>
          {cover.totalWidth.toFixed(3)}″ × {cover.totalHeight.toFixed(3)}″
        </dd>
      </dl>
      {[...validation.errors, ...validation.warnings].map((m) => (
        <p key={m} className="note">
          {m}
        </p>
      ))}
    </div>
  );
}

export default function Studio() {
  const [rawText, setRawText] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [overrides, setOverrides] = useState<Overrides>({});
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [theme, setTheme] = useState<Theme>("color");
  const [report, setReport] = useState<BookReport | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [busy, setBusy] = useState<Partial<Record<ExportKey, boolean>>>({});
  const [exportError, setExportError] = useState<string | null>(null);
  const [pasteOpen, setPasteOpen] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [dragging, setDragging] = useState(false);
  const [origin, setOrigin] = useState("");
  const [zoom, setZoom] = useState(0);
  const [frameWidth, setFrameWidth] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const frameWrapRef = useRef<HTMLDivElement>(null);
  const restored = useRef(false);

  useEffect(() => {
    const el = frameWrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setFrameWidth(entry.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, [origin]);

  useEffect(() => {
    setOrigin(window.location.origin);
    try {
      const current = localStorage.getItem(STORAGE_KEY);
      const legacy = LEGACY_STORAGE_KEYS.map((k) => localStorage.getItem(k)).find(Boolean);
      const saved = JSON.parse(current ?? legacy ?? "null");
      // Versões anteriores gravaram o ramo em 18.2px; assume o padrão atual.
      if (saved && !current && saved.settings) delete saved.settings.ornamentPx;
      LEGACY_STORAGE_KEYS.forEach((k) => localStorage.removeItem(k));
      if (saved) {
        setRawText(saved.rawText ?? "");
        setSourceName(saved.sourceName ?? "");
        setOverrides(saved.overrides ?? {});
        setSettings(sanitizeSettings(saved.settings));
      }
    } catch {
      // Estado salvo corrompido: começa do zero.
    }
    restored.current = true;
  }, []);

  useEffect(() => {
    if (!restored.current) return;
    const t = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ rawText, sourceName, overrides, settings }));
      } catch {
        // Sem espaço no localStorage: apenas não persiste.
      }
    }, 400);
    return () => clearTimeout(t);
  }, [rawText, sourceName, overrides, settings]);

  const parsed = useMemo(() => parseSource(rawText, overrides, settings.year), [rawText, overrides, settings.year]);
  const book = parsed?.book ?? null;

  const loadJson = useCallback((text: string, name: string) => {
    setRawText(text);
    setSourceName(name);
    setOverrides({});
    setReport(null);
    const result = normalizeBookJson(text, { year: DEFAULT_SETTINGS.year });
    if (Object.keys(result.settings).length) setSettings((s) => sanitizeSettings(result.settings, s));
  }, []);

  const loadFile = useCallback(
    async (file: File) => {
      loadJson(await file.text(), file.name);
    },
    [loadJson]
  );

  const loadSample = async (file: string) => {
    const res = await fetch(`/samples/${file}`);
    loadJson(await res.text(), file);
  };

  const update = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    setSettings((s) => sanitizeSettings({ ...s, [key]: value }));

  // Preview: o mesmo HTML e paginador usados no PDF, renderizados num iframe.
  const fontCss = useMemo(() => (origin ? fontFaceCss((f) => `${origin}/fonts/${f}`) : ""), [origin]);
  const [debounced, setDebounced] = useState({ book, settings, theme });
  useEffect(() => {
    const t = setTimeout(() => setDebounced({ book, settings, theme }), 350);
    return () => clearTimeout(t);
  }, [book, settings, theme]);

  const previewHtml = useMemo(
    () =>
      debounced.book && fontCss
        ? buildBookHtml(debounced.book, debounced.settings, { theme: debounced.theme, mode: "preview", fontCss })
        : "",
    [debounced, fontCss]
  );

  useEffect(() => {
    if (!previewHtml) return;
    setRendering(true);
    setPreviewError(null);
  }, [previewHtml]);

  useEffect(() => {
    const onMessage = (ev: MessageEvent) => {
      if (ev.source !== iframeRef.current?.contentWindow) return;
      if (ev.data?.type === "book-report") {
        setReport(ev.data.report as BookReport);
        setRendering(false);
      } else if (ev.data?.type === "book-error") {
        setPreviewError(String(ev.data.error));
        setRendering(false);
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  const gotoPage = (page: number) => iframeRef.current?.contentWindow?.postMessage({ type: "goto-page", page }, "*");

  const run = async (key: ExportKey, task: () => Promise<void>) => {
    setBusy((b) => ({ ...b, [key]: true }));
    setExportError(null);
    try {
      await task();
    } catch (e) {
      setExportError((e as Error).message);
    } finally {
      setBusy((b) => ({ ...b, [key]: false }));
    }
  };

  const exportPdf = (t: Theme) =>
    run(t, async () => {
      if (!book) return;
      const blob = await requestPdf(book, settings, t);
      download(blob, `${book.bookId}_interior_${t === "color" ? "colorido" : "preto-e-branco"}.pdf`);
    });

  const exportEpub = () =>
    run("epub", async () => {
      if (!book) return;
      const bytes = await buildEpub(book);
      download(new Blob([bytes as BlobPart], { type: "application/epub+zip" }), epubFileName(book));
    });

  const exportAll = () =>
    run("zip", async () => {
      if (!book) return;
      const [color, bw, epub] = await Promise.all([
        requestPdf(book, settings, "color"),
        requestPdf(book, settings, "bw"),
        buildEpub(book),
      ]);
      const zip = new JSZip();
      zip.file(`${book.bookId}_interior_colorido.pdf`, color);
      zip.file(`${book.bookId}_interior_preto-e-branco.pdf`, bw);
      zip.file(epubFileName(book), epub);
      if (report) {
        zip.file(
          "relatorio-kdp.json",
          JSON.stringify(
            {
              livro: { titulo: book.title, subtitulo: book.subtitle, autor: book.author, idioma: book.language, dias: book.days.length },
              regrasKdp: KDP_RULES_VERSION,
              configuracao: settings,
              avisosDoJson: parsed?.warnings ?? [],
              diagramacao: report,
              edicoes: {
                colorida: editionSummary("color", report, settings),
                pretoEBranco: editionSummary("bw", report, settings),
              },
            },
            null,
            2
          )
        );
      }
      download(await zip.generateAsync({ type: "blob" }), `${book.bookId}.zip`);
    });

  const anyBusy = Object.values(busy).some(Boolean);
  const fitAdjusted =
    report && (report.fontSizePt !== settings.fontSizePt || report.lineHeight !== settings.lineHeight);
  const trims = TRIM_SIZES[settings.editionType];
  const pageWidthPx = pageGeometry(settings.trimSize, settings.editionType, settings.bleed).pageWidth * 96;
  // 32px de respiro do preview + 16px da barra de rolagem do iframe.
  const fitScale = frameWidth ? Math.min(1.5, Math.max(0.3, frameWidth / (pageWidthPx + 48))) : 1;
  const scale = zoom || fitScale;

  // Ferramenta 100% cliente (localStorage, iframe): evita divergência de hidratação.
  if (!origin) return <div className="studio" />;

  return (
    <div className="studio">
      <aside className="sidebar">
          <header className="brand">
            <span className="brand-mark" aria-hidden>
              ❦
            </span>
            <div>
              <h1>Devocional Premium</h1>
              <p>Miolo colorido, miolo P&amp;B e EPUB a partir de um JSON</p>
            </div>
          </header>

          <section className="panel">
            <h2>Exportar</h2>
            <button className="btn primary block" disabled={!book || anyBusy} onClick={exportAll}>
              {busy.zip ? "Gerando pacote…" : "Exportar tudo (.zip)"}
            </button>
            <div className="export-grid">
              <button className="btn" disabled={!book || anyBusy} onClick={() => exportPdf("color")}>
                {busy.color ? "Gerando…" : "PDF colorido"}
              </button>
              <button className="btn" disabled={!book || anyBusy} onClick={() => exportPdf("bw")}>
                {busy.bw ? "Gerando…" : "PDF P&B"}
              </button>
              <button className="btn" disabled={!book || anyBusy} onClick={exportEpub}>
                {busy.epub ? "Gerando…" : "EPUB"}
              </button>
            </div>
            {exportError && (
              <div className="messages error">
                <strong>Falha na exportação:</strong> {exportError}{" "}
                <button className="link" onClick={() => setExportError(null)}>
                  fechar
                </button>
              </div>
            )}
          </section>

          <section className="panel">
            <h2>1. Conteúdo (JSON)</h2>
            <div
              className={`dropzone ${dragging ? "over" : ""}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                const f = e.dataTransfer.files?.[0];
                if (f) loadFile(f);
              }}
            >
              <p>
                <strong>Arraste o JSON aqui</strong> ou
              </p>
              <label className="btn small">
                Escolher arquivo
                <input
                  type="file"
                  accept="application/json,.json"
                  hidden
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) loadFile(f);
                    e.target.value = "";
                  }}
                />
              </label>
              <button className="btn small ghost" onClick={() => setPasteOpen((v) => !v)}>
                Colar JSON
              </button>
            </div>
            {pasteOpen && (
              <div className="paste">
                <textarea
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  placeholder='{ "titulo": "...", "dias": [ ... ] }'
                  rows={8}
                />
                <button
                  className="btn small primary"
                  disabled={!pasteText.trim()}
                  onClick={() => {
                    loadJson(pasteText, "JSON colado");
                    setPasteOpen(false);
                  }}
                >
                  Usar este JSON
                </button>
              </div>
            )}
            <div className="samples">
              <span>Exemplos:</span>
              {SAMPLE_FILES.map((f) => (
                <button key={f} className="link" onClick={() => loadSample(f)}>
                  {f.replace(/\.json$/, "")}
                </button>
              ))}
            </div>
            {sourceName && (
              <p className="source">
                Carregado: <strong>{sourceName}</strong>
                {book && ` · ${book.days.length} dias · ${book.language === "pt" ? "português" : "inglês"}`}
              </p>
            )}
            {parsed?.errors.length ? (
              <ul className="messages error">
                {parsed.errors.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            ) : null}
            {parsed?.warnings.length ? (
              <details className="messages warn">
                <summary>{parsed.warnings.length} aviso(s) no JSON</summary>
                <ul>
                  {parsed.warnings.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </details>
            ) : null}
          </section>

          {book && (
            <section className="panel">
              <h2>2. Dados do livro</h2>
              {(["title", "subtitle", "author"] as const).map((k) => (
                <label className="field" key={k}>
                  <span>{{ title: "Título", subtitle: "Subtítulo", author: "Autor" }[k]}</span>
                  <input
                    value={overrides[k] ?? book[k]}
                    onChange={(e) => setOverrides((o) => ({ ...o, [k]: e.target.value }))}
                  />
                </label>
              ))}
              <NumberField label="Ano do copyright" value={Number(settings.year)} step={1} onChange={(v) => update("year", String(Math.round(v)))} />
            </section>
          )}

          <section className="panel">
            <h2>3. Formato KDP</h2>
            <div className="grid2">
              <label className="field">
                <span>Encadernação</span>
                <select value={settings.editionType} onChange={(e) => update("editionType", e.target.value as Settings["editionType"])}>
                  <option value="paperback">Brochura (paperback)</option>
                  <option value="hardcover">Capa dura (hardcover)</option>
                </select>
              </label>
              <label className="field">
                <span>Formato</span>
                <select value={settings.trimSize} onChange={(e) => update("trimSize", e.target.value)}>
                  {trims.map((t) => (
                    <option key={t.code} value={t.code}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Tinta (colorido)</span>
                <select value={settings.colorInk} onChange={(e) => update("colorInk", e.target.value as Settings["colorInk"])}>
                  <option value="premium_color">Premium color</option>
                  <option value="standard_color">Standard color</option>
                </select>
              </label>
              <label className="field">
                <span>Papel (P&amp;B)</span>
                <select value={settings.bwPaper} onChange={(e) => update("bwPaper", e.target.value as Settings["bwPaper"])}>
                  <option value="cream">Creme</option>
                  <option value="white">Branco</option>
                </select>
              </label>
              <label className="field">
                <span>Abertura de cada dia</span>
                <select value={settings.openingRule} onChange={(e) => update("openingRule", e.target.value as Settings["openingRule"])}>
                  <option value="new_page">Próxima página</option>
                  <option value="recto">Sempre página ímpar</option>
                </select>
              </label>
              <label className="check">
                <input type="checkbox" checked={settings.bleed} onChange={(e) => update("bleed", e.target.checked)} />
                Sangria (bleed)
              </label>
            </div>
            <h3>Margens (polegadas)</h3>
            <div className="grid2">
              <NumberField label="Interna (calha)" value={settings.marginInside} step={0.025} onChange={(v) => update("marginInside", v)} />
              <NumberField label="Externa" value={settings.marginOutside} step={0.025} onChange={(v) => update("marginOutside", v)} />
              <NumberField label="Superior" value={settings.marginTop} step={0.025} onChange={(v) => update("marginTop", v)} />
              <NumberField label="Inferior" value={settings.marginBottom} step={0.025} onChange={(v) => update("marginBottom", v)} />
            </div>
          </section>

          <section className="panel">
            <h2>4. Tipografia</h2>
            <div className="grid2">
              <NumberField label="Corpo do texto" value={settings.fontSizePt} step={0.1} suffix="pt" onChange={(v) => update("fontSizePt", v)} />
              <NumberField label="Entrelinha" value={settings.lineHeight} step={0.02} onChange={(v) => update("lineHeight", v)} />
              <NumberField label="Ramo sob o título" value={settings.ornamentPx} step={0.1} suffix="px" onChange={(v) => update("ornamentPx", v)} />
              <NumberField label="Meta de páginas/dia" value={settings.targetPagesPerDay} step={1} onChange={(v) => update("targetPagesPerDay", v)} />
            </div>
            <label className="check">
              <input type="checkbox" checked={settings.autoFit} onChange={(e) => update("autoFit", e.target.checked)} />
              Ajustar entrelinha/corpo automaticamente para caber na meta
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={settings.includeFrontMatter}
                onChange={(e) => update("includeFrontMatter", e.target.checked)}
              />
              Incluir pré-textuais (rosto, copyright, dedicatória, introdução, sumário)
            </label>
            <button className="link" onClick={() => setSettings((s) => ({ ...DEFAULT_SETTINGS, year: s.year }))}>
              Restaurar padrões
            </button>
          </section>

          {report && book && (
            <section className="panel">
              <h2>5. Resultado</h2>
              <div className="stats">
                <div>
                  <b>{report.totalPages}</b>
                  <span>páginas</span>
                </div>
                <div>
                  <b>{report.frontMatterPages}</b>
                  <span>pré-textuais</span>
                </div>
                <div>
                  <b>{report.maxDayPages}</b>
                  <span>máx. pág./dia</span>
                </div>
                <div>
                  <b>
                    {report.fontSizePt}pt / {report.lineHeight}
                  </b>
                  <span>{fitAdjusted ? "ajustado auto." : "corpo / entrelinha"}</span>
                </div>
                <div>
                  <b>{report.margins.inside.toFixed(3)}″</b>
                  <span>calha aplicada</span>
                </div>
              </div>
              {(report.warnings.length > 0 || report.days.some((d) => d.cardsAlone)) && (
                <ul className="messages warn">
                  {report.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                  {report.days
                    .filter((d) => d.cardsAlone)
                    .map((d) => (
                      <li key={`alone-${d.day}`}>
                        Dia {d.day}: os cards não couberam e foram para uma página só deles (p. {d.end}).{" "}
                        <button className="link" onClick={() => gotoPage(d.end)}>
                          ver
                        </button>
                      </li>
                    ))}
                </ul>
              )}
              <div className="editions">
                <EditionCard title="Edição colorida" summary={editionSummary("color", report, settings)} />
                <EditionCard title="Edição preto e branco" summary={editionSummary("bw", report, settings)} />
              </div>
            </section>
          )}
      </aside>

      <main className="viewer">
          <div className="preview-bar">
            <div className="tabs" role="tablist">
              {(["color", "bw"] as const).map((t) => (
                <button key={t} role="tab" aria-selected={theme === t} className={theme === t ? "active" : ""} onClick={() => setTheme(t)}>
                  {t === "color" ? "Colorida" : "Preto e branco"}
                </button>
              ))}
            </div>
            {report && book && (
              <select
                className="goto"
                defaultValue=""
                onChange={(e) => {
                  if (e.target.value) gotoPage(Number(e.target.value));
                  e.target.value = "";
                }}
              >
                <option value="">Ir para…</option>
                <option value="1">Início</option>
                {report.days.map((d) => (
                  <option key={d.day} value={d.start}>
                    Dia {d.day} · p. {d.start} ({d.pages} pág.)
                  </option>
                ))}
              </select>
            )}
            <select className="goto" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} aria-label="Zoom">
              {ZOOMS.map((z) => (
                <option key={z.value} value={z.value}>
                  {z.value === 0 ? `${z.label} (${Math.round(fitScale * 100)}%)` : z.label}
                </option>
              ))}
            </select>
            <span className="status">
              {rendering ? "Diagramando…" : report ? `${report.totalPages} páginas · ${report.elapsedMs} ms` : ""}
            </span>
          </div>

          {previewError && <div className="banner error">Erro na diagramação: {previewError}</div>}

          <div className="frame-wrap" ref={frameWrapRef}>
            {previewHtml ? (
              <iframe
                ref={iframeRef}
                title="Preview do livro"
                srcDoc={previewHtml}
                style={{
                  width: `${100 / scale}%`,
                  height: `${100 / scale}%`,
                  transform: `scale(${scale})`,
                  transformOrigin: "0 0",
                }}
              />
            ) : (
              <div className="empty">
                <p>Carregue um JSON de devocional para ver as páginas diagramadas.</p>
                <p className="muted">
                  Aceita o manuscrito (<code>titulo</code>, <code>dias[].reflexao</code>, <code>oracao</code>…) ou o formato
                  estruturado (<code>book_title</code>, <code>days[].page1</code>…).
                </p>
              </div>
            )}
          </div>
      </main>
    </div>
  );
}
