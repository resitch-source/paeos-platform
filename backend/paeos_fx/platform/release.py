"""Release manifest (Phase 13).

A factual description of the delivered platform: the release version and the
completed phases with their capability summaries. Content mirrors what is
actually implemented (see ``CHANGELOG.md``); nothing here is fabricated. Build
metadata (git SHA) is read from the environment and defaults to ``"unknown"``
rather than being invented.
"""

from __future__ import annotations

import os

from paeos_fx import __version__

RELEASE_VERSION = __version__

# Ordered manifest of completed phases (FX Foundation through Phase 13).
PHASE_MANIFEST: tuple[dict[str, str], ...] = (
    {"phase": "FX", "name": "PAEOS-FX Foundation",
     "summary": "Horizontal platform: config, DB/RLS, IAM/RBAC, audit, events, "
                "workflow, approval, currency, master-data, interfaces."},
    {"phase": "0", "name": "Project Governance",
     "summary": "Contribution/policy docs, templates, pre-commit, session hook."},
    {"phase": "1", "name": "Enterprise Core",
     "summary": "JWT auth, RBAC pipeline, tenant onboarding, IAM, org units."},
    {"phase": "2", "name": "Agriculture Master Data + GIS",
     "summary": "Crop/soil catalogs; PostGIS farms/parcels with GeoJSON import."},
    {"phase": "3", "name": "Crop Production + Simulation",
     "summary": "Cropping cycles, harvests, and the GDD simulation engine."},
    {"phase": "4", "name": "Livestock + Poultry",
     "summary": "Species/breeds; animal groups with production/mortality/health."},
    {"phase": "5", "name": "Fisheries + Aquaculture",
     "summary": "Aquatic species; culture units; aquaculture cycles + records."},
    {"phase": "6", "name": "Inventory + Procurement + Warehouse",
     "summary": "Central inventory service; suppliers and purchase orders (Money)."},
    {"phase": "7", "name": "Processing + MES + Coconut Oil Digital Twin",
     "summary": "Recipes/runs via central inventory; advisory mass-balance twin."},
    {"phase": "8", "name": "Marketplace + Trading + Logistics",
     "summary": "Customers, listings, sales orders (Money), shipments."},
    {"phase": "9", "name": "Training + Technical Support + Expert Marketplace",
     "summary": "Courses/enrollments, support tickets, expert engagements (Money)."},
    {"phase": "10", "name": "AgriIntelligence / AI Agents",
     "summary": "Advisory agents via guarded read-only tools; human-decided."},
    {"phase": "11", "name": "AgriSim + Optimization + Digital Twins",
     "summary": "EOQ/allocation + engine registry; advisory twin projections."},
    {"phase": "12", "name": "IoT + Integrations + Security + Prod Hardening",
     "summary": "Idempotent inbound-message ledger; opt-in rate limiting."},
    {"phase": "13", "name": "Commercialization + Customer Deployment",
     "summary": "Release manifest, build-info endpoint, deployment docs."},
)

# Capability groupings referenced by the commercialization documentation. These
# are capability bundles only — pricing is a deferred business decision and is
# never fabricated here.
CAPABILITY_BUNDLES: dict[str, tuple[str, ...]] = {
    "core": ("enterprise-core", "iam-rbac", "multi-tenant-rls", "audit"),
    "agriculture": ("crops", "livestock", "fisheries", "gis", "simulation"),
    "enterprise": ("inventory", "procurement", "processing-mes", "trading",
                   "logistics", "training", "support", "experts",
                   "agri-intelligence", "agrisim", "integrations"),
}


def build_sha() -> str:
    """Return the build's git SHA from the environment, or ``"unknown"``."""
    return os.environ.get("PAEOS_BUILD_SHA", "unknown")
