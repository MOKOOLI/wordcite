"""wordcite: automatic citations and bibliographies for Word documents."""
from .docx_processor import ProcessReport, process_docx
from .engine import BibEntry, CitationEngine, CiteItem, Cluster
from .models import Name, Reference
from .parsers import load_references
from .styles import Style, get_style, list_styles, register

__version__ = "0.1.0"
__all__ = ["process_docx", "ProcessReport", "CitationEngine", "CiteItem", "Cluster", "BibEntry",
           "Name", "Reference", "load_references", "Style", "get_style", "list_styles", "register"]
