import { FONT_FACES } from "@/generated/assets";
import TITLE_FONT_LIST from "./title-fonts.json";

export interface TitleFont {
  key: string;
  family: string;
  pkg: string;
  weight: number;
  group: string;
  // false para manuscritas: nada de caixa alta nem espaçamento entre letras.
  caps: boolean;
  // Correção de tamanho para igualar a altura visual da fonte padrão.
  scale: number;
}

export const TITLE_FONTS = TITLE_FONT_LIST as TitleFont[];
export const DEFAULT_TITLE_FONT = "default";

export function findTitleFont(key: string): TitleFont | null {
  return TITLE_FONTS.find((f) => f.key === key) ?? null;
}

// Famílias usadas sempre pelo layout base.
const BASE_FAMILIES = ["Cinzel", "Cormorant Garamond", "EB Garamond"];

export type FontSrc = (file: string) => string;

export function fontFaceCss(src: FontSrc, extraFamilies: string[] = []): string {
  const families = new Set([...BASE_FAMILIES, ...extraFamilies]);
  return FONT_FACES.filter((f) => families.has(f.family))
    .map(
      (f) =>
        `@font-face{font-family:'${f.family}';font-style:${f.style};font-weight:${f.weight};font-display:block;src:url(${src(f.file)}) format('woff2');}`
    )
    .join("\n");
}
