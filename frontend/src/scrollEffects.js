/**
 * Apple-style scroll-driven animations.
 *
 * Provides:
 *   - Parallax background shift
 *   - Progressive opacity / scale based on element position in viewport
 *   - Sticky-section feel (elements gently pin while sibling scrolls through)
 */

export function useScrollEffects() {
  let ticking = false
  const elements = []

  function update() {
    const vh = window.innerHeight
    const scrollY = window.scrollY

    for (const el of elements) {
      const rect = el.getBoundingClientRect()
      const elTop = rect.top + scrollY
      const elCenter = rect.top + rect.height / 2
      const elBottom = rect.bottom

      // ── Parallax backgrounds ──────────────────────────────
      if (el.dataset.parallax) {
        const speed = parseFloat(el.dataset.parallax) || 0.15
        const shift = (elCenter - vh) * speed
        el.style.setProperty('--parallax-y', `${shift}px`)
      }

      // ── Scroll-proportional opacity / scale ───────────────
      // 0 when element bottom is at viewport top, 1 at 30% from top, peak 1
      if (el.dataset.scrollFade) {
        const start = vh * 0.85 // start fading in when top of element enters bottom 85%
        const end   = vh * 0.25 // fully visible when element reaches 25% from top
        let progress = (start - rect.top) / (start - end)
        progress = Math.max(0, Math.min(1, progress))
        el.style.setProperty('--scroll-progress', progress.toFixed(3))
        el.style.opacity = 0.3 + progress * 0.7
        el.style.transform = `translateY(${(1 - progress) * 30}px) scale(${0.96 + progress * 0.04})`
      }

      // ── Sticky-pin feel: slight vertical lock ────────────
      if (el.dataset.stickyPin && rect.top < vh * 0.3 && rect.bottom > 0) {
        const pinProgress = Math.max(0, Math.min(1, (vh * 0.3 - rect.top) / (rect.height * 0.5)))
        el.style.setProperty('--pin-progress', pinProgress.toFixed(3))
      }
    }

    ticking = false
  }

  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(update)
      ticking = true
    }
  }

  function observe(el) {
    if (!el) return
    elements.push(el)
    // Initial paint
    update()
  }

  function unobserve(el) {
    const idx = elements.indexOf(el)
    if (idx !== -1) elements.splice(idx, 1)
  }

  function mount() {
    window.addEventListener('scroll', onScroll, { passive: true })
    update()
  }

  function unmount() {
    window.removeEventListener('scroll', onScroll)
    elements.length = 0
  }

  return { observe, unobserve, mount, unmount }
}
