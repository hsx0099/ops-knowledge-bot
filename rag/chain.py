"""
RAG 链模块
把检索到的文档内容 + 用户问题，发给大模型生成最终回答
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from typing import List
import os


def get_llm() -> ChatOpenAI:
    """获取大语言模型（通义千问 qwen-plus）"""
    return ChatOpenAI(
        model="qwen-plus",
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.7,
        streaming=True
    )


PROMPT_TEMPLATE = """
你是一个专业的运维知识助手。请根据下面提供的【参考资料】来回答用户的问题。

规则：
1. 主要根据参考资料来回答，如果参考资料里没有相关信息，就老实说"根据现有资料，我没有找到相关答案"
2. 回答要准确、简洁、有条理
3. 如果参考资料里有具体的步骤或方法，按步骤列出
4. 不要编造参考资料里没有的内容

【参考资料】：
{context}

【用户问题】：
{question}

【回答】：
"""


def build_prompt(docs: List[Document], question: str):
    """把检索到的文档和用户问题拼成完整的提示词"""
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    return prompt.format_messages(context=context, question=question)


def answer_question(docs: List[Document], question: str) -> str:
    """完整的 RAG 问答流程：拼提示词 → 发大模型 → 返回回答"""
    llm = get_llm()
    messages = build_prompt(docs, question)
    response = llm.invoke(messages)
    return response.content
