<template>
  <section class="smart-data-table" dir="rtl">
    <header class="smart-data-table__toolbar">
      <label class="smart-data-table__search">
        <span class="sr-only">جستجو در جدول</span>
        <input v-model.trim="search" class="input" type="search" :placeholder="searchPlaceholder" />
      </label>
      <div class="smart-data-table__meta">
        <span>{{ sortedRows.length.toLocaleString('fa-IR') }} ردیف</span>
        <button v-if="hasViewTransform" type="button" class="table-quiet-button" @click="clearTableView">
          پاک‌کردن فیلتر و مرتب‌سازی
        </button>
      </div>
    </header>

    <div v-if="loading" class="table-state" role="status">در حال بارگذاری جدول...</div>
    <div v-else-if="!sortedRows.length" class="table-state"><slot name="empty">{{ emptyText }}</slot></div>

    <div v-else class="smart-data-table__scroll" :style="stickyHeader && maxHeight ? { maxHeight } : undefined">
      <table class="smart-data-table__table">
        <thead :class="{ 'is-sticky': stickyHeader }">
          <tr>
            <th v-if="hasRowControls" class="controls-column">عملیات</th>
            <th
              v-for="column in normalizedColumns"
              :key="column.key"
              class="table-heading"
              :class="[alignClass(column.align), { sortable: column.sortable, frozen: isFrozen(column.key) }]"
              :style="{ ...columnSizeStyle(column), ...stickyStyle(column.key) }"
              @click="toggleSort(column)"
            >
              <div class="table-heading__content">
                <slot :name="`header-${column.key}`" :column="column">
                  <span>{{ column.label }}</span>
                  <span v-if="column.sortable" class="sort-indicator" aria-hidden="true">
                    <span v-if="sortState.key === column.key && sortState.dir === 'asc'">▲</span>
                    <span v-else-if="sortState.key === column.key && sortState.dir === 'desc'">▼</span>
                    <span v-else>↕</span>
                  </span>
                </slot>
                <button
                  v-if="freezable"
                  type="button"
                  class="column-icon-button"
                  :class="{ active: isFrozen(column.key) }"
                  :title="isFrozen(column.key) ? 'برداشتن فریز ستون' : 'فریز ستون'"
                  :aria-label="isFrozen(column.key) ? 'برداشتن فریز ستون' : 'فریز ستون'"
                  @click.stop="toggleFrozen(column.key)"
                >
                  <PinIcon :size="13" aria-hidden="true" />
                </button>
              </div>
              <button
                v-if="resizable"
                type="button"
                class="resize-handle"
                title="تغییر عرض ستون"
                aria-label="تغییر عرض ستون"
                @click.stop
                @dblclick.stop.prevent="resetColumnWidth(column.key)"
                @pointerdown.stop.prevent="startColumnResize($event, column.key)"
              />
            </th>
          </tr>
          <tr v-if="filterable" class="filter-row">
            <th v-if="hasRowControls" class="controls-column" />
            <th
              v-for="column in normalizedColumns"
              :key="`filter-${column.key}`"
              :class="[alignClass(column.align), { frozen: isFrozen(column.key) }]"
              :style="{ ...columnSizeStyle(column), ...stickyStyle(column.key) }"
            >
              <input
                v-model.trim="columnFilters[column.key]"
                type="search"
                class="table-filter-input"
                :placeholder="`فیلتر ${column.label}`"
                @click.stop
              />
            </th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(row, rowIndex) in sortedRows" :key="rowKeyValue(row, rowIndex)">
            <tr
              :class="[rowClassValue(row, rowIndex), { clickable: rowClickable }]"
              :tabindex="rowClickable ? 0 : undefined"
              @click="handleRowClick($event, row)"
              @keydown.enter.prevent="handleRowKeydown(row)"
              @keydown.space.prevent="handleRowKeydown(row)"
            >
              <td v-if="hasRowControls" class="controls-column">
                <div class="row-actions">
                  <button
                    v-if="expandableRows"
                    type="button"
                    class="row-icon-button"
                    :title="isExpanded(row, rowIndex) ? 'بستن جزئیات ردیف' : 'باز کردن جزئیات ردیف'"
                    @click.stop="$emit('row-toggle', { row, rowIndex, rowKey: rowKeyValue(row, rowIndex) })"
                  >
                    {{ isExpanded(row, rowIndex) ? '−' : '+' }}
                  </button>
                  <button
                    v-for="action in visibleRowActions(row)"
                    :key="action.key"
                    type="button"
                    class="row-action-button"
                    :disabled="typeof action.disabled === 'function' ? action.disabled(row) : action.disabled"
                    @click.stop="$emit('row-action', { action, row, rowIndex, rowKey: rowKeyValue(row, rowIndex) })"
                  >
                    {{ action.label }}
                  </button>
                </div>
              </td>
              <td
                v-for="column in normalizedColumns"
                :key="`${rowKeyValue(row, rowIndex)}-${column.key}`"
                class="table-cell"
                :class="[alignClass(column.align), { frozen: isFrozen(column.key) }]"
                :style="{ ...columnSizeStyle(column), ...stickyStyle(column.key), ...frozenCellBackground(row, rowIndex, column.key) }"
              >
                <slot :name="`cell-${column.key}`" :row="row" :column="column" :value="row[column.key]" :row-index="rowIndex">
                  <slot :name="`cell.${column.key}`" :row="row" :column="column" :value="row[column.key]" :row-index="rowIndex">
                    {{ formatCellValue(row[column.key], column) }}
                  </slot>
                </slot>
              </td>
            </tr>
            <tr v-if="$slots['row-detail'] && expandableRows && isExpanded(row, rowIndex)" class="row-detail">
              <td :colspan="normalizedColumns.length + (hasRowControls ? 1 : 0)">
                <slot name="row-detail" :row="row" :row-index="rowIndex" :row-key="rowKeyValue(row, rowIndex)" />
              </td>
            </tr>
          </template>
        </tbody>

        <tfoot v-if="showTotals && totals && Object.keys(totals).length">
          <tr>
            <td v-if="hasRowControls" class="controls-column" />
            <td
              v-for="column in normalizedColumns"
              :key="`total-${column.key}`"
              class="table-total"
              :class="[alignClass(column.align), { frozen: isFrozen(column.key) }]"
              :style="{ ...columnSizeStyle(column), ...stickyStyle(column.key) }"
            >
              <slot :name="`total-${column.key}`" :value="totals[column.key]" :column="column">
                {{ formatCellValue(totals[column.key], column) }}
              </slot>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <slot name="after-table" :rows="sortedRows" />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Pin as PinIcon } from 'lucide-vue-next'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  totals: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: 'داده‌ای برای نمایش وجود ندارد.' },
  searchPlaceholder: { type: String, default: 'جستجو در ردیف‌ها...' },
  defaultSortKey: { type: String, default: '' },
  defaultSortDir: { type: String, default: 'none' },
  rowKey: { type: [String, Function], default: '' },
  rowClass: { type: Function, default: null },
  showTotals: { type: Boolean, default: true },
  freezable: { type: Boolean, default: true },
  resizable: { type: Boolean, default: true },
  frozenStorageKey: { type: String, default: '' },
  columnWidthStorageKey: { type: String, default: '' },
  clickableRows: { type: Boolean, default: false },
  rowClickable: { type: Boolean, default: false },
  expandedRowKeys: { type: Array, default: () => [] },
  expandableRows: { type: Boolean, default: false },
  rowActions: { type: Array, default: () => [] },
  filterable: { type: Boolean, default: false },
  stickyHeader: { type: Boolean, default: false },
  maxHeight: { type: String, default: '' },
})

const emit = defineEmits(['row-click', 'sort-change', 'row-toggle', 'row-action'])

const search = ref('')
const sortState = ref({ key: props.defaultSortKey || '', dir: props.defaultSortDir || 'none' })
const columnFilters = ref({})
const frozenColumns = ref(loadFrozenColumns())
const columnWidths = ref(loadColumnWidths())
const activeColumnResize = ref(null)

const rowClickable = computed(() => props.rowClickable || props.clickableRows)
const hasRowControls = computed(() => props.expandableRows || props.rowActions.length > 0)
const columnWidthKey = computed(() => props.columnWidthStorageKey || (props.frozenStorageKey ? `${props.frozenStorageKey}.widths` : ''))
const normalizedColumns = computed(() => (props.columns || []).map((column) => {
  const key = String(column?.key || '').trim()
  return {
    ...column,
    key,
    label: column?.label || key,
    sortable: column?.sortable !== false,
    align: column?.align || 'right',
    type: inferColumnType(column),
    width: columnWidths.value[key] || column?.width || '10rem',
  }
}).filter((column) => column.key))

const normalizedFrozenColumns = computed(() => normalizeFrozenColumns(frozenColumns.value, normalizedColumns.value))
const filteredRows = computed(() => {
  const needle = normalizeSearchText(search.value)
  const filters = Object.entries(columnFilters.value)
    .map(([key, value]) => [key, normalizeSearchText(value)])
    .filter(([, value]) => value)
  return (props.rows || []).filter((row) => {
    const matchesSearch = !needle || normalizedColumns.value.some((column) => normalizeSearchText(row?.[column.key]).includes(needle))
    const matchesFilters = filters.every(([key, value]) => normalizeSearchText(row?.[key]).includes(value))
    return matchesSearch && matchesFilters
  })
})

const sortedRows = computed(() => {
  const rows = [...filteredRows.value]
  const column = normalizedColumns.value.find((item) => item.key === sortState.value.key)
  if (!column || sortState.value.dir === 'none') return rows
  const factor = sortState.value.dir === 'asc' ? 1 : -1
  return rows.sort((left, right) => compareValues(left?.[column.key], right?.[column.key], column.type) * factor)
})

const hasViewTransform = computed(() => !!normalizeSearchText(search.value) || Object.values(columnFilters.value).some((value) => normalizeSearchText(value)) || sortState.value.dir !== 'none')

watch(normalizedColumns, () => {
  const available = new Set(normalizedColumns.value.map((column) => column.key))
  columnFilters.value = Object.fromEntries(Object.entries(columnFilters.value).filter(([key]) => available.has(key)))
  frozenColumns.value = normalizedFrozenColumns.value
  columnWidths.value = Object.fromEntries(Object.entries(columnWidths.value).filter(([key]) => available.has(key)))
})

watch(frozenColumns, (value) => {
  if (!props.frozenStorageKey || typeof localStorage === 'undefined') return
  try { localStorage.setItem(props.frozenStorageKey, JSON.stringify(normalizeFrozenColumns(value, normalizedColumns.value))) } catch {}
}, { deep: true })

watch(columnWidths, (value) => {
  if (!columnWidthKey.value || typeof localStorage === 'undefined') return
  try { localStorage.setItem(columnWidthKey.value, JSON.stringify(value || {})) } catch {}
}, { deep: true })

function inferColumnType(column = {}) {
  if (column.type && column.type !== 'text') return column.type
  const key = String(column.key || '').toLowerCase()
  if (key === 'date' || key.endsWith('_date') || key.includes('posting_date')) return 'date'
  if (key.endsWith('_time') || key.includes('datetime')) return 'datetime'
  if (['amount', 'total', 'rate', 'price', 'qty', 'quantity', 'count', 'percent'].some((term) => key.includes(term))) return 'number'
  return column.type || 'text'
}

function compareValues(left, right, type) {
  if (['number', 'currency', 'percent', 'numeric'].includes(String(type).toLowerCase())) return toNumber(left) - toNumber(right)
  if (type === 'date' || type === 'datetime') return toTimestamp(left) - toTimestamp(right)
  return String(left ?? '').localeCompare(String(right ?? ''), 'fa')
}

function formatCellValue(value, column = {}) {
  if (value === null || value === undefined || value === '') return '—'
  if (['number', 'currency', 'percent', 'numeric'].includes(String(column.type).toLowerCase()) && Number.isFinite(toNumber(value))) {
    const formatted = toNumber(value).toLocaleString('fa-IR', { maximumFractionDigits: column.decimals ?? 2 })
    return column.type === 'percent' ? `${formatted}٪` : formatted
  }
  return String(value)
}

function toNumber(value) {
  const normalized = normalizeSearchText(value).replace(/[٬,]/g, '')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

function normalizeSearchText(value) {
  return String(value ?? '')
    .replace(/[۰-۹]/g, (digit) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
    .replace(/[٬,]/g, '')
    .trim()
    .toLocaleLowerCase('fa')
}

function toTimestamp(value) {
  if (!value) return 0
  const timestamp = new Date(String(value).replace(' ', 'T').slice(0, 19)).getTime()
  return Number.isFinite(timestamp) ? timestamp : 0
}

function alignClass(align) {
  if (align === 'left') return 'align-left'
  if (align === 'center') return 'align-center'
  return 'align-right'
}

function rowKeyValue(row, index) {
  if (typeof props.rowKey === 'function') return String(props.rowKey(row, index))
  if (props.rowKey && row?.[props.rowKey] !== undefined) return String(row[props.rowKey])
  return String(row?.name ?? row?.id ?? index)
}

function visibleRowActions(row) {
  return props.rowActions.filter((action) => action?.key && action?.label && (typeof action.visible !== 'function' || action.visible(row)))
}

function isExpanded(row, index) {
  return props.expandedRowKeys.includes(rowKeyValue(row, index))
}

function handleRowClick(event, row) {
  if (!rowClickable.value) return
  if (event?.target?.closest?.('a,button,input,select,textarea,label,[role="button"],[data-no-row-click="1"]')) return
  emit('row-click', row)
}

function handleRowKeydown(row) {
  if (rowClickable.value) emit('row-click', row)
}

function rowClassValue(row, index) {
  const explicit = typeof props.rowClass === 'function' ? props.rowClass(row, index) : ''
  return `${index % 2 === 0 ? 'is-even' : 'is-odd'} ${explicit || ''}`.trim()
}

function normalizeFrozenColumns(value, columns) {
  const available = new Set(columns.map((column) => column.key))
  return (Array.isArray(value) ? value : []).filter((key, index, list) => available.has(key) && list.indexOf(key) === index)
}

function toggleFrozen(columnKey) {
  const current = normalizeFrozenColumns(frozenColumns.value, normalizedColumns.value)
  frozenColumns.value = current.includes(columnKey) ? current.filter((key) => key !== columnKey) : [...current, columnKey]
}

function isFrozen(columnKey) {
  return normalizedFrozenColumns.value.includes(columnKey)
}

function columnWidthValue(column) {
  return String(column?.width || '10rem').match(/^(\d+(?:\.\d+)?)(px|rem|em|%)$/) ? String(column.width) : '10rem'
}

function stickyStyle(columnKey) {
  const index = normalizedFrozenColumns.value.indexOf(columnKey)
  if (index < 0) return {}
  const right = normalizedFrozenColumns.value.slice(0, index)
    .map((key) => columnWidthValue(normalizedColumns.value.find((column) => column.key === key)))
  return { right: right.length ? `calc(${right.join(' + ')})` : '0px', zIndex: 4 }
}

function columnSizeStyle(column) {
  const width = columnWidthValue(column)
  return { minWidth: width, width, maxWidth: column.maxWidth || width }
}

function frozenCellBackground(row, index, columnKey) {
  if (!isFrozen(columnKey)) return {}
  return { background: index % 2 === 0 ? 'var(--mg-bg-surface, #fffaf3)' : 'var(--mg-bg-soft, #f6eee4)' }
}

function toggleSort(column) {
  if (!column?.sortable) return
  if (sortState.value.key !== column.key) sortState.value = { key: column.key, dir: 'asc' }
  else if (sortState.value.dir === 'asc') sortState.value = { key: column.key, dir: 'desc' }
  else sortState.value = { key: '', dir: 'none' }
  emit('sort-change', { ...sortState.value })
}

function clearTableView() {
  search.value = ''
  columnFilters.value = {}
  sortState.value = { key: '', dir: 'none' }
}

function loadFrozenColumns() {
  if (!props.frozenStorageKey || typeof localStorage === 'undefined') return []
  try { return JSON.parse(localStorage.getItem(props.frozenStorageKey) || '[]') || [] } catch { return [] }
}

function loadColumnWidths() {
  if (!props.columnWidthStorageKey && !props.frozenStorageKey) return {}
  const key = props.columnWidthStorageKey || `${props.frozenStorageKey}.widths`
  if (typeof localStorage === 'undefined') return {}
  try { return JSON.parse(localStorage.getItem(key) || '{}') || {} } catch { return {} }
}

function startColumnResize(event, columnKey) {
  if (!props.resizable || !columnKey) return
  const headerCell = event.currentTarget?.closest?.('th')
  activeColumnResize.value = { columnKey, startX: event.clientX, startWidth: headerCell?.getBoundingClientRect?.().width || 160 }
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  window.addEventListener('pointermove', resizeColumn)
  window.addEventListener('pointerup', stopColumnResize, { once: true })
  window.addEventListener('pointercancel', stopColumnResize, { once: true })
}

function resizeColumn(event) {
  if (!activeColumnResize.value) return
  const delta = event.clientX - activeColumnResize.value.startX
  const nextWidth = Math.min(520, Math.max(112, activeColumnResize.value.startWidth - delta))
  columnWidths.value = { ...columnWidths.value, [activeColumnResize.value.columnKey]: `${Math.round(nextWidth)}px` }
}

function stopColumnResize() {
  activeColumnResize.value = null
  window.removeEventListener('pointermove', resizeColumn)
  window.removeEventListener('pointerup', stopColumnResize)
  window.removeEventListener('pointercancel', stopColumnResize)
}

function resetColumnWidth(columnKey) {
  const next = { ...columnWidths.value }
  delete next[columnKey]
  columnWidths.value = next
}

onBeforeUnmount(stopColumnResize)
</script>

<style scoped>
.smart-data-table { min-width: 0; display: grid; gap: .65rem; color: var(--mg-text-main, #34261d); }
.smart-data-table__toolbar { display: flex; align-items: center; justify-content: space-between; gap: .65rem; flex-wrap: wrap; }
.smart-data-table__search { min-width: min(100%, 240px); flex: 1 1 280px; }
.smart-data-table__search .input { width: 100%; }
.smart-data-table__meta { display: inline-flex; align-items: center; gap: .55rem; color: var(--mg-text-muted, #7b6b5c); font-size: .75rem; }
.table-quiet-button { border: 0; background: transparent; color: var(--mg-primary, #c8754e); cursor: pointer; font: inherit; font-size: .72rem; }
.table-state { padding: 1.1rem; border: 1px dashed var(--mg-border, #dfcbb8); border-radius: 13px; color: var(--mg-text-muted, #7b6b5c); text-align: center; }
.smart-data-table__scroll { overflow: auto; border: 1px solid var(--mg-border-light, #eadccc); border-radius: 15px; background: var(--mg-bg-surface, #fffaf3); }
.smart-data-table__table { width: 100%; min-width: max-content; border-collapse: separate; border-spacing: 0; }
.smart-data-table__table th, .smart-data-table__table td { border-bottom: 1px solid var(--mg-border-light, #eadccc); padding: .58rem .55rem; white-space: nowrap; }
.smart-data-table__table thead { background: var(--mg-bg-soft, #f6eee4); }
.smart-data-table__table thead.is-sticky { position: sticky; top: 0; z-index: 5; }
.smart-data-table__table tbody tr.is-even { background: var(--mg-bg-surface, #fffaf3); }
.smart-data-table__table tbody tr.is-odd { background: color-mix(in srgb, var(--mg-bg-soft, #f6eee4) 48%, var(--mg-bg-surface, #fffaf3)); }
.smart-data-table__table tbody tr.clickable { cursor: pointer; }
.smart-data-table__table tbody tr.clickable:hover { background: color-mix(in srgb, var(--mg-primary, #c8754e) 8%, var(--mg-bg-surface, #fffaf3)); }
.table-heading { position: relative; color: var(--mg-text-muted, #7b6b5c); font-size: .74rem; font-weight: 800; }
.table-heading.sortable { cursor: pointer; user-select: none; }
.table-heading.frozen, .table-cell.frozen, .table-total.frozen { position: sticky; }
.table-heading__content { display: inline-flex; align-items: center; gap: .3rem; min-height: 1.6rem; }
.sort-indicator { color: var(--mg-primary, #c8754e); font-size: .62rem; }
.column-icon-button, .row-icon-button { display: inline-grid; place-items: center; border: 0; border-radius: 7px; background: transparent; color: var(--mg-text-muted, #7b6b5c); cursor: pointer; }
.column-icon-button { width: 24px; height: 24px; }
.column-icon-button.active { color: var(--mg-primary, #c8754e); background: color-mix(in srgb, var(--mg-primary, #c8754e) 12%, transparent); }
.resize-handle { position: absolute; inset-block: 0; left: 0; width: 7px; border: 0; background: transparent; cursor: col-resize; }
.resize-handle:hover, .resize-handle:focus-visible { background: color-mix(in srgb, var(--mg-primary, #c8754e) 32%, transparent); }
.filter-row th { padding: .35rem .4rem; }
.table-filter-input { width: 100%; min-width: 8rem; min-height: 32px; border: 1px solid var(--mg-border-light, #eadccc); border-radius: 8px; padding: .25rem .4rem; background: var(--mg-bg-surface, #fffaf3); color: inherit; font: inherit; font-size: .7rem; outline: none; }
.table-filter-input:focus { border-color: var(--mg-primary, #c8754e); box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-primary, #c8754e) 14%, transparent); }
.table-cell, .table-total { color: var(--mg-text-main, #34261d); font-size: .78rem; }
.table-total { border-bottom: 0 !important; background: var(--mg-bg-soft, #f6eee4); font-weight: 800; }
.controls-column { width: 1%; min-width: 7rem; text-align: center; }
.row-actions { display: inline-flex; align-items: center; justify-content: center; gap: .25rem; }
.row-action-button { border: 1px solid var(--mg-border-light, #eadccc); border-radius: 8px; padding: .3rem .42rem; background: var(--mg-bg-surface, #fffaf3); color: var(--mg-text-main, #34261d); cursor: pointer; font: inherit; font-size: .68rem; font-weight: 700; }
.row-action-button:hover:not(:disabled) { border-color: var(--mg-primary, #c8754e); color: var(--mg-primary, #c8754e); }
.row-action-button:disabled { cursor: not-allowed; opacity: .5; }
.row-icon-button { width: 26px; height: 26px; border: 1px solid var(--mg-border-light, #eadccc); font-size: 1rem; }
.row-detail td { padding: 0 !important; white-space: normal !important; background: color-mix(in srgb, var(--mg-primary, #c8754e) 5%, var(--mg-bg-surface, #fffaf3)); }
.align-left { text-align: left; }
.align-center { text-align: center; }
.align-right { text-align: right; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@media (max-width: 760px) { .smart-data-table__toolbar { align-items: stretch; } .smart-data-table__meta { justify-content: space-between; } .smart-data-table__table th, .smart-data-table__table td { padding-inline: .42rem; } }
</style>
