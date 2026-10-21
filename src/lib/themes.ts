import { ICONS } from "@/generated/assets";
import { recolorSvg, svgAspect, svgDataUri } from "./ornament";
import type { Palette, Theme } from "./types";

export interface ThemeDef {
  label: string;
  vars: Record<string, string>;
  icons: { ramo: string; maos: string };
}

export interface PaletteDef extends ThemeDef {
  swatch: string;
}

type Tones = {
  accent: string;
  ink: string;
  inkStrong: string;
  headerText: string;
  headerLine: string;
  badgeBg: string;
  badgeBorder: string;
  cardBg: string;
  cardTitle: string;
  ref: string;
  footer: string;
  muted: string;
};

const vars = (t: Tones): Record<string, string> => ({
  "--accent": t.accent,
  "--ink": t.ink,
  "--ink-strong": t.inkStrong,
  "--header-text": t.headerText,
  "--header-line": t.headerLine,
  "--badge-bg": t.badgeBg,
  "--badge-border": t.badgeBorder,
  "--badge-text": t.cardTitle,
  "--card-bg": t.cardBg,
  "--card-border": t.cardBg,
  "--card-title": t.cardTitle,
  "--ref": t.ref,
  "--footer": t.footer,
  "--muted": t.muted,
  "--rule": t.headerLine,
});

const palette = (key: Palette, label: string, tones: Tones): PaletteDef => ({
  label,
  swatch: tones.accent,
  vars: vars(tones),
  icons: { ramo: ICONS[`ramo_${key}`], maos: ICONS[`maos_${key}`] },
});

export const PALETTE_ORDER: Palette[] = ["creme", "verde", "azul", "rosa", "lilas", "amarelo"];

export const PALETTES: Record<Palette, PaletteDef> = {
  // Paleta extraída dos modelos coloridos (docs/modelos/dia_28_pag_*.png).
  creme: palette("creme", "Creme", {
    accent: "#AF855D",
    ink: "#241C18",
    inkStrong: "#1A1311",
    headerText: "#4A3D37",
    headerLine: "#D8CCBE",
    badgeBg: "#F4EFE9",
    badgeBorder: "#BEAEA0",
    cardBg: "#F5F1E9",
    cardTitle: "#2B211B",
    ref: "#4A3F37",
    footer: "#3C2F28",
    muted: "#7A6A5E",
  }),
  verde: palette("verde", "Verde", {
    accent: "#6F8F6A",
    ink: "#1F2620",
    inkStrong: "#172019",
    headerText: "#3F4F3D",
    headerLine: "#C9D6C4",
    badgeBg: "#EDF2EA",
    badgeBorder: "#A9BCA4",
    cardBg: "#EEF3EC",
    cardTitle: "#263324",
    ref: "#44573F",
    footer: "#33402F",
    muted: "#6B7C66",
  }),
  azul: palette("azul", "Azul", {
    accent: "#5E7FA3",
    ink: "#1C222A",
    inkStrong: "#141A22",
    headerText: "#3A4A5C",
    headerLine: "#C7D3E0",
    badgeBg: "#EBF0F6",
    badgeBorder: "#A7B8CC",
    cardBg: "#EDF2F7",
    cardTitle: "#22303F",
    ref: "#3F5168",
    footer: "#2F3B4A",
    muted: "#66768A",
  }),
  rosa: palette("rosa", "Rosa", {
    accent: "#B97A86",
    ink: "#2A1F21",
    inkStrong: "#211719",
    headerText: "#5A3E44",
    headerLine: "#E6CCD1",
    badgeBg: "#F7ECEE",
    badgeBorder: "#D3AEB5",
    cardBg: "#F8EEF0",
    cardTitle: "#3A262A",
    ref: "#6A4950",
    footer: "#4A3237",
    muted: "#8A6E73",
  }),
  lilas: palette("lilas", "Lilás", {
    accent: "#8C7BAE",
    ink: "#221F2A",
    inkStrong: "#1A1722",
    headerText: "#4A4160",
    headerLine: "#D9D2E6",
    badgeBg: "#F0EDF6",
    badgeBorder: "#BDB2D2",
    cardBg: "#F2EFF7",
    cardTitle: "#2E2840",
    ref: "#54496E",
    footer: "#3A3350",
    muted: "#7A7290",
  }),
  amarelo: palette("amarelo", "Amarelo", {
    accent: "#C29A3A",
    ink: "#262116",
    inkStrong: "#1D180E",
    headerText: "#574820",
    headerLine: "#EADDB5",
    badgeBg: "#F8F1DC",
    badgeBorder: "#D9C48D",
    cardBg: "#FAF4E2",
    cardTitle: "#3A3014",
    ref: "#66562A",
    footer: "#463B1E",
    muted: "#85764B",
  }),
};

// Apenas tons de cinza, exigência do miolo preto e branco do KDP.
const BW: ThemeDef = {
  label: "Preto e branco",
  vars: {
    "--accent": "#1E1E1E",
    "--ink": "#1A1A1A",
    "--ink-strong": "#000000",
    "--header-text": "#333333",
    "--header-line": "#CCCCCC",
    "--badge-bg": "#F0F0F0",
    "--badge-border": "#888888",
    "--badge-text": "#111111",
    "--card-bg": "#F4F4F4",
    "--card-border": "#DEDEDE",
    "--card-title": "#111111",
    "--ref": "#444444",
    "--footer": "#222222",
    "--muted": "#666666",
    "--rule": "#BBBBBB",
  },
  icons: { ramo: ICONS.ramo_bw, maos: ICONS.maos_bw },
};

export function themeDef(theme: Theme, paletteKey: Palette): ThemeDef {
  return theme === "bw" ? BW : (PALETTES[paletteKey] ?? PALETTES.creme);
}

// Proporção do ramo padrão (assets/icons/ramo_*.png).
const DEFAULT_ORNAMENT_RATIO = 256 / 150;

export interface ResolvedTheme extends ThemeDef {
  ornamentRatio: number;
  // SVG do ornamento personalizado já recolorido, ou null para o ramo padrão.
  ornamentSvg: string | null;
}

export function resolveTheme(
  theme: Theme,
  opts: { colorPalette: Palette; customOrnamentSvg: string }
): ResolvedTheme {
  const base = themeDef(theme, opts.colorPalette);
  if (!opts.customOrnamentSvg) return { ...base, ornamentRatio: DEFAULT_ORNAMENT_RATIO, ornamentSvg: null };
  const svg = recolorSvg(opts.customOrnamentSvg, base.vars["--accent"]);
  return {
    ...base,
    icons: { ...base.icons, ramo: svgDataUri(svg) },
    ornamentRatio: svgAspect(svg),
    ornamentSvg: svg,
  };
}
