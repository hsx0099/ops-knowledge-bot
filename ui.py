"""
运维知识库问答机器人 - 主程序（Streamlit界面）
运行命令：streamlit run ui.py

这是用户直接看到的界面
"""
import streamlit as st
import os
from dotenv import load_dotenv

# 加载环境变量（.env文件里存API Key）
load_dotenv()

# 导入我们自己写的模块
from rag.loader import load_document
from rag.splitter import split_documents
from rag.store import create_vector_store, load_vector_store, similarity_search
from rag.chain import answer_question

# ============ 页面配置 ============
st.set_page_config(
    page_title="运维知识库问答机器人",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 运维知识库问答机器人")
st.markdown("上传你的运维文档，用自然语言提问，AI帮你找答案")

# ============ 侧边栏：上传文档 ============
with st.sidebar:
    st.header("📁 知识库管理")

    # 上传文件
    uploaded_file = st.file_uploader(
        "上传文档（支持PDF/TXT/Markdown）",
        type=["pdf", "txt", "md"]
    )

    if uploaded_file and st.button("🚀 上传并建立知识库", type="primary"):
        with st.spinner("正在处理文档..."):
            # 1. 保存上传的文件到临时目录
            os.makedirs("uploads", exist_ok=True)
            file_path = f"uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 2. 加载文档
            docs = load_document(file_path)

            # 3. 切分文档
            chunks = split_documents(docs)

            # 4. 创建向量数据库
            vector_store = create_vector_store(chunks)

            st.session_state["vector_store"] = vector_store
            st.success(f"✅ 知识库建立成功！共 {len(chunks)} 个文档块")

    st.divider()

    # 检查是否已有知识库
    if "vector_store" not in st.session_state:
        # 尝试从本地加载
        vs = load_vector_store()
        if vs:
            st.session_state["vector_store"] = vs
            st.info("📚 已加载本地知识库")

    if "vector_store" in st.session_state:
        st.success("✅ 知识库已就绪，可以提问了")

# ============ 主界面：对话区 ============

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是运维知识助手。请先在左侧上传文档建立知识库，然后就可以开始提问了。"}
    ]

# 显示历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入框
if prompt := st.chat_input("请输入你的问题..."):
    # 检查知识库是否就绪
    if "vector_store" not in st.session_state:
        st.warning("⚠️ 请先在左侧上传文档建立知识库！")
    else:
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    # 1. 检索相关文档
                    docs = similarity_search(st.session_state["vector_store"], prompt, k=3)

                    # 2. 生成回答
                    answer = answer_question(docs, prompt)

                    # 3. 显示回答
                    st.markdown(answer)

                    # 4. 显示引用来源
                    with st.expander("📚 查看参考来源"):
                        for i, doc in enumerate(docs):
                            st.markdown(f"**来源 {i+1}:**")
                            st.markdown(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                            st.divider()

                    # 存入对话历史
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    error_msg = f"❌ 出错了: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
