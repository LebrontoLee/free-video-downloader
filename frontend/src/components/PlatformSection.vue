<script setup>
const platforms = [
  { n: 'YouTube',   c: '#FF0000' },
  { n: 'Bilibili',  c: '#FB7299' },
  { n: 'TikTok',    c: '#000' },
  { n: '抖音',      c: '#FE2C55' },
  { n: 'Instagram', c: '#E4405F' },
  { n: 'Twitter/X', c: '#1DA1F2' },
  { n: 'Facebook',  c: '#1877F2' },
  { n: 'Vimeo',     c: '#1AB7EA' },
]
</script>

<template>
  <section class="plat">
    <div class="container">
      <div class="section-header reveal-header">
        <h2 class="sec-title">支持的平台</h2>
        <p class="sec-sub">覆盖全球主流视频和社交媒体平台</p>
      </div>
      <div class="chips">
        <span v-for="(p, i) in platforms" :key="p.n" class="chip reveal-card" :style="{ transitionDelay: `${i * 0.05}s`, borderColor: p.c + '30' }"><span class="dot" :style="{ background: p.c }"></span>{{ p.n }}</span>
      </div>
      <p class="more reveal">及 1,800+ 更多平台</p>
    </div>
  </section>
</template>

<style scoped>
.plat { padding: 112px 0; background: linear-gradient(180deg, #f5f5f7 0%, #fff 100%); }

.sec-title { font-size: 52px; font-weight: 700; letter-spacing: -0.03em; color: #1d1d1f; text-align: center; margin-bottom: 14px; }
.sec-sub   { font-size: 19px; color: #86868b; text-align: center; margin-bottom: 56px; }

.chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 14px; max-width: 720px; margin: 0 auto 28px; }

.chip {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 24px; border-radius: 9999px;
  background: #fff; border: 1.5px solid rgba(0,0,0,0.08);
  font-size: 16px; font-weight: 500; color: #1d1d1f;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  cursor: default;
}
.chip:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }

.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

.more { text-align: center; font-size: 17px; font-weight: 500; color: #86868b; }

@media (max-width: 640px) { .sec-title { font-size: 36px; } .chip { font-size: 14px; padding: 10px 18px; } }
</style>
