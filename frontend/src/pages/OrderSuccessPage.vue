<template>
  <GlassShell title="سفارش شما ثبت شد" subtitle="وضعیت اولیه سفارش و کد پیگیری">
    <template #actions>
      <a class="secondary-btn" href="/menu">بازگشت به منو</a>
    </template>

    <GlassCard v-if="!orderCode">
      <p class="muted">کد سفارش در آدرس پیدا نشد.</p>
      <a href="/cart" class="secondary-btn">بازگشت به سبد</a>
    </GlassCard>

    <div class="grid-2" v-else>
      <GlassCard>
        <p class="muted">کد سفارش</p>
        <h2>{{ orderCode }}</h2>

        <div class="mobile-track" v-if="!hasMobile">
          <label>
            <span>برای مشاهده جزئیات، موبایل سفارش را وارد کنید</span>
            <input class="input" v-model="mobile" />
          </label>
          <button class="primary-btn" @click="loadOrder">نمایش وضعیت</button>
        </div>

        <p class="muted" v-if="loading">در حال دریافت وضعیت سفارش...</p>
        <p class="error" v-if="error">{{ error }}</p>

        <template v-if="order">
          <p>
            وضعیت فعلی:
            <strong>{{ formatStatus(order.status) }}</strong>
          </p>
          <p class="muted">نام مشتری: {{ order.customer_name }}</p>
          <p class="muted">مبلغ: {{ formatMoney(order.grand_total, currency) }}</p>
        </template>
      </GlassCard>

      <GlassCard v-if="timeline.length">
        <h3 class="section-title">روند سفارش</h3>
        <ul class="timeline">
          <li v-for="row in timeline" :key="row.status" :class="{ done: row.done }">
            {{ formatStatus(row.status) }}
          </li>
        </ul>
      </GlassCard>
    </div>

    <GlassCard v-if="orderItems.length">
      <h3 class="section-title">آیتم های سفارش</h3>
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
    </GlassCard>
  </GlassShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import GlassShell from '@/components/GlassShell.vue'
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
h2 {
  margin: 0.2rem 0 0.4rem;
  font-size: 1.8rem;
}

.mobile-track {
  margin: 0.7rem 0;
  display: grid;
  gap: 0.55rem;
}

.mobile-track label {
  display: grid;
  gap: 0.3rem;
}

.error {
  margin: 0;
  color: var(--danger);
}

.timeline {
  margin: 0;
  padding-inline-start: 1rem;
  display: grid;
  gap: 0.45rem;
}

.timeline li {
  color: var(--text-muted);
}

.timeline li.done {
  color: var(--accent-gold);
  font-weight: 600;
}

.order-table {
  width: 100%;
  border-collapse: collapse;
}

.order-table th,
.order-table td {
  text-align: right;
  border-bottom: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  padding: 0.55rem 0.4rem;
  font-size: 0.9rem;
}

@media (max-width: 720px) {
  .order-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
