<script setup>
const faqs = [
  { q: 'VideoDown 支持哪些视频平台？', a: 'VideoDown 基于 yt-dlp 技术，支持 YouTube、Bilibili、抖音、TikTok、Twitter/X、Instagram、Facebook、Vimeo 等 1800+ 全球主流视频和社交媒体平台。' },
  { q: 'VideoDown 是免费的吗？', a: '完全免费。无需注册登录，无需安装任何软件。支持无限次下载，多种清晰度选择（360p 至 4K）。无广告，无追踪，打开浏览器即用。' },
  { q: '如何使用 VideoDown 下载 YouTube 视频？', a: '只需 3 步：1. 复制 YouTube 视频链接；2. 粘贴到输入框点击解析；3. 选择清晰度点击下载。全程无需登录，手机浏览器也能操作。' },
  { q: '可以下载抖音无水印视频吗？', a: '可以。内置 Playwright 专用解析模块，直接从渲染页面提取无水印视频链接。无需提供 Cookie 或登录，粘贴抖音分享链接即可下载。' },
  { q: 'AI 视频总结功能是什么？', a: '基于 DeepSeek 大模型自动提取视频字幕并分析，生成结构化摘要、思维导图和字幕文本。支持针对视频内容进行多轮 AI 问答，快速理解长视频。' },
  { q: '和其他视频下载工具有什么区别？', a: '核心优势：1. 支持 1800+ 平台，远超同类 10-50 个；2. 内置 AI 总结和思维导图；3. 完全在线无需安装；4. 抖音无水印下载；5. 多格式字幕导出。' },
  { q: '手机上可以使用吗？', a: '可以。响应式设计完美适配手机浏览器（Chrome、Safari）。手机访问与电脑体验一致，无需安装任何 App。' },
]
</script>

<template>
  <section class="faq">
    <div class="container">
      <div class="section-header reveal-header">
        <h2 class="sec-title">常见问题</h2>
        <p class="sec-sub">关于 VideoDown 的更多信息</p>
      </div>
      <div class="faq-list">
        <details v-for="(item, i) in faqs" :key="i" class="faq-item reveal-card" :style="{ transitionDelay: `${i * 0.06}s` }">
          <summary class="faq-q">
            <span>{{ item.q }}</span>
            <svg viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </summary>
          <div class="faq-a">
            <p>{{ item.a }}</p>
          </div>
        </details>
      </div>
    </div>
  </section>
</template>

<style scoped>
.faq {
  padding: 112px 0;
  background: linear-gradient(180deg, #f8f9fa 0%, #f5f5f7 50%, #fafafa 100%);
}

.sec-title { font-size: 52px; font-weight: 700; letter-spacing: -0.03em; color: #1d1d1f; text-align: center; margin-bottom: 14px; }
.sec-sub   { font-size: 19px; color: #86868b; text-align: center; margin-bottom: 64px; }

.faq-list { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }

.faq-item {
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}
.faq-item[open] {
  box-shadow: 0 8px 36px rgba(0,0,0,0.08);
}

/* summary = the clickable question bar */
.faq-q {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 22px 28px;
  font-size: 17px; font-weight: 500; color: #1d1d1f;
  line-height: 1.5; cursor: pointer;
  list-style: none; /* hide default triangle */
  user-select: none;
}
.faq-q::-webkit-details-marker { display: none; }
.faq-q:hover { color: #0071e3; }

.faq-q svg {
  flex-shrink: 0; color: #86868b;
  transition: transform 0.3s ease;
}
.faq-item[open] .faq-q svg {
  transform: rotate(180deg);
  color: #0071e3;
}

/* answer — content below the summary */
.faq-a {
  padding: 0 28px 24px;
  font-size: 15px; color: #6e6e73; line-height: 1.8;
}

@media (max-width: 640px) {
  .sec-title { font-size: 34px; }
  .faq-q { font-size: 15px; padding: 18px 20px; }
  .faq-a { padding: 0 20px 20px; }
}
</style>
