<template>
  <div class="jalali-shell" dir="rtl">
    <div class="flex items-center justify-between mb-3">
      <button type="button" class="nav-btn" @click="prevUnit">
        <ChevronRightIcon class="w-4 h-4" />
      </button>

      <div class="flex items-center gap-1">
        <button
          v-if="currentView === 'days'"
          type="button"
          class="label-btn"
          @click="emit('update:view', 'months')"
        >
          {{ jalaliMonthNames[activeMonth.month - 1] }}
        </button>
        <button
          v-if="currentView !== 'years'"
          type="button"
          class="label-btn"
          @click="emit('update:view', 'years')"
        >
          {{ toPersianDigits(activeMonth.year) }}
        </button>
        <span v-if="currentView === 'years'" class="label-btn cursor-default">
          انتخاب سال
        </span>
      </div>

      <button type="button" class="nav-btn" @click="nextUnit">
        <ChevronLeftIcon class="w-4 h-4" />
      </button>
    </div>

    <div v-if="currentView === 'days'">
      <slot />
    </div>

    <div v-else-if="currentView === 'months'" class="grid grid-cols-3 gap-1.5">
      <button
        v-for="(name, idx) in jalaliMonthNames"
        :key="idx"
        type="button"
        class="month-btn"
        :class="activeMonth.month === idx + 1 ? 'month-btn-active' : ''"
        @click="selectMonth(idx + 1)"
      >
        {{ name }}
      </button>
    </div>

    <div v-else-if="currentView === 'years'" class="grid grid-cols-4 gap-1.5 max-h-48 overflow-y-auto">
      <button
        v-for="year in yearRange"
        :key="year"
        type="button"
        class="year-btn"
        :class="activeMonth.year === year ? 'year-btn-active' : ''"
        @click="selectYear(year)"
      >
        {{ toPersianDigits(year) }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-vue-next'
import { toPersianDigits } from '@/utils/jalali'

const props = defineProps({
  view: { type: String, default: 'days' },
  activeMonth: { type: Object, required: true },
})

const emit = defineEmits(['update:view', 'update:activeMonth'])

const jalaliMonthNames = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

const currentView = computed(() => props.view)

const yearRange = computed(() => {
  const base = props.activeMonth.year
  const years = []
  for (let y = base - 10; y <= base + 10; y++) years.push(y)
  return years
})

function prevUnit() {
  if (currentView.value === 'years') {
    emit('update:activeMonth', { ...props.activeMonth, year: props.activeMonth.year - 12 })
  } else if (currentView.value === 'months') {
    emit('update:activeMonth', { ...props.activeMonth, year: props.activeMonth.year - 1 })
  } else {
    let { year, month } = props.activeMonth
    month -= 1
    if (month < 1) { month = 12; year -= 1 }
    emit('update:activeMonth', { year, month })
  }
}

function nextUnit() {
  if (currentView.value === 'years') {
    emit('update:activeMonth', { ...props.activeMonth, year: props.activeMonth.year + 12 })
  } else if (currentView.value === 'months') {
    emit('update:activeMonth', { ...props.activeMonth, year: props.activeMonth.year + 1 })
  } else {
    let { year, month } = props.activeMonth
    month += 1
    if (month > 12) { month = 1; year += 1 }
    emit('update:activeMonth', { year, month })
  }
}

function selectMonth(month) {
  emit('update:activeMonth', { ...props.activeMonth, month })
  emit('update:view', 'days')
}

function selectYear(year) {
  emit('update:activeMonth', { ...props.activeMonth, year })
  emit('update:view', 'months')
}
</script>

<style scoped>
.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: transparent;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  transition: background 0.15s, color 0.15s;
}
.nav-btn:hover {
  background: #f3f4f6;
  color: #111827;
}
.label-btn {
  padding: 0.2rem 0.5rem;
  border-radius: 0.4rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #374151;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.label-btn:hover {
  background: #f3f4f6;
}
.month-btn {
  padding: 0.4rem 0.2rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
  background: transparent;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background 0.15s;
}
.month-btn:hover {
  background: #fef3c7;
  border-color: #f59e0b;
}
.month-btn-active {
  background: #f59e0b !important;
  border-color: #f59e0b !important;
  color: #fff !important;
}
.year-btn {
  padding: 0.35rem 0.2rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
  background: transparent;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background 0.15s;
}
.year-btn:hover {
  background: #fef3c7;
  border-color: #f59e0b;
}
.year-btn-active {
  background: #f59e0b !important;
  border-color: #f59e0b !important;
  color: #fff !important;
}
</style>
