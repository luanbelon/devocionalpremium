import { launchBrowser } from "@/lib/server/browser";
import { renderPdf } from "@/lib/server/render-pdf";
import { jsonError, parseBookRequest } from "@/lib/server/request";
import type { Theme } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return jsonError(400, "Corpo da requisição não é um JSON válido.");
  }

  const { book, settings, errors } = parseBookRequest(body);
  if (!book) return jsonError(422, "JSON do devocional inválido.", errors);

  const theme: Theme = (body as { theme?: string }).theme === "bw" ? "bw" : "color";
  const browser = await launchBrowser();
  try {
    const { pdf, report } = await renderPdf(browser, book, settings, theme);
    const suffix = theme === "color" ? `colorido-${settings.colorPalette}` : "preto-e-branco";
    return new Response(Buffer.from(pdf), {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${book.bookId}_interior_${suffix}.pdf"`,
        "X-Page-Count": String(report.totalPages),
        "X-Layout-Ms": String(report.elapsedMs),
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    return jsonError(500, (e as Error).message);
  } finally {
    await browser.close().catch(() => {});
  }
}
