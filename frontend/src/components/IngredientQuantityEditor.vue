<template>
  <div class="section">
    <div class="head">
      <h3>مواد تشکیل دهنده</h3>
      <small>{{ ingredients.length }} مورد</small>
    </div>

    <label class="search-box" v-if="ingredients.length">
      <input type="search" v-model.trim="search" placeholder="جستجوی مواد..." />
    </label>

    <div class="cards" v-if="filteredIngredients.length">
      <div class="ingredient-card" v-for="ingredient in filteredIngredients" :key="ingredient.key || ingredient.name">
        <div class="meta-top">
          <div class="meta">
            <strong>{{ ingredient.customer_label || ingredient.name }}</strong>
            <p>{{ ingredient.base_qty }} {{ ingredient.qty_uom || '' }}</p>
          </div>
          <img v-if="ingredient.image" :src="ingredient.image" :alt="ingredient.customer_label || ingredient.name" />
        </div>

        <div class="meta-bottom" v-if="hasIngredientMeta(ingredient)">
          <small v-if="hasPositiveKcal(ingredient)">{{ formatKcal(ingredient.nutrition_kcal) }} kcal</small>
          <small v-if="Number(ingredient.extra_when_added || 0)">
            +{{ formatMoney(ingredient.extra_when_added, currency) }}
          </small>
        </div>

        <div class="alternative-row" v-if="isReplaceable(ingredient)">
          <small>انتخاب جایگزین</small>
          <div class="alternative-options">
            <button
              type="button"
              class="alt-option-btn"
              :class="{ active: !selectedAlternative(ingredient) }"
              @click="setAlternative(ingredient, '')"
            >
              {{ baseAlternativeLabel(ingredient) }}
            </button>
            <button
              v-for="option in getAlternativeOptions(ingredient)"
              :key="option.alternative_item"
              type="button"
              class="alt-option-btn"
              :class="{ active: selectedAlternative(ingredient) === String(option.alternative_item || '').trim() }"
              @click="setAlternative(ingredient, option.alternative_item)"
            >
              {{ alternativeOptionLabel(ingredient, option) }}
            </button>
          </div>
        </div>

        <div class="actions" v-if="canEditQty(ingredient) || canQuickRemove(ingredient)">
          <template v-if="canEditQty(ingredient)">
            <button class="round-btn" type="button" :disabled="isDecDisabled(ingredient)" @click="decrease(ingredient)">-</button>
            <strong>x{{ getMultiplier(ingredient) }}</strong>
            <button class="round-btn" type="button" :disabled="isIncDisabled(ingredient)" @click="increase(ingredient)">+</button>
          </template>
          <button
            v-if="canQuickRemove(ingredient)"
            class="remove-btn"
            type="button"
            :disabled="getMultiplier(ingredient) <= 0"
            @click="quickRemove(ingredient)"
            title="حذف سریع"
            aria-label="حذف سریع"
          >
            ×
          </button>
        </div>
        <p v-else-if="!isRequired(ingredient)" class="fixed-qty-note">مقدار این آیتم ثابت است.</p>
      </div>
    </div>

    <p class="muted" v-else-if="ingredients.length">ماده‌ای با این جستجو پیدا نشد.</p>
    <p class="muted" v-else>برای این محصول ماده قابل تنظیم تعریف نشده است.</p>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { sanitizeCustomization, getIngredientMultiplier, upsertIngredientMultiplier, ingredientQtyStep } from '@/utils/itemConfig'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  ingredients: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

const emit = defineEmits(['update:modelValue'])

const customization = computed(() => sanitizeCustomization(props.modelValue || {}, props.ingredients || []))
const search = ref('')

const filteredIngredients = computed(() => {
  const query = String(search.value || '').trim().toLowerCase()
  if (!query) {
    return props.ingredients || []
  }

  return (props.ingredients || []).filter((ingredient) => {
    const key = String(ingredient.key || '').toLowerCase()
    const name = String(ingredient.name || '').toLowerCase()
    const label = String(ingredient.customer_label || '').toLowerCase()
    return key.includes(query) || name.includes(query) || label.includes(query)
  })
})

function min(ingredient) {
  return Number(ingredient.min_multiplier ?? 0)
}

function max(ingredient) {
  return Math.max(Number(ingredient.max_multiplier ?? 3), min(ingredient))
}

function getMultiplier(ingredient) {
  return getIngredientMultiplier(customization.value, ingredient)
}

function update(ingredient, nextMultiplier) {
  const next = upsertIngredientMultiplier(customization.value, ingredient, nextMultiplier)
  emit('update:modelValue', sanitizeCustomization(next, props.ingredients || []))
}

function getAlternativeOptions(ingredient) {
  return Array.isArray(ingredient?.alternative_options) ? ingredient.alternative_options : []
}

function isReplaceable(ingredient) {
  return Number(ingredient?.is_replaceable || 0) === 1 && getAlternativeOptions(ingredient).length > 0
}

function selectedAlternative(ingredient) {
  const key = String(ingredient?.key || ingredient?.name || '').trim()
  const row = (customization.value.selected_alternatives || []).find(
    (entry) => String(entry.ingredient_key || '').trim() === key,
  )
  return row ? String(row.alternative_item || '').trim() : ''
}

function setAlternative(ingredient, alternativeItem) {
  const key = String(ingredient?.key || ingredient?.name || '').trim()
  if (!key) {
    return
  }

  const list = Array.isArray(customization.value.selected_alternatives)
    ? [...customization.value.selected_alternatives]
    : []
  const index = list.findIndex((row) => String(row.ingredient_key || '').trim() === key)

  if (!alternativeItem) {
    if (index >= 0) {
      list.splice(index, 1)
    }
  } else {
    const row = { ingredient_key: key, alternative_item: String(alternativeItem || '').trim() }
    if (index >= 0) {
      list[index] = row
    } else {
      list.push(row)
    }
  }

  emit(
    'update:modelValue',
    sanitizeCustomization(
      {
        ...customization.value,
        selected_alternatives: list,
      },
      props.ingredients || [],
    ),
  )
}

function alternativeOptionLabel(ingredient, option) {
  const label = String(option?.item_name || option?.alternative_item || '').trim()
  const baseQty = Number(ingredient?.base_qty || 0)
  const multiplier = Number(option?.qty_multiplier ?? 1)
  const addition = Number(option?.qty_addition || 0)
  const finalQty = baseQty * (Number.isFinite(multiplier) ? multiplier : 1) + (Number.isFinite(addition) ? addition : 0)
  const uom = String(option?.uom || option?.stock_uom || ingredient?.qty_uom || '').trim()

  if (!Number.isFinite(finalQty) || finalQty <= 0 || Math.abs(finalQty - baseQty) < 1e-8) {
    return label
  }
  const qtyText = Number.isInteger(finalQty) ? String(finalQty) : String(finalQty.toFixed(3)).replace(/\.?0+$/, '')
  return `${label} (${qtyText} ${uom})`
}

function baseAlternativeLabel(ingredient = {}) {
  const label = String(ingredient?.customer_label || ingredient?.name || '').trim()
  return label || 'گزینه اصلی'
}

function increase(ingredient) {
  update(ingredient, getMultiplier(ingredient) + multiplierStep(ingredient))
}

function decrease(ingredient) {
  update(ingredient, getMultiplier(ingredient) - multiplierStep(ingredient))
}

function isLocked(ingredient) {
  return Number(ingredient.is_editable_qty) !== 1
}

function isRequired(ingredient) {
  return Number(ingredient?.is_required || 0) === 1
}

function canEditQty(ingredient) {
  return !isLocked(ingredient)
}

function canQuickRemove(ingredient) {
  if (Number(ingredient?.can_remove || 0) !== 1) {
    return false
  }
  if (isRequired(ingredient)) {
    return false
  }
  return min(ingredient) <= 0
}

function quickRemove(ingredient) {
  update(ingredient, 0)
}

function hasPositiveKcal(ingredient) {
  const kcal = Number(ingredient?.nutrition_kcal)
  return Number.isFinite(kcal) && kcal > 0
}

function formatKcal(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return ''
  }
  if (Math.abs(numeric - Math.round(numeric)) < 1e-8) {
    return String(Math.round(numeric))
  }
  return numeric.toFixed(1).replace(/\.0$/, '')
}

function hasIngredientMeta(ingredient) {
  return hasPositiveKcal(ingredient) || Number(ingredient?.extra_when_added || 0) > 0
}

function isDecDisabled(ingredient) {
  if (isLocked(ingredient)) {
    return true
  }
  return getMultiplier(ingredient) <= min(ingredient)
}

function isIncDisabled(ingredient) {
  if (isLocked(ingredient)) {
    return true
  }
  return getMultiplier(ingredient) >= max(ingredient)
}

function multiplierStep(ingredient) {
  const baseQty = Number(ingredient?.base_qty || 0)
  const qtyStep = Number(ingredientQtyStep(ingredient) || 0)
  if (Number.isFinite(baseQty) && baseQty > 0 && Number.isFinite(qtyStep) && qtyStep > 0) {
    const asMultiplier = qtyStep / baseQty
    if (Number.isFinite(asMultiplier) && asMultiplier > 0) {
      return asMultiplier
    }
  }

  const fallback = Number(ingredient?.step_multiplier || 0.5)
  return fallback > 0 ? fallback : 0.5
}
</script>

<style scoped>
.section {
  display: grid;
  gap: 0.72rem;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section h3 {
  margin: 0;
  font-size: 1.05rem;
}

.head small {
  color: var(--text-muted);
}

.search-box input {
  width: 100%;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.26);
  background: rgba(255, 255, 255, 0.66);
  border-radius: 999px;
  padding: 0.62rem 0.82rem;
  font-family: inherit;
  font-size: 0.82rem;
}

.cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

.ingredient-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  padding: 0.65rem;
  display: grid;
  gap: 0.48rem;
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.meta-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.meta-top img {
  width: 44px;
  height: 44px;
  object-fit: cover;
  border-radius: 14px;
  box-shadow: 0 8px 20px rgba(39, 57, 51, 0.2);
}

.meta strong {
  display: block;
  font-size: 0.9rem;
}

.meta p {
  margin: 0.14rem 0 0;
  color: var(--text-muted);
  font-size: 0.72rem;
}

.meta-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.meta-bottom small {
  color: var(--text-muted);
  font-size: 0.7rem;
}

.alternative-row {
  display: grid;
  gap: 0.3rem;
}

.alternative-row small {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.alternative-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.alt-option-btn {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgba(255, 255, 255, 0.76);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.74rem;
  padding: 0.32rem 0.58rem;
  cursor: pointer;
  transition: all 0.18s ease;
}

.alt-option-btn.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  border-color: transparent;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.44rem;
}

.round-btn {
  width: 29px;
  height: 29px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.44);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.12);
  color: var(--accent-gold);
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
}

.round-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.remove-btn {
  width: 29px;
  height: 29px;
  border-radius: 999px;
  border: 1px solid rgb(var(--danger-rgb) / 0.4);
  background: rgb(var(--danger-rgb) / 0.12);
  color: var(--danger);
  font-size: 1.02rem;
  line-height: 1;
  cursor: pointer;
}

.remove-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.fixed-qty-note {
  margin: 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.74rem;
}

@media (min-width: 940px) {
  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
