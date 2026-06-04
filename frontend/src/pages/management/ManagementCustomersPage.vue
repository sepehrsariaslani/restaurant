<template>
  <ManagementPageScaffold
    title="مدیریت مشتریان"
    :subtitle="pageSubtitle"
  >
    <!-- Top hero / filters -->
    <ManagementSurfaceCard tone="accent" class="page-hero">
      <div class="hero-header">
        <div class="hero-title-block">
          <span class="hero-kicker">Customer CRM</span>
          <h2>{{ isDetailView ? 'جزئیات مشتری' : 'نمای چندحالته مشتریان' }}</h2>
          <p>
            {{
              isDetailView
                ? 'گزارش خرید، سفارش‌های اخیر و تحلیل رفتاری مشتری'
                : 'جستجو، فیلتر تاریخ و مشاهده مشتریان در چند نما'
            }}
          </p>
        </div>

        <div class="hero-badges" v-if="!isDetailView">
          <span class="hero-badge">
            <strong>{{ customers.length.toLocaleString('fa-IR') }}</strong>
            <small>مشتری</small>
          </span>
          <span class="hero-badge">
            <strong>{{ totalOrders.toLocaleString('fa-IR') }}</strong>
            <small>سفارش</small>
          </span>
          <span class="hero-badge">
            <strong>{{ formatMoney(totalSpent, currency) }}</strong>
            <small>کل خرید</small>
          </span>
        </div>
      </div>

      <div v-if="!isDetailView" class="toolbar-grid">
        <label class="field">
          <span>جستجو مشتری</span>
          <input
            class="input search-field"
            v-model.trim="search"
            placeholder="نام یا موبایل..."
            @keyup.enter="loadCustomers"
          />
        </label>

        <label class="field">
          <span>از تاریخ</span>
          <PersianDateInput v-model="filters.date_from" />
        </label>

        <label class="field">
          <span>تا تاریخ</span>
          <PersianDateInput v-model="filters.date_to" />
        </label>

        <div class="toolbar-actions">
          <button class="primary-btn" type="button" @click="loadCustomers">
            جستجو
          </button>
          <button class="secondary-btn" type="button" @click="resetCustomerFilters">
            ریست فیلتر
          </button>
        </div>
      </div>

      <div v-if="!isDetailView" class="toolbar-secondary">
        <ManagementViewSwitcher v-model="viewMode" :modes="viewModes" />
      </div>

      <div v-else class="detail-toolbar">
        <a class="secondary-btn" href="/management/customers">بازگشت به لیست مشتریان</a>

        <div class="detail-toolbar-filters">
          <label class="field compact">
            <span>از تاریخ</span>
            <PersianDateInput v-model="filters.date_from" />
          </label>

          <label class="field compact">
            <span>تا تاریخ</span>
            <PersianDateInput v-model="filters.date_to" />
          </label>

          <button class="primary-btn" type="button" @click="loadCustomerDetail">
            بروزرسانی گزارش
          </button>
        </div>
      </div>

      <div v-if="isDetailView" class="detail-tabs" role="tablist" aria-label="تب‌های مشتری">
        <button
          v-for="tab in detailTabs"
          :key="`detail-tab-${tab.value}`"
          type="button"
          class="detail-tab-btn"
          :class="{ active: detailTab === tab.value }"
          :aria-selected="detailTab === tab.value"
          @click="setDetailTab(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="muted status-line" v-if="loading">{{ loadingLabel }}</p>
    <p class="error status-line" v-if="error">{{ error }}</p>

    <!-- List view -->
    <template v-if="!isDetailView && !loading">
      <ManagementSurfaceCard
        title="خلاصه فیلتر فعلی"
        subtitle="آمار مشتریان بر اساس بازه انتخاب‌شده"
      >
        <div class="summary-grid">
          <article class="summary-card">
            <small>تعداد مشتری</small>
            <strong>{{ customerSummary.count.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="summary-card">
            <small>تعداد سفارش</small>
            <strong>{{ customerSummary.orders.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="summary-card">
            <small>کل خرید</small>
            <strong>{{ formatMoney(customerSummary.spent, currency) }}</strong>
          </article>
          <article class="summary-card">
            <small>میانگین خرید</small>
            <strong>{{ formatMoney(customerSummary.avgSpent, currency) }}</strong>
          </article>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        title="لیست مشتریان"
        :subtitle="`تعداد: ${customers.length.toLocaleString('fa-IR')} مشتری`"
      >
        <ManagementDataTable
          v-if="viewMode === 'table'"
          :columns="customerColumns"
          :rows="customers"
          :row-key="(row) => `${row.mobile}-${row.customer_name}`"
        >
          <template #cell-customer_name="{ value }">{{ value || 'بدون نام' }}</template>
          <template #cell-mobile="{ value }">{{ value || '-' }}</template>
          <template #cell-orders_count="{ value }">{{ Number(value || 0).toLocaleString('fa-IR') }}</template>
          <template #cell-total_spent="{ value }">{{ formatMoney(value, currency) }}</template>
          <template #cell-last_order_at="{ value }">{{ formatPersianDate(value) }}</template>
          <template #cell-actions="{ row }">
            <button
              class="secondary-btn mini-link-btn"
              type="button"
              @click="openCustomerDetail(row)"
            >
              جزئیات
            </button>
          </template>
        </ManagementDataTable>

        <div v-else-if="viewMode === 'list'" class="customer-list-view">
          <article
            v-for="row in customers"
            :key="`list-customer-${row.mobile}-${row.customer_name}`"
            class="customer-list-item"
            role="button"
            tabindex="0"
            @click="openCustomerDetail(row)"
            @keydown.enter.prevent="openCustomerDetail(row)"
            @keydown.space.prevent="openCustomerDetail(row)"
          >
            <div class="customer-list-meta">
              <div>
                <strong>{{ row.customer_name || 'بدون نام' }}</strong>
                <small>{{ row.mobile || '-' }}</small>
              </div>
              <span class="customer-chip">
                {{ Number(row.orders_count || 0).toLocaleString('fa-IR') }} سفارش
              </span>
            </div>

            <div class="customer-list-stats">
              <span>خرید: {{ formatMoney(row.total_spent, currency) }}</span>
              <span>آخرین خرید: {{ formatPersianDate(row.last_order_at) }}</span>
            </div>

            <button class="secondary-btn mini-link-btn" type="button" @click.stop="openCustomerDetail(row)">
              مشاهده جزئیات
            </button>
          </article>

          <p v-if="!customers.length" class="muted empty-state">
            مشتری‌ای در این بازه پیدا نشد.
          </p>
        </div>

        <div v-else class="customer-grid-view">
          <article
            v-for="row in customers"
            :key="`grid-customer-${row.mobile}-${row.customer_name}`"
            class="customer-grid-card"
            role="button"
            tabindex="0"
            @click="openCustomerDetail(row)"
            @keydown.enter.prevent="openCustomerDetail(row)"
            @keydown.space.prevent="openCustomerDetail(row)"
          >
            <header>
              <div class="customer-avatar">{{ initials(row.customer_name || row.mobile || 'مشتری') }}</div>
              <div class="grid-meta">
                <strong>{{ row.customer_name || 'بدون نام' }}</strong>
                <small>{{ row.mobile || '-' }}</small>
              </div>
            </header>

            <div class="grid-metrics">
              <p>تعداد سفارش: <strong>{{ Number(row.orders_count || 0).toLocaleString('fa-IR') }}</strong></p>
              <p>کل خرید: <strong>{{ formatMoney(row.total_spent, currency) }}</strong></p>
              <p>آخرین خرید: <strong>{{ formatPersianDate(row.last_order_at) }}</strong></p>
            </div>

            <button class="secondary-btn mini-link-btn" type="button" @click.stop="openCustomerDetail(row)">
              مشاهده جزئیات
            </button>
          </article>

          <p v-if="!customers.length" class="muted empty-state">
            مشتری‌ای در این بازه پیدا نشد.
          </p>
        </div>
      </ManagementSurfaceCard>
    </template>

    <!-- Detail view -->
    <template v-if="isDetailView && !loading">
      <ManagementSurfaceCard
        v-if="customerDetail"
        :title="customerDetail.customer?.customer_name || detailCustomerName || 'جزئیات مشتری'"
        :subtitle="customerDetail.customer?.mobile || detailMobile || '-'"
      >
        <div class="customer-detail-header">
          <div class="customer-detail-ident">
            <div class="detail-avatar">
              {{ initials(customerDetail.customer?.customer_name || detailCustomerName || detailMobile || 'مشتری') }}
            </div>

            <div class="detail-ident-text">
              <strong>{{ customerDetail.customer?.customer_name || detailCustomerName || 'بدون نام' }}</strong>
              <small>{{ customerDetail.customer?.mobile || detailMobile || '-' }}</small>
            </div>
          </div>

          <div class="detail-chip-row">
            <span class="detail-chip">
              <strong>{{ formatMoney(customerDetail.customer?.total_spent || 0, currency) }}</strong>
              <small>کل خرید</small>
            </span>
            <span class="detail-chip">
              <strong>{{ Number(customerDetail.customer?.orders_count || 0).toLocaleString('fa-IR') }}</strong>
              <small>سفارش</small>
            </span>
            <span class="detail-chip">
              <strong>{{ formatMoney(customerDetail.customer?.avg_ticket || 0, currency) }}</strong>
              <small>میانگین فاکتور</small>
            </span>
            <span class="detail-chip">
              <strong>{{ Number(customerDetail.customer?.days_since_last_order || 0).toLocaleString('fa-IR') }}</strong>
              <small>روز از آخرین خرید</small>
            </span>
          </div>
        </div>

        <template v-if="detailTab === 'main'">
          <section class="customer-kpis">
            <article>
              <small>کل خرید</small>
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
            <article>
              <small>اولین خرید</small>
              <strong>{{ formatPersianDate(customerDetail.customer?.first_order_at) }}</strong>
            </article>
            <article>
              <small>روز از آخرین خرید</small>
              <strong>{{ Number(customerDetail.customer?.days_since_last_order || 0).toLocaleString('fa-IR') }}</strong>
            </article>
          </section>

          <ManagementSurfaceCard
            title="آخرین سفارش‌های مشتری"
            subtitle="جزئیات سفارش‌های اخیر"
          >
            <ManagementDataTable
              :columns="detailOrderColumns"
              :rows="customerRecentOrders"
              row-key="name"
            >
              <template #cell-status="{ value }">{{ formatStatus(value) }}</template>
              <template #cell-payment_status="{ value }">{{ value || '-' }}</template>
              <template #cell-channel="{ value }">{{ value || '-' }}</template>
              <template #cell-grand_total="{ value }">{{ formatMoney(value, currency) }}</template>
              <template #cell-created_at="{ value }">{{ formatPersianDate(value) }}</template>
              <template #cell-actions="{ row }">
                <a
                  class="secondary-btn mini-link-btn"
                  :href="`/management/orders?order_name=${encodeURIComponent(row.name)}&source=${encodeURIComponent(row.source || 'web')}`"
                >
                  جزئیات سفارش
                </a>
              </template>
            </ManagementDataTable>
          </ManagementSurfaceCard>
        </template>

        <template v-else>
          <ReportKpiGrid :kpis="customerReport.kpis || []" :currency="currency" />

          <section class="charts-grid" v-if="(customerReport.charts || []).length">
            <ReportChartRenderer
              v-for="chart in customerReport.charts || []"
              :key="chart.key || chart.title"
              :chart="chart"
              :currency="currency"
            />
          </section>

          <section class="tables-grid" v-if="(customerReport.tables || []).length">
            <ManagementSurfaceCard
              v-for="table in customerReport.tables || []"
              :key="table.key || table.title"
              :title="table.title || 'جدول'"
            >
              <ManagementDataTable :columns="table.columns || []" :rows="table.rows || []" row-key="name">
                <template
                  v-for="column in table.columns || []"
                  #[`cell-${column.key}`]="{ value }"
                  :key="`col-${table.key}-${column.key}`"
                >
                  {{ formatReportTableCell(column, value) }}
                </template>
              </ManagementDataTable>
            </ManagementSurfaceCard>
          </section>

          <ManagementSurfaceCard title="Insight">
            <ul class="insight-list">
              <li
                v-for="(row, index) in customerReport.insights || []"
                :key="`insight-${index}`"
              >
                {{ row.text }}
              </li>
            </ul>
          </ManagementSurfaceCard>
        </template>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard v-else title="جزئیات مشتری">
        <p class="muted">اطلاعاتی برای این مشتری پیدا نشد.</p>
        <a class="secondary-btn" href="/management/customers">بازگشت</a>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementViewSwitcher from '@/components/management/ManagementViewSwitcher.vue'
import ReportChartRenderer from '@/components/management/bi/ReportChartRenderer.vue'
import ReportKpiGrid from '@/components/management/bi/ReportKpiGrid.vue'
import { getManagementCustomerDetail, listManagementCustomers } from '@/utils/api'
import { formatMoney, formatStatus, parseQuery } from '@/utils/format'

const query = parseQuery()
const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 29)

const loading = ref(false)
const error = ref('')
const currency = ref('IRR')
const customers = ref([])
const customerDetail = ref(null)
const customerReport = ref({ kpis: [], charts: [], tables: [], insights: [] })
const viewMode = ref(String(query.view || 'table').trim() || 'table')
const search = ref(String(query.search || '').trim())
const detailMobile = ref(String(query.mobile || '').trim())
const detailCustomerName = ref(String(query.customer_name || query.customer || '').trim())
const detailTab = ref(String(query.tab || 'main').trim() || 'main')

const filters = reactive({
  date_from: String(query.date_from || start.toISOString().slice(0, 10)),
  date_to: String(query.date_to || today.toISOString().slice(0, 10)),
})

const viewModes = [
  { value: 'table', label: 'جدولی', icon: '☷' },
  { value: 'list', label: 'لیستی', icon: '≡' },
  { value: 'grid', label: 'گرید', icon: '▦' },
]

const detailTabs = [
  { value: 'main', label: 'اطلاعات اصلی' },
  { value: 'reports', label: 'گزارش‌ها' },
]

const customerColumns = [
  { key: 'customer_name', label: 'مشتری' },
  { key: 'mobile', label: 'موبایل' },
  { key: 'orders_count', label: 'تعداد سفارش' },
  { key: 'total_spent', label: 'کل خرید' },
  { key: 'last_order_at', label: 'آخرین سفارش' },
  { key: 'actions', label: 'عملیات' },
]

const detailOrderColumns = [
  { key: 'order_code', label: 'کد سفارش' },
  { key: 'status', label: 'وضعیت' },
  { key: 'payment_status', label: 'پرداخت' },
  { key: 'channel', label: 'کانال' },
  { key: 'grand_total', label: 'مبلغ' },
  { key: 'created_at', label: 'تاریخ' },
  { key: 'actions', label: 'عملیات' },
]

const isDetailView = computed(() => Boolean(detailMobile.value || detailCustomerName.value))
const loadingLabel = computed(() =>
  isDetailView.value ? 'در حال دریافت جزئیات مشتری...' : 'در حال بارگذاری مشتریان...',
)

const customerRecentOrders = computed(() => {
  const rows = Array.isArray(customerDetail.value?.orders) ? customerDetail.value.orders : []
  return rows.slice(0, 60)
})

const pageSubtitle = computed(() =>
  isDetailView.value
    ? 'نمایش جزئیات مشتری، سفارش‌های اخیر و گزارش‌های تحلیلی'
    : 'نمای چندحالته مشتریان + فیلترهای جستجو و تاریخ',
)

const totalOrders = computed(() =>
  customers.value.reduce((sum, row) => sum + Number(row?.orders_count || 0), 0),
)

const totalSpent = computed(() =>
  customers.value.reduce((sum, row) => sum + Number(row?.total_spent || 0), 0),
)

const avgSpent = computed(() =>
  customers.value.length ? totalSpent.value / customers.value.length : 0,
)

const customerSummary = computed(() => ({
  count: customers.value.length,
  orders: totalOrders.value,
  spent: totalSpent.value,
  avgSpent: avgSpent.value,
}))

async function loadCustomers() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementCustomers({
      search: search.value,
      date_from: filters.date_from,
      date_to: filters.date_to,
    })
    customers.value = Array.isArray(payload?.customers) ? payload.customers : []
    syncListQueryInUrl()
  } catch (errObj) {
    error.value = errObj.message || 'بارگذاری مشتریان ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function loadCustomerDetail() {
  if (!detailMobile.value && !detailCustomerName.value) {
    error.value = 'شناسه مشتری نامعتبر است.'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const payload = await getManagementCustomerDetail({
      mobile: detailMobile.value,
      customer_name: detailCustomerName.value,
      date_from: filters.date_from,
      date_to: filters.date_to,
    })

    customerDetail.value = payload || null
    customerReport.value = payload?.report || { kpis: [], charts: [], tables: [], insights: [] }
    detailMobile.value = String(payload?.customer?.mobile || detailMobile.value || '').trim()
    detailCustomerName.value = String(payload?.customer?.customer_name || detailCustomerName.value || '').trim()
    syncDetailQueryInUrl()
  } catch (errObj) {
    customerDetail.value = null
    customerReport.value = { kpis: [], charts: [], tables: [], insights: [] }
    error.value = errObj.message || 'دریافت جزئیات مشتری ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function openCustomerDetail(row) {
  const mobile = String(row?.mobile || '').trim()
  const customerName = String(row?.customer_name || '').trim()

  if (!mobile && !customerName) {
    return
  }

  const params = new URLSearchParams()
  if (mobile) params.set('mobile', mobile)
  if (customerName) params.set('customer_name', customerName)
  params.set('date_from', filters.date_from)
  params.set('date_to', filters.date_to)
  params.set('tab', 'main')

  window.location.href = `/management/customers?${params.toString()}`
}

function setDetailTab(nextTab) {
  const normalized = String(nextTab || '').trim() || 'main'
  detailTab.value = normalized
  syncDetailQueryInUrl()
}

function syncListQueryInUrl() {
  if (typeof window === 'undefined') return

  try {
    const url = new URL(window.location.href)
    const params = new URLSearchParams()

    if (search.value) params.set('search', search.value)
    if (filters.date_from) params.set('date_from', filters.date_from)
    if (filters.date_to) params.set('date_to', filters.date_to)
    if (viewMode.value && viewMode.value !== 'table') params.set('view', viewMode.value)

    const queryString = params.toString()
    const target = `${url.pathname}${queryString ? `?${queryString}` : ''}${url.hash || ''}`
    window.history.replaceState(window.history.state, '', target)
  } catch (urlError) {
    // ignore
  }
}

function syncDetailQueryInUrl() {
  if (typeof window === 'undefined') return

  try {
    const url = new URL(window.location.href)
    const params = new URLSearchParams()

    if (detailMobile.value) params.set('mobile', detailMobile.value)
    if (detailCustomerName.value) params.set('customer_name', detailCustomerName.value)
    if (filters.date_from) params.set('date_from', filters.date_from)
    if (filters.date_to) params.set('date_to', filters.date_to)
    params.set('tab', detailTab.value || 'main')

    const queryString = params.toString()
    const target = `${url.pathname}${queryString ? `?${queryString}` : ''}${url.hash || ''}`
    window.history.replaceState(window.history.state, '', target)
  } catch (urlError) {
    // ignore
  }
}

function resetCustomerFilters() {
  search.value = ''
  filters.date_from = String(start.toISOString().slice(0, 10))
  filters.date_to = String(today.toISOString().slice(0, 10))
  viewMode.value = 'table'
  loadCustomers()
}

function formatPersianDate(value) {
  const raw = String(value || '').trim()
  if (!raw) return '-'

  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}

function formatReportTableCell(column, value) {
  const key = String(column?.key || '').toLowerCase()
  const type = String(column?.type || '').toLowerCase()

  if (
    type === 'money' ||
    /(sales|amount|spent|total|ticket|line_total|price|rate|grand_total)/i.test(key)
  ) {
    return formatMoney(value || 0, currency.value)
  }

  if (type === 'percent' || /percent|rate/i.test(key)) {
    return `${Number(value || 0).toLocaleString('fa-IR')}%`
  }

  if (/(date|time|created_at|last_order_at|first_order_at)/i.test(key)) {
    return formatPersianDate(value)
  }

  if (/(status)/i.test(key)) {
    return formatStatus(value)
  }

  return value === null || value === undefined || value === '' ? '-' : value
}

function initials(value) {
  const raw = String(value || '').trim()
  if (!raw) return 'م'

  const parts = raw.split(/\s+/).filter(Boolean)
  if (!parts.length) return raw.slice(0, 1)
  if (parts.length === 1) return parts[0].slice(0, 1)

  return `${parts[0].slice(0, 1)}${parts[1].slice(0, 1)}`
}

watch(viewMode, () => {
  if (!isDetailView.value) {
    syncListQueryInUrl()
  }
})

watch([search, () => filters.date_from, () => filters.date_to], () => {
  if (!isDetailView.value) {
    syncListQueryInUrl()
  }
})

watch(detailTab, () => {
  if (isDetailView.value) {
    syncDetailQueryInUrl()
  }
})

onMounted(() => {
  if (isDetailView.value) {
    loadCustomerDetail()
  } else {
    loadCustomers()
  }
})
</script>

<style scoped>
.page-hero {
  display: grid;
  gap: 1rem;
}

.hero-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero-title-block {
  display: grid;
  gap: 0.3rem;
}

.hero-kicker {
  width: fit-content;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--module-500) 16%, transparent);
  color: var(--module-title-light);
  font-size: 0.72rem;
  font-weight: 800;
}

:global(.dark) .hero-kicker {
  color: var(--module-title-dark);
}

.hero-title-block h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 900;
  color: var(--text);
}

.hero-title-block p {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
}

.hero-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.hero-badge {
  min-width: 5.8rem;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  display: grid;
  gap: 0.08rem;
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.hero-badge strong {
  font-size: 0.8rem;
}

.hero-badge small {
  color: var(--muted);
  font-size: 0.64rem;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr auto;
  gap: 0.7rem;
  align-items: end;
}

.field {
  display: grid;
  gap: 0.28rem;
  font-size: 0.74rem;
  color: var(--muted);
}

.field span {
  font-weight: 700;
}

.field.compact {
  min-width: 170px;
}

.search-field {
  width: 100%;
}

.toolbar-actions,
.detail-toolbar-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: end;
}

.toolbar-secondary {
  display: flex;
  justify-content: flex-start;
}

.detail-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: end;
}

.detail-tabs {
  display: inline-flex;
  gap: 0.35rem;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 0.25rem;
  background: color-mix(in srgb, var(--bg-card) 90%, transparent);
  box-shadow: var(--shadow-sm);
}

.detail-tab-btn {
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 0.45rem 0.75rem;
  color: var(--muted);
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 800;
}

.detail-tab-btn.active {
  background: var(--module-500);
  color: #fff;
}

.status-line {
  margin: 0.2rem 0 0.7rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.6rem;
}

.summary-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  padding: 0.75rem;
  display: grid;
  gap: 0.16rem;
  box-shadow: var(--shadow-sm);
}

.summary-card small {
  color: var(--muted);
  font-size: 0.72rem;
}

.summary-card strong {
  font-size: 0.9rem;
}

.customer-list-view {
  display: grid;
  gap: 0.55rem;
}

.customer-list-item {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-card) 94%, transparent);
  padding: 0.75rem;
  display: grid;
  gap: 0.55rem;
  cursor: pointer;
  transition: 0.18s ease;
}

.customer-list-item:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--module-500) 32%, var(--border));
  box-shadow: var(--shadow);
}

.customer-list-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.customer-list-meta div {
  display: grid;
  gap: 0.06rem;
}

.customer-list-meta small,
.grid-meta small {
  color: var(--muted);
}

.customer-chip {
  padding: 0.22rem 0.55rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--module-500) 12%, transparent);
  color: var(--module-title-light);
  font-size: 0.7rem;
  font-weight: 800;
}

:global(.dark) .customer-chip {
  color: var(--module-title-dark);
}

.customer-list-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  color: var(--muted);
  font-size: 0.76rem;
}

.customer-grid-view {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
}

.customer-grid-card {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  padding: 0.8rem;
  display: grid;
  gap: 0.6rem;
  cursor: pointer;
  transition: 0.18s ease;
  box-shadow: var(--shadow-sm);
}

.customer-grid-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.customer-grid-card header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.customer-avatar,
.detail-avatar {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--module-500), var(--module-600));
  color: white;
  font-weight: 900;
  flex-shrink: 0;
}

.grid-meta,
.detail-ident-text {
  display: grid;
  gap: 0.05rem;
  min-width: 0;
}

.grid-meta strong,
.detail-ident-text strong {
  font-size: 0.86rem;
}

.grid-metrics {
  display: grid;
  gap: 0.25rem;
}

.grid-metrics p {
  margin: 0;
  color: var(--muted);
  font-size: 0.76rem;
}

.grid-metrics strong {
  color: var(--text);
}

.customer-detail-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.8rem;
}

.customer-detail-ident {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail-ident-text small {
  color: var(--muted);
  font-size: 0.72rem;
}

.detail-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.detail-chip {
  min-width: 6.3rem;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-soft) 70%, transparent);
  display: grid;
  gap: 0.08rem;
  text-align: center;
}

.detail-chip strong {
  font-size: 0.83rem;
}

.detail-chip small {
  color: var(--muted);
  font-size: 0.64rem;
}

.customer-kpis {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.8rem;
}

.customer-kpis article {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  padding: 0.75rem;
  display: grid;
  gap: 0.14rem;
  box-shadow: var(--shadow-sm);
}

.customer-kpis article small {
  color: var(--muted);
  font-size: 0.72rem;
}

.customer-kpis article strong {
  font-size: 0.9rem;
}

.charts-grid,
.tables-grid {
  display: grid;
  gap: 0.75rem;
}

.insight-list {
  margin: 0;
  padding: 0 1rem 0 0;
  display: grid;
  gap: 0.35rem;
  color: var(--text);
}

.empty-state {
  text-align: center;
  padding: 0.75rem 0;
}

.error {
  margin: 0;
  color: var(--danger);
}

.mini-link-btn {
  width: fit-content;
  padding-inline: 0.8rem;
  padding-block: 0.42rem;
  font-size: 0.74rem;
}

@media (max-width: 1100px) {
  .toolbar-grid {
    grid-template-columns: 1fr 1fr;
  }

  .toolbar-actions {
    grid-column: 1 / -1;
  }

  .summary-grid,
  .customer-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .customer-grid-view {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .toolbar-grid,
  .summary-grid,
  .customer-kpis,
  .customer-grid-view {
    grid-template-columns: 1fr;
  }

  .detail-toolbar {
    align-items: stretch;
  }

  .detail-toolbar-filters {
    width: 100%;
  }

  .field.compact {
    min-width: 100%;
  }

  .hero-header {
    flex-direction: column;
  }

  .hero-badges {
    width: 100%;
  }

  .hero-badge {
    flex: 1;
  }

  .customer-list-meta {
    align-items: start;
    flex-direction: column;
  }

  .customer-detail-header {
    flex-direction: column;
  }

  .customer-detail-ident {
    width: 100%;
  }
}
</style>
