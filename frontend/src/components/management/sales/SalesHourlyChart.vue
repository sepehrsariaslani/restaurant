<template>
  <div class="sales-hourly-chart">
    <div class="hourly-chart-body">
      <svg viewBox="0 0 640 150" preserveAspectRatio="none" class="hourly-svg" role="img" aria-label="نمودار ساعتی">
        <!-- خطوط شبکه -->
        <line v-for="step in 4" :key="step" :x1="14" :x2="626" :y1="gridY(step)" :y2="gridY(step)" class="hgrid" />
        <!-- خط محور -->
        <line x1="14" x2="626" y1="150" y2="150" class="haxis" />

        <!-- ستون‌ها -->
        <g v-for="(value, idx) in values" :key="idx">
          <rect
            :x="barX(idx)"
            :y="barY(value)"
            :width="barW"
            :height="barH(value)"
            :fill="color"
            rx="2"
            class="hbar"
          >
            <title>{{ faHour(idx) }}:00 — {{ formatValue(value) }}</title>
          </rect>
        </g>
      </svg>

      <!-- برچسب ساعت‌ها در دو ردیف (خارج از SVG تا کشیده نشوند) -->
      <div class="hour-labels" dir="ltr">
        <span
          v-for="hour in 24"
          :key="hour"
          class="hour-label"
          :class="{ 'row-second': hour > 12 }"
          :style="{ left: labelLeft(hour - 1) }"
        >{{ faHour(hour - 1) }}</span>
      </div>
    </div>

    <div class="hour-axis-note">ساعت (دو ردیف: ۰ تا ۲۳)</div>

    <div class="hourly-legend">
      <span class="legend-dot" :style="{ background: color }"></span>
      <span>{{ legendLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney, toPersianNumber } from '@/utils/format'

const props = defineProps({
  values: {
    type: Array,
    default: () => [],
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
const SLOT = CHART_WIDTH / 24

const barW = computed(() => Math.max(SLOT - 3, 6))

const maxValue = computed(() => {
  const max = Math.max(...(props.values || []).map((v) => Number(v || 0)))
  return max > 0 ? max : 1
})

function gridY(step) {
  return CHART_TOP + ((step - 1) * CHART_HEIGHT) / 3
}

function barX(idx) {
  return CHART_LEFT + idx * SLOT + 1.5
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
  const center = CHART_LEFT + idx * SLOT + SLOT / 2
  return `${(center / CHART_RIGHT) * 100}%`
}

function faHour(hour) {
  return toPersianNumber(hour)
}

function formatValue(value) {
  const numeric = Number(value || 0)
  if (props.mode === 'count') {
    return `${numeric.toLocaleString('fa-IR')} عدد`
  }
  return formatMoney(numeric, props.currency)
}
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

.hbar {
  transition: opacity 0.15s ease;
}

.hbar:hover {
  opacity: 0.78;
}

/* برچسب ساعت‌ها — دو ردیف، دقیقاً زیر ستون‌ها */
.hour-labels {
  position: relative;
  height: 40px;
  direction: ltr;
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
</style>
