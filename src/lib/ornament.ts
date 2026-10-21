// Ornamento (ramo) personalizado enviado como SVG.
// Funciona só com strings (sem DOM) para rodar igual no navegador e no servidor.

export const MAX_SVG_BYTES = 300_000;

export function sanitizeSvg(raw: unknown): string | null {
  if (typeof raw !== "string" || !raw.trim() || raw.length > MAX_SVG_BYTES) return null;
  let s = raw.trim();
  const start = s.search(/<svg[\s>]/i);
  const end = s.toLowerCase().lastIndexOf("</svg>");
  if (start < 0 || end < start) return null;
  s = s.slice(start, end + "</svg>".length);

  s = s
    .replace(/<script[\s\S]*?<\/script\s*>/gi, "")
    .replace(/<foreignObject[\s\S]*?<\/foreignObject\s*>/gi, "")
    .replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*')/gi, "")
    .replace(/((?:xlink:)?href\s*=\s*["'])\s*(?:javascript|data:text\/html)[^"']*/gi, "$1#");

  if (!/^<svg[^>]*\sxmlns\s*=/i.test(s)) s = s.replace(/^<svg/i, '<svg xmlns="http://www.w3.org/2000/svg"');
  return s;
}

const rootTag = (svg: string) => svg.slice(0, svg.indexOf(">") + 1);

// Largura / altura do desenho, a partir do viewBox ou de width/height.
export function svgAspect(svg: string): number {
  const root = rootTag(svg);
  const vb = /viewBox\s*=\s*["']\s*[-\d.e]+[\s,]+[-\d.e]+[\s,]+([\d.e]+)[\s,]+([\d.e]+)/i.exec(root);
  if (vb && Number(vb[1]) > 0 && Number(vb[2]) > 0) return Number(vb[1]) / Number(vb[2]);
  const w = /\swidth\s*=\s*["']\s*([\d.]+)/i.exec(root);
  const h = /\sheight\s*=\s*["']\s*([\d.]+)/i.exec(root);
  if (w && h && Number(w[1]) > 0 && Number(h[1]) > 0) return Number(w[1]) / Number(h[1]);
  return 1;
}

// Pinta todo preenchimento e contorno com a cor do tema, preservando "none"
// e referências a gradientes/padrões.
export function recolorSvg(svg: string, color: string): string {
  let s = svg
    .replace(/\b(fill|stroke)\s*=\s*(["'])(?!\s*none\b)(?!\s*url\()[^"']*\2/gi, (_m, attr, q) => `${attr}=${q}${color}${q}`)
    .replace(/\b(fill|stroke)\s*:\s*(?!\s*none\b)(?!\s*url\()[^;}"']+/gi, (_m, prop) => `${prop}:${color}`)
    .replace(/currentColor/gi, color);
  if (!/\sfill\s*=/i.test(rootTag(s))) s = s.replace(/^<svg/i, `<svg fill="${color}"`);
  return s;
}

export function svgDataUri(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
