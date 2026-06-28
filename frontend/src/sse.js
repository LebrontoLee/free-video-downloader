/**
 * SSE (Server-Sent Events) stream reader utility.
 * Handles POST-based SSE streaming since EventSource only supports GET.
 */

export async function readSSEStream(response, callbacks) {
  if (!response.ok) {
    try {
      const err = await response.json()
      callbacks.onError(err.detail || `Server error: ${response.status}`)
    } catch {
      callbacks.onError(`Server error: ${response.status}`)
    }
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        // Process remaining buffer
        if (buffer.trim()) {
          buffer += decoder.decode()
          processBuffer(buffer, callbacks)
        }
        break
      }

      buffer += decoder.decode(value, { stream: true })

      // Process complete events (separated by \n\n)
      while (true) {
        const idx = buffer.indexOf('\n\n')
        if (idx === -1) break
        const block = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        if (block.trim()) {
          processSSEEvent(block, callbacks)
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') return
    callbacks.onError(err.message || 'Stream read error')
  }
}

function processBuffer(buffer, callbacks) {
  for (const block of buffer.split('\n\n')) {
    if (block.trim()) processSSEEvent(block, callbacks)
  }
}

function processSSEEvent(block, callbacks) {
  const lines = block.split('\n')
  let eventType = 'message'
  let dataStr = ''

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim()
    } else if (line.startsWith('data: ')) {
      dataStr = line.slice(6)
    }
  }

  if (!dataStr) return

  try {
    const data = JSON.parse(dataStr)
    switch (eventType) {
      case 'token':
        callbacks.onToken?.(data.text || '')
        break
      case 'done':
        callbacks.onDone?.(data)
        break
      case 'error':
        callbacks.onError?.(data.message || 'Unknown error')
        break
      default:
        if (data.text) callbacks.onToken?.(data.text)
    }
  } catch (e) {
    console.warn('SSE parse error:', e, dataStr.slice(0, 100))
  }
}
