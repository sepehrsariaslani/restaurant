<template>
  <div class="delivery-page" dir="rtl">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">نوع سفارش</h1>
      <div style="width:40px"></div>
    </div>

    <div class="type-hero">
      <div class="type-tabs">
        <button
          class="type-tab"
          :class="{ active: orderType === 'delivery' }"
          @click="orderType = 'delivery'"
        >
          <span class="tab-icon">🛵</span>
          تحویل درب منزل
        </button>
        <button
          class="type-tab"
          :class="{ active: orderType === 'pickup' }"
          @click="orderType = 'pickup'"
        >
          <span class="tab-icon">🏃</span>
          بیرون‌بر
        </button>
      </div>
    </div>

    <!-- Delivery Mode -->
    <div v-if="orderType === 'delivery'" class="mode-content">
      <div class="info-card">
        <div class="info-icon">📍</div>
        <div class="info-body">
          <strong>آدرس تحویل</strong>
          <p v-if="selectedAddress">{{ selectedAddress.address }}</p>
          <p v-else class="muted">آدرسی انتخاب نشده</p>
        </div>
        <a href="/customer/addresses" class="change-link">تغییر</a>
      </div>

      <div class="estimate-card">
        <div class="estimate-row">
          <span class="est-label">⏱ زمان تحویل</span>
          <span class="est-value">۳۰–۴۵ دقیقه</span>
        </div>
        <div class="estimate-row">
          <span class="est-label">🛵 هزینه ارسال</span>
          <span class="est-value">رایگان (بالای ۱۵۰,۰۰۰ تومان)</span>
        </div>
      </div>

      <div class="note-card">
        <label class="note-label">یادداشت برای پیک (اختیاری)</label>
        <textarea v-model="deliveryNote" class="note-input" rows="3" placeholder="مثلاً: زنگ نزنید، در را باز بگذارید..."></textarea>
      </div>
    </div>

    <!-- Pickup Mode -->
    <div v-else class="mode-content">
      <div class="branch-select-label">انتخاب شعبه</div>
      <div class="branch-radio-list">
        <label
          v-for="b in branches"
          :key="b.id"
          class="branch-radio"
          :class="{ active: selectedBranch === b.id }"
        >
          <input type="radio" :value="b.id" v-model="selectedBranch" hidden />
          <div class="radio-dot" :class="{ active: selectedBranch === b.id }"></div>
          <div class="branch-info">
            <strong>{{ b.name }}</strong>
            <small>{{ b.address }}</small>
            <small class="branch-time">آماده در {{ b.prepTime }} دقیقه</small>
          </div>
          <span class="branch-status" :class="b.isOpen ? 'open' : 'closed'">
            {{ b.isOpen ? 'باز' : 'بسته' }}
          </span>
        </label>
      </div>

      <div class="pickup-estimate" v-if="selectedBranchObj">
        <div class="estimate-row">
          <span class="est-label">⏱ آماده‌سازی</span>
          <span class="est-value">{{ selectedBranchObj.prepTime }} دقیقه</span>
        </div>
      </div>
    </div>

    <div class="bottom-cta">
      <button class="confirm-btn" @click="confirm" :disabled="!canConfirm">
        ادامه و مشاهده منو
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getBranches } from '@/utils/api'

const orderType = ref('delivery')
const deliveryNote = ref('')
const selectedBranch = ref('')
const branches = ref([])

const selectedBranchObj = computed(() => branches.value.find(b => b.id === selectedBranch.value))

const selectedAddress = ref(null)
onMounted(async () => {
  try {
    const addr = localStorage.getItem('selected_address')
    if (addr) selectedAddress.value = JSON.parse(addr)
  } catch {}
  const params = new URLSearchParams(window.location.search)
  if (params.get('type') === 'pickup') orderType.value = 'pickup'
  try {
    const data = await getBranches()
    branches.value = Array.isArray(data?.branches) ? data.branches : []
    selectedBranch.value = branches.value.find(b => b.isOpen)?.id || branches.value[0]?.id || ''
  } catch {}
})

const canConfirm = computed(() => {
  if (orderType.value === 'delivery') return true
  return Boolean(selectedBranch.value) && (selectedBranchObj.value?.isOpen ?? false)
})

function goBack() { window.history.back() }

function confirm() {
  try {
    localStorage.setItem('order_type', orderType.value)
    if (orderType.value === 'pickup' && selectedBranchObj.value) {
      localStorage.setItem('selected_branch', JSON.stringify(selectedBranchObj.value))
    }
    if (deliveryNote.value) {
      localStorage.setItem('delivery_note', deliveryNote.value)
    }
  } catch {}
  window.location.href = '/menu'
}
</script>

<style scoped>
.delivery-page { min-height: 100vh; background: #f7f0e8; direction: rtl; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8;
}
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #3f2a1d; }
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }

.type-hero { background: #fff; padding: 1.25rem; border-bottom: 1px solid #ede3d8; }
.type-tabs { display: flex; gap: 0.75rem; background: #f7f0e8; border-radius: 18px; padding: 0.35rem; }
.type-tab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0.85rem 0.5rem; border-radius: 14px; border: none;
  background: transparent; color: #846b58; font-size: 0.9rem; font-weight: 700;
  font-family: inherit; cursor: pointer; transition: all 0.2s;
}
.type-tab.active { background: #6f4a31; color: #fff; box-shadow: 0 4px 12px rgba(111,74,49,0.3); }
.tab-icon { font-size: 1.2rem; }

.mode-content { padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem; padding-bottom: 8rem; }

.info-card {
  background: #fff; border-radius: 20px; padding: 1.1rem;
  display: flex; align-items: center; gap: 0.9rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.info-icon { font-size: 1.5rem; flex-shrink: 0; }
.info-body { flex: 1; }
.info-body strong { display: block; font-size: 0.9rem; font-weight: 700; color: #3f2a1d; margin-bottom: 0.25rem; }
.info-body p { margin: 0; font-size: 0.83rem; color: #3f2a1d; }
.info-body p.muted { color: #b0997f; }
.change-link { font-size: 0.82rem; font-weight: 700; color: #6f4a31; text-decoration: none; flex-shrink: 0; }

.estimate-card { background: #fff; border-radius: 20px; padding: 1.1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.estimate-row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; font-size: 0.88rem; }
.estimate-row + .estimate-row { border-top: 1px solid #f1e7db; }
.est-label { color: #846b58; }
.est-value { font-weight: 700; color: #3f2a1d; }

.note-card { background: #fff; border-radius: 20px; padding: 1.1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.note-label { display: block; font-size: 0.82rem; font-weight: 700; color: #846b58; margin-bottom: 0.6rem; }
.note-input { width: 100%; border: 1.5px solid #e5ddd4; border-radius: 14px; padding: 0.8rem 1rem; font-family: inherit; font-size: 0.88rem; background: #fdf8f1; outline: none; resize: none; box-sizing: border-box; }

.branch-select-label { font-size: 0.88rem; font-weight: 700; color: #846b58; padding: 0 0.25rem; }
.branch-radio-list { display: flex; flex-direction: column; gap: 0.65rem; }
.branch-radio {
  display: flex; align-items: center; gap: 0.9rem; background: #fff;
  border-radius: 18px; padding: 1rem 1.1rem; border: 2px solid transparent;
  cursor: pointer; transition: border-color 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.branch-radio.active { border-color: #6f4a31; }
.radio-dot { width: 20px; height: 20px; border-radius: 50%; border: 2px solid #c5b09a; flex-shrink: 0; transition: all 0.2s; }
.radio-dot.active { background: #6f4a31; border-color: #6f4a31; }
.branch-info { flex: 1; }
.branch-info strong { display: block; font-size: 0.9rem; font-weight: 700; color: #3f2a1d; }
.branch-info small { display: block; font-size: 0.75rem; color: #846b58; }
.branch-time { color: #6f4a31 !important; font-weight: 600 !important; }
.branch-status { font-size: 0.72rem; font-weight: 700; border-radius: 999px; padding: 3px 8px; flex-shrink: 0; }
.branch-status.open { background: #e8f5e9; color: #2e7d32; }
.branch-status.closed { background: #ffebee; color: #b71c1c; }

.pickup-estimate { background: #fff; border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

.bottom-cta { position: fixed; bottom: 0; left: 0; right: 0; padding: 1rem; background: rgba(247,240,232,0.95); backdrop-filter: blur(8px); border-top: 1px solid #ede3d8; }
.confirm-btn {
  width: 100%; padding: 1rem; background: #6f4a31; color: #fff; border: none;
  border-radius: 16px; font-size: 1rem; font-weight: 700; font-family: inherit; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  transition: opacity 0.2s;
}
.confirm-btn:disabled { opacity: 0.45; }
</style>
