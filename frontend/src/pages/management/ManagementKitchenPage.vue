<template>
  <ManagementPageScaffold title="" subtitle="" :show-title="false">
    <!-- Header Toolbar -->
    <div class="workspace-header">
      <div class="header-intro">
        <h1 class="page-title">نمایشگر آشپزخانه <span class="badge-kds">KDS</span></h1>
        <p class="page-subtitle">مدیریت لحظه‌ای تولید و آماده‌سازی سفارشات</p>
      </div>

      <div class="header-actions">
        <!-- Date Filter (Professional & Visible) -->
        <div class="date-filter-control" :class="{ 'is-today': isToday }">
          <Calendar :size="18" class="date-icon" />
          <input
            type="date"
            v-model="dateFilter"
            class="filter-input date-input"
            @change="fetchOrders(true)"
            title="انتخاب تاریخ"
          />
          <span v-if="isToday" class="today-badge">امروز</span>
        </div>

        <div class="live-indicator" :class="{ offline: !isOnline, live: isToday && isOnline }">
          <div class="pulse-dot"></div>
          <span>{{ !isOnline ? 'آفلاین' : (isToday ? 'زنده' : 'آرشیو') }}</span>
        </div>
        
        <div class="filter-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model.trim="searchQuery"
            class="filter-input search-input"
            placeholder="جستجوی سفارش..."
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

    <!-- KPI Strip (Desktop) -->
    <div v-if="!isMobileView" class="kpi-strip desktop-only">
      <button class="kpi-tile" :class="{ active: filterStatus === '' }" @click="filterStatus = ''">
        <span class="kpi-dot all"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(activeCount) }}</span>
          <span class="kpi-label">فعال</span>
        </div>
      </button>
      <button class="kpi-tile kpi-new" :class="{ active: filterStatus === 'new' }" @click="filterStatus = 'new'">
        <span class="kpi-dot new"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(colNew.length) }}</span>
          <span class="kpi-label">جدید</span>
        </div>
      </button>
      <button class="kpi-tile kpi-prep" :class="{ active: filterStatus === 'preparing' }" @click="filterStatus = 'preparing'">
        <span class="kpi-dot preparing"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(colPrep.length) }}</span>
          <span class="kpi-label">در حال تولید</span>
        </div>
      </button>
      <button class="kpi-tile kpi-ready" :class="{ active: filterStatus === 'ready' }" @click="filterStatus = 'ready'">
        <span class="kpi-dot ready"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(colReady.length) }}</span>
          <span class="kpi-label">آماده تحویل</span>
        </div>
      </button>
      <button class="kpi-tile kpi-closed" :class="{ active: filterStatus === 'closed' }" @click="filterStatus = 'closed'">
        <span class="kpi-dot closed"></span>
        <div class="kpi-info">
          <span class="kpi-val">{{ toFaDigits(colClosed.length) }}</span>
          <span class="kpi-label">تاریخچه / بسته</span>
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

    <!-- Mobile Tabs (Pure Tab-based List) -->
    <div v-if="isMobileView" class="mobile-tabs mobile-only">
      <button class="m-tab" :class="{ active: mobileTab === 'new' }" @click="mobileTab = 'new'">
        <span class="m-tab-label">جدید</span>
        <span class="m-tab-count new" v-if="colNew.length">{{ toFaDigits(colNew.length) }}</span>
      </button>
      <button class="m-tab" :class="{ active: mobileTab === 'preparing' }" @click="mobileTab = 'preparing'">
        <span class="m-tab-label">در تولید</span>
        <span class="m-tab-count prep" v-if="colPrep.length">{{ toFaDigits(colPrep.length) }}</span>
      </button>
      <button class="m-tab m-tab-ready" :class="{ active: mobileTab === 'ready' }" @click="mobileTab = 'ready'">
        <span class="m-tab-label">آماده</span>
        <span class="m-tab-count ready" v-if="colReady.length">{{ toFaDigits(colReady.length) }}</span>
      </button>
      <button class="m-tab" :class="{ active: mobileTab === 'closed' }" @click="mobileTab = 'closed'">
        <span class="m-tab-label">بسته</span>
      </button>
    </div>

    <!-- Loading / Empty States -->
    <p class="muted-loading" v-if="loading && !orders.length">در حال دریافت سفارشات...</p>
    
    <template v-else-if="!orders.length && !searchQuery">
      <div class="empty-state">
        <div class="empty-icon-wrapper"><CheckCheck :size="32" class="success-icon" /></div>
        <strong>لیست خالی است</strong>
        <p>هیچ سفارشی در این تاریخ وجود ندارد.</p>
      </div>
    </template>
    
    <template v-else-if="(isMobileView && !activeMobileList.length) || (!isMobileView && filterStatus && !activeDesktopFilteredList.length) || (!isMobileView && !filterStatus && activeCount === 0)">
      <div class="empty-state">
        <div class="empty-icon-wrapper"><Search :size="32" /></div>
        <strong>سفارشی یافت نشد</strong>
        <p>با تب یا فیلترهای فعلی موردی وجود ندارد.</p>
        <button class="secondary-btn mt-2" @click="clearFilters">نمایش همه</button>
      </div>
    </template>
    
    <template v-else>
      <!-- Structural Switch: Mobile uses a pure vertical list, NO KANBAN elements -->
      <div v-if="isMobileView" class="mobile-ticket-list">
        <KitchenOrder 
          v-for="o in activeMobileList" :key="o.name" 
          :order="o" :type="mobileTab" 
          @action="handleAction(o, mobileTab)" 
        />
      </div>

      <!-- Desktop uses the Kanban Board -->
      <div v-else class="kds-board" :class="filterStatus ? 'desktop-filtered desktop-active-' + filterStatus : 'desktop-all-active'">
        
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

        <!-- Ready Column (Olive Semantic) -->
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

        <!-- Closed Column -->
        <div class="kds-column col-closed" v-show="filterStatus === 'closed'">
          <header class="kds-col-header">
            <div class="col-title">
              <span class="col-dot closed"></span>
              <h3>بسته / تحویل‌شده</h3>
            </div>
            <span class="col-count">{{ toFaDigits(colClosed.length) }}</span>
          </header>
          <div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colClosed" :key="o.name" 
              :order="o" type="closed" 
            />
          </div>
        </div>
      </div>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Search, RefreshCcw, AlertCircle, CheckCheck, Volume2, VolumeX, Calendar } from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import KitchenOrder from '@/components/KitchenOrder.vue'
import { callRestaurantAPI } from '@/utils/api'

// Audio setup
let notifyAudio = null
if (typeof Audio !== 'undefined') {
  notifyAudio = new Audio('/frontend/assets/kds-bell.mp3')
  notifyAudio.volume = 0.6
}

function getLocalTodayDate() {
  const d = new Date()
  const offset = d.getTimezoneOffset() * 60000
  const localDate = new Date(d.getTime() - offset)
  return localDate.toISOString().split('T')[0]
}

// State
const orders = ref([])
const loading = ref(false)
const errorMsg = ref('')
const soundEnabled = ref(true)
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const searchQuery = ref('')
const filterStatus = ref('') // desktop filter
const mobileTab = ref('new') // mobile tab filter
const dateFilter = ref(getLocalTodayDate())
const nowTick = ref(Date.now())
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)

// Timers
let pollTimer = null
let clockTimer = null
let visibilityHandler = null
let resizeHandler = null

const isMobileView = computed(() => windowWidth.value <= 1024)
const isToday = computed(() => dateFilter.value === getLocalTodayDate())

// Filter match logic - completely uncoupled from payment "paid" status
function _match(o, s) {
  const st = String(o.status || '').toLowerCase()
  if (s === 'new') return ['new', 'confirmed'].includes(st)
  if (s === 'preparing') return ['preparing', 'in_progress'].includes(st)
  // Ready means food is ready to handoff, not just paid.
  if (s === 'ready') return ['ready', 'completed'].includes(st)
  // Closed / Delivered states. No longer pollutes the active view.
  if (s === 'closed') return ['delivered', 'cancelled', 'closed'].includes(st)
  return true
}

const shown = computed(() => {
  let l = orders.value
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
const colClosed = computed(() => shown.value.filter(o => _match(o, 'closed')))

const activeCount = computed(() => colNew.value.length + colPrep.value.length + colReady.value.length)

// For mobile vertical list
const activeMobileList = computed(() => {
  if (mobileTab.value === 'new') return colNew.value
  if (mobileTab.value === 'preparing') return colPrep.value
  if (mobileTab.value === 'ready') return colReady.value
  if (mobileTab.value === 'closed') return colClosed.value
  return []
})

const activeDesktopFilteredList = computed(() => {
  if (filterStatus.value === 'new') return colNew.value
  if (filterStatus.value === 'preparing') return colPrep.value
  if (filterStatus.value === 'ready') return colReady.value
  if (filterStatus.value === 'closed') return colClosed.value
  return []
})

const avgTime = computed(() => {
  const active = orders.value.filter(o => !['delivered', 'cancelled', 'closed'].includes(String(o.status || '').toLowerCase()))
  if (!active.length) return 0
  const now = nowTick.value
  const totalMins = active.reduce((s, o) => {
    const created = o.created_at || o.creation || ''
    const safeDateStr = String(created).replace(' ', 'T')
    const ts = created ? new Date(safeDateStr).getTime() : now
    return s + Math.floor((now - ts) / 60000)
  }, 0)
  return Math.round(totalMins / active.length)
})

// Methods
function toFaDigits(val) {
  return Number(val || 0).toLocaleString('fa-IR')
}

function clearFilters() {
  searchQuery.value = ''
  filterStatus.value = ''
  mobileTab.value = 'new'
}

async function fetchOrders(manual = false) {
  if (loading.value && manual) return
  if (manual) loading.value = true
  
  try {
    const res = await callRestaurantAPI('get_kitchen_display_orders', { limit: 100, date: dateFilter.value })
    const newOrders = res.orders || []
    
    // Play sound if there are new active orders, and we are viewing today
    if (soundEnabled.value && orders.value.length > 0 && isToday.value) {
      const oldNewCount = orders.value.filter(o => _match(o, 'new')).length
      const currentNewCount = newOrders.filter(o => _match(o, 'new')).length
      if (currentNewCount > oldNewCount && notifyAudio) {
        notifyAudio.play().catch(() => {})
      }
    }
    
    orders.value = newOrders
    errorMsg.value = ''
    nowTick.value = Date.now()
  } catch (e) {
    if (manual) errorMsg.value = e.message || 'خطا در دریافت سفارش‌ها'
  } finally {
    if (manual) loading.value = false
  }
}

async function _updateOrderStatus(order, nextStatus) {
  const originalStatus = order.status
  // Optimistic update
  order.status = nextStatus
  
  try {
    await callRestaurantAPI('update_kitchen_order_status', {
      order_name: order.name,
      status: nextStatus
    })
  } catch (e) {
    // Rollback
    order.status = originalStatus
    errorMsg.value = e.message || 'خطا در تغییر وضعیت'
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}

function acceptOrder(o) { _updateOrderStatus(o, 'preparing') }
function markReady(o) { _updateOrderStatus(o, 'ready') }
function closeOrder(o) { _updateOrderStatus(o, 'delivered') }

function handleAction(o, type) {
  if (type === 'new') acceptOrder(o)
  else if (type === 'preparing') markReady(o)
  else if (type === 'ready') closeOrder(o)
}

function setupTimers() {
  if (pollTimer) clearInterval(pollTimer)
  // Smart polling: only poll if we are viewing TODAY.
  pollTimer = setInterval(() => {
    if (document.visibilityState === 'visible' && isOnline.value && isToday.value) {
      fetchOrders()
    }
  }, 10000)
  
  if (clockTimer) clearInterval(clockTimer)
  clockTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 60000)
}

onMounted(() => {
  fetchOrders(true)
  setupTimers()
  
  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { isOnline.value = true; if (isToday.value) fetchOrders() })
    window.addEventListener('offline', () => { isOnline.value = false })
    
    visibilityHandler = () => {
      if (document.visibilityState === 'visible' && isToday.value) fetchOrders()
    }
    document.addEventListener('visibilitychange', visibilityHandler)
    
    resizeHandler = () => { windowWidth.value = window.innerWidth }
    window.addEventListener('resize', resizeHandler)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof window !== 'undefined') {
    if (visibilityHandler) document.removeEventListener('visibilitychange', visibilityHandler)
    if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
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
  flex-wrap: wrap;
}

/* Date Filter - Professional UI */
.date-filter-control {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0;
  overflow: hidden;
  transition: all 0.2s;
  height: 2.8rem;
}

.date-filter-control.is-today {
  border-color: rgba(111, 123, 86, 0.4);
  background: rgba(111, 123, 86, 0.05);
}

.date-icon {
  position: absolute;
  right: 0.75rem;
  color: var(--mg-secondary);
  pointer-events: none;
}
.date-filter-control.is-today .date-icon { color: var(--mg-success); }

.date-input {
  background: transparent;
  border: none;
  width: 150px;
  height: 100%;
  padding: 0 1rem 0 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.95rem;
  font-weight: 700;
  outline: none;
  cursor: pointer;
}

.today-badge {
  position: absolute;
  left: 0.5rem;
  background: var(--mg-success);
  color: #fff;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 700;
  pointer-events: none;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--mg-surface-alt);
  color: var(--mg-text-muted);
  padding: 0.4rem 0.85rem;
  border-radius: var(--mg-radius-md);
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid var(--mg-border-light);
  height: 2.8rem;
}
.live-indicator.live {
  background: var(--mg-success-bg);
  color: var(--mg-success);
  border-color: rgba(111, 123, 86, 0.3);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
.live-indicator:not(.live) .pulse-dot { animation: none; opacity: 0.5; }

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 4px rgba(111, 123, 86, 0.2); }
  100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(111, 123, 86, 0); }
}

.filter-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  right: 1rem;
  color: var(--mg-secondary);
}

.filter-input {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.9rem;
  transition: all 0.2s;
  height: 2.8rem;
}

.search-input { width: 220px; }
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
.kpi-tile.kpi-ready.active {
  border-color: var(--mg-success);
  background: rgba(111, 123, 86, 0.05);
}

.kpi-tile.readonly {
  cursor: default;
}
.kpi-tile.readonly:hover {
  transform: none;
  border-color: var(--mg-border-light);
}

.kpi-closed {
  opacity: 0.8;
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
.kpi-dot.closed { background: var(--mg-secondary); }

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

/* Mobile Tabs (Pure Native Tab feeling) */
.mobile-tabs {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.4rem;
  margin-bottom: 1.5rem;
  display: flex;
}

.m-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.8rem 0.2rem;
  border-radius: var(--mg-radius-sm);
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.2s;
  cursor: pointer;
}

.m-tab.active {
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.m-tab.m-tab-ready.active {
  background: rgba(111, 123, 86, 0.05);
  color: var(--mg-success);
}

.m-tab-count {
  background: var(--mg-border);
  color: var(--mg-text-main);
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: 99px;
  min-width: 1.2rem;
  text-align: center;
}

.m-tab.active .m-tab-count.new { background: var(--mg-primary); color: #fff; }
.m-tab.active .m-tab-count.prep { background: var(--mg-danger); color: #fff; }
.m-tab.active .m-tab-count.ready { background: var(--mg-success); color: #fff; }

/* Mobile Ticket List (Vertical Only) */
.mobile-ticket-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-bottom: 2rem;
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

/* Desktop Board Layout */
.kds-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  align-items: start;
}

.kds-board.desktop-filtered {
  grid-template-columns: 1fr;
}

.kds-column {
  display: flex;
  flex-direction: column;
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  height: calc(100vh - 200px);
}

/* Green/Olive Semantics for Ready Column */
.kds-column.col-ready {
  background: rgba(111, 123, 86, 0.03);
  border-color: rgba(111, 123, 86, 0.2);
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

.kds-column.col-ready .kds-col-header {
  background: rgba(111, 123, 86, 0.08);
  border-bottom-color: rgba(111, 123, 86, 0.15);
}

.kds-column.col-ready h3 {
  color: var(--mg-success);
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
.col-dot.closed { background: var(--mg-secondary); }

.col-count {
  background: var(--mg-bg-page);
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-text-muted);
  border: 1px solid var(--mg-border-light);
}

.kds-column.col-ready .col-count {
  background: var(--mg-success-bg);
  color: var(--mg-success);
  border-color: rgba(111, 123, 86, 0.2);
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
  .desktop-only { display: none !important; }
  
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .date-filter-control {
    width: 100%;
  }
  .date-input { width: 100%; }
  .filter-box, .search-input { width: 100%; }
}
</style>
