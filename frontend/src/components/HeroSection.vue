<script setup>
import { ref, inject } from 'vue'

const t = inject('t')
const props = defineProps({ loading: Boolean, compact: Boolean })
const emit = defineEmits(['extract'])
const url = ref('')

const examples = [
  { label: 'YouTube', url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
  { label: 'Bilibili', url: 'https://www.bilibili.com/video/BV1GJ411x7h7' },
  { label: '抖音', url: 'https://www.douyin.com/video/7471186649574509874' },
]

function handleSubmit() {
  const trimmed = url.value.trim()
  if (!trimmed) return
  emit('extract', trimmed)
}

function useExample(u) { url.value = u; emit('extract', u) }
</script>

<template>
  <section class="hero">
    <div class="container">
      <!-- Top content — collapses smoothly, search bar stays anchored below -->
      <div class="hero-top" :class="{ collapsed: compact }">
        <h1 class="hero-title">{{ t.hero_title }}</h1>
        <p class="hero-subtitle">{{ t.hero_sub }}</p>
      </div>

      <!-- Search bar — always at the same position regardless of compact mode -->
      <div class="search-area" :class="{ 'is-loading': loading }">
        <div class="input-wrapper glass">
          <svg class="input-icon" viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <input
            v-model="url" type="url" class="url-input"
            :placeholder="t.hero_placeholder"
            @keydown.enter="handleSubmit"
          />
          <button class="submit-btn" :disabled="loading || !url.trim()" @click="handleSubmit">
            <span v-if="loading" class="spinner"></span>
            <svg v-else viewBox="0 0 24 24" fill="none" width="16" height="16">
              <path d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Bottom content — collapses smoothly -->
      <div class="hero-bottom" :class="{ collapsed: compact }">
        <div class="trust-signals">
          <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_1 }}</div>
          <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_2 }}</div>
          <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_3 }}</div>
        </div>

        <div class="examples">
          <span class="examples-label">{{ t.hero_examples }}</span>
          <button v-for="ex in examples" :key="ex.label" class="example-chip" @click="useExample(ex.url)">{{ ex.label }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ── Section base — padding-top is the anchor: same in both modes ──────── */
.hero {
  text-align: center;
  padding-top: 88px;   /* nav 48px + 40px breathing room */
  padding-bottom: 40px;
}

/* ── Collapsible top (title + subtitle) ─────────────────────────────────── */
.hero-top {
  max-height: 200px;
  overflow: hidden;
  opacity: 1;
  transition: max-height 0.45s var(--ease-out),
              opacity 0.35s var(--ease-out);
}
.hero-top.collapsed {
  max-height: 0;
  opacity: 0;
}
.hero-title {
  font-size: 64px; font-weight: 700; letter-spacing: -0.031em; line-height: 1.0625;
  color: #1d1d1f; margin-bottom: 16px;
  background: linear-gradient(135deg, #1d1d1f 0%, #3a3a3c 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-subtitle {
  font-size: 21px; font-weight: 400; line-height: 1.381;
  color: #6e6e73; padding-bottom: 28px;
}

/* ── Search bar — fixed position, never moves ──────────────────────────── */
.search-area {
  max-width: 620px;
  margin: 0 auto 24px;
}
.input-wrapper {
  position: relative; display: flex; align-items: center;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: saturate(180%) blur(12px);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 20px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
}
.input-wrapper:focus-within {
  border-color: #0071e3;
  box-shadow: 0 0 0 4px rgba(0,113,227,0.12), 0 4px 24px rgba(0,0,0,0.08);
  transform: scale(1.01);
}
.input-icon { position: absolute; left: 18px; color: #86868b; pointer-events: none; }
.url-input {
  flex: 1; border: none; background: transparent; font-family: inherit;
  font-size: 18px; line-height: 1.47; color: #1d1d1f;
  padding: 16px 52px 16px 52px; outline: none;
}
.url-input::placeholder { color: #86868b; }
.submit-btn {
  position: absolute; right: 8px; display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border: none; border-radius: 9999px;
  background: #0071e3; color: #fff; cursor: pointer;
  transition: background 0.2s, transform 0.2s, opacity 0.2s;
}
.submit-btn:hover:not(:disabled) { background: #0066cc; transform: scale(1.05); }
.submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.is-loading .input-wrapper { opacity: 0.7; pointer-events: none; }

/* ── Collapsible bottom (trust + examples) ──────────────────────────────── */
.hero-bottom {
  max-height: 120px;
  overflow: hidden;
  opacity: 1;
  transition: max-height 0.45s var(--ease-out),
              opacity 0.35s var(--ease-out);
}
.hero-bottom.collapsed {
  max-height: 0;
  opacity: 0;
}

.trust-signals { display: flex; justify-content: center; gap: 48px; margin-bottom: 24px; flex-wrap: wrap; }
.trust-item { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #6e6e73; }
.trust-item svg { color: #34c759; flex-shrink: 0; }

.examples { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; }
.examples-label { font-size: 14px; color: #86868b; }
.example-chip {
  font-family: inherit; font-size: 14px; font-weight: 500;
  color: #0071e3; background: rgba(0,113,227,0.05);
  border: 1px solid rgba(0,113,227,0.12);
  border-radius: 9999px; padding: 5px 16px; cursor: pointer;
  transition: all 0.25s;
}
.example-chip:hover { background: rgba(0,113,227,0.1); border-color: #0071e3; transform: translateY(-1px); }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .hero { padding-top: 72px; }
  .hero-top { max-height: 160px; }
  .hero-title { font-size: 40px; }
  .hero-subtitle { font-size: 17px; padding-bottom: 20px; }
  .search-area { max-width: 100%; }
  .url-input { font-size: 16px; padding: 14px 48px 14px 44px; }
  .trust-signals { gap: 20px; }
}
</style>
