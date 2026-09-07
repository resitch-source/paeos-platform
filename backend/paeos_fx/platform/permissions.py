"""Enterprise-core permission catalog (Phase 1).

These are software authorization constants (not fabricated domain values). They
are seeded into the global ``permission`` table by the onboarding service and
referenced by API guards.
"""

from __future__ import annotations

# Platform-level (cross-tenant) administration.
PLATFORM_TENANT_PROVISION = "platform.tenant.provision"

# Tenant-scoped IAM administration.
IAM_USER_READ = "iam.user.read"
IAM_USER_WRITE = "iam.user.write"
IAM_ROLE_READ = "iam.role.read"
IAM_ROLE_MANAGE = "iam.role.manage"

# Organizational structure.
ORG_UNIT_READ = "org.unit.read"
ORG_UNIT_WRITE = "org.unit.write"

# Agriculture master data + GIS (Phase 2).
AGRI_MASTERDATA_READ = "agri.masterdata.read"
AGRI_MASTERDATA_MANAGE = "agri.masterdata.manage"
AGRI_FARM_READ = "agri.farm.read"
AGRI_FARM_WRITE = "agri.farm.write"
AGRI_PARCEL_READ = "agri.parcel.read"
AGRI_PARCEL_WRITE = "agri.parcel.write"

# Crop production + simulation (Phase 3).
AGRI_PRODUCTION_READ = "agri.production.read"
AGRI_PRODUCTION_WRITE = "agri.production.write"
AGRI_SIMULATION_RUN = "agri.simulation.run"

# Livestock + poultry (Phase 4).
LIVESTOCK_MASTERDATA_READ = "livestock.masterdata.read"
LIVESTOCK_MASTERDATA_MANAGE = "livestock.masterdata.manage"
LIVESTOCK_GROUP_READ = "livestock.group.read"
LIVESTOCK_GROUP_WRITE = "livestock.group.write"
LIVESTOCK_RECORD_WRITE = "livestock.record.write"

# Fisheries + aquaculture (Phase 5).
FISHERIES_MASTERDATA_READ = "fisheries.masterdata.read"
FISHERIES_MASTERDATA_MANAGE = "fisheries.masterdata.manage"
FISHERIES_UNIT_READ = "fisheries.unit.read"
FISHERIES_UNIT_WRITE = "fisheries.unit.write"
FISHERIES_CYCLE_READ = "fisheries.cycle.read"
FISHERIES_CYCLE_WRITE = "fisheries.cycle.write"
FISHERIES_RECORD_WRITE = "fisheries.record.write"

# Inventory + procurement + warehouse (Phase 6).
INVENTORY_ITEM_READ = "inventory.item.read"
INVENTORY_ITEM_MANAGE = "inventory.item.manage"
INVENTORY_WAREHOUSE_READ = "inventory.warehouse.read"
INVENTORY_WAREHOUSE_MANAGE = "inventory.warehouse.manage"
INVENTORY_STOCK_READ = "inventory.stock.read"
INVENTORY_MOVEMENT_WRITE = "inventory.movement.write"
PROCUREMENT_SUPPLIER_MANAGE = "procurement.supplier.manage"
PROCUREMENT_PO_READ = "procurement.po.read"
PROCUREMENT_PO_WRITE = "procurement.po.write"
PROCUREMENT_PO_APPROVE = "procurement.po.approve"
PROCUREMENT_PO_RECEIVE = "procurement.po.receive"

# Processing + MES + digital twin (Phase 7). No machinery-control permission
# exists by design — the twin is advisory only.
PROCESSING_DEFINITION_READ = "processing.definition.read"
PROCESSING_DEFINITION_MANAGE = "processing.definition.manage"
PROCESSING_RUN_READ = "processing.run.read"
PROCESSING_RUN_WRITE = "processing.run.write"
PROCESSING_QUALITY_WRITE = "processing.quality.write"
PROCESSING_ASSET_READ = "processing.asset.read"
PROCESSING_ASSET_MANAGE = "processing.asset.manage"
PROCESSING_TELEMETRY_WRITE = "processing.telemetry.write"
PROCESSING_SIMULATION_RUN = "processing.simulation.run"

# Marketplace + trading + logistics (Phase 8). Trading pricing is financial (#12).
MARKETPLACE_LISTING_READ = "marketplace.listing.read"
MARKETPLACE_LISTING_MANAGE = "marketplace.listing.manage"
TRADING_CUSTOMER_MANAGE = "trading.customer.manage"
TRADING_ORDER_READ = "trading.order.read"
TRADING_ORDER_WRITE = "trading.order.write"
TRADING_ORDER_CONFIRM = "trading.order.confirm"
TRADING_ORDER_FULFILL = "trading.order.fulfill"
LOGISTICS_SHIPMENT_READ = "logistics.shipment.read"
LOGISTICS_SHIPMENT_WRITE = "logistics.shipment.write"

# Training + technical support + expert marketplace (Phase 9).
# Expert engagement fees/rates are financial (#12).
TRAINING_COURSE_READ = "training.course.read"
TRAINING_COURSE_MANAGE = "training.course.manage"
TRAINING_ENROLLMENT_WRITE = "training.enrollment.write"
SUPPORT_TICKET_READ = "support.ticket.read"
SUPPORT_TICKET_WRITE = "support.ticket.write"
SUPPORT_TICKET_RESOLVE = "support.ticket.resolve"
EXPERTS_PROFILE_READ = "experts.profile.read"
EXPERTS_PROFILE_MANAGE = "experts.profile.manage"
EXPERTS_ENGAGEMENT_READ = "experts.engagement.read"
EXPERTS_ENGAGEMENT_WRITE = "experts.engagement.write"

# AgriIntelligence / AI agents (Phase 10). Advisory only — no mutating or
# machinery-control AI permission exists by design (gates #13/#14).
AI_AGENT_RUN = "ai.agent.run"
AI_RECOMMENDATION_READ = "ai.recommendation.read"
AI_RECOMMENDATION_DECIDE = "ai.recommendation.decide"

# AgriSim + optimization + digital twins (Phase 11). Advisory simulation only —
# no actuation/machinery-control permission exists by design (gates #13/#14).
AGRISIM_SCENARIO_RUN = "agrisim.scenario.run"
AGRISIM_SCENARIO_READ = "agrisim.scenario.read"
AGRISIM_OPTIMIZE_RUN = "agrisim.optimize.run"

# IoT + integrations (Phase 12). Inbound records only — no actuation permission.
INTEGRATION_MESSAGE_INGEST = "integration.message.ingest"
INTEGRATION_MESSAGE_READ = "integration.message.read"

# Full catalog seeded per environment.
ENTERPRISE_CORE_PERMISSIONS: dict[str, str] = {
    PLATFORM_TENANT_PROVISION: "Provision new tenants (platform administrators).",
    IAM_USER_READ: "Read users within the tenant.",
    IAM_USER_WRITE: "Create, update, and deactivate users.",
    IAM_ROLE_READ: "Read roles and permissions.",
    IAM_ROLE_MANAGE: "Create roles and grant/revoke permissions.",
    ORG_UNIT_READ: "Read organizational units.",
    ORG_UNIT_WRITE: "Create and modify organizational units.",
    AGRI_MASTERDATA_READ: "Read agriculture master/reference data.",
    AGRI_MASTERDATA_MANAGE: "Create and modify agriculture master data.",
    AGRI_FARM_READ: "Read farms.",
    AGRI_FARM_WRITE: "Create and modify farms.",
    AGRI_PARCEL_READ: "Read land parcels.",
    AGRI_PARCEL_WRITE: "Create and modify land parcels.",
    AGRI_PRODUCTION_READ: "Read cropping cycles and harvests.",
    AGRI_PRODUCTION_WRITE: "Create/advance cropping cycles and record harvests.",
    AGRI_SIMULATION_RUN: "Run crop simulations.",
    LIVESTOCK_MASTERDATA_READ: "Read livestock species/breeds.",
    LIVESTOCK_MASTERDATA_MANAGE: "Create and modify livestock master data.",
    LIVESTOCK_GROUP_READ: "Read animal groups (herds/flocks).",
    LIVESTOCK_GROUP_WRITE: "Create and advance animal groups.",
    LIVESTOCK_RECORD_WRITE: "Record production, mortality, and health events.",
    FISHERIES_MASTERDATA_READ: "Read aquatic species.",
    FISHERIES_MASTERDATA_MANAGE: "Create and modify fisheries master data.",
    FISHERIES_UNIT_READ: "Read culture units (ponds/cages/tanks).",
    FISHERIES_UNIT_WRITE: "Create and modify culture units.",
    FISHERIES_CYCLE_READ: "Read aquaculture cycles.",
    FISHERIES_CYCLE_WRITE: "Create and advance aquaculture cycles.",
    FISHERIES_RECORD_WRITE: "Record water quality, harvests, and mortality.",
    INVENTORY_ITEM_READ: "Read inventory items.",
    INVENTORY_ITEM_MANAGE: "Create and modify inventory items.",
    INVENTORY_WAREHOUSE_READ: "Read warehouses and locations.",
    INVENTORY_WAREHOUSE_MANAGE: "Create and modify warehouses and locations.",
    INVENTORY_STOCK_READ: "Read stock levels and movements.",
    INVENTORY_MOVEMENT_WRITE: "Record stock movements.",
    PROCUREMENT_SUPPLIER_MANAGE: "Manage suppliers.",
    PROCUREMENT_PO_READ: "Read purchase orders.",
    PROCUREMENT_PO_WRITE: "Create and edit purchase orders.",
    PROCUREMENT_PO_APPROVE: "Submit/approve/cancel purchase orders.",
    PROCUREMENT_PO_RECEIVE: "Receive purchase orders into stock.",
    PROCESSING_DEFINITION_READ: "Read process definitions (recipes).",
    PROCESSING_DEFINITION_MANAGE: "Create and modify process definitions.",
    PROCESSING_RUN_READ: "Read production runs.",
    PROCESSING_RUN_WRITE: "Create, start, and complete production runs.",
    PROCESSING_QUALITY_WRITE: "Record quality checks.",
    PROCESSING_ASSET_READ: "Read processing assets and twin state.",
    PROCESSING_ASSET_MANAGE: "Create and modify processing assets.",
    PROCESSING_TELEMETRY_WRITE: "Ingest processing-asset telemetry.",
    PROCESSING_SIMULATION_RUN: "Run processing (mass-balance) simulations.",
    MARKETPLACE_LISTING_READ: "Read marketplace listings.",
    MARKETPLACE_LISTING_MANAGE: "Create and modify marketplace listings.",
    TRADING_CUSTOMER_MANAGE: "Manage customers.",
    TRADING_ORDER_READ: "Read sales orders.",
    TRADING_ORDER_WRITE: "Create and edit sales orders.",
    TRADING_ORDER_CONFIRM: "Confirm/cancel sales orders.",
    TRADING_ORDER_FULFILL: "Fulfill sales orders from stock.",
    LOGISTICS_SHIPMENT_READ: "Read shipments.",
    LOGISTICS_SHIPMENT_WRITE: "Create and advance shipments.",
    TRAINING_COURSE_READ: "Read training courses.",
    TRAINING_COURSE_MANAGE: "Create and modify training courses.",
    TRAINING_ENROLLMENT_WRITE: "Enroll learners and advance enrollments.",
    SUPPORT_TICKET_READ: "Read support tickets.",
    SUPPORT_TICKET_WRITE: "Create, comment on, and assign support tickets.",
    SUPPORT_TICKET_RESOLVE: "Resolve, reopen, close, or cancel support tickets.",
    EXPERTS_PROFILE_READ: "Read expert profiles.",
    EXPERTS_PROFILE_MANAGE: "Create and modify expert profiles.",
    EXPERTS_ENGAGEMENT_READ: "Read expert engagements.",
    EXPERTS_ENGAGEMENT_WRITE: "Create and advance expert engagements.",
    AI_AGENT_RUN: "Run advisory AI agents.",
    AI_RECOMMENDATION_READ: "Read AI recommendations.",
    AI_RECOMMENDATION_DECIDE: "Accept or reject AI recommendations (human decision).",
    AGRISIM_SCENARIO_RUN: "Run AgriSim simulation scenarios.",
    AGRISIM_SCENARIO_READ: "Read AgriSim scenario runs.",
    AGRISIM_OPTIMIZE_RUN: "Run optimization models (EOQ, allocation).",
    INTEGRATION_MESSAGE_INGEST: "Ingest inbound integration messages (e.g. IoT telemetry).",
    INTEGRATION_MESSAGE_READ: "Read inbound integration messages.",
}

# Permissions granted to the seeded TENANT_ADMIN system role (tenant-scoped;
# excludes platform-level provisioning).
TENANT_ADMIN_PERMISSIONS: tuple[str, ...] = (
    IAM_USER_READ,
    IAM_USER_WRITE,
    IAM_ROLE_READ,
    IAM_ROLE_MANAGE,
    ORG_UNIT_READ,
    ORG_UNIT_WRITE,
    AGRI_MASTERDATA_READ,
    AGRI_MASTERDATA_MANAGE,
    AGRI_FARM_READ,
    AGRI_FARM_WRITE,
    AGRI_PARCEL_READ,
    AGRI_PARCEL_WRITE,
    AGRI_PRODUCTION_READ,
    AGRI_PRODUCTION_WRITE,
    AGRI_SIMULATION_RUN,
    LIVESTOCK_MASTERDATA_READ,
    LIVESTOCK_MASTERDATA_MANAGE,
    LIVESTOCK_GROUP_READ,
    LIVESTOCK_GROUP_WRITE,
    LIVESTOCK_RECORD_WRITE,
    FISHERIES_MASTERDATA_READ,
    FISHERIES_MASTERDATA_MANAGE,
    FISHERIES_UNIT_READ,
    FISHERIES_UNIT_WRITE,
    FISHERIES_CYCLE_READ,
    FISHERIES_CYCLE_WRITE,
    FISHERIES_RECORD_WRITE,
    INVENTORY_ITEM_READ,
    INVENTORY_ITEM_MANAGE,
    INVENTORY_WAREHOUSE_READ,
    INVENTORY_WAREHOUSE_MANAGE,
    INVENTORY_STOCK_READ,
    INVENTORY_MOVEMENT_WRITE,
    PROCUREMENT_SUPPLIER_MANAGE,
    PROCUREMENT_PO_READ,
    PROCUREMENT_PO_WRITE,
    PROCUREMENT_PO_APPROVE,
    PROCUREMENT_PO_RECEIVE,
    PROCESSING_DEFINITION_READ,
    PROCESSING_DEFINITION_MANAGE,
    PROCESSING_RUN_READ,
    PROCESSING_RUN_WRITE,
    PROCESSING_QUALITY_WRITE,
    PROCESSING_ASSET_READ,
    PROCESSING_ASSET_MANAGE,
    PROCESSING_TELEMETRY_WRITE,
    PROCESSING_SIMULATION_RUN,
    MARKETPLACE_LISTING_READ,
    MARKETPLACE_LISTING_MANAGE,
    TRADING_CUSTOMER_MANAGE,
    TRADING_ORDER_READ,
    TRADING_ORDER_WRITE,
    TRADING_ORDER_CONFIRM,
    TRADING_ORDER_FULFILL,
    LOGISTICS_SHIPMENT_READ,
    LOGISTICS_SHIPMENT_WRITE,
    TRAINING_COURSE_READ,
    TRAINING_COURSE_MANAGE,
    TRAINING_ENROLLMENT_WRITE,
    SUPPORT_TICKET_READ,
    SUPPORT_TICKET_WRITE,
    SUPPORT_TICKET_RESOLVE,
    EXPERTS_PROFILE_READ,
    EXPERTS_PROFILE_MANAGE,
    EXPERTS_ENGAGEMENT_READ,
    EXPERTS_ENGAGEMENT_WRITE,
    AI_AGENT_RUN,
    AI_RECOMMENDATION_READ,
    AI_RECOMMENDATION_DECIDE,
    AGRISIM_SCENARIO_RUN,
    AGRISIM_SCENARIO_READ,
    AGRISIM_OPTIMIZE_RUN,
    INTEGRATION_MESSAGE_INGEST,
    INTEGRATION_MESSAGE_READ,
)

TENANT_ADMIN_ROLE_CODE = "TENANT_ADMIN"
PLATFORM_ADMIN_ROLE_CODE = "PLATFORM_ADMIN"
