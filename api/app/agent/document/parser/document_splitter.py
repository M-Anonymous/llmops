from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def splitter(docs: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    print(f"Split documentation into {len(all_splits)} chunks.")