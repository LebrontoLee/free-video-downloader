<script setup>
import { ref, inject } from 'vue'

const t = inject('t')
const props = defineProps({ loading: Boolean })
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
  <section class="hero section">
    <div class="container">
      <h1 class="hero-title animate-in">{{ t.hero_title }}</h1>
      <p class="hero-subtitle animate-in">{{ t.hero_sub }}</p>

      <div class="input-group animate-in" :class="{ 'is-loading': loading }">
        <div class="input-wrapper">
          <svg class="input-icon" viewBox="0 0 24 24" fill="none" width="20" height="20">
            <path d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <input
            v-model="url" type="url" class="url-input"
            :placeholder="t.hero_placeholder"
            @keydown.enter="handleSubmit" autofocus
          />
          <button class="submit-btn" :disabled="loading || !url.trim()" @click="handleSubmit">
            <span v-if="loading" class="spinner"></span>
            <svg v-else viewBox="0 0 24 24" fill="none" width="16" height="16">
              <path d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="trust-signals animate-in">
        <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_1 }}</div>
        <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_2 }}</div>
        <div class="trust-item"><svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>{{ t.hero_trust_3 }}</div>
      </div>

      <div class="examples animate-in">
        <span class="examples-label">{{ t.hero_examples }}</span>
        <button v-for="ex in examples" :key="ex.label" class="example-chip" @click="useExample(ex.url)">{{ ex.label }}</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero { text-align: center; padding-top: 96px; padding-bottom: 64px; }
.hero-title { font-size: 56px; font-weight: 700; letter-spacing: -0.028em; line-height: 1.07143; color: #1d1d1f; margin-bottom: 16px; }
.hero-subtitle { font-size: 19px; font-weight: 400; line-height: 1.4211; color: #6e6e73; margin-bottom: 40px; }
.input-group { max-width: 560px; margin: 0 auto 24px; }
.input-wrapper { position: relative; display: flex; align-items: center; background: #fff; border: 1px solid #d2d2d7; border-radius: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); transition: border-color 0.2s, box-shadow 0.2s; }
.input-wrapper:focus-within { border-color: #0071e3; box-shadow: 0 0 0 4px rgba(0,113,227,0.15); }
.input-icon { position: absolute; left: 16px; color: #6e6e73; pointer-events: none; }
.url-input { flex: 1; border: none; background: transparent; font-family: inherit; font-size: 17px; line-height: 1.47; color: #1d1d1f; padding: 14px 48px 14px 48px; outline: none; }
.url-input::placeholder { color: #86868b; }
.submit-btn { position: absolute; right: 6px; display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border: none; border-radius: 9999px; background: #0071e3; color: #fff; cursor: pointer; transition: background 0.2s, opacity 0.2s; }
.submit-btn:hover:not(:disabled) { background: #0066cc; }
.submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.trust-signals { display: flex; justify-content: center; gap: 40px; margin-bottom: 24px; flex-wrap: wrap; }
.trust-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #6e6e73; }
.trust-item svg { color: #34c759; flex-shrink: 0; }
.examples { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; }
.examples-label { font-size: 13px; color: #86868b; }
.example-chip { font-family: inherit; font-size: 13px; font-weight: 500; color: #0071e3; background: rgba(0,113,227,0.06); border: 1px solid rgba(0,113,227,0.15); border-radius: 9999px; padding: 4px 14px; cursor: pointer; transition: all 0.2s; }
.example-chip:hover { background: rgba(0,113,227,0.12); border-color: #0071e3; }
.is-loading .input-wrapper { opacity: 0.7; }

@media (max-width: 768px) {
  .hero { padding-top: 60px; }
  .hero-title { font-size: 36px; }
  .hero-subtitle { font-size: 17px; }
  .url-input { font-size: 16px; padding: 12px 44px 12px 42px; }
  .trust-signals { gap: 16px; }
}
</style>
