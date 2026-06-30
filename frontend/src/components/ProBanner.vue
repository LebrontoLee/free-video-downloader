<script setup>
import { inject } from 'vue'

const t = inject('t')
const user = inject('user')
const isPro = inject('isPro')
const handleUpgrade = inject('handleUpgrade')

function onUpgradeClick() {
  handleUpgrade()
}
</script>

<template>
  <section class="pro">
    <div class="container">
      <div class="pro-grid reveal-card">
        <!-- Free -->
        <div class="pro-col free-col">
          <span class="col-tag">免费版</span>
          <h3 class="col-price">免费</h3>
          <p class="col-desc">适合日常使用</p>
          <ul class="col-list">
            <li>无限次下载</li>
            <li>1080p 高清画质</li>
            <li>单个视频下载</li>
            <li>AI 视频总结</li>
            <li>思维导图生成</li>
            <li>字幕提取 &amp; 下载</li>
            <li>抖音无水印下载</li>
          </ul>
          <button class="col-btn free-btn">开始使用</button>
        </div>

        <!-- Pro -->
        <div class="pro-col pro-col-highlight">
          <span class="col-tag pro-tag">PRO</span>
          <h3 class="col-price">$4.99<span class="price-period"> / 月</span></h3>
          <p class="col-desc">解锁全部高级功能</p>
          <ul class="col-list">
            <li><strong>以上全部</strong> +</li>
            <li>4K / 8K 超高清</li>
            <li>批量下载多视频</li>
            <li>播放列表 &amp; 频道</li>
            <li>内置格式转换器</li>
            <li>优先下载速度</li>
            <li>零广告体验</li>
          </ul>
          <button
            v-if="!isPro"
            class="col-btn pro-btn"
            @click="onUpgradeClick"
          >
            {{ t.pro_upgrade_btn }}
          </button>
          <button
            v-if="isPro"
            class="col-btn pro-btn pro-active-btn"
            @click="onUpgradeClick"
          >
            {{ t.pro_manage_btn }}
          </button>
          <p v-if="!user" class="pro-note">{{ t.pro_login_first }}</p>
          <p v-if="isPro" class="pro-note pro-active-note">{{ t.pro_current_member }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pro {
  padding: var(--spacing-2xl) 0;
  background: #ffffff;
}

.pro-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 780px;
  margin: 0 auto;
}

.pro-col {
  border-radius: 20px;
  padding: 44px 36px;
  text-align: center;
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.pro-col:hover { transform: translateY(-4px); }

.pro-col-highlight {
  border-color: #0071e3;
  box-shadow: 0 4px 28px rgba(0,113,227,0.1);
  position: relative;
}

.col-tag {
  display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
  padding: 5px 14px; border-radius: 9999px; margin-bottom: 20px;
  background: rgba(0,0,0,0.04); color: #6e6e73;
}
.pro-tag {
  background: #0071e3; color: #fff;
}

.col-price {
  font-size: 44px; font-weight: 700; letter-spacing: -0.03em;
  color: #1d1d1f; margin-bottom: 4px;
}
.price-period { font-size: 18px; font-weight: 400; color: #86868b; }

.col-desc {
  font-size: 15px; color: #86868b; margin-bottom: 32px;
}

.col-list {
  list-style: none; text-align: left; margin-bottom: 32px;
}
.col-list li {
  padding: 10px 0; font-size: 15px; color: #1d1d1f;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  display: flex; align-items: center; gap: 10px;
}
.col-list li::before {
  content: ''; width: 18px; height: 18px;
  background: #34c759; border-radius: 50%;
  flex-shrink: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: 12px 12px;
  background-position: center;
  background-repeat: no-repeat;
}
.col-list li:last-child { border-bottom: none; }
.col-list li strong { color: #0071e3; }

.col-btn {
  width: 100%; padding: 14px; border: none; border-radius: 12px;
  font-family: inherit; font-size: 17px; font-weight: 600; cursor: pointer;
  transition: all 0.25s ease;
}
.free-btn {
  background: #f5f5f7; color: #1d1d1f;
}
.free-btn:hover { background: #e8e8ed; }
.pro-btn {
  background: #0071e3; color: #fff;
  box-shadow: 0 2px 12px rgba(0,113,227,0.25);
}
.pro-btn:hover { background: #0066cc; box-shadow: 0 6px 24px rgba(0,113,227,0.35); }
.pro-active-btn { background: #34c759; box-shadow: 0 2px 12px rgba(52,199,89,0.25); }
.pro-active-btn:hover { background: #2db84e; box-shadow: 0 6px 24px rgba(52,199,89,0.35); }

.pro-note { font-size: 12px; color: #aeaeb2; margin-top: 16px; }
.pro-active-note { color: #34c759; font-weight: 500; }

/* ── Responsive ─────────────────────────── */
@media (max-width: 640px) {
  .pro-grid { grid-template-columns: 1fr; }
  .pro-col { padding: 32px 24px; }
  .col-price { font-size: 36px; }
}
</style>
