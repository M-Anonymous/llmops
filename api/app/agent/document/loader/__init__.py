from app.agent.document.loader import md_loader as _md_loader  # noqa: F401
from app.agent.document.loader import pdf_loader as _pdf_loader  # noqa: F401
from app.agent.document.loader import txt_loader as _txt_loader  # noqa: F401
from app.agent.document.loader import word_loader as _word_loader  # noqa: F401
from app.agent.document.loader.document_loader import DocumentLoader, get_loader
from app.agent.document.loader.md_loader import MDLoader
from app.agent.document.loader.pdf_loader import PdfLoader
from app.agent.document.loader.txt_loader import TxtLoader
from app.agent.document.loader.word_loader import WordLoader

__all__ = [
    "DocumentLoader",
    "TxtLoader",
    "MDLoader",
    "PdfLoader",
    "WordLoader",
    "get_loader",
]
