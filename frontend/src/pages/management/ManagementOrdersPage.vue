<template>
  <ManagementPageScaffold title="مدیریت سفارش‌ها" subtitle="پایش سفارش‌ها، پرداخت و وضعیت تحویل">
    <ManagementSurfaceCard v-if="!isOrderDetailView" tone="accent">
      <div class="filters">
        <label>
          منبع
          <SearchableDropdown
            v-model="filters.source"
            :options="sourceOptions"
            placeholder="انتخاب منبع"
            search-placeholder="جستجوی منبع..."
          />
        </label>
        <label>
          وضعیت
          <SearchableDropdown
            v-model="filters.status"
            :options="statusOptions"
            placeholder="انتخاب وضعیت"
            search-placeholder="جستجوی وضعیت..."
          />
        </label>
        <button class="primary-btn" type="button" @click="loadOrders">اعمال فیلتر</button>
      </div>

      <div class="mobile-overview">
        <div class="mobile-stats">
          <div class="stat-card">
            <p class="stat-value">{{ toFaDigits(getTabCount('all')) }}</p>
            <p class="stat-label">کل سفارش‌ها</p>
          </div>
          <div class="stat-card stat-card--paid">
            <p class="stat-value">{{ toFaDigits(getTabCount('paid_only')) }}</p>
            <p class="stat-label">پرداخت شده</p>
          </div>
          <div class="stat-card stat-card--done">
            <p class="stat-value">{{ toFaDigits(getTabCount('delivered')) }}</p>
            <p class="stat-label">تحویل شده</p>
          </div>
        </div>

        <div class="mobile-tabs">
          <button
            v-for="tab in mobileTabs"
            :key="tab.value"
            type="button"
            class="tab-pill"
            :class="{ 'tab-pill--active': activeTab === tab.value }"
            @click="activeTab = tab.value"
          >
            {{ tab.label }}
            <span class="tab-count">{{ toFaDigits(getTabCount(tab.value)) }}</span>
          </button>
        </div>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard
      v-if="isOrderDetailView && selectedOrder"
      :title="`جزئیات سفارش ${selectedOrder.order.order_code}`"
      subtitle="نمای کامل سفارش"
    >
      <div class="row-actions">
        <a class="secondary-btn" href="/desk/orders">بازگشت به لیست سفارش‌ها</a>
      </div>
      <p class="muted">وضعیت: {{ formatStatus(selectedOrder.order.status) }} | کانال: {{ selectedOrder.order.channel }}</p>
      <p class="muted">
        پرداخت: {{ selectedOrder.order.payment_status || '-' }} | روش:
        {{ selectedOrder.order.payment_method || '-' }} | مرجع:
        {{ selectedOrder.order.payment_reference || '-' }}
      </p>

      <div class="payment-actions" v-if="selectedOrder.order.source === 'web'">
        <input class="input" v-model="manualPayment.reference_no" placeholder="مرجع پرداخت" />
        <input class="input" v-model="manualPayment.rrn" placeholder="RRN" />
        <button
          class="primary-btn"
          type="button"
          @click="markOrderPaid(selectedOrder.order)"
          :disabled="isPayDisabled(selectedOrder.order)"
        >
          {{ updatingOrderAction ? 'در حال انجام...' : 'پرداخت سفارش' }}
        </button>
        <button
          class="success-btn"
          type="button"
          @click="completeOrder(selectedOrder.order)"
          :disabled="isCompleteDisabled(selectedOrder.order)"
        >
          {{ updatingOrderAction ? 'در حال انجام...' : 'تکمیل سفارش' }}
        </button>
      </div>

      <ManagementDataTable :columns="detailColumns" :rows="selectedOrder.order.items || []">
        <template #cell-line_total="{ value }">{{ formatMoney(value, currency) }}</template>
      </ManagementDataTable>
    </ManagementSurfaceCard>
    <ManagementSurfaceCard v-else-if="isOrderDetailView && !loading" title="جزئیات سفارش">
      <p class="muted">جزئیات سفارش در دسترس نیست.</p>
      <div class="row-actions">
        <a class="secondary-btn" href="/desk/orders">بازگشت به لیست سفارش‌ها</a>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">{{ isOrderDetailView ? 'در حال بارگذاری جزئیات سفارش...' : 'در حال بارگذاری سفارش‌ها...' }}</p>
    <p class="error" v-if="error">{{ error }}</p>

    <ManagementSurfaceCard title="لیست سفارش‌ها" v-if="!loading && !isOrderDetailView" class="desktop-table">
      <ManagementDataTable :columns="columns" :rows="displayOrders" :row-key="(row) => `${row.source}-${row.name}`">
        <template #cell-status="{ value }">{{ formatStatus(value) }}</template>
        <template #cell-grand_total="{ value }">{{ formatMoney(value, currency) }}</template>
        <template #cell-created_at="{ value }">{{ formatDateTime(value) }}</template>
        <template #cell-payment="{ row }">{{ row.payment_status || '-' }} / {{ row.payment_method || '-' }}</template>
        <template #cell-actions="{ row }">
          <div class="row-actions">
            <button class="secondary-btn" type="button" @click="openOrderDetail(row)">جزئیات</button>
            <button class="primary-btn" type="button" @click="markOrderPaid(row)" :disabled="isPayDisabled(row)">
              پرداخت سفارش
            </button>
            <button class="success-btn" type="button" @click="completeOrder(row)" :disabled="isCompleteDisabled(row)">
              تکمیل سفارش
            </button>
          </div>
        </template>
      </ManagementDataTable>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="سفارش‌ها" v-if="!loading && !isOrderDetailView" class="mobile-cards">
      <ManagementMobileCardList
        class="order-card-list"
        :rows="displayOrders"
        :row-key="(row) => `m-${row.source}-${row.name}`"
        card-class="order-card"
        empty-text="در این فیلتر سفارشی ثبت نشده است."
      >
        <template #card="{ row }">
          <div class="order-card__head">
            <div>
              <p class="order-code">{{ row.order_code }}</p>
              <p class="order-meta">{{ row.customer_name || '-' }} • {{ formatDateTime(row.created_at) }}</p>
            </div>
            <span class="status-chip">{{ formatStatus(row.status) }}</span>
          </div>

          <div class="order-card__totals">
            <p>{{ formatMoney(row.grand_total, currency) }}</p>
            <p>{{ row.payment_status || '-' }} / {{ row.payment_method || '-' }}</p>
          </div>

          <div class="row-actions">
            <button class="secondary-btn" type="button" @click="openOrderDetail(row)">جزئیات</button>
            <button class="primary-btn" type="button" @click="markOrderPaid(row)" :disabled="isPayDisabled(row)">
              پرداخت سفارش
            </button>
            <button class="success-btn" type="button" @click="completeOrder(row)" :disabled="isCompleteDisabled(row)">
              تکمیل سفارش
            </button>
          </div>
        </template>
      </ManagementMobileCardList>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementMobileCardList from '@/components/management/ManagementMobileCardList.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { completeManagementOrder, getManagementOrderDetail, listManagementOrders, markManagementOrderPaid } from '@/utils/api'
import { formatMoney, formatStatus, parseQuery } from '@/utils/format'

const query = parseQuery()
const detailOrderName = ref(String(query.order_name || query.order || '').trim())
const detailOrderSource = ref(String(query.source || '').trim())

const loading = ref(false)
const error = ref('')
const orders = ref([])
const selectedOrder = ref(null)
const currency = ref('IRR')
const updatingOrderAction = ref(false)
const activeTab = ref('all')
const manualPayment = reactive({
  reference_no: '',
  rrn: '',
})

const filters = reactive({
  source: '',
  status: '',
})

const sourceOptions = [
  { value: '', label: 'همه' },
  { value: 'web', label: 'سفارش آنلاین' },
  { value: 'table', label: 'سفارش میز' },
]

const statusOptions = [
  { value: '', label: 'همه' },
  { value: 'new', label: 'جدید' },
  { value: 'confirmed', label: 'تایید شده' },
  { value: 'preparing', label: 'در حال آماده سازی' },
  { value: 'ready', label: 'آماده تحویل' },
  { value: 'delivered', label: 'تحویل شده' },
  { value: 'cancelled', label: 'لغو شده' },
]

const mobileTabs = [
  { value: 'all', label: 'همه' },
  { value: 'open', label: 'جاری' },
  { value: 'paid_only', label: 'پرداخت شده' },
  { value: 'delivered', label: 'تحویل شده' },
  { value: 'cancelled', label: 'لغو شده' },
]

const columns = [
  { key: 'order_code', label: 'کد' },
  { key: 'customer_name', label: 'مشتری' },
  { key: 'channel', label: 'کانال' },
  { key: 'status', label: 'وضعیت' },
  { key: 'payment', label: 'پرداخت' },
  { key: 'grand_total', label: 'مبلغ' },
  { key: 'created_at', label: 'تاریخ' },
  { key: 'actions', label: 'عملیات' },
]

const detailColumns = [
  { key: 'title', label: 'آیتم' },
  { key: 'qty', label: 'تعداد' },
  { key: 'line_total', label: 'قیمت' },
]
const isOrderDetailView = computed(() => Boolean(detailOrderName.value))

const displayOrders = computed(() => {
  if (activeTab.value === 'all') {
    return orders.value
  }
  if (activeTab.value === 'delivered') {
    return orders.value.filter((row) => String(row.status || '').toLowerCase() === 'delivered')
  }
  if (activeTab.value === 'cancelled') {
    return orders.value.filter((row) => String(row.status || '').toLowerCase() === 'cancelled')
  }
  if (activeTab.value === 'paid_only') {
    return orders.value.filter((row) => {
      const paid = String(row.payment_status || '').toLowerCase() === 'paid'
      const delivered = String(row.status || '').toLowerCase() === 'delivered'
      return paid && !delivered
    })
  }
  if (activeTab.value === 'open') {
    return orders.value.filter((row) => {
      const status = String(row.status || '').toLowerCase()
      return !['delivered', 'cancelled'].includes(status)
    })
  }
  return orders.value
})

function getTabCount(tab) {
  if (tab === 'all') {
    return orders.value.length
  }
  return displayOrdersBy(tab).length
}

function displayOrdersBy(tab) {
  if (tab === 'delivered') {
    return orders.value.filter((row) => String(row.status || '').toLowerCase() === 'delivered')
  }
  if (tab === 'cancelled') {
    return orders.value.filter((row) => String(row.status || '').toLowerCase() === 'cancelled')
  }
  if (tab === 'paid_only') {
    return orders.value.filter((row) => {
      const paid = String(row.payment_status || '').toLowerCase() === 'paid'
      const delivered = String(row.status || '').toLowerCase() === 'delivered'
      return paid && !delivered
    })
  }
  if (tab === 'open') {
    return orders.value.filter((row) => {
      const status = String(row.status || '').toLowerCase()
      return !['delivered', 'cancelled'].includes(status)
    })
  }
  return orders.value
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch (error) {
    return value
  }
}

function toFaDigits(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

function isWebOrder(order) {
  return String(order?.source || '').toLowerCase() === 'web'
}

function isPayDisabled(order) {
  const paid = String(order?.payment_status || '').toLowerCase() === 'paid'
  return updatingOrderAction.value || !isWebOrder(order) || paid
}

function isCompleteDisabled(order) {
  const delivered = String(order?.status || '').toLowerCase() === 'delivered'
  return updatingOrderAction.value || !isWebOrder(order) || delivered
}

async function loadOrders() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementOrders({
      source: filters.source,
      status: filters.status,
    })
    orders.value = payload.orders || []
  } catch (errObj) {
    error.value = errObj.message || 'بارگذاری سفارش‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function loadOrderDetail(orderName, source = '') {
  const normalizedOrderName = String(orderName || '').trim()
  if (!normalizedOrderName) {
    return
  }
  error.value = ''
  loading.value = true
  try {
    const payload = await getManagementOrderDetail(normalizedOrderName, String(source || '').trim())
    selectedOrder.value = payload
    detailOrderName.value = String(payload?.order?.name || normalizedOrderName).trim()
    detailOrderSource.value = String(payload?.order?.source || source || '').trim()
    currency.value = String(payload?.order?.currency || currency.value || 'IRR').trim() || 'IRR'
    manualPayment.reference_no = payload?.order?.payment_reference || ''
    manualPayment.rrn = payload?.order?.payment_rrn || ''
  } catch (errObj) {
    error.value = errObj.message || 'دریافت جزئیات سفارش ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function openOrderDetail(row) {
  const orderName = String(row?.name || row?.order_code || '').trim()
  if (!orderName) {
    return
  }
  const source = String(row?.source || '').trim()
  const params = new URLSearchParams()
  params.set('order_name', orderName)
  if (source) {
    params.set('source', source)
  }
  window.location.href = `/desk/orders?${params.toString()}`
}

async function markOrderPaid(order) {
  if (!order?.name) {
    return
  }
  updatingOrderAction.value = true
  error.value = ''
  try {
    await markManagementOrderPaid({
      order_name: order.name,
      reference_no: manualPayment.reference_no,
      rrn: manualPayment.rrn,
      provider_payload: { source: 'management-orders-page' },
    })
    if (isOrderDetailView.value) {
      await loadOrderDetail(order.name, order.source || detailOrderSource.value)
    } else {
      await loadOrders()
    }
  } catch (errObj) {
    error.value = errObj.message || 'ثبت پرداخت سفارش ناموفق بود.'
  } finally {
    updatingOrderAction.value = false
  }
}

async function completeOrder(order) {
  if (!order?.name) {
    return
  }
  updatingOrderAction.value = true
  error.value = ''
  try {
    await completeManagementOrder({
      order_name: order.name,
      reference_no: manualPayment.reference_no,
      rrn: manualPayment.rrn,
      provider_payload: { source: 'management-orders-page' },
    })
    if (isOrderDetailView.value) {
      await loadOrderDetail(order.name, order.source || detailOrderSource.value)
    } else {
      await loadOrders()
    }
  } catch (errObj) {
    error.value = errObj.message || 'تکمیل سفارش ناموفق بود.'
  } finally {
    updatingOrderAction.value = false
  }
}

if (isOrderDetailView.value) {
  loadOrderDetail(detailOrderName.value, detailOrderSource.value)
} else {
  loadOrders()
}
</script>

<style scoped>
.filters {
  display: flex;
  gap: 0.5rem;
  align-items: end;
  flex-wrap: wrap;
}

.filters label {
  min-width: 160px;
  display: grid;
  gap: 0.2rem;
  font-size: 0.78rem;
}

.mobile-overview {
  display: none;
}

.mobile-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(13, 66, 142, 0.12);
  border-radius: 0.85rem;
  text-align: center;
  padding: 0.5rem 0.3rem;
}

.stat-card--paid {
  border-color: rgba(57, 121, 196, 0.24);
}

.stat-card--done {
  border-color: rgba(24, 143, 89, 0.28);
}

.stat-value {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
}

.stat-label {
  margin: 0.1rem 0 0;
  font-size: 0.65rem;
  color: rgba(16, 24, 40, 0.76);
}

.mobile-tabs {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.tab-pill {
  border: 1px solid rgba(14, 76, 154, 0.2);
  border-radius: 0.7rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--management-ink);
  padding: 0.38rem 0.6rem;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  gap: 0.28rem;
  align-items: center;
  white-space: nowrap;
}

.tab-pill--active {
  background: var(--accent-green);
  color: #fff;
  border-color: transparent;
}

.tab-count {
  font-size: 0.65rem;
  padding: 0.12rem 0.28rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
}

.desktop-table {
  display: block;
}

.mobile-cards {
  display: none;
}

.order-card-list {
  display: grid;
  gap: 0.6rem;
}

.order-card {
  border: 1px solid rgba(11, 68, 139, 0.12);
  border-radius: 0.95rem;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.65rem;
  display: grid;
  gap: 0.45rem;
}

.order-card__head {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: start;
}

.order-code {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 800;
}

.order-meta {
  margin: 0.2rem 0 0;
  color: rgba(16, 24, 40, 0.74);
  font-size: 0.68rem;
}

.status-chip {
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  font-size: 0.64rem;
  background: rgba(13, 66, 142, 0.14);
  color: #0d428e;
  font-weight: 700;
}

.order-card__totals {
  display: flex;
  justify-content: space-between;
  font-size: 0.74rem;
  color: rgba(16, 24, 40, 0.8);
}

.row-actions {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.payment-actions {
  display: grid;
  grid-template-columns: 1fr 1fr auto auto;
  gap: 0.45rem;
  margin-bottom: 0.5rem;
}

.success-btn {
  border: none;
  border-radius: 0.72rem;
  background: var(--accent-green);
  color: #fff;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
}

.success-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 920px) {
  .filters {
    gap: 0.42rem;
  }

  .mobile-overview {
    display: grid;
    gap: 0.55rem;
    margin-top: 0.65rem;
  }

  .desktop-table {
    display: none;
  }

  .mobile-cards {
    display: block;
  }

  .payment-actions {
    grid-template-columns: 1fr;
  }
}
</style>
