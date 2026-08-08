from __future__ import annotations


class ApplicationError(Exception):
    """Base class for domain and application-level errors."""


class NotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""


class BusinessRuleError(ApplicationError):
    """Raised when a business rule is violated."""
