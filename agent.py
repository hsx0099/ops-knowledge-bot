"""
阶段 2：手写一个最简 Agent
==========================
不依赖 LangChain 的 AgentExecutor，直接用 openai SDK 的 tools 参数。

Agent 的本质（看完这段代码你就懂了）：
    while True:
        1. 把对话历史发给模型，告诉它"你有这些工具可以用"
        2. 模型要么：
           a) 返回一段普通文字 → 打印，结束循环
           b) 返回一个工具调用请求 → Python 执行这个工具，把结果塞回对话历史，回到第 1 步
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from config import LLM_MODEL, LLM_BASE_URL

load_dotenv()

# 初始化客户端（和 chain.py 里用的是同一个模型、同一个 base_url）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=LLM_BASE_URL,
)


# ============ 第一步：定义工具函数 ============
# 这些就是 Python 普通函数，Agent 不会自己跑——它只是"决定"要调哪个，真正干活的是这里的代码

def list_files() -> str:
    """列出当前目录下有哪些文件和子文件夹"""
    entries = os.listdir(".")
    return "当前目录内容：\n" + "\n".join(f"  - {e}" for e in entries)


def read_text_file(path: str) -> str:
    """读取一个文本文件的内容"""
    if not os.path.exists(path):
        return f"错误：文件 {path} 不存在"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return f"文件 {path} 内容（前 2000 字）：\n{content[:2000]}"


def write_config(customer_name: str, greeting: str) -> str:
    """给客户生成一个 config.json 配置文件"""
    config = {
        "customer": customer_name,
        "app_name": f"{customer_name} 知识库",
        "welcome_message": greeting,
    }
    filename = f"config_{customer_name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return f"已生成配置文件 {filename}，内容：\n{json.dumps(config, ensure_ascii=False, indent=2)}"


# 把上面的函数装进一个字典，名字 → 函数本体
TOOLS_FUNCTIONS = {
    "list_files": list_files,
    "read_text_file": read_text_file,
    "write_config": write_config,
}


# ============ 第二步：用 JSON Schema 描述工具给模型看 ============
# 模型看不懂 Python 函数，但看得懂这个 schema——它就靠这个决定调哪个
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出当前项目目录下的所有文件和子文件夹",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "读取一个文本文件的内容（.py / .md / .txt / .json 等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要读的文件路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_config",
            "description": "根据客户名和欢迎语，生成一份 config.json 配置文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "客户名称，例如 'XX银行运维部'"},
                    "greeting": {"type": "string", "description": "给客户用户的欢迎语"},
                },
                "required": ["customer_name", "greeting"],
            },
        },
    },
]


# ============ 第三步：Plan 阶段 ============
def make_plan(user_message: str) -> str:
    """
    先不让模型调工具，只让它输出一份执行计划
    这样用户能在真正动手之前，看到 Agent 打算怎么做
    """
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个项目规划助手。根据用户的需求，输出一份简短的中文执行计划（3-5 步，编号列表）。"
                           "不要调用任何工具，不要执行，只输出计划本身。",
            },
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


# ============ 第四步：Execute 阶段（原来的工具循环）============
def run_agent(user_message: str):
    # ① 先出计划
    print(f"\n{'='*60}")
    print(f"🧑 用户: {user_message}")
    print(f"{'='*60}")

    plan = make_plan(user_message)
    print(f"\n📋 Agent 计划:\n{plan}\n")
    print(f"{'-'*60}\n开始执行...\n{'-'*60}")

    # ② 再进入工具循环
    messages = [
        {
            "role": "system",
            "content": "你是一个项目助手。按上面的计划逐步执行。"
                       "需要用工具时就调用，所有工具调用完成后，用中文给用户一个总结。"
                       "如果某个工具调用失败（文件不存在、参数错误等），请阅读错误信息，"
                       "换个路径或换个工具重试，不要直接放弃。",
        },
        {"role": "user", "content": f"需求：{user_message}\n计划：{plan}"},
    ]

    while True:
        # 1. 把对话历史 + 工具列表发给模型
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # 2a. 模型决定调工具
        if msg.tool_calls:
            # 先把模型这条"我要调工具"的消息存回历史
            messages.append(msg.model_dump())

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"\n🔧 模型要调工具: {tool_name}({tool_args})")

                # ReAct 关键：工具执行出错时不崩溃，把错误信息返回给模型
                # 模型看到错误后，会自己决定换个路径/换个工具/放弃
                try:
                    result = TOOLS_FUNCTIONS[tool_name](**tool_args)
                except Exception as e:
                    result = f"❌ 工具执行失败: {type(e).__name__}: {e}。请检查参数，或换一个工具/方式重试。"
                    print(f"⚠️ 工具报错: {result}")

                print(f"📤 工具返回:\n{result[:500]}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            # 回到 while 开头，再问模型一次
            continue

        # 2b. 模型不调工具了，直接给最终回答
        print(f"\n🤖 助手: {msg.content}")
        break


if __name__ == "__main__":
    # ReAct 测试：故意让模型读一个不存在的文件，看它会不会读错误信息后换个文件
    run_agent("帮我读一下 not_exist.py 这个文件，然后告诉我项目结构")
