<script setup>
import { inject } from 'vue'

const t = inject('t')
</script>

<template>
  <section class="section">
    <div class="container">
      <div class="pro-card reveal">
        <div class="pro-badge">{{ t.pro_badge }}</div>
        <h2 class="pro-title">{{ t.pro_title }}</h2>
        <p class="pro-desc">{{ t.pro_desc }}</p>

        <ul class="pro-features">
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_1 }}</li>
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_2 }}</li>
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_3 }}</li>
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_4 }}</li>
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_5 }}</li>
          <li class="pro-feature"><svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.pro_feat_6 }}</li>
        </ul>

        <div class="pro-pricing">
          <span class="pro-price">{{ t.pro_price }}</span>
          <span class="pro-period">{{ t.pro_period }}</span>
        </div>

        <button class="pro-cta">
          {{ t.pro_cta }}
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <p class="pro-note">{{ t.pro_note }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pro-card { position: relative; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 24px; padding: 64px 40px; text-align: center; color: #fff; overflow: hidden; }
.pro-card::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%); pointer-events: none; }
.pro-badge { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; background: rgba(255,255,255,0.18); padding: 4px 12px; border-radius: 9999px; margin-bottom: 16px; backdrop-filter: blur(10px); }
.pro-title { font-size: 32px; font-weight: 700; letter-spacing: -0.025em; margin-bottom: 8px; }
.pro-desc { font-size: 17px; opacity: 0.85; max-width: 400px; margin: 0 auto 24px; }
.pro-features { list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; max-width: 540px; margin: 0 auto 40px; text-align: left; }
.pro-feature { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 500; opacity: 0.92; }
.pro-feature svg { flex-shrink: 0; opacity: 0.9; }
.pro-pricing { margin-bottom: 24px; }
.pro-price { font-size: 40px; font-weight: 700; letter-spacing: -0.025em; }
.pro-period { font-size: 17px; opacity: 0.75; }
.pro-cta { display: inline-flex; align-items: center; gap: 8px; padding: 14px 32px; border: none; border-radius: 9999px; background: #fff; color: #764ba2; font-family: inherit; font-size: 17px; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-bottom: 16px; }
.pro-cta:hover { transform: scale(1.03); box-shadow: 0 8px 30px rgba(0,0,0,0.2); }
.pro-note { font-size: 12px; opacity: 0.6; }
</style>
