"""
RAG 链模块
把检索到的文档内容 + 用户问题，发给大模型生成最终回答
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from typing import List
import os
import sys

# 让本文件能 import 项目根目录的 config.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE,
    SYSTEM_PROMPT_TEMPLATE,
)


def get_llm() -> ChatOpenAI:
    """获取大语言模型（参数全部来自 config.py）"""
    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
        openai_api_base=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
        streaming=True,
    )


def build_prompt(docs: List[Document], question: str):
    """把检索到的文档和用户问题拼成完整的提示词"""
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT_TEMPLATE)
    return prompt.format_messages(context=context, question=question)


def answer_question(docs: List[Document], question: str) -> str:
    """完整 RAG 问答：拼提示词 → 发大模型 → 返回回答"""
    llm = get_llm()
    messages = build_prompt(docs, question)
    response = llm.invoke(messages)
    return response.content
