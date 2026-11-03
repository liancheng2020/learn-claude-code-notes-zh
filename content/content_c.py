# -*- coding: utf-8 -*-
"""第 9–17 章（进阶：关键片段）+ 结语。"""

CH_C = [
    {
        "id": "s09", "no": "09", "advanced": True,
        "title": "跨会话记住该记的", "sub": "Memory",
        "quote": "把以后还会用到的信息留下来",
        "problem": "每开一个新会话都从零开始：昨天定下的约定、这个项目的坑，今天还得再说一遍。"
                   "把整段历史都带上又太重。",
        "idea": [
            "记忆写成 markdown 文件，外加一份索引（名字 + 一句话）；",
            "每轮结束抽取候选记忆，先判断值不值得记、是否重复，再写盘并重建索引；",
            "下一轮开始时，把「目录 + 当前请求」给模型，让它挑编号召回；",
            "模型不可用就退回关键词匹配——记忆坏了不能拖垮主流程。",
        ],
        "rel": "s09_memory/code.py",
        "blocks": [{
            "from": "def keyword_memory_selection(",
            "to": 'return json.dumps(loaded, ensure_ascii=False, indent=2) if loaded else ""',
            "notes": [
                         {"at": "def keyword_memory_selection(", "text": "兜底方案：把用户这句话切成词，和记忆的名字、描述做匹配打分。粗糙，但不需要模型，通常都能用。"},
                         {"at": "return [filename for _, filename in ranked[:max_items]]", "text": "只取前几条。召回宁缺毋滥——塞十条不相干的记忆，比不塞更糟。"},
                         {"at": "def select_relevant_memories(messages: list, max_items: int = 5) -> list[str]:", "text": "主方案让模型自己挑：给一份带编号的目录和当前请求，让它只回一个 JSON 数组，比如 [0, 2]。"},
                         {"at": "return keyword_memory_selection(records, query, max_items)", "text": "模型调用一失败就退回关键词匹配。记忆是增强功能，不能变成单点故障。"},
                         {"at": "def load_memories(messages: list) -> str:", "text": "选中后按字符预算截断，拼成 JSON 注入 system prompt；预算用完就停。"},
                         {"at": "ranked.sort", "text": "按命中词数从高到低排，分高的先取。"},
                         {"at": "catalog = \"\\n\".join(", "text": "把目录拼成「编号: 名字 - 描述」，给模型挑。"},
                         {"at": "prompt = (", "text": "提示只要求返回 JSON 下标数组，解析简单。"},
                         {"at": "response = client.messages.create(", "text": "这一步也要调一次模型；失败就走兜底。"},
                         {"at": "indices = extract_json_array(", "text": "解析下标；越界、非整数会被过滤。"},
                         {"at": "selected = []", "text": "去重并限制条数，最多 5 条。"},
                         {"at": "loaded = []", "text": "按预算依次读正文，读满就停。"},
                         {"at": "for filename in select_relevant_memories(messages):", "text": "只读选中的记忆，不整库加载。"},
                         {"at": "score = sum(word in catalog_text for word in words)", "text": "按命中的关键词数量打分；一个都没中就跳过。"},
                     ],
        }],
        "points": [
            ("两级结构", "索引常驻（便宜），正文按需（贵）。和 s07 技能加载是同一个套路。"),
            ("召回要有 query", "拿当前用户请求去匹配，而不是把所有记忆一股脑塞进去。"),
            ("写入发生在轮末", "这一版在每轮结束后抽取候选记忆并整理索引，不是边聊边写。"),
            ("一定要能降级", "模型挑选失败 → 关键词匹配；匹配失败 → 不召回。"),
        ],
        "pitfalls": [
            "什么都记：一次性的调试细节也写进去，下次召回全是噪声。",
            "记忆和当前代码冲突：记着「用 npm」，但项目早换 pnpm 了，模型会照记忆办事。",
            "召回条数不设上限，一次塞进十条长记忆，上下文直接见底。",
        ],
        "try": "让它记住「这个项目用 pnpm，不要用 npm」，然后开一个新会话直接问「装个依赖用哪个命令」。验收：新会话里模型引用了这条记忆，或回答里明确说「按记忆用 pnpm」。",
    },
    {
        "id": "s10", "no": "10", "advanced": True,
        "title": "任务落盘，进度可恢复", "sub": "Task System",
        "quote": "依赖「未完成」才阻塞，列表非空不算",
        "problem": "s05 的清单只在内存里，进程一挂就没了；而且没有依赖关系，A 还没做完就去做 B。"
                   "这一章把任务写成文件，加上状态和依赖——但注意它没有并发保护。",
        "idea": [
            "每个任务一个 JSON 文件，状态只有 pending → in_progress → completed；",
            "blockedBy 存依赖 id，认领前检查的是「这些依赖里还有没有没完成的」；",
            "id 用随机 hex，靠「独占创建」保证不撞名；",
            "完成任务时校验状态和 owner；这一版没有文件锁。",
        ],
        "rel": "s10_task_system/code.py",
        "blocks": [
            {
                "from": 'def create(self, subject: str, description: str = "") -> Task:',
                "to": "except FileExistsError:",
                "notes": [
                             {"at": "for _ in range(100):", "text": "建任务 = 在 tasks/ 下写 JSON；撞名就重试，最多 100 次。"},
                             {"at": "except FileExistsError:", "text": "x 模式只保证独占创建、不覆盖已有文件；json.dump 中途失败仍可能留下半个文件。"},
                         ],
            },
            {
                "from": 'def claim_task(task_id: str, owner: str = "agent") -> str:',
                "to": 'task.status = "in_progress"',
                "notes": [
                             {"at": "def claim_task(task_id: str, owner: str = \"agent\") -> str:", "text": "认领只做两件检查：状态是不是 pending、依赖里有没有没完成的。没有锁，也没有 owner 冲突检查。"},
                             {"at": "if dependencies:", "text": "只有「未完成的依赖」才挡人；blockedBy 非空但都完成了，照样能开工。"},
                             {"at": "task.status = \"in_progress\"", "text": "状态单向流转，没有取消、没有退回。想重做只能再建一个任务。"},
                         ],
            },
        ],
        "points": [
            ("文件即存储", "一个任务一个 JSON，可视化、可手改、可 diff。"),
            ("依赖看「完成没」", "blockedBy 里有值不代表被挡；只有其中存在未完成（或找不到）的任务才阻塞。"),
            ("状态单向", "pending → in_progress → completed，没有回退和取消。"),
            ("没有并发保护", "两个进程同时 claim 同一个任务，可能都成功——锁是 s13 才加的。"),
            ("完成才校验 owner", "complete_task 会检查 status 和 owner；claim 时不检查 owner。"),
        ],
        "pitfalls": [
            "把「blockedBy 非空」当成「不能开工」——实际只挡未完成的依赖。",
            "在多进程/多 agent 场景直接用它：没有锁，会重复认领。",
            "依赖的任务文件被删了：加载失败也算「未完成」，于是一直被挡住，直到文件恢复。",
            "手改 JSON 改坏了结构，load 时会直接抛错。",
        ],
        "try": "按顺序做：① create_task 建 A、B、C、D 四个任务，记下 id；② update_task(B, addBlockedBy=[A])、update_task(D, addBlockedBy=[C])；③ claim_task(B) → 返回 `Blocked by: [A]`；④ claim_task(A) → `Claimed`，再 complete_task(A) → `Completed`；⑤ claim_task(B) → 这次返回 `Claimed`；⑥ 删掉 `.tasks/<C>.json` 后 claim_task(D) → 返回 `Blocked by: [C]`（缺失的依赖也算未完成）。注意 complete_task(A) 前必须先 claim_task(A)，否则会因为状态不是 in_progress 被拒。",
    },
    {
        "id": "s11", "no": "11", "advanced": True,
        "title": "慢操作丢后台", "sub": "Background Tasks",
        "quote": "慢命令放后台线程，主循环继续转",
        "problem": "跑一次测试要三分钟。主循环就干等着，用户也没法插话，体验像卡死。",
        "idea": [
            "给 bash 加 run_in_background 参数；",
            "起一个线程跑子进程，任务 id 和状态存在管理器里；",
            "主循环每轮开头 collect 一次完成的任务；",
            "把结果包成 <task_notification> 注入上下文。",
        ],
        "rel": "s11_background_tasks/code.py",
        "blocks": [{
            "from": "class BackgroundManager:",
            "to": "return notifications",
            "notes": [
                         {"at": "class BackgroundManager:", "text": "管理器就三样东西：任务表、结果表、待领取队列。都在内存里。"},
                         {"at": "self._lock = threading.Lock()", "text": "两个线程可能同时改状态，所有读写都进锁；否则结果会被取走两次。"},
                         {"at": "def collect(self) -> list[str]:", "text": "主循环每轮开头调一次 collect：把已完成的任务取出来，变成通知。"},
                         {"at": "<summary>{result[:500]}</summary>", "text": "只给 500 字摘要，避免上下文被后台输出撑爆；完整结果没有落盘。"},
                         {"at": "return notifications", "text": "返回一组字符串，塞进 messages 的 user 消息里——模型看到的就是「有个后台任务完成了」。"},
                         {"at": "for task_id, task, result in ready:", "text": "把完成的任务拼成通知文本。"},
                         {"at": "raise ValueError(\"Bash command cannot be empty\")", "text": "只接受 bash；命令必须是非空字符串，否则直接拒绝。"},
                         {"at": "print(f\"  [background] started {task_id}: {command[:60]}\")", "text": "在锁里分配 id、登记 running；再起 daemon 线程，启动失败回滚。"},
                         {"at": "except Exception as error:", "text": "线程体：跑命令，把结果或异常格式化。"},
                         {"at": "self._ready.append(task_id)", "text": "加锁写状态和结果，再把 id 放进待领取队列。"},
                     ],
        }],
        "points": [
            ("只有 bash 能后台", "文件读写/搜索是毫秒级，结果要马上用；只有 shell 可能长跑。"),
            ("锁保护共享状态", "后台线程 + 主线程；不加锁可能重复取走同一结果，或丢掉刚写入的通知。"),
            ("通知只给摘要", "通知只留 id、状态、原命令和前 500 字；完整结果在内存里，进程退出就没了。"),
            ("整组杀进程", "后台命令通常带管道，只杀父进程会留下孤儿。"),
            ("daemon 线程，不是独立进程", "进程一退，后台任务跟着没；电脑休眠也不会继续跑。"),
            ("没人收就堆着", "不调 collect，结果留在内存，模型也收不到通知。"),
        ],
        "pitfalls": [
            "以为关掉终端它还在跑——不会，线程随进程结束。",
            "后台进程泄漏：用户退出会话了，子进程可能还活着。",
            "输出无限增长：tail -f 这种命令会把内存吃满，必须有大小上限。",
            "collect 调用太晚，通知堆了几十条，一次全塞给模型。",
        ],
        "try": "让它后台跑 `sleep 5 && echo done`，同时继续问它别的问题。验收：5 秒后收到一条 `<task_notification>`，里面能看到 task_id 和摘要，而主对话在这 5 秒里没有卡住。",
    },
    {
        "id": "s12", "no": "12", "advanced": True,
        "title": "到点自己开工", "sub": "Cron Scheduler",
        "quote": "进程内定时轮询，到点入队",
        "problem": "「每天早上 9 点跑测试」「每 30 分钟看一次 CI」——总不能让用户每次到点手动敲一遍。",
        "idea": [
            "存一条 cron 表达式 + 一段 prompt；",
            "后台线程每隔一段时间检查是否匹配当前时间；",
            "匹配就把 prompt 塞进队列；",
            "Agent 空闲时取队列，当作一条用户消息注入。",
        ],
        "rel": "s12_cron_scheduler/code.py",
        "blocks": [{
            "from": "def cron_matches(cron_expr: str, moment: datetime) -> bool:",
            "to": "return day_matches or weekday_matches",
            "notes": [
                {"at": "def cron_matches(cron_expr: str, moment: datetime) -> bool:",
                 "text": "自己实现 5 段 cron：分、时、日、月、周。没有依赖库，逻辑一目了然。"},
                {"at": "cron_weekday = (moment.weekday() + 1) % 7",
                 "text": "Python 里周一 = 0，cron 里周日 = 0。这一行换算错，你的「每周一」就会变成「每周日」。"},
                {"at": 'if day == "*" and weekday == "*":',
                 "text": "日和周都不限，直接匹配。真正麻烦的是下面两种情况。"},
                {"at": "return day_matches or weekday_matches",
                 "text": "日和周都被指定时是「或」关系，不是「与」——这是 cron 的历史坑。"},
            ],
        }],
        "points": [
            ("5 段 cron", "分 时 日 月 周，够用且好读。"),
            ("日/周是 or", "同时指定时，任意一个匹配就触发。"),
            ("任务持久化", "cron 任务会写到磁盘（save_durable_jobs），进程重启后还能读回来。"),
            ("同一分钟只触发一次", "用 minute_marker 去重，否则一小时内会触发 60 次。"),
            ("进程内轮询，不是系统 cron", "程序退出、电脑休眠时不会执行；醒来也不会把错过的补上。"),
        ],
        "pitfalls": [
            "以为它像系统 cron 一样常驻——它只是主进程里的一个线程。",
            "时区：服务器 UTC、用户东八区，早上 9 点可能变成下午 5 点。",
            "重复触发：每分钟检查一次，但没记录「这一分钟已经跑过」。",
        ],
        "try": "加一条 `*/2 * * * *` 的任务，观察它是不是每两分钟自己跑一次。验收：队列里出现两次间隔 2 分钟的注入记录；把进程停掉 5 分钟再启动，验收：错过的两次不会补跑。",
    },
    {
        "id": "s13", "no": "13", "advanced": True,
        "title": "多个 Agent 抢任务", "sub": "Agent Teams",
        "quote": "文件锁 + 一个进行中任务 + 可选 worktree",
        "problem": "任务多了要并行。一旦并行，就会抢同一个任务、互相踩同一个文件。",
        "idea": [
            "共享任务板（s10 的文件任务）+ 一把锁；",
            "认领必须在锁里完成「读—检查—改—写」；",
            "一个队友同一时间只能干一件事；",
            "可选 worktree：显式创建并绑定后，队友才有独立工作目录。",
        ],
        "rel": "s13_agent_teams/code.py",
        "blocks": [{
            "from": 'def claim_task(task_id: str, owner: str = "agent") -> str:',
            "to": 'return f"Claimed {task.id} ({task.subject})"',
            "notes": [
                         {"at": "def claim_task(task_id: str, owner: str = \"agent\") -> str:", "text": "和 s10 的核心区别：整个认领过程放进锁里。多 agent 场景下，这一句就是全部。"},
                         {"at": "with task_store_lock():", "text": "两把锁：RLock 管同进程线程，flock 管不同进程；锁文件是任务目录的 .lock。"},
                         {"at": "if assignment:", "text": "一个队友同时只能有一个任务。不然它会开五个任务、每个都干一半。"},
                         {"at": "teammate_assignments[owner] = {\"task_id\": task.id, \"cwd\": cwd}", "text": "认领时绑定工作目录。cwd 默认是仓库目录；只有显式建了 worktree，才会指向那个 worktree。"},
                         {"at": "current = _owner_in_progress(owner)", "text": "同一 owner 一次只能领一个任务；先查手头有没有进行中的。"},
                         {"at": "task.owner = owner", "text": "检查都过了才写状态：先落盘，再更新 assignment。"},
                     ],
        }],
        "points": [
            ("认领要原子", "不加锁的「先查再改」，并发下可能抢到同一个任务。"),
            ("一个 owner 一件事", "限制并发度，比事后收拾半成品便宜。"),
            ("锁是跨线程 + 跨进程的", "RLock 管线程，flock 管进程，两层都要。"),
            ("worktree 是可选机制", "不建就没有独立目录；建了也只是工作目录隔离，不是权限或安全隔离。"),
            ("完成要验 owner", "防止 A 把 B 的任务标成完成。"),
        ],
        "pitfalls": [
            "把 worktree 当沙箱：它只是另一个 git 工作目录，文件系统权限完全一样。",
            "锁粒度太大（锁住整个任务执行），并行退化成串行。",
            "worktree 建了没清理，磁盘里堆一堆分支和目录。",
            "队友之间看不到彼此进度，重复调研同一件事。",
        ],
        "try": "起两个队友同时抢同一个任务。验收：第二个收到「already owned / must finish」之类的拒绝，而不是也返回 Claimed。再给其中一个建 worktree，验收：它的文件工具 cwd 指向新目录，另一个仍在原目录。",
    },
    {
        "id": "s14", "no": "14", "advanced": True,
        "title": "工具改由外部提供", "sub": "MCP",
        "quote": "内存版 mock：清单 + 宿主策略，没有真实传输",
        "problem": "每接一个外部服务（文档、部署平台），就要手写工具定义、参数格式、调用代码。接十个就乱成一锅粥。",
        "idea": [
            "服务端声明「我有哪些工具、参数是什么」；",
            "宿主负责连接、改名、加权限策略，再并进工具池；",
            "调用统一走 call_tool，异常收成字符串；",
            "要不要审批由宿主配置决定，不信任服务端的描述。",
        ],
        "rel": "s14_mcp_plugin/code.py",
        "blocks": [{
            "from": "class MCPClient:",
            "to": '("deploy", "trigger"): "confirm",',
            "notes": [
                         {"at": "class MCPClient:", "text": "本章 MCP 是内存替身：模拟 tools/list 与 tools/call，没有真实 stdio/HTTP 连接。"},
                         {"at": "def register(self, tool_defs: list[dict], handlers: dict[str, callable]):", "text": "注册时先校验：名字非空、不重复、每个工具都有实现。第三方的东西，进门先体检。"},
                         {"at": "def call_tool(self, tool_name: str, args: dict) -> str:", "text": "调用只做一件事：按名找 handler，展开参数，把异常收成字符串。"},
                         {"at": "return f\"MCP error: {type(exc).__name__}: {exc}\"", "text": "不能把第三方异常直接抛进主循环——那会让整个 agent 崩掉，而不是让模型看到一条错误。"},
                         {"at": "MCP_HOST_POLICY = {", "text": "最关键的安全设计：某个工具要不要审批，由宿主的策略表决定，而不是读服务端自己写的 description。"},
                     ],
        }],
        "points": [
            ("这是 mock，不是真实连接", "没有 JSON-RPC、没有 stdio/HTTP transport；换成真协议要另写连接层。"),
            ("工具池是动态的", "连上服务才知道有哪些工具，schema 和 handler 一起并入。"),
            ("宿主掌握策略", "服务端的描述是「广告」，不是「授权」；没配置默认 confirm。"),
            ("错误收成字符串", "外部代码失败，对模型来说就是一次普通的工具失败。"),
            ("命名要归一化", "外部工具名可能带奇怪字符，先清洗再加 mcp__server__ 前缀。"),
        ],
        "pitfalls": [
            "以为跑通这一章就等于接上了真实 MCP 服务——中间还差一整个传输层。",
            "工具名冲突：归一化后撞名会直接报错，不会静默覆盖。",
            "把服务端的描述当指令直接塞进 prompt，等于让第三方给你下命令。",
            "连接失败就整个启动失败，生产环境应降级成「这个服务不可用」。",
        ],
        "try": "照着 _mock_server_docs 再写一个 mock server，只暴露一个工具。验收：工具以 `mcp__<server>__<tool>` 出现在工具池里，且没有在 MCP_HOST_POLICY 配置时调用会要求确认。",
    },
    {
        "id": "s15", "no": "15", "advanced": True,
        "title": "把前面的机制装进一个循环", "sub": "Integrated Harness",
        "quote": "一个循环 + 两个注册表",
        "problem": "前面每章都是独立 demo。真实系统要把工具、权限、钩子、记忆、任务、团队、插件装在一起，"
                   "而且不能互相打架——这一个文件有 3000 多行。"
                   "读之前最好先看 s05 的 todo 和 s08 的压缩；忘了可以翻术语表。",
        "idea": [
            "仍然是一个 while 循环：每轮装配工具池、准备上下文、调模型、分发工具；",
            "工具池 = 内置工具 + 所有 MCP 工具，每轮重新合成；",
            "权限、日志、大输出、收工统计全是 hook，不是循环里的 if；",
            "定时任务、后台通知、todo 提醒、上下文压缩都在循环头尾按顺序发生。",
        ],
        "rel": "s15_integrated_harness/code.py",
        "blocks": [
            {
                "from": "def assemble_tool_pool()",
                "to": "return tools, handlers",
                "notes": [
                             {"at": "def assemble_tool_pool()", "text": "能力装配点：把内置工具和所有已连接 MCP 服务的工具合成一份 (schemas, handlers)。"},
                             {"at": "for server_name, mcp_client in mcp_clients.items():", "text": "每个连上的服务都遍历一遍；中途新连上的服务，下一轮就会生效。"},
                             {"at": "prefixed = f\"mcp__{safe_server}__{safe_tool}\"", "text": "加前缀，避免外部工具和内置工具重名。"},
                             {"at": "tools.append({", "text": "每个 MCP 工具带自己的 schema，直接并进工具池。"},
                             {"at": "handlers[prefixed] = (", "text": "这个函数带着创建时的 client/tool，把调用转发给对应服务。"},
                             {"at": "if prefixed in origins:", "text": "工具名过长、归一化后撞名都直接报错，并带上两个来源。"},
                             {"at": "mcp_tool_policies = policies", "text": "handler 带着创建时的 client/tool；MCP_HOST_POLICY 在顶部，默认 confirm。"},
                         ],
            },
            {
                "from": "HOOKS = {",
                "to": 'register_hook("Stop", stop_hook)',
                "notes": [
                             {"at": "HOOKS = {", "text": "扩展点注册表：四个事件，每个挂一串回调。"},
                             {"at": "def register_hook(event: str, callback):", "text": "注册就是 append。没有任何框架。"},
                             {"at": "result = callback(*args)", "text": "PreToolUse 和 Stop 的非 None 返回会生效；PostToolUse 的返回值被丢弃。"},
                             {"at": "register_hook(\"PreToolUse\", permission_hook)", "text": "权限检查是一个 hook，不是写死在循环里的 if。想换策略，换这一行。"},
                             {"at": "register_hook(\"Stop\", stop_hook)", "text": "收工前还能插一脚；本版这里只打印统计，不阻止退出。"},
                             {"at": "if (block.name.startswith(\"mcp__\")", "text": "MCP 工具默认要确认，除非宿主策略放行。"},
                             {"at": "def log_hook(block):", "text": "日志 hook 只观察。"},
                             {"at": "def large_output_hook(block, output):", "text": "大输出只告警。"},
                             {"at": "def user_prompt_hook(query: str):", "text": "用户提交时打印工作目录。"},
                             {"at": "def stop_hook(messages: list):", "text": "收工前统计 tool_result 数量。"},
                             {"at": "for msg in messages:", "text": "遍历消息，数 tool_result 的个数。"},
                             {"at": "interactive shell approval is unavailable", "text": "异步轮次 = 后台线程自动跑的一轮（cron/团队/后台任务），没有终端可问。"},
                             {"at": "if block.name == \"bash\":", "text": "bash 先查黑名单；命中直接拒，不问人。"},
                             {"at": "for pattern in DENY_LIST:", "text": "再校验参数类型和危险词；通过后才问 y/N。"},
                             {"at": "if block.name in (\"read_file\", \"write_file\", \"edit_file\"):", "text": "文件工具只查路径是否还在工作区。"},
                         ],
            },
            {
                "from": "def agent_loop(messages: list, context: dict, active_request: str):",
                "to": "response = call_llm(messages, context, tools, state, max_tokens)",
                "notes": [
                             {"at": "def agent_loop(messages: list, context: dict, active_request: str):", "text": "主循环。比前几章多了 context 和 active_request——压缩和记忆都要用。"},
                             {"at": "state = RecoveryState()", "text": "循环前先装一次，首轮又被重装覆盖；每轮重装是为了接新 MCP。"},
                             {"at": "fired = consume_cron_queue()", "text": "定时任务到点后在这里被取出来，作为 [Scheduled] 用户消息注入。"},
                             {"at": "inject_background_notifications(messages)", "text": "后台任务完成的通知也在循环头统一注入。"},
                             {"at": "if rounds_since_todo >= 3:", "text": "和 s05 一样的提醒机制：连续 3 轮没更新 todo 就补一句。"},
                             {"at": "prepare_context(messages, active_request)", "text": "s08 的四步压缩入口：外置 → 归档 → 截断 → 摘要。"},
                             {"at": "response = call_llm(messages, context, tools, state, max_tokens)", "text": "统一模型入口，重试和错误处理都在 call_llm 里，循环本身不关心。"},
                         ],
            },
            {
                "from": 'if block.name == "compact":',
                "to": "messages.append({\"role\": \"user\", \"content\": build_user_content(results)})",
                "notes": [
                             {"at": "if block.name == \"compact\":", "text": "从循环体的这里看：模型主动要求压缩，先回一条确认，本轮结束再真正压。"},
                             {"at": "blocked = trigger_hooks(\"PreToolUse\", block)", "text": "权限检查在分发之前，而且对每个 tool_use 都跑一次。"},
                             {"at": "if should_run_background(block.name, block.input):", "text": "慢命令转后台，立刻返回一个 task_id；真正结果走通知。"},
                             {"at": "handler = handlers.get(block.name)", "text": "从工具池里查 handler。查不到也不会崩，call_tool_handler 会返回错误字符串。"},
                             {"at": "trigger_hooks(\"PostToolUse\", block, output)", "text": "执行后再给扩展点一次机会（大输出告警就是在这一步）。"},
                             {"at": "if block.name == \"todo_write\":", "text": "更新计数：调用了就清零，没调用就加一。"},
                             {"at": "messages.append({\"role\": \"user\", \"content\": build_user_content(results)})", "text": "结果回填，进入下一圈。整个 Harness 的「一轮」在这里闭合。"},
                             {"at": "output = call_tool_handler(handler, block.input, block.name)", "text": "handler 抛异常也会被收成字符串，循环不中断。"},
                             {"at": "bg_id = start_background_task(block, handlers)", "text": "启动后台任务，立刻拿到 id。"},
                         ],
            },
        ],
        "points": [
            ("一个循环 + 两个注册表", "工具池（能做什么）和 hook 表（什么时候插一脚），其余都是装配。"),
            ("工具池每轮重建", "MCP 中途连上也能立刻用；代价是每轮有点开销。"),
            ("权限是 hook，不是 if", "想换策略就换注册的那一行。"),
            ("循环头尾有顺序", "定时 → 后台通知 → todo 提醒 → 压缩 → 调模型；顺序影响行为。"),
            ("生产化的事源码没做", "「配置开关」「初始化幂等」「错误定位」在本文件里没有实现，属于你自己要补的工程工作。"),
        ],
        "pitfalls": [
            "从头读 3000 行，读到一半就迷路——先看这三个注册点：assemble_tool_pool、HOOKS、agent_loop。",
            "以为它已经能多租户/多会话隔离：它仍是一个进程、一份全局状态。",
            "拿它直接上生产：没有配置校验、没有优雅停机、没有指标，这些都得自己加。",
        ],
        "try": "在 s15 里只搜三处：`assemble_tool_pool`、`trigger_hooks`、`prepare_context`。验收：能说出「一轮循环里工具池被装配几次、PreToolUse/PostToolUse 各在哪触发、压缩在哪一步执行」，并在文中找到对应行号。",
    },
    {
        "id": "s16", "no": "16", "advanced": True,
        "title": "单步交给模型，编排交给脚本", "sub": "Workflow Runtime",
        "quote": "demo 离线跑；只有交互 CLI 才装真实 runner",
        "problem": "多步流程里，如果每一步都由模型决定下一步，既慢又贵，而且同一份输入跑两次结果可能不同。"
                   "这一章的 demo 默认用 MockAgentRunner，不联网、不花钱；真实模型只在交互模式里接上。",
        "idea": [
            "编排写成脚本：谁先谁后、串行还是并行、失败怎么重试；",
            "每一步仍是一次模型调用，但只负责「这一步」；",
            "带 schema 的输出会校验，失败重试一次；",
            "每一步追加写 journal；resume 时只有 key 完全相同才复用缓存。",
        ],
        "rel": "s16_workflow_runtime/code.py",
        "blocks": [
            {
                "from": "class AnthropicAgentRunner:",
                "to": "return RunnerOutput(value, tokens)",
                "notes": [
                             {"at": "class AnthropicAgentRunner:", "text": "真实 runner：用 host 的 client 和模型名，一次只做一步。"},
                             {"at": "request += (", "text": "把 schema 和要求拼进 prompt；模型看到的是文字，没有工具。"},
                             {"at": "if schema is not None:", "text": "要结构化输出就把 schema 写进 prompt，再解析；失败重试一次，也会再计费一次。"},
                             {"at": "response = self.client.messages.create(", "text": "唯一真正调用模型的地方；demo 模式不会走到这里。"},
                             {"at": "max_tokens=2000,", "text": "单步输出上限 2000 token，防止一步写太长。"},
                             {"at": "return RunnerOutput(value, tokens)", "text": "统一返回「值 + token 数」；token 统计是记账，不是计费开关。"},
                             {"at": "text = _response_text(response)", "text": "把响应里的文字块拼成文本，后面按有没有 schema 决定怎么解析。"},
                             {"at": "usage = getattr(response, \"usage\", None)", "text": "token 只用于预算和展示；请求在上一步已经发出，可能已计费。"},
                             {"at": "value = _parse_runner_json(text)", "text": "解析失败只影响返回值，不会撤销已经产生的请求费用。"},
                         ],
            },
            {
                "from": "def install_workflow_tool(host):",
                "to": "host._workflow_tool_installed = True",
                "notes": [
                             {"at": "def install_workflow_tool(host):", "text": "交互模式才调用：把 Workflow 挂到 s15 host，同时换上真实 runner。"},
                             {"at": "RUNNER_FACTORY = lambda:", "text": "真实 runner 要 client、model 两个参数；直接写类名会 TypeError。"},
                             {"at": "if getattr(host, \"_workflow_tool_installed\"", "text": "已经装过就返回；重复包装会让工具池出现两份。"},
                             {"at": "def assemble_with_workflow():", "text": "包装 host 原有的工具池，只追加 Workflow，不改它的分发循环。"},
                             {"at": "tools.append(WORKFLOW_TOOL)", "text": "Workflow 作为普通工具进池，模型像调其他工具一样调它。"},
                             {"at": "host._workflow_tool_installed = True", "text": "这个标记防止重复安装。"},
                         ],
            },
            {
                "from": "if __name__ == \"__main__\":",
                "to": "        run_cli()",
                "notes": [
                             {"at": "if __name__ == \"__main__\":", "text": "两条入口：demo/resume 走离线，否则进交互 CLI。"},
                             {"at": "if sys.argv[1:] and sys.argv[1] in {\"demo\", \"resume\"}:", "text": "只认 demo 和 resume；拼错参数会掉进交互模式。"},
                             {"at": "asyncio.run(run_demo(sys.argv[1:]))", "text": "demo 和 resume 都用 MockAgentRunner：不联网、不花钱。"},
                             {"at": "run_cli()", "text": "无参数才装真实 runner；之后每次请求都可能产生费用。"},
                         ],
            },
        ],
        "points": [
            ("三种入口", "`demo` 离线演示、`resume` 离线续跑、无参数进入交互 CLI。"),
            ("demo/resume 不花钱", "默认 RUNNER_FACTORY = MockAgentRunner，返回确定性结果。"),
            ("真实 runner 由 host 安装", "install_workflow_tool(host) 里改成 AnthropicAgentRunner(host.client, host.MODEL)。"),
            ("不能无参替换", "AnthropicAgentRunner 的构造函数需要 client 和 model；直接替换类名会 TypeError。"),
            ("journal 支持续跑", "resume 只读同一次 run 的 journal；新 demo 是新 run；key = kind + label + prompt + schema，四项全同才复用。"),
            ("费用看请求，不看返回", "`client.messages.create` 发出就可能计费；解析失败、重试或抛异常都不会退。"),
        ],
        "pitfalls": [
            "以为 `demo` 在调真模型——它用的是 MockAgentRunner。",
            "把 RUNNER_FACTORY 直接赋成 AnthropicAgentRunner：缺少 client/model，直接报错。",
            "以为只有成功返回才计费：请求一发出就可能计费，解析失败也一样。",
            "以为改了 prompt 还能命中缓存：key 含 kind/label/prompt/schema，改了就会重跑。",
            "以为后台任务会主动叫醒模型：只有主循环每轮开头 collect 才注入通知。",
        ],
        "try": "离线练习：先跑 `python s16_workflow_runtime/code.py demo`，记下输出的 agents 数和 journal 条目数；再跑 `python s16_workflow_runtime/code.py resume`。验收：第二次的 agents 数小于第一次，且 journal 里能看到被复用的记录——全程不产生模型费用。想看真实调用，只能用无参数进入 CLI（会安装 AnthropicAgentRunner，每次请求都可能计费），不要靠改类名。",
    },
    {
        "id": "s17", "no": "17", "advanced": True,
        "title": "模型说完了不算完", "sub": "Goal Loop",
        "quote": "另起一次无工具的模型调用做裁决",
        "problem": "s01 的退出条件是「模型不再要工具」。但模型经常在事情没做完时就说「已完成」。"
                   "让它自己判断，等于让学生自己批卷子。",
        "idea": [
            "目标是一段可判定的条件，比如「测试全绿」「文件存在」；",
            "每轮结束，交给一个独立的、不带工具的模型调用裁决；",
            "没达成就再跑一轮，并告诉模型「还差什么」；",
            "连续被挡超过阈值就返回 limit，避免无限循环。",
        ],
        "rel": "s17_goal_loop/code.py",
        "blocks": [{
            "from": "def set_goal(self, condition: str, tokens_at_start: int = 0) -> GoalState:",
            "to": "def status(self, current_tokens: int = 0) -> str:",
            "notes": [
                         {"at": "def set_goal(self, condition: str, tokens_at_start: int = 0) -> GoalState:", "text": "目标是一段自然语言条件，但要能被证据判定——「代码优雅」不行，「pytest 全绿」可以。"},
                         {"at": "if self.active is not None:", "text": "设新目标前，先给旧目标记一笔「被替换」。审计链不断。"},
                         {"at": "self._record(active=True, met=False, failed=False, reason=\"goal set\")", "text": "每次状态变化都落一条记录。事后能复盘「它为什么觉得没完成、依据是什么」。"},
                         {"at": "def status(self, current_tokens: int = 0) -> str:", "text": "status 是给模型看的：目标是什么、跑了几轮、花了多少 token、还差什么。"},
                         {"at": "self.active = GoalState(", "text": "用新 goal 替换旧状态，轮数和起点 token 都重置。"},
                         {"at": "def clear(self, reason", "text": "清空时也记一条历史，保留「为什么清」。"},
                         {"at": "self.active = None", "text": "内存清空，但 last_status 仍留给 status() 用。"},
                     ],
        }],
        "points": [
            ("判断器独立于执行者", "另起一次调用，不带工具，只读 transcript 做判断。"),
            ("但它仍是模型", "判断可能出错：被漂亮的说法骗过，或者对证据理解偏差。不能等同于确定性的测试验收。"),
            ("条件要可判定", "用命令退出码、文件是否存在、测试是否通过，而不是形容词。"),
            ("有止损但无 token 硬上限", "连续 block 超过 block_cap 会返回 limit；代码里没有「花到多少钱就停」的硬约束。"),
            ("裁决要留痕", "每次判定都记录，才能调试「它为什么一直说没完成」。"),
        ],
        "pitfalls": [
            "把独立判断器当成「客观真理」——它只是换了一次模型调用，仍会误判。",
            "目标本身不可判定（「体验要好」），判断器只能瞎猜。",
            "完全依赖它决定收工，却没有外部测试或人工验收兜底。",
        ],
        "try": "设一个「pytest 必须全绿」的目标，故意留一个失败测试。验收：判断器连续返回 block，模型回去改代码；等测试真的全绿后，下一次判断返回 achieved。再把目标改成「代码写得优雅」，观察它给出的理由有多主观。",
    },
]

OUTRO = r"""
<h2 style="font-size:26px;margin:0 0 6px">学完之后</h2>
<p style="color:var(--mid);margin:0 0 18px">17 章看下来，其实就三句话——但这三句都要加限定条件。</p>

<div class="intro-card">
  <h3>1. 循环是地基，能力长在它外面</h3>
  <p>工具是注册表、权限是钩子、上下文是包装、子 Agent 是再开一个循环。
  这套课程里，加能力基本不用改 while 循环——但如果你要的是多租户、并发隔离、可观测性，那些工作不在循环里，也不在这 17 个文件里。</p>
</div>

<div class="intro-card">
  <h3>2. 模型负责决策，代码负责边界</h3>
  <p>让它决定调什么工具、写什么代码；但「能不能删这个目录」「上下文满了怎么办」「什么算完成」，
  这些边界得由代码兜住。prompt 是建议，代码才是约束。</p>
</div>

<div class="intro-card">
  <h3>3. 上下文是唯一的稀缺资源</h3>
  <p>s06 子 Agent、s07 技能加载、s08 压缩、s09 记忆，四个章节都在干同一件事：
  <strong>让模型在有限窗口里看到最该看的东西</strong>。这也是这份代码里最值得反复读的部分。</p>
</div>

<div class="intro-card warn-card">
  <h3>这份代码不是什么</h3>
  <p>它不是安全沙箱（s03 只是字符串黑名单），不是生产级多租户系统（s15 只有一个进程、一份全局状态），
  不是真实的 MCP 实现（s14 是内存 mock），也不是可靠的自动验收（s17 的判断器仍然是模型）。
  把它当教材读，别当框架用。</p>
</div>

<h3 style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--mid);margin:34px 0 8px;font-weight:700">接下来可以做什么</h3>
<ul style="margin:0;padding-left:22px">
<li>把 s01 那份 40 行代码改成你熟悉的语言（TypeScript / Go），你会真正理解每个细节。</li>
<li>给 s02 加一个你工作里最常用的工具，体会「加工具不改循环」。</li>
<li>把 s03 的黑名单换成真正的命令解析，看看能防住多少绕过手法。</li>
<li>把 s08 的阈值调小，观察一次真实的长任务里四步压缩各触发了几次。</li>
</ul>

<p style="margin-top:26px;color:var(--mid);font-size:14px">
配套仓库：<a href="https://github.com/shareAI-lab/learn-claude-code" target="_blank" rel="noreferrer">shareAI-lab/learn-claude-code</a>（MIT），
本教程对应 commit <code>7226f55</code>。每章目录里都有独立的 README 和可运行代码，建议对照原仓库一起读。
</p>
"""
