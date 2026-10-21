import { defaultFrontMatter, LABELS } from "./i18n";
import type { Book, Card, Day, FrontMatter, GuidanceItem, Language } from "./types";

// Aceita três formatos de JSON:
// 1. Manuscrito "raw" (titulo, subtitulo, idioma, dias[].reflexao, oracao, ...)
// 2. Formato estruturado do sistema Python (book_title, days[].page1/page2/page3, card_heart, ...)
// 3. O próprio formato interno (Book), para reenvio do cliente ao servidor.

type Obj = Record<string, unknown>;

export interface NormalizeResult {
  book: Book | null;
  errors: string[];
  warnings: string[];
  settings: Obj;
}

const isObj = (v: unknown): v is Obj => !!v && typeof v === "object" && !Array.isArray(v);

const clean = (v: unknown): string =>
  typeof v === "string" ? v.replace(/\s+/g, " ").trim() : typeof v === "number" ? String(v) : "";

const stripQuotes = (s: string): string => s.replace(/^["“”«]+|["“”»]+$/g, "").trim();

function first(obj: Obj, keys: string[]): unknown {
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null && obj[k] !== "") return obj[k];
  }
  return undefined;
}

function paragraphs(v: unknown): string[] {
  if (typeof v === "string") return v.split(/\n\s*\n/).map(clean).filter(Boolean);
  if (Array.isArray(v)) return v.flatMap((p) => (typeof p === "string" ? paragraphs(p) : [])).filter(Boolean);
  return [];
}

export function slugify(text: string): string {
  return (
    text
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/[\s_-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "devocional"
  );
}

function detectLanguage(obj: Obj): Language {
  const raw = clean(first(obj, ["idioma", "language", "lang"])).toLowerCase();
  if (raw.startsWith("pt")) return "pt";
  if (raw.startsWith("en")) return "en";
  return Array.isArray(obj.dias) ? "pt" : "en";
}

function card(v: unknown, fallbackTitle: string, extraText?: unknown, extraTitle?: unknown): Card {
  if (isObj(v)) {
    return {
      title: clean(first(v, ["title", "titulo"])) || clean(extraTitle) || fallbackTitle,
      text: clean(first(v, ["text", "texto"])),
    };
  }
  return { title: clean(extraTitle) || fallbackTitle, text: clean(v ?? extraText) };
}

function normalizeDay(raw: unknown, index: number, lang: Language, errors: string[], warnings: string[]): Day | null {
  if (!isObj(raw)) {
    errors.push(`Dia na posição ${index + 1} não é um objeto.`);
    return null;
  }
  const labels = LABELS[lang];
  const dayNumber = Number(first(raw, ["dia", "day", "numero"])) || index + 1;
  const title = clean(first(raw, ["titulo", "title"]));

  const verseObj = first(raw, ["verse", "versiculo"]);
  const verse = isObj(verseObj)
    ? {
        text: stripQuotes(clean(first(verseObj, ["text", "texto"]))),
        reference: clean(first(verseObj, ["reference", "referencia"])),
      }
    : {
        text: stripQuotes(clean(first(raw, ["parafrase_biblica", "versiculo_texto", "texto_biblico"]) ?? verseObj)),
        reference: clean(first(raw, ["referencia_biblica", "referencia", "reference"])),
      };

  let paras = paragraphs(first(raw, ["paragraphs", "reflexao", "paragrafos", "reflection"]));
  if (!paras.length) {
    paras = [...paragraphs(raw.page1), ...paragraphs(raw.page2), ...paragraphs(raw.page3)];
  }

  const heart = card(
    first(raw, ["heart", "card_heart"]),
    labels.heart,
    first(raw, ["para_guardar_no_coracao", "guardar_no_coracao", "to_keep_in_your_heart"]),
    raw.titulo_guardar
  );
  const prayer = card(first(raw, ["prayer", "card_prayer"]), labels.prayer, first(raw, ["oracao", "oração"]), raw.titulo_oracao);

  const where = `Dia ${dayNumber}`;
  if (!title) errors.push(`${where}: título ausente.`);
  if (!paras.length) errors.push(`${where}: nenhum parágrafo de reflexão.`);
  if (!verse.text && !verse.reference) warnings.push(`${where}: sem versículo/referência.`);
  if (!heart.text) warnings.push(`${where}: sem texto de "${heart.title}".`);
  if (!prayer.text) warnings.push(`${where}: sem oração.`);

  return { day: dayNumber, title, verse, paragraphs: paras, heart, prayer };
}

function guidanceItems(v: unknown): GuidanceItem[] | undefined {
  if (!Array.isArray(v)) return undefined;
  return v
    .map((g) =>
      isObj(g)
        ? { title: clean(first(g, ["title", "titulo"])), text: clean(first(g, ["text", "texto"])) }
        : { title: "", text: clean(g) }
    )
    .filter((g) => g.title || g.text);
}

function frontMatter(obj: Obj, base: FrontMatter): FrontMatter {
  if (isObj(obj.frontMatter)) {
    const fm = obj.frontMatter as Partial<FrontMatter>;
    return {
      copyright: Array.isArray(fm.copyright) ? fm.copyright.map(clean) : base.copyright,
      dedication: typeof fm.dedication === "string" ? clean(fm.dedication) : base.dedication,
      epigraph: isObj(fm.epigraph)
        ? { text: clean(fm.epigraph.text), reference: clean(fm.epigraph.reference) }
        : base.epigraph,
      introTitle: typeof fm.introTitle === "string" ? clean(fm.introTitle) : base.introTitle,
      intro: Array.isArray(fm.intro) ? paragraphs(fm.intro) : base.intro,
      guidanceTitle: typeof fm.guidanceTitle === "string" ? clean(fm.guidanceTitle) : base.guidanceTitle,
      guidanceIntro: typeof fm.guidanceIntro === "string" ? clean(fm.guidanceIntro) : base.guidanceIntro,
      guidance: guidanceItems(fm.guidance) ?? base.guidance,
      journeyLabel: typeof fm.journeyLabel === "string" ? clean(fm.journeyLabel) : base.journeyLabel,
    };
  }

  const fm = (first(obj, ["frontMatter", "front_matter", "pre_textuais", "pretextuais"]) ?? {}) as Obj;
  const src: Obj = { ...obj, ...(isObj(fm) ? fm : {}) };

  const copyright = paragraphs(first(src, ["copyright", "direitos"]));
  const epi = first(src, ["epigraph", "epigrafe"]);
  const intro = paragraphs(first(src, ["intro", "introduction", "introducao"]));
  const guidance = guidanceItems(first(src, ["guidance", "orientacoes"]));
  const dedication = first(src, ["dedication", "dedicatoria"]);

  // `false` desliga a página correspondente.
  const off = (v: unknown) => v === false;

  return {
    copyright: copyright.length ? copyright : base.copyright,
    dedication: dedication === undefined ? base.dedication : clean(dedication),
    epigraph: off(epi)
      ? { text: "", reference: "" }
      : isObj(epi)
        ? {
            text: stripQuotes(clean(first(epi, ["text", "texto"]))),
            reference: clean(first(epi, ["reference", "referencia"])),
          }
        : base.epigraph,
    introTitle: clean(first(src, ["introTitle", "titulo_introducao"])) || base.introTitle,
    intro: off(first(src, ["intro", "introduction", "introducao"])) ? [] : intro.length ? intro : base.intro,
    guidanceTitle: clean(first(src, ["guidanceTitle", "titulo_orientacoes"])) || base.guidanceTitle,
    guidanceIntro: clean(first(src, ["guidanceIntro", "orientacoes_intro"])) || base.guidanceIntro,
    guidance: off(first(src, ["guidance", "orientacoes"])) ? [] : (guidance ?? base.guidance),
    journeyLabel: clean(first(src, ["journeyLabel", "rotulo_jornada"])) || base.journeyLabel,
  };
}

export function normalizeBookJson(input: unknown, opts: { year: string }): NormalizeResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  let data = input;
  if (typeof data === "string") {
    try {
      data = JSON.parse(data);
    } catch (e) {
      return { book: null, errors: [`JSON inválido: ${(e as Error).message}`], warnings, settings: {} };
    }
  }
  if (!isObj(data)) return { book: null, errors: ["O JSON precisa ser um objeto."], warnings, settings: {} };

  const obj = data;
  const lang = detectLanguage(obj);
  const editorial = isObj(obj.orientacao_editorial) ? obj.orientacao_editorial : {};

  const title = clean(first(obj, ["title", "titulo", "book_title"]));
  const subtitle = clean(first(obj, ["subtitle", "subtitulo"]));
  const author = clean(first(obj, ["author", "autor"]) ?? first(editorial, ["autor", "author"]));

  const rawDays = first(obj, ["days", "dias"]);
  if (!Array.isArray(rawDays) || rawDays.length === 0) {
    errors.push('Nenhum dia encontrado. O JSON precisa de uma lista "dias" (ou "days").');
  }
  const days = (Array.isArray(rawDays) ? rawDays : [])
    .map((d, i) => normalizeDay(d, i, lang, errors, warnings))
    .filter((d): d is Day => d !== null);

  days.forEach((d, i) => {
    if (i > 0 && d.day !== days[i - 1].day + 1) {
      warnings.push(`Numeração dos dias não sequencial: dia ${days[i - 1].day} seguido de ${d.day}.`);
    }
  });

  if (!title) warnings.push("Título do livro ausente.");
  if (!author) warnings.push("Autor ausente.");

  const settings: Obj = {};
  const cfg = first(obj, ["configuracao", "layout", "settings"]);
  if (isObj(cfg)) Object.assign(settings, cfg);
  for (const k of ["trim_size", "edition_type", "bleed", "reading_opening_rule"]) {
    if (obj[k] !== undefined && settings[k] === undefined) settings[k] = obj[k];
  }

  const base = defaultFrontMatter(lang, { days: days.length, author, year: opts.year });
  const book: Book = {
    bookId: clean(first(obj, ["bookId", "book_id"])) || slugify(title || "devocional"),
    title: title || (lang === "pt" ? "Devocional" : "Devotional"),
    subtitle,
    author,
    language: lang,
    days,
    frontMatter: frontMatter(obj, base),
  };

  return { book: errors.length ? null : book, errors, warnings, settings };
}
