from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain_text_splitters.base import TextSplitter
from app.agent.document.splitter.support.support_splitter import SupportSplitter

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


def resolve_splitter_type(file_ext: str | None) -> SupportSplitter:
    if file_ext and file_ext.lstrip(".").lower() in {"md", "markdown"}:
        return SupportSplitter.MD
    return SupportSplitter.DEFAULT

class DocumentSplitter:

    @staticmethod
    def split(
        docs: list[Document],
        splitter_type: SupportSplitter = SupportSplitter.DEFAULT,
        **kwargs,
    ) -> list[Document]:
        chunk_size = kwargs.pop("chunk_size", DEFAULT_CHUNK_SIZE)
        chunk_overlap = kwargs.pop("chunk_overlap", DEFAULT_CHUNK_OVERLAP)
        splitter_kwargs = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            **kwargs,
        }
        if splitter_type == SupportSplitter.MD:
            text_splitter =  MarkdownTextSplitter(**splitter_kwargs)
        else:
            text_splitter = RecursiveCharacterTextSplitter(**splitter_kwargs)
        return text_splitter.split_documents(docs)

