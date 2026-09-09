"""Processing / MES services (Phase 7).

Recipes, production runs (consume inputs and produce outputs through the central
``InventoryService``), quality checks, asset telemetry, and the advisory
mass-balance simulation. No machinery is actuated.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from paeos_fx.agri.production import SimulationRun
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.interfaces.digital_twin import TelemetrySample
from paeos_fx.interfaces.simulation import SimulationRequest, SimulationResult
from paeos_fx.inventory.models import MovementType
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.processing.models import (
    PRODUCTION_RUN_WORKFLOW,
    AssetTelemetry,
    ProcessDefinition,
    ProcessingAsset,
    ProcessInput,
    ProcessOutput,
    ProductionRun,
    QualityCheck,
)
from paeos_fx.processing.simulation import MassBalanceModel
from paeos_fx.processing.twin import CoconutOilTwin


class ProcessDefinitionService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[ProcessDefinition] = TenantRepository(
            session, ProcessDefinition, self.tenant_id
        )

    def create(self, *, code: str, name: str, description: str = "") -> ProcessDefinition:
        d = ProcessDefinition(code=code, name=name, description=description)
        self.repo.add(d)
        self._record(action="process_definition.create", entity_type="ProcessDefinition",
                     entity_id=str(d.id), after={"code": code})
        return d

    def add_input(self, *, definition_id: uuid.UUID, item_id: uuid.UUID,
                  quantity_per_batch: Decimal) -> ProcessInput:
        self.repo.get_or_404(definition_id)
        row = ProcessInput(tenant_id=self.tenant_id, definition_id=definition_id,
                           item_id=item_id, quantity_per_batch=Decimal(quantity_per_batch))
        self.session.add(row)
        self.session.flush()
        return row

    def add_output(self, *, definition_id: uuid.UUID, item_id: uuid.UUID,
                   quantity_per_batch: Decimal) -> ProcessOutput:
        self.repo.get_or_404(definition_id)
        row = ProcessOutput(tenant_id=self.tenant_id, definition_id=definition_id,
                            item_id=item_id, quantity_per_batch=Decimal(quantity_per_batch))
        self.session.add(row)
        self.session.flush()
        return row


class ProductionRunService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[ProductionRun] = TenantRepository(
            session, ProductionRun, self.tenant_id
        )

    def create(self, *, code: str, definition_id: uuid.UUID, warehouse_id: uuid.UUID,
               batch_size: Decimal = Decimal("1")) -> ProductionRun:
        if Decimal(batch_size) <= 0:
            raise BusinessRuleError("batch_size must be positive.")
        run = ProductionRun(
            code=code, definition_id=definition_id, warehouse_id=warehouse_id,
            batch_size=Decimal(batch_size), status=PRODUCTION_RUN_WORKFLOW.initial,
        )
        self.repo.add(run)
        self._record(action="production_run.create", entity_type="ProductionRun",
                     entity_id=str(run.id), after={"code": code})
        return run

    def start(self, run_id: uuid.UUID) -> ProductionRun:
        run = self.repo.get_or_404(run_id)
        run.status = PRODUCTION_RUN_WORKFLOW.fire(run.status, "start")
        run.started_at = dt.datetime.now(dt.UTC)
        self.session.flush()
        self._record(action="production_run.start", entity_type="ProductionRun",
                     entity_id=str(run_id))
        return run

    def complete(self, run_id: uuid.UUID) -> ProductionRun:
        """Complete a run: consume inputs and produce outputs via inventory."""
        run = self.repo.get_or_404(run_id)
        if run.status != "running":
            raise BusinessRuleError("Only a running run can be completed.")
        inputs = self.session.execute(
            select(ProcessInput).where(
                ProcessInput.tenant_id == self.tenant_id,
                ProcessInput.definition_id == run.definition_id,
            )
        ).scalars().all()
        outputs = self.session.execute(
            select(ProcessOutput).where(
                ProcessOutput.tenant_id == self.tenant_id,
                ProcessOutput.definition_id == run.definition_id,
            )
        ).scalars().all()

        inventory = InventoryService(self.session, self.ctx)
        # Consume inputs first (fails closed if insufficient stock).
        for inp in inputs:
            inventory.record_movement(
                item_id=inp.item_id, warehouse_id=run.warehouse_id,
                movement_type=MovementType.OUT,
                quantity=inp.quantity_per_batch * run.batch_size,
                reference=f"RUN:{run.code}",
            )
        for out in outputs:
            inventory.record_movement(
                item_id=out.item_id, warehouse_id=run.warehouse_id,
                movement_type=MovementType.IN,
                quantity=out.quantity_per_batch * run.batch_size,
                reference=f"RUN:{run.code}",
            )
        run.status = PRODUCTION_RUN_WORKFLOW.fire(run.status, "complete")
        run.completed_at = dt.datetime.now(dt.UTC)
        self.session.flush()
        self._record(action="production_run.complete", entity_type="ProductionRun",
                     entity_id=str(run_id), after={"status": run.status})
        self._emit("production_run.completed", {"id": str(run_id)})
        return run

    def record_quality(self, *, run_id: uuid.UUID, metric_type: str, value: Decimal,
                       uom: str,
                       classification: Classification = Classification.MEASURED) -> QualityCheck:
        self.repo.get_or_404(run_id)
        qc = QualityCheck(
            tenant_id=self.tenant_id, run_id=run_id, metric_type=metric_type,
            value=Decimal(value), uom=uom, classification=classification.value,
        )
        self.session.add(qc)
        self.session.flush()
        self._record(action="quality_check.record", entity_type="QualityCheck",
                     entity_id=str(qc.id), after={"run_id": str(run_id)})
        return qc


class ProcessingAssetService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[ProcessingAsset] = TenantRepository(
            session, ProcessingAsset, self.tenant_id
        )

    def create(self, *, code: str, name: str, asset_type: str = "processor") -> ProcessingAsset:
        asset = ProcessingAsset(code=code, name=name, asset_type=asset_type)
        self.repo.add(asset)
        self._record(action="processing_asset.create", entity_type="ProcessingAsset",
                     entity_id=str(asset.id), after={"code": code})
        return asset

    def ingest_telemetry(self, *, asset_id: uuid.UUID, metric: str, value: Decimal,
                         uom: str, read_at: dt.datetime | None = None) -> AssetTelemetry:
        self.repo.get_or_404(asset_id)
        row = AssetTelemetry(
            tenant_id=self.tenant_id, asset_id=asset_id, metric=metric,
            value=Decimal(value), uom=uom, read_at=read_at or dt.datetime.now(dt.UTC),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def twin_state(self, asset_id: uuid.UUID):
        """Build an advisory twin from the asset's telemetry (latest per metric)."""
        self.repo.get_or_404(asset_id)
        rows = self.session.execute(
            select(AssetTelemetry).where(
                AssetTelemetry.tenant_id == self.tenant_id,
                AssetTelemetry.asset_id == asset_id,
            ).order_by(AssetTelemetry.read_at)
        ).scalars().all()
        twin = CoconutOilTwin(str(asset_id))
        for r in rows:
            twin.ingest(TelemetrySample(metric=r.metric, value=float(r.value), unit=r.uom,
                                        at=r.read_at))
        return twin.state()


class ProcessSimulationService(DomainService):
    def run_mass_balance(self, *, scenario: str, parameters: dict[str, Any]
                         ) -> tuple[SimulationRun, SimulationResult]:
        model = MassBalanceModel()
        result = model.run(SimulationRequest(scenario=scenario, parameters=parameters))
        record = asdict(result.record)
        record["validation_status"] = result.record.validation_status.value
        run = SimulationRun(
            tenant_id=self.tenant_id, cycle_id=None, model_name=model.name,
            model_version=model.version, scenario=scenario,
            ran_at=dt.datetime.now(dt.UTC), record=record,
        )
        self.session.add(run)
        self.session.flush()
        self._record(action="processing.simulation.run", entity_type="SimulationRun",
                     entity_id=str(run.id), after={"model": model.name})
        return run, result
