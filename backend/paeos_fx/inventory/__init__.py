"""Phase 6 — Inventory + Warehouse (central stock-movement service).

All stock changes flow through ``InventoryService`` — the single authorized,
audited path. No domain code mutates stock levels directly.
"""
