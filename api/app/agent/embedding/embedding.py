import os

from langchain_community.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings(
    model=os.getenv("QWEN_EMBEDDING_NAME",""),
    dashscope_api_key=os.getenv("QWEN_API_KEY"))