"""Localization engine (section S).

Locale resolution and message catalog lookup for the supported locales
(English + Filipino at the foundation). Timezone handling defaults to
Asia/Manila. Catalogs are simple in-memory dicts here; a compiled catalog
backend (Babel .mo) can replace the lookup without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "fil")
DEFAULT_TIMEZONE = "Asia/Manila"

# Foundation-level message catalog (framework strings only, no domain content).
_CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "error.not_found": "The requested resource was not found.",
        "error.unauthorized": "You are not authorized to perform this action.",
        "error.validation": "The submitted data is invalid.",
    },
    "fil": {
        "error.not_found": "Hindi natagpuan ang hiniling na mapagkukunan.",
        "error.unauthorized": "Wala kang pahintulot na gawin ang aksyong ito.",
        "error.validation": "Hindi wasto ang isinumiteng datos.",
    },
}


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE
    base = locale.split("-")[0].split("_")[0].lower()
    return base if base in SUPPORTED_LOCALES else DEFAULT_LOCALE


@dataclass
class Translator:
    locale: str = DEFAULT_LOCALE
    catalog: dict[str, dict[str, str]] = field(default_factory=lambda: _CATALOG)

    def gettext(self, key: str, **params: object) -> str:
        locale = normalize_locale(self.locale)
        table = self.catalog.get(locale, {})
        template = table.get(key) or self.catalog[DEFAULT_LOCALE].get(key, key)
        try:
            return template.format(**params) if params else template
        except (KeyError, IndexError):
            return template
