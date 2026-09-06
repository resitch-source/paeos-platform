"""Import all ORM models so they register on ``Base.metadata``.

Alembic's ``target_metadata`` points at :data:`paeos_fx.db.base.metadata`; this
module guarantees every foundation model is imported before autogenerate runs.
"""

from __future__ import annotations

# noqa: F401 — imports are for side effects (model registration).
from paeos_fx.agri import gis as _agri_gis  # noqa: F401
from paeos_fx.agri import masterdata as _agri_masterdata  # noqa: F401
from paeos_fx.platform import approval as _approval  # noqa: F401
from paeos_fx.platform import audit as _audit  # noqa: F401
from paeos_fx.platform import documents as _documents  # noqa: F401
from paeos_fx.platform import events as _events  # noqa: F401
from paeos_fx.platform import iam as _iam  # noqa: F401
from paeos_fx.platform import notifications as _notifications  # noqa: F401
from paeos_fx.platform import numbering as _numbering  # noqa: F401
from paeos_fx.platform import org as _org  # noqa: F401
from paeos_fx.platform import tenancy as _tenancy  # noqa: F401
from paeos_fx.platform import workflow as _workflow  # noqa: F401

# Tenant-owned tables subject to Row-Level Security policies.
TENANT_OWNED_TABLES: tuple[str, ...] = (
    "tenant_setting",
    "app_user",
    "role",
    "role_permission",
    "user_role",
    "audit_log",
    "outbox_event",
    "number_sequence",
    "workflow_instance",
    "approval_request",
    "approval_step",
    "document",
    "notification",
    "org_unit",
    "agri_crop_category",
    "agri_crop",
    "agri_crop_variety",
    "agri_soil_type",
    "agri_land_use_type",
    "agri_admin_area",
    "agri_farm",
    "agri_land_parcel",
)
