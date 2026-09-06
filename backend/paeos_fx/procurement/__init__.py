"""Phase 6 — Procurement.

Suppliers and purchase orders with line pricing (Foundation ``Money`` type,
integer minor units). Receiving a PO posts stock through the central
``InventoryService`` — never bypassing it. Scope is limited to PO + receipt +
pricing; no general ledger, tax engine, or payments.
"""
