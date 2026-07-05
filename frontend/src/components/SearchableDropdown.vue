<template>
  <div
    ref="rootRef"
    class="searchable-dropdown"
    :class="[`tone-${tone}`, { 'is-open': isOpen, 'is-disabled': disabled }]"
  >
    <button
      type="button"
      class="select trigger"
      :disabled="disabled"
      @click="toggleOpen"
      @keydown.down.prevent="openAndFocus"
      @keydown.enter.prevent="toggleOpen"
      @keydown.space.prevent="toggleOpen"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
    >
      <span class="selected-label" :class="{ placeholder: !selectedLabel }">
        {{ selectedLabel || placeholder }}
      </span>
      <span class="trigger-actions">
        <span
          v-if="clearable && hasValue"
          class="clear-btn"
          role="button"
          tabindex="0"
          title="پاک کردن"
          @click.stop="clearValue"
          @keydown.enter.prevent="clearValue"
          @keydown.space.prevent="clearValue"
        >
          ×
        </span>
        <span class="chevron" aria-hidden="true">{{ isOpen ? '▴' : '▾' }}</span>
      </span>
    </button>

    <div v-if="isOpen" class="dropdown-panel" role="listbox">
      <div class="search-row">
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          class="input search-input"
          :placeholder="searchPlaceholder"
          @keydown.esc.prevent="close"
          @keydown.down.prevent="highlightNext"
          @keydown.up.prevent="highlightPrev"
          @keydown.enter.prevent="selectHighlighted"
        />
      </div>

      <div class="options-list">
        <button
          v-for="(option, index) in filteredOptions"
          :key="`option-${index}-${String(option.value)}`"
          type="button"
          class="option-btn"
          :class="{
            selected: isSelected(option.value),
            highlighted: index === highlightedIndex,
          }"
          @mouseenter="highlightedIndex = index"
          @click="selectOption(option.value)"
        >
          <span class="option-label">{{ option.label }}</span>
          <span class="option-check" v-if="isSelected(option.value)">✓</span>
        </button>

        <button
          v-if="createOption"
          type="button"
          class="option-btn create-option-btn"
          @click="createOptionFromSearch"
        >
          <span class="option-label">{{ createOption.label }}</span>
          <span class="option-check">+</span>
        </button>

        <p v-if="!filteredOptions.length && !createOption" class="empty-text">{{ noResultsText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Array, null],
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'انتخاب کنید',
  },
  searchPlaceholder: {
    type: String,
    default: 'جستجو...',
  },
  noResultsText: {
    type: String,
    default: 'نتیجه‌ای پیدا نشد',
  },
  labelKey: {
    type: String,
    default: 'label',
  },
  valueKey: {
    type: String,
    default: 'value',
  },
  includeEmptyOption: {
    type: Boolean,
    default: false,
  },
  emptyLabel: {
    type: String,
    default: 'انتخاب نشده',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  tone: {
    type: String,
    default: 'default',
  },
  allowCreate: {
    type: Boolean,
    default: false,
  },
  createOptionLabel: {
    type: String,
    default: 'افزودن مقدار جدید',
  },
})

const emit = defineEmits(['update:modelValue', 'create-option'])

const rootRef = ref(null)
const searchInputRef = ref(null)
const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(-1)

const normalizedOptions = computed(() => {
  const mapped = (props.options || []).map((option) => {
    if (option && typeof option === 'object') {
      const label = option[props.labelKey] ?? option.label ?? option[props.valueKey] ?? option.value ?? ''
      const value = option[props.valueKey] ?? option.value ?? option[props.labelKey] ?? option.label ?? ''
      return {
        label: String(label || value || ''),
        value,
      }
    }
    return {
      label: String(option ?? ''),
      value: option,
    }
  })

  if (props.includeEmptyOption) {
    mapped.unshift({ label: props.emptyLabel, value: '' })
  }

  return mapped
})

const filteredOptions = computed(() => {
  const query = String(searchQuery.value || '').trim().toLowerCase()
  if (!query) {
    return normalizedOptions.value
  }
  return normalizedOptions.value.filter((option) => {
    const label = String(option.label || '').toLowerCase()
    const value = String(option.value || '').toLowerCase()
    return label.includes(query) || value.includes(query)
  })
})

const createOption = computed(() => {
  if (!props.allowCreate) {
    return null
  }
  const query = String(searchQuery.value || '').trim()
  if (!query) {
    return null
  }
  const normalizedQuery = query.toLowerCase()
  const exists = normalizedOptions.value.some((option) => {
    const label = String(option.label || '').trim().toLowerCase()
    const value = String(option.value || '').trim().toLowerCase()
    return normalizedQuery === label || normalizedQuery === value
  })
  if (exists) {
    return null
  }
  return {
    label: `${props.createOptionLabel}: ${query}`,
    value: query,
  }
})

const selectedValues = computed(() => {
  if (props.multiple) {
    if (Array.isArray(props.modelValue)) {
      return props.modelValue
    }
    if (props.modelValue === '' || props.modelValue === null || props.modelValue === undefined) {
      return []
    }
    return [props.modelValue]
  }
  return [props.modelValue]
})

const selectedOptions = computed(() =>
  normalizedOptions.value.filter((option) => selectedValues.value.some((value) => isSameValue(value, option.value))),
)

const selectedLabel = computed(() => {
  if (!props.multiple) {
    return selectedOptions.value[0]?.label || String(props.modelValue ?? '').trim()
  }

  if (!selectedOptions.value.length) {
    return ''
  }
  if (selectedOptions.value.length <= 2) {
    return selectedOptions.value.map((row) => row.label).join('، ')
  }
  return `${selectedOptions.value.length} مورد انتخاب شد`
})

const hasValue = computed(() => {
  if (props.multiple) {
    return selectedValues.value.length > 0
  }
  return !(props.modelValue === '' || props.modelValue === null || props.modelValue === undefined)
})

watch(
  () => isOpen.value,
  async (openState) => {
    if (openState) {
      searchQuery.value = ''
      highlightedIndex.value = selectedOptionIndex()
      await nextTick()
      searchInputRef.value?.focus?.()
      return
    }
    searchQuery.value = ''
    highlightedIndex.value = -1
  },
)

function selectedOptionIndex() {
  const firstSelected = selectedValues.value[0]
  return filteredOptions.value.findIndex((option) => isSameValue(firstSelected, option.value))
}

function isSelected(value) {
  return selectedValues.value.some((entry) => isSameValue(entry, value))
}

function selectOption(value) {
  if (!props.multiple) {
    emit('update:modelValue', value ?? '')
    close()
    return
  }

  const next = [...selectedValues.value]
  const selectedIndex = next.findIndex((entry) => isSameValue(entry, value))
  if (selectedIndex >= 0) {
    next.splice(selectedIndex, 1)
  } else {
    next.push(value)
  }
  emit('update:modelValue', next)
  searchQuery.value = ''
  highlightedIndex.value = -1
  nextTick(() => searchInputRef.value?.focus?.())
}

function clearValue() {
  emit('update:modelValue', props.multiple ? [] : '')
  if (!props.multiple) {
    close()
  }
}

function toggleOpen() {
  if (props.disabled) {
    return
  }
  isOpen.value = !isOpen.value
}

function openAndFocus() {
  if (props.disabled) {
    return
  }
  isOpen.value = true
}

function close() {
  isOpen.value = false
}

function highlightNext() {
  if (!filteredOptions.value.length) {
    highlightedIndex.value = -1
    return
  }
  highlightedIndex.value = Math.min(highlightedIndex.value + 1, filteredOptions.value.length - 1)
}

function highlightPrev() {
  if (!filteredOptions.value.length) {
    highlightedIndex.value = -1
    return
  }
  highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
}

function selectHighlighted() {
  if (highlightedIndex.value < 0 || highlightedIndex.value >= filteredOptions.value.length) {
    if (createOption.value) {
      createOptionFromSearch()
    }
    return
  }
  selectOption(filteredOptions.value[highlightedIndex.value].value)
}

function createOptionFromSearch() {
  const option = createOption.value
  if (!option) {
    return
  }
  emit('create-option', option.value)
  selectOption(option.value)
}

function isSameValue(left, right) {
  return String(left ?? '') === String(right ?? '')
}

function onDocumentClick(event) {
  if (!isOpen.value) {
    return
  }
  if (!rootRef.value?.contains(event.target)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocumentClick)
})
</script>

<style scoped>
.searchable-dropdown {
  position: relative;
  width: 100%;
  z-index: 1;
}

.searchable-dropdown.is-open {
  z-index: 1200;
}

.trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  text-align: right;
  cursor: pointer;
}

.selected-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-label.placeholder {
  color: var(--text-muted);
}

.trigger-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.24rem;
  margin-inline-start: auto;
}

.chevron {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.clear-btn {
  width: 1.35rem;
  height: 1.35rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  border-radius: 999px;
  background: rgb(var(--palette-eggshell-rgb) / 0.85);
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.clear-btn:hover {
  color: var(--text-primary);
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 0.35rem);
  inset-inline-start: 0;
  width: 100%;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 18px 30px rgb(15 23 42 / 0.14);
  overflow: hidden;
  z-index: 1201;
}

.search-row {
  padding: 0.5rem;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.search-input {
  padding: 0.52rem 0.64rem;
}

.options-list {
  max-height: 260px;
  overflow-y: auto;
  padding: 0.25rem;
}

.option-btn {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 0.48rem 0.56rem;
  font-size: 0.8rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  text-align: right;
  cursor: pointer;
}

.option-btn:hover,
.option-btn.highlighted {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.09);
}

.option-btn.selected {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.create-option-btn {
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  margin-top: 0.24rem;
}

.option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-check {
  color: var(--accent-green);
  font-size: 0.8rem;
}

.empty-text {
  margin: 0;
  padding: 0.75rem 0.65rem;
  font-size: 0.76rem;
  color: var(--text-muted);
  text-align: center;
}

.is-disabled .trigger {
  cursor: not-allowed;
  opacity: 0.68;
}

.tone-dark .trigger {
  border-color: rgb(255 255 255 / 0.22);
  background: rgb(255 255 255 / 0.08);
  color: #f8fafc;
}

.tone-dark .selected-label.placeholder,
.tone-dark .chevron {
  color: rgb(255 255 255 / 0.62);
}

.tone-dark .clear-btn {
  border-color: rgb(255 255 255 / 0.28);
  background: rgb(255 255 255 / 0.12);
  color: rgb(255 255 255 / 0.82);
}

.tone-dark .dropdown-panel {
  border-color: rgb(255 255 255 / 0.26);
  background: #0f172a;
  box-shadow: 0 20px 34px rgb(2 6 23 / 0.62);
}

.tone-dark .search-row {
  border-bottom-color: rgb(255 255 255 / 0.16);
}

.tone-dark .search-input {
  border-color: rgb(255 255 255 / 0.22);
  background: rgb(15 23 42 / 0.88);
  color: #f8fafc;
}

.tone-dark .search-input::placeholder {
  color: rgb(255 255 255 / 0.52);
}

.tone-dark .option-btn {
  color: #e2e8f0;
}

.tone-dark .option-btn:hover,
.tone-dark .option-btn.highlighted {
  background: rgb(37 99 235 / 0.22);
}

.tone-dark .option-btn.selected {
  background: rgb(37 99 235 / 0.3);
}

.tone-dark .empty-text {
  color: rgb(255 255 255 / 0.56);
}
</style>
