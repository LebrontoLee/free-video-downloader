<script setup>
import { ref, computed, inject } from 'vue'

const t = inject('t')
const props = defineProps({ video: Object, selectedFormat: String, isDownloading: Boolean })
defineEmits(['select-format', 'download', 'reset', 'ai-features'])

const thumbnailFailed = ref(false)

const thumbnailProxyUrl = computed(() => {
  if (!props.video?.thumbnail) return ''
  return `/api/thumbnail?url=${encodeURIComponent(props.video.thumbnail)}`
})

function onThumbnailError() { thumbnailFailed.value = true }
</script>

<template>
  <section class="section">
    <div class="container">
      <div class="preview-card card animate-in">
        <div class="preview-header">
          <div class="thumbnail-wrap">
            <img v-if="video.thumbnail && !thumbnailFailed" :src="thumbnailProxyUrl" :alt="video.title" class="thumbnail" referrerpolicy="no-referrer" @error="onThumbnailError" />
            <div v-if="!video.thumbnail || thumbnailFailed" class="thumbnail-placeholder">
              <svg viewBox="0 0 24 24" fill="currentColor" width="36" height="36" opacity="0.3"><path d="M4.5 4.5a3 3 0 00-3 3v9a3 3 0 003 3h8.25a3 3 0 003-3v-9a3 3 0 00-3-3H4.5zM19.94 18.75l-2.69-2.69V7.94l2.69-2.69c.944-.945 2.56-.276 2.56 1.06v11.38c0 1.336-1.616 2.005-2.56 1.06z"/></svg>
            </div>
          </div>
          <div class="preview-info">
            <h2 class="video-title">{{ video.title }}</h2>
            <div class="video-meta">
              <span v-if="video.duration_string" class="meta-item">
                <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clip-rule="evenodd"/></svg>
                {{ video.duration_string }}
              </span>
              <span v-if="video.uploader" class="meta-item">
                <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z"/></svg>
                {{ video.uploader }}
              </span>
              <span class="meta-item meta-platform">{{ video.extractor }}</span>
            </div>
          </div>
        </div>

        <div class="format-section">
          <h3 class="format-label">{{ t.preview_quality }}</h3>
          <div class="format-grid">
            <button v-for="fmt in video.formats" :key="fmt.format_id"
              class="format-chip"
              :class="{ 'format-active': selectedFormat === fmt.format_id, 'format-audio': fmt.note === 'audio' }"
              :disabled="isDownloading"
              @click="$emit('select-format', fmt.format_id)">
              <span class="fmt-resolution">{{ fmt.height ? fmt.height + 'p' : 'MP3' }}</span>
              <span class="fmt-detail">{{ fmt.ext }} · {{ fmt.filesize_str }}</span>
              <span v-if="fmt.note === 'merge'" class="fmt-badge">{{ t.merge_badge }}</span>
            </button>
          </div>
        </div>

        <div class="preview-actions">
          <button class="download-btn" :disabled="isDownloading" @click="$emit('download')">
            <svg v-if="!isDownloading" viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span v-else class="spinner-sm"></span>
            {{ isDownloading ? t.preview_downloading : t.preview_download }}
          </button>
          <button class="ai-btn" @click="$emit('ai-features')">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {{ t.ai_analyze }}
          </button>
          <button class="reset-btn" @click="$emit('reset')">{{ t.preview_new_url }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.preview-card { padding: 40px; }
.preview-header { display: flex; gap: 24px; margin-bottom: 24px; }
.thumbnail-wrap { flex-shrink: 0; width: 200px; height: 112px; border-radius: 12px; overflow: hidden; background: #f0f0f0; }
.thumbnail { width: 100%; height: 100%; object-fit: cover; }
.thumbnail-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #e8e8ed, #d2d2d7); color: #6e6e73; }
.preview-info { flex: 1; min-width: 0; }
.video-title { font-size: 19px; font-weight: 600; letter-spacing: -0.022em; line-height: 1.3; color: #1d1d1f; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.video-meta { display: flex; flex-wrap: wrap; gap: 12px; }
.meta-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #6e6e73; }
.meta-platform { text-transform: capitalize; font-weight: 500; color: #86868b; background: #f5f5f7; padding: 2px 8px; border-radius: 4px; }
.format-section { border-top: 1px solid #e8e8ed; padding-top: 24px; }
.format-label { font-size: 13px; font-weight: 600; color: #6e6e73; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; }
.format-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.format-chip { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 14px 12px; border: 2px solid #e8e8ed; border-radius: 12px; background: #fff; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.format-chip:hover:not(:disabled) { border-color: #0071e3; background: rgba(0,113,227,0.03); }
.format-chip:disabled { opacity: 0.5; cursor: not-allowed; }
.format-active { border-color: #0071e3; background: rgba(0,113,227,0.06); box-shadow: 0 0 0 1px #0071e3; }
.fmt-resolution { font-size: 20px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.022em; }
.format-audio .fmt-resolution { font-size: 17px; }
.fmt-detail { font-size: 12px; color: #6e6e73; }
.fmt-badge { font-size: 10px; font-weight: 500; color: #86868b; background: #f5f5f7; padding: 1px 6px; border-radius: 4px; margin-top: 2px; }
.preview-actions { display: flex; gap: 16px; margin-top: 24px; padding-top: 24px; border-top: 1px solid #e8e8ed; }
.download-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px 24px; border: none; border-radius: 18px; background: #0071e3; color: #fff; font-family: inherit; font-size: 17px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.download-btn:hover:not(:disabled) { background: #0066cc; }
.download-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.ai-btn { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 14px 20px; border: 1px solid #d2d2d7; border-radius: 18px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; font-family: inherit; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.ai-btn:hover { transform: scale(1.03); box-shadow: 0 4px 20px rgba(102,126,234,0.35); }
.reset-btn { padding: 14px 20px; border: 1px solid #d2d2d7; border-radius: 18px; background: #fff; color: #0071e3; font-family: inherit; font-size: 15px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.reset-btn:hover { background: #f5f5f7; border-color: #0071e3; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .preview-header { flex-direction: column; }
  .thumbnail-wrap { width: 100%; height: auto; aspect-ratio: 16/9; }
  .format-grid { grid-template-columns: repeat(2, 1fr); }
  .preview-actions { flex-direction: column; }
}
</style>
