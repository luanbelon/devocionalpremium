export type Language = "en" | "pt";
export type Theme = "color" | "bw";

export interface Card {
  title: string;
  text: string;
}

export interface Day {
  day: number;
  title: string;
  verse: { text: string; reference: string };
  paragraphs: string[];
  heart: Card;
  prayer: Card;
}

export interface GuidanceItem {
  title: string;
  text: string;
}

export interface FrontMatter {
  copyright: string[];
  dedication: string;
  epigraph: { text: string; reference: string };
  introTitle: string;
  intro: string[];
  guidanceTitle: string;
  guidanceIntro: string;
  guidance: GuidanceItem[];
  journeyLabel: string;
}

export interface Book {
  bookId: string;
  title: string;
  subtitle: string;
  author: string;
  language: Language;
  days: Day[];
  frontMatter: FrontMatter;
}

export interface DayReport {
  day: number;
  title: string;
  start: number;
  end: number;
  pages: number;
  cardsAlone: boolean;
}

export interface BookReport {
  totalPages: number;
  frontMatterPages: number;
  trailingBlank: boolean;
  fontSizePt: number;
  lineHeight: number;
  margins: { inside: number; outside: number; top: number; bottom: number };
  days: DayReport[];
  maxDayPages: number;
  overflowDays: number[];
  warnings: string[];
  layoutPasses: number;
  elapsedMs: number;
}
