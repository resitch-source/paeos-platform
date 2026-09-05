import uuid

import pytest

from paeos_fx.core.pagination import MAX_PAGE_SIZE, Page, PageParams
from paeos_fx.platform.i18n import Translator, normalize_locale
from paeos_fx.platform.search import InMemorySearchBackend, SearchQuery

pytestmark = pytest.mark.unit


def test_page_params_offsets():
    p = PageParams(page=3, size=20)
    assert p.offset == 40
    assert p.limit == 20


def test_page_params_validation():
    with pytest.raises(ValueError):
        PageParams(page=0)
    with pytest.raises(ValueError):
        PageParams(size=MAX_PAGE_SIZE + 1)


def test_page_pages_calc():
    page = Page(items=[1, 2, 3], total=7, page=1, size=3)
    assert page.pages == 3


def test_normalize_locale():
    assert normalize_locale("en-US") == "en"
    assert normalize_locale("fil") == "fil"
    assert normalize_locale("de") == "en"  # unsupported -> default
    assert normalize_locale(None) == "en"


def test_translator_fallback_and_fil():
    t_en = Translator(locale="en")
    assert t_en.gettext("error.not_found").startswith("The requested")
    t_fil = Translator(locale="fil")
    assert t_fil.gettext("error.not_found") != t_en.gettext("error.not_found")
    # Unknown key returns the key itself.
    assert t_en.gettext("no.such.key") == "no.such.key"


def test_search_isolates_by_tenant():
    backend = InMemorySearchBackend()
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    backend.index(t1, "farm", "f1", {"name": "Palawan Farm"})
    backend.index(t2, "farm", "f2", {"name": "Palawan Estate"})
    hits = backend.search(SearchQuery(tenant_id=t1, text="Palawan"))
    assert len(hits) == 1
    assert hits[0].entity_id == "f1"
