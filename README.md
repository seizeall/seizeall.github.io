# Rongtao Chen — 个人学术主页

一个纯静态的学术主页：HTML + CSS + 一点点原生 JS，**没有构建步骤、没有依赖、没有外部字体和追踪脚本**。
双击 `index.html` 就能看，推到 GitHub 就能上线。

线上地址（部署后）：<https://seizeall.github.io/>

---

## 1. 文件结构

```
.
├── index.html                 ← 全部内容都在这里
├── assets/
│   ├── css/style.css          ← 设计系统：配色、排版、卡片、响应式、深色、打印
│   ├── js/main.js             ← 主题切换 / 目录高亮 / 论文筛选 / 复制邮箱 / 滚动动效
│   └── img/
│       ├── portrait.jpg       ← 头像（换掉它即可）
│       └── favicon.svg        ← 标签页图标
├── robots.txt / sitemap.xml    ← 搜索引擎用
└── .nojekyll                   ← 关掉 Jekyll，让静态文件原样发布
```

## 2. 本地预览

```powershell
cd E:\myself
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

直接双击 `index.html` 也能看，但用 http 起服务更接近线上效果。

## 3. 上线（GitHub Pages）

仓库名必须叫 **`seizeall.github.io`**，这样地址才是 `https://seizeall.github.io/`。

1. 在 GitHub 上新建一个**空仓库**（不要勾选 Add a README / .gitignore），名字填 `seizeall.github.io`
2. 本地已经 `git init` 并提交好了，直接接上远端：

```powershell
cd E:\myself
git remote add origin https://github.com/seizeall/seizeall.github.io.git
git push -u origin main
```

然后：

1. 打开 `https://github.com/seizeall/seizeall.github.io/settings/pages`
2. **Build and deployment → Source** 选 **Deploy from a branch**
3. **Branch** 选 `main`，目录选 `/ (root)`，Save
4. 等 1 分钟左右访问 `https://seizeall.github.io/`，手机上也看一眼

之后每次 `git push` 到 `main`，线上会在几十秒内自动更新，不用再碰设置。

> 仓库如果已经存在且非空，先 `git pull --rebase origin main` 再推。
> 想用自定义域名（比如 `chenrongtao.com`）：在 Settings → Pages 里填 Custom domain，再按提示加一条 CNAME 记录。

## 4. 要改的地方

| 位置 | 改什么 |
| --- | --- |
| `index.html` 搜索 `rongtao.chen@seu.edu.cn` | **换成真实邮箱**（共 3 处：hero 按钮、Contact 卡片、`data-email`） |
| `index.html` 搜索 `seizeall.github.io` | 如果仓库名不是 `seizeall.github.io`，OG/结构化数据里的域名要跟着改 |
| `assets/img/portrait.jpg` | 换成正式证件照/半身照，正方形最好，≥512×512 |
| `<section id="news">` | 新闻条目，复制一个 `<li>` 改年份和文字 |
| `<section id="publications">` | 论文条目，复制一个 `<li class="pub">`；`data-type` 填 `journal` 或 `conference`，筛选用得到 |
| `<section id="code">` | GitHub 仓库卡片 |

**加 CV**：把 PDF 放到 `assets/files/cv.pdf`，然后在 hero 的按钮区加一行：

```html
<a class="btn btn-ghost" href="assets/files/cv.pdf" target="_blank" rel="noopener">CV</a>
```

**加论文 BibTeX / PDF 链接**：在对应条目的 `<div class="pub-links">` 里加一个 `<a href="...">PDF</a>`。

## 5. 已内置的功能

- 深色 / 浅色主题，跟随系统，可手动切换并记住选择（`localStorage`）
- 顶部导航当前位置高亮，移动端折叠菜单
- 论文按期刊 / 会议筛选
- 邮箱一键复制（带降级方案，`file://` 下也能用）
- 滚动淡入、数字滚动，`prefers-reduced-motion` 下自动关闭
- 响应式（手机 / 平板 / 桌面）、打印样式、无障碍焦点环、`skip-link`
- SEO：`Person` 结构化数据、Open Graph、`robots.txt`、`sitemap.xml`

## 6. 已知待确认

- 邮箱是占位地址，**上线前必须换掉**。
- 新闻区的日期只精确到年份（从论文的发表年份推的），有具体月份就自己补上。
- Google Scholar 上的单位写的是 *South China Normal University*，本页按你给的 **东南大学 网络安全学院** 写。
  如果本科/硕士前段在华南师大，可以在 About 里补一句教育经历；否则不用动。
- 头像暂时用的 Google Scholar 头像（卡通），建议换成真人照片更可信；`assets/img/portrait.jpg` 覆盖即可，正方形最好。

---

内容数据来源：Google Scholar 公开主页（论文、引用数、h-index）、GitHub 公开 API（仓库、star 数），均为 2026-10-27 抓取。
