import re

from app.agent.document.cleaner.base_cleaner import (
    BaseDocumentCleaner,
    normalize_whitespace,
    remove_invisible_chars,
)
from app.agent.document.cleaner.document_cleaner import register_cleaner

# Markdown YAML front matter（文件开头的 --- ... --- 元数据块）
_FRONT_MATTER = re.compile(r"^\s*---\s*\n.*?\n---\s*\n", re.DOTALL)
# HTML 注释，部分 .md 混排 HTML 时会产生检索噪声
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


class MDCleaner(BaseDocumentCleaner):

    @classmethod
    def clean_text(cls, text: str) -> str:
        text = remove_invisible_chars(text)
        text = _FRONT_MATTER.sub("", text, count=1)
        text = _HTML_COMMENT.sub("", text)
        return normalize_whitespace(text)

register_cleaner("md", "markdown", cleaner=MDCleaner)
