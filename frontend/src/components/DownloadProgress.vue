<script setup>
import { computed, inject } from 'vue'

const t = inject('t')
const props = defineProps({ download: Object, filename: String, apiBase: String })

const isComplete = computed(() => props.download.status === 'finished')
const isProcessing = computed(() => props.download.status === 'processing')
const isDownloading = computed(() => props.download.status === 'downloading')

const etaDisplay = computed(() => {
  if (!props.download.eta) return ''
  const eta = props.download.eta
  if (eta < 60) return `${eta}s`
  const m = Math.floor(eta / 60), s = eta % 60
  return `${m}m ${s}s`
})
</script>

<template>
  <section class="section">
    <div class="container">
      <div class="progress-card card animate-in" :class="{ 'progress-complete': isComplete }">
        <div class="progress-header">
          <div class="progress-status">
            <template v-if="isDownloading">
              <svg class="status-icon spin" viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M3 12a9 9 0 119 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              <span>{{ t.progress_downloading }}</span>
            </template>
            <template v-else-if="isProcessing">
              <svg class="status-icon pulse" viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>{{ download.message || t.progress_processing }}</span>
            </template>
            <template v-else-if="isComplete">
              <svg class="status-icon success-icon" viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd"/></svg>
              <span>{{ t.progress_complete }}</span>
            </template>
          </div>
          <span v-if="isDownloading" class="progress-percent">{{ download.percent }}%</span>
        </div>

        <div class="progress-track">
          <div class="progress-fill" :class="{ 'indeterminate': isProcessing }" :style="{ width: isComplete ? '100%' : download.percent + '%' }"></div>
        </div>

        <div v-if="isDownloading" class="progress-stats">
          <div class="stat"><span class="stat-label">{{ t.progress_downloaded }}</span><span class="stat-value">{{ download.downloadedStr }} / {{ download.totalStr }}</span></div>
          <div v-if="download.speedStr" class="stat"><span class="stat-label">{{ t.progress_speed }}</span><span class="stat-value">{{ download.speedStr }}</span></div>
          <div v-if="etaDisplay" class="stat"><span class="stat-label">{{ t.progress_eta }}</span><span class="stat-value">{{ etaDisplay }}</span></div>
        </div>

        <div v-if="isComplete" class="complete-info">
          <p class="filename-display">{{ filename }}</p>
          <a :href="`${apiBase}/api/downloads/${filename}`" class="save-link" download>
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {{ t.progress_save_file }}
          </a>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.progress-card { padding: 24px 40px; }
.progress-complete { border: 1px solid #34c759; }
.progress-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.progress-status { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: #1d1d1f; }
.status-icon { flex-shrink: 0; color: #0071e3; }
.success-icon { color: #34c759; }
.spin { animation: spin 1.2s linear infinite; }
.pulse { animation: pulse 1.5s ease-in-out infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.progress-percent { font-size: 24px; font-weight: 700; color: #0071e3; letter-spacing: -0.022em; }
.progress-track { height: 6px; background: #e8e8ed; border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
.progress-fill { height: 100%; background: #0071e3; border-radius: 3px; transition: width 0.3s cubic-bezier(0.25,0.1,0.25,1); }
.progress-fill.indeterminate { width: 40% !important; animation: indeterminate 1.5s ease-in-out infinite; }
@keyframes indeterminate { 0% { transform: translateX(-100%); } 100% { transform: translateX(350%); } }
.progress-stats { display: flex; gap: 40px; }
.stat { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 11px; font-weight: 600; color: #86868b; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 14px; color: #1d1d1f; font-variant-numeric: tabular-nums; }
.complete-info { display: flex; align-items: center; justify-content: space-between; padding-top: 16px; border-top: 1px solid #e8e8ed; }
.filename-display { font-size: 14px; color: #6e6e73; word-break: break-all; margin-right: 16px; }
.save-link { flex-shrink: 0; display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: #34c759; color: #fff; border-radius: 9999px; font-size: 14px; font-weight: 600; text-decoration: none; transition: opacity 0.2s; }
.save-link:hover { opacity: 0.85; color: #fff; }
</style>
