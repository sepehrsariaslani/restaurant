<template>
  <section class="blk products" dir="rtl" v-if="items.length">
    <div class="blk__head">
      <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
      <h2 class="blk__title">{{ title }}</h2>
      <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
    </div>

    <!-- GRID -->
    <div v-if="variant === 'grid'" class="products-grid">
      <MenuItemCard
        v-for="(item, idx) in items"
        :key="item.slug || item.item_code || idx"
        :item="item"
        :card-variant="cardVariant"
        :currency="currency"
        @quick-add="$emit('quick-add', item)"
      />
    </div>

    <!-- RAIL -->
    <div v-else-if="variant === 'rail'" class="products-rail">
      <div
        v-for="(item, idx) in items"
        :key="item.slug || item.item_code || idx"
        class="products-rail__item"
      >
        <MenuItemCard
          :item="item"
          :card-variant="cardVariant"
          :currency="currency"
          @quick-add="$emit('quick-add', item)"
        />
      </div>
    </div>

    <!-- SPOTLIGHT -->
    <div v-else class="products-spotlight">
      <div class="products-spotlight__main">
        <MenuItemCard
          :item="items[0]"
          :card-variant="cardVariant"
          :currency="currency"
          @quick-add="$emit('quick-add', items[0])"
        />
      </div>
      <div class="products-spotlight__side">
        <MenuItemCard
          v-for="(item, idx) in items.slice(1, 5)"
          :key="item.slug || item.item_code || idx"
          :item="item"
          :card-variant="cardVariant"
          :currency="currency"
          @quick-add="$emit('quick-add', item)"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import MenuItemCard from '@/components/MenuItemCard.vue'
import '@/components/blocks/blocks.css'

defineProps({
  variant: { type: String, default: 'grid' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  cardVariant: { type: String, default: 'classic' },
  currency: { type: String, default: 'IRR' },
})

defineEmits(['quick-add'])
</script>

<style scoped>
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--blk-gap);
  align-items: stretch;
}

.products-rail {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: min(70%, 260px);
  gap: var(--blk-gap);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding-bottom: 0.5rem;
  scrollbar-width: none;
}

.products-rail::-webkit-scrollbar {
  display: none;
}

.products-rail__item {
  scroll-snap-align: start;
}

.products-spotlight {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: var(--blk-gap);
  align-items: stretch;
}

.products-spotlight__side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--blk-gap);
}

@media (max-width: 800px) {
  .products-spotlight {
    grid-template-columns: 1fr;
  }
}
</style>
