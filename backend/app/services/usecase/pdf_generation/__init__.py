"""PDF generation use case — HTML template + (later) WeasyPrint adapter."""

from app.services.usecase.pdf_generation.template import render_report_html

__all__ = ["render_report_html"]
