<script setup>
import { ref, inject, computed, nextTick } from 'vue'

const t = inject('t')
const API_BASE = 'http://localhost:8000'

const props = defineProps({ url: String })

const status = ref('idle')
const treeData = ref(null)
const errorMsg = ref('')
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const collapsedNodes = ref(new Set())
const svgContainer = ref(null)

// ─── Layout Constants ────────────────────────────────────────────────────
const NODE_W = 180
const NODE_H = 48
const H_GAP = 70
const V_GAP = 20

// ─── Flat tree layout ─────────────────────────────────────────────────────
const layoutTree = computed(() => {
  if (!treeData.value?.root) return null
  const allNodes = []
  let maxDepth = 0

  // First pass: assign depth and collect nodes
  function walk(node, depth) {
    const n = { node, depth, children: [], id: allNodes.length }
    maxDepth = Math.max(maxDepth, depth)
    allNodes.push(n)
    if (node.children) {
      for (const c of node.children) {
        const child = walk(c, depth + 1)
        n.children.push(child)
      }
    }
    return n
  }
  const root = walk(treeData.value.root, 0)

  // Group nodes by depth, assign Y positions
  const depthGroups = {}
  for (const n of allNodes) {
    if (!depthGroups[n.depth]) depthGroups[n.depth] = []
    depthGroups[n.depth].push(n)
  }

  // Assign positions
  for (let d = 0; d <= maxDepth; d++) {
    const nodes = depthGroups[d] || []
    const totalH = nodes.length * (NODE_H + V_GAP)
    const startY = -(totalH / 2) + NODE_H / 2
    nodes.forEach((n, i) => {
      n.x = d * (NODE_W + H_GAP) + 40
      n.y = startY + i * (NODE_H + V_GAP)
    })
  }

  const w = (maxDepth + 1) * (NODE_W + H_GAP) + 80
  const maxInCol = Math.max(...Object.values(depthGroups).map(g => g.length), 1)
  const h = Math.max(maxInCol * (NODE_H + V_GAP) + 80, 400)

  return { root, allNodes, width: w, height: h, depthGroups, maxDepth }
})

// ─── Visible nodes ────────────────────────────────────────────────────────
const visibleNodes = computed(() => {
  if (!layoutTree.value) return []
  const result = []

  function walk(n, path) {
    const p = [...path, n.node.label]
    result.push({ ...n, path: p })
    if (!collapsedNodes.value.has(p.join('/'))) {
      for (const c of n.children) walk(c, p)
    }
  }
  walk(layoutTree.value.root, [])
  return result
})

// ─── Edges ────────────────────────────────────────────────────────────────
const edges = computed(() => {
  const visibleSet = new Set(visibleNodes.value.map(n => n.id))
  const result = []
  for (const vn of visibleNodes.value) {
    if (collapsedNodes.value.has(vn.path.join('/'))) continue
    for (const c of vn.children) {
      if (!visibleSet.has(c.id)) continue
      result.push({
        x1: vn.x + NODE_W, y1: vn.y + NODE_H / 2,
        x2: c.x, y2: c.y + NODE_H / 2,
      })
    }
  }
  return result
})

// ─── Actions ──────────────────────────────────────────────────────────────
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
    scale.value = 1; panX.value = 0; panY.value = 0
    collapsedNodes.value = new Set()
    status.value = 'loaded'
  } catch (err) {
    errorMsg.value = err.message || 'Network error'
    status.value = 'error'
  }
}

function toggleCollapse(nodePath) {
  const key = nodePath.join('/')
  const s = new Set(collapsedNodes.value)
  s.has(key) ? s.delete(key) : s.add(key)
  collapsedNodes.value = s
}

// ─── Pan / Zoom ───────────────────────────────────────────────────────────
function onWheel(e) {
  e.preventDefault()
  scale.value = Math.max(0.3, Math.min(2, scale.value + (e.deltaY > 0 ? -0.1 : 0.1)))
}

function onMouseDown(e) {
  if (e.target.closest('.mm-node-g')) return
  isPanning.value = true
  panStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
}

function onMouseMove(e) {
  if (!isPanning.value) return
  panX.value = e.clientX - panStart.value.x
  panY.value = e.clientY - panStart.value.y
}
function onMouseUp() { isPanning.value = false }
function resetView() { scale.value = 1; panX.value = 0; panY.value = 0 }
function retry() { generateMindMap() }

// ─── Download as PNG ──────────────────────────────────────────────────────
function downloadAsImage() {
  const svgEl = document.querySelector('.mindmap-svg')
  if (!svgEl) return

  const w = parseInt(svgEl.getAttribute('width')) || 1000
  const h = parseInt(svgEl.getAttribute('height')) || 600
  const svgData = new XMLSerializer().serializeToString(svgEl)

  const canvas = document.createElement('canvas')
  canvas.width = w * 2
  canvas.height = h * 2
  const ctx = canvas.getContext('2d')
  ctx.scale(2, 2)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, w, h)

  const img = new Image()
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  img.onload = () => {
    ctx.drawImage(img, 0, 0, w, h)
    URL.revokeObjectURL(url)
    const link = document.createElement('a')
    link.download = 'mindmap.png'
    link.href = canvas.toDataURL('image/png')
    link.click()
  }
  img.src = url
}
</script>

<template>
  <div class="mindmap-wrapper">
    <!-- Idle -->
    <div v-if="status === 'idle'" class="mm-idle">
      <p class="mm-desc">{{ t.ai_mindmap_desc || '基于视频内容自动生成结构化思维导图，帮助快速梳理知识结构。' }}</p>
      <button class="mm-generate-btn" @click="generateMindMap">
        <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M11 3a1 1 0 10-2 0v3a1 1 0 102 0V3zM7 7a1 1 0 00-1 1v2a1 1 0 002 0V8a1 1 0 00-1-1zM5 13a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1zM13 11a1 1 0 10-2 0v6a1 1 0 102 0v-6zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" fill="currentColor"/></svg>
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
      <button class="mm-retry-btn" @click="retry">{{ t.ai_retry || '重试' }}</button>
    </div>

    <!-- Loaded -->
    <div v-else-if="status === 'loaded' && layoutTree" class="mm-loaded">
      <div class="mm-controls">
        <button class="mm-ctrl-btn" @click="scale = Math.min(2, scale + 0.2)">+</button>
        <span class="mm-zoom-label">{{ Math.round(scale * 100) }}%</span>
        <button class="mm-ctrl-btn" @click="scale = Math.max(0.3, scale - 0.2)">−</button>
        <button class="mm-ctrl-btn" @click="resetView">⟲</button>
        <button class="mm-ctrl-btn" @click="downloadAsImage" title="下载PNG">
          <svg viewBox="0 0 24 24" fill="none" width="15" height="15"><path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <div ref="svgContainer" class="mm-svg-container"
        @wheel="onWheel" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp">
        <svg :width="layoutTree.width" :height="layoutTree.height"
          :style="{ transform: `scale(${scale}) translate(${panX}px, ${panY}px)` }"
          class="mindmap-svg" xmlns="http://www.w3.org/2000/svg">

          <!-- Edges -->
          <g class="mm-edges">
            <path v-for="(e, i) in edges" :key="'e'+i"
              :d="`M ${e.x1} ${e.y1} C ${(e.x1+e.x2)/2} ${e.y1}, ${(e.x1+e.x2)/2} ${e.y2}, ${e.x2} ${e.y2}`"
              class="mm-edge" />
          </g>

          <!-- Nodes -->
          <g v-for="vn in visibleNodes" :key="vn.id" class="mm-node-g" @click.stop="toggleCollapse(vn.path)">
            <rect :x="vn.x" :y="vn.y" :width="NODE_W" :height="NODE_H" :rx="10"
              class="mm-node-bg" :class="'mm-d'+Math.min(vn.depth,2)" />
            <foreignObject :x="vn.x+10" :y="vn.y+8" :width="NODE_W-20" :height="NODE_H-16">
              <div class="mm-node-label" :class="{'mm-label-root': vn.depth===0}" xmlns="http://www.w3.org/1999/xhtml">
                {{ vn.node.label }}
              </div>
            </foreignObject>
            <!-- Collapse toggle -->
            <g v-if="vn.children.length" class="mm-toggle">
              <circle :cx="vn.x+NODE_W-8" :cy="vn.y+8" r="9" class="mm-toggle-circle" :class="'mm-tc'+Math.min(vn.depth,2)" />
              <text :x="vn.x+NODE_W-8" :y="vn.y+12" class="mm-toggle-text" :class="{'mm-tt-root': vn.depth===0}">
                {{ collapsedNodes.has(vn.path.join('/')) ? '+' : '−' }}
              </text>
            </g>
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mindmap-wrapper { min-height: 300px; }

.mm-idle { text-align: center; padding: 40px 20px; }
.mm-desc { font-size: 15px; color: var(--color-text-sub); margin-bottom: 24px; line-height: 1.6; }
.mm-generate-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 28px; border: none; border-radius: var(--radius-md);
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff; font-family: var(--font-system); font-size: 16px; font-weight: 600;
  cursor: pointer; transition: all var(--duration-fast);
}
.mm-generate-btn:hover { transform: scale(1.03); box-shadow: 0 8px 30px rgba(102,126,234,0.3); }

.mm-loading { text-align: center; padding: 64px 0; color: var(--color-text-sub); }
.mm-loading-spinner {
  width: 36px; height: 36px; border: 3px solid var(--color-border-light);
  border-top-color: var(--color-accent); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.mm-error { text-align: center; padding: 40px 20px; }
.mm-error p { font-size: 14px; color: var(--color-error); margin-bottom: 16px; }
.mm-retry-btn { padding: 8px 20px; border: 1px solid var(--color-border); border-radius: var(--radius-full); background: var(--color-surface); color: var(--color-accent); font-family: var(--font-system); font-size: 14px; cursor: pointer; }

.mm-loaded { position: relative; }
.mm-controls {
  display: flex; align-items: center; gap: 6px; position: absolute; top: 8px; right: 8px; z-index: 10;
}
.mm-ctrl-btn {
  width: 30px; height: 30px; border: 1px solid var(--color-border); border-radius: 8px;
  background: var(--color-surface); color: var(--color-text-sub); font-size: 15px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; justify-content: center; font-family: var(--font-system);
}
.mm-ctrl-btn:hover { background: var(--color-bg); color: var(--color-text); }
.mm-zoom-label { font-size: 12px; color: var(--color-text-sub); min-width: 36px; text-align: center; }

.mm-svg-container {
  overflow: auto; border-radius: var(--radius-sm); background: #fafafa;
  cursor: grab; user-select: none; height: 500px; max-height: 70vh;
}
.mm-svg-container:active { cursor: grabbing; }
.mindmap-svg { display: block; transform-origin: 0 0; transition: transform 0.15s ease-out; }

/* Edges */
.mm-edge { stroke: #c0c4cc; stroke-width: 2; fill: none; opacity: 0.7; }

/* Nodes */
.mm-node-g { cursor: pointer; transition: filter 0.15s; }
.mm-node-g:hover { filter: brightness(0.94); }
.mm-node-bg { stroke-width: 1.5; }
.mm-d0 { fill: #0071e3; stroke: #0066cc; }
.mm-d1 { fill: #e8f0fe; stroke: #a8c8fa; }
.mm-d2 { fill: #ffffff; stroke: #d2d2d7; }

.mm-node-label {
  font-family: var(--font-system); font-size: 13px; line-height: 1.35;
  color: #1d1d1f; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  word-break: break-word; height: 100%;
}
.mm-label-root { color: #fff; font-weight: 600; font-size: 14px; }

/* Toggle */
.mm-toggle-circle { fill: rgba(0,0,0,0.12); }
.mm-tc0 { fill: rgba(255,255,255,0.25); }
.mm-toggle-text { font-family: var(--font-system); font-size: 12px; font-weight: 700; fill: #6e6e73; text-anchor: middle; dominant-baseline: central; pointer-events: none; }
.mm-tt-root { fill: #fff; }
</style>
