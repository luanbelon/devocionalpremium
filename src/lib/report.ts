import { coverDimensions, validateProfile, type CoverDimensions, type InkType, type PaperType, type ProfileValidation } from "./kdp";
import type { Settings } from "./settings";
import type { BookReport, Theme } from "./types";

export interface EditionSummary {
  ink: InkType;
  paper: PaperType;
  validation: ProfileValidation;
  cover: CoverDimensions;
}

export function editionProfile(theme: Theme, settings: Settings): { ink: InkType; paper: PaperType } {
  return theme === "color" ? { ink: settings.colorInk, paper: "white" } : { ink: "black_and_white", paper: settings.bwPaper };
}

export function editionSummary(theme: Theme, report: BookReport, settings: Settings): EditionSummary {
  const { ink, paper } = editionProfile(theme, settings);
  const base = { edition: settings.editionType, trimSize: settings.trimSize, ink, paper, pageCount: report.totalPages };
  return { ink, paper, validation: validateProfile(base), cover: coverDimensions(base) };
}
