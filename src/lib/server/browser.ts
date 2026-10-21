import fs from "node:fs";
import type { Browser } from "puppeteer-core";

const LOCAL_CANDIDATES: Record<string, string[]> = {
  win32: [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  ],
  darwin: [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  ],
  linux: ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"],
};

const COMMON_ARGS = ["--font-render-hinting=none", "--disable-gpu"];

function localExecutable(): string | null {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  return (LOCAL_CANDIDATES[process.platform] ?? []).find((p) => fs.existsSync(p)) ?? null;
}

export async function launchBrowser(): Promise<Browser> {
  const puppeteer = (await import("puppeteer-core")).default;
  const serverless = !!(process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME);
  const local = serverless ? null : localExecutable();

  if (local) {
    return puppeteer.launch({ executablePath: local, headless: true, args: COMMON_ARGS });
  }

  if (process.platform !== "linux") {
    throw new Error("Chrome/Edge não encontrado. Instale o Google Chrome ou defina CHROME_PATH.");
  }

  const chromium = (await import("@sparticuz/chromium")).default;
  return puppeteer.launch({
    args: puppeteer.defaultArgs({ args: [...chromium.args, ...COMMON_ARGS], headless: "shell" }),
    executablePath: await chromium.executablePath(),
    headless: "shell",
  });
}
