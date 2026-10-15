"""
文本切分模块
把长文档切成适合放入向量数据库的小块
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHUNK_SIZE, CHUNK_OVERLAP


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    把长文档切分成小块

    为什么要切分？
    - LLM的上下文窗口有限，不能一次性把整个文档塞进去
    - 切分成小块后，检索时只取最相关的几块，既省token又更精准

    参数:
        documents: 加载好的文档列表
        chunk_size: 每块的最大字符数（推荐300-800）
        chunk_overlap: 相邻两块重叠的字符数（保证上下文连贯）

    返回:
        List[Document]: 切分后的文档块列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""]
    )

    split_docs = text_splitter.split_documents(documents)
    print(f"✅ 文档切分完成: {len(documents)} 段 → {len(split_docs)} 块")
    return split_docs


if __name__ == "__main__":
    # 测试代码
    from loader import load_document

    test_file = "example.txt"
    try:
        docs = load_document(test_file)
        chunks = split_documents(docs)
        print(f"\n--- 第一块内容预览 ---")
        print(chunks[0].page_content[:300])
    except FileNotFoundError:
        print("测试文件不存在，这是正常的")
