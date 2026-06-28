<script setup>
import { ref, computed, inject } from 'vue'

const t = inject('t')

const props = defineProps({
  subtitlesData: Object,
})

const sortAsc = ref(true)
const searchQuery = ref('')
const copied = ref(false)
const dropdownOpen = ref(false)

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function closeDropdown() {
  dropdownOpen.value = false
}

const subtitles = computed(() => {
  const items = props.subtitlesData?.subtitles || []
  // Already sorted by start time from backend; toggle reverse if needed
  return sortAsc.value ? items : [...items].reverse()
})

const filteredSubtitles = computed(() => {
  if (!searchQuery.value.trim()) return subtitles.value
  const q = searchQuery.value.toLowerCase()
  return subtitles.value.filter(s => s.text.toLowerCase().includes(q))
})

const stats = computed(() => ({
  total: subtitles.value.length,
  filtered: filteredSubtitles.value.length,
  language: props.subtitlesData?.language || 'unknown',
  isAuto: props.subtitlesData?.is_auto_generated || false,
  source: props.subtitlesData?.source || null,
}))

function formatTime(seconds) {
  if (seconds == null || isNaN(seconds)) return '--:--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function toSRT() {
  return subtitles.value.map((sub, i) => {
    const idx = i + 1
    const start = formatSrtTime(sub.start)
    const end = formatSrtTime(sub.end)
    return `${idx}\n${start} --> ${end}\n${sub.text}\n`
  }).join('\n')
}

function formatSrtTime(seconds) {
  if (seconds == null || isNaN(seconds)) return '00:00:00,000'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

function toPlainText() {
  return subtitles.value.map(s => s.text).join('\n')
}

function download(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadSRT() {
  const filename = (props.subtitlesData?.video_id || 'subtitles') + '.srt'
  download(filename, toSRT(), 'text/plain;charset=utf-8')
}

function downloadTXT() {
  const filename = (props.subtitlesData?.video_id || 'subtitles') + '.txt'
  download(filename, toPlainText(), 'text/plain;charset=utf-8')
}

async function copyAll() {
  const text = subtitles.value
    .map(s => `[${formatTime(s.start)}] ${s.text}`)
    .join('\n')
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}
</script>

<template>
  <div class="sv-root">
    <!-- Stats bar -->
    <div class="sv-stats">
      <div class="sv-stat-item">
        <span class="sv-stat-label">{{ t.sv_total || '共' }}</span>
        <span class="sv-stat-value">{{ stats.total }}</span>
        <span class="sv-stat-label">{{ t.sv_entries || '条字幕' }}</span>
      </div>
      <div class="sv-stat-divider"></div>
      <div class="sv-stat-item">
        <span class="sv-stat-label">{{ t.sv_lang || '语言' }}</span>
        <span class="sv-stat-value">{{ stats.language }}</span>
      </div>
      <div v-if="stats.isAuto" class="sv-stat-badge">{{ t.sv_auto || '自动生成' }}</div>
      <div v-else class="sv-stat-badge sv-stat-badge-manual">{{ t.sv_manual || '人工字幕' }}</div>
    </div>

    <!-- Toolbar: search + sort + actions -->
    <div class="sv-toolbar">
      <div class="sv-search">
        <svg viewBox="0 0 24 24" fill="none" width="16" height="16" class="sv-search-icon">
          <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="sv-search-input"
          :placeholder="t.sv_search_placeholder || '搜索字幕...'"
        />
        <button v-if="searchQuery" class="sv-search-clear" @click="searchQuery = ''">
          <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="sv-actions">
        <button
          class="sv-btn sv-btn-icon"
          :title="sortAsc ? (t.sv_sort_desc || '倒序') : (t.sv_sort_asc || '正序')"
          @click="sortAsc = !sortAsc"
        >
          <svg v-if="sortAsc" viewBox="0 0 24 24" fill="none" width="16" height="16">
            <path d="M3 4h13M3 8h9M3 12h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M18 20V4m0 0l3 3m-3-3l-3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" width="16" height="16">
            <path d="M3 4h13M3 8h9M3 12h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M18 4v16m0 0l3-3m-3 3l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button
          class="sv-btn sv-btn-icon"
          :title="t.sv_copy || '复制'"
          @click="copyAll"
        >
          <svg v-if="!copied" viewBox="0 0 24 24" fill="none" width="16" height="16">
            <path d="M8 4v12a2 2 0 002 2h8a2 2 0 002-2V7.242a2 2 0 00-.602-1.43L16.083 2.57A2 2 0 0014.685 2H10a2 2 0 00-2 2z" stroke="currentColor" stroke-width="2"/>
            <path d="M16 18v2a2 2 0 01-2 2H6a2 2 0 01-2-2V9a2 2 0 012-2h2" stroke="currentColor" stroke-width="2"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" width="16" height="16">
            <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <div class="sv-dropdown" :class="{ open: dropdownOpen }">
          <button class="sv-btn sv-btn-download" :title="t.sv_download || '下载'" @click.stop="toggleDropdown">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ t.sv_download || '下载' }}</span>
            <svg viewBox="0 0 24 24" fill="none" width="12" height="12" class="sv-chevron" :class="{ flip: dropdownOpen }">
              <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <div v-if="dropdownOpen" class="sv-dropdown-menu" @click="closeDropdown">
            <button @click="downloadSRT(); closeDropdown()">
              <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="2"/>
                <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ t.sv_download_srt || '下载 SRT' }}
            </button>
            <button @click="downloadTXT(); closeDropdown()">
              <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="2"/>
                <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ t.sv_download_txt || '下载 TXT' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Click-outside backdrop -->
    <div v-if="dropdownOpen" class="sv-backdrop" @click="closeDropdown"></div>

    <!-- Subtitle list -->
    <div class="sv-list">
      <div v-if="filteredSubtitles.length === 0" class="sv-empty">
        <svg viewBox="0 0 24 24" fill="none" width="32" height="32" opacity="0.3">
          <path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-4.5H9m6-3H9m7.5 12.75h-9A2.25 2.25 0 016.75 19.5V4.5A2.25 2.25 0 019 2.25h6.75a2.25 2.25 0 012.25 2.25v15a2.25 2.25 0 01-2.25 2.25z" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <p>{{ searchQuery ? (t.sv_no_results || '无匹配结果') : (t.sv_empty || '暂无字幕') }}</p>
      </div>
      <div
        v-for="(sub, idx) in filteredSubtitles"
        :key="idx"
        class="sv-entry"
      >
        <span class="sv-timestamp">{{ formatTime(sub.start) }}</span>
        <span class="sv-text">{{ sub.text }}</span>
      </div>
    </div>

    <!-- Footer stats when filtering -->
    <div v-if="searchQuery && filteredSubtitles.length > 0" class="sv-filter-info">
      {{ t.sv_showing || '显示' }} {{ stats.filtered }} / {{ stats.total }} {{ t.sv_entries || '条字幕' }}
    </div>
  </div>
</template>

<style scoped>
.sv-root {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

/* Stats bar */
.sv-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: 13px;
}
.sv-stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.sv-stat-label {
  color: var(--color-text-sub);
}
.sv-stat-value {
  font-weight: 600;
  color: var(--color-text);
}
.sv-stat-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border);
}
.sv-stat-badge {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  background: #fff3e0;
  color: #e65100;
}
.sv-stat-badge-manual {
  background: #e8f5e9;
  color: #2e7d32;
}

/* Toolbar */
.sv-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sv-search {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}
.sv-search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-tertiary);
  pointer-events: none;
}
.sv-search-input {
  width: 100%;
  padding: 9px 36px 9px 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-family: var(--font-system);
  font-size: 13px;
  color: var(--color-text);
  transition: border-color var(--duration-fast) var(--ease-out);
}
.sv-search-input::placeholder {
  color: var(--color-text-tertiary);
}
.sv-search-input:focus {
  border-color: var(--color-accent);
  box-shadow: var(--shadow-glow);
}
.sv-search-clear {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: var(--color-border-light);
  color: var(--color-text-sub);
  cursor: pointer;
}
.sv-search-clear:hover {
  background: var(--color-border);
  color: var(--color-text);
}
.sv-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Buttons */
.sv-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-sub);
  font-family: var(--font-system);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}
.sv-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.sv-btn-icon {
  padding: 9px;
}

/* Dropdown — click-based */
.sv-dropdown {
  position: relative;
}
.sv-dropdown-menu {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 4px;
  min-width: 160px;
  padding: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  z-index: 20;
  animation: dropdownIn 0.15s var(--ease-out);
}
@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}
.sv-chevron {
  transition: transform 0.2s var(--ease-out);
}
.sv-chevron.flip {
  transform: rotate(180deg);
}
.sv-dropdown-menu button {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text);
  font-family: var(--font-system);
  font-size: 13px;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out);
}
.sv-dropdown-menu button:hover {
  background: var(--color-bg);
}

/* Click-outside backdrop */
.sv-backdrop {
  position: fixed;
  inset: 0;
  z-index: 15;
}

/* Subtitle list */
.sv-list {
  max-height: 480px;
  overflow-y: auto;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}
.sv-list::-webkit-scrollbar {
  width: 6px;
}
.sv-list::-webkit-scrollbar-track {
  background: transparent;
}
.sv-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}
.sv-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

.sv-entry {
  display: flex;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--duration-fast) var(--ease-out);
}
.sv-entry:last-child {
  border-bottom: none;
}
.sv-entry:hover {
  background: var(--color-surface);
}
.sv-timestamp {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-accent);
  background: rgba(0, 113, 227, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  height: fit-content;
  margin-top: 1px;
  min-width: 56px;
  text-align: center;
}
.sv-text {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.6;
}

/* Empty state */
.sv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 24px;
  color: var(--color-text-sub);
  font-size: 14px;
}

/* Filter info */
.sv-filter-info {
  text-align: center;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* Responsive */
@media (max-width: 600px) {
  .sv-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .sv-actions {
    justify-content: flex-end;
  }
  .sv-entry {
    padding: 8px 12px;
    gap: 8px;
  }
  .sv-timestamp {
    font-size: 11px;
    padding: 2px 6px;
    min-width: 48px;
  }
  .sv-text {
    font-size: 13px;
  }
}
</style>
