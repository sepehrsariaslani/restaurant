<template>
  <div class="review-step">
    <h3 class="review-step__title">خلاصه سفارش شما</h3>

    <!-- Product header -->
    <div class="review-step__product" v-if="template">
      <strong>{{ template.title || template.name }}</strong>
      <span class="review-step__base-price muted">
        قیمت پایه: {{ formatMoney(basePrice, currency) }}
      </span>
    </div>

    <!-- Per-step selections -->
    <div
      v-for="(step, stepIdx) in template?.steps || []"
      :key="step.step_key"
      class="review-step__section"
    >
      <button
        type="button"
        class="review-step__section-header"
        @click="$emit('edit-step', stepIdx)"
      >
        <h4>{{ step.step_title }}</h4>
        <span class="review-step__edit-hint muted">ویرایش ←</span>
      </button>

      <div class="review-step__options">
        <div
          v-for="sel in getStepSelections(step.step_key)"
          :key="sel.option_key"
          class="review-step__option-row"
        >
          <span class="review-step__option-name">
            {{ getOptionLabel(step, sel.option_key) }}
          </span>
          <span class="review-step__option-price muted">
            {{ formatDelta(getOptionDelta(step, sel.option_key)) }}
          </span>
        </div>
        <p v-if="!getStepSelections(step.step_key).length" class="review-step__empty muted">
          انتخابی نشده
        </p>
      </div>

      <!-- Allergen summary for step -->
      <p
        v-if="getStepAllergens(step).length"
        class="review-step__allergens"
      >
        ⚠️ آلرژن‌ها: {{ getStepAllergens(step).join('، ') }}
      </p>
    </div>

    <!-- Divider -->
    <hr class="review-step__divider" />

    <!-- Total -->
    <div class="review-step__total">
      <span>جمع کل</span>
      <strong class="review-step__total-price">{{ formatMoney(totalPrice, currency) }}</strong>
    </div>

    <!-- Error message -->
    <p v-if="submitError" class="review-step__error">
      {{ submitError }}
    </p>

    <!-- Submit button -->
    <button
      type="button"
      class="review-step__submit"
      :disabled="isSubmitting"
      @click="$emit('submit')"
    >
      <span v-if="isSubmitting" class="review-step__spinner" />
      <span v-else>
        افزودن به سبد — {{ formatMoney(totalPrice, currency) }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { formatMoney } from '@/utils/format'

const props = defineProps({
  template: { type: Object, default: null },
  selections: { type: Object, default: () => ({}) },
  totalPrice: { type: Number, default: 0 },
  basePrice: { type: Number, default: 0 },
  currency: { type: String, default: 'TOMAN' },
  isSubmitting: { type: Boolean, default: false },
  submitError: { type: String, default: '' },
})

defineEmits(['submit', 'edit-step'])

function getStepSelections(stepKey) {
  return props.selections[stepKey] || []
}

function getOptionLabel(step, optionKey) {
  const opt = step.options?.find(o => o.option_key === optionKey)
  return opt?.option_label || optionKey
}

function getOptionDelta(step, optionKey) {
  const opt = step.options?.find(o => o.option_key === optionKey)
  return Number(opt?.price_delta) || 0
}

function formatDelta(delta) {
  if (!delta) return ''
  return `+${formatMoney(delta, props.currency)}`
}

function getStepAllergens(step) {
  const allergens = new Set()
  const sels = getStepSelections(step.step_key)
  for (const sel of sels) {
    const opt = step.options?.find(o => o.option_key === sel.option_key)
    if (opt?.allergens) {
      for (const a of opt.allergens) allergens.add(a)
    }
  }
  return [...allergens]
}
</script>

<style scoped>
.review-step {
  padding: 0.75rem 1rem 1.5rem;
}

.review-step__title {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
}

.review-step__product {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.12);
}

.review-step__base-price {
  font-size: 0.82rem;
}

.review-step__section {
  margin-bottom: 0.75rem;
}

.review-step__section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  background: none;
  border: none;
  padding: 0.4rem 0;
  cursor: pointer;
  font-family: inherit;
}

.review-step__section-header h4 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink-800, #1e1a17);
}

.review-step__edit-hint {
  font-size: 0.72rem;
}

.review-step__options {
  padding-right: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.review-step__option-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.review-step__option-name {
  font-size: 0.82rem;
  color: var(--ink-700, #2e2820);
}

.review-step__option-price {
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--accent-gold, #c8963e);
  flex-shrink: 0;
}

.review-step__empty {
  font-size: 0.75rem;
  font-style: italic;
  margin: 0;
}

.review-step__allergens {
  font-size: 0.7rem;
  color: #b06000;
  margin: 0.25rem 0 0;
  font-weight: 600;
}

.review-step__divider {
  border: none;
  border-top: 1.5px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  margin: 0.65rem 0;
}

.review-step__total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.review-step__total-price {
  font-size: 1.2rem;
  color: var(--ink-900, #141210);
  font-variant-numeric: tabular-nums;
}

.review-step__error {
  margin: 0 0 0.65rem;
  font-size: 0.8rem;
  color: #d93025;
  text-align: center;
  font-weight: 600;
}

.review-step__submit {
  width: 100%;
  border: none;
  border-radius: 16px;
  background: var(--ink-800, #1e1a17);
  color: #fff;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 700;
  padding: 0.85rem 1.5rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 12px 28px rgba(20, 15, 8, 0.25);
}

.review-step__submit:hover:not(:disabled) {
  background: var(--ink-900, #141210);
  transform: translateY(-1px);
}

.review-step__submit:disabled {
  opacity: 0.6;
  pointer-events: none;
}

.review-step__spinner {
  width: 22px;
  height: 22px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.muted {
  color: var(--text-muted, #7a6e64);
}

@media (min-width: 920px) {
  .review-step {
    padding: 0.75rem 1.5rem 2rem;
  }
  .review-step__title {
    font-size: 1.25rem;
  }
}
</style>
