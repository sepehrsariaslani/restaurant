<template>
  <ManagementSmartDataTable
    :columns="columns"
    :rows="rows"
    :row-key="rowKey"
    :row-clickable="rowClickable"
    :row-actions="rowActions"
    :loading="loading"
    :empty-text="emptyText"
    :show-search="showSearch"
    :show-count="showCount"
    :filterable="filterable"
    :sticky-header="stickyHeader"
    :max-height="maxHeight"
    @row-click="$emit('row-click', $event)"
    @sort-change="$emit('sort-change', $event)"
    @row-toggle="$emit('row-toggle', $event)"
    @row-action="$emit('row-action', $event)"
  >
    <template v-for="column in columns" :key="`col-${column.key}`" #[`cell-${column.key}`]="slotProps">
      <slot :name="`cell-${column.key}`" v-bind="slotProps">
        <slot :name="`cell.${column.key}`" v-bind="slotProps">
          {{ slotProps.value }}
        </slot>
      </slot>
    </template>

    <template #empty>
      <slot name="empty">{{ emptyText }}</slot>
    </template>
    <template #after-table="slotProps"><slot name="after-table" v-bind="slotProps" /></template>
  </ManagementSmartDataTable>
</template>

<script setup>
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'

defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: '' },
  rowClickable: { type: Boolean, default: false },
  rowActions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: 'داده‌ای برای نمایش وجود ندارد.' },
  showSearch: { type: Boolean, default: false },
  showCount: { type: Boolean, default: true },
  filterable: { type: Boolean, default: false },
  stickyHeader: { type: Boolean, default: false },
  maxHeight: { type: String, default: '' },
})

defineEmits(['row-click', 'sort-change', 'row-toggle', 'row-action'])
</script>
