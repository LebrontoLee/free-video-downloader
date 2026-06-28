<script setup>
import { ref, inject, nextTick } from 'vue'

const t = inject('t')
const API_BASE = 'http://localhost:8000'

const props = defineProps({
  url: String,
})

const messages = ref([])
const inputText = ref('')
const isStreaming = ref(false)
const sessionId = ref(null)
const errorMsg = ref('')
const abortController = ref(null)
const messagesContainer = ref(null)

// ── Typewriter (100% DOM — zero Vue reactivity during streaming) ──────
let twBuffer = ''
let twTimer = null
let twFull = ''

function showCursorDOM(visible) {
  const el = document.querySelector('.qa-cursor')
  if (el) el.style.display = visible ? 'inline' : 'none'
}

function twTypeNext() {
  if (twBuffer.length === 0) {
    twTimer = null
    return
  }
  const el = document.querySelector('.qa-streaming .tw-text')
  if (el) el.textContent += twBuffer[0]
  twFull += twBuffer[0]
  twBuffer = twBuffer.slice(1)
  twTimer = setTimeout(twTypeNext, 80)
}

function twEnqueue(text) {
  if (!text) return
  twBuffer += text
  if (!twTimer) {
    showCursorDOM(true)
    twTypeNext()
  }
}

function twSkip() {
  if (twTimer) { clearTimeout(twTimer); twTimer = null }
  if (twBuffer) {
    const el = document.querySelector('.qa-streaming .tw-text')
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
  const el = document.querySelector('.qa-streaming .tw-text')
  if (el) el.textContent = ''
  showCursorDOM(false)
}

function twGetFull() { return twFull + twBuffer }

function scrollToBottom() {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 50)
}

async function sendMessage() {
  const question = inputText.value.trim()
  if (!question || isStreaming.value) return

  inputText.value = ''
  errorMsg.value = ''

  messages.value.push({ id: Date.now(), role: 'user', content: question })
  scrollToBottom()

  isStreaming.value = true
  twReset()

  if (abortController.value) {
    abortController.value.abort()
  }
  const qs = `url=${encodeURIComponent(props.url)}&question=${encodeURIComponent(question)}&session_id=${sessionId.value || ''}`
  const es = new EventSource(`${API_BASE}/api/ai/chat/stream?${qs}`)
  abortController.value = { abort: () => es.close() }

  es.addEventListener('token', (e) => {
    const data = JSON.parse(e.data)
    twEnqueue(data.text || '')
  })

  es.addEventListener('done', (e) => {
    twSkip()
    const data = JSON.parse(e.data)
    const fullAnswer = data.full_answer || twGetFull()
    messages.value.push({ id: Date.now(), role: 'assistant', content: fullAnswer })
    if (data.session_id) sessionId.value = data.session_id
    isStreaming.value = false
    es.close()
    scrollToBottom()
  })

  es.addEventListener('error', () => {
    if (es.readyState === EventSource.CLOSED) {
      showCursorDOM(false)
      if (twGetFull()) {
        twSkip()
        messages.value.push({ id: Date.now(), role: 'assistant', content: twGetFull() })
      } else {
        errorMsg.value = 'Connection failed'
      }
      isStreaming.value = false
      es.close()
    }
  })
}

function stopStreaming() {
  if (abortController.value) {
    abortController.value.abort()
  }
  if (twGetFull().trim()) {
    twSkip()
    messages.value.push({ id: Date.now(), role: 'assistant', content: twGetFull() })
  }
  isStreaming.value = false
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function clearChat() {
  messages.value = []
  sessionId.value = null
  errorMsg.value = ''
  twReset()
}
</script>

<template>
  <div class="qa-chat">
    <div ref="messagesContainer" class="qa-messages">
      <div v-if="messages.length === 0 && !isStreaming" class="qa-empty">
        <svg viewBox="0 0 24 24" fill="none" width="36" height="36" opacity="0.2">
          <path d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 01-.923 1.785A5.969 5.969 0 006 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
        <p>{{ t.ai_chat_placeholder || '针对视频内容提问，AI 将基于字幕为你解答。' }}</p>
      </div>

      <div v-for="msg in messages" :key="msg.id" class="qa-message" :class="'qa-' + msg.role">
        <div class="qa-bubble">{{ msg.content }}</div>
      </div>

      <!-- Streaming bubble — direct DOM writes to inner <span> -->
      <div v-if="isStreaming" class="qa-message qa-assistant">
        <div class="qa-bubble qa-streaming">
          <span class="tw-text"></span><span class="qa-cursor" style="display:none">|</span>
        </div>
      </div>

      <div v-if="!isStreaming && errorMsg" class="qa-error">
        <span>{{ errorMsg }}</span>
      </div>
    </div>

    <div class="qa-input-area">
      <input
        v-model="inputText"
        type="text"
        class="qa-input"
        :placeholder="t.ai_chat_input || '针对视频内容提问...'"
        :disabled="isStreaming"
        @keydown="handleKeydown"
      />
      <button
        v-if="!isStreaming"
        class="qa-send-btn"
        :disabled="!inputText.trim()"
        @click="sendMessage"
      >
        <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
          <path d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <button
        v-else
        class="qa-stop-btn"
        @click="stopStreaming"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
          <rect x="6" y="6" width="12" height="12" rx="2"/>
        </svg>
      </button>
      <button
        v-if="messages.length > 0 && !isStreaming"
        class="qa-clear-btn"
        :title="t.ai_clear_chat || '清除对话'"
        @click="clearChat"
      >
        <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
          <path d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.qa-chat { display: flex; flex-direction: column; height: 520px; }

.qa-messages {
  flex: 1; overflow-y: auto; padding: 8px 0;
  display: flex; flex-direction: column; gap: 12px;
}
.qa-messages::-webkit-scrollbar { width: 4px; }
.qa-messages::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 2px; }

.qa-empty { text-align: center; padding: 60px 20px; color: var(--color-text-sub); }
.qa-empty p { font-size: 14px; margin-top: 12px; line-height: 1.6; }

.qa-message { display: flex; max-width: 85%; }
.qa-user { align-self: flex-end; }
.qa-assistant { align-self: flex-start; }

.qa-bubble {
  padding: 10px 16px; border-radius: 16px; font-size: 14px; line-height: 1.55;
  word-break: break-word;
}
.qa-user .qa-bubble {
  background: var(--color-accent); color: #fff;
  border-bottom-right-radius: 4px;
}
.qa-assistant .qa-bubble {
  background: var(--color-bg); color: var(--color-text);
  border-bottom-left-radius: 4px;
}
.qa-streaming { position: relative; white-space: pre-wrap; }
.qa-cursor {
  animation: typewriterBlink 0.8s infinite; color: var(--color-accent); font-weight: 300;
  margin-left: 1px;
}
@keyframes typewriterBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.qa-error {
  align-self: center; padding: 8px 16px;
  background: #fff2f0; border: 1px solid #ffccc7; border-radius: var(--radius-sm);
  font-size: 13px; color: var(--color-error);
}

.qa-input-area {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 0 0; border-top: 1px solid var(--color-border-light);
  margin-top: 12px;
}
.qa-input {
  flex: 1; padding: 10px 16px; border: 1px solid var(--color-border); border-radius: var(--radius-full);
  font-family: var(--font-system); font-size: 14px; color: var(--color-text);
  outline: none; transition: border-color var(--duration-fast);
}
.qa-input:focus { border-color: var(--color-accent); box-shadow: var(--shadow-glow); }
.qa-input::placeholder { color: var(--color-text-tertiary); }
.qa-input:disabled { opacity: 0.5; }

.qa-send-btn {
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border: none; border-radius: 50%;
  background: var(--color-accent); color: #fff; cursor: pointer;
  transition: all var(--duration-fast);
  flex-shrink: 0;
}
.qa-send-btn:hover:not(:disabled) { background: var(--color-accent-hover); }
.qa-send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.qa-stop-btn {
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border: none; border-radius: 50%;
  background: var(--color-error); color: #fff; cursor: pointer;
  flex-shrink: 0;
}

.qa-clear-btn {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: 1px solid var(--color-border);
  border-radius: 50%; background: var(--color-surface); color: var(--color-text-sub);
  cursor: pointer; transition: all var(--duration-fast);
  flex-shrink: 0;
}
.qa-clear-btn:hover { background: var(--color-bg); color: var(--color-error); }
</style>
