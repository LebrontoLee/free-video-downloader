<script setup>
import { ref, inject, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const t = inject('t')
const API_BASE = 'http://localhost:8000'

const props = defineProps({ url: String })

const status = ref('idle')
const treeData = ref(null)
const errorMsg = ref('')
const markmapMd = ref('')

// ─── DOM refs ───────────────────────────────────────────────────────────────
const mmContainer = ref(null)
const mmSvgRef = ref(null)
let markmapInstance = null
const isFullscreen = ref(false)

// ─── JSON Tree → Markdown ───────────────────────────────────────────────────
function treeToMarkdown(node, depth = 0) {
  if (!node || !node.label) return ''
  const prefix = '#'.repeat(Math.min(depth + 1, 6))
  let md = `${prefix} ${node.label.trim()}\n`
  if (node.children && node.children.length > 0) {
    for (const child of node.children) {
      md += treeToMarkdown(child, depth + 1)
    }
  }
  return md
}

// ─── Render mind map ────────────────────────────────────────────────────────
function renderMindmap(md) {
  if (!mmSvgRef.value) {
    console.warn('[MindMap] SVG ref not found, will retry after nextTick')
    return false
  }
  try {
    // Clear previous
    mmSvgRef.value.innerHTML = ''

    const transformer = new Transformer()
    const { root } = transformer.transform(md)

    markmapInstance = Markmap.create(
      mmSvgRef.value,
      {
        autoFit: true,
        colorFreezeLevel: 2,
        duration: 300,
        maxWidth: 260,
      },
      root
    )
    return true
  } catch (e) {
    console.error('[MindMap] render failed:', e)
    return false
  }
}

// ─── Actions ────────────────────────────────────────────────────────────────
async function generateMindMap() {
  status.value = 'loading'
  errorMsg.value = ''
  try {
    const res = await fetch(`${API_BASE}/api/ai/mindmap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: props.url, source: 'summary' }),
    })
    const data = await res.json()
    if (!res.ok || !data.success) throw new Error(data.detail || 'Failed')

    treeData.value = data.data
    markmapMd.value = treeToMarkdown(data.data.root)
    // Set status FIRST so Vue renders the SVG element into the DOM
    status.value = 'loaded'
    await nextTick()
    // Render with retry in case ref isn't attached yet
    if (!renderMindmap(markmapMd.value)) {
      await nextTick()
      renderMindmap(markmapMd.value)
    }
  } catch (err) {
    errorMsg.value = err.message || 'Network error'
    status.value = 'error'
  }
}

function retry() {
  generateMindMap()
}

// ─── Zoom controls ──────────────────────────────────────────────────────────
function zoomIn() {
  if (markmapInstance) markmapInstance.rescale(1.25)
}
function zoomOut() {
  if (markmapInstance) markmapInstance.rescale(0.8)
}
function fitView() {
  if (markmapInstance) markmapInstance.fit()
}

// ─── Fullscreen ─────────────────────────────────────────────────────────────
function toggleFullscreen() {
  if (!mmContainer.value) return

  if (!isFullscreen.value) {
    const el = mmContainer.value
    if (el.requestFullscreen) {
      el.requestFullscreen()
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    }
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!(
    document.fullscreenElement || document.webkitFullscreenElement
  )
  nextTick(() => {
    if (markmapInstance) markmapInstance.fit()
  })
}

// ─── Get safe filename ──────────────────────────────────────────────────────
function getSafeFilename() {
  // Try to get video title from tree root label
  const title = treeData.value?.root?.label || 'mindmap'
  return title.replace(/[\\/*?:"<>|]/g, '_').substring(0, 80)
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ─── Build exportable SVG (replace foreignObject with text) ──────────────────
function buildExportableSvg() {
  if (!mmSvgRef.value) return null

  const cloned = mmSvgRef.value.cloneNode(true)

  // Fix broken transforms
  cloned.querySelectorAll('[transform]').forEach((el) => {
    const t = el.getAttribute('transform')
    if (t && t.includes('NaN')) {
      el.setAttribute('transform', 'translate(0,0) scale(1)')
    }
  })

  // Replace foreignObject with native <text> for compatibility
  cloned.querySelectorAll('foreignObject').forEach((fo) => {
    const textContent = fo.textContent?.trim() || ''
    if (!textContent) {
      fo.remove()
      return
    }

    const x = parseFloat(fo.getAttribute('x')) || 0
    const y = parseFloat(fo.getAttribute('y')) || 0
    const h = parseFloat(fo.getAttribute('height')) || 20

    const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    textEl.setAttribute('x', String(x + 4))
    textEl.setAttribute('y', String(y + h / 2 + 5))
    textEl.setAttribute('font-size', '14')
    textEl.setAttribute('font-family', 'sans-serif')
    textEl.setAttribute('fill', '#333')
    textEl.setAttribute('dominant-baseline', 'middle')
    textEl.textContent = textContent

    fo.parentNode.replaceChild(textEl, fo)
  })

  return cloned
}

// ─── Serialize SVG with embedded styles ─────────────────────────────────────
function serializeSvg(svgEl) {
  const serializer = new XMLSerializer()
  let svgString = serializer.serializeToString(svgEl)

  // Ensure root <svg> element has xmlns attribute
  if (!/xmlns=/.test(svgString.match(/<svg[^>]*>/)?.[0] || '')) {
    svgString = svgString.replace(
      /<svg/,
      '<svg xmlns="http://www.w3.org/2000/svg"'
    )
  }

  // Embed markmap CSS styles into the SVG so it renders standalone
  const styles = document.querySelectorAll('style')
  let markmapCss = ''
  styles.forEach((s) => {
    if (s.textContent.includes('.markmap')) {
      markmapCss += s.textContent
    }
  })
  if (markmapCss) {
    // Insert <defs><style> right after the <svg> opening tag (not the first >)
    svgString = svgString.replace(
      /(<svg[^>]*>)/,
      `$1<defs><style>${markmapCss}</style></defs>`
    )
  }

  return svgString
}

// ─── Get full content bounding box ──────────────────────────────────────────
function getContentBBox() {
  const svgEl = mmSvgRef.value
  if (!svgEl) return { x: 0, y: 0, width: 800, height: 600 }

  try {
    // getBBox on the SVG element returns bounds of ALL child content
    // in SVG coordinate space, naturally including child transforms
    const bbox = svgEl.getBBox()
    if (bbox.width > 0 && bbox.height > 0) return bbox
  } catch {
    // Element not in document — try the first <g> child
    try {
      const g = svgEl.querySelector('g')
      if (g) {
        const bbox = g.getBBox()
        if (bbox.width > 0 && bbox.height > 0) return bbox
      }
    } catch {
      // Fall through
    }
  }
  return { x: 0, y: 0, width: 800, height: 600 }
}

// ─── Set viewBox on cloned SVG to show full content ─────────────────────────
function setFullViewBox(svgClone) {
  const dims = getContentBBox()
  const padding = 60
  const vx = dims.x - padding
  const vy = dims.y - padding
  const vw = dims.width + padding * 2
  const vh = dims.height + padding * 2
  svgClone.setAttribute('viewBox', `${vx} ${vy} ${vw} ${vh}`)
  svgClone.removeAttribute('width')
  svgClone.removeAttribute('height')
  // width/height set to 100% so it scales responsively when opened standalone
  svgClone.setAttribute('width', '100%')
  svgClone.setAttribute('height', '100%')
  return { vw, vh }
}

// ─── Download as SVG (vector, full content) ─────────────────────────────────
function downloadAsSvg() {
  if (!mmSvgRef.value) return

  const cloned = mmSvgRef.value.cloneNode(true)

  // Fix NaN transforms
  cloned.querySelectorAll('[transform]').forEach((el) => {
    const t = el.getAttribute('transform')
    if (t && t.includes('NaN')) {
      el.setAttribute('transform', 'translate(0,0) scale(1)')
    }
  })

  // Convert foreignObjects to text for standalone SVG compatibility
  cloned.querySelectorAll('foreignObject').forEach((fo) => {
    const textContent = fo.textContent?.trim() || ''
    if (!textContent) {
      fo.remove()
      return
    }
    const x = parseFloat(fo.getAttribute('x')) || 0
    const y = parseFloat(fo.getAttribute('y')) || 0
    const h = parseFloat(fo.getAttribute('height')) || 20
    const w = parseFloat(fo.getAttribute('width')) || 160

    const textEl = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'text'
    )
    textEl.setAttribute('x', String(x + 4))
    textEl.setAttribute('y', String(y + h / 2 + 5))
    textEl.setAttribute('font-size', '14')
    textEl.setAttribute('font-family', 'sans-serif')
    textEl.setAttribute('fill', '#333')
    textEl.setAttribute('dominant-baseline', 'middle')
    textEl.textContent = textContent

    fo.parentNode.replaceChild(textEl, fo)
  })

  // Set full content viewBox
  setFullViewBox(cloned)

  // Serialize and download
  const svgString = serializeSvg(cloned)
  const blob = new Blob([svgString], {
    type: 'image/svg+xml;charset=utf-8',
  })
  triggerDownload(blob, getSafeFilename() + ' - mindmap.svg')
}

// ─── Download as PNG (high resolution, full content) ────────────────────────
async function downloadAsPng() {
  if (!mmSvgRef.value) {
    console.error('[MindMap] PNG export failed: SVG ref not found')
    alert('PNG export failed: mind map not rendered yet.')
    return
  }

  const exportSvg = buildExportableSvg()
  if (!exportSvg) {
    alert('PNG export failed: could not build exportable SVG.')
    return
  }

  const { vw, vh } = setFullViewBox(exportSvg)

  // Cap scale to keep canvas within browser limits (max ~268 megapixels)
  const MAX_AREA = 16000000 // 16 MP — safe for most browsers
  let scale = Math.max(2, Math.ceil(3840 / vw))
  while (vw * scale * vh * scale > MAX_AREA && scale > 1) {
    scale = Math.max(1, scale - 1)
  }

  const svgString = serializeSvg(exportSvg)

  const canvas = document.createElement('canvas')
  canvas.width = Math.round(vw * scale)
  canvas.height = Math.round(vh * scale)
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  const img = new Image()
  const blob = new Blob([svgString], {
    type: 'image/svg+xml;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)

  return new Promise((resolve) => {
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      URL.revokeObjectURL(url)
      canvas.toBlob((pngBlob) => {
        if (pngBlob) {
          triggerDownload(pngBlob, getSafeFilename() + ' - mindmap.png')
        } else {
          alert('PNG export failed: could not create blob.')
        }
        resolve()
      }, 'image/png')
    }
    img.onerror = (e) => {
      URL.revokeObjectURL(url)
      console.error('[MindMap] PNG image load failed:', e)
      alert(
        'PNG export failed. The image may be too large. Please use SVG download instead.'
      )
      resolve()
    }
    img.src = url
  })
}

// ─── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
  // Clean up markmap instance
  if (markmapInstance) {
    markmapInstance.destroy()
    markmapInstance = null
  }
})
</script>

<template>
  <div class="mindmap-wrapper">
    <!-- Idle -->
    <div v-if="status === 'idle'" class="mm-idle">
      <p class="mm-desc">
        {{
          t.ai_mindmap_desc ||
          '基于视频内容自动生成结构化思维导图，帮助快速梳理知识结构。'
        }}
      </p>
      <button class="mm-generate-btn" @click="generateMindMap">
        <svg
          viewBox="0 0 24 24" fill="none" width="18" height="18"
        >
          <path
            d="M11 3a1 1 0 10-2 0v3a1 1 0 102 0V3zM7 7a1 1 0 00-1 1v2a1 1 0 002 0V8a1 1 0 00-1-1zM5 13a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1zM13 11a1 1 0 10-2 0v6a1 1 0 102 0v-6zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z"
            fill="currentColor"
          />
        </svg>
        {{ t.ai_generate_mindmap || '生成思维导图' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-else-if="status === 'loading'" class="mm-loading">
      <div class="mm-loading-spinner"></div>
      <p>{{ t.ai_generating_mindmap || '正在生成思维导图...' }}</p>
    </div>

    <!-- Error -->
    <div v-else-if="status === 'error'" class="mm-error">
      <p>{{ errorMsg }}</p>
      <button class="mm-retry-btn" @click="retry">
        {{ t.ai_retry || '重试' }}
      </button>
    </div>

    <!-- Loaded — mind map display -->
    <div v-else-if="status === 'loaded'" class="mm-loaded">
      <!-- Toolbar -->
      <div class="mm-toolbar">
        <div class="mm-toolbar-group">
          <button
            class="mm-tb-btn" :title="t.ai_mindmap_fit || '适应屏幕'"
            @click="fitView"
          >
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
              <path
                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
          <button class="mm-tb-btn" title="Zoom out" @click="zoomOut">−</button>
          <button class="mm-tb-btn" title="Zoom in" @click="zoomIn">+</button>
        </div>
        <div class="mm-toolbar-group">
          <button
            class="mm-tb-btn"
            :title="t.ai_mindmap_download_svg || '下载 SVG'"
            @click="downloadAsSvg"
          >
            <svg viewBox="0 0 24 24" fill="none" width="15" height="15">
              <path
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            SVG
          </button>
          <button
            class="mm-tb-btn"
            :title="t.ai_mindmap_download_png || '下载 PNG'"
            @click="downloadAsPng"
          >
            <svg viewBox="0 0 24 24" fill="none" width="15" height="15">
              <path
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            PNG
          </button>
          <button
            class="mm-tb-btn"
            :title="
              isFullscreen
                ? t.ai_mindmap_exit_fullscreen || '退出全屏'
                : t.ai_mindmap_fullscreen || '全屏'
            "
            @click="toggleFullscreen"
          >
            <svg
              v-if="!isFullscreen" viewBox="0 0 24 24" fill="none"
              width="15" height="15"
            >
              <path
                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <svg
              v-else viewBox="0 0 24 24" fill="none" width="15" height="15"
            >
              <path
                d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Mind map container -->
      <div
        ref="mmContainer"
        class="mm-svg-container"
        :class="{ 'mm-fullscreen': isFullscreen }"
      >
        <svg
          ref="mmSvgRef"
          class="mindmap-svg"
          xmlns="http://www.w3.org/2000/svg"
        ></svg>

        <!-- Fullscreen exit button -->
        <button
          v-if="isFullscreen"
          class="mm-fs-exit-btn"
          @click="toggleFullscreen"
        >
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <path
              d="M6 18L18 6M6 6l12 12"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          {{ t.ai_mindmap_exit_fullscreen || '退出全屏' }}
        </button>
      </div>

      <!-- Regenerate -->
      <div class="mm-footer">
        <button class="mm-retry-btn" @click="retry">
          <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
            <path
              d="M1 4v6h6M23 20v-6h-6"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          {{ t.ai_regenerate || '重新生成' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mindmap-wrapper {
  min-height: 300px;
}

/* ─── Idle ─────────────────────────────────────────────────────────────── */
.mm-idle {
  text-align: center;
  padding: 40px 20px;
}
.mm-desc {
  font-size: 15px;
  color: var(--color-text-sub, #6e6e73);
  margin-bottom: 24px;
  line-height: 1.6;
}
.mm-generate-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius-md, 18px);
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-family: var(--font-system, sans-serif);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease-out;
}
.mm-generate-btn:hover {
  transform: scale(1.03);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
}

/* ─── Loading ──────────────────────────────────────────────────────────── */
.mm-loading {
  text-align: center;
  padding: 64px 0;
  color: var(--color-text-sub, #6e6e73);
}
.mm-loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border-light, #e8e8ed);
  border-top-color: var(--color-accent, #0071e3);
  border-radius: 50%;
  animation: mm-spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes mm-spin {
  to {
    transform: rotate(360deg);
  }
}

/* ─── Error ────────────────────────────────────────────────────────────── */
.mm-error {
  text-align: center;
  padding: 40px 20px;
}
.mm-error p {
  font-size: 14px;
  color: var(--color-error, #ff3b30);
  margin-bottom: 16px;
}
.mm-retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: 1px solid var(--color-border, #d2d2d7);
  border-radius: var(--radius-full, 9999px);
  background: var(--color-surface, #ffffff);
  color: var(--color-accent, #0071e3);
  font-family: var(--font-system, sans-serif);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease-out;
}
.mm-retry-btn:hover {
  background: var(--color-bg, #f5f5f7);
  color: var(--color-text, #1d1d1f);
}

/* ─── Loaded / Toolbar ─────────────────────────────────────────────────── */
.mm-loaded {
  position: relative;
}
.mm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  margin-bottom: 12px;
}
.mm-toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}
.mm-tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 32px;
  min-width: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border, #d2d2d7);
  border-radius: 8px;
  background: var(--color-surface, #ffffff);
  color: var(--color-text-sub, #6e6e73);
  font-family: var(--font-system, sans-serif);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease-out;
  white-space: nowrap;
}
.mm-tb-btn:hover {
  background: var(--color-bg, #f5f5f7);
  color: var(--color-text, #1d1d1f);
  border-color: var(--color-text-sub, #6e6e73);
}

/* ─── SVG Container ────────────────────────────────────────────────────── */
.mm-svg-container {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-sm, 12px);
  background: #ffffff;
  border: 1px solid var(--color-border-light, #e8e8ed);
  min-height: 500px;
  height: 500px;
  max-height: 70vh;
}
.mindmap-svg {
  display: block;
  width: 100%;
  height: 100%;
}

/* ─── Fullscreen ───────────────────────────────────────────────────────── */
.mm-fullscreen {
  position: fixed !important;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  border-radius: 0 !important;
  border: none !important;
  min-height: 100vh !important;
  height: 100vh !important;
  max-height: 100vh !important;
  background: #ffffff;
}
.mm-fs-exit-btn {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 10000;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--color-border, #d2d2d7);
  border-radius: var(--radius-sm, 12px);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  color: var(--color-text, #1d1d1f);
  font-family: var(--font-system, sans-serif);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.15s ease-out;
}
.mm-fs-exit-btn:hover {
  background: #ffffff;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

/* ─── Footer ───────────────────────────────────────────────────────────── */
.mm-footer {
  display: flex;
  justify-content: center;
  padding-top: 12px;
}

/* ─── markmap text rendering fixes ─────────────────────────────────────── */
:deep(.markmap-foreign) {
  display: inline-block !important;
  font-family: var(--font-system, -apple-system, BlinkMacSystemFont, sans-serif) !important;
  font-size: 14px !important;
  color: #333 !important;
}
:deep(foreignObject) {
  overflow: visible !important;
}
:deep(.markmap-node) {
  cursor: pointer;
}
:deep(.markmap-link) {
  stroke: #c0c4cc;
  stroke-width: 1.5;
  fill: none;
  opacity: 0.6;
}
:deep(.markmap-node circle) {
  stroke: var(--color-accent, #0071e3);
  stroke-width: 1.5;
  fill: var(--color-accent, #0071e3);
}
</style>
