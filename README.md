# VideoDown — 万能视频下载总结器

> 免费在线视频下载器 + AI 视频分析工具

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的在线视频下载器 + AI 视频分析工具。支持 **YouTube、Bilibili、抖音** 等 1,800+ 网站的视频下载，以及 **AI 总结、思维导图、AI 问答、字幕提取** 等智能分析功能。

前端采用 Apple 风格设计，默认中文界面，支持中英文切换。已完成 **SEO 搜索引擎优化** 和 **GEO 生成式引擎优化**。

## 特性

### 视频下载
- 🎬 **多平台下载** — YouTube、Bilibili、抖音（Douyin）等 1,800+ 网站
- 🎨 **格式选择** — 1080p / 720p / 480p / Audio 可选
- 🎯 **抖音免登录** — Playwright 自动获取 cookie，无需用户操作
- 📊 **实时进度** — SSE 流式推送下载进度
- 🖼️ **封面预览** — 缩略图代理，突破防盗链
- 📁 **下载管理** — 已下载文件列表，支持二次下载

### AI 智能分析
- 🤖 **AI 视频总结** — 基于 DeepSeek 大模型的视频总结，打字机逐字渲染
- 🧠 **思维导图** — AI 自动生成结构化思维导图，基于 markmap (D3.js) 渲染，支持 SVG/PNG 导出
- 💬 **AI 问答** — 针对视频内容提问，流式对话回复
- 📝 **字幕提取** — 自动提取字幕/转录文本（YouTube 自动字幕、B 站 CC 字幕）
- 📄 **字幕查看器** — 时间戳排序、搜索过滤、正序/倒序切换、SRT/TXT 下载

### 设计 & 优化
- 🍎 **Apple 风格 UI** — 52-72px 大标题、卡片式布局、毛玻璃导航、滚动渐入动画
- 🇨🇳 **中文优先** — 默认中文界面，一键切换 English
- 🔍 **SEO 优化** — TDK 标签、Open Graph、Twitter Card、Schema.org 结构化数据
- 🤖 **GEO 优化** — JSON-LD (WebApplication/FAQPage/HowTo)、AI 爬虫白名单、`<noscript>` 兜底
- 📱 **响应式设计** — 完美适配手机、平板、桌面端

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python FastAPI + yt-dlp + Playwright + DeepSeek API |
| 前端 | Vue 3 + Vite + markmap (D3.js 思维导图) + marked (Markdown 渲染) |
| 通信 | REST API + SSE 进度推送 + EventSource 流式 |
| AI | DeepSeek V4 Pro（OpenAI 兼容 SDK） |
| 设计 | Apple 风格 Design Token + CSS 自定义属性 |
| SEO | robots.txt + sitemap.xml + JSON-LD + Open Graph + Twitter Card |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Chrome 浏览器（用于抖音下载、B 站字幕提取）
- FFmpeg（用于视频合并）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/LebrontoLee/free-video-downloader.git
cd free-video-downloader

# 2. 安装后端依赖
pip install -r backend/requirements.txt
pip install playwright httpx
python -m playwright install chromium  # 可选，优先使用系统 Chrome

# 3. 安装前端依赖
cd frontend
npm install
cd ..

# 4. 安装 FFmpeg（Windows）
winget install ffmpeg
# 或 macOS: brew install ffmpeg
# 或 Linux: sudo apt install ffmpeg
```

### 配置

```bash
cd backend
cp .env.example .env
```

编辑 `.env`：

```env
# DeepSeek API Key（必填，用于 AI 分析）
DEEPSEEK_API_KEY=sk-your-key-here

# Bilibili Cookie（可选，用于 B 站 CC 字幕提取）
# 1. 浏览器登录 bilibili.com
# 2. F12 → Application → Cookies → bilibili.com
# 3. 复制 SESSDATA 的值
BILIBILI_SESSDATA=your-sessdata-here
```

### 运行

```bash
# 终端 1：启动后端（端口 8000）
cd backend
python server.py

# 终端 2：启动前端（端口 5173）
cd frontend
npm run dev
```

访问 **http://localhost:5173**

## 项目结构

```
free-video-downloader/
├── backend/
│   ├── server.py              # FastAPI 后端（API + yt-dlp + AI 端点）
│   ├── douyin_helper.py       # 抖音专用下载器（Playwright + RENDER_DATA）
│   ├── subtitle_helper.py     # 字幕提取（yt-dlp + VTT/SRT 解析）
│   ├── ai_helper.py           # DeepSeek 客户端 + Prompt 模板
│   ├── ai_tasks.py            # 内存缓存 + 会话管理
│   ├── bilibili_auth.py       # B 站 Cookie 管理
│   ├── .env.example           # 环境变量模板
│   └── requirements.txt       # Python 依赖
├── frontend/
│   ├── index.html             # SEO 完整标签 + JSON-LD + noscript 兜底
│   ├── vite.config.js
│   ├── public/
│   │   ├── robots.txt         # 爬虫规则（含 AI 爬虫白名单）
│   │   ├── sitemap.xml        # XML 站点地图
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── App.vue            # 根组件（状态 + 语言 + 滚动动画）
│       ├── main.js
│       ├── i18n.js            # 中英文文案（含 SEO 营销内容）
│       ├── sse.js             # SSE 流读取工具
│       ├── scrollEffects.js   # 滚动动画引擎（parallax/scrollFade/stickyPin）
│       ├── style.css          # Apple 设计系统 + 动画 + 滚动效果
│       └── components/
│           ├── NavBar.vue          # 毛玻璃导航栏
│           ├── HeroSection.vue     # Hero + URL 输入（72px 大标题 + 辉光背景）
│           ├── VideoPreview.vue    # 视频信息 + 格式选择
│           ├── DownloadProgress.vue# 实时进度条
│           ├── FileList.vue        # 已下载列表
│           ├── ProBanner.vue       # PRO 解锁（免费版 vs PRO 左右对比卡片）
│           ├── AiPanel.vue         # AI 功能标签页容器
│           ├── SummaryCard.vue     # AI 总结（DOM 逐字打字机 + marked 渲染 Markdown）
│           ├── SubtitleViewer.vue  # 字幕文本查看器
│           ├── MindMap.vue         # 思维导图（markmap，SVG/PNG 导出）
│           ├── QAChat.vue          # AI 问答（流式打字机动画）
│           ├── FeatureSection.vue  # 功能介绍（6 卡片网格）
│           ├── HowToSection.vue    # 使用教程（3 步骤卡片）
│           ├── FAQSection.vue      # 常见问题（原生 <details> 折叠）
│           ├── PlatformSection.vue # 支持平台（标签云）
│           └── AppFooter.vue       # 页脚（4 栏布局）
└── downloads/                 # 下载存储目录
```

## SEO & GEO 优化

### 已完成的优化项

| 类别 | 内容 |
|------|------|
| **TDK** | 每个页面独立 Title（50-60 字符）、Description（150-160 字符）、Keywords |
| **Open Graph** | og:title / og:description / og:image / og:type / og:url / og:locale / og:site_name |
| **Twitter Card** | twitter:card=summary_large_image / twitter:title / twitter:description |
| **Schema.org** | WebApplication / FAQPage（7 条问答）/ HowTo（3 步骤）JSON-LD 结构化数据 |
| **noscript 兜底** | 完整 HTML 内容（功能列表、对比表、FAQ），确保无 JS 爬虫能抓取 |
| **robots.txt** | 允许所有爬虫 + GPTBot / ChatGPT-User / ClaudeBot / PerplexityBot 显式白名单 |
| **sitemap.xml** | 标准 XML Sitemap，提交至 Google Search Console / 百度站长平台 |
| **结构化内容** | H1-H3 层级标题、FAQ 格式、对比表格、列表格式，符合 GEO 最佳实践 |
| **时效性标注** | 页面标注"更新于 2026 年 X 月"，满足 AI 引擎对新鲜内容的偏好 |
| **响应式设计** | 一套代码适配所有设备，URL 统一，利于 SEO |
| **性能** | Vite 构建、CSS 自定义属性、will-change 优化 |

### 上线后操作

1. 将 `robots.txt`、`sitemap.xml`、`index.html` 中的 `videownd.example.com` 替换为实际域名
2. 提交 sitemap 至 [Google Search Console](https://search.google.com/search-console) 和[百度站长平台](https://ziyuan.baidu.com/)
3. 验证结构化数据：[Google Rich Results Test](https://search.google.com/test/rich-results)
4. 验证 OG 标签：[Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
5. 替换 `og-image.png` 为实际社交分享图（建议 1200×630px）

## API 端点

### 下载相关

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/extract` | 提取视频元信息（标题、封面、格式列表） |
| POST | `/api/download` | 启动下载任务，返回 task_id |
| GET | `/api/download/{id}/progress` | SSE 实时进度流 |
| GET | `/api/files` | 已下载文件列表 |
| GET | `/api/downloads/{filename}` | 下载已完成文件 |
| GET | `/api/thumbnail?url=...` | 封面图代理（突破防盗链） |

### AI 分析

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/ai/subtitles` | 提取字幕/转录文本 |
| GET | `/api/ai/summary` | AI 总结（SSE 流式，打字机效果） |
| POST | `/api/ai/mindmap` | 生成思维导图 JSON |
| GET | `/api/ai/chat/stream` | AI 问答（SSE 流式） |
| GET | `/api/ai/health` | DeepSeek 配置检查 |

## 平台兼容性

| 平台 | 提取 | 下载 | 字幕 | AI 分析 |
|------|------|------|------|------|
| YouTube | ✅ | ✅ | ✅ 自动字幕 | ✅ |
| Bilibili | ✅ | ✅ | ⚠️ 需 SESSDATA | ✅ |
| 抖音 (Douyin) | ✅ | ✅ | ❌ | ⚠️ 元数据 |
| Twitter/X | ✅ | ✅ | ✅ | ✅ |
| 其他 1,800+ 网站 | ✅ | ✅ | ✅ | ✅ |

## 抖音下载原理

抖音的 `_$jsvmprt` JS 反爬会拦截所有非浏览器请求。本项目通过 Playwright 调用系统 Chrome 执行页面 JS，从渲染后的 `RENDER_DATA` JSON 中提取无水印视频直链，完全绕开 yt-dlp 的兼容问题，用户无需提供 cookie 或登录。

```
用户 URL → Playwright(系统Chrome) → 执行 JS 挑战
         → 提取 RENDER_DATA.app.videoDetail
         → 无水印直链 → httpx 下载
```

## AI 分析原理

```
用户输入 URL → 提取视频信息
  ├─ 字幕提取: yt-dlp writeautomaticsub / B站 CC API
  ├─ 字幕查看: 时间戳排序、搜索过滤、正序/倒序、SRT/TXT 下载
  ├─ AI 总结: 字幕 → DeepSeek SSE 流式 → DOM 逐字打字机渲染 → marked 渲染 Markdown
  ├─ 思维导图: 字幕 → DeepSeek JSON 模式 → markmap (D3.js) 交互式渲染 → SVG/PNG 导出
  └─ AI 问答: 字幕 + 用户问题 → DeepSeek 流式回复
```

## License

MIT
