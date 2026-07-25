import os
import tempfile

import chardet
import requests
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from app.agent.document.loader.document_loader import DocumentLoader, register_loader


class TxtLoader(DocumentLoader):

    @classmethod
    def load(cls, url: str) -> list[Document]:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 1. 获取原始字节流 (不要直接用 response.text)
        raw_bytes = response.content

        # 2. 智能检测编码
        detected_encoding = "utf-8"

        if chardet:
            result = chardet.detect(raw_bytes[:10000])
            if result and result.get("confidence", 0) > 0.7:
                detected_encoding = result["encoding"]
                print(
                    f"检测到文件编码: {detected_encoding} "
                    f"(置信度: {result['confidence']:.2f})"
                )
        else:
            detected_encoding = response.encoding or "utf-8"

        # 3. 使用检测到的编码写入临时文件
        assert detected_encoding is not None
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding=detected_encoding
        ) as f:
            f.write(raw_bytes.decode(detected_encoding, errors="ignore"))
            temp_path = f.name

        # 4. 加载文档
        loader = TextLoader(temp_path, encoding=detected_encoding)
        documents = loader.load()

        # 5. 清理临时文件
        os.unlink(temp_path)
        return documents


register_loader("txt", "text", loader=TxtLoader)
