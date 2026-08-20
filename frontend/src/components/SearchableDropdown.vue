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

    <div
      v-if="isOpen"
      class="dropdown-panel"
      :class="{ 'dropdown-panel--fixed': fixedPanel }"
      :style="fixedPanel ? panelStyle : {}"
      role="listbox"
    >
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

        <button
          v-if="missingItemOption"
          type="button"
          class="option-btn create-item-option"
          @click="openItemCreator"
        >
          <span class="option-label">ایجاد کالا «{{ missingItemOption.value }}»</span>
          <span class="option-check">+</span>
        </button>
        <p v-if="!filteredOptions.length && !createOption && !missingItemOption" class="empty-text">{{ noResultsText }}</p>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="itemCreatorOpen" class="item-create-backdrop" @click.self="closeItemCreator">
        <section class="item-create-modal" dir="rtl" role="dialog" aria-modal="true" aria-label="ایجاد کالای جدید" @click.stop>
          <header class="item-create-head">
            <div>
              <span class="item-create-kicker">کالای جدید</span>
              <h3>ایجاد «{{ itemForm.item_name }}»</h3>
            </div>
            <button type="button" class="item-create-close" @click="closeItemCreator">×</button>
          </header>
          <p class="item-create-hint">این کالا در ERPNext ساخته می‌شود و سپس در همین فهرست انتخاب خواهد شد.</p>
          <p v-if="itemCreateError" class="item-create-error">{{ itemCreateError }}</p>
          <div class="item-create-grid">
            <label>نام کالا
              <input class="input" v-model.trim="itemForm.item_name" />
            </label>
            <label>کد کالا
              <input class="input" v-model.trim="itemForm.item_code" dir="ltr" />
            </label>
            <label>واحد پیش‌فرض
              <select class="input" v-model="itemForm.stock_uom" :disabled="itemUomsLoading">
                <option v-for="uom in itemUomOptions" :key="uom" :value="uom">{{ uom }}</option>
              </select>
            </label>
            <label>گروه کالا
              <input class="input" v-model.trim="itemForm.item_group" placeholder="All Item Groups" />
            </label>
            <label>موجودی اولیه
              <input class="input" type="number" min="0" step="0.001" v-model.number="itemForm.opening_qty" />
            </label>
            <label>انبار موجودی اولیه
              <select class="input" v-model="itemForm.opening_warehouse" :disabled="warehousesLoading">
                <option value="">بدون موجودی اولیه</option>
                <option v-for="warehouse in itemWarehouses" :key="warehouse" :value="warehouse">{{ warehouse }}</option>
              </select>
            </label>
          </div>
          <footer class="item-create-actions">
            <button type="button" class="secondary-btn" @click="closeItemCreator">انصراف</button>
            <button type="button" class="primary-btn" :disabled="itemCreateSaving || !itemForm.item_name || !itemForm.item_code || !itemForm.stock_uom" @click="createMissingItem">
              {{ itemCreateSaving ? 'در حال ساخت...' : 'ساخت و انتخاب کالا' }}
            </button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { createManagementInventoryItem, listManagementUOMs, listManagementWarehouses } from '@/utils/api'

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
  allowItemCreate: {
    type: Boolean,
    default: false,
  },
  itemCreateDefaults: {
    type: Object,
    default: () => ({}),
  },
  createOptionLabel: {
    type: String,
    default: 'افزودن مقدار جدید',
  },
  fixedPanel: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'create-option', 'item-created'])

const rootRef = ref(null)
const searchInputRef = ref(null)
const isOpen = ref(false)
const panelStyle = ref({})
const searchQuery = ref('')
const highlightedIndex = ref(-1)
const itemCreatorOpen = ref(false)
const itemCreateSaving = ref(false)
const itemCreateError = ref('')
const itemUomsLoading = ref(false)
const warehousesLoading = ref(false)
const itemUomOptions = ref([])
const itemWarehouses = ref([])
const itemForm = reactive({
  item_name: '',
  item_code: '',
  stock_uom: '',
  item_group: 'All Item Groups',
  opening_qty: 0,
  opening_warehouse: '',
})
const createdOptions = ref([])

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

  const merged = [...createdOptions.value, ...mapped]
  if (props.includeEmptyOption) {
    merged.unshift({ label: props.emptyLabel, value: '' })
  }

  return merged
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

const missingItemOption = computed(() => {
  if (!props.allowItemCreate) return null
  const query = String(searchQuery.value || '').trim()
  if (!query || filteredOptions.value.length) return null
  return { value: query, label: query }
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

function updatePanelPosition() {
  if (!props.fixedPanel || !rootRef.value) return
  const rect = rootRef.value.getBoundingClientRect()
  const panelWidth = Math.max(rect.width, 220)
  const spaceBelow = window.innerHeight - rect.bottom
  const panelHeight = 320
  const openUp = spaceBelow < panelHeight && rect.top > spaceBelow
  panelStyle.value = {
    position: 'fixed',
    top: openUp ? `${Math.max(8, rect.top - panelHeight)}px` : `${rect.bottom + 6}px`,
    insetInlineStart: `${Math.max(8, Math.min(rect.left, window.innerWidth - panelWidth - 8))}px`,
    width: `${panelWidth}px`,
    maxHeight: `${Math.min(panelHeight, window.innerHeight - 16)}px`,
    zIndex: 13000,
  }
}

function toggleOpen() {
  if (props.disabled) {
    return
  }
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    updatePanelPosition()
  }
}

function openAndFocus() {
  if (props.disabled) {
    return
  }
  updatePanelPosition()
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

async function openItemCreator() {
  const query = String(missingItemOption.value?.value || searchQuery.value || '').trim()
  if (!query) return
  itemCreateError.value = ''
  itemForm.item_name = query
  itemForm.item_code = query
  itemForm.stock_uom = String(props.itemCreateDefaults?.stock_uom || '')
  itemForm.item_group = String(props.itemCreateDefaults?.item_group || 'All Item Groups')
  itemForm.opening_qty = Number(props.itemCreateDefaults?.opening_qty || 0)
  itemForm.opening_warehouse = String(props.itemCreateDefaults?.opening_warehouse || '')
  itemCreatorOpen.value = true
  isOpen.value = false
  itemUomsLoading.value = true
  warehousesLoading.value = true
  try {
    const [uomPayload, warehousePayload] = await Promise.all([
      listManagementUOMs({ limit: 300 }),
      listManagementWarehouses({ options_only: 1 }),
    ])
    itemUomOptions.value = Array.isArray(uomPayload?.uoms) ? uomPayload.uoms : []
    itemWarehouses.value = (warehousePayload?.warehouses || [])
      .filter((row) => Number(row?.is_group || 0) !== 1 && Number(row?.disabled || 0) !== 1)
      .map((row) => row.name || row.warehouse_name)
      .filter(Boolean)
    if (!itemForm.stock_uom) itemForm.stock_uom = itemUomOptions.value[0] || 'Nos'
    if (!itemForm.opening_warehouse) itemForm.opening_warehouse = itemWarehouses.value[0] || ''
  } catch (error) {
    itemCreateError.value = error?.message || 'دریافت واحدها و انبارها ناموفق بود.'
    if (!itemForm.stock_uom) itemForm.stock_uom = 'Nos'
  } finally {
    itemUomsLoading.value = false
    warehousesLoading.value = false
  }
}

function closeItemCreator() {
  if (itemCreateSaving.value) return
  itemCreatorOpen.value = false
  itemCreateError.value = ''
}

async function createMissingItem() {
  if (itemCreateSaving.value) return
  itemCreateSaving.value = true
  itemCreateError.value = ''
  try {
    const result = await createManagementInventoryItem({ ...itemForm, is_stock_item: 1 })
    const value = result.item_code || result.name
    createdOptions.value = [
      { value, label: `${result.item_name || value} (${value})` },
      ...createdOptions.value.filter((option) => String(option.value) !== String(value)),
    ]
    emit('update:modelValue', value)
    emit('item-created', result)
    itemCreatorOpen.value = false
    itemCreateError.value = ''
  } catch (error) {
    itemCreateError.value = error?.message || 'ساخت کالا ناموفق بود.'
  } finally {
    itemCreateSaving.value = false
  }
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
  color: var(--mg-text-muted);
}

.trigger-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.24rem;
  margin-inline-start: auto;
}

.chevron {
  color: var(--mg-text-muted);
  font-size: 0.74rem;
}

.clear-btn {
  width: 1.35rem;
  height: 1.35rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 999px;
  background: var(--mg-bg-soft);
  color: var(--mg-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.clear-btn:hover {
  color: var(--mg-text-main);
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 0.35rem);
  inset-inline-start: 0;
  width: 100%;
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  box-shadow: var(--mg-shadow-md);
  overflow: hidden;
  z-index: 1201;
}

.dropdown-panel--fixed {
  position: fixed;
  overflow-y: auto;
}

.search-row {
  padding: 0.5rem;
  border-bottom: 1px solid var(--mg-border-light);
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
  color: var(--mg-text-main);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  text-align: right;
  cursor: pointer;
}

.option-btn:hover,
.option-btn.highlighted {
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

.option-btn.selected {
  background: color-mix(in srgb, var(--mg-primary) 16%, transparent);
}

.create-option-btn {
  border: 1px dashed color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  margin-top: 0.24rem;
}

.create-item-option {
  margin-top: 0.3rem;
  border: 1px dashed color-mix(in srgb, var(--mg-primary, #c97852) 45%, transparent);
  background: color-mix(in srgb, var(--mg-primary, #c97852) 8%, transparent);
  color: var(--mg-primary, #c97852);
  font-weight: 800;
}

.item-create-backdrop {
  position: fixed;
  inset: 0;
  z-index: 15000;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(30 22 17 / 0.48);
  backdrop-filter: blur(4px);
}

.item-create-modal {
  width: min(600px, 100%);
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid color-mix(in srgb, var(--mg-border, #d8c8b4) 84%, transparent);
  border-radius: 22px;
  background: var(--mg-bg-surface, #fbf7f1);
  color: var(--mg-text-main, #34261f);
  box-shadow: 0 28px 70px rgb(30 22 17 / 0.28);
}

.item-create-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.7rem;
}

.item-create-kicker {
  color: var(--mg-primary, #c97852);
  font-size: 0.68rem;
  font-weight: 800;
}

.item-create-head h3 {
  margin: 0.15rem 0 0;
  font-size: 1rem;
}

.item-create-close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--mg-border-light, #d8c8b4);
  border-radius: 10px;
  background: transparent;
  color: var(--mg-text-muted, #746454);
  font-size: 1.2rem;
  cursor: pointer;
}

.item-create-hint {
  margin: 0;
  color: var(--mg-text-muted, #746454);
  font-size: 0.75rem;
  line-height: 1.7;
}

.item-create-error {
  margin: 0;
  padding: 0.5rem 0.6rem;
  border-radius: 10px;
  color: var(--mg-danger, #a6543f);
  background: color-mix(in srgb, var(--mg-danger, #a6543f) 9%, transparent);
  font-size: 0.75rem;
}

.item-create-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

.item-create-grid label {
  display: grid;
  gap: 0.25rem;
  color: var(--mg-text-muted, #746454);
  font-size: 0.75rem;
}

.item-create-grid .input {
  width: 100%;
  min-height: 40px;
  border: 1px solid var(--mg-border-light, #d8c8b4);
  border-radius: 10px;
  background: var(--mg-bg-surface, #fbf7f1);
  color: var(--mg-text-main, #34261f);
  font: inherit;
}

.item-create-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--mg-border-light, #d8c8b4);
}

@media (max-width: 600px) {
  .item-create-backdrop { align-items: end; padding: 0; }
  .item-create-modal { width: 100%; max-height: 92dvh; overflow-y: auto; border-radius: 22px 22px 0 0; padding: 0.85rem; }
  .item-create-grid { grid-template-columns: 1fr; }
  .item-create-actions { flex-direction: column-reverse; }
  .item-create-actions > button { width: 100%; }
}

.option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-check {
  color: var(--mg-success);
  font-size: 0.8rem;
}

.empty-text {
  margin: 0;
  padding: 0.75rem 0.65rem;
  font-size: 0.76rem;
  color: var(--mg-text-muted);
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
  border-color: var(--mg-border-light);
  background: var(--mg-bg-surface);
  box-shadow: var(--mg-shadow-md);
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
