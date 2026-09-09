# PAEOS — Commercialization

This document frames how PAEOS 1.0.0 can be packaged for customers. It describes
**capability bundles** only. Pricing, discounts, and contract terms are business
decisions and are deliberately left **UNDECIDED** here — no prices, tiers, or
figures are fabricated (per the no-fabrication policy). Fill these in through the
appropriate business process.

## Capability bundles
Bundles map to the capability groups surfaced by `GET /api/v1/info`
(`capability_bundles`) and defined in `paeos_fx/platform/release.py`.

### Core
Enterprise foundation for any deployment:
- Enterprise core, IAM/RBAC, multi-tenant isolation (RLS), audit trail.

### Agriculture
Domain capabilities for producers:
- Crop production + master data, GIS (farms/parcels), crop simulation,
  livestock/poultry, fisheries/aquaculture.

### Enterprise
Operations, marketplace, enablement, and intelligence:
- Inventory + procurement, processing/MES, trading + logistics, training,
  technical support, expert marketplace, AgriIntelligence (advisory AI), AgriSim
  optimization, and IoT/integration ingestion.

## Editions (structure only)
Suggested edition structure — **capabilities listed, pricing undecided**:

| Edition     | Bundles included                     | Price          |
|-------------|--------------------------------------|----------------|
| Starter     | Core                                 | UNDECIDED      |
| Producer    | Core + Agriculture                   | UNDECIDED      |
| Enterprise  | Core + Agriculture + Enterprise      | UNDECIDED      |

## Deployment models (structure only)
- Single-tenant dedicated, or multi-tenant shared (isolation enforced by RLS).
- Terms, SLAs, and support levels: **UNDECIDED** (business decision).

## Notes
- Any billing/payment functionality is out of scope for 1.0.0 and would be a
  gated financial-logic change (controller gate #12).
- Commercial terms must be set by the business; this document is a capability
  map, not a price list.
