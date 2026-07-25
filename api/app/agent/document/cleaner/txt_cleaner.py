import re

from app.agent.document.cleaner.base_cleaner import (
    BaseDocumentCleaner,
    normalize_whitespace,
    remove_invisible_chars,
)
from app.agent.document.cleaner.document_cleaner import register_cleaner

# 行尾连字符断词：implementa-\ntion → implementation
_HYPHEN_LINE_BREAK = re.compile(r"(\w)-\n(\w)")


class TxtCleaner(BaseDocumentCleaner):

    @classmethod
    def clean_text(cls, text: str) -> str:
        text = remove_invisible_chars(text)
        text = _HYPHEN_LINE_BREAK.sub(r"\1\2", text)
        return normalize_whitespace(text)


register_cleaner("txt", "text", cleaner=TxtCleaner)
