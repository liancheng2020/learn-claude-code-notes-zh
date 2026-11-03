# Learn Claude Code · 大白话教程

用大白话读懂 Agent 的循环、工具、上下文与协作机制。

**在线阅读：<https://liancheng2020.github.io/learn-claude-code-notes-zh/>**

![两组代码与紧邻讲解](docs/preview.png)

## 适合谁

- 会一点 Python，想搞懂 Agent 到底怎么跑起来，而不是只调 API。
- 正在读 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)，被几千行代码和术语卡住。
- 想自己写一个最小 Harness，需要能落地的结构和边界。

## 能学到什么

- 一个循环怎么长成 Agent：工具分发、权限、hook、todo。
- 上下文怎么管：子 Agent、压缩、记忆、任务系统。
- 长任务怎么跑：后台任务、定时、多 Agent、MCP、Workflow、目标循环。
- 每章都有「解决什么问题 → 思路 → 代码分段讲解 → 边界与练习」，并区分**本版实现 / 教学简化 / 生产建议**。

## 实际讲解范围

| 章节    | 代码     | 讲解方式                    |
| ------- | -------- | --------------------------- |
| s01–s02 | 完整源码 | 关键行注解                  |
| s03–s08 | 核心节选 | 节选内关键行注解            |
| s09–s17 | 关键片段 | 片段内关键行注解 + 分段说明 |

- 全站 **17 章，配有关键代码注解**。
- **不是逐行注释，也不是全文翻译**：没注解的行，留给你对照原文读。
- 每章标题会标出实际注解量；代码块标 `L起–L止`，可对照固定 commit。

## 这不是什么

- **非官方**社区教程，不代表 Anthropic 或 Claude Code 团队。
- **不是 Claude Code 官方源码、官方文档，也不是命令行使用手册。**
- 不包含 Claude Code 产品源码；讲的是教学仓库 `shareAI-lab/learn-claude-code`。
- 示例是教学实现，不等于生产可用；上生产要自己补配置、隔离、指标和停机。

## 本地阅读

在线版不需要 API Key。想本地看，仓库里已经带了构建好的 `site/`：

```bash
git clone https://github.com/liancheng2020/learn-claude-code-notes-zh.git
cd learn-claude-code-notes-zh
python3 -m http.server -d site 8000     # http://localhost:8000
```

只有修改 `content/`、需要重新构建时，才要准备上游源码（见文末）。

## 纠错 / 反馈

发现讲错、行号对不上、例子跑不通，欢迎提 [Issue](https://github.com/liancheng2020/learn-claude-code-notes-zh/issues)：

- 写清章节、代码块行号、你认为不对的地方；
- 附上你的理解或截图更好；
- 不确定的也欢迎问，不用怕「问题太基础」。

## AI 辅助与许可

- 讲解文字在 AI 辅助下撰写，经人工校对；代码逐字取自上游固定 commit，构建时会校验。
- 代码片段：上游 MIT，版权归 shareAI Lab，见 [NOTICE](NOTICE)。
- 讲解文字：CC BY 4.0，见 [LICENSE](LICENSE)。
- 上游：[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)，固定 commit `7226f555d48900076eba126acf37c9ed5f002b5d`（2026-10-27）。

## 构建与测试

<details>
<summary>克隆、构建、测试（需要 Python 3.10+，只用标准库）</summary>

### 1. 克隆本仓库和上游源码

```bash
git clone https://github.com/liancheng2020/learn-claude-code-notes-zh.git
cd learn-claude-code-notes-zh

git clone https://github.com/shareAI-lab/learn-claude-code.git ../learn-claude-code
git -C ../learn-claude-code checkout 7226f555d48900076eba126acf37c9ed5f002b5d
```

### 2. 构建

```bash
python3 build.py --src ../learn-claude-code --out site
```

构建会校验上游 HEAD 与固定 commit 一致，先写临时目录再原子替换；`--out` 拒绝项目根、上游根、`$HOME` 和 `/`。

### 3. 测试

```bash
python3 -m unittest discover -s tests -v                     # 路径安全、版本校验、原子替换
python3 tests/check_site.py site --src ../learn-claude-code   # 链接、章节、代码与源码一致
python3 tests/lint_notes.py --src ../learn-claude-code       # 注解长段、字数、措辞、术语
python3 tests/ui_smoke.py --site site                        # 复制/目录/主题/320px（需 Chrome，缺失则跳过）
```

### 4. 发布

改 `content/*.py` → 构建 → 提交 `site/` → push 到 `main`，GitHub Pages 自动更新。
提交信息用中文，格式 `type:描述`，如 `feat:新增 s05 注解`、`fix:修正 s10 依赖说明`。

</details>
