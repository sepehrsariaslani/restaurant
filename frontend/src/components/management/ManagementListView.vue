<template>
  <ManagementDataTable
    :columns="columns"
    :rows="rows"
    :row-key="rowKey"
    :row-clickable="rowClickable"
    @row-click="$emit('row-click', $event)"
  >
    <template v-for="column in columns" :key="`col-${column.key}`" #[`cell-${column.key}`]="slotProps">
      <slot :name="`cell-${column.key}`" v-bind="slotProps">
        {{ slotProps.value }}
      </slot>
    </template>

    <template #empty>
      <slot name="empty">داده‌ای برای نمایش وجود ندارد.</slot>
    </template>
  </ManagementDataTable>
</template>

<script setup>
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'

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
