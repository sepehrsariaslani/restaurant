<template>
  <div ref="rootEl" class="relative w-full" dir="rtl">
    <button
      type="button"
      class="trigger-btn"
      @click="toggleOpen"
    >
      <div class="flex flex-col gap-0.5 min-w-0 text-right">
        <span v-if="title" class="text-[11px] text-gray-400">{{ title }}</span>
        <span class="text-sm font-bold text-gray-800 truncate">{{ displayLabel }}</span>
      </div>
      <CalendarIcon class="w-4 h-4 shrink-0 text-amber-500" />
    </button>

    <Transition name="dp-fade">
      <div v-if="isOpen" class="dropdown">

        <div class="mb-3">
          <p class="text-[11px] font-medium text-gray-400 mb-1.5">بازه‌های پیش‌فرض</p>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="p in presets"
              :key="p.id"
              type="button"
              class="preset-chip"
              :class="activePreset === p.id ? 'preset-chip--active' : ''"
              @click="applyPreset(p.id)"
            >
              {{ p.label }}
            </button>
          </div>
        </div>

        <div class="flex gap-2 mb-3">
          <button
            type="button"
            class="range-tab"
            :class="mode === 'start' ? 'range-tab--active' : ''"
            @click="mode = 'start'"
          >
            <div class="text-[10px] opacity-70 mb-0.5">از تاریخ</div>
            <div class="text-xs font-bold">{{ draftStart ? jalaliShort(draftStart) : '——' }}</div>
          </button>
          <button
            type="button"
            class="range-tab"
            :class="mode === 'end' ? 'range-tab--active' : ''"
            @click="mode = 'end'"
          >
            <div class="text-[10px] opacity-70 mb-0.5">تا تاریخ</div>
            <div class="text-xs font-bold">{{ draftEnd ? jalaliShort(draftEnd) : '——' }}</div>
          </button>
        </div>

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
                :class="dayClass(cell.date)"
                @click="pickDate(cell.date)"
                @mouseenter="hoverDate = cell.date"
                @mouseleave="hoverDate = ''"
              >
                {{ toPersianDigits(cell.day) }}
              </button>
            </template>
          </div>
        </JalaliCalendarShell>

        <div class="footer">
          <button type="button" class="btn-clear" @click="clearRange">همه بازه‌ها</button>
          <div class="flex items-center gap-2">
            <span class="text-[11px] text-gray-400">
              {{ mode === 'start' ? 'تاریخ شروع را انتخاب کنید' : 'تاریخ پایان را انتخاب کنید' }}
            </span>
            <button
              v-if="draftStart && draftEnd"
              type="button"
              class="btn-apply"
              @click="applyManual"
            >
              اعمال
            </button>
          </div>
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
  formatJalaliNumericDate,
  getJalaliDaysInMonth,
  gregorianToJalali,
  jalaliToGregorian,
  toPersianDigits,
} from '@/utils/jalali'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ preset: 'all', startDate: '', endDate: '' }),
  },
  title: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const presets = [
  { id: 'today', label: 'امروز' },
  { id: 'yesterday', label: 'دیروز' },
  { id: 'last_7_days', label: '۷ روز گذشته' },
  { id: 'last_30_days', label: '۳۰ روز گذشته' },
  { id: 'last_90_days', label: '۹۰ روز گذشته' },
  { id: 'this_month', label: 'ماه جاری' },
  { id: 'last_month', label: 'ماه گذشته' },
  { id: 'this_year', label: 'سال جاری' },
  { id: 'last_year', label: 'سال گذشته' },
]

const presetLabels = {
  all: 'همه بازه‌ها', today: 'امروز', yesterday: 'دیروز',
  last_7_days: '۷ روز گذشته', last_30_days: '۳۰ روز گذشته',
  last_90_days: '۹۰ روز گذشته', this_month: 'ماه جاری',
  last_month: 'ماه گذشته', this_year: 'سال جاری', last_year: 'سال گذشته',
  custom: 'بازه دلخواه',
}

const weekDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

const rootEl = ref(null)
const isOpen = ref(false)
const calendarView = ref('days')
const mode = ref('start')
const draftStart = ref('')
const draftEnd = ref('')
const hoverDate = ref('')
const activeMonth = ref(jalaliMonthOf(props.modelValue?.startDate || props.modelValue?.endDate))

const activePreset = computed(() => props.modelValue?.preset || 'all')

const displayLabel = computed(() => {
  const start = normalize(props.modelValue?.startDate)
  const end = normalize(props.modelValue?.endDate)
  const preset = props.modelValue?.preset
  if (!start && !end) return presetLabels.all
  const rangeText = start && end
    ? `${formatJalaliNumericDate(start)} تا ${formatJalaliNumericDate(end)}`
    : start ? `از ${formatJalaliNumericDate(start)}` : `تا ${formatJalaliNumericDate(end)}`
  if (preset && preset !== 'custom' && presetLabels[preset]) return `${presetLabels[preset]} · ${rangeText}`
  return rangeText
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
    const date = formatGregorianDate(new Date(g.year, g.month - 1, g.day))
    cells.push({ blank: false, key: `${year}-${month}-${day}`, day, date })
  }
  while (cells.length % 7 !== 0) cells.push({ blank: true, key: `t${cells.length}` })
  return cells
})

function dayClass(date) {
  const isStart = date === draftStart.value
  const isEnd = date === draftEnd.value
  const effectiveEnd = draftEnd.value || (mode.value === 'end' ? hoverDate.value : '')
  const inRange = draftStart.value && effectiveEnd && date > draftStart.value && date < effectiveEnd

  if (isStart && isEnd) return 'day-btn day-btn--start day-btn--end'
  if (isStart) return 'day-btn day-btn--start'
  if (isEnd) return 'day-btn day-btn--end'
  if (inRange) return 'day-btn day-btn--in-range'
  return 'day-btn day-btn--normal'
}

function pickDate(date) {
  if (mode.value === 'start') {
    draftStart.value = date
    if (draftEnd.value && date > draftEnd.value) draftEnd.value = ''
    mode.value = 'end'
  } else {
    if (date < draftStart.value) {
      draftEnd.value = draftStart.value
      draftStart.value = date
    } else {
      draftEnd.value = date
    }
    if (draftStart.value && draftEnd.value) {
      applyManual()
    }
  }
}

function applyManual() {
  if (!draftStart.value || !draftEnd.value) return
  const range = { preset: 'custom', startDate: draftStart.value, endDate: draftEnd.value }
  emit('update:modelValue', range)
  emit('change', range)
  isOpen.value = false
}

function applyPreset(id) {
  const range = computePreset(id)
  if (!range) return
  draftStart.value = range.startDate
  draftEnd.value = range.endDate
  if (range.startDate) activeMonth.value = jalaliMonthOf(range.startDate)
  emit('update:modelValue', range)
  emit('change', range)
  isOpen.value = false
}

function clearRange() {
  draftStart.value = ''
  draftEnd.value = ''
  const range = { preset: 'all', startDate: '', endDate: '' }
  emit('update:modelValue', range)
  emit('change', range)
  isOpen.value = false
}

function computePreset(id) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayStr = formatGregorianDate(today)
  const shift = (n) => {
    const d = new Date(today)
    d.setDate(d.getDate() + n)
    return formatGregorianDate(d)
  }
  switch (id) {
    case 'today': return { preset: id, startDate: todayStr, endDate: todayStr }
    case 'yesterday': { const y = shift(-1); return { preset: id, startDate: y, endDate: y } }
    case 'last_7_days': return { preset: id, startDate: shift(-6), endDate: todayStr }
    case 'last_30_days': return { preset: id, startDate: shift(-29), endDate: todayStr }
    case 'last_90_days': return { preset: id, startDate: shift(-89), endDate: todayStr }
    case 'this_month': {
      const first = new Date(today.getFullYear(), today.getMonth(), 1)
      return { preset: id, startDate: formatGregorianDate(first), endDate: todayStr }
    }
    case 'last_month': {
      const first = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      const last = new Date(today.getFullYear(), today.getMonth(), 0)
      return { preset: id, startDate: formatGregorianDate(first), endDate: formatGregorianDate(last) }
    }
    case 'this_year': {
      return { preset: id, startDate: formatGregorianDate(new Date(today.getFullYear(), 0, 1)), endDate: todayStr }
    }
    case 'last_year': {
      const y = today.getFullYear() - 1
      return { preset: id, startDate: formatGregorianDate(new Date(y, 0, 1)), endDate: formatGregorianDate(new Date(y, 11, 31)) }
    }
    default: return { preset: 'all', startDate: '', endDate: '' }
  }
}

function jalaliShort(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-').map(Number)
  const j = gregorianToJalali(y, m, d)
  return `${toPersianDigits(j.year)}/${toPersianDigits(String(j.month).padStart(2, '0'))}/${toPersianDigits(String(j.day).padStart(2, '0'))}`
}

function toggleOpen() {
  if (!isOpen.value) {
    draftStart.value = normalize(props.modelValue?.startDate)
    draftEnd.value = normalize(props.modelValue?.endDate)
    activeMonth.value = jalaliMonthOf(draftStart.value || draftEnd.value)
    calendarView.value = 'days'
    mode.value = 'start'
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
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  background: #fff;
  text-align: right;
  cursor: pointer;
  transition: border-color 0.15s;
  gap: 0.5rem;
}
.trigger-btn:hover { border-color: #d1d5db; }

.dropdown {
  position: absolute;
  right: 0;
  z-index: 1700;
  margin-top: 0.5rem;
  width: 100%;
  min-width: 320px;
  max-width: 400px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  padding: 0.75rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.12);
}

.preset-chip {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
}
.preset-chip:hover { background: #fef3c7; border-color: #fcd34d; }
.preset-chip--active { background: #f59e0b; border-color: #f59e0b; color: #fff; }

.range-tab {
  flex: 1;
  border-radius: 0.6rem;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
  padding: 0.4rem 0.6rem;
  text-align: right;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.range-tab--active {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
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
  transition: background 0.1s, border-color 0.1s;
  cursor: pointer;
  outline: none;
}
.day-btn--normal {
  color: #374151;
  border-color: #e5e7eb;
  background: transparent;
}
.day-btn--normal:hover {
  background: #fef3c7;
  border-color: #fcd34d;
}
.day-btn--start {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
  font-weight: 700;
  border-radius: 0.4rem 0 0 0.4rem;
}
.day-btn--end {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
  font-weight: 700;
  border-radius: 0 0.4rem 0.4rem 0;
}
.day-btn--start.day-btn--end {
  border-radius: 0.4rem;
}
.day-btn--in-range {
  background: #fef3c7;
  border-color: #fde68a;
  color: #92400e;
  border-radius: 0;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f3f4f6;
}
.btn-clear {
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
.btn-clear:hover { background: #e5e7eb; }
.btn-apply {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 0.5rem;
  background: #f59e0b;
  color: #fff;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-apply:hover { background: #d97706; }

.dp-fade-enter-active, .dp-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dp-fade-enter-from, .dp-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
