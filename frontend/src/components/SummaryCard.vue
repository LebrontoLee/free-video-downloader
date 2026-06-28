<script setup>
import { ref, inject, nextTick } from 'vue'
import { marked } from 'marked'

const t = inject('t')
const API_BASE = 'http://localhost:8000'

const props = defineProps({ url: String, subtitlesData: Object })

const status = ref('idle')
const summaryText = ref('')
const errorMsg = ref('')
const scroller = ref(null)

let es = null

// ── Typewriter (100% DOM — zero Vue reactivity during streaming) ──────
let twBuffer = ''
let twTimer = null
let twFull = ''

function showCursorDOM(visible) {
  const el = document.querySelector('.sc-cursor')
  if (el) el.style.display = visible ? 'inline' : 'none'
}
function showWaitingDOM(visible) {
  const el = document.querySelector('.sc-waiting')
  if (el) el.style.display = visible ? '' : 'none'
}

function twTypeNext() {
  if (twBuffer.length === 0) {
    twTimer = null
    return
  }
  const el = document.querySelector('.sc-streaming-text')
  if (el) el.textContent += twBuffer[0]
  twFull += twBuffer[0]
  twBuffer = twBuffer.slice(1)
  twTimer = setTimeout(twTypeNext, 80)
}

function twEnqueue(text) {
  if (!text) return
  twBuffer += text
  if (!twTimer) {
    showWaitingDOM(false)
    showCursorDOM(true)
    twTypeNext()
  }
}

function twSkip() {
  if (twTimer) { clearTimeout(twTimer); twTimer = null }
  if (twBuffer) {
    const el = document.querySelector('.sc-streaming-text')
    if (el) el.textContent += twBuffer
  }
  twFull += twBuffer
  twBuffer = ''
  showCursorDOM(false)
}

function twReset() {
  if (twTimer) { clearTimeout(twTimer); twTimer = null }
  twBuffer = ''
  twFull = ''
  const el = document.querySelector('.sc-streaming-text')
  if (el) el.textContent = ''
  showCursorDOM(false)
  showWaitingDOM(true)
}

function twGetFull() { return twFull + twBuffer }

// ── SSE summary generation ──────────────────────────────────────────────
async function generateSummary() {
  if (es) { es.close(); es = null }
  twReset()
  status.value = 'generating'
  summaryText.value = ''
  errorMsg.value = ''

  // Pre-cache subtitles
  try {
    await fetch(`${API_BASE}/api/ai/subtitles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: props.url }),
    })
  } catch { /* ignore */ }

  const qs = `url=${encodeURIComponent(props.url)}&style=detailed`
  es = new EventSource(`${API_BASE}/api/ai/summary?${qs}`)

  es.addEventListener('token', async (e) => {
    const text = JSON.parse(e.data).text || ''
    twEnqueue(text)
    await nextTick()
    if (scroller.value) {
      scroller.value.scrollTop = scroller.value.scrollHeight
    }
  })

  es.addEventListener('done', (e) => {
    twSkip()
    const data = JSON.parse(e.data)
    summaryText.value = data.summary || twGetFull()
    status.value = 'done'
    es.close()
    es = null
  })

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) {
      showCursorDOM(false)
      es.close(); es = null
      if (!twGetFull()) {
        errorMsg.value = 'Connection failed'
        status.value = 'error'
      } else {
        twSkip()
        summaryText.value = twGetFull()
        status.value = 'done'
      }
    }
  }
}

function stopGeneration() {
  if (es) { es.close(); es = null }
  twSkip()
  summaryText.value = twGetFull() || summaryText.value
  status.value = 'done'
}

function copySummary() {
  const text = summaryText.value || twGetFull() || ''
  navigator.clipboard.writeText(text).catch(() => {})
}

function retry() { generateSummary() }

function renderMarkdown(text) {
  if (!text) return ''
  // Parse with marked, producing clean HTML
  return marked.parse(text, {
    breaks: true,
    gfm: true,
  })
}
</script>

<template>
  <div class="summary-card">
    <!-- Idle -->
    <div v-if="status === 'idle'" class="sc-idle">
      <p class="sc-desc">{{ t.ai_summary_desc || '基于视频字幕生成 AI 智能总结，快速了解视频核心内容。' }}</p>
      <button class="sc-generate-btn" @click="generateSummary">
        <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        {{ t.ai_generate_summary || '生成 AI 总结' }}
      </button>
    </div>

    <!-- Generating -->
    <div v-else-if="status === 'generating'" class="sc-generating">
      <div ref="scroller" class="sc-streaming-content">
        <pre class="sc-streaming-text"></pre><span class="sc-cursor" style="display:none">|</span>
        <span class="sc-waiting">⏳ {{ t.ai_generating || '正在生成总结...' }}</span>
      </div>
      <button class="sc-stop-btn" @click="stopGeneration">{{ t.ai_stop || '停止生成' }}</button>
    </div>

    <!-- Done -->
    <div v-else-if="status === 'done'" class="sc-done">
      <div class="sc-content md-apple" v-html="renderMarkdown(summaryText)"></div>
      <div class="sc-actions">
        <button class="sc-action-btn" @click="copySummary">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M15.666 3.888a2.25 2.25 0 00-1.837-.795H8.213c-1.44 0-2.384 0-3.009.248a3 3 0 00-1.456 1.456c-.248.625-.248 1.569-.248 3.009v3.179c0 .766 0 1.381.058 1.879.207 1.773 1.841 3.106 3.692 3.106h6.5c1.44 0 2.384 0 3.009-.248a3 3 0 001.456-1.456c.248-.625.248-1.569.248-3.009v-3.179c0-.766 0-1.381-.058-1.879a2.25 2.25 0 00-.795-1.311z" fill="currentColor"/></svg>
          {{ t.ai_copy || '复制' }}
        </button>
        <button class="sc-action-btn sc-regenerate" @click="retry">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          {{ t.ai_regenerate || '重新生成' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="status === 'error'" class="sc-error">
      <p>{{ errorMsg || t.ai_summary_error || '生成总结失败' }}</p>
      <button class="sc-action-btn sc-regenerate" @click="retry">{{ t.ai_retry || '重试' }}</button>
    </div>
  </div>
</template>

<style scoped>
.summary-card { min-height: 200px; }
.sc-idle { text-align: center; padding: 40px 20px; }
.sc-desc { font-size: 15px; color: var(--color-text-sub); margin-bottom: 24px; line-height: 1.6; }
.sc-generate-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 28px; border: none; border-radius: var(--radius-md);
  background: linear-gradient(135deg, #667eea, #764ba2); color: #fff;
  font-family: var(--font-system); font-size: 16px; font-weight: 600;
  cursor: pointer; transition: all var(--duration-fast);
}
.sc-generate-btn:hover { transform: scale(1.03); box-shadow: 0 8px 30px rgba(102,126,234,0.3); }

.sc-generating { position: relative; }
.sc-streaming-content {
  padding: 20px; background: var(--color-bg); border-radius: var(--radius-sm);
  font-size: 15px; line-height: 1.7; min-height: 100px; max-height: 50vh; overflow-y: auto;
}
.sc-streaming-text { white-space: pre-wrap; word-break: break-word; margin: 0; font-family: var(--font-system); display: inline; }
.sc-cursor {
  color: var(--color-accent); font-weight: 300;
  animation: typewriterBlink 0.7s infinite;
}
@keyframes typewriterBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.sc-waiting { color: var(--color-text-sub); animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.sc-stop-btn {
  display: block; margin: 12px auto 0; padding: 8px 20px;
  border: 1px solid var(--color-border); border-radius: var(--radius-full);
  background: var(--color-surface); color: var(--color-text-sub);
  font-family: var(--font-system); font-size: 13px; cursor: pointer;
}
.sc-stop-btn:hover { border-color: var(--color-error); color: var(--color-error); }

/* ── Apple-style Markdown Content ───────────────────────────────────── */
.md-apple {
  padding: 24px 28px;
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text);
}
/* Headings */
.md-apple :deep(h1) {
  font-size: 24px; font-weight: 700; letter-spacing: -0.022em;
  color: var(--color-text); margin: 28px 0 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-light);
}
.md-apple :deep(h1:first-child) { margin-top: 0; }
.md-apple :deep(h2) {
  font-size: 20px; font-weight: 600; letter-spacing: -0.021em;
  color: var(--color-text); margin: 24px 0 10px;
}
.md-apple :deep(h2:first-child) { margin-top: 0; }
.md-apple :deep(h3) {
  font-size: 17px; font-weight: 600; letter-spacing: -0.02em;
  color: var(--color-text); margin: 20px 0 8px;
}
.md-apple :deep(h3:first-child) { margin-top: 0; }
.md-apple :deep(h4) {
  font-size: 15px; font-weight: 600;
  color: var(--color-text); margin: 16px 0 6px;
}
.md-apple :deep(h4:first-child) { margin-top: 0; }

/* Paragraphs */
.md-apple :deep(p) {
  margin: 8px 0;
  color: var(--color-text);
}
.md-apple :deep(p:first-child) { margin-top: 0; }
.md-apple :deep(p:last-child) { margin-bottom: 0; }

/* Bold & italic */
.md-apple :deep(strong) {
  font-weight: 600;
  color: var(--color-text);
}
.md-apple :deep(em) {
  font-style: italic;
}

/* Lists */
.md-apple :deep(ul),
.md-apple :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}
.md-apple :deep(li) {
  margin: 4px 0;
  padding-left: 4px;
  color: var(--color-text);
}
.md-apple :deep(li::marker) {
  color: var(--color-accent);
}

/* Code */
.md-apple :deep(code) {
  font-family: var(--font-mono);
  font-size: 13px;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  color: #d63384;
}
.md-apple :deep(pre) {
  background: #1d1d1f;
  color: #f5f5f7;
  padding: 16px 20px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.6;
}
.md-apple :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}

/* Blockquote */
.md-apple :deep(blockquote) {
  margin: 12px 0;
  padding: 12px 16px;
  border-left: 3px solid var(--color-accent);
  background: rgba(0, 113, 227, 0.04);
  border-radius: 0 8px 8px 0;
  color: var(--color-text-sub);
}
.md-apple :deep(blockquote p) {
  color: inherit;
  margin: 4px 0;
}

/* Horizontal rule */
.md-apple :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border-light);
  margin: 20px 0;
}

/* Links */
.md-apple :deep(a) {
  color: var(--color-accent);
  text-decoration: none;
}
.md-apple :deep(a:hover) {
  text-decoration: underline;
}

/* Tables */
.md-apple :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}
.md-apple :deep(th) {
  text-align: left;
  padding: 10px 14px;
  background: var(--color-bg);
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  color: var(--color-text);
}
.md-apple :deep(td) {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border-light);
  color: var(--color-text);
}
.md-apple :deep(tr:last-child td) {
  border-bottom: none;
}

/* Images */
.md-apple :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-sm);
  margin: 12px 0;
}

/* ── Actions ─────────────────────────────────────────────────────────── */
.sc-actions { display: flex; gap: 12px; margin-top: 16px; justify-content: center; }
.sc-action-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border: 1px solid var(--color-border); border-radius: var(--radius-full);
  background: var(--color-surface); color: var(--color-text);
  font-family: var(--font-system); font-size: 14px; font-weight: 500; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.sc-action-btn:hover { background: var(--color-bg); border-color: var(--color-accent); color: var(--color-accent); }
.sc-regenerate { color: var(--color-accent); }
.sc-error { text-align: center; padding: 40px 20px; }
.sc-error p { font-size: 14px; color: var(--color-error); margin-bottom: 16px; }
</style>
