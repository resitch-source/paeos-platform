"""Error handling foundation (section V).

Central exception taxonomy and a consistent error envelope. Internal details are
never leaked to clients; a correlation id lets operators trace the real cause.
"""

from __future__ import annotations

from typing import Any


class PaeosError(Exception):
    """Base class for all PAEOS domain/platform errors.

    Attributes:
        code: stable machine-readable error code.
        http_status: default HTTP status for API mapping.
        details: safe, structured, client-facing details.
    """

    code: str = "paeos_error"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_envelope(self, correlation_id: str) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "correlation_id": correlation_id,
            }
        }


class ValidationError(PaeosError):
    code = "validation_error"
    http_status = 422


class NotFoundError(PaeosError):
    code = "not_found"
    http_status = 404


class ConflictError(PaeosError):
    code = "conflict"
    http_status = 409


class AuthenticationError(PaeosError):
    code = "authentication_error"
    http_status = 401


class AuthorizationError(PaeosError):
    code = "authorization_error"
    http_status = 403


class TenantIsolationError(AuthorizationError):
    """Raised when an operation would cross a tenant boundary."""

    code = "tenant_isolation_error"


class BusinessRuleError(PaeosError):
    code = "business_rule_error"
    http_status = 409


class DependencyUnavailableError(PaeosError):
    code = "dependency_unavailable"
    http_status = 503
