"""Phase 8 — Marketplace + Trading.

Marketplace listings, customers, and sales orders with pricing. Fulfilling a
sales order posts stock OUT through the central ``InventoryService`` — never
bypassing it. Financial scope is line pricing only (Money, integer minor units);
no payments, AR settlement, tax, or GL.
"""
