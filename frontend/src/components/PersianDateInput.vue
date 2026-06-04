<template>
  <div class="persian-date-input" :class="{ disabled }">
    <date-picker
      v-model="internalValue"
      format="YYYY-MM-DD"
      display-format="jYYYY/jMM/jDD"
      :placeholder="placeholder"
      :disabled="disabled"
      :editable="false"
      auto-submit
      :color="pickerColor"
      :min="normalizedMin"
      :max="normalizedMax"
      :input-class="['management-date-input', inputClass]"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import DatePicker from 'vue3-persian-datetime-picker'

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
    type: Boolean,
    default: false,
  },
  min: {
    type: String,
    default: '',
  },
  max: {
    type: String,
    default: '',
  },
  inputClass: {
    type: [String, Array, Object],
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const internalValue = ref(normalizeDateOnly(props.modelValue))
const normalizedMin = computed(() => normalizeDateOnly(props.min))
const normalizedMax = computed(() => normalizeDateOnly(props.max))
const pickerColor = ref('#6F4A31')

function syncPickerColor() {
  if (typeof window === 'undefined') {
    return
  }
  const nextColor = window.getComputedStyle(document.documentElement).getPropertyValue('--accent-green').trim()
  pickerColor.value = nextColor || '#6F4A31'
}

onMounted(() => {
  syncPickerColor()
  if (typeof window !== 'undefined') {
    window.addEventListener('restaurant-theme-updated', syncPickerColor)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('restaurant-theme-updated', syncPickerColor)
  }
})

watch(
  () => props.modelValue,
  (nextValue) => {
    const normalized = normalizeDateOnly(nextValue)
    if (internalValue.value !== normalized) {
      internalValue.value = normalized
    }
  },
)

watch(
  internalValue,
  (nextValue) => {
    emit('update:modelValue', normalizeDateOnly(nextValue))
  },
)

function normalizeDateOnly(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return ''
  }
  return raw.length >= 10 ? raw.slice(0, 10) : raw
}

</script>

<style scoped>
.persian-date-input {
  width: 100%;
}

.persian-date-input :deep(.vpd-content) {
  background: var(--palette-eggshell);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  border-radius: 14px;
  box-shadow: 0 16px 34px rgb(var(--palette-deep-sapphire-rgb) / 0.24) !important;
  color: var(--text-primary);
}

.persian-date-input :deep(.vpd-header) {
  background: var(--accent-green);
  color: #fff;
}

.persian-date-input :deep(.management-date-input) {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  border-right: none;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-top-left-radius: 11px;
  border-bottom-left-radius: 11px;
  background: var(--palette-eggshell);
  color: var(--text-primary);
}

.persian-date-input :deep(.management-date-input::placeholder) {
  color: var(--text-muted);
}

.persian-date-input :deep(.vpd-icon-btn) {
  background: var(--accent-green) !important;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  border-left: none;
  color: #fff;
  border-top-right-radius: 11px;
  border-bottom-right-radius: 11px;
}

.persian-date-input :deep(.vpd-week) {
  color: var(--text-muted);
}

.persian-date-input :deep(.vpd-month-label > span),
.persian-date-input :deep(.vpd-year-label > span) {
  color: var(--text-primary) !important;
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.24) !important;
}

.persian-date-input :deep(.vpd-controls button),
.persian-date-input :deep(.vpd-day-text) {
  color: var(--text-primary);
}

.persian-date-input :deep(.vpd-day-effect) {
  background: var(--accent-green);
}

.persian-date-input :deep(.vpd-day:not([disabled='true']):hover .vpd-day-effect),
.persian-date-input :deep(.vpd-day:not([disabled='true']).vpd-range-hover .vpd-day-effect) {
  background: var(--accent-gold);
}

.persian-date-input :deep(.vpd-day[disabled='true']),
.persian-date-input :deep(.vpd-day[disabled='true'] .vpd-day-text) {
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.34) !important;
}

.persian-date-input :deep(.vpd-actions button) {
  color: var(--accent-green);
}

.persian-date-input :deep(.vpd-actions button:hover) {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.persian-date-input :deep(.vpd-addon-list),
.persian-date-input :deep(.vpd-simple-content),
.persian-date-input :deep(.vpd-simple-content .vpd-column .vpd-column-content) {
  background: var(--palette-eggshell);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
}

.persian-date-input :deep(.vpd-addon-list-item) {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--text-secondary);
}

.persian-date-input :deep(.vpd-addon-list-item.vpd-selected),
.persian-date-input :deep(.vpd-addon-list-item:hover) {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: var(--text-primary);
}
</style>
