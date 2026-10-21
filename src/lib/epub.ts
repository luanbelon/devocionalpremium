import JSZip from "jszip";
import { LABELS } from "./i18n";
import { THEMES } from "./themes";
import type { Book } from "./types";

const EPUB_CSS = `@charset "utf-8";
body { margin: 5% 7%; font-family: "EB Garamond", Garamond, Georgia, serif; color: #241C18; line-height: 1.6; }
h1, h2 { font-weight: 600; line-height: 1.25; text-align: center; color: #1A1311; }
.center { text-align: center; }
.title-page { text-align: center; margin-top: 18%; }
.book-title { font-size: 2.1em; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.4em; }
.book-subtitle { font-size: 1.1em; font-style: italic; color: #4A3D37; margin-bottom: 1.6em; }
.book-author { font-size: 1em; letter-spacing: 0.2em; text-transform: uppercase; color: #4A3D37; margin-top: 1.6em; }
.ornament { text-align: center; margin: 0.4em 0 1.2em; }
.ornament img { width: 2em; height: auto; }
.copyright { margin-top: 30%; font-size: 0.85em; line-height: 1.6; color: #4A3D37; text-align: center; }
.copyright p { margin: 0 0 0.8em; }
.copyright .head { font-weight: bold; color: #1A1311; }
.dedication, .epigraph { margin-top: 30%; text-align: center; font-style: italic; font-size: 1.15em; line-height: 1.7; padding: 0 8%; }
.epigraph-ref { font-style: normal; font-size: 0.8em; letter-spacing: 0.18em; text-transform: uppercase; color: #4A3F37; margin-top: 0.8em; }
.heading { font-size: 1.4em; letter-spacing: 0.12em; text-transform: uppercase; margin: 1.2em 0 1em; }
.toc { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0 0 0.55em; border-bottom: 1px dotted #D8CCBE; padding-bottom: 0.3em; }
.toc a { color: #1A1311; text-decoration: none; }
.toc .toc-day { font-size: 0.8em; letter-spacing: 0.08em; text-transform: uppercase; color: #7A6A5E; margin-right: 0.5em; }
.day-badge-wrap { text-align: center; margin: 1em 0 0.8em; }
.day-badge { display: inline-block; padding: 0.2em 1.2em; border: 1px solid #BEAEA0; border-radius: 9px; background-color: #F4EFE9; font-size: 0.8em; font-weight: bold; letter-spacing: 0.2em; color: #2B211B; text-transform: uppercase; }
.day-title { font-size: 1.8em; margin: 0 0 0.4em; }
.scripture { background-color: #F5F1E9; border-radius: 8px; padding: 1.1em 1.4em; margin: 1.2em 0 1.6em; text-align: center; }
.scripture-text { font-style: italic; font-size: 1.05em; line-height: 1.5; color: #1A1311; margin: 0 0 0.5em; }
.scripture-ref { font-size: 0.78em; font-weight: bold; letter-spacing: 0.2em; color: #4A3F37; text-transform: uppercase; margin: 0; }
p.para { text-align: justify; margin: 0 0 0.9em; text-indent: 0; }
.dropcap { float: left; font-size: 3.2em; line-height: 0.8; padding: 0.04em 0.12em 0 0; color: #1A1311; font-weight: bold; }
.card { background-color: #F5F1E9; border-radius: 8px; padding: 1em 1.2em; margin: 1.2em 0; }
.card-head { margin: 0 0 0.4em; }
.card-head img { width: 1.4em; height: auto; vertical-align: middle; margin-right: 0.5em; }
.card-title { font-size: 0.8em; font-weight: bold; letter-spacing: 0.16em; color: #2B211B; text-transform: uppercase; vertical-align: middle; }
.card-text { margin: 0; text-align: justify; }
`;

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");

function stableUuid(seed: string): string {
  const hashes: string[] = [];
  for (let round = 0; round < 4; round++) {
    let h = 0x811c9dc5 ^ round;
    for (let i = 0; i < seed.length; i++) {
      h ^= seed.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    hashes.push(h.toString(16).padStart(8, "0"));
  }
  const hex = hashes.join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-5${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function xhtml(lang: string, title: string, body: string, bodyType?: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="${lang}" lang="${lang}">
<head>
<meta charset="UTF-8"/>
<title>${esc(title)}</title>
<link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body${bodyType ? ` epub:type="${bodyType}"` : ""}>
${body}
</body>
</html>`;
}

interface Chapter {
  id: string;
  file: string;
  title: string;
  html: string;
  inToc: boolean;
}

export function epubFileName(book: Book): string {
  return `${book.bookId || "devocional"}.epub`;
}

export async function buildEpub(book: Book): Promise<Uint8Array> {
  const lang = book.language === "pt" ? "pt-BR" : "en-US";
  const labels = LABELS[book.language];
  const fm = book.frontMatter;
  const icons = THEMES.color.icons;
  const chapters: Chapter[] = [];
  const add = (id: string, title: string, body: string, inToc: boolean, bodyType?: string) =>
    chapters.push({ id, file: `text/${id}.xhtml`, title, html: xhtml(lang, title, body, bodyType), inToc });

  const ornament = `<div class="ornament"><img src="../images/ramo.png" alt=""/></div>`;

  add(
    "titlepage",
    book.title,
    `<div class="title-page">
<h1 class="book-title">${esc(book.title)}</h1>
${book.subtitle ? `<p class="book-subtitle">${esc(book.subtitle)}</p>` : ""}
${ornament}
${book.author ? `<p class="book-author">${esc(book.author)}</p>` : ""}
</div>`,
    false,
    "titlepage"
  );

  add(
    "copyright",
    "Copyright",
    `<div class="copyright">${fm.copyright.map((t, i) => `<p${i === 0 ? ' class="head"' : ""}>${esc(t)}</p>`).join("\n")}</div>`,
    false,
    "copyright-page"
  );

  if (fm.dedication) {
    add(
      "dedication",
      book.language === "pt" ? "Dedicatória" : "Dedication",
      `<div class="dedication"><p>“${esc(fm.dedication)}”</p></div>`,
      false,
      "dedication"
    );
  }

  if (fm.epigraph.text) {
    add(
      "epigraph",
      book.language === "pt" ? "Epígrafe" : "Epigraph",
      `<div class="epigraph"><p>“${esc(fm.epigraph.text)}”</p>${
        fm.epigraph.reference ? `<p class="epigraph-ref">${esc(fm.epigraph.reference)}</p>` : ""
      }</div>`,
      false,
      "epigraph"
    );
  }

  if (fm.intro.length || fm.guidance.length) {
    const intro = fm.intro.length
      ? `<h2 class="heading">${esc(fm.introTitle)}</h2>\n${fm.intro.map((p) => `<p class="para">${esc(p)}</p>`).join("\n")}`
      : "";
    const guidance = fm.guidance.length
      ? `<h2 class="heading">${esc(fm.guidanceTitle)}</h2>
${fm.guidanceIntro ? `<p class="para">${esc(fm.guidanceIntro)}</p>` : ""}
${fm.guidance
  .map((g) => `<p class="para">• ${g.title ? `<strong>${esc(g.title)}:</strong> ` : ""}${esc(g.text)}</p>`)
  .join("\n")}`
      : "";
    add("introduction", fm.introTitle || fm.guidanceTitle, `${intro}\n${guidance}`, true, "introduction");
  }

  const dayId = (n: number) => `day_${String(n).padStart(2, "0")}`;
  add(
    "contents",
    labels.contents,
    `<h2 class="heading">${esc(labels.contents)}</h2>
<ul class="toc">
${book.days
  .map(
    (d) =>
      `<li><a href="${dayId(d.day)}.xhtml"><span class="toc-day">${esc(labels.day)} ${d.day}</span>${esc(d.title)}</a></li>`
  )
  .join("\n")}
</ul>`,
    false,
    "toc"
  );

  for (const d of book.days) {
    const paras = d.paragraphs
      .map((p, i) => {
        if (i > 0) return `<p class="para">${esc(p)}</p>`;
        const m = /^([“‘"'(\[«]*)(.)([\s\S]*)$/u.exec(p);
        return m
          ? `<p class="para"><span class="dropcap">${esc(m[1] + m[2])}</span>${esc(m[3])}</p>`
          : `<p class="para">${esc(p)}</p>`;
      })
      .join("\n");
    const card = (img: string, c: { title: string; text: string }) =>
      c.text
        ? `<div class="card"><p class="card-head"><img src="../images/${img}" alt=""/><span class="card-title">${esc(
            c.title
          )}</span></p><p class="card-text">${esc(c.text)}</p></div>`
        : "";

    add(
      dayId(d.day),
      `${labels.day} ${d.day}: ${d.title}`,
      `<div class="day-badge-wrap"><span class="day-badge">${esc(labels.day)} ${d.day}</span></div>
<h1 class="day-title">${esc(d.title)}</h1>
${ornament}
${
  d.verse.text || d.verse.reference
    ? `<div class="scripture">${d.verse.text ? `<p class="scripture-text">“${esc(d.verse.text)}”</p>` : ""}${
        d.verse.reference ? `<p class="scripture-ref">${esc(d.verse.reference)}</p>` : ""
      }</div>`
    : ""
}
${paras}
${card("ramo.png", d.heart)}
${card("maos.png", d.prayer)}`,
      true,
      "chapter"
    );
  }

  const uuid = stableUuid(`${book.bookId}|${book.title}|${book.language}`);
  const modified = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const firstDay = chapters.find((c) => c.id.startsWith("day_"));
  const tocChapters = chapters.filter((c) => c.inToc);

  const nav = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="${lang}" lang="${lang}">
<head><meta charset="UTF-8"/><title>${esc(labels.contents)}</title><link rel="stylesheet" type="text/css" href="styles/style.css"/></head>
<body>
<nav epub:type="toc" id="toc"><h2 class="heading">${esc(labels.contents)}</h2>
<ol>
${tocChapters.map((c) => `<li><a href="${c.file}">${esc(c.title)}</a></li>`).join("\n")}
</ol>
</nav>
<nav epub:type="landmarks" hidden="hidden"><ol>
<li><a epub:type="toc" href="text/contents.xhtml">${esc(labels.contents)}</a></li>
${firstDay ? `<li><a epub:type="bodymatter" href="${firstDay.file}">${esc(firstDay.title)}</a></li>` : ""}
</ol></nav>
</body>
</html>`;

  const ncx = `<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="${lang}">
<head><meta name="dtb:uid" content="urn:uuid:${uuid}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
<docTitle><text>${esc(book.title)}</text></docTitle>
<navMap>
${tocChapters
  .map((c, i) => `<navPoint id="np${i + 1}" playOrder="${i + 1}"><navLabel><text>${esc(c.title)}</text></navLabel><content src="${c.file}"/></navPoint>`)
  .join("\n")}
</navMap>
</ncx>`;

  const opf = `<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="${lang}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">urn:uuid:${uuid}</dc:identifier>
<dc:title>${esc(book.title)}</dc:title>
${book.author ? `<dc:creator>${esc(book.author)}</dc:creator>` : ""}
<dc:language>${lang}</dc:language>
${book.subtitle ? `<dc:description>${esc(book.subtitle)}</dc:description>` : ""}
<dc:subject>${book.language === "pt" ? "Devocional cristão" : "Christian Devotional"}</dc:subject>
<meta property="dcterms:modified">${modified}</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="styles/style.css" media-type="text/css"/>
<item id="img-ramo" href="images/ramo.png" media-type="image/png"/>
<item id="img-maos" href="images/maos.png" media-type="image/png"/>
${chapters.map((c) => `<item id="${c.id}" href="${c.file}" media-type="application/xhtml+xml"/>`).join("\n")}
</manifest>
<spine toc="ncx">
${chapters.map((c) => `<itemref idref="${c.id}"/>`).join("\n")}
</spine>
</package>`;

  const zip = new JSZip();
  zip.file("mimetype", "application/epub+zip", { compression: "STORE" });
  zip.file(
    "META-INF/container.xml",
    `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>`
  );
  zip.file("OEBPS/content.opf", opf);
  zip.file("OEBPS/nav.xhtml", nav);
  zip.file("OEBPS/toc.ncx", ncx);
  zip.file("OEBPS/styles/style.css", EPUB_CSS);
  zip.file("OEBPS/images/ramo.png", icons.ramo.split(",")[1], { base64: true });
  zip.file("OEBPS/images/maos.png", icons.maos.split(",")[1], { base64: true });
  for (const c of chapters) zip.file(`OEBPS/${c.file}`, c.html);

  return zip.generateAsync({ type: "uint8array", compression: "DEFLATE", mimeType: "application/epub+zip" });
}
