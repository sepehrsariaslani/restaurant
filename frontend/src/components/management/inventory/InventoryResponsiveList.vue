<template>
  <ManagementCollectionView :model-value="'list'" :show-mode-selector="false">
    <template #list>
      <div class="responsive-list">
        <div class="desktop-list">
          <ManagementListView
            :columns="columns"
            :rows="rows"
            :row-key="rowKey"
            :row-clickable="rowClickable"
            @row-click="$emit('row-click', $event)"
          >
            <template v-for="column in columns" :key="column.key" #[`cell-${column.key}`]="slotProps">
              <slot :name="`cell-${column.key}`" v-bind="slotProps">{{ slotProps.value }}</slot>
            </template>
            <template #empty>
              <slot name="empty">{{ emptyText }}</slot>
            </template>
          </ManagementListView>
        </div>
        <div class="mobile-list">
          <ManagementMobileCardList
            :rows="rows"
            :row-key="rowKey"
            :card-clickable="rowClickable"
            :empty-text="emptyText"
            @card-click="$emit('row-click', $event)"
          >
            <template #card="slotProps">
              <slot name="card" v-bind="slotProps">
                <strong>{{ slotProps.row?.name || '—' }}</strong>
              </slot>
            </template>
          </ManagementMobileCardList>
        </div>
      </div>
    </template>
  </ManagementCollectionView>
</template>

<script setup>
import ManagementCollectionView from '@/components/management/ManagementCollectionView.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementMobileCardList from '@/components/management/ManagementMobileCardList.vue'

defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: 'name' },
  rowClickable: { type: Boolean, default: true },
  emptyText: { type: String, default: 'داده‌ای برای نمایش وجود ندارد.' },
})

defineEmits(['row-click'])
</script>

<style scoped>
.responsive-list {
  min-width: 0;
}

.mobile-list {
  display: none;
}

@media (max-width: 760px) {
  .desktop-list {
    display: none;
  }

  .mobile-list {
    display: block;
  }
}
</style>
