# Learn Claude Code · 大白话逐行教程

**在线阅读：https://liancheng2020.github.io/learn-claude-code-zh/**

把 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的 17 章拆成中文大白话：
逐行讲关键代码，讲清每一层为什么存在，并明确区分 **本版实现 / 教学简化 / 生产建议**。

> 非官方社区教程。代码逐字取自上游 commit `7226f555d48900076eba126acf37c9ed5f002b5d`（2026-10-27），
> 每个代码块标注 `L起–L止`，可对照上游原文。

## 讲什么

| 章节 | 代码 | 讲解 |
|---|---|---|
| s01–s02 | 完整源码 | 逐行 |
| s03–s08 | 核心节选 | 逐行 |
| s09–s17 | 关键片段 | 逐行 + 机制说明 |

## 本地构建

```bash
git clone https://github.com/shareAI-lab/learn-claude-code ../learn-claude-code
git -C ../learn-claude-code checkout 7226f555d48900076eba126acf37c9ed5f002b5d

python3 build.py --src ../learn-claude-code --out site
python3 -m http.server -d site 8000     # 预览 http://localhost:8000
```

只依赖 Python 标准库。

## 目录

```
build.py       生成站点（读上游源码 + content/）
content/       17 章文案与注解锚点（改这里）
assets/        样式与交互
site/          构建产物，提交后自动部署
.github/       Pages 部署 + 产物一致性校验
```

## 更新与发布

改 `content/*.py` → `python3 build.py` → 提交 `site/` → push 到 `main`，Pages 自动更新。

提交信息统一中文，格式 `type:描述`，如 `feat:新增 s05 注解`、`fix:修正 s10 依赖说明`。

## 许可

- 代码片段：上游 MIT，版权归 shareAI Lab，全文见 [NOTICE](NOTICE)
- 讲解文字：CC BY 4.0，见 [LICENSE](LICENSE)
