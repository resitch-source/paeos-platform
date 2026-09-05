// Minimal localization for the frontend shell (en + fil), mirroring the
// backend's supported locales. Domain strings are added by their phases.

export type Locale = "en" | "fil";

type Catalog = Record<string, string>;

const catalogs: Record<Locale, Catalog> = {
  en: {
    "app.title": "PAEOS-FX",
    "app.subtitle": "Philippine Agriculture Enterprise Operating System",
    "status.foundation": "Foundation framework active. No domain phase started.",
  },
  fil: {
    "app.title": "PAEOS-FX",
    "app.subtitle": "Sistema ng Operasyon ng Negosyong Agrikultura ng Pilipinas",
    "status.foundation":
      "Aktibo ang foundation framework. Wala pang domain phase na sinimulan.",
  },
};

export function t(key: string, locale: Locale = "en"): string {
  return catalogs[locale][key] ?? catalogs.en[key] ?? key;
}
