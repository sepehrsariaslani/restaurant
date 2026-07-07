<template>
  <ManagementPageScaffold title="مدیریت مواد اولیه" subtitle="فرمول و دستور ساخت محصولات">
    <template #actions>
      <a class="secondary-btn" href="/management/products">بازگشت به محصولات</a>
    </template>

    <ManagementSurfaceCard tone="accent">
      <p class="hint">
        در این صفحه می‌توانید فرمول ساخت محصولات را تعریف کنید، مواد اولیه و گزینه‌های سفارشی‌سازی را ویرایش کنید.
      </p>
      <p class="hint" v-if="initialItemCode">فیلتر اولیه محصول: {{ initialItemCode }}</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="ویرایشگر فرمول ساخت" subtitle="مواد اولیه و گزینه‌های سفارشی">
      <ManagementBomManager :initial-item-code="initialItemCode" :initial-bom-name="initialBomName" />
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import ManagementBomManager from '@/components/management/ManagementBomManager.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { parseQuery } from '@/utils/format'

const query = parseQuery()

const initialItemCode = computed(() => String(query.item || query.item_name || '').trim())
const initialBomName = computed(() => String(query.bom || '').trim())

onMounted(() => {
  if (!initialBomName.value) {
    return
  }
  const params = new URLSearchParams()
  if (initialItemCode.value) {
    params.set('item', initialItemCode.value)
  }
  params.set('bom', initialBomName.value)
  window.location.replace(`/management/bom?${params.toString()}`)
})
</script>

<style scoped>
.hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
  line-height: 1.75;
}
</style>
