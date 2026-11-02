# -*- coding: utf-8 -*-
"""导读 + 第 1–2 章（完整源码 + 关键行注解）。"""

LEAD = ("这个仓库用 17 章的 Python 示例，把 Claude Code 这类编程 Agent 拆开给你看："
        "没有魔法，只有循环、工具、权限、上下文管理和一层层「补丁」。"
        "本教程按 commit 7226f55 讲，代码全部取自该版本的源文件。")

INTRO_HTML = r"""
<div class="intro-card">
  <h3>模型负责「想」，代码负责「让它能动手」</h3>
  <p>大模型只会输出文字。它能写出 <code>rm -rf build</code>，但没有手。所谓 Agent，就是
  <strong>模型 + 一套让它能感知和行动的外壳</strong>——作者把它叫 <b>Harness</b>（载具）。</p>
  <p>这本书不教模型变聪明，只教你怎么造载具：怎么把工具递过去、怎么拦危险操作、
  怎么在上下文快满时腾地方、怎么让多个 Agent 分工。</p>
</div>

<div class="intro-card warn-card">
  <h3>覆盖范围：不是每章都「逐行」</h3>
  <p>章节标题旁会标出代码完整度和注解量，例如「核心节选 · 8 处注解」。
  没有注解的行，就是留给你自己读的。</p>
  <table class="tbl">
  <thead><tr><th>章节</th><th>代码</th><th>注解方式</th></tr></thead>
  <tbody>
  <tr><td>s01–s02</td><td><b>完整源码</b>（整个 code.py）</td><td>关键行注解，每章十几到三十几处</td></tr>
  <tr><td>s03–s08</td><td><b>核心节选</b>（每章 1–3 段）</td><td>节选内关键行注解，其余行自行阅读</td></tr>
  <tr><td>s09–s17</td><td><b>关键片段</b>（每章 1–4 段）</td><td>片段内关键行注解 + 分段说明</td></tr>
  </tbody>
  </table>
  <p>每段代码都标了 <code>L起–L止</code>，可对照固定 commit 的原文逐行读。</p>
</div>

<details class="before">
  <summary>开始之前：环境、费用与安全</summary>
  <p><b>依赖</b>（以仓库 requirements.txt 为准）：anthropic、python-dotenv、PyYAML。</p>
<pre class="sh">git clone https://github.com/shareAI-lab/learn-claude-code
cd learn-claude-code
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

printf 'ANTHROPIC_API_KEY=\nMODEL_ID=\n' &gt; .env
python s01_agent_loop/code.py</pre>
  <p><b>从仓库根目录运行</b>：s07 在 cwd 下找 <code>skills/</code>，s08 把记录写到
  <code>./.transcripts/</code>，文件工具都以启动目录为根。</p>
  <p><b>密钥只放本机 <code>.env</code></b>，不要贴进对话或截图。模型名按你账号实际权限填，
  教程里的示例名不保证可用。<code>ANTHROPIC_BASE_URL</code> 只换地址，服务仍须兼容
  Anthropic Messages 协议。</p>
  <p><b>这些示例会真的执行命令、读写文件、调用模型（产生费用）。</b>建议在干净的虚拟机、
  容器或专门目录里练手，不要在有密钥和重要数据的目录里试。教程练习不需要关闭权限检查。</p>
</details>

<div class="intro-card">
  <h3>怎么读</h3>
  <p><b>第 1–2 章</b>：完整代码，先建立「循环 + 工具分发」的手感。</p>
  <p><b>第 3–8 章</b>：看每章加在循环外面的那一层——权限、钩子、计划、子 Agent、技能、压缩。</p>
  <p><b>第 9–17 章</b>：看机制和关键片段；s15 一个文件 3000 多行，这里只挑主循环、工具池、hook 三处。</p>
  <p>文中会尽量区分<b>本版实现</b>、<b>教学简化</b>和<b>生产建议</b>；看到「生产环境」这类词，
  基本说明源码里没有。</p>
</div>
"""

INTRO = {"lead": LEAD, "html": INTRO_HTML}

CH_A = [
    {
        "id": "s01", "no": "01", "full": True,
        "title": "一个循环就够了", "sub": "Agent Loop",
        "quote": "一个工具 + 一个循环 = 一个 Agent",
        "problem": "模型只会说话不会动手。要让它干活，你得给它一条「行动—观察—再行动」的回路。"
                   "这一章用 40 行左右把回路写出来，后面每一章都是往它外面加东西。",
        "idea": [
            "把「有一个 bash 工具」这件事，用 JSON Schema 告诉模型；",
            "发请求，拿回复；回复里除了文字，还可能有 tool_use（模型说：帮我执行这个）；",
            "你执行完，把结果包成 tool_result 塞回 messages；",
            "再发一次请求，模型看到结果继续决策——直到它不再要工具。",
        ],
        "rel": "s01_agent_loop/code.py",
        "blocks": [{
            "full": True,
            "notes": [
                {"at": "The entire secret of an AI coding agent in one pattern:",
                 "text": "整本书的起点就这一句：AI 编程 Agent 的秘密是一个循环，不是一堆 if-else。"},
                {"at": "        append results",
                 "text": "把这四行背下来：调模型 → 看有没有工具调用 → 执行 → 把结果塞回去。"},
                {"at": "(loop continues)",
                 "text": "注意图里的箭头是闭环的：工具结果回到模型，模型再决定下一步。这是 Agent 和「一问一答」的本质区别。"},
                {"at": "until the model decides to stop.",
                 "text": "停止条件只有一个：模型不再要求用工具。代码本身不判断「任务完成没」——这是 s17 才补的洞。"},
                {"at": "import subprocess",
                 "text": "只用了两个标准库：os 读环境变量，subprocess 执行 shell 命令。没有框架。"},
                {"at": "except ImportError:",
                 "text": "readline 只是为了输入体验（macOS 终端退格不乱码）。整段删掉，程序照样跑。"},
                {"at": "from dotenv import load_dotenv",
                 "text": "dotenv 读同目录的 .env，省得每次开终端都 export 一遍。"},
                {"at": "load_dotenv(override=True)",
                 "text": "override=True：.env 里的值覆盖 shell 里同名的。不加的话，你改了 .env 却发现不生效。"},
                {"at": 'os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)',
                 "text": "走自定义 BASE_URL 时，SDK 可能优先用 AUTH_TOKEN，导致「明明配了 key 却 401」。这里直接删掉，只认 API_KEY。"},
                {"at": "client = Anthropic(base_url=os.getenv",
                 "text": "base_url 为空 = 官方地址；填了 = 你的兼容 Anthropic Messages 协议的地址。协议不兼容，填了也跑不通。"},
                {"at": 'MODEL = os.environ["MODEL_ID"]',
                 "text": "模型名从环境变量来。教程里的示例名不保证你能用，按自己账号的权限填。"},
                {"at": "ENVIRONMENT_PROMPT = (",
                 "text": "先给模型交代运行环境。Windows 上所谓 bash 其实是 cmd.exe，不提醒它就会写出 ls、rm -rf 这种命令。"},
                {"at": "SYSTEM = (",
                 "text": "system prompt 就三件事：你是谁、你在哪个目录、你怎么干活。getcwd() 让相对路径有基准。"},
                {"at": "Act, don't explain.",
                 "text": "这半句很关键。模型天生爱解释，这句话把它往「先动手」推。删掉它，回答会长很多。"},
                {"at": '"name": "bash",',
                 "text": "工具定义就是一份 JSON Schema：名字、描述、参数。模型只能通过这份描述知道「有这么个工具、怎么调」。"},
                {"at": '"required": ["command"],',
                 "text": "required 别漏。不写的话，模型偶尔会传个空对象过来，代码就 KeyError 了。"},
                {"at": "def run_bash(command: str) -> str:",
                 "text": "工具本体就是一个普通 Python 函数：输入字符串，输出字符串。没有基类、没有装饰器。"},
                {"at": "dangerous = [",
                 "text": "这一版没有权限系统，只有一个最粗糙的黑名单。先能跑起来，权限是 s03 的事。"},
                {"at": 'return "Error: Dangerous command blocked"',
                 "text": "被拦截时返回的是一句话，不是抛异常。工具失败也要变成「结果」让模型看到，它才知道换条路。"},
                {"at": "r = subprocess.run(command, shell=True",
                 "text": "shell=True 才能用管道和重定向；cwd 固定工作目录；timeout=120 防止一条命令把整个会话挂死。"},
                {"at": "out = (r.stdout + r.stderr).strip()",
                 "text": "stdout 和 stderr 直接合并。模型不关心这是正常输出还是报错，它要的是「到底发生了什么」。"},
                {"at": 'return out[:50000] if out else "(no output)"',
                 "text": "截断 + 空输出兜底。不截断的话，一条 dmesg 就能把上下文撑爆（s08 专门解决这个）。"},
                {"at": "except subprocess.TimeoutExpired:",
                 "text": "超时、文件找不到、系统错误，全都翻译成人话返回。别让 Python 堆栈打断循环。"},
                {"at": "def agent_loop(messages: list):",
                 "text": "核心循环。messages 是传引用：这个函数会往里 append，调用方拿到的就是同一份历史。"},
                {"at": "tools=TOOLS, max_tokens=8000,",
                 "text": "每次请求都带完整历史和工具表。模型是无状态的，「记忆」全靠你每次重新传。"},
                {"at": 'messages.append({"role": "assistant", "content": response.content})',
                 "text": "先把模型这轮说的话原样存进历史，包括 tool_use 块。后面要靠它的 id 把结果配对回去。"},
                {"at": "if not tool_calls:",
                 "text": "没有工具调用 = 模型认为答完了 = 退出循环。这里的「完成」完全由模型自己声明。"},
                {"at": "for block in tool_calls:",
                 "text": "一轮里模型可能要调多个工具，一个个执行。这里先 for 循环，s02 换成查表分发。"},
                {"at": 'output = run_bash(block.input["command"])',
                 "text": "block.input 就是模型给的参数，SDK 已经帮你解析成 dict 了。"},
                {"at": '"tool_use_id": block.id,',
                 "text": "这个 id 必须原样回传。模型靠它把「我请求的调用」和「你给我的结果」对上号，对不上直接报错。"},
                {"at": 'messages.append({"role": "user", "content": results})',
                 "text": "工具结果以 user 身份回填——这是 Anthropic 协议的约定：tool_result 属于 user 消息的一种。"},
                {"at": "history = []",
                 "text": "整场对话只有这一份历史，循环内外共用。这就是它能记住上一轮干了什么的原因。"},
                {"at": "query = input(",
                 "text": "一个极简 REPL：一行输入 = 一轮对话。q 退出。"},
                {"at": 'if query.strip().lower() in ("q", "exit"):',
                 "text": "strip() 先去掉首尾空格，避免用户多敲一个空格就匹配不上。"},
                {"at": "agent_loop(history)",
                 "text": "每次输入都接着同一份 history 继续跑，而不是新开一段。"},
                {"at": "if isinstance(response_content, list):",
                 "text": "循环结束后，最后一条 assistant 消息里可能有好几个内容块，只打印文字。"},
            ],
        }],
        "points": [
            ("四步循环", "问模型 → 执行工具 → 回填结果 → 再问。本课程后面每一章都沿用这个骨架。"),
            ("停止 = 模型不再要工具", "代码不判断任务完成度，这是 s17 Goal Loop 要补的洞。"),
            ("模型无状态", "messages 就是它的全部记忆，每轮完整传回，所以上下文管理（s08）才重要。"),
            ("错误也是结果", "工具失败返回字符串而不是抛异常，模型才能读到并自己纠错。"),
        ],
        "pitfalls": [
            "回填 tool_result 时漏了 tool_use_id，或 id 对不上，API 会直接 400。",
            "忘了设 timeout 和输出截断，一条 `yes` 就能让会话一直转下去。",
            "把 tool_result 塞进 assistant 消息里，协议不认——它必须放在 user 消息中。",
        ],
        "try": "把 SYSTEM 里的 \"Act, don't explain.\" 删掉，再问「看看这个目录有什么」。验收：回答明显变长、开始解释而不是直接调用 bash。改完记得改回来。",
    },
    {
        "id": "s02", "no": "02", "full": True,
        "title": "加工具只加一行", "sub": "Tool Use",
        "quote": "循环不用动，新工具注册进 dispatch map 就行",
        "problem": "只有 bash 时，模型读文件要 cat、改文件要 sed，既容易写错，也没法限制它乱翻文件。"
                   "这一章加四个专用工具（读、写、改、找），把「调哪个函数」从硬编码变成查表。",
        "idea": [
            "每个工具 = 一个 handler 函数 + 一份 JSON Schema；",
            "所有 handler 收进一张字典 TOOL_HANDLERS，工具名 → 函数；",
            "循环里把 run_bash(...) 换成 TOOL_HANDLERS[name](**args)；",
            "所有文件路径先过 safe_path，出不了工作目录。",
        ],
        "rel": "s02_tool_use/code.py",
        "blocks": [{
            "full": True,
            "notes": [
                {"at": "Key insight: the loop stays the same",
                 "text": "本章最重要的一句：加工具不需要动循环。如果你为了加个工具要改循环，说明分发结构没做好。"},
                {"at": "WORKDIR = Path.cwd()",
                 "text": "把工作目录固定成一个 Path 对象。所有文件工具都拿它当根，越界一律拒绝。"},
                {"at": "def safe_path(p: str) -> Path:",
                 "text": "文件工具的守门员：相对路径先拼成绝对路径，再检查是不是还在工作目录里。"},
                {"at": "if not path.is_relative_to(WORKDIR):",
                 "text": "is_relative_to 能挡住 ../../etc/passwd 这类路径穿越——注意要先 resolve()，否则符号链接能绕过。"},
                {"at": 'raise ValueError(f"Path escapes workspace: {p}")',
                 "text": "抛异常，由调用方的 except 统一转成错误字符串。异常在内层飞，不出工具边界。"},
                {"at": "def run_read(path: str, limit",
                 "text": "读文件支持 limit：先读 50 行看看，需要再往下读，不用一次把大文件塞进上下文。"},
                {"at": 'lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]',
                 "text": "截断时告诉模型「还有多少行」。只截断不提示，它会以为文件就这么长。"},
                {"at": "file_path.parent.mkdir(parents=True, exist_ok=True)",
                 "text": "写文件顺手建父目录。不然模型得先 mkdir 再 write，多一轮对话就多一份上下文。"},
                {"at": "text.replace(old_text, new_text, 1)",
                 "text": "只替换第一次出现。这是 edit 工具的语义：改一处就是改一处，不会把同名代码全改掉。"},
                {"at": "if old_text not in text:",
                 "text": "找不到原文就明确报错，让模型重新读一遍再改，而不是「尽力而为」地瞎写。"},
                {"at": "matches = sorted({",
                 "text": "glob 结果先去重再排序。集合推导里的条件又检查了一次越界——文件工具的安全检查做了两层。"},
                {"at": "shown = matches[:200]",
                 "text": "最多返回 200 条，超了提示「还有更多，请缩小范围」。列表太长同样是上下文炸弹。"},
                {"at": "TOOLS = [",
                 "text": "五个工具的 schema 全是手写 JSON。真实产品会用装饰器或类型注解生成，本质一样。"},
                {"at": "TOOL_HANDLERS = {",
                 "text": "dispatch map：工具名 → 函数。加工具只需要在这张表里加一行。"},
                {"at": "# s02: output = TOOL_HANDLERS",
                 "text": "对比 s01：原来是 run_bash(block.input[\"command\"])，固定得死死的；现在是查表 + 展开参数。"},
                {"at": "handler = TOOL_HANDLERS.get(block.name)",
                 "text": "用 get 而不是 []：模型偶尔会编出不存在的工具名，这时返回「未知工具」，而不是让程序崩掉。"},
                {"at": 'output = handler(**block.input) if handler else f"Unknown: {block.name}"',
                 "text": "**block.input 把 JSON 参数按名字展开成关键字参数——所以 schema 里的参数名必须和函数形参一模一样。"},
            ],
        }],
        "points": [
            ("加工具 = schema + handler + 表里一行", "在这套 dispatch 结构里，加工具不需要碰循环。"),
            ("先 resolve 再判断", "路径安全检查必须在解析完 .. 和符号链接之后做，否则形同虚设。"),
            ("参数名必须对齐", "schema 里的 key 就是 Python 的 kwarg 名，错一个字母就是 TypeError。"),
            ("工具只返回字符串", "成功、失败、空结果，一律是字符串；模型的世界里没有异常。"),
        ],
        "pitfalls": [
            "用 `WORKDIR / p` 但不 resolve，`../` 一路能跑到根目录。",
            "edit 用 replace 不带次数限制，改一处结果全文件同名代码都被改了。",
            "read 不限行数，模型一条命令读了 5000 行日志，这一轮的上下文基本就废了。",
            "注意：safe_path 只约束「文件工具」的路径，bash 仍然能访问工作区外的任何东西——它不是沙箱。",
        ],
        "try": "加一个 `list_dir` 工具：写 handler、加一段 schema、在 TOOL_HANDLERS 里加一行。验收：循环代码一个字没改，模型能成功调用它；再给 read_file 传 `../../etc/hosts`，应返回 `Error: Path escapes workspace`。",
    },
]
