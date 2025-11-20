"""Custom exceptions for Kapso API integration."""


class KapsoAPIError(Exception):
    """Base exception for Kapso API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class KapsoAuthenticationError(KapsoAPIError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Invalid API token"):
        super().__init__(message, status_code=401)


class KapsoNotFoundError(KapsoAPIError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class KapsoValidationError(KapsoAPIError):
    """Raised when request validation fails (422)."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class KapsoTimeoutError(KapsoAPIError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timeout"):
        super().__init__(message, status_code=None)
