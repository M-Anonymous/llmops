from langchain_core.documents import Document

from app.agent.document.loader.document_loader import DocumentLoader, register_loader
from app.agent.document.loader.txt_loader import TxtLoader


class MDLoader(DocumentLoader):
    """Markdown 本质是文本，复用 TxtLoader 的下载与解码逻辑。"""

    @classmethod
    def load(cls, url: str) -> list[Document]:
        return TxtLoader.load(url)

register_loader("md", "markdown", loader=MDLoader)
