import re
from app.agent.document.cleaner.document_cleaner import DocumentCleaner

# ASCII 控制字符（保留 \t \n），常见于 PDF/Word 导出或编码错误
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# 零宽字符与 BOM，肉眼不可见但会影响分词与 embedding
_ZERO_WIDTH = re.compile(r"[\u200b-\u200d\ufeff]")
# 连续 3 个及以上换行，压缩为段落间单空行，避免 chunk 被空白占满
_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
# 每行末尾的空格/制表符
_TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)

class BaseDocumentCleaner(DocumentCleaner):

    @classmethod
    def clean_text(cls, text: str) -> str:
        text = remove_invisible_chars(text)
        return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WHITESPACE.sub("", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def remove_invisible_chars(text: str) -> str:
    text = _ZERO_WIDTH.sub("", text)
    text = text.lstrip("\ufeff")
    return _CONTROL_CHARS.sub("", text)
