// Especificações de impressão Amazon KDP (portadas de kdp_specs.py).
// Fontes oficiais:
// - https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6 (formatos e limites de páginas)
// - https://kdp.amazon.com/en_US/help/topic/G201834180 (margens e sangria)
// - https://kdp.amazon.com/en_US/help/topic/G201857950 (capa paperback)
// - https://kdp.amazon.com/en_US/help/topic/GKYZRXFBZH2LDXAK (capa dura)

export type EditionType = "paperback" | "hardcover";
export type InkType = "black_and_white" | "standard_color" | "premium_color";
export type PaperType = "cream" | "white";

export interface TrimSize {
  code: string;
  width: number;
  height: number;
  name: string;
}

export const KDP_RULES_VERSION = "2026.1";
export const KDP_RULES_VERIFIED = "2026-10-01";

export const GUTTER_TIERS = [
  { minPages: 24, maxPages: 150, gutter: 0.375 },
  { minPages: 151, maxPages: 300, gutter: 0.5 },
  { minPages: 301, maxPages: 500, gutter: 0.625 },
  { minPages: 501, maxPages: 700, gutter: 0.75 },
  { minPages: 701, maxPages: 828, gutter: 0.875 },
];

export const MIN_OUTSIDE_MARGIN = { noBleed: 0.25, bleed: 0.375 };
export const BLEED_PAD = 0.125;

const trim = (code: string, width: number, height: number, name?: string): TrimSize => ({
  code,
  width,
  height,
  name: name ?? `${width}" x ${height}"`,
});

export const TRIM_SIZES: Record<EditionType, TrimSize[]> = {
  paperback: [
    trim("5x8", 5, 8),
    trim("5.06x7.81", 5.06, 7.81),
    trim("5.25x8", 5.25, 8),
    trim("5.5x8.5", 5.5, 8.5),
    trim("6x9", 6, 9),
    trim("6.14x9.21", 6.14, 9.21),
    trim("6.69x9.61", 6.69, 9.61),
    trim("7x10", 7, 10),
    trim("7.44x9.69", 7.44, 9.69),
    trim("7.5x9.25", 7.5, 9.25),
    trim("8x10", 8, 10),
    trim("8.5x8.5", 8.5, 8.5),
    trim("8.5x11", 8.5, 11),
    trim("8.27x11.69", 8.27, 11.69, 'A4 (8.27" x 11.69")'),
  ],
  hardcover: [
    trim("5.5x8.5", 5.5, 8.5),
    trim("6x9", 6, 9),
    trim("6.14x9.21", 6.14, 9.21),
    trim("7x10", 7, 10),
    trim("8.25x11", 8.25, 11),
  ],
};

type Limits = { min: number; max: number };
const PAGE_LIMITS: Record<EditionType, Partial<Record<InkType, Partial<Record<PaperType, Limits>>>>> = {
  paperback: {
    black_and_white: { white: { min: 24, max: 828 }, cream: { min: 24, max: 828 } },
    standard_color: { white: { min: 72, max: 600 } },
    premium_color: { white: { min: 24, max: 828 } },
  },
  hardcover: {
    black_and_white: { white: { min: 75, max: 550 }, cream: { min: 75, max: 550 } },
    standard_color: { white: { min: 75, max: 550 } },
    premium_color: { white: { min: 75, max: 550 } },
  },
};

const PAPER_THICKNESS: Record<InkType, Partial<Record<PaperType, number>>> = {
  black_and_white: { white: 0.002252, cream: 0.0025 },
  standard_color: { white: 0.002252 },
  premium_color: { white: 0.002347 },
};

const COVER = {
  paperback: { bleed: 0.125, minPagesSpineText: 79 },
  hardcover: { wrap: 0.59, hinge: 0.394, spineWrapAllowance: 0.197, minPagesSpineText: 79 },
};

export function minGutter(pageCount: number): number {
  for (const t of GUTTER_TIERS) {
    if (pageCount >= t.minPages && pageCount <= t.maxPages) return t.gutter;
  }
  return pageCount < GUTTER_TIERS[0].minPages ? GUTTER_TIERS[0].gutter : GUTTER_TIERS[GUTTER_TIERS.length - 1].gutter;
}

export function findTrim(code: string, edition: EditionType): TrimSize {
  const norm = code.toLowerCase().replace(/["″\s]/g, "");
  const found = TRIM_SIZES[edition].find((t) => t.code === norm) ?? TRIM_SIZES.paperback.find((t) => t.code === norm);
  if (found) return found;
  const [w, h] = norm.split("x").map(Number);
  if (w > 0 && h > 0) return trim(norm, w, h);
  return TRIM_SIZES.paperback.find((t) => t.code === "6x9")!;
}

export interface PageGeometry {
  trimWidth: number;
  trimHeight: number;
  pageWidth: number;
  pageHeight: number;
  bleedPad: number;
}

export function pageGeometry(trimCode: string, edition: EditionType, bleed: boolean): PageGeometry {
  const t = findTrim(trimCode, edition);
  return {
    trimWidth: t.width,
    trimHeight: t.height,
    pageWidth: bleed ? t.width + BLEED_PAD : t.width,
    pageHeight: bleed ? t.height + 2 * BLEED_PAD : t.height,
    bleedPad: bleed ? BLEED_PAD : 0,
  };
}

export interface ProfileValidation {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

export function validateProfile(opts: {
  edition: EditionType;
  trimSize: string;
  ink: InkType;
  paper: PaperType;
  pageCount: number;
}): ProfileValidation {
  const errors: string[] = [];
  const warnings: string[] = [];
  const editionName = opts.edition === "hardcover" ? "capa dura" : "brochura";

  if (!TRIM_SIZES[opts.edition].some((t) => t.code === opts.trimSize)) {
    errors.push(`Formato ${opts.trimSize} não é suportado pelo KDP para ${editionName}.`);
  }

  const limits = PAGE_LIMITS[opts.edition][opts.ink]?.[opts.paper];
  if (!limits) {
    errors.push(`Papel ${opts.paper} não está disponível para ${editionName} com tinta ${opts.ink}.`);
  } else if (opts.pageCount < limits.min) {
    errors.push(`${opts.pageCount} páginas está abaixo do mínimo de ${limits.min} para ${editionName} (${opts.ink}).`);
  } else if (opts.pageCount > limits.max) {
    errors.push(`${opts.pageCount} páginas excede o máximo de ${limits.max} para ${editionName} (${opts.ink}).`);
  }

  if (opts.pageCount % 2 !== 0) {
    warnings.push("O total de páginas é ímpar; o KDP exige número par.");
  }
  const minSpine = COVER[opts.edition].minPagesSpineText;
  if (opts.pageCount < minSpine) {
    warnings.push(`Com ${opts.pageCount} páginas o KDP não permite texto na lombada (mínimo ${minSpine}).`);
  }

  return { ok: errors.length === 0, errors, warnings };
}

export interface CoverDimensions {
  spineWidth: number;
  totalWidth: number;
  totalHeight: number;
  allowSpineText: boolean;
}

export function coverDimensions(opts: {
  edition: EditionType;
  trimSize: string;
  ink: InkType;
  paper: PaperType;
  pageCount: number;
}): CoverDimensions {
  const t = findTrim(opts.trimSize, opts.edition);
  const perPage = PAPER_THICKNESS[opts.ink][opts.paper] ?? PAPER_THICKNESS[opts.ink].white ?? 0.002252;
  const interiorSpine = opts.pageCount * perPage;

  if (opts.edition === "hardcover") {
    const c = COVER.hardcover;
    const spineWidth = interiorSpine + c.spineWrapAllowance;
    return {
      spineWidth,
      totalWidth: 2 * t.width + spineWidth + 2 * c.wrap + 2 * c.hinge,
      totalHeight: t.height + 2 * c.wrap + 0.25,
      allowSpineText: opts.pageCount >= c.minPagesSpineText,
    };
  }

  const c = COVER.paperback;
  return {
    spineWidth: interiorSpine,
    totalWidth: 2 * t.width + interiorSpine + 2 * c.bleed,
    totalHeight: t.height + 2 * c.bleed,
    allowSpineText: opts.pageCount >= c.minPagesSpineText,
  };
}
