from langchain_core.documents import Document

from app.agent.document.loader.document_loader import DocumentLoader, register_loader


class PdfLoader(DocumentLoader):

    @classmethod
    def load(cls, url: str) -> list[Document]:
        raise NotImplementedError("PdfLoader 尚未实现")


register_loader("pdf", loader=PdfLoader)
