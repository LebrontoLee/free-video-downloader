# Free Video Downloader

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的在线视频下载器 + AI 视频分析工具。支持 **YouTube、Bilibili、抖音** 等 1700+ 网站的视频下载，以及 **AI 总结、思维导图、AI 问答** 等智能分析功能。

前端采用 Apple 风格设计，默认中文界面，支持中英文切换。

## 特性

- 🎬 **多平台下载** — YouTube、Bilibili、抖音（Douyin）等 1700+ 网站
- 🤖 **AI 视频分析** — 基于 DeepSeek 大模型的视频总结（打字机逐字渲染）、思维导图、AI 问答
- 📝 **字幕提取** — 自动提取字幕/转录文本（支持 YouTube 自动字幕、B 站 CC 字幕）
- 🧠 **思维导图** — AI 自动生成结构化思维导图，基于 markmap (D3.js) 渲染，支持缩放拖拽、节点折叠、全屏展示、SVG/PNG 高清导出
- 💬 **AI 问答** — 针对视频内容提问，流式对话回复
- 🍎 **Apple 风格 UI** — 极简高级设计，Vue 3 + Vite 前端
- 🇨🇳 **中文优先** — 默认中文界面，一键切换 English
- 🎯 **抖音免登录** — Playwright 自动获取 cookie，无需用户操作
- 📊 **实时进度** — SSE 流式推送下载进度
- 🎨 **格式选择** — 1080p / 720p / 480p / Audio 可选
- 🖼️ **封面预览** — 缩略图代理，突破防盗链

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python FastAPI + yt-dlp + Playwright + DeepSeek API |
| 前端 | Vue 3 + Vite + markmap (D3.js 思维导图) |
| 通信 | REST API + SSE 进度推送 + EventSource 流式 |
| AI | DeepSeek V4 Pro（OpenAI 兼容 SDK） |
| 设计 | Apple 风格设计 Token |

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
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── App.vue            # 根组件（状态 + 语言管理）
│       ├── main.js
│       ├── i18n.js            # 中英文文案
│       ├── sse.js             # SSE 流读取工具
│       ├── style.css          # Apple 设计系统
│       └── components/
│           ├── NavBar.vue          # 毛玻璃导航栏
│           ├── HeroSection.vue     # Hero + URL 输入
│           ├── VideoPreview.vue    # 视频信息 + 格式选择
│           ├── DownloadProgress.vue# 实时进度条
│           ├── FileList.vue        # 已下载列表
│           ├── ProBanner.vue       # 付费升级横幅
│           ├── AiPanel.vue         # AI 功能标签页容器
│           ├── SummaryCard.vue     # AI 总结（DOM 逐字打字机动画）
│           ├── MindMap.vue         # 思维导图（markmap 渲染，支持缩放/全屏/SVG+PNG 导出）
│           └── QAChat.vue          # AI 问答（DOM 逐字打字机动画）
└── downloads/                 # 下载存储目录
```

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
| 其他 1700+ 网站 | ✅ | ✅ | ✅ | ✅ |

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
  ├─ AI 总结: 字幕 → DeepSeek SSE 流式 → DOM 逐字打字机渲染
  ├─ 思维导图: 字幕 → DeepSeek JSON 模式 → markmap (D3.js) 交互式渲染 → SVG/PNG 导出
  └─ AI 问答: 字幕 + 用户问题 → DeepSeek 流式回复
```

## License

MIT
