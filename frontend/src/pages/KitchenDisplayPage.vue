<template>
  <div class="kds-page" dir="rtl">
    <header class="kds-header">
      <div class="kds-brand">
        <span class="kds-icon">🍳</span>
        <div>
          <h1>صفحه نمایش آشپزخانه</h1>
          <p class="kds-time">{{ currentTime }}</p>
        </div>
      </div>
      <div class="kds-controls">
        <span class="online-badge" :class="{ offline: !isOnline }">
          {{ isOnline ? '● آنلاین' : '● آفلاین' }}
        </span>
        <button class="refresh-btn" type="button" @click="fetchOrders" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
          بروز‌رسانی
        </button>
        <button class="sound-btn" type="button" @click="soundEnabled = !soundEnabled" :title="soundEnabled ? 'صدا خاموش' : 'صدا روشن'">
          {{ soundEnabled ? '🔔' : '🔕' }}
        </button>
      </div>
    </header>

    <p v-if="errorMsg" class="kds-error">⚠️ {{ errorMsg }}</p>

    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-pill stat-pending">
        <strong>{{ pending.length }}</strong>
        <span>در انتظار</span>
      </div>
      <div class="stat-pill stat-inprogress">
        <strong>{{ inProgress.length }}</strong>
        <span>در حال آماده‌سازی</span>
      </div>
      <div class="stat-pill stat-ready">
        <strong>{{ ready.length }}</strong>
        <span>آماده تحویل</span>
      </div>
    </div>

    <div v-if="loading && !orders.length" class="kds-loader">
      <div class="loader-spinner"></div>
      <p>در حال دریافت سفارش‌ها...</p>
    </div>

    <div v-else class="kds-columns">

      <!-- Pending -->
      <div class="kds-col">
        <div class="col-header col-header--pending">
          <span class="col-dot"></span>
          در انتظار پردازش
          <span class="col-count">{{ pending.length }}</span>
        </div>
        <div class="orders-list" :class="{ 'orders-list--empty': !pending.length }">
          <div v-if="!pending.length" class="col-empty">
            <span>🎉</span>
            <p>سفارشی در انتظار نیست</p>
          </div>
          <KdsOrderCard
            v-for="order in pending"
            :key="order.name"
            :order="order"
            status="pending"
            @accept="acceptOrder(order)"
            @reject="rejectOrder(order)"
          />
        </div>
      </div>

      <!-- In Progress -->
      <div class="kds-col">
        <div class="col-header col-header--inprogress">
          <span class="col-dot"></span>
          در حال آماده‌سازی
          <span class="col-count">{{ inProgress.length }}</span>
        </div>
        <div class="orders-list" :class="{ 'orders-list--empty': !inProgress.length }">
          <div v-if="!inProgress.length" class="col-empty">
            <span>🍽️</span>
            <p>سفارشی در حال آماده‌سازی نیست</p>
          </div>
          <KdsOrderCard
            v-for="order in inProgress"
            :key="order.name"
            :order="order"
            status="inprogress"
            @done="markReady(order)"
          />
        </div>
      </div>

      <!-- Ready -->
      <div class="kds-col">
        <div class="col-header col-header--ready">
          <span class="col-dot"></span>
          آماده تحویل
          <span class="col-count">{{ ready.length }}</span>
        </div>
        <div class="orders-list" :class="{ 'orders-list--empty': !ready.length }">
          <div v-if="!ready.length" class="col-empty">
            <span>📦</span>
            <p>سفارشی آماده نیست</p>
          </div>
          <KdsOrderCard
            v-for="order in ready"
            :key="order.name"
            :order="order"
            status="ready"
            @close="closeOrder(order)"
          />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { callMethodByPathGET, callMethodByPath } from '@/utils/api'

const KdsOrderCard = {
  name: 'KdsOrderCard',
  props: {
    order: { type: Object, required: true },
    status: { type: String, default: 'pending' },
  },
  emits: ['accept', 'reject', 'done', 'close'],
  setup(props, { emit }) {
    function elapsedMin() {
      const created = props.order.creation || props.order.created_at || ''
      if (!created) return 0
      const diff = Date.now() - new Date(created).getTime()
      return Math.floor(diff / 60000)
    }
    const elapsed = ref(elapsedMin())
    const timer = setInterval(() => { elapsed.value = elapsedMin() }, 30000)
    onUnmounted(() => clearInterval(timer))
    return { elapsed, emit }
  },
  template: `
  <div class="kds-card" :class="'kds-card--' + status">
    <div class="kds-card-header">
      <div class="kds-card-code">
        <span class="channel-badge">{{ order.channel || order.delivery_mode || 'آنلاین' }}</span>
        <strong>{{ order.order_code || order.name }}</strong>
      </div>
      <span class="elapsed-time" :class="{ urgent: elapsed >= 20 }">{{ elapsed }} دقیقه</span>
    </div>

    <div class="kds-card-customer" v-if="order.customer_name">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
      {{ order.customer_name }}
    </div>

    <div class="kds-items">
      <div v-for="(item, idx) in (order.items || [])" :key="idx" class="kds-item">
        <span class="item-qty">{{ item.qty }}×</span>
        <span class="item-name">{{ item.title || item.item_name }}</span>
        <span v-if="item.note" class="item-note">{{ item.note }}</span>
      </div>
    </div>

    <div v-if="order.note" class="kds-note">
      📝 {{ order.note }}
    </div>

    <div class="kds-card-actions">
      <template v-if="status === 'pending'">
        <button class="kds-btn kds-btn--accept" @click="$emit('accept')">✓ قبول</button>
        <button class="kds-btn kds-btn--reject" @click="$emit('reject')">✗ رد</button>
      </template>
      <template v-else-if="status === 'inprogress'">
        <button class="kds-btn kds-btn--done" @click="$emit('done')">✓ آماده شد</button>
      </template>
      <template v-else>
        <button class="kds-btn kds-btn--close" @click="$emit('close')">✓ تحویل داده شد</button>
      </template>
    </div>
  </div>
  `,
}

const orders = ref([])
const loading = ref(false)
const errorMsg = ref('')
const soundEnabled = ref(true)
const isOnline = ref(navigator.onLine)
const currentTime = ref(formatTime())
let pollInterval = null
let clockInterval = null
const prevOrderCount = ref(0)

function formatTime() {
  return new Date().toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const pending = computed(() =>
  orders.value.filter(o => ['Pending', 'Draft', 'Open', 'pending', 'draft', 'open'].includes(o.status || o.docstatus))
)
const inProgress = computed(() =>
  orders.value.filter(o => ['In Progress', 'Accepted', 'Cooking', 'in_progress', 'accepted', 'cooking'].includes(o.status))
)
const ready = computed(() =>
  orders.value.filter(o => ['Ready', 'Prepared', 'ready', 'prepared'].includes(o.status))
)

async function fetchOrders() {
  loading.value = true
  errorMsg.value = ''
  try {
    const result = await callMethodByPathGET('restaurant.api.get_kitchen_orders', { limit: 50 })
    const list = Array.isArray(result) ? result : (Array.isArray(result?.orders) ? result.orders : [])
    const hadNew = list.length > prevOrderCount.value && prevOrderCount.value > 0
    orders.value = list
    prevOrderCount.value = list.length
    if (hadNew && soundEnabled.value) playAlert()
    isOnline.value = true
  } catch (err) {
    isOnline.value = !err.message?.includes('Failed to fetch')
    if (!orders.value.length) {
      errorMsg.value = 'اتصال به سرور برقرار نشد. در حالت آفلاین هستید.'
      orders.value = getMockOrders()
    }
  } finally {
    loading.value = false
  }
}

function getMockOrders() {
  return [
    { name: 'ORD-001', order_code: '1001', status: 'Pending', channel: 'آنلاین', customer_name: 'علی محمدی', creation: new Date(Date.now() - 5 * 60000).toISOString(), items: [{ qty: 2, item_name: 'پیتزا مارگاریتا' }, { qty: 1, item_name: 'نوشابه' }], note: '' },
    { name: 'ORD-002', order_code: '1002', status: 'In Progress', channel: 'تیک‌اوت', customer_name: 'سارا احمدی', creation: new Date(Date.now() - 12 * 60000).toISOString(), items: [{ qty: 1, item_name: 'برگر کلاسیک' }, { qty: 1, item_name: 'سیب زمینی' }], note: 'بدون سس مایو' },
    { name: 'ORD-003', order_code: '1003', status: 'Ready', channel: 'آنلاین', customer_name: 'رضا کریمی', creation: new Date(Date.now() - 22 * 60000).toISOString(), items: [{ qty: 3, item_name: 'چلو کباب' }], note: '' },
  ]
}

function playAlert() {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.setValueAtTime(880, ctx.currentTime)
    osc.frequency.setValueAtTime(660, ctx.currentTime + 0.15)
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.4)
  } catch (_) {}
}

async function acceptOrder(order) {
  try {
    await callMethodByPath('restaurant.api.update_order_status', { order_name: order.name, status: 'In Progress' })
    order.status = 'In Progress'
  } catch (_) {
    order.status = 'In Progress'
  }
}

async function rejectOrder(order) {
  if (!confirm(`سفارش ${order.order_code || order.name} رد شود؟`)) return
  try {
    await callMethodByPath('restaurant.api.update_order_status', { order_name: order.name, status: 'Cancelled' })
    orders.value = orders.value.filter(o => o.name !== order.name)
  } catch (_) {
    orders.value = orders.value.filter(o => o.name !== order.name)
  }
}

async function markReady(order) {
  try {
    await callMethodByPath('restaurant.api.update_order_status', { order_name: order.name, status: 'Ready' })
    order.status = 'Ready'
  } catch (_) {
    order.status = 'Ready'
  }
}

async function closeOrder(order) {
  try {
    await callMethodByPath('restaurant.api.update_order_status', { order_name: order.name, status: 'Completed' })
    orders.value = orders.value.filter(o => o.name !== order.name)
  } catch (_) {
    orders.value = orders.value.filter(o => o.name !== order.name)
  }
}

onMounted(() => {
  fetchOrders()
  pollInterval = setInterval(fetchOrders, 30000)
  clockInterval = setInterval(() => { currentTime.value = formatTime() }, 1000)
  window.addEventListener('online', () => { isOnline.value = true; fetchOrders() })
  window.addEventListener('offline', () => { isOnline.value = false })
})

onUnmounted(() => {
  clearInterval(pollInterval)
  clearInterval(clockInterval)
})
</script>

<style scoped>
.kds-page {
  min-height: 100vh;
  background: #1a1108;
  color: #f7f0e8;
  font-family: inherit;
  dir: rtl;
  display: flex;
  flex-direction: column;
}

.kds-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: #2a1c0e;
  border-bottom: 1px solid #3d2912;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.kds-brand { display: flex; align-items: center; gap: 0.85rem; }
.kds-icon { font-size: 1.8rem; }

.kds-brand h1 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #f7f0e8;
  margin: 0;
}

.kds-time { font-size: 0.82rem; color: #9e8878; margin: 0.15rem 0 0; dir: ltr; }

.kds-controls { display: flex; align-items: center; gap: 0.75rem; }

.online-badge {
  font-size: 0.8rem;
  color: #4ade80;
  font-weight: 600;
  background: rgba(74,222,128,0.12);
  padding: 0.3rem 0.7rem;
  border-radius: 20px;
}

.online-badge.offline { color: #f87171; background: rgba(248,113,113,0.12); }

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #f7f0e8;
  border-radius: 8px;
  padding: 0.45rem 0.85rem;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.2s;
}
.refresh-btn:hover { background: rgba(255,255,255,0.14); }
.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.sound-btn {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.sound-btn:hover { background: rgba(255,255,255,0.14); }

.kds-error {
  background: rgba(248,113,113,0.15);
  color: #fca5a5;
  padding: 0.75rem 1.5rem;
  font-size: 0.88rem;
  margin: 0;
}

.stats-bar {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: #221508;
  border-bottom: 1px solid #3d2912;
  overflow-x: auto;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  white-space: nowrap;
}

.stat-pill strong { font-size: 1.1rem; font-weight: 800; }
.stat-pending { background: rgba(251,191,36,0.15); color: #fbbf24; }
.stat-inprogress { background: rgba(99,179,237,0.15); color: #63b3ed; }
.stat-ready { background: rgba(74,222,128,0.15); color: #4ade80; }

.kds-loader {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #9e8878;
}

.loader-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #6f4a31;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.kds-columns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  flex: 1;
  min-height: 0;
}

.kds-col {
  display: flex;
  flex-direction: column;
  border-left: 1px solid #3d2912;
  min-height: calc(100vh - 170px);
}

.kds-col:last-child { border-left: none; }

.col-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  font-size: 0.88rem;
  font-weight: 700;
  border-bottom: 2px solid;
  position: sticky;
  top: 0;
  z-index: 2;
}

.col-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.col-count {
  margin-right: auto;
  background: rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 0.1rem 0.55rem;
  font-size: 0.8rem;
}

.col-header--pending {
  background: #2a200a;
  border-color: #fbbf24;
  color: #fbbf24;
}

.col-header--pending .col-dot { background: #fbbf24; }

.col-header--inprogress {
  background: #0a1a2a;
  border-color: #63b3ed;
  color: #63b3ed;
}

.col-header--inprogress .col-dot { background: #63b3ed; }

.col-header--ready {
  background: #0a2010;
  border-color: #4ade80;
  color: #4ade80;
}

.col-header--ready .col-dot { background: #4ade80; }

.orders-list {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  overflow-y: auto;
}

.orders-list--empty {
  justify-content: center;
  align-items: center;
}

.col-empty {
  text-align: center;
  color: #4a3525;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.col-empty span { font-size: 2rem; }

/* KDS Card (inline component styles via deep) */
:deep(.kds-card) {
  background: #2a1c0e;
  border-radius: 12px;
  padding: 0.9rem;
  border: 1.5px solid #3d2912;
  animation: slideIn 0.25s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.kds-card--inprogress) { border-color: #2563eb44; }
:deep(.kds-card--ready) { border-color: #16a34a44; }

:deep(.kds-card-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.55rem;
}

:deep(.kds-card-code) { display: flex; align-items: center; gap: 0.5rem; }

:deep(.channel-badge) {
  font-size: 0.7rem;
  background: rgba(255,255,255,0.08);
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  color: #9e8878;
}

:deep(.kds-card-code strong) { font-size: 0.95rem; color: #f7f0e8; }

:deep(.elapsed-time) { font-size: 0.78rem; color: #9e8878; }
:deep(.elapsed-time.urgent) { color: #fca5a5; font-weight: 700; }

:deep(.kds-card-customer) {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: #c4a882;
  margin-bottom: 0.6rem;
}

:deep(.kds-items) {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.6rem;
}

:deep(.kds-item) {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  font-size: 0.88rem;
  color: #f7f0e8;
}

:deep(.item-qty) {
  background: #6f4a31;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.35rem;
  border-radius: 5px;
  flex-shrink: 0;
}

:deep(.item-note) {
  font-size: 0.75rem;
  color: #fbbf24;
  font-style: italic;
}

:deep(.kds-note) {
  background: rgba(251,191,36,0.1);
  border-right: 2px solid #fbbf24;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #fbbf24;
  margin-bottom: 0.6rem;
}

:deep(.kds-card-actions) {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.1rem;
}

:deep(.kds-btn) {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s;
}

:deep(.kds-btn:hover) { opacity: 0.85; }

:deep(.kds-btn--accept) { background: #16a34a; color: #fff; }
:deep(.kds-btn--reject) { background: #dc2626; color: #fff; }
:deep(.kds-btn--done) { background: #2563eb; color: #fff; }
:deep(.kds-btn--close) { background: #4ade80; color: #14532d; }

@media (max-width: 768px) {
  .kds-columns {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .kds-col { min-height: 300px; border-left: none; border-bottom: 1px solid #3d2912; }
}
</style>
