<template>
  <div class="reservation-page" dir="rtl">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">رزرو میز</h1>
      <div style="width:40px"></div>
    </div>

    <div class="content-scroll">
      <!-- Step Indicator -->
      <div class="steps-row">
        <div v-for="(s, i) in steps" :key="i" class="step-item" :class="{ active: step === i, done: step > i }">
          <div class="step-dot">{{ step > i ? '✓' : i + 1 }}</div>
          <span class="step-label">{{ s }}</span>
        </div>
      </div>

      <!-- Step 1: Date & Time -->
      <div v-if="step === 0" class="step-card">
        <h3 class="step-title">تاریخ و ساعت</h3>

        <div class="form-group">
          <label>تعداد نفرات</label>
          <div class="guests-row">
            <button class="qty-btn" @click="guests = Math.max(1, guests - 1)">−</button>
            <span class="qty-val">{{ guests }} نفر</span>
            <button class="qty-btn" @click="guests = Math.min(20, guests + 1)">+</button>
          </div>
        </div>

        <div class="form-group">
          <label>تاریخ</label>
          <div class="date-grid">
            <button
              v-for="d in availableDates"
              :key="d.value"
              class="date-chip"
              :class="{ active: selectedDate === d.value, disabled: !d.available }"
              :disabled="!d.available"
              @click="selectedDate = d.value"
            >
              <span class="date-day">{{ d.dayName }}</span>
              <span class="date-num">{{ d.label }}</span>
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>ساعت</label>
          <div class="time-grid">
            <button
              v-for="t in availableTimes"
              :key="t.value"
              class="time-chip"
              :class="{ active: selectedTime === t.value, disabled: !t.available }"
              :disabled="!t.available"
              @click="selectedTime = t.value"
            >{{ t.label }}</button>
          </div>
        </div>

        <button class="next-btn" :disabled="!selectedDate || !selectedTime" @click="step = 1">
          انتخاب میز
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
      </div>

      <!-- Step 2: Table Selection -->
      <div v-if="step === 1" class="step-card">
        <h3 class="step-title">انتخاب میز</h3>
        <p class="step-sub">میز مورد نظر خود را انتخاب کنید</p>
        <p v-if="tablesLoading" class="step-sub">در حال دریافت میزهای آزاد...</p>
        <p v-if="error" class="step-sub" style="color:#b84f4f">{{ error }}</p>
        <a href="/table-select" class="table-select-link">
          <div class="table-map-preview">
            <div class="table-grid">
              <div
                v-for="t in tables"
                :key="t.id"
                class="table-item"
                :class="[t.status, { selected: selectedTable?.id === t.id }]"
                @click.prevent="t.is_available && (selectedTable = t)"
              >
                <span>{{ t.label }}</span>
              </div>
            </div>
            <div class="map-overlay">
              <span>برای انتخاب کلیک کنید</span>
            </div>
          </div>
        </a>

        <div class="table-legend">
          <span class="legend-item"><i class="dot available"></i>خالی</span>
          <span class="legend-item"><i class="dot reserved"></i>رزرو</span>
          <span class="legend-item"><i class="dot occupied"></i>اشغال</span>
        </div>

        <div class="selected-table-info" v-if="selectedTable">
          <span class="stl">میز انتخابی:</span>
          <strong>{{ selectedTable.label }} ({{ selectedTable.capacity }} نفره)</strong>
        </div>

        <div class="btn-row">
          <button class="back-step-btn" @click="step = 0">برگشت</button>
          <button class="next-btn flex-1" @click="step = 2" :disabled="!selectedTable">مرحله بعد</button>
        </div>
      </div>

      <!-- Step 3: Confirm -->
      <div v-if="step === 2" class="step-card">
        <h3 class="step-title">تأیید رزرو</h3>

        <div class="confirm-summary">
          <div class="summary-row">
            <span>📅 تاریخ</span>
            <strong>{{ selectedDateLabel }}</strong>
          </div>
          <div class="summary-row">
            <span>⏰ ساعت</span>
            <strong>{{ selectedTime }}</strong>
          </div>
          <div class="summary-row">
            <span>👥 تعداد نفرات</span>
            <strong>{{ guests }} نفر</strong>
          </div>
          <div class="summary-row" v-if="selectedTable">
            <span>🪑 میز</span>
            <strong>{{ selectedTable?.label }}</strong>
          </div>
        </div>

        <div class="form-group">
          <label>نام برای رزرو</label>
          <input class="form-input" v-model="reserverName" placeholder="نام و نام خانوادگی" />
        </div>
        <div class="form-group">
          <label>شماره تماس</label>
          <input class="form-input" v-model="reserverPhone" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="ltr" type="tel" />
        </div>
        <div class="form-group">
          <label>توضیحات (اختیاری)</label>
          <textarea class="form-input" v-model="reserverNote" rows="2" placeholder="مثلاً: مناسبت ویژه، رژیم غذایی..."></textarea>
        </div>

        <div class="btn-row">
          <button class="back-step-btn" @click="step = 1">برگشت</button>
          <button class="next-btn flex-1" @click="submitReservation" :disabled="!reserverName || !reserverPhone || submitting">
            <span v-if="submitting" class="spinner"></span>
            <span v-else>ثبت رزرو</span>
          </button>
        </div>
      </div>

      <!-- Step 4: Success -->
      <div v-if="step === 3" class="step-card success-card">
        <div class="success-icon">✅</div>
        <h3>رزرو ثبت شد!</h3>
        <p>رزرو شما با موفقیت انجام شد. کد رزرو برای شما ارسال می‌شود.</p>
        <div class="confirm-summary">
          <div class="summary-row"><span>📅 تاریخ</span><strong>{{ selectedDateLabel }}</strong></div>
          <div class="summary-row"><span>⏰ ساعت</span><strong>{{ selectedTime }}</strong></div>
          <div class="summary-row"><span>👥 نفرات</span><strong>{{ guests }} نفر</strong></div>
        </div>
        <a href="/customer/dashboard" class="next-btn" style="text-decoration:none; display:block; text-align:center; margin-top:1rem;">بازگشت به خانه</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { createTableReservation, getAvailableTables } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const step = ref(0)
const guests = ref(2)
const selectedDate = ref('')
const selectedTime = ref('')
const selectedTable = ref(null)
const reserverName = ref('')
const reserverPhone = ref('')
const reserverNote = ref('')
const submitting = ref(false)
const tablesLoading = ref(false)
const error = ref('')

const steps = ['تاریخ و ساعت', 'انتخاب میز', 'تأیید']

const availableDates = Array.from({ length: 7 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() + i)
  const value = date.toISOString().slice(0, 10)
  return {
    value,
    label: new Intl.DateTimeFormat('fa-IR', { day: 'numeric' }).format(date),
    dayName: new Intl.DateTimeFormat('fa-IR', { weekday: 'long' }).format(date),
    available: true,
  }
})

const availableTimes = ['12:00', '13:00', '14:00', '18:00', '19:00', '20:00', '21:00', '22:00']
  .map(value => ({ value, label: value, available: true }))

const tables = ref([])

const selectedDateLabel = computed(() => {
  const d = availableDates.find(d => d.value === selectedDate.value)
  return d ? `${d.dayName} ${d.label}` : ''
})

async function loadTables() {
  if (!selectedDate.value || !selectedTime.value) return
  tablesLoading.value = true
  error.value = ''
  try {
    const data = await getAvailableTables({
      reservation_date: selectedDate.value,
      reservation_time: selectedTime.value,
      guest_count: guests.value,
    })
    tables.value = Array.isArray(data?.tables) ? data.tables : []
    if (selectedTable.value && !tables.value.some(t => t.id === selectedTable.value.id && t.is_available)) {
      selectedTable.value = null
    }
  } catch (err) {
    error.value = err?.message || 'خطا در دریافت میزها'
  } finally {
    tablesLoading.value = false
  }
}

async function submitReservation() {
  if (!selectedTable.value) return
  submitting.value = true
  error.value = ''
  try {
    await createTableReservation({
      customer_name: reserverName.value,
      mobile: reserverPhone.value,
      table: selectedTable.value.id,
      branch: selectedTable.value.branch || '',
      reservation_date: selectedDate.value,
      reservation_time: selectedTime.value,
      guest_count: guests.value,
      note: reserverNote.value,
    })
    step.value = 3
  } catch (err) {
    error.value = err?.message || 'خطا در ثبت رزرو'
  } finally {
    submitting.value = false
  }
}

function goBack() { window.history.back() }

onMounted(() => {
  selectedDate.value = availableDates[0]?.value || ''
  selectedTime.value = availableTimes[0]?.value || ''
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    reserverName.value = auth.customer_name || localStorage.getItem('customer_name') || ''
    reserverPhone.value = auth.mobile || localStorage.getItem('customer_phone') || ''
  } catch {}
  loadTables()
})

watch([selectedDate, selectedTime, guests], loadTables)
</script>

<style scoped>
.reservation-page { min-height: 100vh; background: #f7f0e8; direction: rtl; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8;
}
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #3f2a1d; }
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }

.content-scroll { padding: 1.25rem; padding-bottom: 4rem; }

.steps-row {
  display: flex; align-items: center; gap: 0; margin-bottom: 1.5rem;
  background: #fff; border-radius: 20px; padding: 1rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.step-item { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; flex: 1; }
.step-dot {
  width: 30px; height: 30px; border-radius: 50%;
  background: #f1e7db; color: #846b58; font-size: 0.78rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.step-item.active .step-dot { background: #6f4a31; color: #fff; }
.step-item.done .step-dot { background: #2e7d32; color: #fff; }
.step-label { font-size: 0.7rem; color: #846b58; font-weight: 600; }
.step-item.active .step-label { color: #6f4a31; }

.step-card { background: #fff; border-radius: 24px; padding: 1.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.07); margin-bottom: 1rem; }
.step-title { font-size: 1.05rem; font-weight: 800; color: #3f2a1d; margin: 0 0 0.3rem; }
.step-sub { font-size: 0.83rem; color: #846b58; margin: 0 0 1.2rem; }

.form-group { margin-bottom: 1.3rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 700; color: #846b58; margin-bottom: 0.5rem; }

.guests-row { display: flex; align-items: center; gap: 1.2rem; }
.qty-btn { width: 38px; height: 38px; border-radius: 50%; background: #6f4a31; color: #fff; border: none; font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: 700; }
.qty-val { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; min-width: 4rem; text-align: center; }

.date-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.5rem; }
.date-chip {
  display: flex; flex-direction: column; align-items: center; gap: 0.2rem;
  padding: 0.5rem 0.3rem; border-radius: 12px; border: 1.5px solid #e5ddd4;
  background: #fdf8f1; cursor: pointer; transition: all 0.2s;
}
.date-chip.active { background: #6f4a31; border-color: #6f4a31; }
.date-chip.active .date-day, .date-chip.active .date-num { color: #fff; }
.date-chip.disabled { opacity: 0.4; cursor: not-allowed; }
.date-day { font-size: 0.6rem; color: #846b58; font-weight: 600; }
.date-num { font-size: 0.9rem; color: #3f2a1d; font-weight: 800; }

.time-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; }
.time-chip {
  padding: 0.6rem 0.3rem; border-radius: 12px; border: 1.5px solid #e5ddd4;
  background: #fdf8f1; font-family: inherit; font-size: 0.82rem; font-weight: 700;
  color: #3f2a1d; cursor: pointer; transition: all 0.2s;
}
.time-chip.active { background: #6f4a31; border-color: #6f4a31; color: #fff; }
.time-chip.disabled { opacity: 0.4; cursor: not-allowed; }

.table-select-link { text-decoration: none; display: block; }
.table-map-preview {
  border-radius: 16px; overflow: hidden; border: 1.5px solid #e5ddd4;
  position: relative; background: #fdf8f1;
}
.table-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; padding: 0.75rem; }
.table-item {
  aspect-ratio: 1; border-radius: 10px; display: flex; align-items: center;
  justify-content: center; font-size: 0.7rem; font-weight: 700;
}
.table-item.available { background: #e8f5e9; color: #2e7d32; }
.table-item.reserved { background: #fff8e1; color: #f57f17; }
.table-item.occupied { background: #ffebee; color: #b71c1c; }
.map-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 0.9rem; font-weight: 700; border-radius: 16px;
}

.table-legend { display: flex; gap: 1rem; justify-content: center; margin: 0.75rem 0; }
.legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.75rem; color: #846b58; }
.dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.dot.available { background: #e8f5e9; border: 1px solid #2e7d32; }
.dot.reserved { background: #fff8e1; border: 1px solid #f57f17; }
.dot.occupied { background: #ffebee; border: 1px solid #b71c1c; }

.selected-table-info { background: #f1e7db; border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; margin-bottom: 1rem; }
.stl { color: #846b58; }

.confirm-summary { background: #fdf8f1; border-radius: 16px; padding: 1rem; margin-bottom: 1.2rem; }
.summary-row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; font-size: 0.88rem; }
.summary-row + .summary-row { border-top: 1px solid #e5ddd4; }
.summary-row span { color: #846b58; }
.summary-row strong { color: #3f2a1d; }

.form-input { width: 100%; padding: 0.85rem 1rem; border: 1.5px solid #e5ddd4; border-radius: 14px; background: #fdf8f1; font-size: 0.92rem; font-family: inherit; outline: none; box-sizing: border-box; resize: none; }
.form-input:focus { border-color: #6f4a31; }

.btn-row { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.flex-1 { flex: 1; }
.back-step-btn { padding: 0.9rem 1.2rem; border: 1.5px solid #e5ddd4; border-radius: 14px; background: #fdf8f1; color: #3f2a1d; font-size: 0.9rem; font-weight: 700; font-family: inherit; cursor: pointer; flex-shrink: 0; }
.next-btn {
  padding: 0.9rem 1.5rem; background: #6f4a31; color: #fff; border: none;
  border-radius: 14px; font-size: 0.95rem; font-weight: 700; font-family: inherit; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  transition: opacity 0.2s;
}
.next-btn:disabled { opacity: 0.45; }

.success-card { text-align: center; }
.success-icon { font-size: 4rem; margin-bottom: 0.5rem; }
.success-card h3 { font-size: 1.2rem; font-weight: 800; color: #2e7d32; margin: 0 0 0.5rem; }
.success-card p { font-size: 0.88rem; color: #846b58; margin: 0 0 1.5rem; }

.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
