import JSZip from "jszip";
import { buildEpub } from "@/lib/epub";
import { KDP_RULES_VERSION } from "@/lib/kdp";
import { editionSummary } from "@/lib/report";
import { launchBrowser } from "@/lib/server/browser";
import { renderPdf } from "@/lib/server/render-pdf";
import { jsonError, parseBookRequest } from "@/lib/server/request";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

// Automação: recebe o JSON do devocional e devolve um ZIP com
// o miolo colorido, o miolo preto e branco, o EPUB e o relatório KDP.
export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return jsonError(400, "Corpo da requisição não é um JSON válido.");
  }

  const { book, settings, errors, warnings } = parseBookRequest(body);
  if (!book) return jsonError(422, "JSON do devocional inválido.", errors);

  const browser = await launchBrowser();
  try {
    const color = await renderPdf(browser, book, settings, "color");
    const bw = await renderPdf(browser, book, settings, "bw");
    const epub = await buildEpub(book, settings.colorPalette);
    const slug = book.bookId;

    const relatorio = {
      livro: { titulo: book.title, subtitulo: book.subtitle, autor: book.author, idioma: book.language, dias: book.days.length },
      regrasKdp: KDP_RULES_VERSION,
      configuracao: settings,
      avisosDoJson: warnings,
      diagramacao: color.report,
      edicoes: {
        colorida: editionSummary("color", color.report, settings),
        pretoEBranco: editionSummary("bw", bw.report, settings),
      },
    };

    const zip = new JSZip();
    zip.file(`${slug}_interior_colorido-${settings.colorPalette}.pdf`, color.pdf);
    zip.file(`${slug}_interior_preto-e-branco.pdf`, bw.pdf);
    zip.file(`${slug}.epub`, epub);
    zip.file("relatorio-kdp.json", JSON.stringify(relatorio, null, 2));
    const out = await zip.generateAsync({ type: "uint8array", compression: "DEFLATE" });

    return new Response(Buffer.from(out), {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${slug}.zip"`,
        "X-Page-Count": String(color.report.totalPages),
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    return jsonError(500, (e as Error).message);
  } finally {
    await browser.close().catch(() => {});
  }
}
