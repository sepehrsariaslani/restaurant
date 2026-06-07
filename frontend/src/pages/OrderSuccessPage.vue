<template>
  <section class="order-success-page" dir="rtl">
    <header class="success-hero">
      <div class="success-hero-copy">
        <p class="eyebrow">پیگیری سفارش</p>
        <h1>سفارش شما ثبت شد</h1>
        <p class="muted">کد سفارش، وضعیت فعلی، و آیتم‌های ثبت‌شده در یک نگاه.</p>
      </div>

      <div class="success-hero-actions">
        <a class="secondary-btn" href="/menu">بازگشت به منو</a>
        <a class="primary-btn" href="/cart">رفتن به سبد</a>
      </div>
    </header>

    <GlassCard v-if="!orderCode" class="empty-state-card">
      <p class="muted">کد سفارش در آدرس پیدا نشد.</p>
      <a href="/cart" class="secondary-btn">بازگشت به سبد</a>
    </GlassCard>

    <template v-else>
      <div class="summary-grid">
        <GlassCard class="summary-card summary-card--code">
          <div class="summary-head">
            <div>
              <p class="muted">کد سفارش</p>
              <h2>{{ orderCode }}</h2>
            </div>
            <span class="status-pill" v-if="order">{{ formatStatus(order.status) }}</span>
          </div>

          <div class="mobile-track" v-if="!hasMobile">
            <label>
              <span>برای مشاهده جزئیات، موبایل سفارش را وارد کنید</span>
              <input class="input" v-model="mobile" />
            </label>
            <button class="primary-btn" @click="loadOrder">نمایش وضعیت</button>
          </div>

          <p class="muted" v-if="loading">در حال دریافت وضعیت سفارش...</p>
          <p class="error" v-if="error">{{ error }}</p>

          <dl v-if="order" class="facts-grid">
            <div>
              <dt>نام مشتری</dt>
              <dd>{{ order.customer_name }}</dd>
            </div>
            <div>
              <dt>مبلغ</dt>
              <dd>{{ formatMoney(order.grand_total, currency) }}</dd>
            </div>
            <div>
              <dt>وضعیت فعلی</dt>
              <dd>{{ formatStatus(order.status) }}</dd>
            </div>
            <div>
              <dt>کد رهگیری</dt>
              <dd>{{ orderCode }}</dd>
            </div>
          </dl>
        </GlassCard>

        <GlassCard v-if="timeline.length" class="summary-card summary-card--timeline">
          <h3 class="section-title">روند سفارش</h3>
          <ul class="timeline">
            <li v-for="row in timeline" :key="row.status" :class="{ done: row.done }">
              <span class="timeline-dot"></span>
              <span>{{ formatStatus(row.status) }}</span>
            </li>
          </ul>
        </GlassCard>
      </div>

      <GlassCard v-if="orderItems.length" class="items-card">
        <header class="items-head">
          <div>
            <h3 class="section-title">آیتم‌های سفارش</h3>
            <p class="muted">لیست اقلام ثبت‌شده در این سفارش</p>
          </div>
          <span class="items-count">{{ orderItems.length }} آیتم</span>
        </header>

        <div class="table-wrap">
          <table class="order-table">
            <thead>
              <tr>
                <th>محصول</th>
                <th>تعداد</th>
                <th>قیمت واحد</th>
                <th>قیمت خط</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in orderItems" :key="line.title + line.qty">
                <td>{{ line.title }}</td>
                <td>{{ line.qty }}</td>
                <td>{{ formatMoney(line.unit_price, currency) }}</td>
                <td>{{ formatMoney(line.line_total, currency) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassCard>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import GlassCard from '@/components/GlassCard.vue'
import { getOrder } from '@/utils/api'
import { formatMoney, formatStatus, normalizeMobile, parseQuery } from '@/utils/format'
import { cartState, saveLastOrder } from '@/stores/cartStore'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const query = parseQuery()
const order = ref(null)
const orderItems = ref([])
const timeline = ref([])
const currency = ref('TOMAN')
const loading = ref(false)
const error = ref('')

const orderCode = ref(resolveOrderCode())
const mobile = ref(
  normalizeMobile(props.boot.mobile || query.mobile || cartState.lastOrder.mobile || ''),
)

const hasMobile = computed(() => Boolean(normalizeMobile(mobile.value)))

function resolveOrderCode() {
  const fromBoot = String(props.boot.order_code || '').trim()
  if (fromBoot) {
    return fromBoot
  }

  const path = window.location.pathname.replace(/^\/+|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[parts.length - 2] === 'order-success') {
    return parts[parts.length - 1]
  }
  return ''
}

async function loadOrder() {
  if (!orderCode.value || !normalizeMobile(mobile.value)) {
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await getOrder(orderCode.value, normalizeMobile(mobile.value))
    order.value = data.order
    orderItems.value = data.items || []
    timeline.value = data.status_timeline || []
    saveLastOrder({ order_code: orderCode.value, mobile: normalizeMobile(mobile.value) })
  } catch (err) {
    error.value = err.message || 'دریافت وضعیت سفارش ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (orderCode.value && hasMobile.value) {
    loadOrder()
  }
})
</script>

<style scoped>
.order-success-page {
  width: min(1180px, calc(100% - 2rem));
  margin: 1rem auto 2rem;
  display: grid;
  gap: 1rem;
  color: var(--text-primary);
}

.success-hero {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 28px;
  background: linear-gradient(135deg, rgb(var(--palette-eggshell-rgb) / 0.96), rgb(var(--palette-june-bud-rgb) / 0.18));
  box-shadow: 0 12px 28px rgb(15 23 42 / 0.08);
  padding: 1.05rem 1.1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.success-hero-copy {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 0.22rem;
  font-size: 0.72rem;
  color: var(--accent-green);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.success-hero h1 {
  margin: 0;
  font-size: 1.9rem;
  line-height: 1.15;
}

.success-hero .muted {
  margin: 0.3rem 0 0;
}

.success-hero-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.9fr);
  gap: 1rem;
  align-items: start;
}

.summary-card {
  min-width: 0;
  padding: 1rem;
}

.summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.summary-head h2 {
  margin: 0.15rem 0 0;
  font-size: 1.9rem;
  line-height: 1.1;
}

.status-pill,
.items-count {
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.76rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.09);
  color: var(--accent-green);
  white-space: nowrap;
}

.facts-grid {
  margin: 0.95rem 0 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem 1rem;
}

.facts-grid div {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.48);
  padding: 0.72rem 0.8rem;
}

.facts-grid dt {
  font-size: 0.74rem;
  color: var(--text-muted);
  margin-bottom: 0.22rem;
}

.facts-grid dd {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
}

.summary-card--timeline {
  display: grid;
  gap: 0.75rem;
}

.timeline {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.55rem;
}

.timeline li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--text-muted);
  padding: 0.6rem 0.7rem;
  border-radius: 14px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  background: rgb(var(--palette-eggshell-rgb) / 0.46);
}

.timeline li.done {
  color: var(--accent-gold);
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.22);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.08);
  font-weight: 700;
}

.timeline-dot {
  width: 0.62rem;
  height: 0.62rem;
  border-radius: 999px;
  background: currentColor;
  flex-shrink: 0;
}

.items-card {
  padding: 1rem;
}

.items-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.items-head h3 {
  margin-bottom: 0.18rem;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.order-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 680px;
}

.order-table th,
.order-table td {
  text-align: right;
  border-bottom: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.18);
  padding: 0.7rem 0.55rem;
  font-size: 0.92rem;
}

.order-table th {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.empty-state-card {
  padding: 1rem;
}

.mobile-track {
  margin: 0.85rem 0 0;
  display: grid;
  gap: 0.65rem;
}

.mobile-track label {
  display: grid;
  gap: 0.3rem;
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 920px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .success-hero {
    padding: 0.95rem;
  }

  .success-hero h1 {
    font-size: 1.6rem;
  }
}

@media (max-width: 640px) {
  .order-success-page {
    width: min(100% - 1rem, 100%);
    margin-top: 0.6rem;
  }

  .success-hero,
  .summary-card,
  .items-card {
    padding: 0.8rem;
    border-radius: 22px;
  }

  .success-hero-actions {
    width: 100%;
  }

  .success-hero-actions > * {
    flex: 1 1 0;
    text-align: center;
  }

  .summary-head h2 {
    font-size: 1.45rem;
  }

  .facts-grid {
    grid-template-columns: 1fr;
  }

  .order-table {
    min-width: 560px;
  }

  .order-table th,
  .order-table td {
    padding: 0.58rem 0.42rem;
    font-size: 0.82rem;
  }
}
</style>
