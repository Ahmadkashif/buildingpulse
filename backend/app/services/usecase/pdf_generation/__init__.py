"""PDF generation use case — HTML template + WeasyPrint adapter."""

from app.services.usecase.pdf_generation.service import (
    PdfGatingError,
    PdfGenerationRequest,
    PdfGenerationResult,
    PdfGenerationUseCaseService,
    render_pdf_with_weasyprint,
)
from app.services.usecase.pdf_generation.template import render_report_html

__all__ = [
    "PdfGatingError",
    "PdfGenerationRequest",
    "PdfGenerationResult",
    "PdfGenerationUseCaseService",
    "render_pdf_with_weasyprint",
    "render_report_html",
]
