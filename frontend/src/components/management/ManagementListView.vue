<template>
  <ManagementSmartDataTable
    :columns="columns"
    :rows="rows"
    :row-key="rowKey"
    :row-clickable="rowClickable"
    :show-search="false"
    @row-click="$emit('row-click', $event)"
  >
    <template v-for="column in columns" :key="`col-${column.key}`" #[`cell-${column.key}`]="slotProps">
      <slot :name="`cell-${column.key}`" v-bind="slotProps">
        <slot :name="`cell.${column.key}`" v-bind="slotProps">
          {{ slotProps.value }}
        </slot>
      </slot>
    </template>

    <template #empty>
      <slot name="empty">داده‌ای برای نمایش وجود ندارد.</slot>
    </template>
  </ManagementSmartDataTable>
</template>

<script setup>
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'

defineProps({
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

defineEmits(['row-click'])
</script>
