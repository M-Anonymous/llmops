from abc import ABC, abstractmethod

from langchain_core.documents import Document


class DocumentCleaner(ABC):
    """
    数据清洗
    """

    @classmethod
    @abstractmethod
    def clean_text(cls, text: str) -> str:
        pass

    @classmethod
    def clean(cls, docs: list[Document]) -> list[Document]:
        cleaned: list[Document] = []
        for doc in docs:
            content = cls.clean_text(doc.page_content)
            # 如果为空白文档，跳过
            if not content.strip():
                continue
            cleaned.append(
                Document(page_content=content, metadata=dict(doc.metadata))
            )
        return cleaned



_CLEANER_BY_EXT: dict[str, type[DocumentCleaner]] = {}


def register_cleaner(*extensions: str, cleaner: type[DocumentCleaner]) -> None:
    for ext in extensions:
        _CLEANER_BY_EXT[ext.lower()] = cleaner


def get_cleaner(file_ext: str) -> type[DocumentCleaner]:
    from app.agent.document.cleaner.base_cleaner import BaseDocumentCleaner

    return _CLEANER_BY_EXT.get(file_ext.lower().lstrip("."), BaseDocumentCleaner)
