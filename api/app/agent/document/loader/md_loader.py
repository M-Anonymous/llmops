import requests
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_langchain_docs(doc_paths: list[str]) -> list[Document]:
    """Fetch LangChain documentation pages as Documents."""
    docs: list[Document] = []
    for path in doc_paths:
        try:
            response = requests.get(path, timeout=20)
            response.raise_for_status()
        except requests.RequestException:
            continue
        docs.append(
            Document(page_content=response.text, metadata={"source": path})
        )
    return docs


text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
all_splits = text_splitter.split_documents(load_langchain_docs(["https://docs.langchain.com/oss/python/langchain/agents.md"]))
