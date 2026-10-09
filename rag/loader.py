"""
文档加载模块
负责把各种格式的文档（PDF、TXT、Markdown）加载成 LangChain 的 Document 对象
"""
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from typing import List


def load_document(file_path: str) -> List[Document]:
    """加载文档文件，自动识别文件格式（支持 .pdf / .txt / .md）"""
    file_ext = file_path.lower().split(".")[-1]

    if file_ext == "pdf":
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    elif file_ext in ["txt", "md"]:
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
    else:
        raise ValueError(f"不支持的文件格式: .{file_ext}，目前支持 .pdf / .txt / .md")

    print(f"✅ 成功加载文档: {file_path}，共 {len(docs)} 页/段")
    return docs
