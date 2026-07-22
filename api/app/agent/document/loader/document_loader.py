import os
import chardet
import tempfile
from abc import ABC

import requests
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


class DocumentLoader(ABC):

    @classmethod
    def load(cls,url: str) -> list[Document]:
        pass

class TxtLoader(DocumentLoader):

    @classmethod
    def load(cls, url: str) -> list[Document]:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 1. 获取原始字节流 (不要直接用 response.text)
        raw_bytes = response.content

        # 2. 智能检测编码
        detected_encoding = 'utf-8'  # 默认值

        if chardet:
            # 使用 chardet 检测，取前 10000 字节以加快速度
            result = chardet.detect(raw_bytes[:10000])
            if result and result.get('confidence', 0) > 0.7:
                detected_encoding = result['encoding']
                print(f"检测到文件编码: {detected_encoding} (置信度: {result['confidence']:.2f})")
        else:
            # 如果没有 chardet，回退到 requests 的猜测或默认 utf-8
            detected_encoding = response.encoding or 'utf-8'

        # 3. 使用检测到的编码写入临时文件
        # 注意：这里不再指定 encoding='utf-8'，而是使用动态检测到的编码
        assert detected_encoding is not None
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding=detected_encoding) as f:
            # 将字节流解码为字符串后写入
            f.write(raw_bytes.decode(detected_encoding, errors='ignore'))
            temp_path = f.name

        # 4. 加载文档 (TextLoader 的 encoding 最好也保持一致，或者留空让它自适应)
        loader = TextLoader(temp_path, encoding=detected_encoding)
        documents = loader.load()
        # 5. 清理临时文件
        os.unlink(temp_path)
        return documents


class PdfLoader(DocumentLoader):

    @classmethod
    def load(cls,url: str) -> list[Document]:
        pass

class WordLoader(DocumentLoader):

    @classmethod
    def load(cls,url: str) -> list[Document]:
        pass

class MDLoader(DocumentLoader):

    @classmethod
    def load(cls,url: str) -> list[Document]:
        pass
