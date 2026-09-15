<template>
  <section class="smart-data-table">
    <div class="smart-data-table__toolbar">
      <label class="smart-data-table__search">
        <span class="sr-only">جستجو در جدول</span>
        <input v-model.trim="search" class="input" type="search" :placeholder="searchPlaceholder" />
      </label>
      <span class="smart-data-table__count">{{ filteredRows.length.toLocaleString('fa-IR') }} ردیف</span>
    </div>

    <ManagementDataTable
      :columns="columns"
      :rows="filteredRows"
      :row-key="rowKey"
      :row-clickable="rowClickable"
      @row-click="$emit('row-click', $event)"
    >
      <template v-for="column in columns" :key="`smart-col-${column.key}`" #[`cell-${column.key}`]="slotProps">
        <slot :name="`cell-${column.key}`" v-bind="slotProps">
          {{ slotProps.value }}
        </slot>
      </template>

      <template #empty>
        <slot name="empty">داده‌ای برای نمایش وجود ندارد.</slot>
      </template>
    </ManagementDataTable>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import ManagementDataTable from './ManagementDataTable.vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: '' },
  rowClickable: { type: Boolean, default: false },
  searchPlaceholder: { type: String, default: 'جستجو در ردیف‌ها...' },
})

defineEmits(['row-click'])

const search = ref('')
const searchableKeys = computed(() => props.columns.map((column) => column.key).filter(Boolean))
const filteredRows = computed(() => {
  const needle = String(search.value || '').trim().toLocaleLowerCase()
  if (!needle) return props.rows
  return props.rows.filter((row) => searchableKeys.value.some((key) => String(row?.[key] ?? '').toLocaleLowerCase().includes(needle)))
})
</script>

<style scoped>
.smart-data-table {
  display: grid;
  gap: 0.65rem;
}

.smart-data-table__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.smart-data-table__search {
  flex: 1 1 220px;
}

.smart-data-table__count {
  color: var(--mg-text-muted);
  font-size: 0.78rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
