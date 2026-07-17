<template>
  <ManagementPageScaffold title="" subtitle="" :show-title="false">
    <!-- Header Toolbar -->
    <div class="workspace-header">
      <div class="header-intro">
        <h1 class="page-title">نمایشگر آشپزخانه <span class="badge-kds">KDS</span></h1>
        <p class="page-subtitle">مدیریت لحظه‌ای تولید و آماده‌سازی سفارشات</p>
      </div>

      <div class="header-actions">
        <div class="live-indicator" :class="{ offline: !isOnline }">
          <div class="pulse-dot"></div>
          <span>{{ isOnline ? 'آنلاین' : 'آفلاین' }}</span>
        </div>
        
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model.trim="searchQuery"
            class="search-input"
            placeholder="جستجوی سفارش، میز یا مشتری..."
          />
        </div>
        
        <button class="icon-btn" :class="{ active: soundEnabled }" @click="soundEnabled = !soundEnabled" :title="soundEnabled ? 'صدا روشن' : 'صدا خاموش'">
          <Volume2 v-if="soundEnabled" :size="18" />
          <VolumeX v-else :size="18" />
        </button>

        <button class="refresh-btn" type="button" :disabled="loading" @click="fetchOrders(true)" title="بروزرسانی">
          <RefreshCcw :size="18" :class="{ 'is-spinning': loading }" />
        </button>
      </div>
    </div>

    <div class="workspace-alerts" v-if="errorMsg">
      <p class="error-alert"><AlertCircle :size="16" /> {{ errorMsg }}</p>
    </div>

    <!-- KPI Strip -->
    <div class="kpi-strip">
      <button class="kpi-tile" :class="{ active: filterStatus === '' }" @click="filterStatus = ''">
        <span class="kpi-dot all"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(orders.length) }}</span>
          <span class="kpi-label">کل سفارش‌ها</span>
        </div>
      </button>
      <button class="kpi-tile" :class="{ active: filterStatus === 'new' }" @click="filterStatus = 'new'">
        <span class="kpi-dot new"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(cntFilter('new')) }}</span>
          <span class="kpi-label">جدید</span>
        </div>
      </button>
      <button class="kpi-tile" :class="{ active: filterStatus === 'preparing' }" @click="filterStatus = 'preparing'">
        <span class="kpi-dot preparing"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(cntFilter('preparing')) }}</span>
          <span class="kpi-label">در حال تولید</span>
        </div>
      </button>
      <button class="kpi-tile" :class="{ active: filterStatus === 'ready' }" @click="filterStatus = 'ready'">
        <span class="kpi-dot ready"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(cntFilter('ready')) }}</span>
          <span class="kpi-label">آماده تحویل</span>
        </div>
      </button>
      
      <div class="kpi-divider"></div>
      
      <div class="kpi-tile readonly">
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(avgTime) }} <small class="text-sm">دقیقه</small></span>
          <span class="kpi-label">میانگین زمان</span>
        </div>
      </div>
    </div>

    <p class="muted-loading" v-if="loading && !orders.length">در حال همگام‌سازی تابلو...</p>
    
    <template v-else-if="!orders.length">
      <div class="empty-state">
        <div class="empty-icon-wrapper"><CheckCheck :size="32" class="success-icon" /></div>
        <strong>تابلو خالی است</strong>
        <p>همه سفارش‌ها انجام شده‌اند. خسته نباشید!</p>
      </div>
    </template>
    
    <template v-else>
      <div v-if="!shown.length" class="empty-state">
        <div class="empty-icon-wrapper"><Search :size="32" /></div>
        <strong>سفارشی یافت نشد</strong>
        <p>با فیلترها و جستجوی فعلی موردی وجود ندارد.</p>
        <button class="secondary-btn mt-2" @click="searchQuery = ''; filterStatus = ''">پاک کردن فیلترها</button>
      </div>
      
      <!-- Board Layout -->
      <div v-else class="kds-board">
        <!-- New Column -->
        <div class="kds-column col-new" v-show="!filterStatus || filterStatus === 'new'">
          <header class="kds-col-header">
            <div class="col-title">
              <span class="col-dot new"></span>
              <h3>جدید</h3>
            </div>
            <span class="col-count">{{ toFaDigits(colNew.length) }}</span>
          </header>
          <div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colNew" :key="o.name" 
              :order="o" type="new" 
              @action="acceptOrder(o)" 
            />
          </div>
        </div>

        <!-- Preparing Column -->
        <div class="kds-column col-preparing" v-show="!filterStatus || filterStatus === 'preparing'">
          <header class="kds-col-header">
            <div class="col-title">
              <span class="col-dot preparing"></span>
              <h3>در حال تولید</h3>
            </div>
            <span class="col-count">{{ toFaDigits(colPrep.length) }}</span>
          </header>
          <div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colPrep" :key="o.name" 
              :order="o" type="prep" 
              @action="markReady(o)" 
            />
          </div>
        </div>

        <!-- Ready Column -->
        <div class="kds-column col-ready" v-show="!filterStatus || filterStatus === 'ready'">
          <header class="kds-col-header">
            <div class="col-title">
              <span class="col-dot ready"></span>
              <h3>آماده تحویل</h3>
            </div>
            <span class="col-count">{{ toFaDigits(colReady.length) }}</span>
          </header>
          <div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colReady" :key="o.name" 
              :order="o" type="ready" 
              @action="closeOrder(o)" 
            />
          </div>
        </div>
      </div>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Search, RefreshCcw, AlertCircle, CheckCheck, Volume2, VolumeX } from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import KitchenOrder from '@/components/KitchenOrder.vue'
import { callRestaurantAPI } from '@/utils/api'

// Audio setup
let notifyAudio = null
if (typeof Audio !== 'undefined') {
  notifyAudio = new Audio('/frontend/assets/kds-bell.mp3')
  notifyAudio.volume = 0.6
}

// State
const orders = ref([])
const loading = ref(false)
const errorMsg = ref('')
const soundEnabled = ref(true)
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const searchQuery = ref('')
const filterStatus = ref('')
const nowTick = ref(Date.now())

// Timers
let pollTimer = null
let clockTimer = null
let visibilityHandler = null

// Computed
const shown = computed(() => {
  let l = orders.value
  if (filterStatus.value) l = l.filter(o => _match(o, filterStatus.value))
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    l = l.filter(o => 
      String(o.order_code || '').toLowerCase().includes(q) || 
      String(o.customer_name || '').toLowerCase().includes(q) ||
      String(o.channel || '').toLowerCase().includes(q)
    )
  }
  return l
})

const colNew = computed(() => shown.value.filter(o => _match(o, 'new')))
const colPrep = computed(() => shown.value.filter(o => _match(o, 'preparing')))
const colReady = computed(() => shown.value.filter(o => _match(o, 'ready')))

const avgTime = computed(() => {
  if (!orders.value.length) return 0
  const now = nowTick.value
  const totalMins = orders.value.reduce((s, o) => {
    const ts = new Date(o.created_at || o.creation || now).getTime()
    return s + Math.floor((now - ts) / 60000)
  }, 0)
  return Math.round(totalMins / orders.value.length)
})

// Methods
function toFaDigits(val) {
  return Number(val || 0).toLocaleString('fa-IR')
}

function _match(o, s) {
  const st = String(o.status || '').toLowerCase()
  if (s === 'new') return ['new', 'confirmed'].includes(st)
  if (s === 'preparing') return ['preparing', 'in_progress'].includes(st)
  if (s === 'ready') return ['ready', 'paid'].includes(st)
  return true
}

function cntFilter(s) {
  return orders.value.filter(o => _match(o, s)).length
}

async function fetchOrders(manual = false) {
  if (loading.value && manual) return
  if (manual) loading.value = true
  
  try {
    const res = await callRestaurantAPI('get_kitchen_display_orders', { limit: 100 })
    const newOrders = res.orders || []
    
    // Play sound if there are new orders that weren't there before
    if (soundEnabled.value && orders.value.length > 0) {
      const oldNewCount = orders.value.filter(o => _match(o, 'new')).length
      const currentNewCount = newOrders.filter(o => _match(o, 'new')).length
      if (currentNewCount > oldNewCount && notifyAudio) {
        notifyAudio.play().catch(() => {})
      }
    }
    
    orders.value = newOrders
    errorMsg.value = ''
    nowTick.value = Date.now() // Update elapsed times
  } catch (e) {
    if (manual) errorMsg.value = e.message || 'خطا در دریافت سفارش‌ها'
  } finally {
    if (manual) loading.value = false
  }
}

async function _updateOrderStatus(order, nextStatus) {
  // Optimistic UI update
  const originalStatus = order.status
  order.status = nextStatus
  
  try {
    await callRestaurantAPI('update_kitchen_order_status', {
      order_name: order.name,
      status: nextStatus
    })
  } catch (e) {
    // Revert on failure
    order.status = originalStatus
    errorMsg.value = e.message || 'خطا در تغییر وضعیت'
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}

function acceptOrder(o) {
  _updateOrderStatus(o, 'preparing')
}

function markReady(o) {
  _updateOrderStatus(o, 'ready')
}

function closeOrder(o) {
  // For KDS, closing an order means it leaves the board (delivered)
  _updateOrderStatus(o, 'delivered')
  // Instantly hide it from board
  orders.value = orders.value.filter(item => item.name !== o.name)
}

function setupTimers() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    if (document.visibilityState === 'visible' && isOnline.value) {
      fetchOrders()
    }
  }, 10000) // Poll every 10s for kitchen responsiveness
  
  if (clockTimer) clearInterval(clockTimer)
  clockTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 60000) // Update minute counters every 60s
}

onMounted(() => {
  fetchOrders(true)
  setupTimers()
  
  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { isOnline.value = true; fetchOrders() })
    window.addEventListener('offline', () => { isOnline.value = false })
    
    visibilityHandler = () => {
      if (document.visibilityState === 'visible') fetchOrders()
    }
    document.addEventListener('visibilitychange', visibilityHandler)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof window !== 'undefined' && visibilityHandler) {
    document.removeEventListener('visibilitychange', visibilityHandler)
  }
})
</script>

<style scoped>
/* Workflow-based KDS Dashboard */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.badge-kds {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  font-size: 0.8rem;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  vertical-align: middle;
  margin-right: 0.25rem;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  color: var(--mg-text-muted);
  font-size: 0.95rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--mg-success-bg);
  color: var(--mg-success);
  padding: 0.4rem 0.85rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid rgba(111, 123, 86, 0.2);
}
.live-indicator.offline {
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  border-color: var(--mg-border);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
.offline .pulse-dot { animation: none; }

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 4px rgba(111, 123, 86, 0.2); }
  100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(111, 123, 86, 0); }
}

.search-box {
  position: relative;
  width: 260px;
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
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.9rem;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--mg-primary);
  outline: none;
}

.icon-btn, .refresh-btn {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  width: 2.8rem;
  height: 2.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}
.icon-btn:hover, .refresh-btn:hover {
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
}
.icon-btn.active {
  color: var(--mg-primary);
}

.is-spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* KPI Strip */
.kpi-strip {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.kpi-tile {
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  flex: 1;
  min-width: 130px;
  border: 1px solid var(--mg-border-light);
  text-align: right;
  cursor: pointer;
  transition: all 0.2s;
}

.kpi-tile:hover {
  border-color: var(--mg-border);
  transform: translateY(-2px);
}

.kpi-tile.active {
  background: var(--mg-bg-surface);
  border-color: var(--mg-primary);
  box-shadow: var(--mg-shadow-sm);
}

.kpi-tile.readonly {
  cursor: default;
}
.kpi-tile.readonly:hover {
  transform: none;
  border-color: var(--mg-border-light);
}

.kpi-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 0.5rem;
  flex-shrink: 0;
}

.kpi-dot.all { background: var(--mg-text-main); }
.kpi-dot.new { background: var(--mg-primary); } 
.kpi-dot.preparing { background: var(--mg-danger); } 
.kpi-dot.ready { background: var(--mg-success); }

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-val {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.8rem;
  color: var(--mg-text-muted);
  font-weight: 700;
  margin-top: 0.25rem;
}

.text-sm { font-size: 0.85rem; }

.kpi-divider {
  width: 1px;
  background: var(--mg-border-light);
  margin: 0.5rem 0.5rem;
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background: var(--mg-surface-alt);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1.5rem;
  opacity: 0.8;
}
.success-icon { color: var(--mg-success); }

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
.secondary-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
  padding: 0.6rem 1.2rem;
  border-radius: var(--mg-radius-sm);
  font-weight: 700;
  cursor: pointer;
  margin-top: 1rem;
}

.workspace-alerts {
  margin-bottom: 1.5rem;
}
.error-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  border: 1px solid rgba(166, 84, 63, 0.2);
}
.muted-loading {
  color: var(--mg-secondary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 2rem;
}

/* Board Layout */
.kds-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  align-items: start;
}

.kds-column {
  display: flex;
  flex-direction: column;
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  height: calc(100vh - 200px);
}

.kds-col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  border-radius: 16px 16px 0 0;
}

.col-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.col-title h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--mg-text-main);
}
.col-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.col-dot.new { background: var(--mg-primary); }
.col-dot.preparing { background: var(--mg-danger); }
.col-dot.ready { background: var(--mg-success); }

.col-count {
  background: var(--mg-bg-page);
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-text-muted);
  border: 1px solid var(--mg-border-light);
}

.kds-col-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

@media (max-width: 1024px) {
  .kds-board {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .kds-column {
    height: auto;
    max-height: 600px;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box { width: 100%; }
  .header-actions { flex-wrap: wrap; }
  .kpi-divider { display: none; }
  .kpi-tiles, .kpi-strip {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
