<template>
  <div class="sales-hourly-chart">
    <div class="hourly-chart-body" @mouseleave="hoverIndex = -1">
      <svg viewBox="0 0 640 150" preserveAspectRatio="none" class="hourly-svg" role="img" aria-label="نمودار">
        <!-- خطوط شبکه -->
        <line v-for="step in 4" :key="step" :x1="14" :x2="626" :y1="gridY(step)" :y2="gridY(step)" class="hgrid" />
        <!-- خط محور -->
        <line x1="14" x2="626" y1="150" y2="150" class="haxis" />

        <!-- ستون‌ها -->
        <g
          v-for="(value, idx) in values"
          :key="idx"
          @mouseenter="hoverIndex = idx"
          
        >
          <rect
            :x="barX(idx)"
            :y="barY(value)"
            :width="barW"
            :height="barH(value)"
            :fill="color"
            :opacity="hoverIndex === null || hoverIndex === idx ? 1 : 0.45"
            rx="2"
            class="hbar"
          />
        </g>

        <!-- خط راهنمای هاور -->
        <line
          v-if="hoverIndex !== null"
          :x1="barX(hoverIndex) + barW / 2"
          :x2="barX(hoverIndex) + barW / 2"
          y1="26"
          y2="150"
          class="hhover-line"
        />
      </svg>

      <!-- برچسب‌ها (خارج از SVG تا کشیده نشوند) -->
      <div class="hour-labels" :dir="twoRowLabels ? 'ltr' : 'rtl'">
        <span
          v-for="(label, idx) in displayLabels"
          :key="idx"
          class="hour-label"
          :class="{ 'row-second': twoRowLabels && idx >= Math.ceil(displayLabels.length / 2) }"
          :style="{ left: labelLeft(idx) }"
        >{{ label }}</span>
      </div>

      <!-- Tooltip هاور -->
      <div
        v-if="hoverIndex !== null && hoverValue !== null"
        class="hover-tooltip"
        :style="{ left: tooltipLeft, top: tooltipTop }"
      >
        <strong>{{ hoverLabel }}</strong>
        <span>{{ hoverValueText }}</span>
      </div>
    </div>

    <div v-if="twoRowLabels" class="hour-axis-note">ساعت (دو ردیف: ۰ تا ۲۳)</div>

    <div class="hourly-legend">
      <span class="legend-dot" :style="{ background: color }"></span>
      <span>{{ legendLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatMoney, toPersianNumber } from '@/utils/format'

const props = defineProps({
  values: {
    type: Array,
    default: () => [],
  },
  labels: {
    type: Array,
    default: null,
  },
  twoRowLabels: {
    type: Boolean,
    default: false,
  },
  color: {
    type: String,
    default: '#6F7B56',
  },
  mode: {
    type: String,
    default: 'money',
  },
  currency: {
    type: String,
    default: 'IRR',
  },
  legendLabel: {
    type: String,
    default: 'مقدار',
  },
})

const CHART_TOP = 30
const CHART_BOTTOM = 150
const CHART_LEFT = 14
const CHART_RIGHT = 626
const CHART_WIDTH = CHART_RIGHT - CHART_LEFT
const CHART_HEIGHT = CHART_BOTTOM - CHART_TOP

const hoverIndex = ref(null)

const count = computed(() => Math.max(props.values?.length || 0, 1))
const SLOT = computed(() => CHART_WIDTH / count.value)

const barW = computed(() => Math.max(SLOT.value - (count.value > 16 ? 3 : 8), 4))

const maxValue = computed(() => {
  const max = Math.max(...(props.values || []).map((v) => Number(v || 0)))
  return max > 0 ? max : 1
})

// برچسب‌های نمایشی: پیش‌فرض ۰ تا ۲۳ (ساعتی)
const displayLabels = computed(() => {
  if (Array.isArray(props.labels) && props.labels.length) {
    return props.labels.map((label, idx) => (String(label || '').trim() ? label : `${idx + 1}`))
  }
  return Array.from({ length: 24 }, (_, i) => toPersianNumber(i))
})

function gridY(step) {
  return CHART_TOP + ((step - 1) * CHART_HEIGHT) / 3
}

function barX(idx) {
  return CHART_LEFT + idx * SLOT.value + (count.value > 16 ? 1.5 : 4)
}

function barY(value) {
  const h = barH(value)
  return CHART_BOTTOM - h
}

function barH(value) {
  const numeric = Number(value || 0)
  return Math.max((numeric / maxValue.value) * CHART_HEIGHT, 1.5)
}

// موقعیت دقیق مرکز هر ستون نسبت به عرض چارت (درصد)
function labelLeft(idx) {
  const center = CHART_LEFT + idx * SLOT.value + SLOT.value / 2
  return `${(center / CHART_RIGHT) * 100}%`
}

const hoverValue = computed(() => {
  if (hoverIndex.value === null) return null
  const value = Number(props.values?.[hoverIndex.value] || 0)
  return value > 0 || true ? value : value
})

const hoverLabel = computed(() => {
  if (hoverIndex.value === null) return ''
  return String(displayLabels.value[hoverIndex.value] || '')
})

const hoverValueText = computed(() => {
  if (hoverValue.value === null) return ''
  const numeric = Number(hoverValue.value || 0)
  if (props.mode === 'count') {
    return `${numeric.toLocaleString('fa-IR')} عدد`
  }
  return formatMoney(numeric, props.currency)
})

const tooltipLeft = computed(() => {
  if (hoverIndex.value === null) return '0px'
  const center = CHART_LEFT + hoverIndex.value * SLOT.value + SLOT.value / 2
  const percent = (center / CHART_RIGHT) * 100
  return `${percent}%`
})

const tooltipTop = computed(() => {
  const value = Number(props.values?.[hoverIndex.value] || 0)
  const h = barH(value)
  const topPx = 150 - h - 8
  return `${(topPx / 150) * 100}%`
})
</script>

<style scoped>
.sales-hourly-chart {
  display: grid;
  gap: 0.35rem;
}

.hourly-chart-body {
  position: relative;
}

.hourly-svg {
  width: 100%;
  height: auto;
  display: block;
}

.hgrid {
  stroke: color-mix(in srgb, var(--mg-text-muted) 14%, transparent);
  stroke-width: 1;
}

.haxis {
  stroke: color-mix(in srgb, var(--mg-text-muted) 30%, transparent);
  stroke-width: 1.2;
}

.hhover-line {
  stroke: color-mix(in srgb, var(--mg-primary, #c97852) 55%, transparent);
  stroke-width: 1;
  stroke-dasharray: 3 3;
  pointer-events: none;
}

.hbar {
  transition: opacity 0.15s ease;
  cursor: pointer;
}

/* برچسب‌ها — برای حالت ساعتی دو ردیف، برای روزانه/هفتگی یک ردیف */
.hour-labels {
  position: relative;
  height: 40px;
}

.hour-label {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 10.5px;
  color: var(--mg-text-muted);
  line-height: 1;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.hour-label.row-second {
  top: 21px;
}

.hour-axis-note {
  font-size: 10px;
  color: var(--mg-text-muted);
  opacity: 0.8;
  text-align: center;
}

.hourly-legend {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

/* Tooltip هاور */
.hover-tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  z-index: 5;
  display: grid;
  gap: 0.1rem;
  padding: 0.35rem 0.6rem;
  border-radius: 10px;
  background: var(--mg-bg-surface, #fbf7f1);
  border: 1px solid color-mix(in srgb, var(--mg-primary, #c97852) 30%, var(--mg-border-light));
  box-shadow: 0 10px 22px rgb(52 38 31 / 0.18);
  pointer-events: none;
  white-space: nowrap;
}

.hover-tooltip strong {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.hover-tooltip span {
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--mg-text-main);
}
</style>
