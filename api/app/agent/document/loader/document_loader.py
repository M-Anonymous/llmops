import os
from abc import ABC

from langchain_core.documents import Document
from app.component.cos.cos_client import cos_client

from langchain_community.document_loaders import UnstructuredURLLoader



loader = UnstructuredURLLoader(urls=[""])
documents = loader.load()
print(documents)