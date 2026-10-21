import { FONT_FACES } from "@/generated/assets";

export function fontFaceCss(src: (file: string) => string): string {
  return FONT_FACES.map(
    (f) =>
      `@font-face{font-family:'${f.family}';font-style:${f.style};font-weight:${f.weight};font-display:block;src:url(${src(f.file)}) format('woff2');}`
  ).join("\n");
}
