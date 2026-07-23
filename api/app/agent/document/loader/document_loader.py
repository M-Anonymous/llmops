from abc import ABC, abstractmethod

from langchain_core.documents import Document


class DocumentLoader(ABC):
    """文档加载"""

    @classmethod
    @abstractmethod
    def load(cls, url: str) -> list[Document]:
        pass


_LOADER_BY_EXT: dict[str, type[DocumentLoader]] = {}


def register_loader(*extensions: str, loader: type[DocumentLoader]) -> None:
    for ext in extensions:
        _LOADER_BY_EXT[ext.lower()] = loader


def get_loader(file_ext: str) -> type[DocumentLoader]:
    ext = file_ext.lower().lstrip(".")
    loader = _LOADER_BY_EXT.get(ext)
    if loader is None:
        raise ValueError(f"不支持的文件类型: {ext}")
    return loader
