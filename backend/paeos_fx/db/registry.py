"""Import all ORM models so they register on ``Base.metadata``.

Alembic's ``target_metadata`` points at :data:`paeos_fx.db.base.metadata`; this
module guarantees every foundation model is imported before autogenerate runs.
"""

from __future__ import annotations

# noqa: F401 — imports are for side effects (model registration).
from paeos_fx.agri import gis as _agri_gis  # noqa: F401
from paeos_fx.agri import masterdata as _agri_masterdata  # noqa: F401
from paeos_fx.agri import production as _agri_production  # noqa: F401
from paeos_fx.experts import models as _experts_models  # noqa: F401
from paeos_fx.fisheries import masterdata as _fish_masterdata  # noqa: F401
from paeos_fx.fisheries import models as _fish_models  # noqa: F401
from paeos_fx.inventory import models as _inv_models  # noqa: F401
from paeos_fx.livestock import masterdata as _lv_masterdata  # noqa: F401
from paeos_fx.livestock import models as _lv_models  # noqa: F401
from paeos_fx.logistics import models as _log_models  # noqa: F401
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
from paeos_fx.processing import models as _proc_mes_models  # noqa: F401
from paeos_fx.procurement import models as _proc_models  # noqa: F401
from paeos_fx.support import models as _support_models  # noqa: F401
from paeos_fx.trading import models as _trading_models  # noqa: F401
from paeos_fx.training import models as _training_models  # noqa: F401

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
    "cropping_cycle",
    "growth_observation",
    "harvest_record",
    "simulation_run",
    "livestock_species",
    "livestock_breed",
    "animal_group",
    "animal_production_record",
    "animal_mortality_record",
    "animal_health_event",
    "aquatic_species",
    "culture_unit",
    "aquaculture_cycle",
    "water_quality_reading",
    "aqua_harvest_record",
    "aqua_mortality_record",
    "inventory_item",
    "warehouse",
    "storage_location",
    "stock_level",
    "stock_movement",
    "supplier",
    "purchase_order",
    "purchase_order_line",
    "process_definition",
    "process_input",
    "process_output",
    "production_run",
    "quality_check",
    "processing_asset",
    "asset_telemetry",
    "customer",
    "listing",
    "sales_order",
    "sales_order_line",
    "shipment",
    "course",
    "enrollment",
    "support_ticket",
    "ticket_comment",
    "expert_profile",
    "engagement",
)
