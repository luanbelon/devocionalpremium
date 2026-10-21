import { TRIM_SIZES, type EditionType, type PaperType } from "./kdp";
import { sanitizeSvg } from "./ornament";
import type { Palette } from "./types";

export const PALETTE_KEYS = ["creme", "verde", "azul", "rosa", "lilas", "amarelo"] as const satisfies readonly Palette[];

export interface Settings {
  editionType: EditionType;
  trimSize: string;
  bleed: boolean;
  openingRule: "new_page" | "recto";
  marginInside: number;
  marginOutside: number;
  marginTop: number;
  marginBottom: number;
  fontSizePt: number;
  lineHeight: number;
  autoFit: boolean;
  targetPagesPerDay: number;
  ornamentPx: number;
  // SVG enviado pelo usuário para substituir o ramo ("" = ramo padrão).
  customOrnamentSvg: string;
  customOrnamentName: string;
  includeFrontMatter: boolean;
  colorInk: "premium_color" | "standard_color";
  colorPalette: Palette;
  bwPaper: PaperType;
  year: string;
}

export const DEFAULT_SETTINGS: Settings = {
  editionType: "paperback",
  trimSize: "6x9",
  bleed: false,
  openingRule: "new_page",
  marginInside: 0.75,
  marginOutside: 0.65,
  marginTop: 0.55,
  marginBottom: 0.55,
  fontSizePt: 11.4,
  lineHeight: 1.68,
  autoFit: true,
  targetPagesPerDay: 3,
  // 32px do modelo colorido (docs/modelos/dia_28_pag_1.png) + 30%.
  ornamentPx: 42,
  customOrnamentSvg: "",
  customOrnamentName: "",
  includeFrontMatter: true,
  colorInk: "premium_color",
  colorPalette: "creme",
  bwPaper: "cream",
  year: String(new Date().getFullYear()),
};

const num = (v: unknown, fallback: number, min: number, max: number): number => {
  const n = typeof v === "string" ? Number(v) : typeof v === "number" ? v : NaN;
  return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
};

const pick = <T extends string>(v: unknown, options: readonly T[], fallback: T): T =>
  typeof v === "string" && (options as readonly string[]).includes(v) ? (v as T) : fallback;

const bool = (v: unknown, fallback: boolean): boolean => (typeof v === "boolean" ? v : fallback);

export function sanitizeSettings(input: unknown, base: Settings = DEFAULT_SETTINGS): Settings {
  const s = (input && typeof input === "object" ? input : {}) as Record<string, unknown>;
  const editionType = pick(s.editionType ?? s.edition_type, ["paperback", "hardcover"] as const, base.editionType);
  const trimCodes = TRIM_SIZES[editionType].map((t) => t.code);
  const trimInput = String(s.trimSize ?? s.trim_size ?? base.trimSize).toLowerCase().replace(/["″\s]/g, "");
  const trimSize = trimCodes.includes(trimInput) ? trimInput : trimCodes.includes(base.trimSize) ? base.trimSize : "6x9";

  return {
    editionType,
    trimSize,
    bleed: bool(s.bleed, base.bleed),
    openingRule: pick(s.openingRule ?? s.reading_opening_rule, ["new_page", "recto"] as const, base.openingRule),
    marginInside: num(s.marginInside, base.marginInside, 0.375, 1.5),
    marginOutside: num(s.marginOutside, base.marginOutside, 0.25, 1.5),
    marginTop: num(s.marginTop, base.marginTop, 0.25, 1.5),
    marginBottom: num(s.marginBottom, base.marginBottom, 0.25, 1.5),
    fontSizePt: num(s.fontSizePt, base.fontSizePt, 8, 16),
    lineHeight: num(s.lineHeight, base.lineHeight, 1.1, 2.2),
    autoFit: bool(s.autoFit, base.autoFit),
    targetPagesPerDay: Math.round(num(s.targetPagesPerDay, base.targetPagesPerDay, 1, 8)),
    ornamentPx: num(s.ornamentPx, base.ornamentPx, 8, 160),
    customOrnamentSvg:
      s.customOrnamentSvg === undefined ? base.customOrnamentSvg : (sanitizeSvg(s.customOrnamentSvg) ?? ""),
    customOrnamentName:
      typeof s.customOrnamentName === "string" ? s.customOrnamentName.slice(0, 120) : base.customOrnamentName,
    includeFrontMatter: bool(s.includeFrontMatter, base.includeFrontMatter),
    colorInk: pick(s.colorInk, ["premium_color", "standard_color"] as const, base.colorInk),
    colorPalette: pick(s.colorPalette ?? s.paleta, PALETTE_KEYS, base.colorPalette),
    bwPaper: pick(s.bwPaper, ["cream", "white"] as const, base.bwPaper),
    year: typeof s.year === "string" || typeof s.year === "number" ? String(s.year).slice(0, 8) : base.year,
  };
}
