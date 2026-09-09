"""Seed a demo tenant + admin for browser testing.

Idempotent: if the demo tenant already exists, it prints the existing login
details and exits 0. Reads the database URL from application settings
(``PAEOS_DATABASE_URL``). Intended for local/dev testing only — never for
production data.

Usage:
    python -m scripts.seed_demo            # uses default demo credentials
    DEMO_SLUG=acme DEMO_EMAIL=me@acme.ph python -m scripts.seed_demo
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from paeos_fx.core.config import get_settings
from paeos_fx.core.errors import ConflictError
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.tenancy import Tenant

DEMO_SLUG = os.environ.get("DEMO_SLUG", "farm")
DEMO_NAME = os.environ.get("DEMO_NAME", "Demo Farm Co")
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "admin@demofarm.ph")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "supersecret123")


def main() -> int:
    engine = create_engine(get_settings().database_url, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        existing = session.execute(
            select(Tenant).where(Tenant.slug == DEMO_SLUG)
        ).scalar_one_or_none()
        if existing is not None:
            print(f"Demo tenant '{DEMO_SLUG}' already exists — nothing to do.")
        else:
            try:
                provision_tenant(
                    session, slug=DEMO_SLUG, name=DEMO_NAME,
                    admin_email=DEMO_EMAIL, admin_password=DEMO_PASSWORD,
                )
                session.commit()
                print(f"Provisioned demo tenant '{DEMO_SLUG}'.")
            except ConflictError:
                session.rollback()
                print(f"Demo tenant '{DEMO_SLUG}' already exists — nothing to do.")

    print("\n=== Demo login (use at POST /api/v1/auth/login) ===")
    print(f"  tenant_slug: {DEMO_SLUG}")
    print(f"  email:       {DEMO_EMAIL}")
    print(f"  password:    {DEMO_PASSWORD}")
    print("\nOpen the interactive API docs at:  http://localhost:8000/docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
