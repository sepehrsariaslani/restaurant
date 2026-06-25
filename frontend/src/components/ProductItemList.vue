<template>
  <div class="product-item-list">
    <!-- Grid layout (v1 default) -->
    <div class="item-grid" :style="{ '--item-count': items.length }">
      <ProductItemCard
        v-for="(item, idx) in items"
        :key="item.item_code"
        :item="item"
        :index="idx"
        :currency="currency"
      />
    </div>
  </div>
</template>

<script setup>
import ProductItemCard from './ProductItemCard.vue'

defineProps({
  items: { type: Array, required: true },
  currency: { type: String, default: 'TOMAN' },
})

defineEmits(['item-tap'])
</script>

<style scoped>
.product-item-list {
  padding: 0 0.75rem;
}

@media (min-width: 768px) {
  .product-item-list {
    padding: 0 1rem;
  }
}

.item-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
