"""
Custom exception hierarchy for consistent error handling.
All exceptions map to specific HTTP status codes and error codes.
"""

from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error."""

    def __init__(
        self,
        status_code: int,
        error: str,
        code: str,
    ) -> None:
        self.error = error
        self.code = code
        super().__init__(status_code=status_code, detail=error)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, resource: str = "Resource", resource_id: str = "") -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error=detail,
            code="NOT_FOUND",
        )


class PermissionDeniedError(AppError):
    """Permission denied (403)."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error=message,
            code="PERMISSION_DENIED",
        )


class ValidationError(AppError):
    """Validation error (422)."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error=message,
            code="VALIDATION_ERROR",
        )


class AuthenticationError(AppError):
    """Authentication failure (401)."""

    def __init__(self, message: str = "Invalid or expired credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error=message,
            code="AUTHENTICATION_ERROR",
        )


class ConflictError(AppError):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error=message,
            code="CONFLICT",
        )


class FileTooLargeError(AppError):
    """File exceeds size limit (413)."""

    def __init__(self, max_mb: int = 200) -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error=f"File exceeds maximum size of {max_mb}MB",
            code="FILE_TOO_LARGE",
        )


class InvalidFileTypeError(AppError):
    """Unsupported file type (415)."""

    def __init__(self, mime_type: str = "") -> None:
        detail = "Unsupported file type"
        if mime_type:
            detail = f"Unsupported file type: {mime_type}"
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error=detail,
            code="INVALID_FILE_TYPE",
        )


class SSRFError(AppError):
    """SSRF attempt blocked (400)."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="URL targets a restricted network address",
            code="SSRF_BLOCKED",
        )


class ProviderError(AppError):
    """LLM provider error (502)."""

    def __init__(self, message: str = "LLM provider error") -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error=message,
            code="PROVIDER_ERROR",
        )
