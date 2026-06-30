<script setup>
import { ref, reactive, provide, computed, onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import VideoPreview from './components/VideoPreview.vue'
import DownloadProgress from './components/DownloadProgress.vue'
import FileList from './components/FileList.vue'
import ProBanner from './components/ProBanner.vue'
import AiPanel from './components/AiPanel.vue'
import AuthModal from './components/AuthModal.vue'
import FeatureSection from './components/FeatureSection.vue'
import HowToSection from './components/HowToSection.vue'

import FAQSection from './components/FAQSection.vue'
import PlatformSection from './components/PlatformSection.vue'
import AppFooter from './components/AppFooter.vue'
import { useScrollEffects } from './scrollEffects.js'
import messages from './i18n.js'

// ─── i18n ───────────────────────────────────────────────────────────────────
const lang = ref('zh')
const t = computed(() => messages[lang.value])

function toggleLang() {
  lang.value = lang.value === 'zh' ? 'en' : 'zh'
}

const scrollFx = useScrollEffects()

// ─── Auth State ────────────────────────────────────────────────────────────────
const user = ref(null)            // { id, email, is_pro, pro_expires_at } or null
const showAuthModal = ref(false)
const paymentView = ref(null)     // 'success' | 'cancel' | null
const usageStatus = ref({ remaining: 3, limit: 3, used_today: 0, is_pro: false })

const isPro = computed(() => user.value?.is_pro === true)

async function fetchUser() {
  const token = localStorage.getItem('auth_token')
  if (!token) return
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (data.success && data.user) {
      user.value = data.user
      fetchUsageStatus()
    } else {
      localStorage.removeItem('auth_token')
    }
  } catch { /* network error — keep token for retry */ }
}

async function fetchUsageStatus() {
  const token = localStorage.getItem('auth_token')
  if (!token) return
  try {
    const res = await fetch(`${API_BASE}/api/usage/status`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (data.success) {
      usageStatus.value = {
        remaining: data.remaining,
        limit: data.limit,
        used_today: data.used_today,
        is_pro: data.is_pro,
      }
    }
  } catch { /* non-critical */ }
}

function handleAuthenticated({ token, user: u }) {
  user.value = u
  showAuthModal.value = false
  fetchUsageStatus()
}

function handleLogout() {
  localStorage.removeItem('auth_token')
  user.value = null
  usageStatus.value = { remaining: 3, limit: 3, used_today: 0, is_pro: false }
}

function openAuthModal() {
  showAuthModal.value = true
}

async function handleUpgrade() {
  // Requires login first
  if (!user.value) {
    openAuthModal()
    return
  }

  // Already PRO — go to customer portal
  if (user.value.is_pro) {
    const token = localStorage.getItem('auth_token')
    try {
      const res = await fetch(`${API_BASE}/api/payments/portal?return_url=${encodeURIComponent(window.location.origin)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.success && data.url) {
        window.location.href = data.url
      } else {
        alert(data.detail || 'Failed to open subscription management')
      }
    } catch { alert(t.value.error_network) }
    return
  }

  // Create checkout session
  const token = localStorage.getItem('auth_token')
  try {
    const res = await fetch(`${API_BASE}/api/payments/create-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        success_url: `${window.location.origin}?payment=success`,
        cancel_url: `${window.location.origin}?payment=cancel`,
      }),
    })
    const data = await res.json()
    if (data.success && data.url) {
      window.location.href = data.url
    } else {
      alert(data.detail || 'Failed to create checkout')
    }
  } catch { alert(t.value.error_network) }
}

// Check for payment redirect on mount
async function checkPaymentRedirect() {
  const params = new URLSearchParams(window.location.search)
  const token = localStorage.getItem('auth_token')

  if (params.get('payment') === 'success') {
    const sessionId = params.get('session_id')
    // Clean URL immediately so refreshing doesn't re-trigger
    window.history.replaceState({}, '', window.location.pathname)

    // First ensure user info is loaded
    if (token) {
      await fetchUser()
    }

    // Verify the session with backend to get up-to-date PRO status
    if (sessionId && token && user.value) {
      try {
        const res = await fetch(`${API_BASE}/api/payments/verify-session`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ session_id: sessionId }),
        })
        const data = await res.json()
        if (data.success && (data.is_pro || data.status === 'paid')) {
          // Refresh user from DB to get authoritative PRO status
          await fetchUser()
          await fetchUsageStatus()
        }
      } catch {
        // fetchUser already ran above, so user is loaded
      }
    }
    paymentView.value = 'success'
  } else if (params.get('payment') === 'cancel') {
    paymentView.value = 'cancel'
    window.history.replaceState({}, '', window.location.pathname)
  }
}

provide('t', t)
provide('lang', lang)
provide('scrollFx', scrollFx)
provide('user', user)
provide('isPro', isPro)
provide('usageStatus', usageStatus)
provide('openAuthModal', openAuthModal)
provide('handleLogout', handleLogout)
provide('handleUpgrade', handleUpgrade)
provide('fetchUsageStatus', fetchUsageStatus)

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
    // Wait for DOM update + compact hero transition, then scroll with offset
    setTimeout(() => {
      const el = document.getElementById('preview-section')
      if (!el) return
      const top = el.getBoundingClientRect().top + window.scrollY - 200
      window.scrollTo({ top, behavior: 'smooth' })
    }, 200)
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
// Initialize auth state and check for payment redirects
fetchUser()
checkPaymentRedirect()

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
    { threshold: 0.15, rootMargin: '0px 0px -80px 0px' }
  )

  const REVEAL_SELECTOR = '.reveal, .reveal-header, .reveal-card, .reveal-blur'

  // Observe existing reveal elements
  document.querySelectorAll(REVEAL_SELECTOR).forEach((el) => observer.observe(el))

  // Re-scan for dynamically added reveal elements (e.g., after view switches)
  const mutationObserver = new MutationObserver(() => {
    document.querySelectorAll(`${REVEAL_SELECTOR}:not(.is-visible)`).forEach((el) => {
      if (!el.dataset.revealObserved) {
        el.dataset.revealObserved = '1'
        observer.observe(el)
      }
    })
  })
  mutationObserver.observe(document.body, { childList: true, subtree: true })

  // ─── Scroll-driven Apple-style effects ──────────────────
  scrollFx.mount()
})
</script>

<template>
  <div class="app">
    <NavBar :lang="lang" @reset="handleReset" @toggle-lang="toggleLang" />

    <main class="main" :class="{ 'main-pro': isPro }">
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

      <!-- Pro Banner (hidden for PRO users) -->
      <ProBanner v-if="!isPro" />

      <!-- Marketing Sections (hidden when in downloading/AI views) -->
      <template v-if="view === 'hero' || view === 'preview' || view === 'complete'">
        <FeatureSection />
        <HowToSection />
        <FAQSection />
        <PlatformSection />
      </template>
    </main>

    <!-- Payment Success / Cancel Views -->
    <div v-if="paymentView === 'success'" class="container">
      <div class="payment-result success animate-in">
        <div class="payment-icon">&#10003;</div>
        <h2 class="payment-title">{{ t.payment_success_title }}</h2>
        <p class="payment-desc">{{ t.payment_success_desc }}</p>
        <button class="payment-btn" @click="paymentView = null">{{ t.nav_title }} &#8594;</button>
      </div>
    </div>
    <div v-if="paymentView === 'cancel'" class="container">
      <div class="payment-result cancel animate-in">
        <div class="payment-icon payment-icon-cancel">&#10007;</div>
        <h2 class="payment-title">{{ t.payment_cancel_title }}</h2>
        <p class="payment-desc">{{ t.payment_cancel_desc }}</p>
        <button class="payment-btn" @click="paymentView = null">{{ t.payment_try_again }}</button>
      </div>
    </div>

    <!-- Auth Modal -->
    <AuthModal
      v-if="showAuthModal"
      @close="showAuthModal = false"
      @authenticated="handleAuthenticated"
    />

    <!-- Footer -->
    <AppFooter />
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

/* Payment Result */
.payment-result {
  text-align: center; padding: 64px 32px; max-width: 520px; margin: 40px auto;
  border-radius: 20px; background: #fff; border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 2px 24px rgba(0,0,0,0.04);
}
.payment-icon {
  width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; color: #fff; background: #34c759;
}
.payment-icon-cancel { background: #ff9500; }
.payment-title { font-size: 24px; font-weight: 700; color: #1d1d1f; margin-bottom: 8px; }
.payment-desc { font-size: 15px; color: #86868b; margin-bottom: 24px; line-height: 1.5; }
.payment-btn {
  padding: 12px 28px; border: none; border-radius: 12px;
  background: #0071e3; color: #fff; font-family: inherit; font-size: 15px;
  font-weight: 600; cursor: pointer; transition: all 0.25s;
  box-shadow: 0 2px 12px rgba(0,113,227,0.25);
}
.payment-btn:hover { background: #0066cc; box-shadow: 0 6px 24px rgba(0,113,227,0.35); }
</style>
