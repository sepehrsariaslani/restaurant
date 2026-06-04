<template>
  <ManagementPageScaffold :title="pageTitle" :subtitle="pageSubtitle">
    <template #actions>
      <a class="secondary-btn" :href="backUrl">بازگشت به لیست BOMها</a>
    </template>

    <ManagementSurfaceCard tone="accent">
      <p class="hint" v-if="initialBomName">
        در حال ویرایش BOM: <strong>{{ initialBomName }}</strong>
      </p>
      <p class="hint" v-else>
        در حال ایجاد BOM جدید هستید.
      </p>
      <p class="hint" v-if="initialItemCode">محصول انتخاب‌شده: {{ initialItemCode }}</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="جزئیات BOM" subtitle="ویرایش کامل فرمول، آیتم‌ها و Modifier ها">
      <ManagementBomManager :detail-only="true" :initial-item-code="initialItemCode" :initial-bom-name="initialBomName" />
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed } from 'vue'
import ManagementBomManager from '@/components/management/ManagementBomManager.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { parseQuery } from '@/utils/format'

const query = parseQuery()

const initialItemCode = computed(() => String(query.item || query.item_name || '').trim())
const initialBomName = computed(() => String(query.bom || '').trim())

const pageTitle = computed(() => (initialBomName.value ? `جزئیات ${initialBomName.value}` : 'ایجاد BOM جدید'))
const pageSubtitle = computed(() => initialItemCode.value || '')

const backUrl = computed(() => {
  if (!initialItemCode.value) {
    return '/desk/boms'
  }
  const params = new URLSearchParams({ item: initialItemCode.value })
  return `/desk/boms?${params.toString()}`
})
</script>

<style scoped>
.hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.hint + .hint {
  margin-top: 0.25rem;
}
</style>
