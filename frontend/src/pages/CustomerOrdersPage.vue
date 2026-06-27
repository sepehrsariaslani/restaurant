<template>
  <div class="customer-page orders-page" dir="rtl">
    <section class="customer-page__hero">
      <div class="customer-page__topbar">
        <button class="customer-page__back" type="button" @click="goBack" aria-label="بازگشت">
          <ChevronRight :size="20" />
        </button>
        <div class="customer-page__titles">
          <p class="customer-page__eyebrow"><ReceiptText :size="14" /> تاریخچه خرید</p>
          <h1 class="customer-page__title">سفارش‌های من</h1>
          <p class="customer-page__subtitle">همه سفارش‌های ثبت‌شده را با جزئیات و وضعیت جاری ببینید.</p>
        </div>
        <button class="customer-page__action" type="button" :disabled="loading" @click="loadOrders">
          <RefreshCcw :size="16" />
          <span>بروزرسانی</span>
        </button>
      </div>

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
    </section>

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
        <a
          v-for="order in orders"
          :key="order.order_code || order.name"
          class="order-card customer-glass-card"
          :href="orderDetailUrl(order)"
        >
          <div class="order-card__top">
            <div>
              <small>کد سفارش</small>
              <strong>{{ order.order_code || order.name }}</strong>
            </div>
            <span class="order-status">{{ formatStatus(order.status) }}</span>
          </div>
          <div class="order-card__meta">
            <span>{{ formatDate(order.created_at || order.transaction_date || order.creation) }}</span>
            <span>{{ formatMoney(order.grand_total || order.total || 0, currency) }}</span>
          </div>
          <div class="order-card__footer">
            <span>{{ order.channel || order.delivery_mode || 'آنلاین' }}</span>
            <span class="order-card__more">مشاهده جزئیات <ChevronLeft :size="16" /></span>
          </div>
        </a>
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
import { ChevronLeft, ChevronRight, ReceiptText, RefreshCcw } from 'lucide-vue-next'
import { getCustomerOrders } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const loading = ref(false)
const error = ref('')
const orders = ref([])
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

function goBack() {
  window.history.back()
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
  } catch (err) {
    error.value = err?.message || 'دریافت تاریخچه سفارش‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (mobile.value) loadOrders()
})
</script>

<style scoped>
.hero-summary {
  margin-top: 0.95rem;
}

.hero-summary__item {
  padding: 0.85rem 0.95rem;
  background: rgb(255 255 255 / 0.1);
  border-color: rgb(255 255 255 / 0.12);
  color: #fff;
  box-shadow: none;
}

.hero-summary__item small {
  display: block;
  color: rgb(255 255 255 / 0.7);
}

.hero-summary__item strong {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.96rem;
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
}

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
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--accent-green);
  font-size: 0.74rem;
  font-weight: 800;
  white-space: nowrap;
}

.order-card__meta {
  margin-top: 0.8rem;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.order-card__footer {
  margin-top: 0.8rem;
  padding-top: 0.8rem;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 700;
}

.order-card__more {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
}

.empty-cta {
  display: inline-flex;
}
</style>
