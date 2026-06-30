<script setup>
const steps = [
  { num: '01', t: '复制视频链接', d: '在 YouTube、Bilibili、抖音等平台找到想下载的视频，复制分享链接或地址栏 URL。' },
  { num: '02', t: '粘贴并解析',   d: '将链接粘贴到 VideoDown 输入框，系统自动识别平台并展示视频信息与可用格式。' },
  { num: '03', t: '选择清晰度下载', d: '从格式列表中选择想要的清晰度（最高 4K），点击下载保存到本地。还能一键 AI 分析。' },
]
</script>

<template>
  <section class="how">
    <div class="container">
      <div class="section-header reveal-header">
        <h2 class="sec-title">三步下载视频</h2>
        <p class="sec-sub">无需安装，无需注册，一分钟搞定</p>
      </div>
      <div class="steps">
        <div v-for="(s, i) in steps" :key="s.num" class="step reveal-card" :style="{ transitionDelay: `${i * 0.08}s` }">
          <span class="step-num">{{ s.num }}</span>
          <div>
            <h3 class="step-title">{{ s.t }}</h3>
            <p class="step-desc">{{ s.d }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.how { padding: 112px 0; background: #fff; }

.sec-title { font-size: 52px; font-weight: 700; letter-spacing: -0.03em; color: #1d1d1f; text-align: center; margin-bottom: 14px; }
.sec-sub   { font-size: 19px; color: #86868b; text-align: center; margin-bottom: 64px; }

.steps { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

.step {
  display: flex; align-items: flex-start; gap: 28px;
  padding: 36px 32px; border-radius: 20px; background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.step:hover { transform: translateY(-4px); box-shadow: 0 12px 36px rgba(0,0,0,0.06); }

.step-num { flex-shrink: 0; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; border-radius: 16px; font-size: 24px; font-weight: 700; color: #fff; background: linear-gradient(135deg, #0071e3 0%, #5ac8fa 100%); letter-spacing: -0.02em; }

.step-title { font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 6px; }
.step-desc  { font-size: 16px; color: #6e6e73; line-height: 1.7; }

@media (max-width: 640px) {
  .sec-title { font-size: 36px; }
  .step { padding: 28px 24px; gap: 20px; }
  .step-num { width: 44px; height: 44px; font-size: 20px; }
  .step-title { font-size: 17px; }
}
</style>
