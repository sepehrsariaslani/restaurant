<template>
  <div class="kds-workspace">
    
    <!-- Unified Top Toolbar -->
    <div class="kds-toolbar">
      <div class="toolbar-start">
        <h1 class="page-title">
          آشپزخانه 
          <span class="live-dot" :class="{ offline: !isOnline, live: isToday && isOnline }" :title="isToday && isOnline ? 'زنده' : 'آرشیو'"></span>
        </h1>
        
        <div class="date-filter-compact" :class="{ 'is-today': isToday }">
          <Calendar :size="16" class="icon-date" />
          <input
            type="date"
            v-model="dateFilter"
            class="date-input"
            @change="fetchOrders(true)"
            title="انتخاب تاریخ"
          />
          <span v-if="isToday" class="today-tag">امروز</span>
        </div>
      </div>

      <div class="toolbar-end">
        <div class="search-compact">
          <Search :size="16" class="icon-search" />
          <input
            v-model.trim="searchQuery"
            class="search-input"
            placeholder="جستجو..."
          />
        </div>
        
        <div class="toolbar-actions">
          <button class="action-btn" :class="{ active: soundEnabled }" @click="soundEnabled = !soundEnabled" title="صدا">
            <Volume2 v-if="soundEnabled" :size="18" />
            <VolumeX v-else :size="18" />
          </button>

          <button class="action-btn" :disabled="loading" @click="fetchOrders(true)" title="بروزرسانی">
            <RefreshCcw :size="18" :class="{ 'is-spinning': loading }" />
          </button>
        </div>
      </div>
    </div>

    <div class="workspace-alerts" v-if="errorMsg">
      <p class="error-alert"><AlertCircle :size="16" /> {{ errorMsg }}</p>
    </div>

    <!-- Desktop KPI Strip -->
    <div v-if="!isMobileView" class="kpi-strip">
      <button class="kpi-btn" :class="{ active: filterStatus === '' }" @click="filterStatus = ''">
        <span class="kpi-val">{{ toFaDigits(activeCount) }}</span>
        <span class="kpi-lbl">فعال</span>
      </button>
      
      <div class="kpi-sep"></div>
      
      <button class="kpi-btn accent-new" :class="{ active: filterStatus === 'new' }" @click="filterStatus = 'new'">
        <span class="kpi-val">{{ toFaDigits(colNew.length) }}</span>
        <span class="kpi-lbl">جدید</span>
      </button>
      
      <button class="kpi-btn accent-prep" :class="{ active: filterStatus === 'preparing' }" @click="filterStatus = 'preparing'">
        <span class="kpi-val">{{ toFaDigits(colPrep.length) }}</span>
        <span class="kpi-lbl">تولید</span>
      </button>
      
      <button class="kpi-btn accent-ready" :class="{ active: filterStatus === 'ready' }" @click="filterStatus = 'ready'">
        <span class="kpi-val">{{ toFaDigits(colReady.length) }}</span>
        <span class="kpi-lbl">آماده</span>
      </button>
      
      <div class="kpi-sep"></div>
      
      <button class="kpi-btn" :class="{ active: filterStatus === 'closed' }" @click="filterStatus = 'closed'">
        <span class="kpi-val">{{ toFaDigits(colClosed.length) }}</span>
        <span class="kpi-lbl">بسته / تحویل</span>
      </button>
      
      <div class="kpi-spacer"></div>
      
      <div class="kpi-read">
        <span class="kpi-val">{{ toFaDigits(avgTime) }}<small>د</small></span>
        <span class="kpi-lbl">میانگین</span>
      </div>
    </div>

    <!-- Mobile Tabs (Pure Tab-based List) -->
    <div v-if="isMobileView" class="mobile-tabs">
      <button class="m-tab" :class="{ active: mobileTab === 'new' }" @click="mobileTab = 'new'">
        <span class="m-tab-lbl">جدید</span>
        <span class="m-tab-count new" v-if="colNew.length">{{ toFaDigits(colNew.length) }}</span>
      </button>
      <button class="m-tab" :class="{ active: mobileTab === 'preparing' }" @click="mobileTab = 'preparing'">
        <span class="m-tab-lbl">تولید</span>
        <span class="m-tab-count prep" v-if="colPrep.length">{{ toFaDigits(colPrep.length) }}</span>
      </button>
      <button class="m-tab m-tab-ready" :class="{ active: mobileTab === 'ready' }" @click="mobileTab = 'ready'">
        <span class="m-tab-lbl">آماده</span>
        <span class="m-tab-count ready" v-if="colReady.length">{{ toFaDigits(colReady.length) }}</span>
      </button>
      <button class="m-tab" :class="{ active: mobileTab === 'closed' }" @click="mobileTab = 'closed'">
        <span class="m-tab-lbl">بسته</span>
      </button>
    </div>

    <!-- Loading / Empty States -->
    <p class="muted-loading" v-if="loading && !orders.length">در حال دریافت سفارشات...</p>
    
    <template v-else-if="!orders.length && !searchQuery">
      <div class="empty-state">
        <div class="empty-icon-wrapper"><CheckCheck :size="40" class="success-icon" /></div>
        <strong>لیست خالی است</strong>
        <p>هیچ سفارشی در این تاریخ وجود ندارد.</p>
      </div>
    </template>
    
    <template v-else-if="(isMobileView && !activeMobileList.length) || (!isMobileView && filterStatus && !activeDesktopFilteredList.length) || (!isMobileView && !filterStatus && activeCount === 0)">
      <div class="empty-state">
        <div class="empty-icon-wrapper"><Search :size="40" /></div>
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
            <h3>جدید</h3>
            <span class="col-count">{{ toFaDigits(colNew.length) }}</span>
          </header>
          <div class="kds-col-body">
            <div v-if="!colNew.length" class="lane-empty">سفارش جدیدی نیست</div>
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
            <h3>در حال تولید</h3>
            <span class="col-count">{{ toFaDigits(colPrep.length) }}</span>
          </header>
          <div class="kds-col-body">
            <div v-if="!colPrep.length" class="lane-empty">آیتمی در حال تولید نیست</div>
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
            <h3>آماده تحویل</h3>
            <span class="col-count">{{ toFaDigits(colReady.length) }}</span>
          </header>
          <div class="kds-col-body">
            <div v-if="!colReady.length" class="lane-empty">سفارشی آماده‌ی تحویل نیست</div>
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
            <h3>بسته / تاریخچه</h3>
            <span class="col-count">{{ toFaDigits(colClosed.length) }}</span>
          </header>
          <div class="kds-col-body">
            <div v-if="!colClosed.length" class="lane-empty">سفارشی در تاریخچه نیست</div>
            <KitchenOrder 
              v-for="o in colClosed" :key="o.name" 
              :order="o" type="closed" 
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Search, RefreshCcw, AlertCircle, CheckCheck, Volume2, VolumeX, Calendar } from 'lucide-vue-next'
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

// Prevent race conditions
const inFlightMutations = ref(new Set())

// Timers
let pollTimer = null
let clockTimer = null
let visibilityHandler = null
let resizeHandler = null

const isMobileView = computed(() => windowWidth.value <= 1024)
const isToday = computed(() => dateFilter.value === getLocalTodayDate())

// Filter match logic - strictly isolated from payment flow
function _match(o, s) {
  const st = String(o.status || '').toLowerCase()
  if (s === 'new') return ['new', 'confirmed'].includes(st)
  if (s === 'preparing') return ['preparing', 'in_progress'].includes(st)
  if (s === 'ready') return ['ready', 'completed'].includes(st)
  if (s === 'closed') return ['delivered', 'cancelled', 'closed'].includes(st)
  return true
}

const shown = computed(() => {
  let l = orders.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    l = l.filter(o => {
      const matchMeta = String(o.order_code || '').toLowerCase().includes(q) || 
                        String(o.customer_name || '').toLowerCase().includes(q) ||
                        String(o.channel || '').toLowerCase().includes(q);
      const matchItems = (o.items || []).some(it => 
        String(it.title || it.item_name || '').toLowerCase().includes(q) ||
        String(it.note || '').toLowerCase().includes(q)
      );
      return matchMeta || matchItems;
    })
  }
  return l
})

const colNew = computed(() => shown.value.filter(o => _match(o, 'new')))
const colPrep = computed(() => shown.value.filter(o => _match(o, 'preparing')))
const colReady = computed(() => shown.value.filter(o => _match(o, 'ready')))
const colClosed = computed(() => shown.value.filter(o => _match(o, 'closed')))

const activeCount = computed(() => colNew.value.length + colPrep.value.length + colReady.value.length)

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
    let newOrders = res.orders || []
    
    // Protect optimistic updates: keep local status if order is currently being mutated
    if (inFlightMutations.value.size > 0) {
      newOrders = newOrders.map(no => {
        if (inFlightMutations.value.has(no.name)) {
          const localOrder = orders.value.find(lo => lo.name === no.name)
          if (localOrder) no.status = localOrder.status
        }
        return no
      })
    }
    
    // Sound notification
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
  inFlightMutations.value.add(order.name)
  
  try {
    await callRestaurantAPI('update_kitchen_order_status', {
      order_name: order.name,
      status: nextStatus
    })
    inFlightMutations.value.delete(order.name)
  } catch (e) {
    // Rollback
    inFlightMutations.value.delete(order.name)
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
  // Smart polling: only poll if viewing TODAY and tab is active
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
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('resize', handleResize)
  }
})

function handleOnline() { isOnline.value = true; if (isToday.value) fetchOrders() }
function handleOffline() { isOnline.value = false }
function handleVisibilityChange() { if (document.visibilityState === 'visible' && isToday.value) fetchOrders() }
function handleResize() { windowWidth.value = window.innerWidth }

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof window !== 'undefined') {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    window.removeEventListener('resize', handleResize)
  }
})
</script>

<style scoped>

.kds-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1.5rem;
  overflow: hidden;
  background: var(--mg-bg-page);
}
@media (max-width: 1024px) {
  .kds-workspace {
    height: auto;
    overflow: visible;
    padding: 1rem 0.5rem;
  }
}

/* 1. Header & Toolbar */
.kds-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.75rem 1rem;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(52, 38, 31, 0.02);
}

.toolbar-start, .toolbar-end {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.live-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--mg-text-muted);
}
.live-dot.live {
  background: var(--mg-success);
  animation: pulse-live 2s infinite;
}
@keyframes pulse-live {
  0% { box-shadow: 0 0 0 0px rgba(111, 123, 86, 0.4); }
  50% { box-shadow: 0 0 0 5px rgba(111, 123, 86, 0); }
  100% { box-shadow: 0 0 0 0px rgba(111, 123, 86, 0); }
}

.date-filter-compact {
  display: flex;
  align-items: center;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 0 0.5rem;
  height: 2.4rem;
  transition: border-color 0.2s;
  position: relative;
}
.date-filter-compact.is-today {
  border-color: rgba(111, 123, 86, 0.4);
  background: rgba(111, 123, 86, 0.04);
}
.icon-date {
  color: var(--mg-secondary);
  margin-left: 0.25rem;
}
.date-filter-compact.is-today .icon-date { color: var(--mg-success); }

.date-input {
  background: transparent;
  border: none;
  color: var(--mg-text-main);
  font-size: 0.9rem;
  font-weight: 700;
  outline: none;
  cursor: pointer;
}
.today-tag {
  position: absolute;
  left: 0.25rem;
  background: var(--mg-success);
  color: #fff;
  font-size: 0.65rem;
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-weight: 700;
  pointer-events: none;
}

.search-compact {
  display: flex;
  align-items: center;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 0 0.75rem;
  height: 2.4rem;
  width: 200px;
  transition: border-color 0.2s;
}
.search-compact:focus-within {
  border-color: var(--mg-primary);
}
.icon-search {
  color: var(--mg-secondary);
  margin-left: 0.5rem;
}
.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--mg-text-main);
  font-size: 0.9rem;
  outline: none;
  min-width: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  width: 2.4rem;
  height: 2.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover { background: var(--mg-bg-surface); color: var(--mg-primary); }
.action-btn.active { color: var(--mg-primary); }

.is-spinning { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

/* 2. Desktop KPI Strip */
.kpi-strip {
  display: flex;
  align-items: center;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 0.5rem 0.75rem;
  margin-bottom: 1.5rem;
  gap: 0.5rem;
}

.kpi-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: none;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--mg-text-muted);
}
.kpi-btn:hover { background: var(--mg-bg-surface); }
.kpi-btn.active {
  background: var(--mg-bg-surface);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.kpi-val { font-size: 1.1rem; font-weight: 800; color: var(--mg-text-main); }
.kpi-lbl { font-size: 0.85rem; font-weight: 700; }

.kpi-btn.accent-new.active .kpi-lbl { color: var(--mg-primary); }
.kpi-btn.accent-prep.active .kpi-lbl { color: var(--mg-danger); }
.kpi-btn.accent-ready.active .kpi-lbl { color: var(--mg-success); }

.kpi-sep {
  width: 1px;
  height: 1.5rem;
  background: var(--mg-border-light);
  margin: 0 0.25rem;
}
.kpi-spacer { flex: 1; }

.kpi-read {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0 0.5rem;
}
.kpi-read .kpi-val { color: var(--mg-secondary); font-size: 1rem; }
.kpi-read .kpi-lbl { color: var(--mg-text-muted); }

/* 3. Mobile Tabs */
.mobile-tabs {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 0.4rem;
  margin-bottom: 1.25rem;
  display: flex;
}

.m-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.6rem 0.2rem;
  border-radius: 6px;
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
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.m-tab.m-tab-ready.active { background: rgba(111, 123, 86, 0.08); color: var(--mg-success); }

.m-tab-count {
  background: var(--mg-border);
  color: var(--mg-text-main);
  font-size: 0.75rem;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  min-width: 1.1rem;
  text-align: center;
}
.m-tab.active .m-tab-count.new { background: var(--mg-primary); color: #fff; }
.m-tab.active .m-tab-count.prep { background: var(--mg-danger); color: #fff; }
.m-tab.active .m-tab-count.ready { background: var(--mg-success); color: #fff; }

/* 4. Empty / Loading States */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  background: var(--mg-surface-alt);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper { margin-bottom: 1rem; opacity: 0.6; }
.success-icon { color: var(--mg-success); opacity: 0.8; }
.empty-state strong { font-size: 1.1rem; color: var(--mg-text-main); margin-bottom: 0.4rem; font-weight: 800; }
.empty-state p { font-size: 0.9rem; color: var(--mg-text-muted); margin: 0; }
.secondary-btn {
  background: var(--mg-bg-surface); border: 1px solid var(--mg-border); color: var(--mg-text-main);
  padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; cursor: pointer; margin-top: 1.25rem;
}

.workspace-alerts { margin-bottom: 1.25rem; }
.error-alert {
  display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; border-radius: var(--mg-radius-sm);
  font-size: 0.9rem; font-weight: 700; margin: 0; background: var(--mg-danger-bg); color: var(--mg-danger);
  border: 1px solid rgba(166, 84, 63, 0.2);
}
.muted-loading { color: var(--mg-secondary); font-size: 0.95rem; font-weight: 700; margin-bottom: 2rem; }

/* Mobile Vertical List */
.mobile-ticket-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding-bottom: 2rem;
}

/* 5. Desktop Kanban Board */
.kds-board {
  flex: 1;
  overflow: hidden;

  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
  align-items: start;
}
.kds-board.desktop-filtered { grid-template-columns: 1fr; }

.kds-column {
  display: flex;
  flex-direction: column;
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  max-height: 100%;
}

.kds-column.col-ready {
  background: rgba(111, 123, 86, 0.03);
  border-color: rgba(111, 123, 86, 0.15);
}

.kds-col-header {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md) var(--mg-radius-md) 0 0;
  z-index: 10;
}
.kds-column.col-ready .kds-col-header {
  background: rgba(111, 123, 86, 0.06);
  border-bottom-color: rgba(111, 123, 86, 0.15);
}

.kds-col-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--mg-text-main);
}
.kds-column.col-new h3 { color: var(--mg-primary); }
.kds-column.col-preparing h3 { color: var(--mg-danger); }
.kds-column.col-ready h3 { color: var(--mg-success); }

.col-count {
  background: var(--mg-bg-page);
  padding: 0.15rem 0.5rem;
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
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}


.lane-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--mg-text-muted);
  border: 1px dashed var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  background: var(--mg-bg-page);
  text-align: center;
  margin: 0.5rem;
  opacity: 0.8;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .kds-toolbar {
    flex-direction: column;
    align-items: stretch;
    padding: 0.75rem;
  }
  .toolbar-start { justify-content: space-between; }
  .toolbar-end { width: 100%; }
  .search-compact { flex: 1; width: auto; }
}
</style>
