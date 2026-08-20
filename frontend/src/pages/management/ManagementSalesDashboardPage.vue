<template>
  <ManagementBreadcrumbs class="page-breadcrumbs" :items="breadcrumbItems" />
  <ManagementPageScaffold title="داشبورد فروش" subtitle="نمای سریع فروش، میانبرها و نمودارهای تحلیلی">
    <template #actions>
      <button type="button" class="secondary-btn" @click="loadAll" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <ManagementSurfaceCard tone="accent">
      <div class="global-controls">
        <div class="control-meta">
          <strong>بازه گزارش</strong>
          <small>{{ todayLabel }}</small>
        </div>

        <label>
          از تاریخ
          <PersianDateInput v-model="filters.date_from" />
        </label>

        <label>
          تا تاریخ
          <PersianDateInput v-model="filters.date_to" />
        </label>

        <button type="button" class="primary-btn" @click="loadAll" :disabled="loading">اجرای فیلتر</button>
      </div>
      <p class="window-line">{{ rangeLabel }}</p>
    </ManagementSurfaceCard>

    <!-- ─── دسترسی سریع ─── -->
    <ManagementSurfaceCard title="دسترسی سریع" subtitle="میانبرهای پرکاربرد فروش">
      <div class="quick-actions">
        <a class="quick-action" href="/management/pos">
          <span class="qa-icon qa-pos"><PosIcon :size="19" /></span>
          <strong>صندوق POS</strong>
          <small>ثبت فاکتور حضوری</small>
        </a>
        <a class="quick-action" href="/management/orders">
          <span class="qa-icon qa-orders"><OrdersIcon :size="19" /></span>
          <strong>سفارش‌ها</strong>
          <small>مشاهده و پیگیری</small>
        </a>
        <a class="quick-action" href="/management/customers">
          <span class="qa-icon qa-customers"><UsersIcon :size="19" /></span>
          <strong>مشتریان</strong>
          <small>لیست و جزئیات</small>
        </a>
        <a class="quick-action" href="/management/products">
          <span class="qa-icon qa-products"><ProductsIcon :size="19" /></span>
          <strong>محصولات</strong>
          <small>منو و قیمت</small>
        </a>
        <a class="quick-action" href="/management/reports">
          <span class="qa-icon qa-reports"><ReportsIcon :size="19" /></span>
          <strong>گزارش عملکرد</strong>
          <small>تحلیل کامل</small>
        </a>
        <a class="quick-action" href="/management/pos-defaults">
          <span class="qa-icon qa-settings"><SettingsIcon :size="19" /></span>
          <strong>پیش‌فرض‌های POS</strong>
          <small>چاپ و مشتری</small>
        </a>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری داشبورد فروش...</p>
    <p class="error" v-if="error">{{ error }}</p>

    <template v-if="!loading && !error">
      <!-- ─── KPI ها ─── -->
      <section class="kpi-grid" v-if="kpis.length">
        <article class="kpi-card" :class="`kpi-${kpi.key}`" v-for="kpi in kpis" :key="kpi.key">
          <small>{{ kpi.label }}</small>
          <strong>{{ formatKpiValue(kpi) }}</strong>
          <div class="meta-row">
            <span class="change" :class="trendClass(kpi.trend)">{{ formatChange(kpi.change_pct) }}</span>
            <small>{{ kpi.change_label || 'نسبت به بازه قبل' }}</small>
          </div>
        </article>
      </section>

      <!-- ─── چارت‌ها ─── -->
      <section class="charts-grid">
        <ReportChartRenderer
          v-for="chart in trendCharts"
          :key="chart.key"
          :chart="chart"
          :currency="currency"
        />
        <ReportChartRenderer
          v-for="chart in hourlyCharts"
          :key="chart.key"
          :chart="chart"
          :currency="currency"
        />
      </section>

      <section class="charts-grid two-col">
        <ReportChartRenderer
          v-for="chart in topProductsCharts"
          :key="chart.key"
          :chart="chart"
          :currency="currency"
        />
        <ReportChartRenderer
          v-for="chart in channelCharts"
          :key="chart.key"
          :chart="chart"
          :currency="currency"
        />
      </section>

      <!-- ─── وضعیت سفارش‌ها ─── -->
      <ManagementSurfaceCard
        v-if="statusRows.length"
        title="وضعیت سفارش‌ها"
        subtitle="توزیع سفارش‌های بازه انتخابی"
      >
        <ManagementBarList
          :rows="statusRows"
          mode="count"
          :currency="currency"
        />
      </ManagementSurfaceCard>

      <!-- ─── سفارش‌های اخیر ─── -->
      <ManagementSurfaceCard
        v-if="recentOrders.length"
        title="سفارش‌های اخیر"
        subtitle="آخرین تراکنش‌های ثبت‌شده در این بازه"
      >
        <div class="recent-orders-list">
          <article v-for="order in recentOrders" :key="order.name" class="recent-order-row">
            <div class="ro-main">
              <strong>{{ order.name }}</strong>
              <span>{{ order.customer_name || 'مشتری POS' }}</span>
            </div>
            <div class="ro-meta">
              <span class="order-status-badge" :class="`status-${order.status}`">{{ formatStatus(order.status) }}</span>
              <span class="ro-time">{{ formatInvoiceDateTime(order.created_at) }}</span>
              <strong class="ro-amount">{{ formatMoney(order.grand_total || 0, currency) }}</strong>
            </div>
          </article>
        </div>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  MonitorCog as PosIcon,
  ClipboardList as OrdersIcon,
  Package as ProductsIcon,
  Users as UsersIcon,
  BarChart3 as ReportsIcon,
  Settings as SettingsIcon,
} from 'lucide-vue-next'
import ManagementBreadcrumbs from '@/components/management/ManagementBreadcrumbs.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementBarList from '@/components/management/bi/ManagementBarList.vue'
import ReportChartRenderer from '@/components/management/bi/ReportChartRenderer.vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import {
  getManagementDashboard,
  getManagementReportSalesTrend,
  getManagementReportSalesHourly,
  getManagementReportTopProducts,
  getManagementReportChannelSplit,
} from '@/utils/api'
import { formatMoney, formatStatus } from '@/utils/format'

const loading = ref(false)
const error = ref('')
const currency = ref('IRR')

const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 29)

const filters = reactive({
  date_from: start.toISOString().slice(0, 10),
  date_to: today.toISOString().slice(0, 10),
})

const dashboard = ref(null)
const trendReport = ref(null)
const hourlyReport = ref(null)
const topProductsReport = ref(null)
const channelReport = ref(null)

const breadcrumbItems = [
  { label: 'مدیریت', href: '/management' },
  { label: 'داشبورد فروش' },
]

const todayLabel = computed(() => new Date().toLocaleDateString('fa-IR'))
const rangeLabel = computed(() => {
  const from = formatPersianDate(filters.date_from)
  const to = formatPersianDate(filters.date_to)
  return `از ${from} تا ${to}`
})

function formatPersianDate(value) {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(new Date(value))
  } catch (err) {
    return value
  }
}

function formatInvoiceDateTime(value) {
  if (!value) return '-'
  try {
    const date = new Date(value)
    return `${date.toLocaleDateString('fa-IR')} ${date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}`
  } catch (err) {
    return value
  }
}

const kpis = computed(() => {
  const summary = dashboard.value?.kpis || {}
  const kpiList = [
    {
      key: 'total_sales',
      label: 'فروش کل',
      value: summary.total_sales || 0,
      unit: 'money',
    },
    {
      key: 'total_orders',
      label: 'تعداد سفارش',
      value: summary.total_orders || 0,
      unit: 'count',
    },
    {
      key: 'avg_ticket',
      label: 'میانگین فاکتور',
      value: summary.avg_ticket || 0,
      unit: 'money',
    },
    {
      key: 'total_items',
      label: 'آیتم فروخته‌شده',
      value: summary.total_items || 0,
      unit: 'count',
    },
  ]
  return kpiList
})

function formatKpiValue(kpi) {
  const value = Number(kpi?.value || 0)
  if (kpi.unit === 'money') {
    return formatMoney(value, currency.value)
  }
  return value.toLocaleString('fa-IR')
}

function formatChange(value) {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(1)}%`
}

function trendClass(trend) {
  const normalized = String(trend || '').toLowerCase()
  if (normalized === 'up') return 'up'
  if (normalized === 'down') return 'down'
  return ''
}

const trendCharts = computed(() => localizeCharts(applySystemChartColors((trendReport.value?.charts || []).slice(0, 2))))
const hourlyCharts = computed(() => localizeCharts(applySystemChartColors((hourlyReport.value?.charts || []).slice(0, 2))))
const topProductsCharts = computed(() => localizeCharts(applySystemChartColors((topProductsReport.value?.charts || []).slice(0, 2))))
const channelCharts = computed(() => localizeCharts(applySystemChartColors((channelReport.value?.charts || []).slice(0, 2))))

// پالت رنگ‌های سیستم: سبز موفقیت، نارنجی اصلی، زیتونی
const SYSTEM_PALETTE = ['#6F7B56', '#C97852', '#8A8B63']

function applySystemChartColors(charts = []) {
  return charts.map((chart) => ({
    ...chart,
    series: (chart.series || []).map((series, idx) => ({
      ...series,
      color: SYSTEM_PALETTE[idx % SYSTEM_PALETTE.length] || series.color,
    })),
  }))
}

// ترجمه عنوان چارت‌ها و لیبل سری‌ها به فارسی
const CHART_TITLE_FA = {
  'Sales vs Expected': 'فروش در برابر پیش‌بینی',
  'Cumulative Sales': 'فروش تجمعی',
  'Hourly Sales': 'فروش ساعتی',
  'Hourly Orders': 'سفارش‌های ساعتی',
  'Top Products by Sales': 'پرفروش‌ترین محصولات (بر اساس مبلغ)',
  'Top Products by Quantity': 'پرفروش‌ترین محصولات (بر اساس تعداد)',
  'Sales by Channel': 'فروش بر اساس کانال',
  'Orders by Channel': 'سفارش بر اساس کانال',
  'Sales Trend': 'روند فروش',
  'Top Products': 'پرفروش‌ترین محصولات',
  'Channel Split': 'تفکیک کانال‌ها',
  'Hourly Sales Trend': 'روند فروش ساعتی',
}

const SERIES_LABEL_FA = {
  'Sales': 'فروش',
  'Expected': 'پیش‌بینی',
  'Cumulative': 'تجمعی',
  'Orders': 'سفارش‌ها',
  'Quantity': 'تعداد',
  'Amount': 'مبلغ',
  'Qty': 'تعداد',
  'Count': 'تعداد',
}

function localizeCharts(charts = []) {
  return charts.map((chart) => {
    const title = String(chart.title || '')
    const localizedTitle = CHART_TITLE_FA[title] || title
    const subtitle = String(chart.subtitle || '')
    const localizedSubtitle = CHART_TITLE_FA[subtitle] || SERIES_LABEL_FA[subtitle] || subtitle
    return {
      ...chart,
      title: localizedTitle,
      subtitle: localizedSubtitle || undefined,
      series: (chart.series || []).map((series) => ({
        ...series,
        label: SERIES_LABEL_FA[String(series.label || '')] || series.label,
      })),
    }
  })
}

const statusRows = computed(() => {
  const rows = (dashboard.value?.status_breakdown || []).map((row) => ({
    key: row.status || 'unknown',
    label: formatStatus(row.status),
    value: Number(row.orders || 0),
  }))
  return rows
})

const recentOrders = computed(() => (dashboard.value?.recent_orders || []).slice(0, 8))

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [dash, trend, hourly, topProducts, channels] = await Promise.all([
      getManagementDashboard({
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
      getManagementReportSalesTrend({
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
      getManagementReportSalesHourly({
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
      getManagementReportTopProducts({
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
      getManagementReportChannelSplit({
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
    ])
    dashboard.value = dash
    trendReport.value = trend
    hourlyReport.value = hourly
    topProductsReport.value = topProducts
    channelReport.value = channels
    currency.value = dash?.currency || 'IRR'
  } catch (err) {
    error.value = err?.message || 'خطا در بارگذاری داشبورد فروش'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.page-breadcrumbs {
  margin-bottom: 0.35rem;
  padding-inline: 0.15rem;
}

.global-controls {
  display: flex;
  align-items: flex-end;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.control-meta {
  display: grid;
  gap: 0.15rem;
  margin-inline-end: 0.5rem;
}

.control-meta strong {
  font-size: 0.9rem;
  color: var(--mg-text-main);
}

.control-meta small {
  font-size: 0.72rem;
  color: var(--mg-text-muted);
}

.global-controls label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--mg-text-muted);
}

.window-line {
  margin: 0.5rem 0 0;
  font-size: 0.72rem;
  color: var(--mg-text-muted);
}

/* ─── دسترسی سریع ─── */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.6rem;
}

.quick-action {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  background: var(--mg-bg-surface);
  padding: 0.75rem 0.85rem;
  text-decoration: none;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.quick-action:hover {
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 7%, var(--mg-bg-surface) 93%);
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 60%, var(--mg-border-light));
  transform: translateY(-2px);
}

.quick-action strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
}

.quick-action small {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.qa-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.2rem;
}

.qa-pos {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 13%, transparent);
}

.qa-orders {
  color: var(--mg-success, #6f7b56);
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 14%, transparent);
}

.qa-customers {
  color: var(--mg-olive, #8a8b63);
  background: color-mix(in srgb, var(--mg-olive, #8a8b63) 14%, transparent);
}

.qa-products {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 13%, transparent);
}

.qa-reports {
  color: var(--mg-success, #6f7b56);
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 14%, transparent);
}

.qa-settings {
  color: var(--mg-olive, #8a8b63);
  background: color-mix(in srgb, var(--mg-olive, #8a8b63) 14%, transparent);
}

/* ─── KPI ─── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.7rem;
}

.kpi-card {
  border: 1px solid var(--mg-border-light);
  border-radius: 16px;
  background: var(--mg-bg-surface);
  padding: 0.85rem 1rem;
  display: grid;
  gap: 0.3rem;
  box-shadow: var(--mg-shadow-sm);
  transition: border-color 0.15s ease, background 0.15s ease;
  position: relative;
  overflow: hidden;
}

.kpi-card::before {
  content: '';
  position: absolute;
  inset-inline: 0;
  top: 0;
  height: 3px;
  background: var(--mg-primary);
}

.kpi-total_orders::before,
.kpi-total_items::before {
  background: var(--mg-success, #6f7b56);
}

.kpi-avg_ticket::before {
  background: var(--mg-olive, #8a8b63);
}

.kpi-card:hover {
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 50%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 5%, var(--mg-bg-surface) 95%);
}

.kpi-card small {
  font-size: 0.72rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.kpi-card strong {
  font-size: 1.15rem;
  color: var(--mg-text-main);
}

.kpi-card .meta-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.kpi-card .meta-row small {
  font-size: 0.65rem;
  font-weight: 400;
}

.change {
  font-size: 0.68rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 0.05rem 0.45rem;
}

.change.up {
  color: var(--mg-success);
  background: var(--mg-success-bg);
}

.change.down {
  color: var(--mg-danger);
  background: color-mix(in srgb, var(--mg-danger) 12%, transparent);
}

/* ─── چارت‌ها ─── */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
}

.charts-grid.two-col {
  grid-template-columns: 1fr 1fr;
}

@media (max-width: 1000px) {
  .charts-grid,
  .charts-grid.two-col {
    grid-template-columns: 1fr;
  }
}

/* ─── سفارش‌های اخیر ─── */
.recent-orders-list {
  display: grid;
  gap: 0.4rem;
}

.recent-order-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  padding: 0.5rem 0.75rem;
  background: var(--mg-bg-surface);
  flex-wrap: wrap;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.recent-order-row:hover {
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 50%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 5%, var(--mg-bg-surface) 95%);
}

.ro-main {
  display: grid;
  gap: 0.1rem;
}

.ro-main strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
}

.ro-main span {
  font-size: 0.7rem;
  color: var(--mg-text-muted);
}

.ro-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.ro-time {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.ro-amount {
  font-size: 0.82rem;
  color: var(--mg-text-main);
}

.order-status-badge {
  font-size: 0.64rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
  background: var(--mg-bg-soft);
  color: var(--mg-text-muted);
}

.order-status-badge.status-paid,
.order-status-badge.status-delivered,
.order-status-badge.status-completed {
  background: var(--mg-success-bg);
  color: var(--mg-success);
}

.order-status-badge.status-cancelled {
  background: color-mix(in srgb, var(--mg-danger) 12%, transparent);
  color: var(--mg-danger);
}
</style>
