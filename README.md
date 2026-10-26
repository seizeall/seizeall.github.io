# Rongtao Chen — 个人学术主页

纯静态学术主页（HTML + CSS + 原生 JS），外加一个**跑在自己电脑上的图形化编辑器**：
打开一个本地网页就能改文字、加论文、传 PDF，点一下就 commit + push 上线，改错了能一键回退。

线上地址：<https://seizeall.github.io/>

---

## 1. 日常怎么用（推荐）

双击 **`start-editor.cmd`**，或者：

```powershell
cd E:\myself
python tools\admin.py
```

浏览器会自动打开 `http://127.0.0.1:8099/admin`。左边选栏目，右边改内容：

| 按钮 | 作用 |
| --- | --- |
| **保存并生成** | 写入 `content.json` 并重新生成 `index.html`（本地生效） |
| **发布到 GitHub** | 先保存，再 `git commit` + `git push`，约 30 秒后线上更新 |
| **预览** | 新标签页打开本地站点 |
| **历史** | 看最近 20 次提交，任意一条可以「回退」（生成一个反向提交再推送） |

细节：

- 论文卡片右上角有 **上传 PDF**，文件存到 `assets/files/papers/`，并自动在链接里加一条 `PDF`。
- 「站点信息」页底部可以 **更换头像**，覆盖 `assets/img/portrait.jpg`（页面会带版本号，不会被浏览器缓存坑）。
- 文案里可以用 `**加粗**`、`*斜体*`、`[文字](https://链接)`。
- 作者一栏把自己的名字用 `**` 包起来（`R. **Chen**, C. Xie`），页面上就会高亮。
- 关闭窗口前有未保存修改会提示；`Ctrl + S` 也能保存。

## 2. 编辑器为什么是安全的

- 服务只监听 `127.0.0.1`，外网访问不到。
- 每次启动生成一个随机 token，注入到页面里；所有 `/api/*` 请求都要带这个 token，别的网站/标签页调不动。
- 上传只允许写进 `assets/`，扩展名白名单，单文件 ≤ 60 MB。
- 回退是 `git revert`（生成反向提交），不会丢历史；工作区有未提交改动时会拒绝回退。

## 3. 文件结构

```
.
├── index.html                  ← 生成物（别手改，会被下次生成覆盖）
├── content.json                ← 全部内容都在这里（唯一数据源）
├── templates/index.template.html  ← 页面骨架，改版式时才动
├── tools/
│   ├── build.py                ← content.json → index.html（无第三方依赖）
│   ├── admin.py                ← 本地编辑器服务器（保存/上传/发布/回退）
│   └── admin.html              ← 编辑器界面
├── assets/
│   ├── css/style.css
│   ├── js/main.js
│   ├── img/portrait.jpg | favicon.svg
│   └── files/papers/           ← 上传的 PDF 落在这里
├── start-editor.cmd            ← 双击启动编辑器
├── robots.txt / sitemap.xml
└── .nojekyll
```

## 4. 不用编辑器，直接改文件

```powershell
cd E:\myself
# 改 content.json
python tools\build.py          # 重新生成 index.html
python tools\build.py --check  # 只校验，不写文件
git add -A; git commit -m "update"; git push
```

改版式/配色才需要动 `templates/index.template.html` 和 `assets/css/style.css`。

## 5. 上线（GitHub Pages）

仓库是 `seizeall.github.io`，发布方式已经配好：**Deploy from a branch → main → / (root)**。
`git push` 之后几十秒自动更新，不需要再碰设置。

首次配置回忆：

1. Settings → Pages → Source 选 **Deploy from a branch**
2. Branch 选 `main`，目录 `/ (root)`，Save

> 想用自定义域名（比如 `chenrongtao.com`）：Settings → Pages 填 Custom domain，再加一条 CNAME 记录。

## 6. 还要改的地方

- 邮箱 `rongtao.chen@seu.edu.cn` 仍是占位地址，**上线前换成真的**（编辑器「站点信息」里改一处，全站生效）。
- 新闻的日期只精确到年份，有具体月份可以自己补。
- Google Scholar 上的单位写的是 *South China Normal University*，本页按 **东南大学 网络安全学院** 写；如果本科在华南师大，可以在「关于」里加一段教育经历。
- 头像现在是 Scholar 上的卡通头像，想换真人照就在编辑器里上传。

## 7. 页面本身

- 深浅色跟随系统、可手动切换并记住
- 导航滚动高亮、移动端折叠菜单
- 论文按期刊 / 会议筛选（数量自动算）
- 邮箱一键复制、滚动淡入、`prefers-reduced-motion` 下自动关闭动效
- 响应式 + 打印样式 + 无障碍焦点环 + `skip-link`
- SEO：`Person` 结构化数据、Open Graph、`robots.txt`、`sitemap.xml`

内容数据来源：Google Scholar 公开主页、GitHub 公开 API（2026-10-27 抓取）。
