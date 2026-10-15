"""
全局配置文件
================
换一个客户/场景，只改这个文件，不动业务代码。

分组：
1. 应用身份      —— 名字、图标、欢迎语
2. 文件路径      —— 上传目录、向量库目录
3. 切分参数      —— chunk_size / overlap
4. 检索参数      —— top-k
5. 模型参数      —— LLM、Embedding、base_url
6. 系统提示词    —— AI 的角色和回答规则
"""

# ============ 1. 应用身份 ============
APP_NAME = "运维知识库问答机器人"
APP_ICON = "🤖"
APP_SUBTITLE = "上传你的运维文档，用自然语言提问，AI帮你找答案"
WELCOME_MESSAGE = "你好！我是运维知识助手。请先在左侧上传文档建立知识库，然后就可以开始提问了。"

# 支持上传的文件后缀
SUPPORTED_EXTENSIONS = ["pdf", "txt", "md"]

# ============ 2. 文件路径 ============
UPLOAD_DIR = "uploads"           # 上传的临时文件放这里
VECTOR_DB_DIR = "./chroma_db"   # 向量数据库持久化目录

# ============ 3. 文档切分参数 ============
CHUNK_SIZE = 500        # 每块字符数（300-800 之间调）
CHUNK_OVERLAP = 50      # 相邻块重叠字符数，防止句子被拦腰切断

# ============ 4. 检索参数 ============
RETRIEVAL_TOP_K = 3     # 每次提问，从库里取最相关的几块塞给大模型

# ============ 5. 模型参数 ============
# 通义千问（阿里云百炼），走 OpenAI 兼容接口
LLM_MODEL = "qwen-plus"
EMBEDDING_MODEL = "text-embedding-v4"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_TEMPERATURE = 0.7   # 0=严谨保守，1=自由发挥
# API Key 不要写在这里！放在 .env 文件里，通过环境变量 DASHSCOPE_API_KEY 读取

# ============ 6. 系统提示词 ============
# 这是 RAG 的灵魂——告诉 AI 只基于资料回答，不准编
SYSTEM_PROMPT_TEMPLATE = """
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
