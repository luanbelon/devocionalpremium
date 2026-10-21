import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Devocional Premium · Gerador KDP",
  description: "Gere o miolo colorido, o miolo preto e branco e o EPUB do seu devocional a partir de um JSON.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
