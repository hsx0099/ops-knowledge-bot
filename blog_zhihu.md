# 39 岁运维工程师转行 AI，我用一个月做了个知识库问答机器人

> 写在前面：这是我转行 AI 学习一个月的练手项目。把过程、踩坑、代码全公开，希望给同样在 35+ 想转方向的兄弟一点参考。

---

## 一、我为什么要做这个东西

我做运维快 15 年了。

小公司的运维是什么状态？线上半夜告警爬起来看日志，平时处理员工的 VPN 连不上、打印机坏了、CRM 打不开。真正让我焦虑的不是累，是**我发现自己的经验正在贬值**。

新来的小伙直接问 ChatGPT，排查速度比我翻 wiki 快得多。而我们公司那堆运维手册——Excel、PDF、微信群里转发的 word——零散、过期、搜索基本靠 Ctrl+F。

所以这个项目的初衷特别朴素：**做一个能直接读我们自己文档的 AI 助手**。不是问通用大模型（它根本不知道我们公司的服务器长啥样），而是让它只基于我们自己的手册回答。

技术圈管这个叫 **RAG（Retrieval-Augmented Generation，检索增强生成）**。

---

## 二、为什么不是微调，也不是直接问大模型

刚想这事的时候我查了一堆方案，最后选 RAG 的原因很现实：

| 方案 | 问题 |
|---|---|
| 直接把文档粘贴给 ChatGPT | 文档太长，上下文塞不下；每次都要手动贴，麻烦 |
| 微调一个专属大模型 | 我们这种小公司没数据、没 GPU、没预算，学不动也跑不起 |
| **RAG** | 文档存在本地向量库里，提问时只把相关几段塞给大模型，便宜、快、可追溯 |

RAG 的流程一句话讲清楚：

```
你的问题
  → 在文档库里找最相关的 3 段
  → 把这 3 段 + 你的问题一起发给大模型
  → 大模型基于这 3 段回答
```

它胡说八道的概率比直接问低很多，因为**答案必须从你给的资料里来**。

---

## 三、整个项目就 9 个文件

我没有上来就搞微服务、Docker、MySQL——一个人练手，先跑通再说。

```
ops-knowledge-bot/
├── ui.py              # Streamlit 网页界面（200 行）
├── requirements.txt
├── .env.example       # API Key 模板
└── rag/
    ├── loader.py      # 读 PDF/TXT/MD
    ├── splitter.py    # 长文档切成小块
    ├── store.py       # 向量数据库
    └── chain.py       # 调大模型生成回答
```

技术选型：

- **界面**：Streamlit（运维人别抗拒 Python 做前端，真的快，一个下午就能做出像模像样的网页）
- **RAG 框架**：LangChain（生态全，教程多）
- **向量库**：ChromaDB（本地文件，不用起服务）
- **大模型**：阿里云通义千问 qwen-plus（新用户免费额度，不用翻墙不用绑信用卡）
- **Embedding**：通义千问 text-embedding-v2（把文本转成向量）

---

## 四、每个文件在干什么

### 1. `loader.py` —— 读文档

```python
if file_ext == "pdf":
    loader = PyPDFLoader(file_path)
elif file_ext in ["txt", "md"]:
    loader = TextLoader(file_path, encoding="utf-8")
```

没什么花活，就是 LangChain 现成的 Loader，按后缀名分流。

### 2. `splitter.py` —— 切文档

大模型上下文窗口有限，一整本 100 页的手册塞不进去。要切成小块：

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # 每块 500 字
    chunk_overlap=50,     # 相邻块重叠 50 字，避免句子被拦腰砍断
)
```

`chunk_overlap` 这个参数挺关键——不重叠的话，一段故障排查步骤刚好被切到两块中间，检索时就漏了。

### 3. `store.py` —— 向量化 + 存

把每块文本丢给 Embedding 模型转成向量，存进 ChromaDB。下次你提问，它把你的问题也转成向量，找最相近的 3 块。

### 4. `chain.py` —— 调大模型

这是整个项目的灵魂——提示词。我写的提示词不长，但规则很硬：

```
你是一个专业的运维知识助手。请根据下面提供的【参考资料】来回答：
1. 主要根据参考资料回答，资料里没有就说"没找到"
2. 不要编造参考资料里没有的内容
3. 有步骤就按步骤列
```

第 2 条是关键。不加这句，大模型会用它训练时背下来的"通用运维知识"瞎答，那就失去了 RAG 的意义。

### 5. `ui.py` —— 界面

Streamlit 的聊天组件 `st.chat_message`、`st.chat_input` 是真的香，几十行代码就做出了聊天窗口。上传文档、显示历史、展开"参考来源"全有。

---

## 五、踩过的坑（这部分最值钱）

### 坑 1：Python 版本太新会教你做人

我本机装的是 Python 3.14（最新版），结果 `requirements.txt` 里写的是 2024 年的老版本（`streamlit==1.38`、`chromadb==0.5.5`），全部报"没有匹配的版本"。

最后解决方案：把版本号全去掉，让 pip 自己选最新版：

```
streamlit
langchain
langchain-community
langchain-openai
langchain-chroma
chromadb
pypdf
python-dotenv
```

**教训**：练手项目别钉死版本号，除非你遇到了具体的兼容问题。

### 坑 2：LangChain 大改版，import 路径全变了

老教程里写的：

```python
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
```

在新版 LangChain 里全挂了，得改成：

```python
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma   # 这个也独立成包了
```

**教训**：看教程一定看发布时间，半年前的 LangChain 教程现在都可能跑不通。

### 坑 3：DashScope 控制台域名下线了

按老教程打开 `dashscope.console.aliyun.com`，直接 404。原来 2026 年 8 月改名成**阿里云百炼**了，新地址是 `bailian.console.aliyun.com`。但 API 后端地址没变，代码不用改。

### 坑 4：unstructured 这个包根本没必要装

老 requirements 里让装 `unstructured`，但我翻了一遍自己的 loader 代码，根本没用它（我只用了 pypdf）。删掉就装过去了。

**教训**：别盲信教程里的依赖清单，想想每一行为什么需要。

---

## 六、跑起来是什么效果

- 上传一份 50 页的《公司网络运维手册》
- 问："专线中断怎么排查？"
- AI 秒回 4 步排查流程，还能点开看是引用了手册的第 3 章第 2 节

对我们这种小团队来说，新员工上手速度能快不少。

---

## 七、39 岁转行，我学到了什么

说几句掏心窝的：

1. **不要上来就学大模型训练、CUDA、扩散模型**。那些是算法工程师的活，我们这种转行者先把 RAG、Agent、API 调用这些"应用层"玩明白，接外包、做内部工具、转 AI 运维岗都够用。
2. **一个完整的小项目 > 十个半途而废的教程**。这个项目代码量不到 500 行，但从环境配置、踩依赖坑、调提示词、到最后部署，每一步都自己趟过一遍，比看十篇文章强。
3. **别害怕 35+**。我 39 了，英语一般，数学也就高中水平，但只要愿意动手，一个月真的能做出能跑的东西。

代码我放 GitHub 了（链接在文末），README 写得很详细，跟着做一下午能跑起来。

下一个目标：加个 Docker 部署，再加个微信机器人入口。

---

**欢迎交流**：评论区聊聊你现在多大、在做什么、想转什么方向。

> 本文是我一个月学习的记录，代码和文档都开源在 GitHub，欢迎 star。
> [GitHub 地址：ops-knowledge-bot]（部署完替换成真实链接）
