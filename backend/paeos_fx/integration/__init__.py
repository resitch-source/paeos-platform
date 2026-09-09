"""Phase 12 — IoT + Integrations.

Concrete integration framework behind the Foundation integration contract
(``interfaces.integration``): an idempotent inbound-message ledger that routes
external messages through a mapper into existing domain services (records only —
e.g. IoT telemetry into the Phase 7 asset-telemetry path). There is NO actuation
and NO external network egress in this build; the default outbound adapter
refuses to fabricate a delivery (NO-FABRICATION).
"""
