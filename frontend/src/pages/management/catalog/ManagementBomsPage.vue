<template>
  <ManagementBomManager :initial-item-code="initialItemCode" :initial-bom-name="initialBomName" />
</template>

<script setup>
import { computed, onMounted } from 'vue'
import ManagementBomManager from '@/components/management/catalog/ManagementBomManager.vue'
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
