"""Fisheries / aquaculture services (Phase 5)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, update

from paeos_fx.agri.geometry import to_geojson_string, validate_geojson_geometry
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.core.pagination import Page, PageParams
from paeos_fx.fisheries.models import (
    AQUACULTURE_CYCLE_WORKFLOW,
    AquacultureCycle,
    AquaHarvestRecord,
    AquaMortalityRecord,
    CultureUnit,
    WaterQualityReading,
)
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService

SRID = 4326


class CultureUnitService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[CultureUnit] = TenantRepository(
            session, CultureUnit, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        name: str,
        unit_type: str = "pond",
        farm_id: uuid.UUID | None = None,
        location_geojson: dict[str, Any] | None = None,
        water_area_sqm: Decimal | None = None,
        area_classification: Classification = Classification.UNKNOWN,
    ) -> CultureUnit:
        unit = CultureUnit(
            code=code, name=name, unit_type=unit_type, farm_id=farm_id,
            water_area_sqm=water_area_sqm,
            area_classification=area_classification.value,
        )
        self.repo.add(unit)
        if location_geojson is not None:
            geom = validate_geojson_geometry(location_geojson, allowed_types=("Point",))
            self.session.execute(
                update(CultureUnit)
                .where(CultureUnit.id == unit.id)
                .values(location=func.ST_SetSRID(
                    func.ST_GeomFromGeoJSON(to_geojson_string(geom)), SRID))
            )
        self.session.flush()
        self._record(action="culture_unit.create", entity_type="CultureUnit",
                     entity_id=str(unit.id), after={"code": code})
        return unit

    def list(self, params: PageParams | None = None) -> Page[CultureUnit]:
        return self.repo.list(params)


class AquacultureCycleService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[AquacultureCycle] = TenantRepository(
            session, AquacultureCycle, self.tenant_id
        )
        self.units: TenantRepository[CultureUnit] = TenantRepository(
            session, CultureUnit, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        culture_unit_id: uuid.UUID,
        species_id: uuid.UUID,
        stocking_count: int = 0,
        stocking_date: dt.date | None = None,
        expected_harvest_date: dt.date | None = None,
    ) -> AquacultureCycle:
        if stocking_count < 0:
            raise BusinessRuleError("stocking_count cannot be negative.")
        self.units.get_or_404(culture_unit_id)
        cycle = AquacultureCycle(
            code=code, culture_unit_id=culture_unit_id, species_id=species_id,
            stocking_count=stocking_count, stocking_date=stocking_date,
            expected_harvest_date=expected_harvest_date,
            status=AQUACULTURE_CYCLE_WORKFLOW.initial,
        )
        self.repo.add(cycle)
        self._record(action="aquaculture_cycle.create", entity_type="AquacultureCycle",
                     entity_id=str(cycle.id), after={"code": code})
        self._emit("aquaculture_cycle.created", {"id": str(cycle.id)})
        return cycle

    def transition(self, cycle_id: uuid.UUID, event: str) -> AquacultureCycle:
        cycle = self.repo.get_or_404(cycle_id)
        before = cycle.status
        cycle.status = AQUACULTURE_CYCLE_WORKFLOW.fire(cycle.status, event)
        self.session.flush()
        self._record(action=f"aquaculture_cycle.{event}", entity_type="AquacultureCycle",
                     entity_id=str(cycle_id),
                     before={"status": before}, after={"status": cycle.status})
        return cycle

    def record_harvest(
        self, *, cycle_id: uuid.UUID, harvest_date: dt.date, quantity: Decimal,
        uom: str, classification: Classification = Classification.MEASURED,
    ) -> AquaHarvestRecord:
        self.repo.get_or_404(cycle_id)
        rec = AquaHarvestRecord(
            tenant_id=self.tenant_id, cycle_id=cycle_id, harvest_date=harvest_date,
            quantity=quantity, uom=uom, classification=classification.value,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="aqua_harvest.record", entity_type="AquaHarvestRecord",
                     entity_id=str(rec.id), after={"cycle_id": str(cycle_id)})
        return rec

    def record_mortality(
        self, *, cycle_id: uuid.UUID, event_date: dt.date, count: int,
        cause_note: str = "",
    ) -> AquaMortalityRecord:
        cycle = self.repo.get_or_404(cycle_id)
        if count <= 0:
            raise BusinessRuleError("Mortality count must be positive.")
        if count > cycle.stocking_count:
            raise BusinessRuleError("Mortality count exceeds stocking count.")
        cycle.stocking_count -= count
        rec = AquaMortalityRecord(
            tenant_id=self.tenant_id, cycle_id=cycle_id, event_date=event_date,
            count=count, cause_note=cause_note,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="aqua_mortality.record", entity_type="AquaMortalityRecord",
                     entity_id=str(rec.id),
                     after={"cycle_id": str(cycle_id), "count": count})
        return rec

    def list(self, params: PageParams | None = None) -> Page[AquacultureCycle]:
        return self.repo.list(params)


class WaterQualityService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.units: TenantRepository[CultureUnit] = TenantRepository(
            session, CultureUnit, self.tenant_id
        )

    def record(
        self, *, culture_unit_id: uuid.UUID, read_at: dt.date, metric_type: str,
        value: Decimal, uom: str,
        classification: Classification = Classification.MEASURED,
    ) -> WaterQualityReading:
        self.units.get_or_404(culture_unit_id)
        rec = WaterQualityReading(
            tenant_id=self.tenant_id, culture_unit_id=culture_unit_id, read_at=read_at,
            metric_type=metric_type, value=value, uom=uom,
            classification=classification.value,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="water_quality.record", entity_type="WaterQualityReading",
                     entity_id=str(rec.id), after={"culture_unit_id": str(culture_unit_id)})
        return rec
