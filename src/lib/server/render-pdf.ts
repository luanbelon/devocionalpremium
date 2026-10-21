import { PDFDocument } from "pdf-lib";
import type { Browser } from "puppeteer-core";
import { FONT_DATA } from "@/generated/fonts-data";
import { buildBookHtml } from "../book-html";
import { fontFaceCss } from "../fonts";
import { pageGeometry } from "../kdp";
import type { Settings } from "../settings";
import type { Book, BookReport, Theme } from "../types";

const embeddedFontCss = fontFaceCss((file) => `data:font/woff2;base64,${FONT_DATA[file]}`);

export interface RenderedPdf {
  pdf: Uint8Array;
  report: BookReport;
}

export async function renderPdf(browser: Browser, book: Book, settings: Settings, theme: Theme): Promise<RenderedPdf> {
  const geo = pageGeometry(settings.trimSize, settings.editionType, settings.bleed);
  const html = buildBookHtml(book, settings, { theme, mode: "print", fontCss: embeddedFontCss });
  const page = await browser.newPage();

  try {
    await page.setViewport({ width: Math.ceil(geo.pageWidth * 96), height: Math.ceil(geo.pageHeight * 96) });
    await page.setContent(html, { waitUntil: "load", timeout: 120_000 });
    await page.waitForFunction("window.__BOOK_REPORT__ || window.__BOOK_ERROR__", { timeout: 240_000, polling: 100 });

    const error = (await page.evaluate("window.__BOOK_ERROR__ || null")) as string | null;
    if (error) throw new Error(`Falha na paginação: ${error}`);
    const report = (await page.evaluate("window.__BOOK_REPORT__")) as BookReport;

    const raw = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,
      width: `${geo.pageWidth}in`,
      height: `${geo.pageHeight}in`,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
      timeout: 240_000,
    });

    const doc = await PDFDocument.load(raw);
    const count = doc.getPageCount();
    if (count !== report.totalPages) {
      throw new Error(`O PDF saiu com ${count} páginas, mas a diagramação previa ${report.totalPages}.`);
    }
    const { width, height } = doc.getPage(0).getSize();
    if (Math.abs(width - geo.pageWidth * 72) > 1 || Math.abs(height - geo.pageHeight * 72) > 1) {
      throw new Error(`Tamanho de página inesperado no PDF: ${width.toFixed(1)} x ${height.toFixed(1)} pt.`);
    }

    doc.setTitle(book.title, { showInWindowTitleBar: true });
    if (book.author) doc.setAuthor(book.author);
    if (book.subtitle) doc.setSubject(book.subtitle);
    doc.setLanguage(book.language === "pt" ? "pt-BR" : "en-US");
    doc.setKeywords([theme === "color" ? "interior colorido" : "interior preto e branco", "KDP"]);
    doc.setCreator("Devocional Premium");
    doc.setProducer("Devocional Premium (Chromium + pdf-lib)");

    return { pdf: await doc.save(), report };
  } finally {
    await page.close().catch(() => {});
  }
}
