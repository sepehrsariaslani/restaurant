<template>
  <div class="orders-page" dir="rtl">
    <header class="page-header">
      <button class="back-btn" type="button" @click="goBack" aria-label="بازگشت">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">سفارش‌های من</h1>
      <button class="refresh-btn" type="button" :disabled="loading" @click="loadOrders">↻</button>
    </header>

    <section class="hero-card">
      <div>
        <p class="eyebrow">تاریخچه خرید</p>
        <h2>{{ customerName }}</h2>
        <p>{{ mobile ? `شماره ${mobile}` : 'برای دیدن سفارش‌ها وارد شوید.' }}</p>
      </div>
      <a v-if="!mobile" href="/customer/login?redirect=/customer/orders" class="login-link">ورود</a>
    </section>

    <section class="stats-grid" v-if="orders.length">
      <article>
        <strong>{{ orders.length.toLocaleString('fa-IR') }}</strong>
        <span>سفارش</span>
      </article>
      <article>
        <strong>{{ formatMoney(totalSpent, currency) }}</strong>
        <span>جمع خرید</span>
      </article>
    </section>

    <p v-if="loading" class="state muted">در حال دریافت سفارش‌ها...</p>
    <p v-else-if="error" class="state error">{{ error }}</p>

    <section v-else-if="orders.length" class="orders-list">
      <a
        v-for="order in orders"
        :key="order.order_code || order.name"
        class="order-card"
        :href="orderDetailUrl(order)"
      >
        <div class="order-top">
          <div>
            <small>کد سفارش</small>
            <strong>{{ order.order_code || order.name }}</strong>
          </div>
          <span class="status-pill">{{ formatStatus(order.status) }}</span>
        </div>
        <div class="order-meta">
          <span>{{ formatDate(order.created_at || order.transaction_date || order.creation) }}</span>
          <span>{{ formatMoney(order.grand_total || order.total || 0, currency) }}</span>
        </div>
        <div class="order-footer">
          <span>{{ order.channel || order.delivery_mode || 'آنلاین' }}</span>
          <span>جزئیات ←</span>
        </div>
      </a>
    </section>

    <section v-else class="empty-card">
      <div class="empty-icon">🧾</div>
      <h3>هنوز سفارشی ندارید</h3>
      <p>بعد از ثبت سفارش، تاریخچه خرید شما اینجا نمایش داده می‌شود.</p>
      <a href="/menu" class="primary-btn">شروع سفارش</a>
    </section>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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
.orders-page { min-height: 100vh; background: #f7f0e8; padding-bottom: 7rem; color: #3f2a1d; }
.page-header { display: flex; align-items: center; justify-content: space-between; padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8; }
.back-btn, .refresh-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; color: #3f2a1d; display: flex; align-items: center; justify-content: center; font-family: inherit; }
.refresh-btn:disabled { opacity: 0.5; }
.page-title { font-size: 1.1rem; font-weight: 800; margin: 0; }
.hero-card { margin: 1rem; padding: 1.2rem; border-radius: 24px; color: #fff; background: linear-gradient(135deg, #3f2a1d, #6f4a31); display: flex; justify-content: space-between; gap: 1rem; align-items: center; box-shadow: 0 12px 26px rgba(63,42,29,.18); }
.hero-card h2, .hero-card p { margin: 0; }
.hero-card p { color: rgba(255,255,255,.72); font-size: .84rem; margin-top: .25rem; }
.eyebrow { color: rgba(255,255,255,.58) !important; font-size: .72rem !important; margin: 0 0 .2rem !important; }
.login-link, .primary-btn { background: #fff; color: #6f4a31; border-radius: 999px; padding: .65rem 1rem; text-decoration: none; font-weight: 800; font-size: .85rem; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin: 0 1rem 1rem; }
.stats-grid article { background: #fff; border-radius: 20px; padding: 1rem; box-shadow: 0 4px 14px rgba(0,0,0,.06); }
.stats-grid strong { display: block; font-size: 1.05rem; }
.stats-grid span { color: #846b58; font-size: .78rem; }
.state { margin: 1rem; text-align: center; }
.muted { color: #846b58; }
.error { color: #b84f4f; }
.orders-list { display: grid; gap: .75rem; margin: 0 1rem; }
.order-card { background: #fff; border-radius: 22px; padding: 1rem; text-decoration: none; color: inherit; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.order-top, .order-meta, .order-footer { display: flex; align-items: center; justify-content: space-between; gap: .75rem; }
.order-top small { display: block; color: #9b866f; font-size: .72rem; margin-bottom: .15rem; }
.order-top strong { font-size: 1rem; direction: ltr; display: inline-block; }
.status-pill { background: #f0e2d3; color: #6f4a31; border-radius: 999px; padding: .35rem .65rem; font-size: .75rem; font-weight: 800; white-space: nowrap; }
.order-meta { margin-top: .75rem; color: #846b58; font-size: .82rem; }
.order-footer { margin-top: .75rem; padding-top: .75rem; border-top: 1px solid #f1e7db; color: #6f4a31; font-size: .82rem; font-weight: 800; }
.empty-card { margin: 1rem; background: #fff; border-radius: 24px; padding: 2rem 1.2rem; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.empty-icon { font-size: 2.4rem; }
.empty-card h3 { margin: .5rem 0; }
.empty-card p { color: #846b58; line-height: 1.8; }
.empty-card .primary-btn { display: inline-block; background: #6f4a31; color: #fff; margin-top: .5rem; }
.bottom-spacer { height: 2rem; }
</style>
