<template>
  <ManagementSurfaceCard v-if="chart" :title="chart.title" :subtitle="chart.subtitle || ''">
    <ManagementLineChart v-if="isLine" :labels="chart.labels || []" :series="chart.series || []" />

    <ManagementBarList
      v-else
      :rows="barRows"
      :mode="chart.unit === 'count' ? 'count' : 'money'"
      :currency="currency"
    />
  </ManagementSurfaceCard>
</template>

<script setup>
import { computed } from 'vue'
import ManagementBarList from '@/components/management/bi/ManagementBarList.vue'
import ManagementLineChart from '@/components/management/bi/ManagementLineChart.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

const props = defineProps({
  chart: {
    type: Object,
    default: null,
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

const isLine = computed(() => {
  const type = String(props.chart?.type || '').toLowerCase()
  return type === 'line' || type === 'area'
})

const HEX_COLOR_REGEX = /^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i

const barRows = computed(() => {
  const labels = props.chart?.labels || []
  const firstSeries = (props.chart?.series || [])[0] || { values: [] }
  return labels.map((label, idx) => ({
    key: `${String(label)}-${idx}`,
    label: formatMaybeDate(label),
    value: Number(firstSeries.values?.[idx] || 0),
    color: resolveSeriesColor(firstSeries.color),
  }))
})

function resolveSeriesColor(color) {
  const raw = String(color || '').trim()
  if (!raw || HEX_COLOR_REGEX.test(raw)) {
    return 'var(--accent-green)'
  }
  return raw
}

function formatMaybeDate(value) {
  const raw = String(value || '')
  if (!raw || !/^\d{4}-\d{2}-\d{2}/.test(raw)) {
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
