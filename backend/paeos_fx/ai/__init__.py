"""Phase 10 — AgriIntelligence / AI Agents.

Concrete, tenant-scoped AI agents built ON the Foundation AI-safety chain
(``paeos_fx.interfaces.ai``): AI reaches data only through permission-checked,
read-only ``AuthorizedTool``s, produces advisory ``AIRecommendation``s that are
persisted and NEVER auto-applied, and requires a human decision to accept or
reject. No LLM/provider is wired; reasoning is deterministic and every output is
classified with an uncertainty note (NO-FABRICATION). No mutating or
safety-critical tool is registered (gates #13/#14 respected).
"""
