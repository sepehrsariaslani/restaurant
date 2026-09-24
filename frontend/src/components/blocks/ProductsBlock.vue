<template>
  <section class="blk products" dir="rtl" v-if="items.length">
    <div class="blk__head">
      <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
      <h2 class="blk__title">{{ title }}</h2>
      <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
    </div>

    <!-- GRID -->
    <div v-if="variant === 'grid'" class="products-grid" :class="{ 'products-grid--single': items.length === 1 && cardVariant === 'classic' }">
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

.products-grid--single {
  grid-template-columns: minmax(0, 1fr);
}

.products-grid--single :deep(.menu-card--classic) {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  min-height: 250px;
}

.products-grid--single :deep(.classic-img-wrap) {
  height: 100%;
  min-height: 250px;
}

.products-grid--single :deep(.classic-img) {
  object-fit: cover;
}

.products-grid--single :deep(.classic-body) {
  padding: clamp(1rem, 3vw, 1.75rem);
}

.products-grid--single :deep(.classic-title) {
  font-size: clamp(1.2rem, 2.3vw, 1.6rem);
}

.products-grid--single :deep(.classic-add) {
  width: 44px;
  height: 44px;
  font-size: 1.35rem;
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
  .products-grid--single :deep(.menu-card--classic) {
    grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
    min-height: 210px;
  }

  .products-grid--single :deep(.classic-img-wrap) {
    min-height: 210px;
  }

  .products-spotlight {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .products-grid--single :deep(.menu-card--classic) {
    display: flex;
    min-height: 0;
  }

  .products-grid--single :deep(.classic-img-wrap) {
    height: auto;
    min-height: 0;
    aspect-ratio: 16 / 9;
  }
}
</style>
