"""
文本切分模块
把长文档切成适合放入向量数据库的小块
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List


def split_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """把长文档切成小块，默认每块 500 字，相邻块重叠 50 字"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    print(f"✅ 文档切分完成: {len(documents)} 段 → {len(split_docs)} 块")
    return split_docs
