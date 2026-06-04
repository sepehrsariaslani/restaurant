<template>
  <div ref="rootEl" class="relative w-full" dir="rtl">
    <button
      type="button"
      class="trigger-btn"
      :class="isDisabled ? 'trigger-btn--disabled' : 'trigger-btn--active'"
      :disabled="isDisabled"
      @click="toggleOpen"
    >
      <span :class="displayValue ? 'text-gray-800' : 'text-gray-400'">
        {{ displayValue || placeholder }}
      </span>
      <CalendarIcon class="w-4 h-4 text-amber-500 shrink-0" />
    </button>

    <Transition name="dp-fade">
      <div
        v-if="isOpen"
        class="dropdown"
      >
        <JalaliCalendarShell
          v-model:view="calendarView"
          v-model:active-month="activeMonth"
        >
          <div class="grid grid-cols-7 gap-0.5 mb-1">
            <div
              v-for="wd in weekDays"
              :key="wd"
              class="h-8 flex items-center justify-center text-[11px] font-medium text-gray-400"
            >
              {{ wd }}
            </div>
          </div>

          <div class="grid grid-cols-7 gap-0.5">
            <template v-for="cell in monthCells" :key="cell.key">
              <div v-if="cell.blank" class="h-9 w-full" />
              <button
                v-else
                type="button"
                class="day-btn"
                :class="dayClass(cell)"
                :disabled="cell.isDisabled"
                @click="pickDay(cell)"
              >
                {{ toPersianDigits(cell.jalaliDay) }}
              </button>
            </template>
          </div>
        </JalaliCalendarShell>

        <div class="footer">
          <button type="button" class="btn-today" @click="pickToday">امروز</button>
          <button type="button" class="btn-close" @click="isOpen = false">بستن</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Calendar as CalendarIcon } from 'lucide-vue-next'
import JalaliCalendarShell from '@/components/jalali/JalaliCalendarShell.vue'
import {
  formatGregorianDate,
  formatJalaliDisplay,
  getJalaliDaysInMonth,
  gregorianToJalali,
  jalaliToGregorian,
  toPersianDigits,
} from '@/utils/jalali'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'انتخاب تاریخ' },
  disabled: { type: [Boolean, Number], default: false },
  minDate: { type: String, default: '' },
  maxDate: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const rootEl = ref(null)
const isOpen = ref(false)
const calendarView = ref('days')
const weekDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

const isDisabled = computed(() => Boolean(props.disabled))

const displayValue = computed(() => formatJalaliDisplay(normalize(props.modelValue)))

const activeMonth = ref(jalaliMonthOf(props.modelValue))

watch(() => props.modelValue, (v) => {
  if (v) activeMonth.value = jalaliMonthOf(v)
})

const monthCells = computed(() => {
  const { year, month } = activeMonth.value
  const g1 = jalaliToGregorian(year, month, 1)
  const d1 = new Date(g1.year, g1.month - 1, g1.day)
  const offset = (d1.getDay() + 1) % 7
  const total = getJalaliDaysInMonth(year, month)
  const cells = []

  for (let i = 0; i < offset; i++) cells.push({ blank: true, key: `b${i}` })

  for (let day = 1; day <= total; day++) {
    const g = jalaliToGregorian(year, month, day)
    const gDate = formatGregorianDate(new Date(g.year, g.month - 1, g.day))
    cells.push({
      blank: false,
      key: `${year}-${month}-${day}`,
      jalaliDay: day,
      gDate,
      isToday: gDate === formatGregorianDate(new Date()),
      isSelected: gDate === normalize(props.modelValue),
      isDisabled: outOfRange(gDate),
    })
  }

  while (cells.length % 7 !== 0) cells.push({ blank: true, key: `t${cells.length}` })
  return cells
})

function dayClass(cell) {
  if (cell.isSelected) return 'day-btn--selected'
  if (cell.isDisabled) return 'day-btn--disabled'
  if (cell.isToday) return 'day-btn--today'
  return 'day-btn--normal'
}

function pickDay(cell) {
  if (cell.isDisabled) return
  emit('update:modelValue', cell.gDate)
  emit('change', cell.gDate)
  isOpen.value = false
}

function pickToday() {
  const today = formatGregorianDate(new Date())
  activeMonth.value = jalaliMonthOf(today)
  calendarView.value = 'days'
  if (!outOfRange(today)) {
    emit('update:modelValue', today)
    emit('change', today)
  }
  isOpen.value = false
}

function toggleOpen() {
  if (isDisabled.value) return
  if (!isOpen.value) {
    calendarView.value = 'days'
    activeMonth.value = jalaliMonthOf(props.modelValue)
  }
  isOpen.value = !isOpen.value
}

function normalize(v) {
  if (!v || typeof v !== 'string') return ''
  return v.slice(0, 10)
}

function jalaliMonthOf(v) {
  const d = normalize(v) || formatGregorianDate(new Date())
  const [y, m, dd] = d.split('-').map(Number)
  const j = gregorianToJalali(y, m, dd)
  return { year: j.year, month: j.month }
}

function outOfRange(d) {
  const mn = normalize(props.minDate)
  const mx = normalize(props.maxDate)
  if (mn && d < mn) return true
  if (mx && d > mx) return true
  return false
}

function onMouseDown(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) isOpen.value = false
}

onMounted(() => document.addEventListener('mousedown', onMouseDown))
onBeforeUnmount(() => document.removeEventListener('mousedown', onMouseDown))
</script>

<style scoped>
.trigger-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 0.75rem;
  border: 1px solid;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  text-align: right;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
}
.trigger-btn--active {
  background: #fff;
  border-color: #d1d5db;
  color: #111827;
}
.trigger-btn--active:hover {
  border-color: #f59e0b;
}
.trigger-btn--active:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}
.trigger-btn--disabled {
  background: #f9fafb;
  border-color: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.dropdown {
  position: absolute;
  right: 0;
  z-index: 1700;
  margin-top: 0.5rem;
  width: 100%;
  min-width: 300px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  padding: 0.75rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.12);
}

.day-btn {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 0.4rem;
  border: 1px solid transparent;
  font-size: 0.8125rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s, border-color 0.12s;
  outline: none;
}
.day-btn--normal {
  color: #374151;
  border-color: #e5e7eb;
  background: transparent;
}
.day-btn--normal:hover:not(:disabled) {
  background: #fef3c7;
  border-color: #fcd34d;
}
.day-btn--selected {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
  font-weight: 700;
}
.day-btn--today {
  border-color: #f59e0b;
  color: #d97706;
  font-weight: 700;
  background: #fffbeb;
}
.day-btn--disabled {
  color: #d1d5db;
  background: #f9fafb;
  border-color: #f3f4f6;
  cursor: not-allowed;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f3f4f6;
}
.btn-today {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 0.5rem;
  background: #fef3c7;
  color: #92400e;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-today:hover {
  background: #fde68a;
}
.btn-close {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  border-radius: 0.5rem;
  background: #f3f4f6;
  color: #6b7280;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-close:hover {
  background: #e5e7eb;
}

.dp-fade-enter-active, .dp-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dp-fade-enter-from, .dp-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
