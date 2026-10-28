<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true },
  width: { type: String, default: '100%' },
  dark: { type: [Boolean, String], default: 'auto' },
  background: { type: Boolean, default: false },
})

const container = ref(null)
const loading = ref(true)
const error = ref('')

function isColorDark(color) {
  if (!color) return true
  const hex = color.replace(/^#/, '')
  if (hex.length < 6) return true
  const r = parseInt(hex.slice(0, 2), 16)
  const g = parseInt(hex.slice(2, 4), 16)
  const b = parseInt(hex.slice(4, 6), 16)
  return (r * 299 + g * 587 + b * 114) / 1000 < 128
}

function detectDarkMode() {
  if (props.dark === true || props.dark === false) return props.dark
  if (typeof document === 'undefined') return true
  const bg = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg').trim()
  return isColorDark(bg)
}

async function render() {
  if (!container.value) return
  loading.value = true
  error.value = ''

  try {
    // Load .excalidraw JSON
    const resp = await fetch(props.src)
    if (!resp.ok) throw new Error(`Failed to load ${props.src}: ${resp.status}`)
    const data = await resp.json()

    // Dynamic import from esm.sh (avoids local React dependency)
    const { exportToSvg } = await import(
      /* @vite-ignore */
      'https://esm.sh/@excalidraw/excalidraw@0.18.0?exports=exportToSvg'
    )

    const isDark = detectDarkMode()

    const svg = await exportToSvg({
      elements: data.elements || [],
      appState: {
        ...(data.appState || {}),
        exportWithDarkMode: isDark,
        exportBackground: props.background,
        viewBackgroundColor: props.background
          ? (isDark ? '#121212' : '#ffffff')
          : 'transparent',
      },
      files: data.files || {},
    })

    // Inject ZCOOL KuaiLe as CJK handwriting fallback for Virgil
    const defs = svg.querySelector('defs') || svg.insertBefore(
      document.createElementNS('http://www.w3.org/2000/svg', 'defs'),
      svg.firstChild
    )
    const fontStyle = document.createElementNS('http://www.w3.org/2000/svg', 'style')
    fontStyle.textContent = `
      @font-face {
        font-family: 'ZCOOL KuaiLe';
        font-style: normal;
        font-weight: 400;
        src: url('/fonts/ZCOOLKuaiLe-Regular.ttf') format('truetype');
      }
    `
    defs.appendChild(fontStyle)

    // Patch all text elements: append ZCOOL KuaiLe to font-family for CJK coverage
    svg.querySelectorAll('text, [style*="font-family"]').forEach(el => {
      const ff = el.getAttribute('font-family') || el.style.fontFamily || ''
      if (ff && !ff.includes('ZCOOL KuaiLe')) {
        const patched = ff.replace(/;?\s*$/, '') + ", 'ZCOOL KuaiLe'"
        if (el.getAttribute('font-family')) {
          el.setAttribute('font-family', patched)
        } else {
          el.style.fontFamily = patched
        }
      }
    })

    // Insert SVG into container
    svg.style.width = props.width
    svg.style.height = 'auto'
    container.value.innerHTML = ''
    container.value.appendChild(svg)
  } catch (e) {
    error.value = e.message || 'Failed to render Excalidraw'
    console.error('[Excalidraw]', e)
  } finally {
    loading.value = false
  }
}

onMounted(render)
watch(() => [props.src, props.dark, props.background], render)
</script>

<template>
  <div ref="container" class="excalidraw-container">
    <div v-if="loading" class="excalidraw-loading">Loading diagram...</div>
    <div v-if="error" class="excalidraw-error">{{ error }}</div>
  </div>
</template>

<style scoped>
.excalidraw-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.excalidraw-loading {
  color: var(--text-dim);
  font-size: 0.85em;
}

.excalidraw-error {
  color: var(--danger);
  font-size: 0.85em;
}
</style>
