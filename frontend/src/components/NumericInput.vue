<template>
  <input
    ref="inputRef"
    type="text"
    :value="displayValue"
    :disabled="disabled"
    :placeholder="placeholder"
    :class="['numeric-input', inputClass]"
    inputmode="decimal"
    dir="ltr"
    @input="handleInput"
    @focus="handleFocus"
    @blur="handleBlur"
  />
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Number, String, null],
    default: null,
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  inputClass: {
    type: String,
    default: '',
  },
  allowNegative: {
    type: Boolean,
    default: false,
  },
  separator: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue', 'input'])

const inputRef = ref(null)

const EN_DIGITS = '0123456789'
const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'

function toEnglishDigits(value) {
  return String(value || '')
    .replace(/[۰-۹]/g, (digit) => EN_DIGITS[FA_DIGITS.indexOf(digit)] || digit)
    .replace(/[٠-٩]/g, (digit) => EN_DIGITS[AR_DIGITS.indexOf(digit)] || digit)
}

function toPersianDigits(value) {
  return String(value || '').replace(/\d/g, (digit) => FA_DIGITS[Number(digit)] || digit)
}

function formatNumber(value) {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  let normalized = toEnglishDigits(value).trim()
  if (!normalized) {
    return ''
  }

  normalized = normalized.replace(/,/g, '')
  const negative = normalized.startsWith('-')
  if (negative) {
    normalized = normalized.slice(1)
  }

  const [integerPartRaw, decimalPartRaw] = normalized.split('.')
  const integerPart = String(integerPartRaw || '').replace(/\D/g, '')
  const decimalPart = String(decimalPartRaw || '').replace(/\D/g, '')
  const baseInteger = integerPart || '0'
  const groupedInteger = props.separator
    ? baseInteger.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    : baseInteger
  const signedInteger = negative ? `-${groupedInteger}` : groupedInteger
  const display = decimalPartRaw !== undefined ? `${signedInteger}.${decimalPart}` : signedInteger
  return toPersianDigits(display)
}

const displayValue = computed(() => formatNumber(props.modelValue))

function normalizeRawNumber(rawValue) {
  let value = toEnglishDigits(rawValue || '').replace(/[,\u066C]/g, '').trim()
  if (!value) {
    return { parsed: null, normalized: '' }
  }

  let sign = 1
  if (props.allowNegative && value.startsWith('-')) {
    sign = -1
    value = value.slice(1)
  }

  value = value.replace(/[^0-9.]/g, '')
  const parts = value.split('.')
  if (parts.length > 2) {
    value = `${parts[0]}.${parts.slice(1).join('')}`
  }

  if (!value) {
    return { parsed: null, normalized: '' }
  }

  const parsed = Number.parseFloat(value)
  if (Number.isNaN(parsed)) {
    return { parsed: null, normalized: '' }
  }

  const numericValue = parsed * sign
  const normalized = sign < 0 ? `-${value}` : value
  return { parsed: numericValue, normalized }
}

function handleInput(event) {
  const { parsed } = normalizeRawNumber(event?.target?.value)
  emit('update:modelValue', parsed)
  emit('input', parsed)
}

function handleFocus() {
  inputRef.value?.select?.()
}

function handleBlur() {
  // keep hook for parity with native input behavior
}
</script>

<style scoped>
.numeric-input {
  direction: ltr;
  text-align: center;
}
</style>
