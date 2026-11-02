# Learn Claude Code · 大白话教程

**在线阅读：https://liancheng2020.github.io/learn-claude-code-notes-zh/**

用大白话读懂 Agent 的循环、工具、上下文与协作机制。

基于 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的非官方中文教程：
用大白话讲解关键源码、运行机制与动手练习，并区分 **本版实现 / 教学简化 / 生产建议**。

> 非官方社区教程。代码逐字取自上游 commit `7226f555d48900076eba126acf37c9ed5f002b5d`（2026-10-27）。
> 构建时会校验 git HEAD 与工作区，不匹配直接失败。

## 讲解范围（据实标注）

| 章节 | 代码 | 注解方式 |
|---|---|---|
| s01–s02 | 完整源码 | 关键行注解（每章十几到三十几处） |
| s03–s08 | 核心节选 | 节选内关键行注解，其余自行阅读 |
| s09–s17 | 关键片段 | 片段内关键行注解 + 分段说明 |

**不是每行都有讲解。** 每章标题会显示实际统计，例如「核心节选 · 8 处注解」；
注解数量直接标在章节标题旁。每段代码标注 `L起–L止`，可对照固定 commit 原文。

## 本地构建

```bash
git clone https://github.com/shareAI-lab/learn-claude-code ../learn-claude-code
git -C ../learn-claude-code checkout 7226f555d48900076eba126acf37c9ed5f002b5d

python3 build.py --src ../learn-claude-code --out site
python3 -m http.server -d site 8000     # http://localhost:8000
```

只依赖 Python 标准库。`--out` 会先解析路径（含 `..`、符号链接），拒绝项目/上游的根与祖先、
`$HOME` 和 `/`，只覆盖带 `.lcc-build` 标记的旧产物；构建先在临时目录完成，失败时保留旧站点。

## 测试

```bash
python3 -m unittest discover -s tests -v      # 路径安全、版本校验、原子替换
python3 tests/check_site.py site --src ../learn-claude-code   # 链接、章节、代码与源码一致
python3 tests/ui_smoke.py --site site        # 复制失败/成功、目录焦点、320px 许可页（需 Chrome，缺失则跳过）
```

## 目录

```
build.py       生成站点（读上游源码 + content/）
content/       17 章文案与注解锚点（改这里）
assets/        样式与交互
site/          构建产物，提交后自动部署
tests/         构建安全检查与产物检查
.github/       Pages 部署 + 校验（部署依赖校验通过）
```

## 更新与发布

改 `content/*.py` → `python3 build.py` → 提交 `site/` → push 到 `main`，Pages 自动更新。

提交信息统一中文，格式 `type:描述`，如 `feat:新增 s05 注解`、`fix:修正 s10 依赖说明`。

## 许可

- 代码片段：上游 MIT，版权归 shareAI Lab，全文见 [NOTICE](NOTICE)
- 讲解文字：CC BY 4.0，见 [LICENSE](LICENSE)
