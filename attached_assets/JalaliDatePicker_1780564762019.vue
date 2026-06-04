<template>
  <div ref="rootEl" class="relative w-full">
    <button
      type="button"
      class="w-full rounded-xl border px-3 py-2.5 text-right text-sm transition-colors flex items-center justify-between"
      :class="buttonClass"
      :disabled="isDisabled"
      @click="toggleCalendar"
    >
      <span :class="displayValue ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'">
        {{ displayValue || placeholder }}
      </span>
      <CalendarIcon class="w-4 h-4 text-amber-600 dark:text-amber-400" />
    </button>

    <div
      v-if="isOpen"
      class="absolute right-0 z-[1700] mt-2 w-full min-w-[320px] rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-3 shadow-xl dark:shadow-black/40"
      style="--accent-500: #f59e0b; --accent-600: #d97706;"
    >
      <JalaliCalendarShell
        v-model:view="calendarView"
        v-model:active-month="activeJalaliMonth"
      >
        <div class="grid grid-cols-7 gap-1 mb-1">
          <div
            v-for="day in weekDays"
            :key="day"
            class="h-8 flex items-center justify-center text-[11px] font-medium text-gray-500 dark:text-gray-400"
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
              class="h-10 w-10 rounded-md border day-cell text-sm font-medium transition-colors flex items-center justify-center"
              :class="getDayClass(cell)"
              :disabled="cell.isDisabled"
              @click="selectDay(cell)"
            >
              {{ toPersianDigits(cell.jalaliDay) }}
            </button>
          </template>
        </div>
      </JalaliCalendarShell>

      <div class="mt-3 flex items-center justify-between border-t border-gray-100 dark:border-gray-700 pt-2">
        <button
          type="button"
          class="text-xs font-medium px-2.5 py-1.5 rounded-lg bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/60"
          @click="goToToday"
        >
          امروز
        </button>
        <button
          type="button"
          class="text-xs font-medium px-2.5 py-1.5 rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          @click="isOpen = false"
        >
          بستن
        </button>
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
  formatJalaliDate,
  getJalaliDaysInMonth,
  gregorianToJalali,
  jalaliToGregorian,
  toPersianDigits,
} from '@/utils/jalali'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: [Boolean, Number],
    default: false,
  },
  minDate: {
    type: String,
    default: '',
  },
  maxDate: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const rootEl = ref(null)
const isOpen = ref(false)
const calendarView = ref('days')
const weekDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

const isDisabled = computed(() => Boolean(props.disabled))
const displayValue = computed(() => formatJalaliDate(normalizeDateValue(props.modelValue)))

const buttonClass = computed(() => {
  if (isDisabled.value) return 'bg-gray-100 dark:bg-gray-800 text-gray-500 cursor-not-allowed border-gray-200 dark:border-gray-700'
  return 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 hover:border-amber-400'
})

const activeJalaliMonth = ref(getJalaliMonthFromValue(props.modelValue))

const monthCells = computed(() => {
  const year = activeJalaliMonth.value.year
  const month = activeJalaliMonth.value.month
  const firstGregorian = jalaliToGregorian(year, month, 1)
  const firstDate = new Date(firstGregorian.year, firstGregorian.month - 1, firstGregorian.day)
  const offset = (firstDate.getDay() + 1) % 7
  const daysInMonth = getJalaliDaysInMonth(year, month)
  const cells = []

  for (let i = 0; i < offset; i++) {
    cells.push({ blank: true, key: `blank-${i}` })
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const gregorian = jalaliToGregorian(year, month, day)
    const gregorianDate = formatGregorianDate(new Date(gregorian.year, gregorian.month - 1, gregorian.day))
    cells.push({
      blank: false,
      key: `${year}-${month}-${day}`,
      jalaliDay: day,
      gregorianDate,
      isToday: gregorianDate === formatGregorianDate(new Date()),
      isSelected: gregorianDate === normalizeDateValue(props.modelValue),
      isDisabled: isOutOfRange(gregorianDate),
    })
  }

  while (cells.length % 7 !== 0) {
    cells.push({ blank: true, key: `tail-${cells.length}` })
  }

  return cells
})

watch(
  () => props.modelValue,
  (value) => {
    if (!value) return
    activeJalaliMonth.value = getJalaliMonthFromValue(value)
  }
)

function toggleCalendar() {
  if (isDisabled.value) return
  if (!isOpen.value) {
    calendarView.value = 'days'
    activeJalaliMonth.value = getJalaliMonthFromValue(props.modelValue)
  }
  isOpen.value = !isOpen.value
}

function selectDay(day) {
  if (day.isDisabled) return
  emit('update:modelValue', day.gregorianDate)
  emit('change', day.gregorianDate)
  isOpen.value = false
}

function goToToday() {
  const today = formatGregorianDate(new Date())
  activeJalaliMonth.value = getJalaliMonthFromValue(today)
  calendarView.value = 'days'
  if (!isOutOfRange(today)) {
    emit('update:modelValue', today)
    emit('change', today)
  }
  isOpen.value = false
}

function getDayClass(day) {
  if (day.isSelected) return 'day-selected'
  if (day.isDisabled) return 'day-disabled'
  if (day.isToday) return 'day-today'
  return 'day-normal'
}

function normalizeDateValue(value) {
  if (!value || typeof value !== 'string') return ''
  return value.slice(0, 10)
}

function getJalaliMonthFromValue(value) {
  const normalizedValue = normalizeDateValue(value) || formatGregorianDate(new Date())
  const [year, month, day] = normalizedValue.split('-').map(Number)
  const jalali = gregorianToJalali(year, month, day)
  return { year: jalali.year, month: jalali.month }
}

function isOutOfRange(dateValue) {
  const minDate = normalizeDateValue(props.minDate)
  const maxDate = normalizeDateValue(props.maxDate)
  if (minDate && dateValue < minDate) return true
  if (maxDate && dateValue > maxDate) return true
  return false
}

function handleClickOutside(event) {
  if (!rootEl.value || rootEl.value.contains(event.target)) return
  isOpen.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<style scoped>
.day-cell {
  border-color: #e5e7eb;
}

:global(.dark) .day-cell {
  border-color: #4b5563;
}

.day-normal {
  color: #374151;
  background-color: transparent;
}

:global(.dark) .day-normal {
  color: #e5e7eb;
}

.day-normal:hover {
  background-color: #f3f4f6;
}

:global(.dark) .day-normal:hover {
  background-color: #374151;
}

.day-selected {
  background-color: #f59e0b;
  border-color: #f59e0b;
  color: #ffffff;
}

.day-today {
  border-color: #f59e0b;
  color: #d97706;
  font-weight: 700;
}

:global(.dark) .day-today {
  color: #fcd34d;
}

.day-disabled {
  color: #cbd5e1;
  background-color: #f8fafc;
  cursor: not-allowed;
}

:global(.dark) .day-disabled {
  color: #6b7280;
  background-color: #111827;
}
</style>
