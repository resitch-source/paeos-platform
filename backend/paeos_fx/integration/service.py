"""Integration service (Phase 12).

Idempotent inbound-message ingestion. A message is recorded once per
(tenant, system, idempotency_key); re-delivery returns the existing record
without repeating side effects. Registered handlers map a payload into an
existing domain service — the telemetry handler records an asset reading via the
Phase 7 path (records only, MEASURED, no actuation).
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import NotFoundError
from paeos_fx.integration.mappers import TELEMETRY_SYSTEM, TelemetryIngestMapper
from paeos_fx.integration.models import InboundMessage
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.processing.models import ProcessingAsset
from paeos_fx.processing.service import ProcessingAssetService


class IntegrationService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[InboundMessage] = TenantRepository(
            session, InboundMessage, self.tenant_id
        )

    def _existing(self, system: str, idempotency_key: str) -> InboundMessage | None:
        return self.session.execute(
            select(InboundMessage).where(
                InboundMessage.tenant_id == self.tenant_id,
                InboundMessage.system == system,
                InboundMessage.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()

    def ingest(self, *, system: str, idempotency_key: str,
               payload: dict[str, Any] | None = None) -> tuple[InboundMessage, bool]:
        """Ingest a message idempotently. Returns (message, created).

        ``created`` is False when the message was already ingested (dedupe no-op).
        """
        payload = payload or {}
        existing = self._existing(system, idempotency_key)
        if existing is not None:
            return existing, False

        message = InboundMessage(system=system, idempotency_key=idempotency_key,
                                 payload=payload, status="received")
        self.repo.add(message)
        try:
            if system == TELEMETRY_SYSTEM:
                self._handle_telemetry(payload)
            message.status = "processed" if system == TELEMETRY_SYSTEM else "received"
        except Exception as exc:  # noqa: BLE001 - recorded on the ledger, then re-raised
            message.status = "failed"
            message.error = str(exc)
            self.session.flush()
            raise
        self.session.flush()
        self._record(action="integration.ingest", entity_type="InboundMessage",
                     entity_id=str(message.id),
                     after={"system": system, "status": message.status})
        return message, True

    def _handle_telemetry(self, payload: dict[str, Any]) -> None:
        args = TelemetryIngestMapper().to_domain(payload)
        asset = self.session.execute(
            select(ProcessingAsset).where(
                ProcessingAsset.tenant_id == self.tenant_id,
                ProcessingAsset.code == args["asset_code"],
            )
        ).scalar_one_or_none()
        if asset is None:
            raise NotFoundError("Unknown processing asset.",
                                details={"asset_code": args["asset_code"]})
        read_at = args.get("read_at")
        parsed_at = (dt.datetime.fromisoformat(read_at)
                     if isinstance(read_at, str) and read_at else None)
        ProcessingAssetService(self.session, self.ctx).ingest_telemetry(
            asset_id=asset.id, metric=args["metric"], value=Decimal(args["value"]),
            uom=args["uom"], read_at=parsed_at,
        )

    def get(self, message_id: uuid.UUID) -> InboundMessage:
        return self.repo.get_or_404(message_id)

    def list(self, params=None):
        return self.repo.list(params)
