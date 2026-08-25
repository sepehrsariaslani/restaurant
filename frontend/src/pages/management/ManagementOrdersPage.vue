<template>
  <ManagementPageScaffold title="" subtitle="" :show-title="false">
    
    <div class="workspace-header">
      <div class="header-intro">
        <h1 class="page-title">مدیریت سفارش‌ها</h1>
        <p class="page-subtitle">پایش لحظه‌ای سفارش‌ها، وضعیت پرداخت و پیشرفت تولید</p>
      </div>

      <div class="header-actions">
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model.trim="search"
            class="search-input"
            placeholder="جستجو (کد سفارش، مشتری، موبایل...)"
            @keyup.enter="loadOrders"
          />
        </div>
        <button class="refresh-btn" type="button" :disabled="loading" @click="loadOrders" title="بروزرسانی اطلاعات">
          <RefreshCcw :size="18" :class="{ 'is-spinning': loading }" />
        </button>
      </div>
    </div>

    <!-- Composed KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi-hero">
        <div class="kpi-hero-val">{{ toFaDigits(orders.length) }}</div>
        <div class="kpi-hero-label">کل سفارش‌ها</div>
      </div>
      <div class="kpi-tiles">
        <div class="kpi-tile">
          <span class="kpi-dot new"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('new')) }}</span>
            <span class="kpi-label">جدید</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot preparing"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('preparing')) }}</span>
            <span class="kpi-label">در حال تولید</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot ready"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('ready')) }}</span>
            <span class="kpi-label">آماده تحویل</span>
          </div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-tile">
          <div class="kpi-info">
            <span class="kpi-val">{{ toFaDigits(getTabCount('unpaid')) }}</span>
            <span class="kpi-label">پرداخت نشده</span>
          </div>
        </div>
      </div>
    </div>

    <div class="workspace-tabs-container">
      <div class="workspace-tabs" role="tablist">
        <button
          v-for="tab in mobileTabs"
          :key="tab.value"
          class="workspace-tab"
          :class="{ active: activeTab === tab.value }"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="activeTab = tab.value"
        >
          <span>{{ tab.label }}</span>
          <span class="tab-badge" v-if="getTabCount(tab.value) > 0">{{ toFaDigits(getTabCount(tab.value)) }}</span>
        </button>
      </div>
    </div>

    <p class="muted-loading" v-if="loading && !orders.length">در حال همگام‌سازی سفارش‌ها...</p>
    <div class="workspace-alerts" v-if="error">
      <p class="error-alert"><AlertCircle :size="16" /> {{ error }}</p>
    </div>

    <template v-if="!loading || orders.length">
      <section class="workspace-floor">
        <div class="floor-grid-area">
          <div class="floor-filters">
            <span class="floor-filter-label">فیلتر منبع:</span>
            <button class="floor-chip" :class="{ active: !filters.source }" @click="filters.source = ''; loadOrders()">همه</button>
            <button class="floor-chip" :class="{ active: filters.source === 'web' }" @click="filters.source = 'web'; loadOrders()">آنلاین</button>
            <button class="floor-chip" :class="{ active: filters.source === 'table' }" @click="filters.source = 'table'; loadOrders()">سالن</button>
          </div>

          <div v-if="displayOrders.length" class="order-list">
            <article 
              v-for="row in displayOrders" 
              :key="row.name" 
              class="order-row"
              :class="{ 'is-selected': isOrderDetailView && selectedOrder?.order?.name === row.name }"
              @click="openOrderDetail(row)"
            >
              <div class="order-row-main">
                <div class="order-identity">
                  <strong>{{ row.order_code || row.name }}</strong>
                  <span class="customer-name">{{ row.customer_name || 'مشتری ناشناس' }}</span>
                </div>
                <div class="order-metrics">
                  <span class="order-total" dir="ltr">{{ formatMoney(row.grand_total, currency) }}</span>
                  <div class="order-badges">
                    <span class="status-badge" :class="`status-${(row.status || '').toLowerCase()}`">{{ formatStatus(row.status) }}</span>
                    <span v-if="row.payment_status" class="payment-badge" :class="`pay-${(row.payment_status || '').toLowerCase()}`">
                      {{ row.payment_status }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="order-row-meta">
                <span class="meta-item"><Clock3 :size="14" /> {{ formatDateTime(row.created_at) }}</span>
                <span class="meta-item" v-if="row.channel"><Store :size="14" /> {{ row.channel }}</span>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon-wrapper"><ClipboardList :size="32" /></div>
            <strong>سفارشی یافت نشد</strong>
            <p>در این نما با فیلترهای فعلی موردی وجود ندارد.</p>
            <button v-if="filters.source || search || activeTab !== 'all'" class="secondary-btn mt-2" @click="activeTab = 'all'; search = ''; filters.source = ''; loadOrders()">پاک کردن فیلترها</button>
          </div>
        </div>

        <aside class="floor-detail-area">
          <div class="inspection-panel">
            <div v-if="!isOrderDetailView || !selectedOrder" class="inspection-empty">
              <div class="empty-illustration"><ClipboardList :size="32" /></div>
              <strong>یک سفارش را انتخاب کنید</strong>
              <p>برای مشاهده جزئیات، اقلام فاکتور و عملیات پرداخت، سفارشی را از لیست باز کنید.</p>
            </div>
            
            <template v-else>
              <header class="inspection-head">
                <div class="head-info">
                  <span class="head-kicker">جزئیات سفارش ({{ selectedOrder.order.channel || 'نامشخص' }})</span>
                  <h2>{{ selectedOrder.order.order_code || selectedOrder.order.name }}</h2>
                  <span class="head-location">{{ selectedOrder.order.customer_name || 'مشتری ناشناس' }}</span>
                </div>
                <div class="head-badges">
                  <span class="status-badge" :class="`status-${(selectedOrder.order.status || '').toLowerCase()}`">{{ formatStatus(selectedOrder.order.status) }}</span>
                </div>
              </header>

              <div class="inspection-body">
                <div class="kpi-grid">
                  <div class="kpi-box highlight">
                    <span class="kpi-box-label">مبلغ کل</span>
                    <strong class="kpi-box-value" dir="ltr">{{ formatMoney(selectedOrder.order.grand_total, currency) }}</strong>
                  </div>
                  <div class="kpi-box">
                    <span class="kpi-box-label">وضعیت پرداخت</span>
                    <strong class="kpi-box-value" :class="{'text-danger': selectedOrder.order.payment_status !== 'Paid', 'text-success': selectedOrder.order.payment_status === 'Paid'}">
                      {{ selectedOrder.order.payment_status || 'Unpaid' }}
                    </strong>
                  </div>
                </div>

                <section class="inspection-section mt-4">
                  <h3 class="section-title">اقلام سفارش</h3>
                  <div class="items-list">
                    <div class="item-row" v-for="(item, idx) in selectedOrder.order.items" :key="idx">
                      <div class="item-qty">{{ toFaDigits(item.qty) }}×</div>
                      <div class="item-name">{{ item.title || item.item_name }}</div>
                      <div class="item-price" dir="ltr">{{ formatMoney(item.line_total, currency) }}</div>
                    </div>
                  </div>
                </section>
                
                <section class="inspection-section mt-4" v-if="isDeliveryOrder(selectedOrder.order)">
                  <h3 class="section-title">تحویل و پیک</h3>
                  <div class="courier-assign-row">
                    <select class="input" v-model="courierAssign.courier">
                      <option value="">انتخاب پیک...</option>
                      <option v-for="c in couriers" :key="c.name" :value="c.name">{{ c.courier_name }}</option>
                    </select>
                    <button class="secondary-btn" type="button" :disabled="courierAssign.busy" @click="assignCourier(selectedOrder.order.name)">
                      {{ courierAssign.busy ? '...' : 'تخصیص پیک' }}
                    </button>
                  </div>
                  <p class="courier-assign-msg ok-text" v-if="courierAssign.message">{{ courierAssign.message }}</p>
                  <p class="courier-assign-msg text-danger" v-if="courierAssign.error">{{ courierAssign.error }}</p>
                </section>

                <section class="inspection-section mt-4" v-if="selectedOrder.order.source === 'web' && selectedOrder.order.payment_status !== 'Paid'">
                  <h3 class="section-title">ثبت پرداخت دستی</h3>
                  <div class="form-grid">
                    <div class="form-group full-width">
                      <label>شماره پیگیری (اختیاری)</label>
                      <input class="input" v-model="manualPayment.reference_no" placeholder="Reference No" dir="ltr" />
                    </div>
                    <div class="form-group full-width">
                      <label>RRN (اختیاری)</label>
                      <input class="input" v-model="manualPayment.rrn" placeholder="RRN" dir="ltr" />
                    </div>
                  </div>
                </section>
              </div>

              <footer class="inspection-footer">
                <button 
                  v-if="selectedOrder.order.source === 'web'"
                  class="primary-btn flex-1" 
                  type="button" 
                  :disabled="isPayDisabled(selectedOrder.order)" 
                  @click="markOrderPaid(selectedOrder.order)"
                >
                  <CreditCard :size="16" />
                  <span>{{ updatingOrderAction ? 'در حال ثبت...' : 'ثبت پرداخت' }}</span>
                </button>
                
                <button 
                  v-if="selectedOrder.order.source === 'web'"
                  class="secondary-btn flex-1" 
                  type="button" 
                  :disabled="isCompleteDisabled(selectedOrder.order)" 
                  @click="completeOrder(selectedOrder.order)"
                >
                  <CheckCheck :size="16" />
                  <span>تکمیل سفارش</span>
                </button>
                
                <button
                  class="secondary-btn flex-1"
                  type="button"
                  :disabled="proformaBusy"
                  @click="openProforma(selectedOrder.order)"
                >
                  <FileText :size="16" />
                  <span>{{ proformaBusy ? 'در حال آماده‌سازی...' : 'پیش‌فاکتور' }}</span>
                </button>

                <button class="ghost-btn flex-1" type="button" @click="closeOrderDetail">
                  <X :size="16" />
                  <span>بستن</span>
                </button>
              </footer>
            </template>
          </div>
        </aside>
      </section>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { CheckCheck, CreditCard, FileText, X } from 'lucide-vue-next'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementMobileCardList from '@/components/management/ManagementMobileCardList.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { completeManagementOrder, getManagementOrderDetail, listManagementOrders, markManagementOrderPaid, listManagementCouriers, assignManagementOrderCourier, createManagementOrderProforma } from '@/utils/api'
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

const couriers = ref([])
const courierAssign = reactive({ courier: '', busy: false, message: '', error: '' })

function isDeliveryOrder(order) {
  const channel = String(order?.channel || '').toLowerCase()
  return channel.includes('delivery') || channel.includes('ارسال') || channel.includes('پیک')
}

async function loadCouriersOnce() {
  if (couriers.value.length) return
  try {
    const payload = await listManagementCouriers({ active_only: 1 })
    couriers.value = Array.isArray(payload?.couriers) ? payload.couriers : []
  } catch (errObj) {
    couriers.value = []
  }
}

const proformaBusy = ref(false)

async function openProforma(order) {
  const orderName = order?.name || ''
  if (!orderName || proformaBusy.value) return
  proformaBusy.value = true
  error.value = ''
  try {
    const payload = await createManagementOrderProforma(orderName)
    const printUrl = String(payload?.print_url || '').trim()
    if (printUrl) {
      window.open(printUrl, '_blank', 'noopener')
    }
  } catch (errObj) {
    error.value = errObj?.message || 'صدور پیش‌فاکتور ناموفق بود.'
  } finally {
    proformaBusy.value = false
  }
}

async function assignCourier(orderName) {
  courierAssign.busy = true
  courierAssign.message = ''
  courierAssign.error = ''
  try {
    await assignManagementOrderCourier({ order_name: orderName, courier: courierAssign.courier })
    courierAssign.message = courierAssign.courier ? 'پیک به سفارش اختصاص یافت و وضعیت «تحویل به پیک» شد.' : 'پیک از سفارش برداشته شد.'
    if (selectedOrder.value?.order) selectedOrder.value.order.courier = courierAssign.courier
  } catch (errObj) {
    courierAssign.error = errObj?.message || 'تخصیص پیک ناموفق بود.'
  } finally {
    courierAssign.busy = false
  }
}

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
    courierAssign.courier = payload?.order?.courier || ''
    courierAssign.message = ''
    courierAssign.error = ''
    if (isDeliveryOrder(payload?.order)) loadCouriersOnce()
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
  window.location.href = `/management/orders?${params.toString()}`
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
/* Workflow-based Operational Dashboard Styles */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  color: var(--mg-text-muted);
  font-size: 1rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.search-box {
  position: relative;
  width: 320px;
}

.search-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mg-secondary);
}

.search-input {
  width: 100%;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.85rem 1rem 0.85rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.95rem;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--mg-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--mg-danger-bg);
}

.refresh-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  width: 3.2rem;
  height: 3.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: var(--mg-bg-soft);
  color: var(--mg-primary);
}

/* KPI Strip */
.kpi-strip {
  display: flex;
  gap: 1rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}

.kpi-hero {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.5rem 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-sm);
  min-width: 220px;
}

.kpi-hero-val {
  font-size: 3rem;
  font-weight: 900;
  color: var(--mg-text-main);
  line-height: 1;
}

.kpi-hero-label {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
  margin-top: 0.5rem;
  font-weight: 700;
}

.kpi-tiles {
  display: flex;
  gap: 1rem;
  flex: 1;
  flex-wrap: wrap;
}

.kpi-tile {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
  min-width: 140px;
  border: 1px solid var(--mg-border-light);
}

.kpi-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-top: 0.4rem;
  flex-shrink: 0;
}

.kpi-dot.new { background: var(--mg-danger); } 
.kpi-dot.preparing { background: var(--mg-olive-soft); border: 1px solid var(--mg-olive); } 
.kpi-dot.ready { background: var(--mg-primary); }

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-val {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-top: 0.25rem;
}

.kpi-divider {
  width: 1px;
  background: var(--mg-border-light);
  margin: 0.5rem 0.5rem;
}

/* Tabs Container */
.workspace-tabs-container {
  display: flex;
  margin-bottom: 2rem;
}

.workspace-tabs {
  display: inline-flex;
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 0.35rem;
  gap: 0.25rem;
  border: 1px solid var(--mg-border-light);
  overflow-x: auto;
  max-width: 100%;
}

.workspace-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  border-radius: var(--mg-radius-sm);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.workspace-tab:hover {
  color: var(--mg-text-main);
}

.workspace-tab.active {
  background: var(--mg-bg-page);
  color: var(--mg-primary);
  box-shadow: var(--mg-shadow-sm);
}

.tab-badge {
  background: var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.15rem 0.6rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 800;
}

.workspace-tab.active .tab-badge {
  background: var(--mg-danger-bg);
  color: var(--mg-primary);
}

/* Floor Grid Area */
.workspace-floor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 460px;
  gap: 2.5rem;
  align-items: start;
}

.floor-filters {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.floor-filter-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-left: 0.5rem;
}

.floor-chip {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.4rem 1rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.floor-chip:hover {
  border-color: var(--mg-border);
}

.floor-chip.active {
  background: var(--mg-text-main);
  border-color: var(--mg-text-main);
  color: var(--mg-bg-surface);
}
:global(.dark) .floor-chip.active {
  background: var(--mg-text-main);
  color: var(--mg-bg-surface);
}

/* Order List (Rows instead of cards) */
.order-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.order-row {
  display: flex;
  flex-direction: column;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: right;
  width: 100%;
}

.order-row:hover {
  border-color: var(--mg-border);
  transform: translateX(-3px);
  box-shadow: var(--mg-shadow-sm);
}

.order-row.is-selected {
  background: var(--mg-bg-soft);
  border-color: var(--mg-primary);
  box-shadow: 4px 0 0 0 var(--mg-primary) inset, var(--mg-shadow-sm);
}

.order-row-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.order-identity {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.order-identity strong {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--mg-text-main);
}

.customer-name {
  font-size: 0.9rem;
  color: var(--mg-text-muted);
  font-weight: 600;
}

.order-metrics {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.order-total {
  font-size: 1.15rem;
  font-weight: 900;
  color: var(--mg-primary);
}

.order-badges {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-badge, .payment-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  border: 1px solid transparent;
}

/* Status variants */
.status-new { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }
.status-confirmed, .status-preparing { background: rgba(221, 167, 123, 0.15); color: #8c5e35; border-color: rgba(221, 167, 123, 0.3); }
.status-ready { background: var(--mg-danger-bg); color: var(--mg-primary); border-color: var(--mg-primary); }
.status-delivered { background: var(--mg-bg-soft); color: var(--mg-text-muted); border-color: var(--mg-border-light); }
.status-cancelled { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }

:global(.dark) .status-confirmed, :global(.dark) .status-preparing { background: rgba(221, 167, 123, 0.1); color: #dda77b; border-color: rgba(221, 167, 123, 0.2); }

/* Payment variants */
.pay-paid { background: rgba(110, 118, 74, 0.15); color: var(--mg-success); border-color: rgba(110, 118, 74, 0.3); }
.pay-unpaid { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }

:global(.dark) .pay-paid { background: rgba(110, 118, 74, 0.1); color: #88935c; }

.order-row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--mg-secondary);
  border-top: 1px dashed var(--mg-border-light);
  padding-top: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 600;
}

/* Detail Area */
.floor-detail-area {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
}

.inspection-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-md);
  overflow: hidden;
}

.inspection-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--mg-secondary);
}

.empty-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--mg-bg-page);
  margin-bottom: 1.5rem;
  color: var(--mg-secondary);
  border: 1px solid var(--mg-border-light);
}

.inspection-empty strong {
  color: var(--mg-text-main);
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
}

.inspection-empty p {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--mg-text-muted);
}

.inspection-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.75rem 2rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
}

.head-info {
  display: flex;
  flex-direction: column;
}

.head-kicker {
  font-size: 0.8rem;
  color: var(--mg-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 800;
  margin-bottom: 0.4rem;
}

.head-info h2 {
  margin: 0;
  font-size: 1.8rem;
  color: var(--mg-text-main);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.head-location {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
  margin-top: 0.25rem;
  font-weight: 600;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.kpi-box {
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.kpi-box.highlight {
  background: var(--mg-bg-surface);
  border-color: var(--mg-border);
}

.kpi-box.highlight .kpi-box-value {
  color: var(--mg-primary);
}

.kpi-box-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.kpi-box-value {
  font-size: 1.3rem;
  color: var(--mg-text-main);
  font-weight: 900;
}

.text-danger { color: var(--mg-danger); }
.text-success { color: var(--mg-success); }

.inspection-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--mg-text-main);
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--mg-bg-page);
  padding: 1rem;
  border-radius: var(--mg-radius-sm);
  border: 1px solid var(--mg-border-light);
}

.item-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.75rem;
  font-size: 0.95rem;
  color: var(--mg-text-main);
  font-weight: 600;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--mg-border-light);
}
.item-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.item-qty { color: var(--mg-secondary); font-weight: 800; }
.item-price { color: var(--mg-primary); font-weight: 800; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.input {
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  border-radius: var(--mg-radius-sm);
  padding: 0.75rem 1rem;
  font-family: inherit;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--mg-primary);
  outline: none;
}

.mt-4 { margin-top: 1rem; }

.inspection-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.flex-1 {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  height: 3.2rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.primary-btn {
  background: var(--mg-primary);
  color: #fff;
}
.primary-btn:hover:not(:disabled) {
  background: var(--mg-primary-hover);
}
:global(.dark) .primary-btn { color: var(--mg-text-main); }

.secondary-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
}
.secondary-btn:hover:not(:disabled) {
  background: var(--mg-bg-soft);
}

.ghost-btn {
  background: transparent;
  color: var(--mg-secondary);
}
.ghost-btn:hover {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  background: var(--mg-bg-surface);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1.5rem;
  opacity: 0.6;
}
.empty-state strong {
  font-size: 1.2rem;
  color: var(--mg-text-main);
  margin-bottom: 0.5rem;
  font-weight: 800;
}
.empty-state p {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
}

.workspace-alerts {
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.error-alert, .success-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}
.error-alert {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  border: 1px solid rgba(166, 84, 63, 0.2);
}
.success-alert {
  background: var(--mg-success-soft);
  color: var(--mg-success);
  border: 1px solid rgba(111, 123, 86, 0.25);
}
.muted-loading {
  color: var(--mg-secondary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 2rem;
}

@media (max-width: 1200px) {
  .workspace-floor {
    grid-template-columns: 1fr;
  }
  .floor-detail-area {
    position: static;
    height: auto;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box { width: 100%; }
  .header-actions {
    flex-wrap: wrap;
  }
  .refresh-btn { flex: 1; }
  .kpi-divider { display: none; }
  .kpi-tiles {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
  .kpi-hero {
    min-width: 100%;
    align-items: center;
  }
  .inspection-footer {
    flex-direction: column;
  }
}
.courier-assign-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.courier-assign-row .input {
  flex: 1;
}
.courier-assign-msg {
  font-size: 0.82rem;
  margin: 0.4rem 0 0;
}
.ok-text {
  color: var(--accent-green, #2f6f5c);
}
</style>

