"""
Image processor — extracts text from images via OCR or provides image metadata.

Supports common image formats: JPG, PNG, GIF, BMP, TIFF, WebP, etc.
"""

from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageFile

# Allow loading of truncated images (handles some corrupt images gracefully)
ImageFile.LOAD_TRUNCATED_IMAGES = True

from app.core.constants import SourceType  # noqa: E402
from app.core.exceptions import ValidationError  # noqa: E402
from app.core.logging import logger  # noqa: E402
from app.services.parsers import BaseParser  # noqa: E402

# Optional OCR dependency
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger = logger  # Keep reference for logging


class ImageParser(BaseParser):
    """Process images to extract text via OCR or provide metadata."""

    supported_types: set[SourceType] = {SourceType.IMAGE}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Extract text from image using OCR, or return image metadata if OCR unavailable.

        Args:
            data: Raw image file content as bytes.
            filename: Original filename (used for logging and format hints).

        Returns:
            Extracted text from image (OCR results) or descriptive metadata.

        Raises:
            ValidationError: If the image cannot be processed.
        """
        logger.info("image_process_start", filename=filename, size=len(data))

        if not data:
            raise ValidationError("Empty image file provided.")

        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(data))
            
            # Get basic image info
            width, height = image.size
            format_name = image.format or "UNKNOWN"
            mode = image.mode
            
            logger.info(
                "image_info",
                filename=filename,
                format=format_name,
                width=width,
                height=height,
                mode=mode,
            )

            # Try OCR if available
            if OCR_AVAILABLE:
                try:
                    # Configure tesseract for better accuracy
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(
                        image, 
                        config=custom_config,
                        lang='eng'  # English; could be made configurable
                    )
                    
                    # Clean up the text
                    text = text.strip()
                    
                    if text:
                        logger.info(
                            "image_ocr_success",
                            filename=filename,
                            text_length=len(text),
                        )
                        return text
                    else:
                        logger.warning(
                            "image_ocr_empty_text",
                            filename=filename,
                        )
                        # Fall back to metadata if OCR found no text
                        
                except Exception as ocr_error:
                    logger.warning(
                        "image_ocr_failed",
                        filename=filename,
                        error=str(ocr_error),
                    )
                    # Fall back to metadata if OCR fails

            # If OCR not available or failed/not fruitful, return descriptive metadata
            description_parts = [
                f"Image: {filename or 'unnamed'}",
                f"Format: {format_name}",
                f"Dimensions: {width}×{height} pixels",
                f"Color mode: {mode}",
            ]
            
            # Add file size info
            size_kb = len(data) / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
            description_parts.append(f"File size: {size_str}")
            
            # Add note about OCR availability
            if not OCR_AVAILABLE:
                description_parts.append(
                    "Note: OCR text extraction not available. "
                    "Install 'pytesseract' and Tesseract OCR for text extraction from images."
                )
            else:
                description_parts.append(
                    "Note: No text detected via OCR. Image may not contain readable text."
                )

            description = "\n".join(description_parts)
            logger.info(
                "image_process_complete_metadata",
                filename=filename,
                description_length=len(description),
            )
            
            return description

        except Exception as exc:
            # Handle PIL/image-specific errors
            if "cannot identify image file" in str(exc).lower():
                raise ValidationError(
                    f"Cannot identify image file '{filename}'. "
                    f"Unsupported or corrupted image format."
                ) from exc
            else:
                logger.error(
                    "image_process_failed",
                    filename=filename,
                    error=str(exc),
                    exc_info=True,
                )
                raise ValidationError(
                    f"Failed to process image '{filename}': {str(exc)}"
                ) from exc


