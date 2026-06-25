<script setup>
import { inject } from 'vue'

const t = inject('t')
const lang = inject('lang')

defineEmits(['reset', 'toggleLang'])
</script>

<template>
  <nav class="navbar">
    <div class="nav-inner">
      <a href="#" class="nav-logo" @click.prevent="$emit('reset')">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" width="22" height="22">
          <path d="M21 7.5L12 2.25L3 7.5V16.5L12 21.75L21 16.5V7.5Z" fill="currentColor" opacity="0.15"/>
          <path d="M12 2.25L3 7.5V16.5L12 21.75L21 16.5V7.5L12 2.25Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M12 9.75L16.5 7.5L12 5.25L7.5 7.5L12 9.75Z" fill="currentColor"/>
          <path d="M12 9.75V16.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span class="nav-title">{{ t.nav_title }}</span>
      </a>
      <div class="nav-right">
        <button class="lang-btn" @click="$emit('toggleLang')" :title="t.lang_switch">
          {{ t.lang_switch }}
        </button>
        <a href="#" class="nav-pro" @click.prevent="$emit('reset')">
          {{ t.nav_pro }}
        </a>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 48px;
  background: rgba(245, 245, 247, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.nav-inner {
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  height: 100%; display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { display: flex; align-items: center; gap: 8px; color: #1d1d1f; font-size: 17px; font-weight: 600; letter-spacing: -0.022em; text-decoration: none; transition: opacity 0.2s; }
.nav-logo:hover { opacity: 0.7; }
.logo-icon { color: #0071e3; }
.nav-right { display: flex; align-items: center; gap: 12px; }
.lang-btn {
  font-size: 12px; font-weight: 500; color: #6e6e73;
  background: rgba(0,0,0,0.04); border: 1px solid #d2d2d7; border-radius: 9999px;
  padding: 4px 10px; cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.lang-btn:hover { background: rgba(0,0,0,0.08); color: #1d1d1f; }
.nav-pro { font-size: 13px; font-weight: 500; color: #0071e3; text-decoration: none; padding: 4px 12px; border-radius: 9999px; transition: background 0.2s; }
.nav-pro:hover { background: rgba(0, 113, 227, 0.08); }
</style>
