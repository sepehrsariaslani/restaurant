<template>
  <div class="reservation-page" dir="rtl">
    <CustomerPageHeader eyebrow="میز و پذیرایی" title="رزرو میز" subtitle="زمان، تعداد نفرات و میز مناسب را در چند قدم انتخاب کنید." fallback-href="/menu">
      <template #eyebrow-icon><CalendarDays :size="14" aria-hidden="true" /></template>
    </CustomerPageHeader>

    <div class="content-scroll">
      <!-- Step Indicator -->
      <div class="steps-row">
        <div v-for="(s, i) in steps" :key="i" :aria-current="step === i ? 'step' : undefined" class="step-item" :class="{ active: step === i, done: step > i }">
          <div class="step-dot"><Check v-if="step > i" :size="15" aria-hidden="true" /><span v-else>{{ i + 1 }}</span></div>
          <span class="step-label">{{ s }}</span>
        </div>
      </div>

      <!-- Step 1: Date & Time -->
      <div v-if="step === 0" class="step-card">
        <h3 class="step-title">تاریخ و ساعت</h3>

        <div class="form-group">
          <label>تعداد نفرات</label>
          <div class="guests-row">
            <button class="qty-btn" type="button" aria-label="کم‌کردن تعداد نفرات" @click="guests = Math.max(1, guests - 1)">−</button>
            <span class="qty-val">{{ guests }} نفر</span>
            <button class="qty-btn" type="button" aria-label="زیادکردن تعداد نفرات" @click="guests = Math.min(20, guests + 1)">+</button>
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

        <button class="next-btn" type="button" :disabled="!selectedDate || !selectedTime || !reservationTimeIsFuture(selectedDate, selectedTime)" @click="step = 1">
          انتخاب میز
          <ArrowLeft :size="18" aria-hidden="true" />
        </button>
      </div>

      <!-- Step 2: Table Selection -->
      <div v-if="step === 1" class="step-card">
        <h3 class="step-title">انتخاب میز</h3>
        <p class="step-sub">فقط میزهای آزاد در زمان انتخابی قابل رزرو هستند.</p>
        <label v-if="areas.length > 1" class="form-group">سالن / محل میز<select class="form-input" v-model="selectedArea"><option value="">همه سالن‌ها</option><option v-for="area in areas" :key="area" :value="area">{{ customerTableAreaLabel(area) }}</option></select></label>
        <p v-if="tablesLoading" class="step-sub" role="status" aria-live="polite">
          <LoaderCircle :size="16" class="reservation-spinner" aria-hidden="true" />
          در حال دریافت میزهای آزاد...
        </p>
        <div v-if="error" class="reservation-error" role="alert">
          <span>{{ error }}</span>
          <button class="retry-tables-btn" type="button" :disabled="tablesLoading" @click="loadTables">
            <RefreshCw :size="15" aria-hidden="true" /> تلاش دوباره
          </button>
        </div>
        <div v-if="tables.length" class="table-map-preview" role="group" aria-label="میزهای قابل رزرو">
          <div class="table-grid">
            <button
              v-for="t in visibleTables"
              :key="t.id"
              class="table-item"
              :class="[t.status, { selected: selectedTable?.id === t.id }]"
              type="button"
              :disabled="!t.is_available"
              :aria-pressed="selectedTable?.id === t.id"
              :aria-label="`${t.is_available ? 'میز آزاد' : t.status === 'reserved' ? 'میز رزروشده' : 'میز اشغال'}، ${t.label}`"
              @click="selectedTable = t"
            >
              <Armchair :size="18" aria-hidden="true" />
              <span>میز {{ t.label }}</span><small v-if="t.branch">{{ customerTableAreaLabel(t.branch) }}</small>
            </button>
          </div>
        </div>
        <div v-else-if="!tablesLoading && !error" class="tables-empty" role="status">
          <Armchair :size="20" aria-hidden="true" />
          <span>برای این زمان میزی پیدا نشد؛ ساعت دیگری را انتخاب کنید.</span>
        </div>

        <div class="table-legend">
          <span class="legend-item"><i class="dot available"></i>خالی</span>
          <span class="legend-item"><i class="dot reserved"></i>رزرو</span>
          <span class="legend-item"><i class="dot occupied"></i>اشغال</span>
        </div>

        <div class="selected-table-info" v-if="selectedTable">
          <span class="stl">میز انتخابی:</span>
          <strong>{{ selectedTable.label }}</strong>
        </div>

        <div class="btn-row">
          <button class="back-step-btn" type="button" @click="step = 0">برگشت</button>
          <button class="next-btn flex-1" type="button" @click="step = 2" :disabled="!selectedTable || tablesLoading">مرحله بعد</button>
        </div>
      </div>

      <!-- Step 3: Confirm -->
      <div v-if="step === 2" class="step-card">
        <h3 class="step-title">تأیید رزرو</h3>

        <div class="confirm-summary">
          <div class="summary-row">
            <span><CalendarDays :size="16" aria-hidden="true" /> تاریخ</span>
            <strong>{{ selectedDateLabel }}</strong>
          </div>
          <div class="summary-row">
            <span><Clock3 :size="16" aria-hidden="true" /> ساعت</span>
            <strong>{{ selectedTime }}</strong>
          </div>
          <div class="summary-row">
            <span><UsersRound :size="16" aria-hidden="true" /> تعداد نفرات</span>
            <strong>{{ guests }} نفر</strong>
          </div>
          <div class="summary-row" v-if="selectedTable">
            <span><Armchair :size="16" aria-hidden="true" /> میز</span>
            <strong>{{ selectedTable?.label }}</strong>
          </div>
        </div>

        <div class="form-group">
          <label for="reservation-name">نام برای رزرو</label>
          <input id="reservation-name" class="form-input" v-model="reserverName" placeholder="نام و نام خانوادگی" autocomplete="name" />
        </div>
        <div class="form-group">
          <label for="reservation-phone">شماره تماس</label>
          <input id="reservation-phone" class="form-input" v-model="reserverPhone" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="ltr" type="tel" autocomplete="tel" />
        </div>
        <div class="form-group">
          <label for="reservation-note">توضیحات (اختیاری)</label>
          <textarea id="reservation-note" class="form-input" v-model="reserverNote" rows="2" placeholder="مثلاً: مناسبت ویژه، رژیم غذایی..."></textarea>
        </div>

        <p v-if="error" class="reservation-error" role="alert">{{ error }}</p>

        <div class="btn-row">
          <button class="back-step-btn" type="button" @click="step = 1">برگشت</button>
          <button class="next-btn flex-1" type="button" @click="submitReservation" :disabled="!reserverName || !reserverPhone || submitting">
            <LoaderCircle v-if="submitting" :size="18" class="reservation-spinner" aria-hidden="true" />
            <span v-else>ثبت رزرو</span>
          </button>
        </div>
      </div>

      <!-- Step 4: Success -->
      <div v-if="step === 3" class="step-card success-card">
        <CircleCheck class="success-icon" :size="48" aria-hidden="true" />
        <h3>درخواست رزرو ثبت شد</h3>
        <p>رزرو شما در انتظار تأیید رستوران است. کد پیگیری را نگه دارید.</p>
        <strong class="reservation-code" dir="ltr">{{ reservation?.name }}</strong>
        <div class="confirm-summary">
          <div class="summary-row"><span><CalendarDays :size="16" aria-hidden="true" /> تاریخ</span><strong>{{ selectedDateLabel }}</strong></div>
          <div class="summary-row"><span><Clock3 :size="16" aria-hidden="true" /> ساعت</span><strong>{{ selectedTime }}</strong></div>
          <div class="summary-row"><span><UsersRound :size="16" aria-hidden="true" /> نفرات</span><strong>{{ guests }} نفر</strong></div>
        </div>
        <a href="/customer/dashboard" class="next-btn" style="text-decoration:none; display:block; text-align:center; margin-top:1rem;">بازگشت به حساب من</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Armchair, ArrowLeft, CalendarDays, Check, CircleCheck, Clock3, LoaderCircle, RefreshCw, UsersRound } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { isValidCustomerMobile, reservationTimeIsFuture } from '@/utils/customerOrderValidation'
import { createTableReservation, getAvailableTables } from '@/utils/api'
import { customerTableAreaLabel } from '@/utils/customerTableAreas'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const reservation = ref(null)
const selectedArea = ref('')
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
let tablesRequestId = 0

const steps = ['تاریخ و ساعت', 'انتخاب میز', 'تأیید']

const availableDates = Array.from({ length: 7 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() + i)
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  return {
    value,
    label: new Intl.DateTimeFormat('fa-IR', { day: 'numeric' }).format(date),
    dayName: new Intl.DateTimeFormat('fa-IR', { weekday: 'long' }).format(date),
    available: true,
  }
})

const availableTimes = computed(() => ['12:00', '13:00', '14:00', '18:00', '19:00', '20:00', '21:00', '22:00']
  .map(value => ({ value, label: value, available: reservationTimeIsFuture(selectedDate.value, value) })))

const tables = ref([])
const areas = computed(() => [...new Set(tables.value.map(t => t.branch).filter(Boolean))])
const visibleTables = computed(() => selectedArea.value ? tables.value.filter(t => t.branch === selectedArea.value) : tables.value)
watch(selectedArea, () => { selectedTable.value = null })

const selectedDateLabel = computed(() => {
  const d = availableDates.find(d => d.value === selectedDate.value)
  return d ? `${d.dayName} ${d.label}` : ''
})

async function loadTables() {
  if (!selectedDate.value || !selectedTime.value) { tablesRequestId++; tables.value = []; selectedTable.value = null; tablesLoading.value = false; return }
  const requestId = ++tablesRequestId
  tablesLoading.value = true
  error.value = ''
  tables.value = []
  selectedTable.value = null
  try {
    const data = await getAvailableTables({
      reservation_date: selectedDate.value,
      reservation_time: selectedTime.value,
      guest_count: guests.value,
    })
    if (requestId !== tablesRequestId) return
    tables.value = Array.isArray(data?.tables) ? data.tables : []
  } catch (err) {
    if (requestId !== tablesRequestId) return
    error.value = err?.message || 'خطا در دریافت میزها'
    tables.value = []
    selectedTable.value = null
  } finally {
    if (requestId === tablesRequestId) tablesLoading.value = false
  }
}

async function submitReservation() {
  if (!selectedTable.value || submitting.value) return
  if (!reserverName.value.trim() || !isValidCustomerMobile(reserverPhone.value)) { error.value = 'نام و شماره موبایل معتبر را وارد کنید.'; return }
  if (!reservationTimeIsFuture(selectedDate.value, selectedTime.value)) { error.value = 'زمان گذشته قابل رزرو نیست؛ ساعت دیگری انتخاب کنید.'; step.value = 0; return }
  submitting.value = true
  error.value = ''
  try {
    const result = await createTableReservation({
      customer_name: reserverName.value,
      mobile: reserverPhone.value,
      table: selectedTable.value.id,
      branch: selectedTable.value.branch || '',
      reservation_date: selectedDate.value,
      reservation_time: selectedTime.value,
      guest_count: guests.value,
      note: reserverNote.value,
    })
    reservation.value = result?.reservation
    if (!reservation.value?.name) throw new Error('ثبت رزرو تأیید نشد؛ دوباره تلاش کنید.')
    step.value = 3
  } catch (err) {
    error.value = err?.message || 'خطا در ثبت رزرو'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  selectedDate.value = availableDates[0]?.value || ''
  selectedTime.value = availableTimes.value.find(t => t.available)?.value || ''
  if (new URLSearchParams(window.location.search).get('step') === 'table') step.value = 1
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    reserverName.value = auth.customer_name || localStorage.getItem('customer_name') || ''
    reserverPhone.value = auth.mobile || localStorage.getItem('customer_phone') || ''
  } catch {}
})

watch(selectedDate, () => { if (!availableTimes.value.some(t => t.value === selectedTime.value && t.available)) selectedTime.value = availableTimes.value.find(t => t.available)?.value || '' })
watch([selectedDate, selectedTime, guests], loadTables)
</script>

<style scoped>
.reservation-code { display: block; padding: 1rem; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); border-radius: var(--ds-radius-md); margin-block: 1rem; }
.table-item small { font-size: .72rem; }

.reservation-page { min-height: 100vh; background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); direction: rtl; }

.content-scroll { width: min(100%, 840px); margin-inline: auto; padding: 1.25rem 1rem 8rem; }

.steps-row {
  display: flex; align-items: center; gap: 0; margin-bottom: 1.5rem;
  background: var(--ds-color-surface-raised); border: 1px solid var(--ds-color-border); border-radius: 20px; padding: 1rem;
  box-shadow: var(--ds-shadow-sm);
}
.step-item { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; flex: 1; }
.step-dot {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--ds-color-surface-muted); color: var(--ds-color-text-secondary); font-size: 0.78rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.step-item.active .step-dot { background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); }
.step-item.done .step-dot { background: var(--ds-color-status-success); color: var(--ds-color-status-success-foreground, var(--ds-color-text-inverse)); }
.step-label { font-size: 0.7rem; color: var(--ds-color-text-muted); font-weight: 600; }
.step-item.active .step-label { color: var(--ds-color-action-primary); }

.step-card { background: var(--ds-color-surface-raised); border: 1px solid var(--ds-color-border); border-radius: 24px; padding: 1.5rem; box-shadow: var(--ds-shadow-sm); margin-bottom: 1rem; }
.step-title { font-size: 1.05rem; font-weight: 800; color: var(--ds-color-text-primary); margin: 0 0 0.3rem; }
.step-sub { font-size: 0.83rem; color: var(--ds-color-text-secondary); margin: 0 0 1.2rem; }

.form-group { margin-bottom: 1.3rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 700; color: var(--ds-color-text-secondary); margin-bottom: 0.5rem; }

.guests-row { display: flex; align-items: center; gap: 1.2rem; }
.qty-btn { width: 44px; height: 44px; border-radius: 50%; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); border: none; font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: 700; }
.qty-val { font-size: 1.1rem; font-weight: 800; color: var(--ds-color-text-primary); min-width: 4rem; text-align: center; }

.date-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.5rem; }
.date-chip {
  display: flex; flex-direction: column; align-items: center; gap: 0.2rem;
  min-height: 52px; padding: 0.5rem 0.2rem; border-radius: 12px; border: 1.5px solid var(--ds-color-border);
  background: var(--ds-color-surface); cursor: pointer; transition: all 0.2s;
}
.date-chip.active { background: var(--ds-color-action-primary); border-color: var(--ds-color-action-primary); }
.date-chip.active .date-day, .date-chip.active .date-num { color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); }
.date-chip.disabled { opacity: 0.4; cursor: not-allowed; }
.date-day { font-size: 0.6rem; color: var(--ds-color-text-muted); font-weight: 600; }
.date-num { font-size: 0.9rem; color: var(--ds-color-text-primary); font-weight: 800; }

.time-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; }
.time-chip {
  padding: 0.6rem 0.3rem; border-radius: 12px; border: 1.5px solid var(--ds-color-border);
  background: var(--ds-color-surface); font-family: inherit; font-size: 0.82rem; font-weight: 700;
  color: var(--ds-color-text-primary); cursor: pointer; transition: all 0.2s;
}
.time-chip.active { background: var(--ds-color-action-primary); border-color: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); }
.time-chip.disabled { opacity: 0.4; cursor: not-allowed; }
.date-chip:focus-visible, .time-chip:focus-visible, .qty-btn:focus-visible, .next-btn:focus-visible, .back-step-btn:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring);
  outline-offset: 2px;
}
.table-map-preview {
  border-radius: 16px; overflow: hidden; border: 1.5px solid var(--ds-color-border);
  position: relative; background: var(--ds-color-surface);
}
.table-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; padding: 0.75rem; }
.table-item {
  aspect-ratio: 1; border-radius: 10px; display: flex; align-items: center;
  justify-content: center; gap: .35rem; font-size: 0.7rem; font-weight: 700;
  font-family: inherit; cursor: pointer; min-width: 0; border: 0;
}
.table-item.available { background: var(--ds-color-status-success-soft); color: var(--ds-color-status-success); }
.table-item.reserved { background: var(--ds-color-status-warning-soft); color: var(--ds-color-status-warning); }
.table-item.occupied { background: var(--ds-color-status-danger-soft); color: var(--ds-color-status-danger); }
.table-item:disabled { cursor: not-allowed; opacity: .7; }
.table-item.selected { background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); }
.table-item:focus-visible, .retry-tables-btn:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.reservation-spinner { flex: none; animation: spin .8s linear infinite; }
.reservation-error { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin: .8rem 0; color: var(--ds-color-status-danger); font-size: .84rem; }
.retry-tables-btn { display: inline-flex; min-height: 40px; align-items: center; justify-content: center; gap: .35rem; padding: 0 .7rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); font: inherit; font-size: .78rem; font-weight: 700; cursor: pointer; }
.tables-empty { display: flex; align-items: center; gap: .6rem; padding: 1rem; border-radius: 16px; background: var(--ds-color-surface-muted); color: var(--ds-color-text-secondary); font-size: .86rem; line-height: 1.7; }
.table-legend { display: flex; gap: 1rem; justify-content: center; margin: 0.75rem 0; }
.legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.75rem; color: var(--ds-color-text-secondary); }
.dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.dot.available { background: var(--ds-color-status-success-soft); border: 1px solid var(--ds-color-status-success); }
.dot.reserved { background: var(--ds-color-status-warning-soft); border: 1px solid var(--ds-color-status-warning); }
.dot.occupied { background: var(--ds-color-status-danger-soft); border: 1px solid var(--ds-color-status-danger); }

.selected-table-info { background: var(--ds-color-surface-muted); border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; margin-bottom: 1rem; }
.stl { color: var(--ds-color-text-secondary); }

.confirm-summary { background: var(--ds-color-surface); border-radius: 16px; padding: 1rem; margin-bottom: 1.2rem; }
.summary-row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; font-size: 0.88rem; }
.summary-row + .summary-row { border-top: 1px solid var(--ds-color-border); }
.summary-row span { display: inline-flex; align-items: center; gap: .45rem; color: var(--ds-color-text-secondary); }
.summary-row strong { color: var(--ds-color-text-primary); }

.form-input { width: 100%; padding: 0.85rem 1rem; border: 1.5px solid var(--ds-color-border); border-radius: 14px; background: var(--ds-color-surface); color: var(--ds-color-text-primary); font-size: 0.92rem; font-family: inherit; outline: none; box-sizing: border-box; resize: none; }
.form-input:focus { border-color: var(--ds-color-action-primary); box-shadow: 0 0 0 3px var(--ds-color-action-primary-soft); }

.btn-row { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.flex-1 { flex: 1; }
.back-step-btn { min-height: 44px; padding: 0.75rem 1.2rem; border: 1.5px solid var(--ds-color-border); border-radius: 14px; background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); font-size: 0.9rem; font-weight: 700; font-family: inherit; cursor: pointer; flex-shrink: 0; }
.next-btn {
  padding: 0.9rem 1.5rem; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); border: none;
  border-radius: 14px; font-size: 0.95rem; font-weight: 700; font-family: inherit; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  transition: opacity 0.2s;
}
.next-btn:disabled { opacity: 0.45; }

.success-card { text-align: center; }
.success-icon { margin-bottom: 0.5rem; color: var(--ds-color-status-success); }
.success-card h3 { font-size: 1.2rem; font-weight: 800; color: var(--ds-color-status-success); margin: 0 0 0.5rem; }
.success-card p { font-size: 0.88rem; color: var(--ds-color-text-secondary); margin: 0 0 1.5rem; }

@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .step-dot, .date-chip, .time-chip, .table-item { transition: none; } .reservation-spinner { animation: none; } }
</style>
