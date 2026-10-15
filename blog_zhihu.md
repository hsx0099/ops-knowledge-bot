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

## 三、整个项目结构

我没有上来就搞微服务、Docker、MySQL——一个人练手，先跑通再说。

```
ops-knowledge-bot/
├── ui.py              # Streamlit 网页界面
├── agent.py           # 手写的最小 Agent（function-calling + Plan-and-Execute）
├── config.py          # 全局配置（换客户只改这一个文件）
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
- **Embedding**：通义千问 text-embedding-v4（最新版，中文效果比 v2 好不少）
- **Agent**：没上 LangGraph、CrewAI，直接用 openai SDK 的 tools 参数手写（详见第七节）

---

## 四、每个文件在干什么

### 1. `loader.py` —— 读文档

```python
if file_ext == "pdf":
    loader = PyPDFLoader(file_path)
elif file_ext in ["txt", "md"]:
    loader = TextLoader(file_path, encoding="utf-8")
```

没什么花活，就是 LangChain 现成的 Loader，按后缀名分流。后来我把上传改成多选，一次能传五六个 PDF，不用一个一个点。

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

这里踩了个坑：通义千问的 Embedding 走 OpenAI 兼容接口时，`langchain_openai.OpenAIEmbeddings` 默认会校验上下文长度，传 v4 模型一直报奇怪的错。最后加了两个参数才搞定：

```python
OpenAIEmbeddings(
    model="text-embedding-v4",
    openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    check_embedding_ctx_length=False,   # 关掉兼容层的长度校验
    chunk_size=10,                     # 通义对单次请求条数有限制，调小
)
```

**教训**：开源库对国内模型的兼容层总有各种小毛病，报错信息看不懂的时候，直接去看官方 SDK 的调用示例，别死磕 LangChain 的封装。

### 4. `chain.py` —— 调大模型

最开始我图省事用 `langchain_openai.ChatOpenAI` 包了一层，结果流式输出、错误处理各种别扭，兼容模式下还偶发 400。后来干脆拆掉 LangChain 的 LLM 封装，直接用官方 `openai` 库调：

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

resp = client.chat.completions.create(
    model="qwen-plus",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
)
answer = resp.choices[0].message.content
```

代码量没少多少，但**报错信息终于能看懂了**，调试效率高很多。

真正的灵魂是提示词，我写的规则很硬：

```
你是一个专业的运维知识助手。请根据下面提供的【参考资料】来回答：
1. 主要根据参考资料回答，资料里没有就说"没找到"
2. 不要编造参考资料里没有的内容
3. 有步骤就按步骤列
```

第 2 条是关键。不加这句，大模型会用它训练时背下来的"通用运维知识"瞎答，那就失去了 RAG 的意义。

### 5. `ui.py` —— 界面

Streamlit 的聊天组件 `st.chat_message`、`st.chat_input` 是真的香，几十行代码就做出了聊天窗口。上传文档（改成多选了）、显示历史、展开"参考来源"全有。

---

## 五、踩过的坑（这部分最值钱）

### 坑 1：Python 版本太新会教你做人

我本机装的是 Python 3.14（最新版），结果 `requirements.txt` 里写的是 2024 年的老版本（`streamlit==1.38`、`chromadb==0.5.5`），全部报"没有匹配的版本"。

最后解决方案：把版本号全去掉，让 pip 自己选最新版。

**教训**：练手项目别钉死版本号，除非你遇到了具体的兼容问题。

### 坑 2：LangChain 大改版，import 路径全变了

老教程里写的 `from langchain.schema import Document`、`from langchain.prompts import ChatPromptTemplate`，在新版 LangChain 里全挂了，得改成 `langchain_core.documents`、`langchain_core.prompts`，Chroma 也独立成 `langchain-chroma` 包了。

**教训**：看教程一定看发布时间，半年前的 LangChain 教程现在都可能跑不通。

### 坑 3：DashScope 控制台域名下线了

按老教程打开 `dashscope.console.aliyun.com`，直接 404。原来 2026 年 8 月改名成**阿里云百炼**了，新地址是 `bailian.console.aliyun.com`。但 API 后端地址没变，代码不用改。

### 坑 4：Embedding v4 在 LangChain 兼容层里直接报错

就是上面 store.py 那段，`check_embedding_ctx_length=False` 这个参数不加上，请求直接 400。这种坑搜索引擎上搜不到，得自己看报错堆栈和 GitHub issue。

### 坑 5：国内直连 GitHub 推代码推不上去

git push 直接超时，但浏览器能开 GitHub。最后代码是通过网页一个个文件传上去的——没错，9 个文件我在 GitHub 网页上点了十几次 Create new file。

**教训**：部署这种事，先确认网络能不能通，再决定用 git 还是网页。

---

## 六、真实跑起来是什么效果

<!-- TODO: 在这里放今天测试的截图：
     1) 上传了 5 个 PDF（HTTP协议、抓包、视频业务、Linux系统、Linux权限）的截图
     2) 问"简单说下DNS"，AI 基于文档回答权威DNS/递归DNS/转发DNS 的截图
-->

我把手头 5 个 PDF 运维资料（HTTP 协议基础、抓包工具、视频业务、Linux 系统概述、Linux 文件权限）全传上去，建了知识库，开始测：

**问 1：「简单说下 DNS？」**

AI 直接基于上传的网络文档，分三段回答了权威 DNS、递归 DNS、转发 DNS 的区别，连"从根→顶级域→权威域"这条链路都列出来了。完全是从资料里提炼的，没有扯闲篇。

**问 2：「Linux 文件权限 755 是什么意思？」**

它准确答出了 owner/group/other 三层，r=4/w=2/x=1 怎么算，跟我上传的那份 Linux 文档里写的一模一样。

**问 3：「怎么修自行车？」**

它老老实实回："根据现有资料，我没有找到相关答案。"

看到这句我反而放心了——这就是 RAG 该有的样子。**知识库没有的，它不瞎编。** 这比那种一本正经胡说八道的通用大模型靠谱太多。

对我们这种小团队来说，新员工上手速度能快不少。

---

## 七、从 RAG 到 Agent：我手写了一个最小 Agent

RAG 跑通之后，我开始好奇外面说的"AI Agent"到底是什么。翻了一堆教程，发现大家都在讲 LangGraph、CrewAI、Multi-Agent，越看越晕。

后来我换了个思路：**别上框架，直接用 openai SDK 手写**。结果发现，所谓 Agent 核心就一个 while 循环：

```python
while True:
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools_schema,   # 告诉模型"你有这些工具可以用"
    )
    if response.choices[0].message.tool_calls:
        # 模型说要调工具 → Python 执行 → 结果塞回 messages → 继续循环
        result = run_tool(...)
        messages.append({"role": "tool", "content": result})
    else:
        # 模型不调工具了 → 直接输出回答
        print(response.choices[0].message.content)
        break
```

就这 20 行，Agent 的本质全在里面了。我给它注册了 3 个工具：列目录、读文件、写配置文件。然后跟它说"帮我看看这个项目有什么文件，读一下 README，给客户生成一份配置"——**它自己按顺序调了三个工具，中间没要我写任何 if-else**。

后来又加了两层：

- **Plan-and-Execute**：复杂任务先让模型输出一份步骤清单，再按清单执行。它会先跟你说"我打算这么做：1. 列文件 2. 读 README 3. 写配置"，然后再动手。
- **ReAct 容错**：工具报错时不崩溃，把错误信息返回给模型。我故意让它读一个不存在的文件，它自己发现报错后，主动列了一下真实目录，换了个文件继续完成任务。

**最大的收获不是写出了什么厉害的东西，而是破除了神秘感**——Agent 不是什么黑科技，就是"大模型 + 工具 + 一个 while 循环"。那些框架（LangGraph 之类）是给生产环境加状态管理、可观测性、权限控制的，学习阶段真没必要上。

---

## 八、39 岁转行，我学到了什么

说几句掏心窝的：

1. **不要上来就学大模型训练、CUDA、扩散模型**。那些是算法工程师的活，我们这种转行者先把 RAG、Agent、API 调用这些"应用层"玩明白，接外包、做内部工具、转 AI 运维岗都够用。
2. **一个完整的小项目 > 十个半途而废的教程**。这个项目代码量不到 500 行，但从环境配置、踩依赖坑、调提示词、到最后部署上线，每一步都自己趟过一遍，比看十篇文章强。
3. **别害怕 35+**。我 39 了，英语一般，数学也就高中水平，但只要愿意动手，一个月真的能做出能跑的东西。

代码我放 GitHub 了，README 写得很详细，跟着做一下午能跑起来。线上也部署了一个 Demo（加了访问权限，想体验的评论区扣 1）。

下一个目标：把手写 Agent 的工具集升级，让它真能"丢一份客户资料进去，自动吐出一套完整的 RAG 项目"，而不只是在命令行里列目录读文件。

---

**欢迎交流**：评论区聊聊你现在多大、在做什么、想转什么方向。

> 代码开源：[github.com/hsx0099/ops-knowledge-bot](https://github.com/hsx0099/ops-knowledge-bot)
> 在线 Demo：[ops-knowledge-bot-weerwxeyqf8srym qur7ezn.streamlit.app](https://ops-knowledge-bot-weerwxeyqf8srym qur7ezn.streamlit.app)（首次访问需等待 10-30 秒唤醒，免费版会自动休眠）
