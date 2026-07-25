"""
Security utilities: SSRF protection, MIME validation, file size checks.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from app.config import settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError, SSRFError

# ─── SSRF Protection ─────────────────────────────────────────

BLOCKED_NETWORKS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("127.0.0.0/8"),
    ipaddress.IPv4Network("169.254.0.0/16"),
    ipaddress.IPv4Network("0.0.0.0/8"),
    ipaddress.IPv6Network("::1/128"),
    ipaddress.IPv6Network("fe80::/10"),
    ipaddress.IPv6Network("fc00::/7"),
]


def validate_url_ssrf(url: str) -> str:
    """
    Validate a URL is not targeting a private/internal network.
    Returns the URL if safe, raises SSRFError otherwise.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise SSRFError()

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError()

    # Resolve hostname to IP
    try:
        ip_str = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip_str)
    except (socket.gaierror, ValueError) as e:
        raise SSRFError() from e

    # Check against blocked ranges
    for network in BLOCKED_NETWORKS:
        if ip_addr in network:
            raise SSRFError()

    return url


# ─── MIME Validation ──────────────────────────────────────────

ALLOWED_MIME_TYPES: set[str] = {
    # Documents
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/epub+zip",
    # Text
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    # Images
    "image/jpeg",
    "image/png",
    "image/webp",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/x-m4a",
    "audio/mp4",
    "audio/ogg",
}


def validate_mime_type(mime_type: str) -> str:
    """
    Validate MIME type against allowed list.
    Returns the MIME type if valid, raises InvalidFileTypeError otherwise.
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(mime_type)
    return mime_type


def detect_mime_type(file_bytes: bytes) -> str:
    """
    Detect MIME type from file magic bytes.
    Requires python-magic system library.
    """
    import magic

    mime = magic.from_buffer(file_bytes[:8192], mime=True)
    return mime


# ─── File Size Validation ────────────────────────────────────


def validate_file_size(size_bytes: int) -> int:
    """
    Validate file size against the configured maximum.
    Returns size if valid, raises FileTooLargeError otherwise.
    """
    if size_bytes > settings.max_upload_bytes:
        raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)
    return size_bytes
