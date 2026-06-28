<script setup>
import { inject } from 'vue'

const t = inject('t')
defineProps({ files: Array, apiBase: String })
defineEmits(['refresh'])

function formatDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) } catch { return '' }
}
</script>

<template>
  <section v-if="files.length > 0" class="section">
    <div class="container">
      <div class="files-card card glass reveal">
        <div class="files-header">
          <h3 class="files-title">{{ t.files_title }}</h3>
          <button class="refresh-btn" @click="$emit('refresh')" title="Refresh">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <ul class="files-list">
          <li v-for="file in files" :key="file.filename" class="file-row">
            <div class="file-info">
              <svg class="file-icon" viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="file-name">{{ file.filename }}</span>
            </div>
            <div class="file-meta">
              <span class="file-size">{{ file.size_str }}</span>
            </div>
            <a :href="`${apiBase}/api/downloads/${file.filename}`" class="file-dl-btn" download title="Download">
              <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </a>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.files-card { padding: 28px 40px; }
.files-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.files-title { font-size: 15px; font-weight: 600; color: #1d1d1f; }
.refresh-btn { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; background: rgba(255,255,255,0.5); color: #6e6e73; cursor: pointer; transition: all 0.2s; }
.refresh-btn:hover { background: rgba(255,255,255,0.8); color: #1d1d1f; }
.files-list { list-style: none; }
.file-row { display: flex; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid #e8e8ed; }
.file-row:last-child { border-bottom: none; }
.file-info { flex: 1; display: flex; align-items: center; gap: 10px; min-width: 0; }
.file-icon { flex-shrink: 0; color: #6e6e73; }
.file-name { font-size: 14px; color: #1d1d1f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-meta { flex-shrink: 0; }
.file-size { font-size: 13px; color: #6e6e73; font-variant-numeric: tabular-nums; }
.file-dl-btn { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 12px; color: #0071e3; transition: background 0.2s; }
.file-dl-btn:hover { background: rgba(0,113,227,0.08); }
</style>
