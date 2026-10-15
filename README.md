# 运维知识库问答机器人

一个基于 **RAG（检索增强生成）** 技术的智能问答系统。上传你的运维手册 / 操作指南 / 故障排查文档，就能用自然语言提问，AI 直接基于你的文档回答，**不会一本正经地胡说八道**。

---

## ✨ 功能特性

- 📄 支持 **PDF / TXT / Markdown** 文档上传
- 🔍 基于向量相似度检索最相关的文档片段
- 💬 完整的聊天式界面，支持多轮对话
- 📚 每条回答都标注**参考来源**，可追溯原文
- 🖥️ 一键启动，浏览器里直接用
- 💰 用阿里云百炼（通义千问），新用户有免费额度

## 🖼️ 界面预览

<!-- TODO: 跑起来后截图替换这里 -->

```
[界面截图位置：左侧边栏上传文档 + 右侧聊天窗口]
```

## 🛠️ 技术栈

| 层 | 选型 |
|---|---|
| 前端 UI | Streamlit |
| RAG 框架 | LangChain |
| 向量数据库 | ChromaDB |
| 大语言模型 | 通义千问 `qwen-plus` |
| Embedding 模型 | 通义千问 `text-embedding-v2` |
| 配置管理 | python-dotenv |

## 🚀 快速开始

### 1. 准备 Python 环境

需要 **Python 3.10+**（推荐 3.11 / 3.12，太新的 3.14 部分老包可能不兼容）。

下载地址：https://www.python.org/downloads/

> Windows 安装时记得勾选 **"Add Python to PATH"**。

### 2. 申请阿里云百炼 API Key

1. 打开 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 用阿里云账号登录（没有就注册一个）
3. 左侧菜单找 **「API-KEY 管理」** → **创建 API-KEY**
4. 复制生成的 `sk-` 开头的 Key

> 新用户有免费额度，够测试很久。

### 3. 配置环境变量

把 `.env.example` 复制一份改名为 `.env`，填入你的 Key：

```env
DASHSCOPE_API_KEY=sk-你的真实Key
```

### 4. 安装依赖

在项目根目录打开命令行：

```bash
pip install -r requirements.txt
```

### 5. 启动

```bash
streamlit run ui.py
```

浏览器会自动打开 **http://localhost:8501**。

## 📖 使用方法

1. 左侧边栏点 **「Browse files」** 上传一个 PDF / TXT / MD 文档
2. 点 **「🚀 上传并建立知识库」**，等几秒钟
3. 在底部输入框直接提问，比如：
   - "专线中断怎么排查？"
   - "服务器 CPU 飙高怎么处理？"
4. AI 回答完后，展开 **「📚 查看参考来源」** 能看到它引用了文档的哪一段

## 📁 项目结构

```
ops-knowledge-bot/
├── ui.py              # Streamlit 主界面（RAG 问答）
├── agent.py           # Agent 实验：Plan-and-Execute + ReAct
├── config.py          # 全局配置（换客户只改这里）
├── requirements.txt   # 依赖清单
├── .env.example       # API Key 配置模板
├── .env               # 你的真实 Key（不要提交到 Git）
├── README.md
├── rag/               # RAG 核心模块
│   ├── __init__.py
│   ├── loader.py      # 文档加载（PDF/TXT/MD）
│   ├── splitter.py    # 文本切分
│   ├── store.py       # 向量存储与检索
│   └── chain.py       # RAG 问答链
├── uploads/           # 上传的文件（自动创建）
└── chroma_db/         # 向量数据库持久化（自动创建）
```

## 🤖 Agent 实验（agent.py）

除了 RAG 问答，这个仓库还包含一个**手写的最小 Agent**，不依赖 LangChain AgentExecutor，直接用 openai SDK 的 tools 参数实现：

- **单 Agent 循环**：模型自己决定调哪个工具，Python 执行后把结果喂回去
- **Plan-and-Execute**：复杂任务先输出步骤清单，再按计划执行
- **ReAct 容错**：工具报错时把错误信息返回给模型，它自己换路径/换工具重试

内置 3 个工具：
- `list_files()`：列出当前目录
- `read_text_file(path)`：读文本文件
- `write_config(customer_name, greeting)`：生成客户配置 JSON

运行：
```bash
python agent.py
```

## 🔧 可调参数

所有参数集中在 **`config.py`**，换客户/换场景只改这一个文件：

| 参数 | 作用 |
|---|---|
| `APP_NAME` / `WELCOME_MESSAGE` | 界面标题和欢迎语 |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 文档切分大小 |
| `RETRIEVAL_TOP_K` | 每次检索几条相关文档 |
| `LLM_MODEL` / `EMBEDDING_MODEL` | 换模型（qwen-plus / qwen-turbo / qwen-max） |
| `SYSTEM_PROMPT_TEMPLATE` | AI 的回答规则 |

## ❓ 常见问题

**Q: 回答不准确怎么办？**
A: 调小 `chunk_size`（比如 300），或者把 `k` 从 3 改成 5。

**Q: 支持 Word 文档吗？**
A: 目前不支持 `.docx`，需要的话可以装 `python-docx` 并在 `loader.py` 里加一个分支。

**Q: 怎么部署到公网？**
A: 把代码推到 GitHub，然后用 [Streamlit Community Cloud](https://share.streamlit.io/) 一键部署，免费。

## 📄 License

MIT
