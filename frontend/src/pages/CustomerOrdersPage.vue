<template>
  <div class="customer-page orders-page" dir="rtl">
    <CustomerPageHeader
      eyebrow="تاریخچه خرید"
      title="سفارش‌های من"
      subtitle="همه سفارش‌های ثبت‌شده را با جزئیات و وضعیت جاری ببینید."
      fallback-href="/customer/dashboard"
    >
      <template #eyebrow-icon><ReceiptText :size="14" aria-hidden="true" /></template>
      <template #action>
        <button class="customer-page__action" type="button" :disabled="loading" @click="loadOrders">
          <RefreshCcw :size="16" />
          <span>بروزرسانی</span>
        </button>
      </template>

      <div class="hero-summary customer-grid customer-grid--2">
        <article class="hero-summary__item customer-glass-card">
          <small>نام مشتری</small>
          <strong>{{ customerName }}</strong>
        </article>
        <article class="hero-summary__item customer-glass-card">
          <small>شماره همراه</small>
          <strong>{{ mobile || '—' }}</strong>
        </article>
      </div>
    </CustomerPageHeader>

    <div class="customer-page__body">
      <section class="stats-grid" v-if="orders.length">
        <article class="customer-glass-card">
          <strong>{{ orders.length.toLocaleString('fa-IR') }}</strong>
          <span>سفارش ثبت‌شده</span>
        </article>
        <article class="customer-glass-card">
          <strong>{{ formatMoney(totalSpent, currency) }}</strong>
          <span>جمع خرید</span>
        </article>
      </section>

      <p v-if="loading" class="state customer-muted-text">در حال دریافت سفارش‌ها...</p>
      <p v-else-if="error" class="state customer-danger-text">{{ error }}</p>

      <section v-else-if="orders.length" class="customer-stack">
        <p v-if="surveyActionError" class="state customer-danger-text" role="alert">{{ surveyActionError }}</p>
        <article
          v-for="order in orders"
          :key="order.order_code || order.name"
          class="order-card customer-glass-card"
        >
          <a class="order-card__main" :href="orderDetailUrl(order)">
          <div class="order-card__top">
            <div>
              <small>کد سفارش</small>
              <strong>{{ order.order_code || order.name }}</strong>
            </div>
            <span class="order-status">{{ formatStatus(order.status) }}</span>
          </div>
          <div class="order-card__meta">
            <span class="order-card__date"><CalendarDays :size="15" aria-hidden="true" /> <span>ثبت‌شده در {{ formatDate(order.created_at || order.placed_at || order.transaction_date || order.creation) }}</span></span>
            <span>{{ formatMoney(order.grand_total || order.total || 0, currency) }}</span>
          </div>
          <div v-if="Array.isArray(order.items) && order.items.length" class="order-card__items" role="group" aria-label="اقلام سفارش">
            <div class="order-card__items-head">
              <strong>آیتم‌های سفارش</strong>
              <small>{{ order.items.length.toLocaleString('fa-IR') }} مورد</small>
            </div>
            <ul class="order-card__items-list">
              <li v-for="(item, index) in order.items" :key="`${item.menu_item || item.title || 'item'}-${index}`">
                <span class="order-item__name">{{ item.title || item.item_name || item.menu_item || 'محصول' }}</span>
                <span class="order-item__qty">× {{ Number(item.qty || 0).toLocaleString('fa-IR') }}</span>
                <strong>{{ formatMoney(item.line_total || item.amount || 0, currency) }}</strong>
              </li>
            </ul>
          </div>
          <p v-else class="order-card__items-empty">جزئیات اقلام این سفارش در دسترس نیست.</p>
          <div class="order-card__footer">
            <span>{{ order.channel || order.delivery_mode || 'آنلاین' }}</span>
            <span class="order-card__more">مشاهده جزئیات <ChevronLeft :size="16" /></span>
          </div>
          </a>
          <CustomerOrderSurveySummary
            :summary="surveySummaries[order.name || order.order_code]"
            :requesting="requestingOrder === String(order.name || order.order_code || '')"
            @request="requestSurvey(order)"
          />
        </article>
      </section>

      <section v-else class="customer-glass-card customer-empty">
        <div class="customer-icon-badge"><ReceiptText :size="28" /></div>
        <h3>هنوز سفارشی ندارید</h3>
        <p>بعد از ثبت اولین سفارش، تاریخچه خرید شما اینجا نمایش داده می‌شود.</p>
        <a href="/menu" class="primary-btn empty-cta">شروع سفارش</a>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { CalendarDays, ChevronLeft, ReceiptText, RefreshCcw } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import CustomerOrderSurveySummary from '@/components/customer/CustomerOrderSurveySummary.vue'
import { getCustomerOrders, getMyOrderSurveySummaries, requestMyOrderSurvey } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const loading = ref(false)
const error = ref('')
const orders = ref([])
const surveySummaries = ref({})
const requestingOrder = ref('')
const surveyActionError = ref('')
const currency = ref('TOMAN')
const auth = ref(readAuth())

const mobile = computed(() => normalizeMobile(auth.value.mobile || ''))
const customerName = computed(() => auth.value.name || 'مهمان عزیز')
const totalSpent = computed(() => orders.value.reduce((sum, order) => sum + Number(order.grand_total || order.total || 0), 0))

function readAuth() {
  try {
    const stored = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return {
      mobile: stored.mobile || localStorage.getItem('customer_phone') || '',
      name: stored.customer_name || localStorage.getItem('customer_name') || '',
    }
  } catch {
    return { mobile: '', name: '' }
  }
}

function formatDate(value = '') {
  if (!value) return '-'
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleDateString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return value
  }
}

function orderDetailUrl(order = {}) {
  const code = encodeURIComponent(order.order_code || order.name || '')
  return `/customer/orders/${code}?mobile=${encodeURIComponent(mobile.value)}`
}

async function loadOrders() {
  if (!mobile.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await getCustomerOrders({ mobile: mobile.value, limit: 50, start: 0 })
    orders.value = Array.isArray(data?.orders) ? data.orders : Array.isArray(data) ? data : []
    if (data?.currency) currency.value = data.currency
    surveySummaries.value = {}
    const orderNames = orders.value.map((order) => String(order.name || '')).filter(Boolean)
    if (orderNames.length) {
      try {
        const surveyData = await getMyOrderSurveySummaries(orderNames)
        surveySummaries.value = surveyData?.summaries || {}
      } catch (_) {
        // Order history remains usable if survey summary data is temporarily unavailable.
      }
    }
  } catch (err) {
    error.value = err?.message || 'دریافت تاریخچه سفارش‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function requestSurvey(order) {
  const orderName = String(order?.name || order?.order_code || '')
  if (!orderName || requestingOrder.value) return
  requestingOrder.value = orderName
  surveyActionError.value = ''
  try {
    const result = await requestMyOrderSurvey(orderName)
    if (result?.href) window.location.assign(result.href)
  } catch (err) {
    surveyActionError.value = err?.message || 'آماده‌سازی فرم نظرخواهی انجام نشد.'
  } finally {
    requestingOrder.value = ''
  }
}

onMounted(() => {
  let token = ''
  try { token = JSON.parse(localStorage.getItem('restaurant-customer-auth-v1') || '{}').customer_token || '' } catch {}
  if (!token) {
    window.location.replace('/customer/login?redirect=%2Fcustomer%2Forders')
    return
  }
  if (mobile.value) loadOrders()
})
</script>

<style scoped>
.hero-summary {
  margin-top: 0.95rem;
}

.hero-summary__item {
  padding: 0.85rem 0.95rem;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  border-inline-start: 3px solid var(--ds-color-action-accent);
  color: var(--ds-color-text-primary);
  box-shadow: none;
}

.hero-summary__item small {
  display: block;
  color: var(--ds-color-text-muted);
}

.hero-summary__item strong {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.96rem;
  color: var(--ds-color-text-primary);
  overflow-wrap: anywhere;
}

.hero-summary__item:nth-child(2) strong {
  direction: ltr;
  text-align: right;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stats-grid article {
  padding: 1rem;
}

.stats-grid strong {
  display: block;
  font-size: 1.02rem;
}

.stats-grid span {
  display: block;
  margin-top: 0.28rem;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.state {
  text-align: center;
  margin: 1rem 0;
}

.order-card {
  padding: 1rem;
  color: inherit;
  text-decoration: none;
  border-color: color-mix(in srgb, var(--ds-color-action-accent) 24%, var(--ds-color-border));
}

.order-card__main { display: block; color: inherit; text-decoration: none; }
.order-card__main:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; border-radius: var(--ds-radius-md); }

.order-card__top,
.order-card__meta,
.order-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.order-card__top small {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}

.order-card__top strong {
  font-size: 0.98rem;
  direction: ltr;
  display: inline-block;
}

.order-status {
  padding: 0.34rem 0.6rem;
  border-radius: 999px;
  background: var(--ds-color-action-accent-soft);
  color: var(--ds-color-action-accent-foreground);
  font-size: 0.74rem;
  font-weight: 800;
  white-space: nowrap;
}

.order-card__meta {
  margin-top: 0.8rem;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.order-card__date {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.order-card__date svg {
  flex: 0 0 auto;
  color: var(--ds-color-action-accent);
}

.order-card__items {
  margin-top: 0.9rem;
  padding: 0.8rem 0.9rem;
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-surface-muted);
  border-inline-start: 3px solid var(--ds-color-action-accent);
}

.order-card__items-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
  color: var(--ds-color-text-primary);
  font-size: 0.84rem;
}

.order-card__items-head small {
  color: var(--ds-color-text-muted);
  font-size: 0.74rem;
  font-weight: 500;
}

.order-card__items-list {
  display: grid;
  gap: 0.15rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.order-card__items-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: baseline;
  gap: 0.65rem;
  padding: 0.45rem 0;
  border-top: 1px solid var(--ds-color-border);
  font-size: 0.8rem;
}

.order-item__name {
  min-width: 0;
  color: var(--ds-color-text-primary);
  overflow-wrap: anywhere;
}

.order-item__qty {
  color: var(--ds-color-text-muted);
  white-space: nowrap;
}

.order-card__items-list li strong {
  color: var(--ds-color-text-secondary);
  font-size: 0.78rem;
  white-space: nowrap;
}

.order-card__items-empty {
  margin: 0.75rem 0 0;
  color: var(--ds-color-text-muted);
  font-size: 0.78rem;
}

.order-card__footer {
  margin-top: 0.8rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--ds-color-border);
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 700;
}

.order-card__more {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  color: var(--ds-color-action-accent-foreground);
}

.order-card__more svg {
  color: var(--ds-color-action-accent);
}

.empty-cta {
  display: inline-flex;
}

.order-card { display: grid; gap: .85rem; }
</style>
