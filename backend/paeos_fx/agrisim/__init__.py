"""Phase 11 — AgriSim + Optimization + Digital Twins.

Concrete simulation and optimization engines behind the Foundation
``SimulationEngine`` contract. Every result carries a full ``CalculationRecord``
(inputs, units, formula/model, assumptions, reference, model version, validation
status) classified SIMULATION; all parameters are caller-supplied and NO
coefficients/rates/specs are fabricated. Digital-twin projections are ADVISORY
only — there is no actuation or machinery-control path (gates #13/#14).
"""
