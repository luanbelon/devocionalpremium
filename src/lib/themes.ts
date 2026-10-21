import { ICONS } from "@/generated/assets";
import type { Theme } from "./types";

export interface ThemeDef {
  label: string;
  vars: Record<string, string>;
  icons: { ramo: string; maos: string };
}

export const THEMES: Record<Theme, ThemeDef> = {
  // Paleta extraída dos modelos coloridos (docs/modelos/dia_28_pag_*.png).
  color: {
    label: "Colorida",
    vars: {
      "--ink": "#241C18",
      "--ink-strong": "#1A1311",
      "--header-text": "#4A3D37",
      "--header-line": "#D8CCBE",
      "--badge-bg": "#F4EFE9",
      "--badge-border": "#BEAEA0",
      "--badge-text": "#2B211B",
      "--card-bg": "#F5F1E9",
      "--card-border": "#F5F1E9",
      "--card-title": "#2B211B",
      "--ref": "#4A3F37",
      "--footer": "#3C2F28",
      "--muted": "#7A6A5E",
      "--rule": "#D8CCBE",
    },
    icons: { ramo: ICONS.ramo_color, maos: ICONS.maos_color },
  },
  // Apenas tons de cinza, exigência do miolo preto e branco do KDP.
  bw: {
    label: "Preto e branco",
    vars: {
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
  },
};
