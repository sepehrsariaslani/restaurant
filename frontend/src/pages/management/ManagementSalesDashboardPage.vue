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

        <PersianRangeDateInput
          :model-value="{ date_from: filters.date_from, date_to: filters.date_to }"
          placeholder="انتخاب بازه تاریخ..."
          @update:model-value="applyRangeFilter"
        />

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
      <!-- ─── مشتریان برتر (بالای صفحه) ─── -->
      <ManagementSurfaceCard
        v-if="topCustomers.length || customerSearchOptions.length"
        title="مشتریان برتر"
        subtitle="پرفروش‌ترین مشتریان این بازه — برای مشاهده جزئیات فروش هر مشتری، روی آن کلیک کنید"
      >
        <div class="top-customers">
          <div class="top-customers-list">
            <button
              v-for="(customer, idx) in topCustomers"
              :key="customer.customer_name || idx"
              type="button"
              class="top-customer-row"
              :class="{ active: selectedCustomerName === customer.customer_name }"
              @click="selectCustomer(customer)"
            >
              <span class="tc-rank">{{ toFa(idx + 1) }}</span>
              <span class="tc-main">
                <strong>{{ customer.customer_name || 'بدون نام' }}</strong>
                <small>{{ Number(customer.orders_count || 0).toLocaleString('fa-IR') }} سفارش</small>
              </span>
              <span class="tc-amount">{{ formatMoney(customer.total_spent || 0, currency) }}</span>
            </button>
            <p v-if="!topCustomers.length" class="muted">در این بازه مشتری‌ای ثبت نشده است.</p>
          </div>

          <div class="customer-picker">
            <label class="customer-picker-label">
              جستجو و انتخاب مشتری
              <SearchableDropdown
                v-model="selectedCustomerName"
                :options="customerSearchOptions"
                placeholder="نام یا موبایل مشتری..."
                search-placeholder="جستجوی مشتری..."
              />
            </label>

            <div v-if="customerDetailLoading" class="muted customer-picker-loading">در حال دریافت اطلاعات مشتری...</div>
            <p v-else-if="customerDetailError" class="error">{{ customerDetailError }}</p>

            <template v-else-if="customerDetail">
              <div class="customer-detail-kpis">
                <article>
                  <small>فروش کل</small>
                  <strong>{{ formatMoney(customerDetail.customer?.total_spent || 0, currency) }}</strong>
                </article>
                <article>
                  <small>تعداد سفارش</small>
                  <strong>{{ Number(customerDetail.customer?.orders_count || 0).toLocaleString('fa-IR') }}</strong>
                </article>
                <article>
                  <small>میانگین فاکتور</small>
                  <strong>{{ formatMoney(customerDetail.customer?.avg_ticket || 0, currency) }}</strong>
                </article>
                <article>
                  <small>آخرین خرید</small>
                  <strong>{{ formatPersianDate(customerDetail.customer?.last_order_at) }}</strong>
                </article>
              </div>

              <div class="customer-detail-orders" v-if="(customerDetail.orders || []).length">
                <strong class="cdo-title">آخرین سفارش‌های این مشتری</strong>
                <article v-for="order in customerDetail.orders.slice(0, 6)" :key="order.name" class="cdo-row">
                  <span class="cdo-name">{{ order.name }}</span>
                  <span class="cdo-status" :class="`status-${order.status}`">{{ formatStatus(order.status) }}</span>
                  <span class="cdo-time">{{ formatInvoiceDateTime(order.created_at) }}</span>
                  <strong class="cdo-amount">{{ formatMoney(order.grand_total || 0, currency) }}</strong>
                </article>
              </div>
            </template>

            <p v-else class="muted customer-picker-hint">
              مشتری را از لیست برترها انتخاب کنید یا با جستجو پیدا کنید تا فروش او نمایش داده شود.
            </p>
          </div>
        </div>
      </ManagementSurfaceCard>

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

      <!-- ─── روند فروش (ساعتی / روزانه / هفتگی) ─── -->
      <ManagementSurfaceCard
        v-if="trendValues.length"
        title="روند فروش"
        subtitle="تغییرات فروش بر اساس بازه نمایش انتخابی"
      >
        <div class="trend-toolbar">
          <div class="trend-segments" role="tablist" aria-label="بازه نمایش روند">
            <button
              v-for="option in trendOptions"
              :key="option.value"
              type="button"
              class="trend-seg"
              :class="{ active: trendMode === option.value }"
              role="tab"
              :aria-selected="trendMode === option.value"
              @click="trendMode = option.value"
            >
              {{ option.label }}
            </button>
          </div>
          <span class="trend-summary" v-if="trendTotal">
            مجموع: <strong>{{ formatMoney(trendTotal, currency) }}</strong>
          </span>
        </div>

        <SalesHourlyChart
          :values="trendValues"
          :labels="trendLabels"
          :two-row-labels="trendMode === 'hourly'"
          :color="trendColor"
          mode="money"
          :currency="currency"
          :legend-label="trendLegendLabel"
        />
      </ManagementSurfaceCard>

      <!-- ─── چارت روند روزانه و تجمعی ─── -->
      <section class="charts-grid" v-if="trendCharts.length">
        <ReportChartRenderer
          v-for="chart in trendCharts"
          :key="chart.key"
          :chart="chart"
          :currency="currency"
        />
      </section>

      <!-- ─── پرفروش‌ترین محصولات ─── -->
      <section class="charts-grid two-col" v-if="topProductsRows.length">
        <ManagementSurfaceCard title="پرفروش‌ترین محصولات (بر اساس مبلغ)" subtitle="۱۰ محصول برتر از نظر فروش ریالی">
          <ManagementBarList :rows="topProductsRows" mode="money" :currency="currency" />
        </ManagementSurfaceCard>
        <ManagementSurfaceCard title="پرفروش‌ترین محصولات (بر اساس تعداد)" subtitle="۱۰ محصول برتر از نظر تعداد فروش">
          <ManagementBarList :rows="topProductsQtyRows" mode="count" :currency="currency" />
        </ManagementSurfaceCard>
      </section>

      <!-- ─── فروش بر اساس کانال ─── -->
      <section class="charts-grid two-col" v-if="channelRows.length">
        <ManagementSurfaceCard title="فروش بر اساس کانال" subtitle="مبلغ فروش هر کانال">
          <ManagementBarList :rows="channelRows" mode="money" :currency="currency" />
        </ManagementSurfaceCard>
        <ManagementSurfaceCard title="سفارش بر اساس کانال" subtitle="تعداد سفارش هر کانال">
          <ManagementBarList :rows="channelCountRows" mode="count" :currency="currency" />
        </ManagementSurfaceCard>
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
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
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
import SalesHourlyChart from '@/components/management/sales/SalesHourlyChart.vue'
import PersianRangeDateInput from '@/components/PersianRangeDateInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  getManagementCustomerDetail,
  getManagementDashboard,
  getManagementReportSalesTrend,
  getManagementReportSalesHourly,
  getManagementReportTopProducts,
  getManagementReportChannelSplit,
  listManagementCustomers,
} from '@/utils/api'
import { formatMoney, formatStatus, toPersianNumber } from '@/utils/format'

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

// مشتریان برتر و انتخاب مشتری
const topCustomers = ref([])
const customerSearchOptions = ref([])
const selectedCustomerName = ref('')
const customerDetail = ref(null)
const customerDetailLoading = ref(false)
const customerDetailError = ref('')

// حالت نمایش روند: ساعتی / روزانه / هفتگی
const trendMode = ref('daily')
const trendOptions = [
  { value: 'hourly', label: 'ساعتی' },
  { value: 'daily', label: 'روزانه' },
  { value: 'weekly', label: 'هفتگی' },
]

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
  return [
    { key: 'total_sales', label: 'فروش کل', value: summary.total_sales || 0, unit: 'money' },
    { key: 'total_orders', label: 'تعداد سفارش', value: summary.total_orders || 0, unit: 'count' },
    { key: 'avg_ticket', label: 'میانگین فاکتور', value: summary.avg_ticket || 0, unit: 'money' },
    { key: 'total_items', label: 'آیتم فروخته‌شده', value: summary.total_items || 0, unit: 'count' },
  ]
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

// ─── چارت روند: ساعتی / روزانه / هفتگی ───
const hourlySalesValues = computed(() => {
  const chart = (hourlyReport.value?.charts || [])[0]
  return (chart?.series?.[0]?.values || []).map((v) => Number(v || 0))
})

const dailySalesValues = computed(() => {
  const chart = (trendReport.value?.charts || [])[0]
  return (chart?.series?.[0]?.values || []).map((v) => Number(v || 0))
})

const dailyLabels = computed(() => {
  const chart = (trendReport.value?.charts || [])[0]
  return (chart?.labels || []).map((label) => {
    const raw = String(label || '')
    if (!/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw
    try {
      return new Intl.DateTimeFormat('fa-IR-u-ca-persian', { month: 'numeric', day: 'numeric' }).format(new Date(raw))
    } catch (err) {
      return raw
    }
  })
})

// گروه‌بندی هفتگی از داده روزانه
const weeklyData = computed(() => {
  const values = dailySalesValues.value
  const labels = dailyLabels.value
  if (!values.length) return { values: [], labels: [] }
  const weeks = []
  for (let i = 0; i < values.length; i += 7) {
    const chunk = values.slice(i, i + 7)
    const weekLabels = labels.slice(i, i + 7).filter(Boolean)
    weeks.push({
      total: chunk.reduce((sum, v) => sum + Number(v || 0), 0),
      label: weekLabels.length ? `${weekLabels[0]} تا ${weekLabels[weekLabels.length - 1]}` : `هفته ${weeks.length + 1}`,
    })
  }
  return {
    values: weeks.map((w) => w.total),
    labels: weeks.map((w) => w.label),
  }
})

const trendValues = computed(() => {
  if (trendMode.value === 'hourly') return hourlySalesValues.value
  if (trendMode.value === 'weekly') return weeklyData.value.values
  return dailySalesValues.value
})

const trendLabels = computed(() => {
  if (trendMode.value === 'hourly') return null
  if (trendMode.value === 'weekly') return weeklyData.value.labels
  return dailyLabels.value
})

const trendTotal = computed(() => trendValues.value.reduce((sum, v) => sum + Number(v || 0), 0))

const trendColor = computed(() => {
  if (trendMode.value === 'hourly') return '#C97852'
  if (trendMode.value === 'weekly') return '#8A8B63'
  return '#6F7B56'
})

const trendLegendLabel = computed(() => {
  if (trendMode.value === 'hourly') return 'فروش ساعتی'
  if (trendMode.value === 'weekly') return 'فروش هفتگی'
  return 'فروش روزانه'
})

// ─── چارت‌های روند روزانه (از API) ───
const trendCharts = computed(() => localizeCharts(applySystemChartColors((trendReport.value?.charts || []).slice(1, 3))))

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

// ─── پرفروش‌ترین‌ها با رنگ‌های سیستم ───
function chartBarRows(chartIndex, mode) {
  const chart = (topProductsReport.value?.charts || [])[chartIndex]
  const labels = chart?.labels || []
  const values = chart?.series?.[0]?.values || []
  return labels.map((label, idx) => ({
    key: `${label}-${idx}`,
    label,
    value: Number(values[idx] || 0),
    color: SYSTEM_PALETTE[idx % SYSTEM_PALETTE.length],
  }))
}

const topProductsRows = computed(() => chartBarRows(0, 'money'))
const topProductsQtyRows = computed(() => chartBarRows(1, 'count'))

// ─── کانال‌ها با لیبل فارسی و رنگ سیستم ───
const CHANNEL_FA = {
  'dine_in': 'سالن',
  'takeaway': 'بیرون‌بر',
  'delivery': 'پیک',
  'online': 'آنلاین',
  'unknown': 'نامشخص',
}

function channelRowsFrom(chartIndex) {
  const chart = (channelReport.value?.charts || [])[chartIndex]
  const labels = chart?.labels || []
  const values = chart?.series?.[0]?.values || []
  return labels.map((label, idx) => ({
    key: `${label}-${idx}`,
    label: CHANNEL_FA[String(label || '').toLowerCase()] || label,
    value: Number(values[idx] || 0),
    color: SYSTEM_PALETTE[idx % SYSTEM_PALETTE.length],
  }))
}

const channelRows = computed(() => channelRowsFrom(0))
const channelCountRows = computed(() => channelRowsFrom(1))

// ─── وضعیت سفارش‌ها ───
const statusRows = computed(() => {
  const rows = (dashboard.value?.status_breakdown || []).map((row, idx) => ({
    key: row.status || `status-${idx}`,
    label: formatStatus(row.status),
    value: Number(row.orders || 0),
    color: SYSTEM_PALETTE[idx % SYSTEM_PALETTE.length],
  }))
  return rows
})

function toFa(value) {
  return toPersianNumber(value)
}

async function loadTopCustomers() {
  try {
    const payload = await listManagementCustomers({
      date_from: filters.date_from,
      date_to: filters.date_to,
    })
    const rows = Array.isArray(payload?.customers) ? payload.customers : []
    topCustomers.value = rows.slice(0, 5)
    customerSearchOptions.value = rows.map((row) => ({
      value: row.customer_name || '',
      label: `${row.customer_name || 'بدون نام'}${row.mobile ? ` - ${row.mobile}` : ''}`,
    }))
  } catch (err) {
    console.error('Failed to load top customers:', err)
  }
}

async function selectCustomer(customer) {
  const name = String(customer?.customer_name || customer || '').trim()
  if (!name) {
    return
  }
  selectedCustomerName.value = name
  customerDetailLoading.value = true
  customerDetailError.value = ''
  customerDetail.value = null
  try {
    const payload = await getManagementCustomerDetail({
      customer_name: name,
      date_from: filters.date_from,
      date_to: filters.date_to,
    })
    customerDetail.value = payload || null
  } catch (err) {
    customerDetailError.value = err?.message || 'دریافت اطلاعات مشتری ناموفق بود.'
  } finally {
    customerDetailLoading.value = false
  }
}

// اعمال بازه انتخاب‌شده از RangeDatePicker
function applyRangeFilter(range) {
  filters.date_from = String(range?.date_from || '').trim()
  filters.date_to = String(range?.date_to || '').trim()
  if (filters.date_from && filters.date_to) {
    loadAll()
  }
}

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
    await loadTopCustomers()
  } catch (err) {
    error.value = err?.message || 'خطا در بارگذاری داشبورد فروش'
  } finally {
    loading.value = false
  }
}

// انتخاب مشتری از دراپ‌داون جستجو
watch(selectedCustomerName, (name) => {
  const clean = String(name || '').trim()
  if (clean) {
    selectCustomer(clean)
  }
})

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

.global-controls :deep(.persian-range-date-input) {
  width: min(340px, 100%);
  flex: 1 1 280px;
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

/* ─── روند فروش ─── */
.trend-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 0.6rem;
}

.trend-segments {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 999px;
  padding: 0.2rem;
  background: var(--mg-bg-soft, #f0f0ea);
}

.trend-seg {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--mg-text-muted);
  font: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.32rem 0.85rem;
  cursor: pointer;
  transition: all 0.16s ease;
}

.trend-seg.active {
  background: var(--mg-primary, #c97852);
  color: #fff;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary, #c97852) 30%, transparent);
}

.trend-summary {
  font-size: 0.74rem;
  color: var(--mg-text-muted);
}

.trend-summary strong {
  color: var(--mg-text-main);
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

/* ─── مشتریان برتر ─── */
.top-customers {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(340px, 1.4fr);
  gap: 0.9rem;
  align-items: start;
}

@media (max-width: 900px) {
  .top-customers {
    grid-template-columns: 1fr;
  }
}

.top-customers-list {
  display: grid;
  gap: 0.4rem;
}

.top-customer-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.5rem 0.7rem;
  cursor: pointer;
  text-align: right;
  font-family: inherit;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.top-customer-row:hover {
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 50%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 5%, var(--mg-bg-surface) 95%);
}

.top-customer-row.active {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface) 92%);
}

.tc-rank {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 800;
  background: color-mix(in srgb, var(--mg-primary) 13%, transparent);
  color: var(--mg-primary);
}

.tc-main {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 0.1rem;
}

.tc-main strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tc-main small {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.tc-amount {
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--mg-text-main);
  white-space: nowrap;
}

.customer-picker {
  display: grid;
  gap: 0.6rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  background: color-mix(in srgb, var(--mg-bg-surface) 70%, var(--mg-bg-page) 30%);
  padding: 0.75rem;
}

.customer-picker-label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.74rem;
  font-weight: 800;
  color: var(--mg-text-muted);
}

.customer-picker :deep(.searchable-dropdown) {
  width: 100%;
}

.customer-picker-loading {
  font-size: 0.78rem;
}

.customer-picker-hint {
  font-size: 0.75rem;
  margin: 0;
}

.customer-detail-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.5rem;
}

.customer-detail-kpis article {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.55rem 0.7rem;
  display: grid;
  gap: 0.2rem;
}

.customer-detail-kpis small {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.customer-detail-kpis strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
}

.customer-detail-orders {
  display: grid;
  gap: 0.35rem;
}

.cdo-title {
  font-size: 0.74rem;
  color: var(--mg-text-main);
}

.cdo-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-surface);
  padding: 0.4rem 0.6rem;
  font-size: 0.7rem;
  transition: border-color 0.15s ease;
}

.cdo-row:hover {
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 50%, var(--mg-border-light));
}

.cdo-name {
  font-weight: 700;
  color: var(--mg-text-main);
}

.cdo-status {
  font-size: 0.62rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 0.05rem 0.45rem;
  background: var(--mg-bg-soft);
  color: var(--mg-text-muted);
}

.cdo-status.status-paid,
.cdo-status.status-delivered,
.cdo-status.status-completed {
  background: var(--mg-success-bg);
  color: var(--mg-success);
}

.cdo-status.status-cancelled {
  background: color-mix(in srgb, var(--mg-danger) 12%, transparent);
  color: var(--mg-danger);
}

.cdo-time {
  color: var(--mg-text-muted);
}

.cdo-amount {
  margin-inline-start: auto;
  font-size: 0.74rem;
  color: var(--mg-text-main);
}

/* ─── موبایل ─── */
@media (max-width: 640px) {
  .page-breadcrumbs {
    margin-bottom: 0.55rem;
    padding-inline: 0;
  }

  :deep(.management-page) {
    padding: 0 0.6rem;
    gap: 0.8rem;
  }

  .quick-actions {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 0.45rem;
  }

  .kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 0.5rem;
  }

  .top-customers {
    gap: 0.6rem;
  }

  .customer-picker {
    padding: 0.6rem;
  }
}
</style>
