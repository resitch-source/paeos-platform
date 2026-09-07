"""API v1 aggregate router.

Only foundation endpoints (health/readiness, and a meta endpoint describing the
platform) are mounted. Domain routers are added by their respective phases.
"""

from __future__ import annotations

from fastapi import APIRouter

from paeos_fx import __version__
from paeos_fx.api.v1 import (
    admin_tenants,
    agents,
    agri_masterdata,
    agrisim,
    animal_groups,
    aqua_cycles,
    auth,
    crop_simulations,
    cropping_cycles,
    enablement,
    farms,
    fisheries_masterdata,
    harvests,
    health,
    info,
    integration,
    inventory,
    livestock_masterdata,
    marketplace,
    org_units,
    parcels,
    processing,
    procurement,
    roles,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(info.router)
api_router.include_router(auth.router)
api_router.include_router(admin_tenants.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(org_units.router)
api_router.include_router(agri_masterdata.router)
api_router.include_router(farms.router)
api_router.include_router(parcels.router)
api_router.include_router(cropping_cycles.router)
api_router.include_router(harvests.router)
api_router.include_router(crop_simulations.router)
api_router.include_router(livestock_masterdata.router)
api_router.include_router(animal_groups.router)
api_router.include_router(fisheries_masterdata.router)
api_router.include_router(aqua_cycles.router)
api_router.include_router(inventory.router)
api_router.include_router(procurement.router)
api_router.include_router(processing.router)
api_router.include_router(marketplace.router)
api_router.include_router(enablement.router)
api_router.include_router(agents.router)
api_router.include_router(agrisim.router)
api_router.include_router(integration.router)


@api_router.get("/meta", tags=["meta"])
async def meta() -> dict:
    """Describe the foundation build and its active phase."""
    return {
        "product": "PAEOS",
        "component": "PAEOS-FX Foundation",
        "version": __version__,
        "active_phase": "PHASE_13_COMMERCIALIZATION",
        "domain_phases_started": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    }
