# Learn Claude Code · 大白话逐行教程

把 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的 17 章拆成中文大白话教程：
逐行讲解关键代码，讲清「这一层为什么存在」，并明确区分**本版实现**、**教学简化**和**生产建议**。

站点按章节拆页，可直接部署到 GitHub Pages。

## 覆盖范围（诚实声明）

| 章节 | 代码呈现 | 讲解 |
|---|---|---|
| s01–s02 | 完整源码（全文） | 逐行 |
| s03–s08 | 核心节选（每章 1–3 段） | 节选内逐行 |
| s09–s17 | 关键片段（每章 1–4 段） | 片段内逐行，其余分段说明 |

代码逐字取自上游 **commit `7226f555d48900076eba126acf37c9ed5f002b5d`（2026-10-27）**，
每个代码块标注 `L起–L止`，可对照上游原文。

## 目录结构

```
.
├─ build.py              # 生成站点（读上游源码 + content/）
├─ content/              # 章节文案与注解锚点（唯一需要手改的地方）
│  ├─ content_a.py       # 导读 + s01–s02
│  ├─ content_b.py       # s03–s08
│  └─ content_c.py       # s09–s17 + 结语
├─ assets/
│  ├─ style.css
│  └─ app.js
├─ site/                 # 构建产物（提交进仓库，供 Pages 直接发布）
└─ .github/workflows/    # Pages 部署 + 源码一致性校验
```

## 本地构建

```bash
git clone https://github.com/shareAI-lab/learn-claude-code ../learn-claude-code
git -C ../learn-claude-code checkout 7226f555d48900076eba126acf37c9ed5f002b5d

python3 build.py --src ../learn-claude-code --out site
open site/index.html            # 或 python3 -m http.server -d site 8000
```

只依赖 Python 标准库。

## 部署到 GitHub Pages

仓库已带 `.github/workflows/pages.yml`：

1. 推到 `main`；
2. Settings → Pages → Source 选 **GitHub Actions**；
3. 首次运行后站点地址是 `https://<user>.github.io/<repo>/`。

`site/` 里全是相对路径（`./assets/...`、`./s05.html`），放在子路径下也能正常工作。
`.nojekyll` 已生成，避免 Jekyll 处理静态资源。

## 修改内容

- 文案、注解、练习：改 `content/*.py` 里对应章节的字符串；
- 注解用「锚点」定位，不写死行号：`{"at": "def agent_loop(...)", "text": "..."}`，
  构建时会找到该行并把讲解插在它后面；锚点不唯一会直接报错，避免注释错位；
- 样式：`assets/style.css`；交互：`assets/app.js`；
- 改完重新构建，把 `site/` 一起提交。

## 提交约定

- **提交信息统一用中文**，格式 `type:描述`，例如：
  `feat:新增 s05 注解`、`fix:修正 s10 依赖说明`、`docs:补充部署说明`、`style:统一主题色`。
- `site/` 是构建产物：改内容请改 `content/`，重新生成后与页面一起提交。

## 校验

```bash
# 手动触发：重新构建并与已提交的 site/ 比对，发现产物过期
gh workflow run verify.yml
```

工作流会 clone 固定 commit 重新构建，`diff -r` 不一致即失败。

## 许可

- **代码片段**：来自上游，MIT，版权归 shareAI Lab，全文见 [NOTICE](NOTICE)。
- **讲解文字**：CC BY 4.0，转载保留出处链接即可，见 [LICENSE](LICENSE)。

本项目是社区非官方教程，不是上游官方文档；以上游每章 README 为准。
