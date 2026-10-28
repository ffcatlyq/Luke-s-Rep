<script setup>
import { ref, onMounted, watch } from 'vue'
import { select } from 'd3-selection'
import { scaleBand, scaleLinear, scaleOrdinal, scaleSequential, scaleTime } from 'd3-scale'
import { arc, pie, line as d3line, lineRadial, curveLinearClosed, linkHorizontal } from 'd3-shape'
import { max, min, extent, range, sum } from 'd3-array'
import { axisBottom, axisLeft } from 'd3-axis'
import { interpolateBlues, interpolateGreens, interpolateReds, interpolateOranges } from 'd3-scale-chromatic'
import { sankey as d3sankey, sankeyLinkHorizontal, sankeyLeft } from 'd3-sankey'
import { treemap as d3treemap, hierarchy } from 'd3-hierarchy'

const props = defineProps({
  type: { type: String, default: 'bar' },
  data: { type: Array, required: true },
  width: { type: Number, default: 400 },
  height: { type: Number, default: 260 },
  color: { type: String, default: '' },
  showValues: { type: Boolean, default: true },
  showAxis: { type: Boolean, default: true },
  title: { type: String, default: '' },
  xTickFormat: { type: Function, default: null },
})

const svgRef = ref(null)

const colorMap = {
  green: '--primary',
  blue: '--secondary',
  yellow: '--warning',
  purple: '--accent',
  red: '--danger',
}

const paletteVars = ['--primary', '--secondary', '--warning', '--accent', '--danger']

function v(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function resolveColor(c) {
  if (!c) return null
  const varName = colorMap[c]
  return varName ? v(varName) : c
}

function getPalette() {
  return paletteVars.map(name => v(name))
}

function clear() {
  if (!svgRef.value) return
  select(svgRef.value).selectAll('*').remove()
}

// ─── Bar Chart ───
function renderBar() {
  const margin = { top: 20, right: 10, bottom: 30, left: 40 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleBand().domain(props.data.map(d => d.label)).range([0, w]).padding(0.3)
  const y = scaleLinear().domain([0, max(props.data, d => d.value) * 1.1]).range([h, 0])

  // Axis
  if (props.showAxis) {
    g.append('g').attr('transform', `translate(0,${h})`)
      .call(axisBottom(x).tickSize(0))
      .call(g => g.select('.domain').attr('stroke', v('--border')))
      .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')

    g.append('g')
      .call(axisLeft(y).ticks(5).tickSize(-w))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line').attr('stroke', v('--border')).attr('opacity', 0.4))
      .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')
  }

  // Bars
  g.selectAll('rect').data(props.data).join('rect')
    .attr('x', d => x(d.label))
    .attr('y', d => y(d.value))
    .attr('width', x.bandwidth())
    .attr('height', d => h - y(d.value))
    .attr('fill', (d, i) => resolveColor(d.color || props.color) || palette[i % palette.length])
    .attr('rx', 2)

  // Values
  if (props.showValues) {
    g.selectAll('.val').data(props.data).join('text')
      .attr('class', 'val')
      .attr('x', d => x(d.label) + x.bandwidth() / 2)
      .attr('y', d => y(d.value) - 5)
      .attr('text-anchor', 'middle')
      .attr('fill', v('--text'))
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .text(d => d.value)
  }
}

// ─── Line Chart ───
function renderLine() {
  const margin = { top: 20, right: 10, bottom: 30, left: 40 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const lineColor = resolveColor(props.color) || v('--primary')

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleBand().domain(props.data.map(d => d.label)).range([0, w]).padding(0.5)
  const y = scaleLinear().domain([0, max(props.data, d => d.value) * 1.15]).range([h, 0])

  // Axis
  if (props.showAxis) {
    g.append('g').attr('transform', `translate(0,${h})`)
      .call(axisBottom(x).tickSize(0))
      .call(g => g.select('.domain').attr('stroke', v('--border')))
      .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')

    g.append('g')
      .call(axisLeft(y).ticks(5).tickSize(-w))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line').attr('stroke', v('--border')).attr('opacity', 0.4))
      .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')
  }

  // Line
  const lineFn = d3line()
    .x(d => x(d.label) + x.bandwidth() / 2)
    .y(d => y(d.value))

  g.append('path')
    .datum(props.data)
    .attr('d', lineFn)
    .attr('fill', 'none')
    .attr('stroke', lineColor)
    .attr('stroke-width', 2)

  // Dots
  g.selectAll('circle').data(props.data).join('circle')
    .attr('cx', d => x(d.label) + x.bandwidth() / 2)
    .attr('cy', d => y(d.value))
    .attr('r', 4)
    .attr('fill', lineColor)

  // Values
  if (props.showValues) {
    g.selectAll('.val').data(props.data).join('text')
      .attr('class', 'val')
      .attr('x', d => x(d.label) + x.bandwidth() / 2)
      .attr('y', d => y(d.value) - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', v('--text'))
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .text(d => d.value)
  }
}

// ─── Pie / Donut ───
function renderPie(donut = false) {
  const palette = getPalette()
  const radius = Math.min(props.width, props.height) / 2 - 10
  const innerRadius = donut ? radius * 0.55 : 0

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${props.width / 2},${props.height / 2})`)

  const pieFn = pie().value(d => d.value).sort(null)
  const arcFn = arc().innerRadius(innerRadius).outerRadius(radius)
  const labelArc = arc().innerRadius(radius * 0.72).outerRadius(radius * 0.72)

  const arcs = g.selectAll('.arc').data(pieFn(props.data)).join('g').attr('class', 'arc')

  arcs.append('path')
    .attr('d', arcFn)
    .attr('fill', (d, i) => resolveColor(d.data.color || props.color) || palette[i % palette.length])
    .attr('stroke', v('--bg'))
    .attr('stroke-width', 2)

  // Labels
  if (props.showValues) {
    arcs.append('text')
      .attr('transform', d => `translate(${labelArc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .attr('fill', v('--text'))
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .text(d => d.data.label)
  }
}

// ─── Radar Chart ───
function renderRadar() {
  const palette = getPalette()
  const fillColor = resolveColor(props.color) || palette[0]
  const radius = Math.min(props.width, props.height) / 2 - 30
  const levels = 5
  const n = props.data.length
  const angleSlice = (Math.PI * 2) / n
  const maxVal = max(props.data, d => d.value) || 100

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${props.width / 2},${props.height / 2})`)

  // Grid circles
  for (let i = 1; i <= levels; i++) {
    const r = (radius / levels) * i
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', v('--border'))
      .attr('opacity', 0.4)
  }

  // Axis lines + labels
  props.data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x2 = Math.cos(angle) * radius
    const y2 = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', v('--border'))
      .attr('opacity', 0.4)

    const lx = Math.cos(angle) * (radius + 16)
    const ly = Math.sin(angle) * (radius + 16)
    g.append('text')
      .attr('x', lx).attr('y', ly)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', v('--text-dim'))
      .attr('font-size', '11px')
      .text(d.label)
  })

  // Data polygon
  const radarLine = lineRadial()
    .radius(d => (d.value / maxVal) * radius)
    .angle((d, i) => i * angleSlice)
    .curve(curveLinearClosed)

  g.append('path')
    .datum(props.data)
    .attr('d', radarLine)
    .attr('fill', fillColor)
    .attr('fill-opacity', 0.2)
    .attr('stroke', fillColor)
    .attr('stroke-width', 2)

  // Data dots
  props.data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const r = (d.value / maxVal) * radius
    g.append('circle')
      .attr('cx', Math.cos(angle) * r)
      .attr('cy', Math.sin(angle) * r)
      .attr('r', 3.5)
      .attr('fill', fillColor)
  })

  // Values
  if (props.showValues) {
    props.data.forEach((d, i) => {
      const angle = angleSlice * i - Math.PI / 2
      const r = (d.value / maxVal) * radius + 8
      // Only show if enough space (skip if too close to label)
      if (radius > 60) {
        g.append('text')
          .attr('x', Math.cos(angle) * r)
          .attr('y', Math.sin(angle) * r)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .attr('fill', fillColor)
          .attr('font-size', '10px')
          .attr('font-weight', '600')
          .text(d.value)
      }
    })
  }
}

// ─── Heatmap ───
function renderHeatmap() {
  const margin = { top: 20, right: 10, bottom: 30, left: 50 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom

  const xLabels = [...new Set(props.data.map(d => d.x))]
  const yLabels = [...new Set(props.data.map(d => d.y))]
  const [minVal, maxVal] = extent(props.data, d => d.value)

  // Pick interpolator based on color prop
  const interpolators = {
    green: interpolateGreens,
    blue: interpolateBlues,
    red: interpolateReds,
    yellow: interpolateOranges,
  }
  const interpolator = interpolators[props.color] || interpolateBlues

  const colorScale = scaleSequential(interpolator).domain([minVal, maxVal])

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleBand().domain(xLabels).range([0, w]).padding(0.05)
  const y = scaleBand().domain(yLabels).range([0, h]).padding(0.05)

  // Cells
  g.selectAll('rect').data(props.data).join('rect')
    .attr('x', d => x(d.x))
    .attr('y', d => y(d.y))
    .attr('width', x.bandwidth())
    .attr('height', y.bandwidth())
    .attr('fill', d => colorScale(d.value))
    .attr('rx', 2)

  // Values
  if (props.showValues) {
    g.selectAll('.val').data(props.data).join('text')
      .attr('class', 'val')
      .attr('x', d => x(d.x) + x.bandwidth() / 2)
      .attr('y', d => y(d.y) + y.bandwidth() / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', d => colorScale(d.value) ? (d.value > (maxVal + minVal) / 2 ? '#fff' : v('--text')) : v('--text'))
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .text(d => d.value)
  }

  // Axis labels
  g.append('g').attr('transform', `translate(0,${h})`)
    .call(axisBottom(x).tickSize(0))
    .call(g => g.select('.domain').remove())
    .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')

  g.append('g')
    .call(axisLeft(y).tickSize(0))
    .call(g => g.select('.domain').remove())
    .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')
}

// ─── Funnel Chart ───
// data: [{ label, value }] — values should be descending for typical funnel
function renderFunnel() {
  const margin = { top: 10, right: 20, bottom: 10, left: 20 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()
  const maxVal = max(props.data, d => d.value)

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const stepH = h / props.data.length
  const minWidth = w * 0.2

  props.data.forEach((d, i) => {
    const ratio = d.value / maxVal
    const barW = minWidth + (w - minWidth) * ratio
    const x = (w - barW) / 2
    const y = i * stepH
    const fillColor = resolveColor(d.color || props.color) || palette[i % palette.length]

    // Trapezoid shape using polygon
    const nextRatio = i < props.data.length - 1 ? props.data[i + 1].value / maxVal : ratio * 0.7
    const nextW = minWidth + (w - minWidth) * nextRatio
    const nextX = (w - nextW) / 2
    const gap = 2

    const points = [
      `${x},${y + gap}`,
      `${x + barW},${y + gap}`,
      `${nextX + nextW},${y + stepH - gap}`,
      `${nextX},${y + stepH - gap}`,
    ].join(' ')

    g.append('polygon')
      .attr('points', points)
      .attr('fill', fillColor)
      .attr('opacity', 0.85)

    // Label
    g.append('text')
      .attr('x', w / 2)
      .attr('y', y + stepH / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .text(d.label)

    // Value on the right
    if (props.showValues) {
      g.append('text')
        .attr('x', (w + barW) / 2 + 8)
        .attr('y', y + stepH / 2)
        .attr('dominant-baseline', 'central')
        .attr('fill', v('--text-dim'))
        .attr('font-size', '11px')
        .text(d.value)
    }
  })
}

// ─── Gantt Chart ───
// data: [{ label, start, end, color? }] — start/end are numeric (e.g. week number, day index)
function renderGantt() {
  const margin = { top: 20, right: 20, bottom: 30, left: 100 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const minStart = min(props.data, d => d.start)
  const maxEnd = max(props.data, d => d.end)

  const x = scaleLinear().domain([minStart, maxEnd]).range([0, w])
  const y = scaleBand().domain(props.data.map(d => d.label)).range([0, h]).padding(0.3)

  // Grid lines
  const ticks = x.ticks(8)
  ticks.forEach(tick => {
    g.append('line')
      .attr('x1', x(tick)).attr('x2', x(tick))
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', v('--border')).attr('opacity', 0.4)
  })

  // X axis
  if (props.showAxis) {
    g.append('g').attr('transform', `translate(0,${h})`)
      .call(axisBottom(x).ticks(8).tickSize(0).tickFormat(props.xTickFormat || (d => d)))
      .call(g => g.select('.domain').attr('stroke', v('--border')))
      .selectAll('text').attr('fill', v('--text-dim')).attr('font-size', '11px')
  }

  // Y axis labels
  props.data.forEach(d => {
    g.append('text')
      .attr('x', -8)
      .attr('y', y(d.label) + y.bandwidth() / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'central')
      .attr('fill', v('--text'))
      .attr('font-size', '11px')
      .text(d.label)
  })

  // Bars
  props.data.forEach((d, i) => {
    const fillColor = resolveColor(d.color || props.color) || palette[i % palette.length]
    g.append('rect')
      .attr('x', x(d.start))
      .attr('y', y(d.label))
      .attr('width', Math.max(x(d.end) - x(d.start), 2))
      .attr('height', y.bandwidth())
      .attr('fill', fillColor)
      .attr('rx', 3)
      .attr('opacity', 0.85)

    // Duration label
    if (props.showValues) {
      const barW = x(d.end) - x(d.start)
      if (barW > 30) {
        g.append('text')
          .attr('x', x(d.start) + barW / 2)
          .attr('y', y(d.label) + y.bandwidth() / 2)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .attr('fill', '#fff')
          .attr('font-size', '10px')
          .attr('font-weight', '600')
          .text(`${d.end - d.start}`)
      }
    }
  })
}

// ─── Timeline ───
// data: [{ label, value (description), date? (optional numeric position) }]
function renderTimeline() {
  const margin = { top: 30, right: 30, bottom: 30, left: 30 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const n = props.data.length
  const lineY = h / 2

  // Main horizontal line
  g.append('line')
    .attr('x1', 0).attr('x2', w)
    .attr('y1', lineY).attr('y2', lineY)
    .attr('stroke', v('--border'))
    .attr('stroke-width', 2)

  props.data.forEach((d, i) => {
    const x = (w / (n + 1)) * (i + 1)
    const above = i % 2 === 0
    const fillColor = resolveColor(d.color || props.color) || palette[i % palette.length]

    // Dot on line
    g.append('circle')
      .attr('cx', x).attr('cy', lineY)
      .attr('r', 6)
      .attr('fill', fillColor)
      .attr('stroke', v('--bg'))
      .attr('stroke-width', 2)

    // Connector line
    const textY = above ? lineY - 25 : lineY + 25
    g.append('line')
      .attr('x1', x).attr('x2', x)
      .attr('y1', lineY + (above ? -8 : 8))
      .attr('y2', textY + (above ? 5 : -5))
      .attr('stroke', v('--border'))
      .attr('stroke-width', 1)

    // Label (title)
    g.append('text')
      .attr('x', x)
      .attr('y', above ? textY - 4 : textY + 4)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', above ? 'auto' : 'hanging')
      .attr('fill', v('--text'))
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .text(d.label)

    // Description (value field)
    if (d.value && props.showValues) {
      g.append('text')
        .attr('x', x)
        .attr('y', above ? textY - 20 : textY + 20)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', above ? 'auto' : 'hanging')
        .attr('fill', v('--text-dim'))
        .attr('font-size', '10px')
        .text(d.value)
    }
  })
}

// ─── Sankey Diagram ───
// data: [{ source, target, value }] — source/target are node names
function renderSankey() {
  const margin = { top: 10, right: 10, bottom: 10, left: 10 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  // Build nodes from data
  const nodeNames = [...new Set(props.data.flatMap(d => [d.source, d.target]))]
  const nodeMap = new Map(nodeNames.map((name, i) => [name, i]))
  const nodes = nodeNames.map(name => ({ name }))
  const links = props.data.map(d => ({
    source: nodeMap.get(d.source),
    target: nodeMap.get(d.target),
    value: d.value,
  }))

  const sankeyLayout = d3sankey()
    .nodeId(d => d.index)
    .nodeAlign(sankeyLeft)
    .nodeWidth(14)
    .nodePadding(12)
    .extent([[0, 0], [w, h]])

  const { nodes: sNodes, links: sLinks } = sankeyLayout({
    nodes: nodes.map(d => ({ ...d })),
    links: links.map(d => ({ ...d })),
  })

  // Links
  g.selectAll('.link')
    .data(sLinks)
    .join('path')
    .attr('class', 'link')
    .attr('d', sankeyLinkHorizontal())
    .attr('fill', 'none')
    .attr('stroke', (d, i) => palette[d.source.index % palette.length])
    .attr('stroke-opacity', 0.35)
    .attr('stroke-width', d => Math.max(1, d.width))

  // Nodes
  g.selectAll('.node')
    .data(sNodes)
    .join('rect')
    .attr('class', 'node')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => Math.max(1, d.y1 - d.y0))
    .attr('fill', (d, i) => palette[i % palette.length])
    .attr('rx', 2)

  // Labels
  g.selectAll('.label')
    .data(sNodes)
    .join('text')
    .attr('class', 'label')
    .attr('x', d => d.x0 < w / 2 ? d.x1 + 6 : d.x0 - 6)
    .attr('y', d => (d.y0 + d.y1) / 2)
    .attr('text-anchor', d => d.x0 < w / 2 ? 'start' : 'end')
    .attr('dominant-baseline', 'central')
    .attr('fill', v('--text'))
    .attr('font-size', '11px')
    .text(d => d.name)

  // Values next to labels
  if (props.showValues) {
    g.selectAll('.val')
      .data(sNodes)
      .join('text')
      .attr('class', 'val')
      .attr('x', d => d.x0 < w / 2 ? d.x1 + 6 : d.x0 - 6)
      .attr('y', d => (d.y0 + d.y1) / 2 + 14)
      .attr('text-anchor', d => d.x0 < w / 2 ? 'start' : 'end')
      .attr('dominant-baseline', 'central')
      .attr('fill', v('--text-dim'))
      .attr('font-size', '9px')
      .text(d => d.value)
  }
}

// ─── Gauge Chart ───
// data: [{ label, value }] — value is 0-100 (percentage)
function renderGauge() {
  const palette = getPalette()
  const d = props.data[0] || { label: '', value: 0 }
  const val = Math.min(100, Math.max(0, d.value))
  const fillColor = resolveColor(d.color || props.color) || palette[0]

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${props.width / 2},${props.height * 0.6})`)

  const radius = Math.min(props.width, props.height) * 0.4
  const startAngle = -Math.PI * 0.75
  const endAngle = Math.PI * 0.75
  const angleRange = endAngle - startAngle

  // Background arc
  const bgArc = arc()
    .innerRadius(radius * 0.7)
    .outerRadius(radius)
    .startAngle(startAngle)
    .endAngle(endAngle)
    .cornerRadius(4)

  g.append('path')
    .attr('d', bgArc())
    .attr('fill', v('--surface'))

  // Value arc
  const valAngle = startAngle + (val / 100) * angleRange
  const valArc = arc()
    .innerRadius(radius * 0.7)
    .outerRadius(radius)
    .startAngle(startAngle)
    .endAngle(valAngle)
    .cornerRadius(4)

  g.append('path')
    .attr('d', valArc())
    .attr('fill', fillColor)

  // Center value text
  if (props.showValues) {
    g.append('text')
      .attr('x', 0).attr('y', -5)
      .attr('text-anchor', 'middle')
      .attr('fill', v('--text'))
      .attr('font-size', `${Math.max(20, radius * 0.4)}px`)
      .attr('font-weight', '700')
      .text(`${val}%`)

    // Label below
    if (d.label) {
      g.append('text')
        .attr('x', 0).attr('y', 20)
        .attr('text-anchor', 'middle')
        .attr('fill', v('--text-dim'))
        .attr('font-size', '12px')
        .text(d.label)
    }
  }

  // Min/Max labels
  const minPos = { x: Math.cos(startAngle) * (radius + 12), y: Math.sin(startAngle) * (radius + 12) }
  const maxPos = { x: Math.cos(endAngle) * (radius + 12), y: Math.sin(endAngle) * (radius + 12) }

  g.append('text').attr('x', minPos.x).attr('y', minPos.y)
    .attr('text-anchor', 'middle').attr('fill', v('--text-dim')).attr('font-size', '10px').text('0')
  g.append('text').attr('x', maxPos.x).attr('y', maxPos.y)
    .attr('text-anchor', 'middle').attr('fill', v('--text-dim')).attr('font-size', '10px').text('100')
}

// ─── Treemap ───
// data: [{ label, value, color?, children? }] — flat list or nested
function renderTreemap() {
  const margin = { top: 4, right: 4, bottom: 4, left: 4 }
  const w = props.width - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  const palette = getPalette()

  const svg = select(svgRef.value)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  // Build hierarchy — flat data gets wrapped in a root
  const rootData = { name: 'root', children: props.data.map(d => ({ name: d.label, value: d.value, color: d.color })) }
  const root = hierarchy(rootData).sum(d => d.value).sort((a, b) => b.value - a.value)

  d3treemap()
    .size([w, h])
    .padding(3)
    .round(true)(root)

  const leaves = root.leaves()

  // Rectangles
  leaves.forEach((leaf, i) => {
    const fillColor = resolveColor(leaf.data.color || props.color) || palette[i % palette.length]
    const lw = leaf.x1 - leaf.x0
    const lh = leaf.y1 - leaf.y0

    g.append('rect')
      .attr('x', leaf.x0).attr('y', leaf.y0)
      .attr('width', lw).attr('height', lh)
      .attr('fill', fillColor)
      .attr('opacity', 0.8)
      .attr('rx', 3)

    // Label — only if cell is large enough
    if (lw > 30 && lh > 20) {
      g.append('text')
        .attr('x', leaf.x0 + lw / 2)
        .attr('y', leaf.y0 + lh / 2 - (props.showValues ? 4 : 0))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', '#fff')
        .attr('font-size', lw > 60 ? '11px' : '9px')
        .attr('font-weight', '600')
        .text(leaf.data.name)

      if (props.showValues && lh > 35) {
        g.append('text')
          .attr('x', leaf.x0 + lw / 2)
          .attr('y', leaf.y0 + lh / 2 + 12)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .attr('fill', 'rgba(255,255,255,0.7)')
          .attr('font-size', '10px')
          .text(leaf.data.value)
      }
    }
  })
}

// ─── Render dispatcher ───
function render() {
  if (!svgRef.value) return
  clear()

  // Title
  if (props.title) {
    select(svgRef.value).append('text')
      .attr('x', props.width / 2)
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', v('--text'))
      .attr('font-size', '13px')
      .attr('font-weight', '600')
      .text(props.title)
  }

  const renderers = {
    bar: renderBar,
    line: renderLine,
    pie: () => renderPie(false),
    donut: () => renderPie(true),
    radar: renderRadar,
    heatmap: renderHeatmap,
    funnel: renderFunnel,
    gantt: renderGantt,
    timeline: renderTimeline,
    sankey: renderSankey,
    gauge: renderGauge,
    treemap: renderTreemap,
  }

  const fn = renderers[props.type]
  if (fn) fn()
}

onMounted(render)
watch(() => [props.type, props.data, props.color, props.width, props.height], render, { deep: true })
</script>

<template>
  <svg
    ref="svgRef"
    :width="width"
    :height="height"
    :viewBox="`0 0 ${width} ${height}`"
    style="overflow: visible; font-family: inherit;"
  />
</template>
