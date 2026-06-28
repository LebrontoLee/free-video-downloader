<script setup>
import { ref, reactive, provide, computed, onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import VideoPreview from './components/VideoPreview.vue'
import DownloadProgress from './components/DownloadProgress.vue'
import FileList from './components/FileList.vue'
import ProBanner from './components/ProBanner.vue'
import AiPanel from './components/AiPanel.vue'
import messages from './i18n.js'

// ─── i18n ───────────────────────────────────────────────────────────────────
const lang = ref('zh')
const t = computed(() => messages[lang.value])

function toggleLang() {
  lang.value = lang.value === 'zh' ? 'en' : 'zh'
}

provide('t', t)
provide('lang', lang)

// ─── API Base ───────────────────────────────────────────────────────────────
const API_BASE = ''

// ─── State ─────────────────────────────────────────────────────────────────
const view = ref('hero')
const isLoading = ref(false)
const error = ref('')

const video = ref(null)
const selectedFormat = ref(null)
const taskId = ref(null)
const eventSource = ref(null)

const download = reactive({
  status: null,
  percent: 0,
  downloadedStr: '',
  totalStr: '',
  speedStr: '',
  eta: 0,
  message: '',
  filename: '',
})

const files = ref([])

// ─── AI State ────────────────────────────────────────────────────────────────
const aiStatus = reactive({
  subtitlesStatus: 'idle',   // 'idle' | 'loading' | 'loaded' | 'unavailable' | 'error'
  subtitlesData: null,
  subtitlesError: '',
  activeTab: 'summary',
})

// ─── Actions ────────────────────────────────────────────────────────────────

async function handleExtract(url) {
  isLoading.value = true
  error.value = ''
  video.value = null
  selectedFormat.value = null

  // Only switch to full hero on the very first search; subsequent searches
  // stay in the current view to avoid a jarring flash of the hero content.
  const isFirstSearch = view.value === 'hero'
  if (isFirstSearch) {
    view.value = 'hero'
  }

  try {
    const res = await fetch(`${API_BASE}/api/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
    const data = await res.json()
    if (!res.ok || !data.success) {
      error.value = data.detail || t.value.error_extract
      return
    }
    video.value = data.data
    if (data.data.formats.length > 0) {
      selectedFormat.value = data.data.formats[0].format_id
    }
    view.value = 'preview'
    // Wait for DOM update, then scroll with offset for fixed nav + compact hero
    const delay = isFirstSearch ? 200 : 100  // longer delay on first search for compact transition
    setTimeout(() => {
      const el = document.getElementById('preview-section')
      if (!el) return
      const top = el.getBoundingClientRect().top + window.scrollY - 140
      window.scrollTo({ top, behavior: 'smooth' })
    }, delay)
  } catch {
    error.value = t.value.error_network
  } finally {
    isLoading.value = false
  }
}

async function startDownload(url, formatId) {
  error.value = ''
  Object.assign(download, { status: null, percent: 0, downloadedStr: '', totalStr: '', speedStr: '', eta: 0, message: '', filename: '' })

  try {
    const res = await fetch(`${API_BASE}/api/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format_id: formatId }),
    })
    const data = await res.json()
    if (!res.ok || !data.success) {
      error.value = data.detail || 'Download failed'
      return
    }
    taskId.value = data.task_id
    view.value = 'downloading'
    connectSSE(data.task_id)
  } catch {
    error.value = t.value.error_network
  }
}

function connectSSE(id) {
  if (eventSource.value) eventSource.value.close()
  const es = new EventSource(`${API_BASE}/api/download/${id}/progress`)
  eventSource.value = es

  es.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data)
    if (data.status === 'downloading') {
      Object.assign(download, {
        status: 'downloading', percent: data.percent,
        downloadedStr: data.downloaded_str, totalStr: data.total_str,
        speedStr: data.speed_str, eta: data.eta,
      })
    }
  })
  es.addEventListener('processing', (e) => {
    const data = JSON.parse(e.data)
    download.status = 'processing'
    download.message = data.message
  })
  es.addEventListener('complete', (e) => {
    const data = JSON.parse(e.data)
    download.status = 'finished'
    download.filename = data.filename
    view.value = 'complete'
    es.close()
    eventSource.value = null
    fetchFiles()
  })
  es.addEventListener('error', () => {
    if (download.status === 'finished') {
      es.close()
      eventSource.value = null
    }
  })
}

async function fetchFiles() {
  try {
    const res = await fetch(`${API_BASE}/api/files`)
    const data = await res.json()
    if (data.success) files.value = data.files
  } catch { /* non-critical */ }
}

function handleReset() {
  view.value = 'hero'
  video.value = null
  selectedFormat.value = null
  error.value = ''
  download.status = null
}

function handleDownload() {
  if (!video.value || !selectedFormat.value) return
  startDownload(video.value.webpage_url, selectedFormat.value)
}

async function openAiPanel() {
  if (!video.value) return
  aiStatus.subtitlesStatus = 'loading'
  aiStatus.subtitlesData = null
  aiStatus.subtitlesError = ''
  aiStatus.activeTab = 'summary'
  view.value = 'ai'

  try {
    const res = await fetch(`${API_BASE}/api/ai/subtitles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: video.value.webpage_url }),
    })
    const data = await res.json()
    if (data.success && data.data) {
      aiStatus.subtitlesData = data.data
      aiStatus.subtitlesStatus = data.data.available !== false ? 'loaded' : 'unavailable'
    } else {
      aiStatus.subtitlesStatus = 'unavailable'
    }
  } catch (e) {
    aiStatus.subtitlesStatus = 'error'
    aiStatus.subtitlesError = t.value.error_network
  }
}

function closeAiPanel() {
  view.value = video.value ? 'preview' : 'hero'
}

fetchFiles()

// ─── Scroll-triggered reveal animation ────────────────────────────────────
onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  )

  // Observe existing .reveal elements
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el))

  // Re-scan for dynamically added .reveal elements (e.g., after view switches)
  const mutationObserver = new MutationObserver(() => {
    document.querySelectorAll('.reveal:not(.is-visible)').forEach((el) => {
      if (!el.dataset.revealObserved) {
        el.dataset.revealObserved = '1'
        observer.observe(el)
      }
    })
  })
  mutationObserver.observe(document.body, { childList: true, subtree: true })
})
</script>

<template>
  <div class="app">
    <NavBar :lang="lang" @reset="handleReset" @toggle-lang="toggleLang" />

    <main class="main">
      <HeroSection :loading="isLoading" :compact="view !== 'hero'" @extract="handleExtract" />

      <!-- Error -->
      <div v-if="error" class="container">
        <div class="error-banner animate-in">
          <svg class="error-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/>
          </svg>
          <span>{{ error }}</span>
          <button class="error-dismiss" @click="error = ''">&times;</button>
        </div>
      </div>

      <!-- Video Preview -->
      <div id="preview-section">
        <VideoPreview
          v-if="video && (view === 'preview' || view === 'downloading' || view === 'complete')"
          :video="video"
          :selected-format="selectedFormat"
          :is-downloading="view === 'downloading'"
          @select-format="selectedFormat = $event"
          @download="handleDownload"
          @reset="handleReset"
          @ai-features="openAiPanel"
        />
      </div>

      <!-- AI Panel -->
      <AiPanel
        v-if="view === 'ai' && video"
        :url="video.webpage_url"
        :video-title="video.title"
        :subtitles-status="aiStatus.subtitlesStatus"
        :subtitles-data="aiStatus.subtitlesData"
        :subtitles-error="aiStatus.subtitlesError"
        @back="closeAiPanel"
        @update:active-tab="aiStatus.activeTab = $event"
      />

      <!-- Progress -->
      <DownloadProgress
        v-if="view === 'downloading' || view === 'complete'"
        :download="download"
        :filename="download.filename"
        :api-base="API_BASE"
      />

      <!-- File List -->
      <FileList :files="files" :api-base="API_BASE" @refresh="fetchFiles" />

      <!-- Pro Banner -->
      <ProBanner />
    </main>

    <!-- Footer -->
    <footer class="footer glass">
      <div class="container">
        <p class="footer-text">
          {{ t.footer_powered }} <a href="https://github.com/yt-dlp/yt-dlp" target="_blank">yt-dlp</a>
          &nbsp;·&nbsp; {{ t.footer_sites }}
          &nbsp;·&nbsp; {{ t.footer_no_account }}
        </p>
        <p class="footer-copy">{{ t.footer_copy }}</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.main { flex: 1; padding-top: 88px; }

.error-banner {
  display: flex; align-items: center; gap: 8px;
  background: #fff2f0; border: 1px solid #ffccc7;
  border-radius: 12px; padding: 12px 16px;
  margin-bottom: 24px; color: #ff3b30; font-size: 14px;
}
.error-icon { flex-shrink: 0; }
.error-dismiss { margin-left: auto; background: none; border: none; color: #ff3b30; font-size: 20px; cursor: pointer; opacity: 0.6; }
.error-dismiss:hover { opacity: 1; }

.footer {
  margin-top: auto; padding: 48px 0; text-align: center;
  border-top: 1px solid rgba(0,0,0,0.06);
  background: rgba(245, 245, 247, 0.6);
  backdrop-filter: saturate(180%) blur(16px);
  -webkit-backdrop-filter: saturate(180%) blur(16px);
}
.footer-text { font-size: 14px; color: #6e6e73; margin-bottom: 6px; }
.footer-text a { color: #6e6e73; text-decoration: underline; transition: color 0.2s; }
.footer-text a:hover { color: #1d1d1f; }
.footer-copy { font-size: 12px; color: #86868b; }
</style>
