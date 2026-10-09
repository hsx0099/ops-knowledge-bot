"""
向量存储模块
把文档块存进向量数据库，并支持相似度检索
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List, Optional
import os


def get_embeddings() -> OpenAIEmbeddings:
    """获取 Embedding 模型（通义千问 text-embedding-v2）"""
    return OpenAIEmbeddings(
        model="text-embedding-v2",
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def create_vector_store(
    documents: List[Document],
    persist_directory: str = "./chroma_db"
) -> Chroma:
    """创建向量数据库并保存文档"""
    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print(f"✅ 向量数据库创建完成，保存到: {persist_directory}")
    return vector_store


def load_vector_store(persist_directory: str = "./chroma_db") -> Optional[Chroma]:
    """从本地加载已有的向量数据库"""
    if not os.path.exists(persist_directory):
        return None
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    print(f"✅ 已加载现有向量数据库: {persist_directory}")
    return vector_store


def similarity_search(vector_store: Chroma, query: str, k: int = 3) -> List[Document]:
    """根据问题检索最相关的 k 个文档块"""
    docs = vector_store.similarity_search(query, k=k)
    print(f"✅ 检索完成: 从向量库中找到 {len(docs)} 条相关内容")
    return docs
