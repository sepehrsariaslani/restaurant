<template>
  <div class="persian-range-date-input" :class="{ disabled }">
    <div class="date-input-shell">
      <input
        ref="inputRef"
        :value="displayValue"
        class="management-date-input"
        :class="inputClass"
        type="text"
        :placeholder="placeholder || 'انتخاب بازه تاریخ'"
        readonly
        :disabled="disabled"
        :aria-expanded="isOpen"
        aria-haspopup="dialog"
        @click="openCalendar"
        @keydown.enter.prevent="openCalendar"
        @keydown.space.prevent="openCalendar"
      />
      <button
        type="button"
        class="date-trigger"
        :disabled="disabled"
        aria-label="باز کردن انتخابگر بازه تاریخ"
        :aria-expanded="isOpen"
        @click="openCalendar"
      >
        <CalendarRange :size="17" :stroke-width="2.1" />
      </button>
    </div>

    <Teleport to="body">
      <Transition name="persian-calendar">
        <div v-if="isOpen" class="calendar-layer" dir="rtl">
          <!-- پس‌زمینه: کلیک روی آن تقویم را می‌بندد -->
          <div class="calendar-backdrop" @click="closeCalendar"></div>

          <div
            class="calendar-popover"
            :style="{ ...popoverStyle, zIndex: props.zIndex }"
            role="dialog"
            aria-label="انتخاب بازه تاریخ شمسی"
            @click.stop
          >
            <header class="calendar-header">
              <div class="calendar-heading">
                <span class="calendar-kicker">انتخاب بازه تاریخ</span>
                <button type="button" class="calendar-month-button" @click="showMonthPicker = !showMonthPicker">
                  {{ monthNames[activeMonth - 1] }} {{ faNumber(activeYear) }}
                  <ChevronDown :size="15" :class="{ rotated: showMonthPicker }" />
                </button>
              </div>
              <button type="button" class="calendar-close" aria-label="بستن" @click="closeCalendar">
                <X :size="16" />
              </button>
            </header>

            <div v-if="showMonthPicker" class="month-picker" aria-label="انتخاب ماه">
              <button
                v-for="(month, index) in monthNames"
                :key="month"
                type="button"
                class="month-option"
                :class="{ active: activeMonth === index + 1 }"
                @click="selectMonth(index + 1)"
              >
                {{ month }}
              </button>
            </div>

            <template v-else>
              <div class="calendar-toolbar">
                <button type="button" class="nav-button" aria-label="ماه قبل" @click="moveMonth(-1)">
                  <ChevronRight :size="18" />
                </button>
                <span class="calendar-year-label">سال {{ faNumber(activeYear) }}</span>
                <button type="button" class="nav-button" aria-label="ماه بعد" @click="moveMonth(1)">
                  <ChevronLeft :size="18" />
                </button>
              </div>

              <div class="weekday-row" aria-hidden="true">
                <span v-for="day in weekDays" :key="day">{{ day }}</span>
              </div>

              <div class="calendar-grid" role="grid">
                <template v-for="cell in calendarCells" :key="cell.key">
                  <span v-if="cell.blank" class="calendar-cell calendar-cell--blank"></span>
                  <button
                    v-else
                    type="button"
                    role="gridcell"
                    class="calendar-day"
                    :class="dayClasses(cell.iso)"
                    :aria-label="`${monthNames[activeMonth - 1]} ${cell.day}`"
                    :aria-selected="cell.iso === tempStart || cell.iso === tempEnd"
                    @click="pickDate(cell.iso)"
                  >
                    {{ faNumber(cell.day) }}
                  </button>
                </template>
              </div>
            </template>

            <footer class="calendar-footer">
              <button type="button" class="today-button" @click="pickToday">امروز</button>
              <button type="button" class="clear-date-button" @click="clearRange">پاک کردن</button>
              <span v-if="!tempStart" class="calendar-hint">تاریخ شروع را انتخاب کنید</span>
              <span v-else-if="!tempEnd" class="calendar-hint">حالا تاریخ پایان را انتخاب کنید</span>
              <button v-else type="button" class="confirm-button" @click="confirmRange">تأیید بازه</button>
            </footer>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { CalendarRange, ChevronDown, ChevronLeft, ChevronRight, X } from 'lucide-vue-next'
import { jalaaliMonthLength, jalaaliToDateObject, toGregorian, toJalaali } from 'jalaali-js'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ date_from: '', date_to: '' }) },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  inputClass: { type: [String, Array, Object], default: '' },
  zIndex: { type: Number, default: 13000 },
})

const emit = defineEmits(['update:modelValue'])

const inputRef = ref(null)
const isOpen = ref(false)
const showMonthPicker = ref(false)
const popoverStyle = ref({})

const monthNames = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]
const weekDays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

const todayIso = getLocalIsoDate()
const todayJalali = isoToJalali(todayIso)
const activeYear = ref(todayJalali.year)
const activeMonth = ref(todayJalali.month)

const tempStart = ref(normalizeDateOnly(props.modelValue?.date_from))
const tempEnd = ref(normalizeDateOnly(props.modelValue?.date_to))

const displayValue = computed(() => {
  const from = isoToJalali(tempStart.value)
  const to = isoToJalali(tempEnd.value)
  if (from && to) {
    return `${faNumber(from.year)}/${faNumber(from.month, 2)}/${faNumber(from.day, 2)} تا ${faNumber(to.year)}/${faNumber(to.month, 2)}/${faNumber(to.day, 2)}`
  }
  if (from) {
    return `از ${faNumber(from.year)}/${faNumber(from.month, 2)}/${faNumber(from.day, 2)} ...`
  }
  return ''
})

const calendarCells = computed(() => {
  const daysInMonth = jalaaliMonthLength(activeYear.value, activeMonth.value)
  const dayOfWeek = jalaaliToDateObject(activeYear.value, activeMonth.value, 1).getDay()
  const firstDayOfWeek = (dayOfWeek + 1) % 7
  const cells = []

  for (let index = 0; index < firstDayOfWeek; index += 1) {
    cells.push({ key: `blank-${index}`, blank: true })
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({
      key: jalaliToIso(activeYear.value, activeMonth.value, day),
      day,
      blank: false,
    })
  }

  return cells
})

function dayClasses(iso) {
  const start = tempStart.value
  const end = tempEnd.value
  return {
    selected: iso === start || iso === end,
    'range-start': start && iso === start,
    'range-end': end && iso === end,
    'in-range': Boolean(start && end && iso > start && iso < end),
    today: iso === todayIso,
  }
}

function pickDate(iso) {
  if (!iso) return
  if (!tempStart.value || (tempStart.value && tempEnd.value)) {
    // شروع جدید
    tempStart.value = iso
    tempEnd.value = ''
    return
  }
  // انتخاب پایان — اگر قبل از شروع بود، جابه‌جا می‌شود
  if (iso < tempStart.value) {
    tempEnd.value = tempStart.value
    tempStart.value = iso
  } else {
    tempEnd.value = iso
  }
  syncActiveMonth(iso)
  // بازه کامل شد — فوراً اعمال و ببند (حتی بدون دکمه تأیید)
  if (tempStart.value && tempEnd.value) {
    emit('update:modelValue', {
      date_from: tempStart.value,
      date_to: tempEnd.value,
    })
    closeCalendar()
  }
}

function openCalendar() {
  if (props.disabled) return
  // اگر انتخاب داخلی ناقص/خالی است از props بخوان
  if (!tempStart.value && !tempEnd.value) {
    tempStart.value = normalizeDateOnly(props.modelValue?.date_from)
    tempEnd.value = normalizeDateOnly(props.modelValue?.date_to)
  }
  syncActiveMonth(tempStart.value || tempEnd.value || '')
  isOpen.value = true
  showMonthPicker.value = false
  nextTick(updatePopoverPosition)
}

function closeCalendar() {
  isOpen.value = false
  showMonthPicker.value = false
}

function pickToday() {
  tempStart.value = todayIso
  tempEnd.value = todayIso
  confirmRange()
}

function clearRange() {
  tempStart.value = ''
  tempEnd.value = ''
  emit('update:modelValue', { date_from: '', date_to: '' })
}

function confirmRange() {
  if (!tempStart.value || !tempEnd.value) {
    return
  }
  emit('update:modelValue', {
    date_from: tempStart.value,
    date_to: tempEnd.value,
  })
  closeCalendar()
}

function normalizeDateOnly(value) {
  const raw = String(value || '').trim()
  return /^\d{4}-\d{2}-\d{2}/.test(raw) ? raw.slice(0, 10) : ''
}

function pad(value) {
  return String(value).padStart(2, '0')
}

function faNumber(value, minimumDigits = 0) {
  const raw = minimumDigits ? String(value).padStart(minimumDigits, '0') : String(value)
  return raw.replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)])
}

function getLocalIsoDate() {
  const date = new Date()
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function isoToJalali(iso) {
  const normalized = normalizeDateOnly(iso)
  if (!normalized) return null
  const [year, month, day] = normalized.split('-').map(Number)
  if (!year || !month || !day) return null
  try {
    const result = toJalaali(year, month, day)
    return { year: result.jy, month: result.jm, day: result.jd }
  } catch (_) {
    return null
  }
}

function jalaliToIso(year, month, day) {
  const gregorian = toGregorian(year, month, day)
  return `${gregorian.gy}-${pad(gregorian.gm)}-${pad(gregorian.gd)}`
}

function selectMonth(month) {
  activeMonth.value = month
  showMonthPicker.value = false
}

function moveMonth(offset) {
  let nextMonth = activeMonth.value + offset
  let nextYear = activeYear.value
  if (nextMonth < 1) {
    nextMonth = 12
    nextYear -= 1
  } else if (nextMonth > 12) {
    nextMonth = 1
    nextYear += 1
  }
  activeYear.value = nextYear
  activeMonth.value = nextMonth
}

function syncActiveMonth(value) {
  const jalali = isoToJalali(value) || todayJalali
  activeYear.value = jalali.year
  activeMonth.value = jalali.month
}

function updatePopoverPosition() {
  if (!isOpen.value || !inputRef.value || typeof window === 'undefined') return
  const rect = inputRef.value.getBoundingClientRect()
  const width = Math.min(380, Math.max(window.innerWidth - 24, 300))
  let left = rect.right - width
  left = Math.max(12, Math.min(left, window.innerWidth - width - 12))
  let top = rect.bottom + 8
  if (top + 460 > window.innerHeight - 12 && rect.top > 472) {
    top = rect.top - 460 - 8
  }
  popoverStyle.value = {
    top: `${Math.max(12, top)}px`,
    left: `${left}px`,
    width: `${width}px`,
  }
}
</script>

<style scoped>
.persian-range-date-input {
  position: relative;
  width: 100%;
}

.date-input-shell {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 42px;
  direction: ltr;
}

.management-date-input {
  min-width: 0;
  width: 100%;
  min-height: 42px;
  padding: 0.56rem 0.72rem;
  border: 1px solid var(--mg-border-light, rgba(216, 200, 180, 0.72));
  border-inline-end: 0;
  border-radius: 11px 0 0 11px;
  outline: none;
  background: var(--mg-bg-surface, #fbf7f1);
  color: var(--mg-text-main, #34261f);
  font: inherit;
  font-size: 0.8rem;
  text-align: right;
  direction: rtl;
  cursor: pointer;
  transition: 0.16s ease;
}

.management-date-input::placeholder {
  color: var(--mg-text-muted, #746454);
  opacity: 0.72;
}

.management-date-input:focus {
  border-color: color-mix(in srgb, var(--mg-primary, #c97852) 55%, var(--mg-border-light) 45%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-primary, #c97852) 13%, transparent);
}

.date-trigger {
  min-height: 42px;
  border: 1px solid var(--mg-primary, #c97852);
  border-radius: 0 11px 11px 0;
  background: var(--mg-primary, #c97852);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: 0.16s ease;
}

.date-trigger:hover:not(:disabled),
.date-trigger:focus-visible {
  background: var(--mg-primary-hover, #b96845);
}

.date-trigger:disabled,
.management-date-input:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

/* لایه تقویم: پشت‌زمینه + پاپ‌آپ */
.calendar-layer {
  position: fixed;
  inset: 0;
  z-index: 13000;
}

.calendar-backdrop {
  position: absolute;
  inset: 0;
  background: transparent;
}

.calendar-popover {
  position: absolute;
  overflow: hidden;
  color: var(--mg-text-main, #34261f);
  background: var(--mg-bg-surface, #fbf7f1);
  border: 1px solid color-mix(in srgb, var(--mg-border, #d8c8b4) 88%, transparent);
  border-radius: 20px;
  box-shadow: 0 24px 60px rgb(52 38 31 / 0.25), 0 0 0 1px rgb(255 255 255 / 0.08) inset;
}

.calendar-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.85rem 0.9rem 0.7rem;
  background: linear-gradient(135deg, var(--mg-primary, #c97852), color-mix(in srgb, var(--mg-primary, #c97852) 72%, var(--mg-text-main, #34261f) 28%));
  color: #fff;
}

.calendar-heading {
  min-width: 0;
  display: grid;
  gap: 0.15rem;
}

.calendar-kicker {
  color: rgb(255 255 255 / 0.76);
  font-size: 0.67rem;
  font-weight: 700;
}

.calendar-month-button {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  width: fit-content;
  border: 0;
  padding: 0.1rem 0;
  background: transparent;
  color: #fff;
  font: inherit;
  font-size: 1.02rem;
  font-weight: 900;
  cursor: pointer;
}

.calendar-month-button svg {
  transition: transform 0.16s ease;
}

.calendar-month-button svg.rotated {
  transform: rotate(180deg);
}

.calendar-close {
  width: 31px;
  height: 31px;
  border: 1px solid rgb(255 255 255 / 0.28);
  border-radius: 10px;
  background: rgb(255 255 255 / 0.12);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.calendar-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.7rem 0.9rem 0.45rem;
}

.nav-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--mg-border-light, rgba(216, 200, 180, 0.72));
  border-radius: 10px;
  background: var(--mg-bg-page, #f6f0e6);
  color: var(--mg-primary, #c97852);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.nav-button:hover,
.nav-button:focus-visible {
  border-color: var(--mg-primary, #c97852);
  background: color-mix(in srgb, var(--mg-primary, #c97852) 10%, var(--mg-bg-surface, #fbf7f1) 90%);
}

.calendar-year-label {
  color: var(--mg-text-muted, #746454);
  font-size: 0.76rem;
  font-weight: 800;
}

.weekday-row,
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.25rem;
  padding-inline: 0.85rem;
}

.weekday-row {
  padding-bottom: 0.3rem;
  color: var(--mg-text-muted, #746454);
  font-size: 0.67rem;
  font-weight: 800;
  text-align: center;
}

.calendar-day,
.calendar-cell {
  min-height: 36px;
}

.calendar-day {
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--mg-text-main, #34261f);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: 0.13s ease;
}

.calendar-day:hover:not(:disabled),
.calendar-day:focus-visible {
  border-color: color-mix(in srgb, var(--mg-primary, #c97852) 45%, transparent);
  background: color-mix(in srgb, var(--mg-primary, #c97852) 11%, var(--mg-bg-surface, #fbf7f1) 89%);
}

.calendar-day.today {
  border-color: color-mix(in srgb, var(--mg-success, #6f7b56) 62%, transparent);
  color: var(--mg-success, #6f7b56);
}

.calendar-day.selected,
.calendar-day.range-start,
.calendar-day.range-end {
  border-color: var(--mg-primary, #c97852);
  background: var(--mg-primary, #c97852);
  color: #fff;
  box-shadow: 0 5px 12px color-mix(in srgb, var(--mg-primary, #c97852) 25%, transparent);
}

.calendar-day.in-range {
  background: color-mix(in srgb, var(--mg-primary, #c97852) 16%, var(--mg-bg-surface, #fbf7f1) 84%);
  border-color: color-mix(in srgb, var(--mg-primary, #c97852) 22%, transparent);
  border-radius: 0;
}

.calendar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.6rem;
  padding: 0.65rem 0.85rem 0.8rem;
  border-top: 1px solid var(--mg-border-light, rgba(216, 200, 180, 0.48));
}

.today-button,
.clear-date-button,
.confirm-button {
  border: 0;
  border-radius: 999px;
  padding: 0.38rem 0.7rem;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 800;
  cursor: pointer;
}

.today-button {
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 13%, transparent);
  color: var(--mg-success, #6f7b56);
}

.clear-date-button {
  background: color-mix(in srgb, var(--mg-danger, #a6543f) 9%, transparent);
  color: var(--mg-danger, #a6543f);
}

.confirm-button {
  background: var(--mg-primary, #c97852);
  color: #fff;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary, #c97852) 28%, transparent);
}

.calendar-hint {
  margin-inline-start: auto;
  color: var(--mg-text-muted, #746454);
  font-size: 0.68rem;
}

.month-picker {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.4rem;
  padding: 0.7rem 0.9rem 0.8rem;
}

.month-option {
  border: 1px solid var(--mg-border-light, rgba(216, 200, 180, 0.72));
  border-radius: 10px;
  background: transparent;
  color: var(--mg-text-main, #34261f);
  font: inherit;
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.5rem 0.2rem;
  cursor: pointer;
  transition: 0.13s ease;
}

.month-option:hover {
  border-color: var(--mg-primary, #c97852);
}

.month-option.active {
  border-color: var(--mg-primary, #c97852);
  background: color-mix(in srgb, var(--mg-primary, #c97852) 13%, transparent);
  color: var(--mg-primary, #c97852);
}
</style>
