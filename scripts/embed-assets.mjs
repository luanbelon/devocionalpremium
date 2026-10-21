// Prepara os assets usados na diagramação:
// - copia as fontes (woff2) para public/fonts (preview no navegador)
// - gera src/generated/fonts-data.ts com as fontes em base64 (PDF no servidor)
// - gera src/generated/assets.ts com a lista de fontes e os ícones em data URI
// - copia os JSONs de exemplo para public/samples
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fontsOut = path.join(root, "public", "fonts");
const samplesOut = path.join(root, "public", "samples");
const genOut = path.join(root, "src", "generated");

const FONTS = [
  ["cinzel", "Cinzel", [[400, "normal"], [500, "normal"], [600, "normal"], [700, "normal"]]],
  [
    "cormorant-garamond",
    "Cormorant Garamond",
    [[400, "normal"], [400, "italic"], [500, "normal"], [500, "italic"], [600, "normal"], [600, "italic"], [700, "normal"]],
  ],
  [
    "eb-garamond",
    "EB Garamond",
    [[400, "normal"], [400, "italic"], [500, "normal"], [600, "normal"], [600, "italic"], [700, "normal"]],
  ],
];

const iconsDir = path.join(root, "assets", "icons");
const ICONS = fs
  .readdirSync(iconsDir)
  .filter((f) => f.endsWith(".png"))
  .map((f) => f.replace(/\.png$/, ""));

fs.mkdirSync(fontsOut, { recursive: true });
fs.mkdirSync(samplesOut, { recursive: true });
fs.mkdirSync(genOut, { recursive: true });

const faces = [];
const fontData = {};
for (const [pkg, family, variants] of FONTS) {
  const dir = path.join(root, "node_modules", "@fontsource", pkg, "files");
  for (const [weight, style] of variants) {
    const file = `${pkg}-latin-${weight}-${style}.woff2`;
    const src = path.join(dir, file);
    if (!fs.existsSync(src)) throw new Error(`Fonte não encontrada: ${src}`);
    fs.copyFileSync(src, path.join(fontsOut, file));
    fontData[file] = fs.readFileSync(src).toString("base64");
    faces.push({ family, weight, style, file });
  }
}

const icons = {};
for (const name of ICONS) {
  const src = path.join(iconsDir, `${name}.png`);
  icons[name] = `data:image/png;base64,${fs.readFileSync(src).toString("base64")}`;
}

const samples = [];
const samplesDir = path.join(root, "samples");
for (const file of fs.readdirSync(samplesDir).filter((f) => f.endsWith(".json"))) {
  fs.copyFileSync(path.join(samplesDir, file), path.join(samplesOut, file));
  samples.push(file);
}

const header = "// Arquivo gerado por scripts/embed-assets.mjs. Não edite manualmente.\n";

fs.writeFileSync(
  path.join(genOut, "assets.ts"),
  header +
    `export const FONT_FACES = ${JSON.stringify(faces, null, 2)} as const;\n\n` +
    `export const ICONS = ${JSON.stringify(icons)} as const;\n\n` +
    `export const SAMPLE_FILES = ${JSON.stringify(samples)} as const;\n`
);

fs.writeFileSync(
  path.join(genOut, "fonts-data.ts"),
  header + `export const FONT_DATA: Record<string, string> = ${JSON.stringify(fontData)};\n`
);

console.log(`[assets] ${faces.length} fontes, ${ICONS.length} ícones, ${samples.length} exemplos.`);
