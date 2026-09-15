<template>
  <section class="editable-table" :class="[`tone-${tone}`]" dir="rtl">
    <header class="table-head">
      <div class="meta">
        <strong>{{ title }}</strong>
        <small v-if="subtitle">{{ subtitle }}</small>
        <span class="row-count">{{ rows.length.toLocaleString('fa-IR') }} ردیف</span>
      </div>
      <div class="head-actions">
        <slot name="toolbar" />
        <button v-if="showColumnSettings" type="button" class="secondary-btn mini" @click="settingsOpen = !settingsOpen">
          {{ settingsOpen ? 'بستن تنظیمات جدول' : 'تنظیمات جدول' }}
        </button>
        <button type="button" class="primary-btn" @click="openAdd" :disabled="disabled || !allowCreate">
          {{ addButtonLabel }}
        </button>
      </div>
    </header>

    <div v-if="settingsOpen" class="column-settings" role="region" aria-label="تنظیمات ستون‌های جدول">
      <div class="column-settings__head">
        <strong>ستون‌های قابل نمایش</strong>
        <button type="button" class="table-quiet-button" @click="resetColumnVisibility">بازنشانی</button>
      </div>
      <label v-for="column in columns" :key="`setting-${column.key}`" class="column-setting">
        <input type="checkbox" :checked="isColumnVisible(column)" @change="toggleColumn(column.key)" />
        <span>{{ column.label }}</span>
      </label>
    </div>

    <ManagementSmartDataTable
      :columns="visibleColumns"
      :rows="rows"
      :row-key="rowKey"
      :row-actions="rowActions"
      :filterable="filterable"
      :loading="loading"
      :empty-text="emptyText"
      :sticky-header="stickyHeader"
      :max-height="maxHeight"
      :frozen-storage-key="`${tableStorageKey()}:frozen`"
      :column-width-storage-key="`${tableStorageKey()}:widths`"
      @row-action="handleRowAction"
    >
      <template v-for="column in visibleColumns" :key="`slot-${column.key}`" #[`cell-${column.key}`]="slotProps">
        <slot :name="`cell-${column.key}`" v-bind="slotProps" :update="(value) => updateCell(slotProps.row, column.key, value)">
          <slot :name="`cell.${column.key}`" v-bind="slotProps" :update="(value) => updateCell(slotProps.row, column.key, value)">
            {{ slotProps.value }}
          </slot>
        </slot>
      </template>

      <template #empty>
        <slot name="empty">{{ emptyText }}</slot>
      </template>
    </ManagementSmartDataTable>

    <ManagementPopup v-model:open="editorOpen" :title="popupTitle" :subtitle="popupSubtitle">
      <p v-if="editorError" class="error">{{ editorError }}</p>
      <slot name="editor" :draft="draft" :mode="editorMode" />

      <template #footer>
        <div class="foot-actions">
          <button type="button" class="secondary-btn" @click="editorOpen = false">انصراف</button>
          <button type="button" class="primary-btn" @click="saveDraft" :disabled="disabled">
            {{ saveButtonLabel }}
          </button>
        </div>
      </template>
    </ManagementPopup>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: 'name' },
  title: { type: String, default: 'جدول' },
  subtitle: { type: String, default: '' },
  tone: { type: String, default: 'default' },
  addButtonLabel: { type: String, default: 'افزودن آیتم' },
  editButtonLabel: { type: String, default: 'ویرایش' },
  deleteButtonLabel: { type: String, default: 'حذف' },
  saveButtonLabel: { type: String, default: 'ذخیره' },
  emptyText: { type: String, default: 'داده‌ای برای نمایش وجود ندارد.' },
  popupTitleAdd: { type: String, default: 'افزودن آیتم' },
  popupTitleEdit: { type: String, default: 'ویرایش آیتم' },
  popupSubtitle: { type: String, default: 'اطلاعات را تکمیل کنید.' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  allowCreate: { type: Boolean, default: true },
  allowEdit: { type: Boolean, default: true },
  allowDelete: { type: Boolean, default: true },
  createEmptyRow: { type: Function, default: () => ({}) },
  normalizeRow: { type: Function, default: (row) => row },
  validateRow: { type: Function, default: () => '' },
  storageKey: { type: String, default: '' },
  showColumnSettings: { type: Boolean, default: true },
  filterable: { type: Boolean, default: true },
  stickyHeader: { type: Boolean, default: false },
  maxHeight: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'row-update', 'row-delete', 'row-add'])

const rows = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))
const settingsOpen = ref(false)
const columnVisibility = ref(loadColumnVisibility())
const editorOpen = ref(false)
const editorMode = ref('add')
const editorIndex = ref(-1)
const editorError = ref('')
const draft = reactive({})

const visibleColumns = computed(() => props.columns.filter((column) => column?.key && isColumnVisible(column)))
const popupTitle = computed(() => (editorMode.value === 'edit' ? props.popupTitleEdit : props.popupTitleAdd))
const rowActions = computed(() => [
  ...(props.allowEdit ? [{ key: 'edit', label: props.editButtonLabel, visible: () => !props.disabled }] : []),
  ...(props.allowDelete ? [{ key: 'delete', label: props.deleteButtonLabel, visible: () => !props.disabled, disabled: () => props.disabled }] : []),
])

function tableStorageKey() {
  return props.storageKey || `restaurant:editable-table:${props.title || 'table'}`
}

function loadColumnVisibility() {
  if (typeof localStorage === 'undefined') return {}
  try {
    const parsed = JSON.parse(localStorage.getItem(`${tableStorageKey()}:columns`) || '{}')
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch { return {} }
}

function persistColumnVisibility() {
  if (typeof localStorage === 'undefined') return
  try { localStorage.setItem(`${tableStorageKey()}:columns`, JSON.stringify(columnVisibility.value)) } catch {}
}

function isColumnVisible(column) {
  return column?.hidden !== true && columnVisibility.value[column.key] !== false
}

function toggleColumn(key) {
  const currentlyVisible = columnVisibility.value[key] !== false
  const visibleCount = visibleColumns.value.length
  if (currentlyVisible && visibleCount <= 1) return
  columnVisibility.value = { ...columnVisibility.value, [key]: !currentlyVisible }
  persistColumnVisibility()
}

function resetColumnVisibility() {
  columnVisibility.value = {}
  persistColumnVisibility()
}

function resolveRowKey(row, rowIndex) {
  if (typeof props.rowKey === 'function') return props.rowKey(row, rowIndex)
  if (typeof props.rowKey === 'string' && props.rowKey) return row?.[props.rowKey] ?? rowIndex
  return row?.name || row?.id || rowIndex
}

function rowIndexFor(row) {
  const rowKey = String(resolveRowKey(row, 0))
  const byKey = rows.value.findIndex((candidate, index) => String(resolveRowKey(candidate, index)) === rowKey)
  return byKey >= 0 ? byKey : rows.value.indexOf(row)
}

function cloneValue(value) {
  if (typeof structuredClone === 'function') {
    try { return structuredClone(value) } catch {}
  }
  try { return JSON.parse(JSON.stringify(value || {})) } catch { return {} }
}

function writeDraft(payload) {
  for (const key of Object.keys(draft)) delete draft[key]
  Object.assign(draft, cloneValue(payload && typeof payload === 'object' ? payload : {}))
}

function openAdd() {
  editorMode.value = 'add'
  editorIndex.value = -1
  editorError.value = ''
  const baseRow = cloneValue(props.createEmptyRow())
  const normalized = props.normalizeRow(cloneValue(baseRow)) || baseRow
  writeDraft({ ...baseRow, ...normalized })
  editorOpen.value = true
}

function openEdit(row) {
  editorMode.value = 'edit'
  editorIndex.value = rowIndexFor(row)
  editorError.value = ''
  const rawRow = cloneValue(row)
  const normalized = props.normalizeRow(cloneValue(rawRow)) || rawRow
  writeDraft({ ...cloneValue(props.createEmptyRow()), ...rawRow, ...normalized })
  editorOpen.value = true
}

function handleRowAction({ action, row }) {
  if (action?.key === 'edit') openEdit(row)
  if (action?.key === 'delete') removeRow(row)
}

function updateCell(row, key, value) {
  const index = rowIndexFor(row)
  if (index < 0) return
  const next = rows.value.map((candidate, candidateIndex) => candidateIndex === index ? { ...candidate, [key]: value } : candidate)
  emit('update:modelValue', next)
  emit('row-update', { row: next[index], index, key, value })
}

function removeRow(row) {
  const index = rowIndexFor(row)
  if (index < 0) return
  const next = [...rows.value]
  const [removed] = next.splice(index, 1)
  emit('update:modelValue', next)
  emit('row-delete', { row: removed, index })
}

function saveDraft() {
  const validationMessage = String(props.validateRow(draft) || '').trim()
  if (validationMessage) {
    editorError.value = validationMessage
    return
  }
  const normalized = props.normalizeRow(cloneValue(draft)) || cloneValue(draft)
  const next = [...rows.value]
  if (editorMode.value === 'edit' && editorIndex.value >= 0) {
    next.splice(editorIndex.value, 1, normalized)
    emit('row-update', { row: normalized, index: editorIndex.value })
  } else {
    next.push(normalized)
    emit('row-add', { row: normalized, index: next.length - 1 })
  }
  emit('update:modelValue', next)
  editorOpen.value = false
}
</script>

<style scoped>
.editable-table { display: grid; gap: .62rem; min-width: 0; border: 1px solid var(--mg-border-light, #eadccc); border-radius: 16px; padding: .62rem; background: var(--mg-bg-surface, #fffaf3); box-shadow: var(--shadow-sm, 0 8px 22px rgb(15 23 42 / .045)); }
.editable-table.tone-accent { border-color: color-mix(in srgb, var(--mg-primary, #c8754e) 28%, var(--mg-border-light, #eadccc)); background: linear-gradient(180deg, var(--mg-bg-surface, #fffaf3), color-mix(in srgb, var(--mg-bg-surface, #fffaf3) 88%, var(--mg-primary, #c8754e))); }
.table-head { display: flex; align-items: flex-start; justify-content: space-between; gap: .65rem; }
.meta { display: grid; gap: .12rem; min-width: 0; }
.meta strong { font-size: .88rem; }
.meta small { color: var(--mg-text-muted, #7b6b5c); font-size: .76rem; line-height: 1.7; }
.row-count { color: var(--mg-text-muted, #7b6b5c); font-size: .7rem; }
.head-actions { display: inline-flex; flex-wrap: wrap; gap: .35rem; align-items: center; justify-content: flex-end; }
.mini { padding: .3rem .48rem; font-size: .7rem; }
.column-settings { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem .65rem; padding: .55rem .62rem; border: 1px dashed var(--mg-border, #dfcbb8); border-radius: 11px; background: var(--mg-bg-soft, #f6eee4); }
.column-settings__head { display: inline-flex; align-items: center; gap: .45rem; width: 100%; color: var(--mg-text-muted, #7b6b5c); font-size: .74rem; }
.column-setting { display: inline-flex; align-items: center; gap: .3rem; color: var(--mg-text-main, #34261d); font-size: .74rem; cursor: pointer; }
.column-setting input { accent-color: var(--mg-primary, #c8754e); }
.table-quiet-button { border: 0; background: transparent; color: var(--mg-primary, #c8754e); cursor: pointer; font: inherit; font-size: .7rem; }
.foot-actions { display: flex; align-items: center; justify-content: flex-end; gap: .4rem; }
.error { margin: 0; color: var(--mg-danger, #b34336); font-size: .78rem; }
@media (max-width: 760px) { .table-head { display: grid; } .head-actions { display: grid; grid-template-columns: minmax(0, 1fr); } .head-actions > * { width: 100%; } }
</style>
