<template>
  <div class="persian-number-input">
    <div class="input-wrap">
      <input
        :value="inputText"
        class="input number-input"
        :class="inputClass"
        type="text"
        inputmode="decimal"
        dir="ltr"
        :placeholder="placeholder"
        :disabled="disabled"
        @focus="onFocus"
        @blur="onBlur"
        @input="onInput"
        @keydown.enter.prevent="$emit('enter')"
        @keydown.esc.prevent="$emit('esc')"
      />
      <span v-if="suffix" class="suffix">{{ suffix }}</span>
    </div>
    <small v-if="showWords && Number(modelValue || 0) > 0" class="word-hint">{{ wordLabel }}</small>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: 0,
  },
  placeholder: {
    type: String,
    default: '',
  },
  suffix: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  allowFloat: {
    type: Boolean,
    default: false,
  },
  min: {
    type: Number,
    default: null,
  },
  max: {
    type: Number,
    default: null,
  },
  showWords: {
    type: Boolean,
    default: false,
  },
  currencyLabel: {
    type: String,
    default: 'ریال',
  },
  inputClass: {
    type: [String, Array, Object],
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'blur', 'enter', 'esc'])

const focused = ref(false)
const inputText = ref('')

watch(
  () => props.modelValue,
  (nextValue) => {
    if (!focused.value) {
      inputText.value = formatForDisplay(toNumeric(nextValue))
    }
  },
  { immediate: true },
)

const wordLabel = computed(() => {
  const value = Math.max(toNumeric(props.modelValue), 0)
  if (!value) {
    return ''
  }
  return `${numberToWords(value)} ${props.currencyLabel}`
})

function onFocus() {
  focused.value = true
  inputText.value = formatForDisplay(toNumeric(props.modelValue))
}

function onBlur() {
  focused.value = false
  inputText.value = formatForDisplay(toNumeric(props.modelValue))
  emit('blur')
}

function onInput(event) {
  const rawValue = String(event?.target?.value || '')
  const normalized = normalizeRawValue(rawValue)
  const parsed = parseNumeric(normalized)
  const clamped = clampValue(parsed)
  inputText.value = clamped ? formatForDisplay(clamped) : ''
  emit('update:modelValue', clamped)
  emit('change', clamped)
}

function normalizeRawValue(value) {
  const english = toEnglishDigits(value).replace(/[٬,\s]/g, '').replace(/٫/g, '.')
  return props.allowFloat ? english.replace(/[^0-9.-]/g, '') : english.replace(/[^0-9-]/g, '')
}

function parseNumeric(value) {
  if (value === '' || value === '-' || value === '.') {
    return 0
  }
  const parsed = props.allowFloat ? parseFloat(value) : parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : 0
}

function toNumeric(value) {
  const raw = normalizeRawValue(String(value ?? ''))
  return parseNumeric(raw)
}

function clampValue(value) {
  let nextValue = Number(value || 0)
  if (typeof props.min === 'number') {
    nextValue = Math.max(nextValue, props.min)
  }
  if (typeof props.max === 'number') {
    nextValue = Math.min(nextValue, props.max)
  }
  if (!props.allowFloat) {
    nextValue = Math.round(nextValue)
  }
  return nextValue
}

function formatForDisplay(value) {
  const numeric = Number(value || 0)
  if (!numeric) {
    return ''
  }

  const raw = props.allowFloat
    ? Number(numeric.toFixed(3)).toString()
    : String(Math.round(numeric))
  const [integerPart, decimalPart] = raw.split('.')
  const groupSeparator = props.allowFloat ? '٬' : '.'
  const decimalSeparator = props.allowFloat ? '٫' : '.'
  const grouped = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, groupSeparator)
  const formatted = decimalPart ? `${grouped}${decimalSeparator}${decimalPart}` : grouped
  return toPersianDigits(formatted)
}

function toPersianDigits(value) {
  const digits = '۰۱۲۳۴۵۶۷۸۹'
  return String(value).replace(/\d/g, (digit) => digits[Number(digit)])
}

function toEnglishDigits(value) {
  const faDigits = '۰۱۲۳۴۵۶۷۸۹'
  let text = String(value || '')
  for (let idx = 0; idx < faDigits.length; idx += 1) {
    text = text.replace(new RegExp(faDigits[idx], 'g'), String(idx))
  }
  return text
}

function numberToWords(value) {
  const ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
  const tens = ['', 'ده', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
  const teens = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده']
  const hundreds = ['', 'صد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
  const scales = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون']

  function threeDigitsToWords(chunk) {
    if (!chunk) {
      return ''
    }
    const parts = []
    if (chunk >= 100) {
      parts.push(hundreds[Math.floor(chunk / 100)])
      chunk %= 100
    }
    if (chunk >= 20) {
      parts.push(tens[Math.floor(chunk / 10)])
      if (chunk % 10) {
        parts.push(ones[chunk % 10])
      }
    } else if (chunk >= 10) {
      parts.push(teens[chunk - 10])
    } else if (chunk > 0) {
      parts.push(ones[chunk])
    }
    return parts.filter(Boolean).join(' و ')
  }

  let num = Math.floor(Number(value || 0))
  if (!num) {
    return 'صفر'
  }

  const parts = []
  let scaleIndex = 0
  while (num > 0 && scaleIndex < scales.length) {
    const chunk = num % 1000
    if (chunk > 0) {
      const text = threeDigitsToWords(chunk)
      const suffix = scales[scaleIndex]
      parts.unshift([text, suffix].filter(Boolean).join(' '))
    }
    num = Math.floor(num / 1000)
    scaleIndex += 1
  }
  return parts.join(' و ')
}
</script>

<style scoped>
.persian-number-input {
  display: grid;
  gap: 0.2rem;
}

.input-wrap {
  position: relative;
}

.number-input {
  padding-left: 3rem;
}

.input-wrap:not(:has(.suffix)) .number-input,
.number-input:not(:has(+ .suffix)) {
  padding-left: 0.6rem;
}

.suffix {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 0.75rem;
  pointer-events: none;
}

.word-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
}
</style>
