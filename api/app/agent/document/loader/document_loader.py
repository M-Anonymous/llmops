import os
import tempfile
from abc import ABC

import requests
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


class DocumentLoader(ABC):

    @classmethod
    def load(cls,urls: list[str]) -> list[Document]:
        pass

class TxtLoader(DocumentLoader):

    @classmethod
    def load(cls,urls: list[str]) -> list[Document]:
        documents = []
        for url in urls:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(response.text)  # 注意这里是 text
                temp_path = f.name
            loader = TextLoader(temp_path, encoding='utf-8')
            # 3. 加载文档
            doc = loader.load()
            documents.append(doc)
            # 4. 清理临时文件
            os.unlink(temp_path)
        return documents


class PdfLoader(DocumentLoader):

    @classmethod
    def load(cls,urls: list[str]) -> list[Document]:
        pass

class WordLoader(DocumentLoader):

    @classmethod
    def load(cls,urls: list[str]) -> list[Document]:
        pass

class MDLoader(DocumentLoader):

    @classmethod
    def load(cls,urls: list[str]) -> list[Document]:
        pass

print(TxtLoader.load(["https://llmops-1258847722.cos.ap-chongqing.myqcloud.com/uploads/afc71cc285e7420e9077b0184bbae80b_test.txt?q-sign-algorithm=sha1&q-ak=AKID0RvLyUvCIMc8Vp6GLKDxbCdx87uVu6A4&q-sign-time=1784634341%3B1784634701&q-key-time=1784634341%3B1784634701&q-header-list=host&q-url-param-list=&q-signature=4ecc2a4712c572e20a22ec98cb0afe916104e20b"]))