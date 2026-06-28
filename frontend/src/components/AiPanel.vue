<script setup>
import { ref, inject, computed } from 'vue'
import SummaryCard from './SummaryCard.vue'
import MindMap from './MindMap.vue'
import QAChat from './QAChat.vue'
import SubtitleViewer from './SubtitleViewer.vue'

const t = inject('t')

const props = defineProps({
  url: String,
  videoTitle: String,
  subtitlesStatus: String,  // 'idle' | 'loading' | 'loaded' | 'unavailable' | 'error'
  subtitlesData: Object,
  subtitlesError: String,
})

const emit = defineEmits(['back', 'update:activeTab'])

const activeTab = ref('summary')

function setTab(tab) {
  activeTab.value = tab
  emit('update:activeTab', tab)
}
</script>

<template>
  <section class="section">
    <div class="container">
      <div class="ai-panel card glass reveal">
        <!-- Header -->
        <div class="ai-header">
          <button class="ai-back-btn glass" @click="$emit('back')">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
              <path d="M19 12H5m0 0l7 7m-7-7l7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ t.ai_back || '返回' }}
          </button>
          <div class="ai-header-info">
            <h2 class="ai-header-title">{{ t.ai_title || 'AI 视频分析' }}</h2>
            <p class="ai-video-name">{{ videoTitle }}</p>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="subtitlesStatus === 'loading'" class="ai-loading">
          <div class="ai-loading-spinner"></div>
          <p>{{ t.ai_loading_subtitles || '正在提取字幕...' }}</p>
        </div>

        <!-- Error state -->
        <div v-else-if="subtitlesStatus === 'error'" class="ai-message ai-message-error">
          <p>{{ subtitlesError || t.ai_subtitle_error || '字幕提取失败' }}</p>
          <button class="ai-retry-btn" @click="$emit('back')">{{ t.ai_go_back || '返回' }}</button>
        </div>

        <!-- No subtitles available -->
        <div v-else-if="subtitlesStatus === 'unavailable'" class="ai-message ai-message-empty">
          <svg viewBox="0 0 24 24" fill="none" width="44" height="44" opacity="0.2">
            <path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-4.5H9m6-3H9m7.5 12.75h-9A2.25 2.25 0 016.75 19.5V4.5A2.25 2.25 0 019 2.25h6.75a2.25 2.25 0 012.25 2.25v15a2.25 2.25 0 01-2.25 2.25z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <h3>{{ t.ai_no_subtitles_title || '该视频暂无字幕' }}</h3>
          <p>{{ t.ai_no_subtitles_desc || 'AI 分析功能需要视频字幕或自动生成的字幕才能工作。请尝试其他有字幕的视频。' }}</p>
          <button class="ai-retry-btn" @click="$emit('back')">{{ t.ai_go_back || '返回' }}</button>
        </div>

        <!-- Loaded state — tabs + content -->
        <template v-if="subtitlesStatus === 'loaded'">
          <!-- Metadata fallback notice -->
          <div v-if="subtitlesData?.source === 'metadata'" class="ai-metadata-notice">
            <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg>
            <span>{{ t.ai_metadata_notice || '该视频无字幕，AI 分析基于视频标题、简介和标签进行，结果可能不够精确。' }}</span>
          </div>
          <!-- Tab bar -->
          <div class="ai-tabs">
            <button
              class="ai-tab" :class="{ active: activeTab === 'summary' }"
              @click="setTab('summary')"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5z" clip-rule="evenodd"/></svg>
              {{ t.ai_tab_summary || 'AI 总结' }}
            </button>
            <button
              class="ai-tab" :class="{ active: activeTab === 'mindmap' }"
              @click="setTab('mindmap')"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path d="M11 3a1 1 0 10-2 0v3a1 1 0 102 0V3zM7 7a1 1 0 00-1 1v2a1 1 0 002 0V8a1 1 0 00-1-1zM5 13a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1zM13 11a1 1 0 10-2 0v6a1 1 0 102 0v-6zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z"/></svg>
              {{ t.ai_tab_mindmap || '思维导图' }}
            </button>
            <button
              class="ai-tab" :class="{ active: activeTab === 'chat' }"
              @click="setTab('chat')"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M10 2c-2.236 0-4.43.18-6.57.524C1.993 2.755 1 4.014 1 5.426v5.148c0 1.413.993 2.67 2.43 2.902.848.137 1.705.248 2.57.331v3.443a.75.75 0 001.28.53l3.58-3.579a.78.78 0 01.527-.224 41.202 41.202 0 005.183-.5c1.437-.232 2.43-1.49 2.43-2.903V5.426c0-1.413-.993-2.67-2.43-2.902A41.289 41.289 0 0010 2z" clip-rule="evenodd"/></svg>
              {{ t.ai_tab_chat || 'AI 问答' }}
            </button>
            <button
              class="ai-tab" :class="{ active: activeTab === 'subtitles' }"
              @click="setTab('subtitles')"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M4.25 2A2.25 2.25 0 002 4.25v11.5A2.25 2.25 0 004.25 18h11.5A2.25 2.25 0 0018 15.75V4.25A2.25 2.25 0 0015.75 2H4.25zm0 3.5a.75.75 0 01.75-.75h2a.75.75 0 010 1.5H5a.75.75 0 01-.75-.75zm0 3a.75.75 0 01.75-.75h4a.75.75 0 010 1.5H5a.75.75 0 01-.75-.75zm0 3a.75.75 0 01.75-.75h6a.75.75 0 010 1.5H5a.75.75 0 01-.75-.75zM13 5.75a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5h-1.5a.75.75 0 01-.75-.75zm.75 2.25a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5z" clip-rule="evenodd"/></svg>
              {{ t.ai_tab_subtitles || '字幕文本' }}
            </button>
          </div>

          <!-- Tab content -->
          <div class="ai-tab-content">
            <SummaryCard
              v-if="activeTab === 'summary'"
              :url="url"
              :subtitles-data="subtitlesData"
            />
            <MindMap
              v-else-if="activeTab === 'mindmap'"
              :url="url"
            />
            <QAChat
              v-else-if="activeTab === 'chat'"
              :url="url"
            />
            <SubtitleViewer
              v-else-if="activeTab === 'subtitles'"
              :subtitles-data="subtitlesData"
            />
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ai-panel { padding: 36px 44px; }

.ai-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.ai-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 16px;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.4);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: var(--color-accent);
  font-family: var(--font-system);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}
.ai-back-btn:hover {
  background: rgba(255,255,255,0.7);
  border-color: var(--color-accent);
  transform: translateX(-2px);
}

.ai-header-info {
  flex: 1;
  min-width: 0;
}
.ai-header-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.022em;
  color: var(--color-text);
  margin-bottom: 4px;
}
.ai-video-name {
  font-size: 14px;
  color: var(--color-text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Loading */
.ai-loading {
  text-align: center;
  padding: 64px 0;
  color: var(--color-text-sub);
}
.ai-loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Metadata fallback notice */
.ai-metadata-notice {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; margin-bottom: 16px;
  background: rgba(255, 248, 225, 0.6);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 224, 130, 0.5);
  border-radius: var(--radius-sm);
  font-size: 13px; color: #8d6e00;
}

/* Messages */
.ai-message {
  text-align: center;
  padding: 56px 24px;
}
.ai-message h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}
.ai-message p {
  font-size: 15px;
  color: var(--color-text-sub);
  margin-bottom: 24px;
}
.ai-retry-btn {
  display: inline-flex;
  padding: 10px 22px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: var(--radius-full);
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: var(--color-accent);
  font-family: var(--font-system);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}
.ai-retry-btn:hover {
  background: rgba(255,255,255,0.8);
  border-color: var(--color-accent);
}

/* Tabs */
.ai-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(0,0,0,0.03);
  border-radius: var(--radius-sm);
  margin-bottom: 24px;
  overflow-x: auto;
}
.ai-tab {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--color-text-sub);
  font-family: var(--font-system);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  white-space: nowrap;
}
.ai-tab.active {
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
}
.ai-tab:hover:not(.active) {
  color: var(--color-text);
  background: rgba(255,255,255,0.4);
}

@media (max-width: 600px) {
  .ai-panel { padding: 24px 20px; }
  .ai-header { flex-direction: column; }
  .ai-tab { font-size: 12px; padding: 8px 6px; gap: 3px; }
  .ai-tab svg { width: 14px; height: 14px; }
}
</style>
