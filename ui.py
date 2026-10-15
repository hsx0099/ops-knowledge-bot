"""
运维知识库问答机器人 - 主程序（Streamlit界面）
运行命令：streamlit run ui.py
"""
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

from rag.loader import load_document
from rag.splitter import split_documents
from rag.store import create_vector_store, load_vector_store, similarity_search
from rag.chain import answer_question
from config import (
    APP_NAME, APP_ICON, APP_SUBTITLE, WELCOME_MESSAGE,
    SUPPORTED_EXTENSIONS, UPLOAD_DIR, RETRIEVAL_TOP_K,
)

# ============ 页面配置 ============
st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")
st.title(f"{APP_ICON} {APP_NAME}")
st.markdown(APP_SUBTITLE)

# ============ 侧边栏：上传文档 ============
with st.sidebar:
    st.header("📁 知识库管理")

    uploaded_file = st.file_uploader(
        "上传文档（支持PDF/TXT/Markdown）",
        type=SUPPORTED_EXTENSIONS,
    )

    if uploaded_file and st.button("🚀 上传并建立知识库", type="primary"):
        with st.spinner("正在处理文档..."):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            docs = load_document(file_path)
            chunks = split_documents(docs)
            vector_store = create_vector_store(chunks)

            st.session_state["vector_store"] = vector_store
            st.success(f"✅ 知识库建立成功！共 {len(chunks)} 个文档块")

    st.divider()

    if "vector_store" not in st.session_state:
        vs = load_vector_store()
        if vs:
            st.session_state["vector_store"] = vs
            st.info("📚 已加载本地知识库")

    if "vector_store" in st.session_state:
        st.success("✅ 知识库已就绪，可以提问了")

# ============ 主界面：对话区 ============
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("请输入你的问题..."):
    if "vector_store" not in st.session_state:
        st.warning("⚠️ 请先在左侧上传文档建立知识库！")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    docs = similarity_search(
                        st.session_state["vector_store"], prompt, k=RETRIEVAL_TOP_K
                    )
                    answer = answer_question(docs, prompt)
                    st.markdown(answer)

                    with st.expander("📚 查看参考来源"):
                        for i, doc in enumerate(docs):
                            st.markdown(f"**来源 {i+1}:**")
                            preview = doc.page_content[:300]
                            if len(doc.page_content) > 300:
                                preview += "..."
                            st.markdown(preview)
                            st.divider()

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    error_msg = f"❌ 出错了: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
