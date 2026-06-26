<template>
  <div class="order-detail-page" dir="rtl">
    <header class="page-header">
      <button class="back-btn" type="button" @click="goBack" aria-label="بازگشت">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">جزئیات سفارش</h1>
      <a class="list-link" href="/customer/orders">لیست</a>
    </header>

    <section class="code-card">
      <p>کد سفارش</p>
      <h2>{{ orderCode || '-' }}</h2>
      <span v-if="order" class="status-pill">{{ formatStatus(order.status) }}</span>
    </section>

    <section v-if="!mobile" class="lookup-card">
      <label>
        <span>شماره موبایل سفارش</span>
        <input v-model="mobileInput" class="input" dir="ltr" inputmode="numeric" placeholder="09123456789" />
      </label>
      <button class="primary-btn" type="button" @click="loadOrder">نمایش سفارش</button>
    </section>

    <p v-if="loading" class="state muted">در حال دریافت سفارش...</p>
    <p v-else-if="error" class="state error">{{ error }}</p>

    <template v-else-if="order">
      <section class="facts-grid">
        <article>
          <span>مشتری</span>
          <strong>{{ order.customer_name || '-' }}</strong>
        </article>
        <article>
          <span>مبلغ</span>
          <strong>{{ formatMoney(order.grand_total || 0, currency) }}</strong>
        </article>
        <article>
          <span>نوع سفارش</span>
          <strong>{{ order.delivery_mode || order.order_type || '-' }}</strong>
        </article>
        <article>
          <span>تاریخ</span>
          <strong>{{ formatDate(order.created_at || order.creation || order.transaction_date) }}</strong>
        </article>
      </section>

      <section v-if="timeline.length" class="timeline-card">
        <h3>روند سفارش</h3>
        <ol class="timeline">
          <li v-for="row in timeline" :key="row.status" :class="{ done: row.done }">
            <i></i>
            <span>{{ formatStatus(row.status) }}</span>
          </li>
        </ol>
      </section>

      <section class="items-card">
        <header>
          <h3>آیتم‌ها</h3>
          <span>{{ items.length.toLocaleString('fa-IR') }} مورد</span>
        </header>
        <div v-if="items.length" class="items-list">
          <article v-for="line in items" :key="`${line.title}-${line.qty}-${line.line_total}`" class="item-row">
            <div>
              <strong>{{ line.title || line.item_name || '-' }}</strong>
              <small>تعداد: {{ line.qty }}</small>
            </div>
            <span>{{ formatMoney(line.line_total || 0, currency) }}</span>
          </article>
        </div>
        <p v-else class="muted">آیتمی برای این سفارش دریافت نشد.</p>
      </section>

      <section v-if="order.address || order.delivery_address" class="address-card">
        <h3>آدرس تحویل</h3>
        <p>{{ order.address || order.delivery_address }}</p>
      </section>

      <div class="actions-row">
        <a :href="successUrl" class="secondary-btn">پیگیری عمومی</a>
        <a href="/menu" class="primary-btn">سفارش دوباره</a>
      </div>
    </template>

    <section v-else class="empty-card">
      <div>🔎</div>
      <h3>سفارشی برای نمایش نیست</h3>
      <p>کد سفارش و شماره موبایل را بررسی کنید.</p>
    </section>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getOrder } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile, parseQuery } from '@/utils/format'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const query = parseQuery()
const order = ref(null)
const items = ref([])
const timeline = ref([])
const loading = ref(false)
const error = ref('')
const currency = ref('TOMAN')
const mobileInput = ref(query.mobile || readAuth().mobile || '')

const orderCode = computed(() => resolveOrderCode())
const mobile = computed(() => normalizeMobile(mobileInput.value || ''))
const successUrl = computed(() => `/order-success/${encodeURIComponent(orderCode.value)}?mobile=${encodeURIComponent(mobile.value)}`)

function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return { mobile: auth.mobile || localStorage.getItem('customer_phone') || '' }
  } catch {
    return { mobile: '' }
  }
}

function resolveOrderCode() {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[0] === 'customer' && parts[1] === 'orders') {
    return decodeURIComponent(parts.slice(2).join('/'))
  }
  return String(query.order_code || '').trim()
}

function goBack() {
  window.history.back()
}

function formatDate(value = '') {
  if (!value) return '-'
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return value
  }
}

async function loadOrder() {
  if (!orderCode.value || !mobile.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await getOrder(orderCode.value, mobile.value)
    order.value = data?.order || null
    items.value = Array.isArray(data?.items) ? data.items : []
    timeline.value = Array.isArray(data?.status_timeline) ? data.status_timeline : []
    if (data?.currency) currency.value = data.currency
  } catch (err) {
    error.value = err?.message || 'دریافت جزئیات سفارش ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (orderCode.value && mobile.value) loadOrder()
})
</script>

<style scoped>
.order-detail-page { min-height: 100vh; background: #f7f0e8; color: #3f2a1d; padding-bottom: 7rem; }
.page-header { display: flex; align-items: center; justify-content: space-between; padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8; }
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; display: flex; align-items: center; justify-content: center; color: #3f2a1d; cursor: pointer; }
.page-title { font-size: 1.1rem; font-weight: 800; margin: 0; }
.list-link { width: 40px; text-align: center; color: #6f4a31; text-decoration: none; font-weight: 800; font-size: .82rem; }
.code-card, .lookup-card, .timeline-card, .items-card, .address-card, .empty-card { margin: 1rem; background: #fff; border-radius: 24px; padding: 1.1rem; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.code-card { background: linear-gradient(135deg, #3f2a1d, #6f4a31); color: #fff; position: relative; }
.code-card p { margin: 0 0 .2rem; color: rgba(255,255,255,.68); font-size: .78rem; }
.code-card h2 { margin: 0; direction: ltr; font-size: 1.45rem; }
.status-pill { position: absolute; left: 1rem; top: 1rem; background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.22); border-radius: 999px; padding: .35rem .65rem; font-size: .75rem; font-weight: 800; }
.lookup-card label { display: grid; gap: .4rem; color: #846b58; font-size: .82rem; font-weight: 700; }
.input { width: 100%; box-sizing: border-box; border: 1.5px solid #e5ddd4; border-radius: 14px; padding: .85rem 1rem; font-family: inherit; background: #fdf8f1; }
.primary-btn, .secondary-btn { border: none; border-radius: 16px; padding: .9rem 1rem; text-decoration: none; font-family: inherit; font-weight: 800; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
.primary-btn { background: #6f4a31; color: #fff; }
.secondary-btn { background: #fff; color: #6f4a31; border: 1px solid #e5d7c7; }
.lookup-card .primary-btn { width: 100%; margin-top: .8rem; }
.state { margin: 1rem; text-align: center; }
.muted { color: #846b58; }
.error { color: #b84f4f; }
.facts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin: 0 1rem 1rem; }
.facts-grid article { background: #fff; border-radius: 20px; padding: .95rem; box-shadow: 0 4px 14px rgba(0,0,0,.06); }
.facts-grid span { display: block; color: #846b58; font-size: .75rem; margin-bottom: .25rem; }
.facts-grid strong { font-size: .9rem; }
.timeline-card h3, .items-card h3, .address-card h3 { margin: 0; font-size: 1rem; }
.timeline { list-style: none; margin: 1rem 0 0; padding: 0; display: grid; gap: .7rem; }
.timeline li { display: flex; align-items: center; gap: .65rem; color: #9b866f; font-weight: 700; }
.timeline i { width: 14px; height: 14px; border-radius: 50%; background: #e8d9ca; }
.timeline li.done { color: #2e7d32; }
.timeline li.done i { background: #2e7d32; box-shadow: 0 0 0 5px rgba(46,125,50,.12); }
.items-card header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f1e7db; padding-bottom: .75rem; margin-bottom: .75rem; }
.items-card header span { color: #846b58; font-size: .78rem; }
.items-list { display: grid; gap: .65rem; }
.item-row { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .75rem; border-radius: 16px; background: #fdf8f1; }
.item-row strong { display: block; font-size: .88rem; }
.item-row small { color: #846b58; }
.item-row > span { color: #6f4a31; font-weight: 800; white-space: nowrap; }
.address-card p { color: #846b58; line-height: 1.8; margin: .6rem 0 0; }
.actions-row { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin: 1rem; }
.empty-card { text-align: center; }
.empty-card div { font-size: 2.2rem; }
.empty-card p { color: #846b58; }
.bottom-spacer { height: 2rem; }
@media (min-width: 720px) { .order-detail-page { max-width: 760px; margin: 0 auto; } }
</style>
