"""Phase 7 — Processing + MES + Coconut Oil Digital Twin.

Manufacturing execution (recipes, production runs that consume/produce stock
through the central inventory service, quality checks) and an advisory
coconut-oil digital twin (telemetry, state, mass-balance simulation).

SAFETY: this package creates NO autonomous machinery-control path. The twin's
control channel remains inert and human-approval-gated (see the Foundation
``interfaces.digital_twin.guard_control``). Processing yields are advisory
simulations with caller-supplied parameters — no coefficients are fabricated.
"""
