<template>
  <div ref="rootEl" class="relative">
    <button
      type="button"
      class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 flex items-center justify-between text-right transition-colors hover:border-gray-300"
      @click="toggleCalendar"
    >
      <div class="flex flex-col gap-0.5 min-w-0">
        <span class="text-[11px] text-gray-500">{{ title }}</span>
        <span class="text-sm font-bold text-gray-900 truncate">{{ displayLabel }}</span>
      </div>
      <CalendarIcon class="w-5 h-5 shrink-0" :style="{ color: theme.color600 }" />
    </button>

    <div
      v-if="isOpen"
      class="absolute right-0 mt-2 w-full min-w-[320px] max-w-[400px] bg-white border border-gray-200 rounded-2xl shadow-xl z-[1700] p-3"
      :style="cssVars"
    >
      <!-- Presets -->
      <div class="mb-3">
        <p class="text-[11px] font-medium text-gray-500 mb-2">بازه‌های پیش‌فرض</p>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="preset in datePresets"
            :key="preset.id"
            type="button"
            class="preset-chip"
            :class="{ 'preset-chip-active': activePresetId === preset.id }"
            @click="applyPreset(preset.id)"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>

      <!-- از تاریخ / تا تاریخ toggle buttons -->
      <div class="flex gap-2 mb-3">
        <button
          type="button"
          class="flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors border text-right"
          :class="selectingMode === 'start'
            ? 'border-transparent text-white'
            : 'border-gray-200 bg-gray-50 text-gray-700'"
          :style="selectingMode === 'start' ? { backgroundColor: theme.color600 } : {}"
          @click="selectingMode = 'start'"
        >
          <div class="text-[10px] opacity-80 mb-0.5">از تاریخ</div>
          <div class="persian-nums text-xs font-bold">{{ draftStart ? formatJalaliShort(draftStart) : '——' }}</div>
        </button>
        <button
          type="button"
          class="flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors border text-right"
          :class="selectingMode === 'end'
            ? 'border-transparent text-white'
            : 'border-gray-200 bg-gray-50 text-gray-700'"
          :style="selectingMode === 'end' ? { backgroundColor: theme.color500 } : {}"
          @click="selectingMode = 'end'"
        >
          <div class="text-[10px] opacity-80 mb-0.5">تا تاریخ</div>
          <div class="persian-nums text-xs font-bold">{{ draftEnd ? formatJalaliShort(draftEnd) : '——' }}</div>
        </button>
      </div>

      <JalaliCalendarShell
        v-model:view="calendarView"
        v-model:active-month="activeMonth"
      >
        <div class="grid grid-cols-7 gap-1 mb-1">
          <div
            v-for="day in weekDays"
            :key="day"
            class="h-8 flex items-center justify-center text-[11px] font-medium text-gray-500"
          >
            {{ day }}
          </div>
        </div>

        <div class="grid grid-cols-7 gap-1">
          <template v-for="cell in monthCells" :key="cell.key">
            <div v-if="cell.blank" class="h-10 w-10" />
            <button
              v-else
              type="button"
              class="h-10 w-10 rounded-md border text-sm font-medium transition-colors flex items-center justify-center day-cell"
              :class="getDayClass(cell.date)"
              @click="selectDate(cell.date)"
            >
              {{ toPersianDigits(cell.day) }}
            </button>
          </template>
        </div>
      </JalaliCalendarShell>

      <div class="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
        <button
          type="button"
          class="text-xs font-medium px-2.5 py-1.5 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200"
          @click="clearRange"
        >
          همه بازه‌ها
        </button>
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500">
            {{ selectingMode === 'start' ? 'تاریخ شروع را انتخاب کنید' : 'تاریخ پایان را انتخاب کنید' }}
          </span>
          <button
            v-if="draftStart && draftEnd"
            type="button"
            class="text-xs font-medium px-3 py-1.5 rounded-lg text-white"
            :style="{ backgroundColor: theme.color600 }"
            @click="applyManualRange"
          >
            اعمال
          </button>
        </div>
      </div>
    </div>
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
  moduleKey: { type: String, default: 'finance' },
  title: { type: String, default: 'انتخاب بازه زمانی' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const moduleThemeMap = {
  finance:       { color500: '#f59e0b', color600: '#d97706', color100: '#fef3c7' },
  accounts:      { color500: '#f97316', color600: '#ea580c', color100: '#ffedd5' },
  procurement:   { color500: '#059669', color600: '#047857', color100: '#d1fae5' },
  inventory:     { color500: '#06b6d4', color600: '#0891b2', color100: '#cffafe' },
  sales:         { color500: '#3b82f6', color600: '#2563eb', color100: '#dbeafe' },
  hr:            { color500: '#8b5cf6', color600: '#7c3aed', color100: '#ede9fe' },
  manufacturing: { color500: '#f43f5e', color600: '#e11d48', color100: '#ffe4e6' },
  reports:       { color500: '#64748b', color600: '#475569', color100: '#e2e8f0' },
}

const presetLabels = {
  all: 'همه بازه‌ها', today: 'امروز', yesterday: 'دیروز',
  last_7_days: '۷ روز گذشته', last_30_days: '۳۰ روز گذشته',
  last_90_days: '۹۰ روز گذشته', this_month: 'ماه جاری',
  last_month: 'ماه گذشته', this_year: 'سال جاری', last_year: 'سال گذشته', custom: 'بازه دلخواه',
}

const datePresets = [
  { id: 'today', label: 'امروز' }, { id: 'yesterday', label: 'دیروز' },
  { id: 'last_7_days', label: '۷ روز گذشته' }, { id: 'last_30_days', label: '۳۰ روز گذشته' },
  { id: 'last_90_days', label: '۹۰ روز گذشته' }, { id: 'this_month', label: 'ماه جاری' },
  { id: 'last_month', label: 'ماه گذشته' }, { id: 'this_year', label: 'سال جاری' },
  { id: 'last_year', label: 'سال گذشته' },
]

const weekDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']
const rootEl = ref(null)
const isOpen = ref(false)
const calendarView = ref('days')
const draftStart = ref('')
const draftEnd = ref('')
const selectingMode = ref('start')

const theme = computed(() => moduleThemeMap[props.moduleKey] || moduleThemeMap.finance)
const cssVars = computed(() => ({
  '--accent-500': theme.value.color500,
  '--accent-600': theme.value.color600,
  '--accent-100': theme.value.color100,
}))

const activePresetId = computed(() => props.modelValue?.preset || 'all')
const activeMonth = ref(getJalaliMonthFromDate(props.modelValue?.startDate || props.modelValue?.endDate))

const displayLabel = computed(() => {
  const preset = props.modelValue?.preset
  const start = normalizeDate(props.modelValue?.startDate)
  const end = normalizeDate(props.modelValue?.endDate)
  if (!start && !end) return presetLabels.all
  const rangeText = start && end
    ? `${formatJalaliNumericDate(start, '/')} تا ${formatJalaliNumericDate(end, '/')}`
    : start ? `از ${formatJalaliNumericDate(start, '/')}` : `تا ${formatJalaliNumericDate(end, '/')}`
  if (preset && preset !== 'custom' && presetLabels[preset]) return `${presetLabels[preset]} · ${rangeText}`
  return rangeText
})

const monthCells = computed(() => {
  const { year, month } = activeMonth.value
  const firstGregorian = jalaliToGregorian(year, month, 1)
  const firstDate = new Date(firstGregorian.year, firstGregorian.month - 1, firstGregorian.day)
  const offset = (firstDate.getDay() + 1) % 7
  const daysInMonth = getJalaliDaysInMonth(year, month)
  const cells = []
  for (let i = 0; i < offset; i++) cells.push({ blank: true, key: `blank-${i}` })
  for (let day = 1; day <= daysInMonth; day++) {
    const g = jalaliToGregorian(year, month, day)
    const date = formatGregorianDate(new Date(g.year, g.month - 1, g.day))
    cells.push({ blank: false, key: `${year}-${month}-${day}`, day, date })
  }
  while (cells.length % 7 !== 0) cells.push({ blank: true, key: `tail-${cells.length}` })
  return cells
})

function normalizeDate(value) {
  if (!value || typeof value !== 'string') return ''
  return value.slice(0, 10)
}

function startOfDay(date) {
  const d = new Date(date); d.setHours(0, 0, 0, 0); return d
}

function addDays(date, days) {
  const d = new Date(date); d.setDate(d.getDate() + days); return startOfDay(d)
}

function formatJalaliShort(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-').map(Number)
  const j = gregorianToJalali(y, m, d)
  return `${toPersianDigits(j.year)}/${toPersianDigits(String(j.month).padStart(2,'0'))}/${toPersianDigits(String(j.day).padStart(2,'0'))}`
}

function computePresetRange(presetId) {
  const today = startOfDay(new Date())
  const endDate = formatGregorianDate(today)
  switch (presetId) {
    case 'today': return { preset: presetId, startDate: endDate, endDate }
    case 'yesterday': { const y = addDays(today, -1); const s = formatGregorianDate(y); return { preset: presetId, startDate: s, endDate: s } }
    case 'last_7_days': return { preset: presetId, startDate: formatGregorianDate(addDays(today, -6)), endDate }
    case 'last_30_days': return { preset: presetId, startDate: formatGregorianDate(addDays(today, -29)), endDate }
    case 'last_90_days': return { preset: presetId, startDate: formatGregorianDate(addDays(today, -89)), endDate }
    case 'this_month': return { preset: presetId, startDate: formatGregorianDate(new Date(today.getFullYear(), today.getMonth(), 1)), endDate }
    case 'last_month': {
      const first = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      const last = new Date(today.getFullYear(), today.getMonth(), 0)
      return { preset: presetId, startDate: formatGregorianDate(first), endDate: formatGregorianDate(last) }
    }
    case 'this_year': return { preset: presetId, startDate: formatGregorianDate(new Date(today.getFullYear(), 0, 1)), endDate }
    case 'last_year': {
      const year = today.getFullYear() - 1
      return { preset: presetId, startDate: formatGregorianDate(new Date(year, 0, 1)), endDate: formatGregorianDate(new Date(year, 11, 31)) }
    }
    case 'all': return { preset: 'all', startDate: '', endDate: '' }
    default: return null
  }
}

function emitRange(range) {
  emit('update:modelValue', range)
  emit('change', range)
}

function applyPreset(presetId) {
  const range = computePresetRange(presetId)
  if (!range) return
  draftStart.value = range.startDate
  draftEnd.value = range.endDate
  activeMonth.value = getJalaliMonthFromDate(range.startDate || range.endDate)
  emitRange(range)
  isOpen.value = false
}

function applyManualRange() {
  if (!draftStart.value || !draftEnd.value) return
  const range = { preset: 'custom', startDate: draftStart.value, endDate: draftEnd.value }
  emitRange(range)
  isOpen.value = false
}

function getJalaliMonthFromDate(dateValue) {
  const normalized = normalizeDate(dateValue) || formatGregorianDate(new Date())
  const [year, month, day] = normalized.split('-').map(Number)
  const jalali = gregorianToJalali(year, month, day)
  return { year: jalali.year, month: jalali.month }
}

function toggleCalendar() {
  if (!isOpen.value) {
    draftStart.value = normalizeDate(props.modelValue?.startDate)
    draftEnd.value = normalizeDate(props.modelValue?.endDate)
    activeMonth.value = getJalaliMonthFromDate(draftStart.value || draftEnd.value)
    calendarView.value = 'days'
    selectingMode.value = 'start'
  }
  isOpen.value = !isOpen.value
}

function selectDate(dateValue) {
  if (selectingMode.value === 'start') {
    draftStart.value = dateValue
    if (draftEnd.value && dateValue > draftEnd.value) draftEnd.value = ''
    selectingMode.value = 'end'
  } else {
    if (dateValue < draftStart.value) {
      draftEnd.value = draftStart.value
      draftStart.value = dateValue
    } else {
      draftEnd.value = dateValue
    }
    if (draftStart.value && draftEnd.value) {
      applyManualRange()
    }
  }
}

function clearRange() {
  draftStart.value = ''
  draftEnd.value = ''
  emitRange({ preset: 'all', startDate: '', endDate: '' })
  isOpen.value = false
}

function getDayClass(dateValue) {
  const start = draftStart.value
  const end = draftEnd.value
  const today = formatGregorianDate(new Date())
  if (dateValue === start || dateValue === end) return 'day-selected'
  if (start && end && dateValue > start && dateValue < end) return 'day-in-range'
  if (dateValue === today) return 'day-today'
  return 'day-normal'
}

function handleClickOutside(event) {
  if (!rootEl.value || rootEl.value.contains(event.target)) return
  isOpen.value = false
}

watch(
  () => [props.modelValue?.startDate, props.modelValue?.endDate],
  ([newStart, newEnd]) => {
    draftStart.value = normalizeDate(newStart)
    draftEnd.value = normalizeDate(newEnd)
  },
  { immediate: true }
)

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
.persian-nums { font-feature-settings: "ss01"; }

.preset-chip {
  @apply text-[11px] font-medium px-2 py-1 rounded-lg border border-gray-200
         text-gray-700 bg-gray-50 hover:bg-gray-100 transition-colors;
}
.preset-chip-active {
  background-color: var(--accent-500);
  border-color: var(--accent-500);
  color: white;
}
.day-cell { border-color: #e5e7eb; }
.day-normal { color: #374151; background-color: transparent; }
.day-normal:hover { background-color: #f3f4f6; }
.day-selected { background-color: var(--accent-500); border-color: var(--accent-500); color: #ffffff; }
.day-in-range { background-color: var(--accent-100); border-color: color-mix(in srgb, var(--accent-500) 45%, #e5e7eb); color: var(--accent-600); }
.day-today { border-color: var(--accent-500); color: var(--accent-600); font-weight: 700; }
</style>
