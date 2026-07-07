<template>
  <div class="chart-shell">
    <div class="chart-stage" v-if="hasData">
      <svg class="chart-svg" viewBox="0 0 640 240" preserveAspectRatio="none" @mousemove="onMouseMove" @mouseleave="hoverIndex = -1">
        <g class="grid">
          <line v-for="step in 5" :key="step" :x1="56" :x2="620" :y1="gridY(step)" :y2="gridY(step)" />
        </g>

        <g class="series-group" v-for="series in normalizedSeries" :key="series.key">
          <polyline :points="series.points" :stroke="series.color" fill="none" stroke-width="2.4" stroke-linecap="round" />
        </g>

        <g class="hover-layer" v-if="hoverIndex >= 0">
          <line class="hover-line" :x1="xForIndex(hoverIndex)" :x2="xForIndex(hoverIndex)" y1="24" y2="190" />
          <circle
            v-for="series in normalizedSeries"
            :key="`dot-${series.key}`"
            v-show="pointAt(series, hoverIndex)"
            :cx="pointAt(series, hoverIndex)?.x || 0"
            :cy="pointAt(series, hoverIndex)?.y || 0"
            r="3.5"
            :fill="series.color"
            stroke="#fff"
            stroke-width="1.2"
          />
        </g>

        <g class="axis-labels">
          <text x="56" y="226">{{ startLabel }}</text>
          <text x="338" y="226" text-anchor="middle">{{ middleLabel }}</text>
          <text x="620" y="226" text-anchor="end">{{ endLabel }}</text>
        </g>
      </svg>

      <div class="hover-tooltip" v-if="hoverIndex >= 0 && tooltipRows.length">
        <strong>{{ tooltipLabel }}</strong>
        <span v-for="row in tooltipRows" :key="row.key">
          <i :style="{ background: row.color }"></i>
          {{ row.label }}: {{ row.value }}
        </span>
      </div>
    </div>

    <p class="empty" v-else>{{ emptyText }}</p>

    <div class="legend" v-if="legendItems.length">
      <span v-for="item in legendItems" :key="item.key" class="legend-item">
        <i :style="{ background: item.color }"></i>
        {{ item.label }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  labels: {
    type: Array,
    default: () => [],
  },
  series: {
    type: Array,
    default: () => [],
  },
  emptyText: {
    type: String,
    default: 'داده‌ای برای نمایش وجود ندارد.',
  },
})

const hoverIndex = ref(-1)
const HEX_COLOR_REGEX = /^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i
const fallbackSeriesColors = Object.freeze([
  'var(--accent-green)',
  'var(--accent-gold)',
  'var(--danger)',
  'var(--success)',
  'var(--warning)',
  'var(--text-secondary)',
])

const pointCount = computed(() => {
  const labelsCount = (props.labels || []).length
  const seriesCount = (props.series || []).reduce((max, item) => Math.max(max, (item.values || []).length), 0)
  return Math.max(labelsCount, seriesCount, 1)
})

const valueMax = computed(() => {
  let max = 0
  for (const item of props.series || []) {
    for (const value of item.values || []) {
      max = Math.max(max, Number(value || 0))
    }
  }
  return max > 0 ? max : 1
})

const hasData = computed(() => (props.series || []).some((item) => (item.values || []).some((value) => Number(value || 0) > 0)))

const displayLabels = computed(() => (props.labels || []).map((label) => formatMaybeDate(label)))

const normalizedSeries = computed(() => {
  const count = Math.max(pointCount.value, 2)
  return (props.series || []).map((item, index) => {
    const points = (item.values || []).map((value, idx) => {
      const x = xForIndex(idx, count)
      const y = yFromValue(value)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })

    return {
      key: item.key,
      label: item.label,
      color: resolveSeriesColor(item.color, index),
      values: item.values || [],
      points: points.join(' '),
    }
  })
})

const legendItems = computed(() =>
  (props.series || []).map((item, index) => ({
    key: item.key,
    label: item.label,
    color: resolveSeriesColor(item.color, index),
  })),
)

const startLabel = computed(() => String(displayLabels.value?.[0] || ''))
const middleLabel = computed(() => String(displayLabels.value?.[Math.floor((displayLabels.value?.length || 1) / 2)] || ''))
const endLabel = computed(() => String(displayLabels.value?.[(displayLabels.value?.length || 1) - 1] || ''))

const tooltipLabel = computed(() => String(displayLabels.value?.[hoverIndex.value] || '-'))
const tooltipRows = computed(() =>
  (props.series || [])
    .map((item, index) => ({
      key: item.key,
      label: item.label,
      color: resolveSeriesColor(item.color, index),
      value: formatNumber(item.values?.[hoverIndex.value]),
    }))
    .filter((row) => row.value !== null),
)

function resolveSeriesColor(color, index) {
  const raw = String(color || '').trim()
  if (raw && !HEX_COLOR_REGEX.test(raw)) {
    return raw
  }
  return fallbackSeriesColors[index % fallbackSeriesColors.length]
}

function gridY(step) {
  return 36 + ((step - 1) * 154) / 4
}

function xForIndex(idx, forcedCount = pointCount.value) {
  const count = Math.max(forcedCount, 2)
  return 56 + (564 * idx) / Math.max(count - 1, 1)
}

function yFromValue(value) {
  const ratio = Number(value || 0) / valueMax.value
  return 190 - ratio * 154
}

function pointAt(series, idx) {
  const value = series?.values?.[idx]
  if (value === undefined || value === null || value === '') {
    return null
  }
  return {
    x: xForIndex(idx),
    y: yFromValue(value),
  }
}

function onMouseMove(event) {
  const svg = event.currentTarget
  if (!svg) {
    return
  }
  const rect = svg.getBoundingClientRect()
  if (!rect.width) {
    return
  }
  const relativeX = ((event.clientX - rect.left) * 640) / rect.width
  const span = pointCount.value <= 1 ? 1 : pointCount.value - 1
  const rawIndex = pointCount.value <= 1 ? 0 : Math.round(((relativeX - 56) * span) / 564)
  hoverIndex.value = Math.min(Math.max(rawIndex, 0), pointCount.value - 1)
}

function formatNumber(value) {
  if (value === undefined || value === null || value === '') {
    return null
  }
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return String(value)
  }
  return Number.isInteger(numeric) ? numeric.toLocaleString('fa-IR') : numeric.toLocaleString('fa-IR', { maximumFractionDigits: 2 })
}

function formatMaybeDate(value) {
  const raw = String(value || '')
  if (!raw) {
    return ''
  }
  if (!/^\d{4}-\d{2}-\d{2}/.test(raw)) {
    return raw
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}
</script>

<style scoped>
.chart-shell {
  display: grid;
  gap: 0.45rem;
}

.chart-stage {
  position: relative;
}

.chart-svg {
  width: 100%;
  height: 240px;
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.45);
}

.grid line {
  stroke: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  stroke-width: 1;
}

.axis-labels text {
  fill: var(--text-muted);
  font-size: 11px;
}

.hover-line {
  stroke: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
  stroke-width: 1.2;
  stroke-dasharray: 3 3;
}

.hover-tooltip {
  position: absolute;
  top: 0.45rem;
  left: 0.45rem;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  background: rgb(var(--palette-eggshell-rgb) / 0.94);
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  padding: 0.4rem 0.46rem;
  display: grid;
  gap: 0.22rem;
  min-width: 132px;
}

.hover-tooltip strong {
  font-size: 0.73rem;
  color: var(--text-primary);
}

.hover-tooltip span {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.hover-tooltip i {
  width: 9px;
  height: 9px;
  border-radius: 999px;
}

.legend {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.74rem;
  color: var(--text-muted);
}

.legend-item i {
  width: 11px;
  height: 11px;
  border-radius: 999px;
}

.empty {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}
</style>
