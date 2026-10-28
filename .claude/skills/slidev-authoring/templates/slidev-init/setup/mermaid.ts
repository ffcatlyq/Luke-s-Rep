import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => {
  const style = typeof document !== 'undefined'
    ? getComputedStyle(document.documentElement)
    : null

  const v = (name: string, fallback: string) =>
    style?.getPropertyValue(name).trim() || fallback

  const bg = v('--bg', '#ffffff')
  const text = v('--text', '#434343')
  const textDim = v('--text-dim', '#706b69')
  const border = v('--border', '#e0e0e0')
  const surface = v('--surface', '#f3f3f3')

  return {
    theme: 'base',
    themeVariables: {
      mainBkg: surface,
      nodeBorder: border,
      clusterBkg: bg,
      clusterBorder: border,
      nodeTextColor: text,
      primaryTextColor: text,
      secondaryTextColor: textDim,
      tertiaryTextColor: textDim,
      lineColor: textDim,
      primaryColor: surface,
      secondaryColor: bg,
      tertiaryColor: bg,
      fontFamily: v('--font-sans', 'Inter, Noto Sans SC, system-ui, sans-serif'),
      fontSize: '13px',
      edgeLabelBackground: bg,
    },
  }
})
