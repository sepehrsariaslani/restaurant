<template>
  <div class="product-item-card" :style="{ '--i': index }">
    <div class="item-card-info">
      <h4 class="item-card-name" :title="item.item_name">{{ item.item_name }}</h4>
      <p v-if="item.description" class="item-card-desc">{{ item.description }}</p>
      <div class="item-card-pill">
        <span class="pill-qty">{{ formattedQty }} {{ item.uom }}</span>
        <span v-if="hasPrice" class="pill-price">+{{ formattedPrice }} تومان</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { toPersianDigits } from '@/utils/jalali'

const props = defineProps({
  item: { type: Object, required: true },
  index: { type: Number, default: 0 },
  currency: { type: String, default: 'TOMAN' },
})

const formattedQty = computed(() => {
  const qty = Number(props.item?.qty || 0)
  if (!Number.isFinite(qty)) return toPersianDigits(0)
  const formatted = qty % 1 === 0 ? String(Math.round(qty)) : qty.toFixed(1)
  return toPersianDigits(formatted)
})

const hasPrice = computed(() => {
  const price = Number(props.item?.unit_price || props.item?.price || 0)
  return Number.isFinite(price) && price > 0
})

const formattedPrice = computed(() => {
  const price = Number(props.item?.unit_price || props.item?.price || 0)
  if (!Number.isFinite(price)) return toPersianDigits(0)
  const display = price % 1 === 0 ? String(Math.round(price)) : price.toFixed(0)
  return toPersianDigits(display)
})
</script>

<style scoped>
.product-item-card {
  background: var(--surface, #fff);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.10);
  border-radius: 14px;
  padding: 0.65rem 0.75rem;
  box-shadow: 0 4px 16px rgb(var(--palette-deep-sapphire-rgb) / 0.05);
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
  animation: card-enter 0.35s ease both;
  animation-delay: calc(min(var(--i, 0), 20) * 50ms);
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .product-item-card {
    animation: none;
  }
}

.product-item-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgb(var(--palette-deep-sapphire-rgb) / 0.10);
}

.product-item-card:active {
  transform: scale(0.97);
}

.item-card-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.item-card-name {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--ink-800);
  text-align: start;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-card-desc {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-card-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.10);
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--ink-800);
  width: fit-content;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}

.pill-qty {
  white-space: nowrap;
}

.pill-price {
  white-space: nowrap;
  color: var(--palette-deep-sapphire);
}
</style>
