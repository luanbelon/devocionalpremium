import { normalizeBookJson } from "../normalize";
import { DEFAULT_SETTINGS, sanitizeSettings, type Settings } from "../settings";
import type { Book } from "../types";

export interface ParsedRequest {
  book: Book | null;
  settings: Settings;
  errors: string[];
  warnings: string[];
}

// Aceita { devocional | book, settings } ou o JSON do devocional diretamente.
export function parseBookRequest(body: unknown): ParsedRequest {
  const obj = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
  const wrapped = obj.devocional ?? obj.book;
  const source = wrapped && typeof wrapped === "object" ? wrapped : body;

  const year = String((obj.settings as Record<string, unknown> | undefined)?.year ?? DEFAULT_SETTINGS.year);
  const result = normalizeBookJson(source, { year });
  const settings = sanitizeSettings(obj.settings, sanitizeSettings(result.settings));

  return { book: result.book, settings, errors: result.errors, warnings: result.warnings };
}

export function jsonError(status: number, message: string, details?: string[]) {
  return Response.json({ error: message, details }, { status });
}
