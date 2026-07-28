<template>
  <ManagementPageScaffold :title="reportTitle" :subtitle="reportKey">
    <template #actions>
      <a class="secondary-btn" href="/management/reports">بازگشت به گزارش‌ها</a>
      <button class="secondary-btn" type="button" @click="loadReport" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی اطلاعات' }}
      </button>
    </template>

    <ManagementSurfaceCard tone="accent">
      <div class="filters">
        <label>
          از تاریخ
          <PersianDateInput v-model="filters.date_from" />
        </label>
        <label>
          تا تاریخ
          <PersianDateInput v-model="filters.date_to" />
        </label>
        <button class="primary-btn" type="button" @click="loadReport">اجرای گزارش</button>
      </div>
      <p class="window-line" v-if="activeMeta">
        {{ formatPersianDate(activeMeta.date_from) }} تا {{ formatPersianDate(activeMeta.date_to) }}
        <span v-if="activeMeta.previous_date_from">
          | مقایسه با {{ formatPersianDate(activeMeta.previous_date_from) }} تا {{ formatPersianDate(activeMeta.previous_date_to) }}
        </span>
      </p>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری گزارش...</p>
    <p class="error" v-if="error">{{ error }}</p>

    <template v-if="!loading && reportPayload">
      <ReportKpiGrid :kpis="activeKpis" :currency="activeCurrency" />

      <section class="charts-grid" v-if="activeCharts.length">
        <ReportChartRenderer
          v-for="chart in activeCharts"
          :key="chart.key || chart.title"
          :chart="chart"
          :currency="activeCurrency"
        />
      </section>

      <ManagementSurfaceCard title="جدول گزارش" v-if="legacyRows.length && !activeTables.length">
        <ManagementDataTable :columns="legacyColumns" :rows="legacyRows">
          <template v-for="column in legacyColumns" #[`cell-${column.key}`]="{ value }" :key="column.key">
            {{ formatLegacyCell(column.key, value) }}
          </template>
        </ManagementDataTable>
      </ManagementSurfaceCard>

      <section class="tables-grid" v-if="activeTables.length">
        <ManagementSurfaceCard
          v-for="table in activeTables"
          :key="table.key || table.title"
          :title="table.title || 'جدول گزارش'"
          :subtitle="table.subtitle || ''"
        >
          <ManagementDataTable :columns="table.columns || []" :rows="table.rows || []" row-key="name">
            <template v-for="column in table.columns || []" #[`cell-${column.key}`]="{ value }" :key="column.key">
              {{ formatTableCell(column, value) }}
            </template>
          </ManagementDataTable>
        </ManagementSurfaceCard>
      </section>

      <ReportInsightCards :insights="activeInsights" />
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import ReportChartRenderer from '@/components/management/bi/ReportChartRenderer.vue'
import ReportInsightCards from '@/components/management/bi/ReportInsightCards.vue'
import ReportKpiGrid from '@/components/management/bi/ReportKpiGrid.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementBIReport,
  getManagementReportCancellations,
  getManagementReportCashierPerformance,
  getManagementReportCategorySales,
  getManagementReportChannelSplit,
  getManagementReportInventoryValuation,
  getManagementReportInventoryWaste,
  getManagementReportCustomerAnalytics,
  getManagementReportCampaignPerformance,
  getManagementReportWalletSummary,
  getManagementReportCreditTransactions,
  getManagementReportCareFeedback,
  getManagementReportSurveyAnalytics,
  getManagementReportCourierPerformance,
  getManagementReportKitchenPerformance,
  getManagementReportProfitLoss,
  getManagementReportBreakeven,
  getManagementReportModifierUsage,
  getManagementReportOrderStatus,
  getManagementReportPaymentMethods,
  getManagementReportProductMix,
  getManagementReportProductSales,
  getManagementReportSalesHourly,
  getManagementReportSalesSummary,
  getManagementReportSalesTrend,
  getManagementReportShiftSales,
  getManagementReportStockMovements,
  getManagementReportTableSales,
  getManagementReportTopProducts,
  listManagementOrders,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const reportKey = computed(() => String(props.boot.report_key || '').trim())
const reportTitle = computed(() => titleMap[reportKey.value] || 'گزارش')

const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 29)

const filters = reactive({
  date_from: start.toISOString().slice(0, 10),
  date_to: today.toISOString().slice(0, 10),
})

const reportPayload = ref(null)
const loading = ref(false)
const error = ref('')

const titleMap = {
  'sales-summary': 'خلاصه فروش',
  'sales-trend': 'روند فروش',
  'sales-hourly': 'فروش ساعتی',
  'top-products': 'محصولات پرفروش',
  'product-sales': 'فروش محصولات',
  'category-sales': 'فروش دسته‌بندی‌ها',
  'table-sales': 'فروش جایگاه‌ها',
  'shift-sales': 'فروش بر اساس شیفت',
  'payment-methods': 'روش‌های پرداخت',
  'product-mix': 'ترکیب محصولات',
  'order-status': 'وضعیت سفارش‌ها',
  'channel-split': 'کانال‌های فروش',
  'cashier-performance': 'عملکرد اپراتور',
  cancellations: 'لغو سفارش',
  'modifier-usage': 'استفاده از افزودنی‌ها',
  'inventory-valuation': 'ارزش‌گذاری موجودی',
  'stock-movements': 'گردش انبار',
  'inventory-waste': 'ضایعات و اتلاف انبار',
  'customer-analytics': 'تحلیل مشتریان (RFM)',
  'campaign-performance': 'عملکرد کمپین‌ها',
  'wallet-summary': 'گزارش اعتباردهی کیف پول',
  'credit-transactions': 'سوابق کارت اعتباری',
  'care-feedback': 'نظرات سایت',
  'survey-analytics': 'تحلیل نظرسنجی',
  'courier-performance': 'عملکرد پیک‌ها',
  'kitchen-performance': 'عملکرد آشپزخانه',
  'profit-loss': 'سود و زیان',
  'breakeven': 'نقطه سربه‌سر',
}

const apiMap = {
  'sales-summary': getManagementReportSalesSummary,
  'sales-trend': getManagementReportSalesTrend,
  'sales-hourly': getManagementReportSalesHourly,
  'top-products': getManagementReportTopProducts,
  'product-sales': getManagementReportProductSales,
  'category-sales': getManagementReportCategorySales,
  'table-sales': getManagementReportTableSales,
  'shift-sales': getManagementReportShiftSales,
  'payment-methods': getManagementReportPaymentMethods,
  'product-mix': getManagementReportProductMix,
  'order-status': getManagementReportOrderStatus,
  'channel-split': getManagementReportChannelSplit,
  'cashier-performance': getManagementReportCashierPerformance,
  cancellations: getManagementReportCancellations,
  'modifier-usage': getManagementReportModifierUsage,
  'inventory-valuation': getManagementReportInventoryValuation,
  'stock-movements': getManagementReportStockMovements,
  'inventory-waste': getManagementReportInventoryWaste,
  'customer-analytics': getManagementReportCustomerAnalytics,
  'campaign-performance': getManagementReportCampaignPerformance,
  'wallet-summary': getManagementReportWalletSummary,
  'credit-transactions': getManagementReportCreditTransactions,
  'care-feedback': getManagementReportCareFeedback,
  'survey-analytics': getManagementReportSurveyAnalytics,
  'courier-performance': getManagementReportCourierPerformance,
  'kitchen-performance': getManagementReportKitchenPerformance,
  'profit-loss': getManagementReportProfitLoss,
  'breakeven': getManagementReportBreakeven,
}

const chartPalette = Object.freeze({
  primary: 'var(--accent-green)',
  accent: 'var(--accent-gold)',
})

const activeCurrency = computed(() => reportPayload.value?.currency || 'IRR')
const activeMeta = computed(() => reportPayload.value?.meta || null)
const activeKpis = computed(() => reportPayload.value?.kpis || [])
const activeCharts = computed(() => reportPayload.value?.charts || [])
const activeTables = computed(() => reportPayload.value?.tables || [])
const activeInsights = computed(() => reportPayload.value?.insights || [])
const legacyRows = computed(() => reportPayload.value?.rows || [])

const legacyColumns = computed(() => {
  const first = legacyRows.value?.[0]
  return first ? Object.keys(first).map((key) => ({ key, label: prettify(key) })) : []
})

function prettify(key) {
  return String(key || '')
    .replace(/_/g, ' ')
    .replace(/^\w/, (m) => m.toUpperCase())
}

function formatLegacyCell(key, value) {
  if (/(date|created_at|time)/i.test(key)) {
    return formatPersianDate(value, true)
  }
  if (/(sales|amount|ticket|spent|total|line_total)/i.test(key)) {
    return formatMoney(value || 0, activeCurrency.value)
  }
  return value
}

function formatTableCell(column, value) {
  const key = String(column?.key || '')
  const valueType = String(column?.type || '').toLowerCase()
  if (valueType === 'money' || /(sales|amount|total|spent|ticket|line_total)/i.test(key)) {
    return formatMoney(value || 0, activeCurrency.value)
  }
  if (valueType === 'percent') {
    return `${Number(value || 0).toLocaleString('fa-IR')}%`
  }
  if (valueType === 'date' || /(date|created_at|time)/i.test(key)) {
    return formatPersianDate(value, true)
  }
  return value
}

function formatPersianDate(value, withTime = false) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}

function buildFallbackPayload(key, data) {
  const summary = data?.summary || {}
  const rows = data?.rows || []

  const kpis = Object.entries(summary).map(([entryKey, entryValue]) => ({
    key: entryKey,
    label: prettify(entryKey),
    value: Number(entryValue || 0),
    unit: /(sales|amount|spent|total|ticket)/i.test(entryKey) ? 'money' : 'count',
    change_pct: 0,
    trend: 'flat',
  }))

  let chartValues = []
  let chartLabels = []
  if (rows.length) {
    const guessValueKey = ['sales', 'amount', 'value', 'orders', 'usage_count'].find((candidate) => candidate in rows[0])
    const guessLabelKey = ['date', 'hour', 'product_title', 'channel', 'status', 'cashier', 'option'].find(
      (candidate) => candidate in rows[0],
    )
    chartValues = rows.map((row) => Number(row[guessValueKey] || 0))
    chartLabels = rows.map((row) => String(row[guessLabelKey] || '-'))
  }

  return {
    report_key: key,
    title: titleMap[key] || 'گزارش',
    currency: data?.currency || 'IRR',
    meta: {
      date_from: filters.date_from,
      date_to: filters.date_to,
      compare_mode: 'previous_window',
    },
    kpis,
    charts: rows.length
      ? [
          {
            key: 'fallback-chart',
            title: 'نمودار اصلی گزارش',
            type: 'line',
            labels: chartLabels,
            series: [{ key: 'main', label: 'مقدار', color: chartPalette.primary, values: chartValues }],
          },
        ]
      : [],
    tables: [],
    insights: [],
    summary,
    rows,
  }
}

function parseDateKey(value) {
  const raw = String(value || '').slice(0, 10)
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return date
}

function toDateKey(value) {
  const date = parseDateKey(value) || new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function resolvePreviousWindow(dateFrom, dateTo) {
  const start = parseDateKey(dateFrom) || new Date()
  const end = parseDateKey(dateTo) || new Date()
  const orderedStart = start <= end ? start : end
  const orderedEnd = start <= end ? end : start
  const dayMs = 24 * 60 * 60 * 1000
  const days = Math.max(Math.floor((orderedEnd.getTime() - orderedStart.getTime()) / dayMs) + 1, 1)

  const prevEnd = new Date(orderedStart.getTime() - dayMs)
  const prevStart = new Date(prevEnd.getTime() - (days - 1) * dayMs)
  return {
    prevStart: toDateKey(prevStart),
    prevEnd: toDateKey(prevEnd),
  }
}

function buildProductMixRulesFromOrders(orders, { limit = 80, minPairOrders = 2, minBaseOrders = 2 } = {}) {
  const validOrders = (orders || []).filter((order) => {
    const status = String(order?.status || '').toLowerCase()
    return status !== 'cancelled' && Array.isArray(order?.items) && order.items.length > 0
  })

  const totalOrders = validOrders.length
  if (totalOrders <= 1) {
    return []
  }

  const baseCounts = new Map()
  const pairCounts = new Map()

  for (const order of validOrders) {
    const titles = new Set(
      (order.items || [])
        .map((item) => String(item?.title || item?.item_code || '').trim())
        .filter(Boolean),
    )

    const uniqueTitles = Array.from(titles).sort()
    if (uniqueTitles.length <= 1) {
      continue
    }

    for (const title of uniqueTitles) {
      baseCounts.set(title, Number(baseCounts.get(title) || 0) + 1)
    }

    for (const left of uniqueTitles) {
      for (const right of uniqueTitles) {
        if (left === right) {
          continue
        }
        const key = `${left}__${right}`
        pairCounts.set(key, Number(pairCounts.get(key) || 0) + 1)
      }
    }
  }

  const rules = []
  for (const [pairKey, coCountRaw] of pairCounts.entries()) {
    const [left, right] = pairKey.split('__')
    const coCount = Number(coCountRaw || 0)
    const leftCount = Number(baseCounts.get(left) || 0)
    const rightCount = Number(baseCounts.get(right) || 0)

    if (leftCount < minBaseOrders || coCount < minPairOrders) {
      continue
    }

    const confidence = Number(((coCount * 100) / leftCount).toFixed(2))
    const support = Number(((coCount * 100) / totalOrders).toFixed(2))
    const expectedSupport = totalOrders > 0 ? (leftCount * rightCount) / (totalOrders * totalOrders) : 0
    const actualSupport = totalOrders > 0 ? coCount / totalOrders : 0
    const lift = expectedSupport > 0 ? Number((actualSupport / expectedSupport).toFixed(3)) : 0

    rules.push({
      product_title: left,
      paired_product_title: right,
      base_order_count: leftCount,
      paired_order_count: rightCount,
      co_order_count: coCount,
      confidence_percent: confidence,
      support_percent: support,
      lift_score: lift,
    })
  }

  return rules
    .sort((a, b) => {
      if (b.confidence_percent !== a.confidence_percent) {
        return b.confidence_percent - a.confidence_percent
      }
      if (b.co_order_count !== a.co_order_count) {
        return b.co_order_count - a.co_order_count
      }
      return b.support_percent - a.support_percent
    })
    .slice(0, Math.max(Number(limit || 80), 1))
}

async function buildProductMixPayloadClientSide(baseCurrency = 'IRR') {
  const { prevStart, prevEnd } = resolvePreviousWindow(filters.date_from, filters.date_to)
  const [currentOrdersPayload, previousOrdersPayload] = await Promise.all([
    listManagementOrders({
      date_from: filters.date_from,
      date_to: filters.date_to,
      source: '',
      status: '',
    }),
    listManagementOrders({
      date_from: prevStart,
      date_to: prevEnd,
      source: '',
      status: '',
    }),
  ])

  const currentRules = buildProductMixRulesFromOrders(currentOrdersPayload?.orders || [])
  const previousRules = buildProductMixRulesFromOrders(previousOrdersPayload?.orders || [])
  const avgConfidence = Number(
    ((currentRules.reduce((sum, row) => sum + Number(row.confidence_percent || 0), 0) / Math.max(currentRules.length, 1)) || 0).toFixed(2),
  )
  const prevAvgConfidence = Number(
    ((previousRules.reduce((sum, row) => sum + Number(row.confidence_percent || 0), 0) / Math.max(previousRules.length, 1)) || 0).toFixed(2),
  )
  const strongRules = currentRules.filter((row) => Number(row.confidence_percent || 0) >= 50)
  const prevStrongRules = previousRules.filter((row) => Number(row.confidence_percent || 0) >= 50)
  const topRule = currentRules[0] || null
  const chartRows = currentRules.slice(0, 12)

  const summaryRows = []
  const seenBase = new Set()
  for (const row of currentRules) {
    const base = String(row.product_title || '').trim()
    if (!base || seenBase.has(base)) {
      continue
    }
    seenBase.add(base)
    summaryRows.push({
      product_title: row.product_title,
      best_pair_title: row.paired_product_title,
      confidence_percent: row.confidence_percent,
      support_percent: row.support_percent,
      co_order_count: row.co_order_count,
    })
  }

  const kpis = [
    {
      key: 'rules_count',
      label: 'Association Rules',
      value: currentRules.length,
      unit: 'count',
      change_pct:
        previousRules.length > 0
          ? Number((((currentRules.length - previousRules.length) * 100) / previousRules.length).toFixed(1))
          : currentRules.length
            ? 100
            : 0,
      trend: currentRules.length >= previousRules.length ? 'up' : 'down',
      change_label: 'Compared to previous window',
    },
    {
      key: 'avg_confidence',
      label: 'Average Confidence',
      value: avgConfidence,
      unit: 'percent',
      change_pct:
        prevAvgConfidence > 0
          ? Number((((avgConfidence - prevAvgConfidence) * 100) / prevAvgConfidence).toFixed(1))
          : avgConfidence
            ? 100
            : 0,
      trend: avgConfidence >= prevAvgConfidence ? 'up' : 'down',
      change_label: 'Compared to previous window',
    },
    {
      key: 'strong_rules',
      label: 'Rules >= 50% Confidence',
      value: strongRules.length,
      unit: 'count',
      change_pct:
        prevStrongRules.length > 0
          ? Number((((strongRules.length - prevStrongRules.length) * 100) / prevStrongRules.length).toFixed(1))
          : strongRules.length
            ? 100
            : 0,
      trend: strongRules.length >= prevStrongRules.length ? 'up' : 'down',
      change_label: 'Compared to previous window',
    },
    {
      key: 'top_confidence',
      label: 'Top Confidence',
      value: Number(topRule?.confidence_percent || 0),
      unit: 'percent',
      change_pct: 0,
      trend: 'flat',
      change_label: 'Compared to previous window',
    },
  ]

  return {
    report_key: 'product-mix',
    title: titleMap['product-mix'],
    currency: baseCurrency || 'IRR',
    meta: {
      date_from: filters.date_from,
      date_to: filters.date_to,
      previous_date_from: prevStart,
      previous_date_to: prevEnd,
      compare_mode: 'previous_window',
    },
    summary: {
      rules_count: currentRules.length,
      unique_products: new Set(currentRules.map((row) => row.product_title)).size,
      avg_confidence_percent: avgConfidence,
    },
    rows: currentRules,
    kpis,
    charts: [
      {
        key: 'mix-confidence',
        title: 'Most Frequent Product Combinations',
        subtitle: 'Confidence percent for each basket rule',
        type: 'line',
        unit: 'count',
        labels: chartRows.map((row) => `${row.product_title} + ${row.paired_product_title}`),
        series: [
          {
            key: 'confidence',
            label: 'Confidence %',
            color: chartPalette.primary,
            values: chartRows.map((row) => Number(row.confidence_percent || 0)),
          },
          {
            key: 'support',
            label: 'Support %',
            color: chartPalette.accent,
            values: chartRows.map((row) => Number(row.support_percent || 0)),
          },
        ],
      },
    ],
    tables: [
      {
        key: 'mix-rules',
        title: 'Product Mix Rules',
        subtitle: 'Example: when customer buys A, how often they also buy B',
        columns: [
          { key: 'product_title', label: 'Product Title', type: 'text' },
          { key: 'paired_product_title', label: 'Paired Product Title', type: 'text' },
          { key: 'base_order_count', label: 'Base Order Count', type: 'count' },
          { key: 'paired_order_count', label: 'Paired Order Count', type: 'count' },
          { key: 'co_order_count', label: 'Co Order Count', type: 'count' },
          { key: 'confidence_percent', label: 'Confidence Percent', type: 'percent' },
          { key: 'support_percent', label: 'Support Percent', type: 'percent' },
          { key: 'lift_score', label: 'Lift Score', type: 'count' },
        ],
        rows: currentRules,
      },
      {
        key: 'mix-summary',
        title: 'Best Cross-Sell Pair per Product',
        columns: [
          { key: 'product_title', label: 'Product Title', type: 'text' },
          { key: 'best_pair_title', label: 'Best Pair Title', type: 'text' },
          { key: 'confidence_percent', label: 'Confidence Percent', type: 'percent' },
          { key: 'support_percent', label: 'Support Percent', type: 'percent' },
          { key: 'co_order_count', label: 'Co Order Count', type: 'count' },
        ],
        rows: summaryRows.slice(0, 20),
      },
    ],
    insights: topRule
      ? [
          {
            key: 'top-mix',
            severity: 'success',
            text: `${topRule.product_title} مشتری ها ${topRule.confidence_percent}% مواقع ${topRule.paired_product_title} هم میخرند.`,
          },
        ]
      : [],
  }
}

function isStaleProductMixPayload(payload) {
  if (reportKey.value !== 'product-mix') {
    return false
  }
  const first = payload?.rows?.[0]
  if (!first || typeof first !== 'object') {
    return false
  }
  if ('paired_product_title' in first || 'confidence_percent' in first) {
    return false
  }
  return 'amount' in first || 'share_percent' in first || 'qty' in first
}

async function loadReport() {
  const legacyFn = apiMap[reportKey.value]
  if (!legacyFn) {
    error.value = 'گزارش نامعتبر است.'
    reportPayload.value = null
    return
  }

  loading.value = true
  error.value = ''

  try {
    const payload = await getManagementBIReport(reportKey.value, {
      date_from: filters.date_from,
      date_to: filters.date_to,
      compare_mode: 'previous_window',
    })
    if (isStaleProductMixPayload(payload)) {
      reportPayload.value = await buildProductMixPayloadClientSide(payload?.currency || 'IRR')
    } else {
      reportPayload.value = payload
    }
  } catch (biErr) {
    try {
      const legacyData = await legacyFn({
        date_from: filters.date_from,
        date_to: filters.date_to,
      })
      if (isStaleProductMixPayload(legacyData)) {
        reportPayload.value = await buildProductMixPayloadClientSide(legacyData?.currency || 'IRR')
      } else {
        reportPayload.value = buildFallbackPayload(reportKey.value, legacyData)
      }
    } catch (legacyErr) {
      error.value = legacyErr.message || biErr.message || 'دریافت گزارش ناموفق بود.'
    }
  } finally {
    loading.value = false
  }
}

loadReport()
</script>

<style scoped>
.filters {
  display: flex;
  align-items: end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filters label {
  min-width: 160px;
  display: grid;
  gap: 0.2rem;
  font-size: 0.78rem;
}

.window-line {
  margin: 0.55rem 0 0;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.charts-grid,
.tables-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 980px) {
  .charts-grid,
  .tables-grid {
    grid-template-columns: 1fr;
  }
}
</style>
