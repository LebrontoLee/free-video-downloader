<script setup>
const features = [
  { k: 'platforms', icon: 'globe' },
  { k: 'ai',        icon: 'sparkles' },
  { k: 'mindmap',   icon: 'diagram' },
  { k: 'subtitle',  icon: 'doc' },
  { k: 'douyin',    icon: 'video' },
  { k: 'noweb',     icon: 'device' },
]

const labels = {
  platforms: ['1800+ 平台支持', '覆盖 YouTube、Bilibili、抖音、TikTok 等全球主流平台，一个工具满足所有下载需求。'],
  ai:        ['AI 智能总结', '基于 DeepSeek 大模型自动分析视频内容，生成结构化摘要，快速了解核心要点。'],
  mindmap:   ['思维导图生成', 'AI 自动提取知识结构，交互式思维导图支持缩放拖拽、SVG/PNG 高清导出。'],
  subtitle:  ['字幕提取下载', '自动提取字幕，时间戳排序、搜索过滤，支持 SRT/VTT/TXT 多格式下载。'],
  douyin:    ['抖音无水印下载', '专用解析模块，无需登录和 Cookie，直接获取无水印高清视频。'],
  noweb:     ['无需安装', '纯网页应用，打开浏览器即用。响应式设计，手机电脑完美适配。'],
}
</script>

<template>
  <section class="feat">
    <div class="container">
      <div class="section-header reveal-header">
        <h2 class="sec-title">为什么选择 VideoDown</h2>
        <p class="sec-sub">集视频下载与 AI 智能分析于一体，一个链接搞定所有需求</p>
      </div>
      <div class="grid">
        <div v-for="(f, i) in features" :key="f.k" class="card reveal-card" :style="{ transitionDelay: `${i * 0.06}s` }">
          <div class="card-icon">
            <svg v-if="f.icon === 'globe'" viewBox="0 0 24 24" fill="none" width="28" height="28"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/><ellipse cx="12" cy="12" rx="4" ry="10" stroke="currentColor" stroke-width="1.5"/><path d="M2 12h20M12 2v20" stroke="currentColor" stroke-width="1.5"/></svg>
            <svg v-else-if="f.icon === 'sparkles'" viewBox="0 0 24 24" fill="none" width="28" height="28"><path d="M12 2l1.5 5.5L19 9l-5.5 1.5L12 16l-1.5-5.5L5 9l5.5-1.5L12 2z" fill="currentColor" opacity="0.3"/><path d="M18 13l1 4 4 1-4 1-1 4-1-4-4-1 4-1 1-4z" fill="currentColor"/></svg>
            <svg v-else-if="f.icon === 'diagram'" viewBox="0 0 24 24" fill="none" width="28" height="28"><rect x="8" y="3" width="8" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="3" y="13" width="7" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="14" y="13" width="7" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/><path d="M12 9v4M8.5 13H6.5M15.5 13h2" stroke="currentColor" stroke-width="1.5"/></svg>
            <svg v-else-if="f.icon === 'doc'" viewBox="0 0 24 24" fill="none" width="28" height="28"><path d="M6 3h8l6 6v12a1 1 0 01-1 1H6a1 1 0 01-1-1V4a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5"/><path d="M14 3v6h6" stroke="currentColor" stroke-width="1.5"/><path d="M8 13h8M8 17h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            <svg v-else-if="f.icon === 'video'" viewBox="0 0 24 24" fill="none" width="28" height="28"><rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" stroke-width="1.5"/><path d="M10 9.5v5l5.5-2.5L10 9.5z" fill="currentColor"/></svg>
            <svg v-else-if="f.icon === 'device'" viewBox="0 0 24 24" fill="none" width="28" height="28"><rect x="4" y="3" width="16" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M8 21h8M12 16v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
          <h3 class="card-title">{{ labels[f.k][0] }}</h3>
          <p class="card-desc">{{ labels[f.k][1] }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.feat { padding: 112px 0; background: linear-gradient(180deg, #f5f5f7 0%, #fafafa 40%, #fff 70%, #f8f9fa 100%); }

.sec-title { font-size: 52px; font-weight: 700; letter-spacing: -0.03em; color: #1d1d1f; text-align: center; margin-bottom: 14px; }
.sec-sub   { font-size: 19px; color: #86868b; text-align: center; margin-bottom: 64px; }

.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }

.card {
  padding: 42px 32px; border-radius: 20px; background: #fff;
  border: 1px solid rgba(0,0,0,0.06); text-align: center;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
}
.card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.08); }

.card-icon { width: 60px; height: 60px; margin: 0 auto 24px; display: flex; align-items: center; justify-content: center; border-radius: 16px; background: linear-gradient(135deg, #0071e3 0%, #5ac8fa 100%); color: #fff; }
.card-title { font-size: 19px; font-weight: 600; color: #1d1d1f; margin-bottom: 10px; }
.card-desc  { font-size: 15px; color: #6e6e73; line-height: 1.7; }

@media (max-width: 1024px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .grid { grid-template-columns: 1fr; } .sec-title { font-size: 36px; } .card { padding: 32px 24px; } }
</style>
