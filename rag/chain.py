"""
RAG 链模块
把检索到的文档内容 + 用户问题，发给大模型生成最终回答
"""
from openai import OpenAI
from langchain_core.documents import Document
from typing import List
import os


def answer_question(docs: List[Document], question: str) -> str:
    """完整的 RAG 问答流程：拼提示词 → 发大模型 → 返回回答"""
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 把检索到的文档内容拼成一段
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])

    prompt = f"""你是一个专业的运维知识助手。请根据下面提供的【参考资料】来回答用户的问题。
规则：
1. 主要根据参考资料来回答，如果参考资料里没有相关信息，就老实说"根据现有资料，我没有找到相关答案"
2. 回答要准确、简洁、有条理
3. 如果参考资料里有具体的步骤或方法，按步骤列出
4. 不要编造参考资料里没有的内容

【参考资料】：
{context}

【用户问题】：
{question}

【回答】："""

    response = client.chat.completions.create(
        model="qwen-plus-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content
