"""Agriculture services (Phase 2): master data + GIS.

Master-data services are generic CRUD over the reference catalogs. GIS services
accept GeoJSON and delegate geometry construction to PostGIS
(``ST_GeomFromGeoJSON``); derived areas are computed with ``ST_Area`` over the
geography cast and recorded with an explicit provenance classification.
"""

from __future__ import annotations

import uuid
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select, update

from paeos_fx.agri.geometry import to_geojson_string, validate_geojson_geometry
from paeos_fx.agri.gis import Farm, LandParcel
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import Page, PageParams
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService

SRID = 4326


class MasterDataService(DomainService):
    """Generic tenant-scoped CRUD for an agriculture master-data model."""

    def __init__(self, session, ctx: ExecutionContext, model: type):
        super().__init__(session, ctx)
        self.model = model
        self.repo: TenantRepository[Any] = TenantRepository(
            session, model, self.tenant_id
        )

    def create(self, **fields: Any):
        entity = self.model(**fields)
        self.repo.add(entity)
        table_name = getattr(self.model, "__tablename__", self.model.__name__)
        self._record(
            action=f"{table_name}.create",
            entity_type=self.model.__name__,
            entity_id=str(entity.id),
            after={"code": fields.get("code")},
        )
        return entity

    def get(self, entity_id: uuid.UUID):
        return self.repo.get_or_404(entity_id)

    def list(self, params: PageParams | None = None) -> Page[Any]:
        return self.repo.list(params)


class FarmService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Farm] = TenantRepository(
            session, Farm, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        name: str,
        org_unit_id: uuid.UUID | None = None,
        admin_area_id: uuid.UUID | None = None,
        location_geojson: dict[str, Any] | None = None,
        area_hectares: Any | None = None,
        area_classification: Classification = Classification.UNKNOWN,
    ) -> Farm:
        farm = Farm(
            code=code,
            name=name,
            org_unit_id=org_unit_id,
            admin_area_id=admin_area_id,
            area_hectares=area_hectares,
            area_classification=area_classification.value,
        )
        self.repo.add(farm)
        if location_geojson is not None:
            geom = validate_geojson_geometry(location_geojson, allowed_types=("Point",))
            self.session.execute(
                update(Farm)
                .where(Farm.id == farm.id)
                .values(
                    location=func.ST_SetSRID(
                        func.ST_GeomFromGeoJSON(to_geojson_string(geom)), SRID
                    )
                )
            )
        self.session.flush()
        self._record(action="farm.create", entity_type="Farm",
                     entity_id=str(farm.id), after={"code": code})
        self._emit("farm.created", {"id": str(farm.id)})
        return farm

    def list(self, params: PageParams | None = None) -> Page[Farm]:
        return self.repo.list(params)


class ParcelService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[LandParcel] = TenantRepository(
            session, LandParcel, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        name: str,
        farm_id: uuid.UUID,
        soil_type_id: uuid.UUID | None = None,
        land_use_type_id: uuid.UUID | None = None,
        boundary_geojson: dict[str, Any] | None = None,
    ) -> LandParcel:
        parcel = LandParcel(
            code=code,
            name=name,
            farm_id=farm_id,
            soil_type_id=soil_type_id,
            land_use_type_id=land_use_type_id,
        )
        self.repo.add(parcel)
        if boundary_geojson is not None:
            geom = validate_geojson_geometry(
                boundary_geojson, allowed_types=("Polygon", "MultiPolygon")
            )
            geojson_str = to_geojson_string(geom)
            # Store boundary as a MULTIPOLYGON in EPSG:4326.
            self.session.execute(
                update(LandParcel)
                .where(LandParcel.id == parcel.id)
                .values(
                    boundary=func.ST_Multi(
                        func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), SRID)
                    )
                )
            )
            self.session.flush()
            # Derive area (sqm) from the stored geometry via the geography cast.
            area = self.session.execute(
                select(func.ST_Area(cast(LandParcel.boundary, Geography))).where(
                    LandParcel.id == parcel.id
                )
            ).scalar_one()
            self.session.execute(
                update(LandParcel)
                .where(LandParcel.id == parcel.id)
                .values(
                    area_sqm=area,
                    area_classification=Classification.ESTIMATE.value,
                )
            )
        self.session.flush()
        self._record(action="parcel.create", entity_type="LandParcel",
                     entity_id=str(parcel.id), after={"code": code})
        return parcel

    def list(self, params: PageParams | None = None) -> Page[LandParcel]:
        return self.repo.list(params)
