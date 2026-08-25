<template>
  <button
    type="button"
    class="option-card"
    :class="{
      selected,
      disabled,
      'mode-single': selectionMode === 'single',
      'mode-multi': selectionMode === 'multi',
    }"
    :aria-pressed="selected"
    :disabled="disabled"
    @click="$emit('select', option)"
  >
    <div class="option-card__image-wrap">
      <img
        v-if="option.image"
        :src="option.image"
        :alt="option.option_label"
        class="option-card__image"
        loading="lazy"
      />
      <div v-else class="option-card__image option-card__image--placeholder">
        <span>🍽️</span>
      </div>

      <!-- Color swatch -->
      <span
        v-if="option.color_code"
        class="option-card__swatch"
        :style="{ backgroundColor: option.color_code }"
      />

      <!-- Selection indicator -->
      <div class="option-card__indicator" v-if="selected">
        <svg
          v-if="selectionMode === 'single'"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <span v-else class="checkbox-mark">✓</span>
      </div>
    </div>

    <div class="option-card__body">
      <h4 class="option-card__name">{{ option.option_label }}</h4>
      <p v-if="option.option_description" class="option-card__desc muted">
        {{ option.option_description }}
      </p>

      <div class="option-card__meta">
        <span v-if="Number(option.price_delta) > 0" class="option-card__price">
          +{{ formatMoney(option.price_delta, currency) }}
        </span>

        <!-- Allergen warning -->
        <span
          v-if="showAllergens && option.allergens && option.allergens.length"
          class="option-card__allergen"
          :title="`آلرژن‌ها: ${option.allergens.join('، ')}`"
        >
          ⚠️
        </span>
      </div>
    </div>
  </button>
</template>

<script setup>
import { formatMoney } from '@/utils/format'

defineProps({
  option: { type: Object, required: true },
  selectionMode: { type: String, default: 'single' },
  selected: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  showAllergens: { type: Boolean, default: true },
  currency: { type: String, default: 'TOMAN' },
})

defineEmits(['select'])
</script>

<style scoped>
.option-card {
  position: relative;
  text-align: right;
  background: #fff;
  border: 1.5px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  display: flex;
  flex-direction: column;
  padding: 0;
  width: 100%;
  font-family: inherit;
}

.option-card:hover:not(.disabled) {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.5);
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.option-card.selected {
  border-color: var(--accent-gold, #c8963e);
  box-shadow: 0 0 0 2px rgb(var(--palette-deep-saffron-rgb) / 0.2), 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.option-card.disabled {
  opacity: 0.4;
  pointer-events: none;
}

.option-card__image-wrap {
  position: relative;
  height: 120px;
  overflow: hidden;
  background: rgb(var(--palette-eggshell-rgb) / 0.5);
}

.option-card__image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  transition: transform 0.3s ease;
}

.option-card:hover:not(.disabled) .option-card__image {
  transform: scale(1.04);
}

.option-card__image--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.option-card__swatch {
  position: absolute;
  bottom: 0.5rem;
  left: 0.5rem;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.option-card__indicator {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-gold, #c8963e);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.checkbox-mark {
  font-size: 0.75rem;
  line-height: 1;
}

.option-card__body {
  padding: 0.65rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}

.option-card__name {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
  line-height: 1.3;
}

.option-card__desc {
  font-size: 0.72rem;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.option-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  gap: 0.25rem;
}

.option-card__price {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--accent-gold, #c8963e);
  font-variant-numeric: tabular-nums;
}

.option-card__allergen {
  font-size: 0.85rem;
  cursor: help;
  flex-shrink: 0;
}

.muted {
  color: var(--text-muted, #7a6e64);
}

@media (min-width: 920px) {
  .option-card__image-wrap {
    height: 140px;
  }
  .option-card__name {
    font-size: 0.95rem;
  }
}
</style>
