<template>
  <div class="kds-page" dir="rtl">
    <header class="kds-header">
      <div class="kds-brand">
        <div class="kds-logo">🍳</div>
        <div>
          <h1>آشپزخانه <span class="kds-title-light">KDS</span></h1>
          <p class="kds-time">{{ currentTime }}</p>
        </div>
      </div>
      <div class="kds-controls">
        <span class="kds-online" :class="{ offline: !isOnline }">{{ isOnline ? '● آنلاین' : '● آفلاین' }}</span>
        <input v-model="searchQuery" placeholder="جستجو..." class="kds-search" />
        <div class="kds-views">
          <button class="kds-view-btn" :class="{ active: viewMode === 'cols' }" @click="viewMode = 'cols'">⊞</button>
          <button class="kds-view-btn" :class="{ active: viewMode === 'grid' }" @click="viewMode = 'grid'">⊡</button>
        </div>
        <button class="kds-refresh" @click="fetchOrders" :disabled="loading">↻ {{ loading ? '...' : 'بروز' }}</button>
        <button class="kds-sound" :class="{ muted: !soundEnabled }" @click="soundEnabled = !soundEnabled">{{ soundEnabled ? '🔊' : '🔇' }}</button>
      </div>
    </header>

    <div v-if="errorMsg" class="kds-error">⚠️ {{ errorMsg }}</div>

    <div class="kds-stats">
      <div class="kds-stat" :class="{ active: filterStatus === 'new' }" @click="filterStatus = 'new'">
        <strong>{{ cntFilter('new') }}</strong><span>جدید</span>
      </div>
      <div class="kds-stat" :class="{ active: filterStatus === 'preparing' }" @click="filterStatus = 'preparing'">
        <strong>{{ cntFilter('preparing') }}</strong><span>تولید</span>
      </div>
      <div class="kds-stat" :class="{ active: filterStatus === 'ready' }" @click="filterStatus = 'ready'">
        <strong>{{ cntFilter('ready') }}</strong><span>آماده</span>
      </div>
      <div class="kds-stat" :class="{ active: !filterStatus }" @click="filterStatus = ''">
        <strong>{{ orders.length }}</strong><span>کل</span>
      </div>
      <div class="kds-stat kds-stat-avg">
        <strong>{{ avgTime }}<small>د</small></strong><span>میانگین</span>
      </div>
    </div>

    <div class="kds-body">
      <div v-if="loading && !orders.length" class="kds-loading">
        <div class="kds-spinner"></div><p>در حال بارگذاری...</p>
      </div>
      <div v-else-if="!shown.length" class="kds-empty">
        <span>✅</span><h3>همه سفارش‌ها انجام شد!</h3>
      </div>
      <template v-else-if="viewMode === 'cols'">
        <div class="kds-cols">
          <div class="kds-col">
            <div class="kds-ch kds-ch-new">🆕 جدید <span class="kds-cb">{{ colNew.length }}</span></div>
            <div class="kds-cbdy"><KitchenOrder v-for="o in colNew" :key="o.name" :order="o" type="new" @click="acceptOrder(o)" /></div>
          </div>
          <div class="kds-col">
            <div class="kds-ch kds-ch-prep">🔧 تولید <span class="kds-cb">{{ colPrep.length }}</span></div>
            <div class="kds-cbdy"><KitchenOrder v-for="o in colPrep" :key="o.name" :order="o" type="prep" @click="markReady(o)" /></div>
          </div>
          <div class="kds-col">
            <div class="kds-ch kds-ch-ready">✅ آماده <span class="kds-cb">{{ colReady.length }}</span></div>
            <div class="kds-cbdy"><KitchenOrder v-for="o in colReady" :key="o.name" :order="o" type="ready" @click="closeOrder(o)" /></div>
          </div>
        </div>
      </template>
      <div v-else class="kds-grid">
        <KitchenOrder v-for="o in shown" :key="o.name" :order="o" :type="orderType(o)" @click="handleAction(o)" />
      </div>
    </div>
  </div>
</template>

<script>
import KitchenOrder from '@/components/KitchenOrder.vue'

export default {
  components: { KitchenOrder },
  data() {
    return {
      orders: [], loading: false, errorMsg: '', soundEnabled: true, isOnline: true,
      searchQuery: '', viewMode: 'cols', filterStatus: '', currentTime: '',
      pollTimer: null, clockTimer: null
    }
  },
  computed: {
    shown() {
      let l = this.orders
      if (this.filterStatus) l = l.filter(o => this._match(o, this.filterStatus))
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.trim().toLowerCase()
        l = l.filter(o => (o.order_code||'').toLowerCase().includes(q) || (o.customer_name||'').toLowerCase().includes(q))
      }
      return l
    },
    colNew() { return this.shown.filter(o => this._match(o, 'new')) },
    colPrep() { return this.shown.filter(o => this._match(o, 'preparing')) },
    colReady() { return this.shown.filter(o => this._match(o, 'ready')) },
    avgTime() {
      if (!this.orders.length) return 0
      const now = Date.now()
      return Math.round(this.orders.reduce((s, o) => s + Math.floor((now - new Date(o.created_at||o.creation||now).getTime())/60000), 0) / this.orders.length)
    }
  },
  methods: {
    _match(o, s) {
      const st = (o.status||'').toLowerCase()
      if (s === 'new') return ['new','confirmed'].includes(st)
      if (s === 'preparing') return ['preparing','in_progress'].includes(st)
      if (s === 'ready') return ['ready','paid'].includes(st)
      return true
    },
    cntFilter(s) { return this.orders.filter(o => this._match(o, s)).length },
    orderType(o) {
      return this._match(o, 'new') ? 'new' : this._match(o, 'preparing') ? 'prep' : 'ready'
    },
    handleAction(o) {
      const t = this.orderType(o)
      if (t === 'new') this.acceptOrder(o)
      else if (t === 'prep') this.markReady(o)
      else this.closeOrder(o)
    },
    async fetchOrders() {
      this.loading = true; this.errorMsg = ''
      try {
        const res = await (await fetch('/api/method/restaurant.api.get_kitchen_display_orders?limit=50')).json()
        const list = res?.message?.orders || []
        if (list.length > this.orders.length && this.soundEnabled && list.some(o => ['new','confirmed'].includes((o.status||'').toLowerCase()))) this.playAlert()
        this.orders = list; this.isOnline = true
      } catch(_) { this.isOnline = false; if (!this.orders.length) this.errorMsg = 'خطا در ارتباط' }
      finally { this.loading = false }
    },
    playAlert() {
      try {
        const c = new (window.AudioContext||window.webkitAudioContext)()
        const o = c.createOscillator(), g = c.createGain()
        o.connect(g); g.connect(c.destination); o.type = 'sine'
        o.frequency.setValueAtTime(800,c.currentTime); o.frequency.setValueAtTime(600,c.currentTime+0.15)
        g.gain.setValueAtTime(0.2,c.currentTime); g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.4)
        o.start(c.currentTime); o.stop(c.currentTime+0.4)
      } catch(_) {}
    },
    async acceptOrder(o) { const p=o.status; o.status='preparing'; try{await fetch('/api/method/restaurant.api.update_kitchen_order_status',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':window.csrf_token||''},body:JSON.stringify({order_name:o.name,status:'preparing'})})}catch(_){o.status=p} },
    async markReady(o) { const p=o.status; o.status='ready'; try{await fetch('/api/method/restaurant.api.update_kitchen_order_status',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':window.csrf_token||''},body:JSON.stringify({order_name:o.name,status:'ready'})})}catch(_){o.status=p} },
    async closeOrder(o) { this.orders=this.orders.filter(x=>x.name!==o.name); try{await fetch('/api/method/restaurant.api.update_kitchen_order_status',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':window.csrf_token||''},body:JSON.stringify({order_name:o.name,status:'delivered'})})}catch(_){} }
  },
  mounted() {
    this.currentTime = new Date().toLocaleTimeString('fa-IR')
    this.fetchOrders()
    this.pollTimer = setInterval(() => this.fetchOrders(), 15000)
    this.clockTimer = setInterval(() => { this.currentTime = new Date().toLocaleTimeString('fa-IR') }, 1000)
    window.addEventListener('online', () => this.isOnline = true)
    window.addEventListener('offline', () => this.isOnline = false)
  },
  unmounted() {
    clearInterval(this.pollTimer); clearInterval(this.clockTimer)
  }
}
</script>

<style scoped>
.kds-page{min-height:100vh;background:#0d0d0d;color:#f0e6d9;display:flex;flex-direction:column;direction:rtl;font-family:inherit}
.kds-header{display:flex;align-items:center;justify-content:space-between;padding:0.65rem 1.25rem;background:#161616;border-bottom:1px solid #252525;gap:0.75rem;flex-wrap:wrap}
.kds-brand{display:flex;align-items:center;gap:0.6rem}
.kds-logo{font-size:1.5rem}
.kds-brand h1{margin:0;font-size:1rem;font-weight:800}
.kds-title-light{color:#e8964a;font-weight:400}
.kds-time{font-size:0.7rem;color:#6a5a4a;margin:0;direction:ltr}
.kds-controls{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap}
.kds-online{font-size:0.7rem;color:#4ade80;font-weight:600;white-space:nowrap}
.kds-online.offline{color:#f87171}
.kds-search{background:#202020;border:1px solid #2a2a2a;border-radius:6px;padding:0.3rem 0.6rem;color:#f0e6d9;font-size:0.75rem;width:100px;outline:none;font-family:inherit}
.kds-search::placeholder{color:#444}
.kds-views{display:flex;gap:1px}
.kds-view-btn{background:#1a1a1a;border:1px solid #2a2a2a;color:#6a5a4a;padding:0.2rem 0.4rem;cursor:pointer;font-size:0.9rem;line-height:1}
.kds-view-btn:first-child{border-radius:5px 0 0 5px}
.kds-view-btn:last-child{border-radius:0 5px 5px 0}
.kds-view-btn.active{background:#e8964a22;border-color:#e8964a;color:#e8964a}
.kds-refresh{background:#202020;border:1px solid #2a2a2a;color:#c4b5a5;border-radius:6px;padding:0.3rem 0.6rem;cursor:pointer;font-size:0.75rem;font-family:inherit}
.kds-sound{background:#202020;border:1px solid #2a2a2a;color:#c4b5a5;border-radius:6px;padding:0.3rem 0.4rem;cursor:pointer;font-size:0.8rem;line-height:1;background:none;border:none}
.kds-sound.muted{opacity:0.4}
.kds-error{background:rgba(239,68,68,0.1);color:#fca5a5;padding:0.4rem 1.25rem;font-size:0.78rem}
.kds-stats{display:flex;gap:0.35rem;padding:0.45rem 1.25rem;background:#101010;border-bottom:1px solid #1e1e1e;overflow-x:auto}
.kds-stat{display:flex;flex-direction:column;align-items:center;gap:0;padding:0.25rem 0.7rem;border-radius:8px;cursor:pointer;border:1px solid transparent;background:rgba(255,255,255,0.03);white-space:nowrap;transition:0.15s}
.kds-stat.active,.kds-stat:hover{border-color:#3a3a3a}
.kds-stat strong{font-size:0.95rem;font-weight:800;color:#f0e6d9}
.kds-stat strong small{font-size:0.55rem;font-weight:400;color:#6a5a4a}
.kds-stat span{font-size:0.58rem;color:#6a5a4a}
.kds-stat-avg{cursor:default}
.kds-stat.active{background:rgba(232,150,74,0.08);border-color:#e8964a}
.kds-body{flex:1;min-height:0;display:flex}
.kds-loading{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.75rem;color:#555}
.kds-spinner{width:30px;height:30px;border:3px solid #222;border-top-color:#e8964a;border-radius:50%;animation:spin 0.7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.kds-empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.3rem;color:#555}
.kds-empty span{font-size:2.5rem}
.kds-empty h3{margin:0;font-size:1rem;color:#7a6a5a}
.kds-cols{display:grid;grid-template-columns:repeat(3,1fr);gap:0;flex:1}
.kds-col{display:flex;flex-direction:column;border-left:1px solid #1e1e1e;min-height:calc(100vh-170px)}
.kds-col:last-child{border-left:none}
.kds-ch{display:flex;align-items:center;gap:0.4rem;padding:0.45rem 0.75rem;font-size:0.8rem;font-weight:700;border-bottom:2px solid;position:sticky;top:0;z-index:2}
.kds-cb{background:rgba(0,0,0,0.25);border-radius:20px;padding:0.05rem 0.35rem;font-size:0.7rem}
.kds-ch-new{background:#1a1402;border-color:#fbbf24;color:#fbbf24}
.kds-ch-prep{background:#020e1a;border-color:#63b3ed;color:#63b3ed}
.kds-ch-ready{background:#021a08;border-color:#4ade80;color:#4ade80}
.kds-cbdy{flex:1;padding:0.45rem;display:flex;flex-direction:column;gap:0.4rem;overflow-y:auto}
.kds-grid{flex:1;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:0.45rem;padding:0.5rem;align-content:start}
@media(max-width:768px){.kds-cols{grid-template-columns:1fr}.kds-col{min-height:auto;border-left:none;border-bottom:1px solid #1e1e1e}}
</style>
