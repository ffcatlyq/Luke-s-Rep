import { defineConfig } from 'vite'
import fs from 'fs'
import path from 'path'

function resolveCustomTheme(entry: string): string {
  const slidesPath = path.resolve(__dirname, entry)
  if (!fs.existsSync(slidesPath)) return 'roche-blue'
  const content = fs.readFileSync(slidesPath, 'utf-8')
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/)
  if (!fmMatch) return 'roche-blue'
  const themeMatch = fmMatch[1].match(/^customTheme:\s*(.+)$/m)
  return themeMatch ? themeMatch[1].trim() : 'roche-blue'
}

function slidevThemeSwitcher(): import('vite').Plugin {
  const entry = process.env.SLIDEV_ENTRY || 'slides.md'
  const theme = resolveCustomTheme(entry)
  return {
    name: 'slidev-theme-switcher',
    enforce: 'pre',
    buildStart() {
      console.log(`[theme-switcher] entry=${entry}, resolved theme=${theme}`)
    },
    transform(code, id) {
      if (id.endsWith('style.css') && code.includes("@import './themes/")) {
        const rewritten = code.replace(
          /@import\s+['"]\.\/themes\/[^/]+\/style\.css['"]/,
          `@import './themes/${theme}/style.css'`
        )
        if (rewritten !== code) {
          console.log(`[theme-switcher] rewrote import → themes/${theme}/style.css`)
        }
        return rewritten
      }
    },
  }
}

export default defineConfig({
  plugins: [slidevThemeSwitcher()],
})
