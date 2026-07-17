<template>
  <div class="table-shell">
    <table class="table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!rows.length">
          <td :colspan="columns.length" class="empty-row">
            <slot name="empty">داده‌ای برای نمایش وجود ندارد.</slot>
          </td>
        </tr>
        <tr
          v-for="(row, rowIndex) in rows"
          :key="resolveRowKey(row, rowIndex)"
          :class="{ clickable: rowClickable }"
          :tabindex="rowClickable ? 0 : undefined"
          @click="handleRowClick($event, row)"
          @keydown.enter.prevent="handleRowKeydown(row)"
          @keydown.space.prevent="handleRowKeydown(row)"
        >
          <td v-for="column in columns" :key="`${resolveRowKey(row, rowIndex)}-${column.key}`">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]" :row-index="rowIndex">
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  columns: {
    type: Array,
    default: () => [],
  },
  rows: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: [String, Function],
    default: '',
  },
  rowClickable: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['row-click'])

function resolveRowKey(row, rowIndex) {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row, rowIndex)
  }
  if (typeof props.rowKey === 'string' && props.rowKey) {
    return row?.[props.rowKey] ?? rowIndex
  }
  return row?.name || row?.id || rowIndex
}

function handleRowClick(event, row) {
  if (!props.rowClickable) {
    return
  }
  const target = event?.target
  if (target?.closest?.('a, button, input, select, textarea, label, [role="button"], [data-no-row-click="1"]')) {
    return
  }
  emit('row-click', row)
}

function handleRowKeydown(row) {
  if (!props.rowClickable) {
    return
  }
  emit('row-click', row)
}
</script>

<style scoped>
.table-shell {
  overflow-x: auto;
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 16px;
  background: var(--bg-card, #fff);
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  text-align: right;
  padding: 0.5rem 0.45rem;
  border-bottom: 1px solid var(--border, var(--mg-border-light));
  font-size: 0.81rem;
  white-space: nowrap;
}

.table tbody tr.clickable {
  cursor: pointer;
}

.table tbody tr.clickable:hover {
  background: var(--module-50, rgb(139 94 52 / 0.075));
}

.table th {
  font-size: 0.78rem;
  color: var(--muted, var(--text-muted));
  background: var(--bg-soft, var(--mg-bg-page));
}

.empty-row {
  text-align: center;
  color: var(--muted, var(--text-muted));
  white-space: normal;
}
</style>
