<template>
  <teleport to="body">
    <div class="sheet-overlay" v-if="open" @click.self="$emit('close')">
      <section class="sheet-panel">
        <header class="sheet-head">
          <button class="icon-btn" type="button" @click="$emit('close')">&#x2039;</button>
          <p>افزودن به سبد</p>
          <button class="icon-btn" type="button" @click="$emit('close')">×</button>
        </header>

        <div class="hero" v-if="selectedItem">
          <img :src="selectedItemImage" :alt="selectedItem.title" />
          <div>
            <h3>{{ selectedItem.title }}</h3>
            <p class="muted">قبل از افزودن، افزودنی‌ها را انتخاب کن</p>
          </div>
        </div>

        <p class="muted" v-if="loading">در حال بارگذاری تنظیمات آیتم...</p>
        <p class="error" v-else-if="error">{{ error }}</p>

        <div class="content" v-else-if="selectedItem">
          <div class="qty-row">
            <small>تعداد</small>
            <div class="qty-actions">
              <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
              <strong>{{ qty }}</strong>
              <button class="qty-btn" type="button" @click="qty += 1">+</button>
            </div>
          </div>

          <IngredientQuantityEditor
            v-if="ingredients.length"
            :ingredients="ingredients"
            :currency="currency"
            :model-value="customization"
            @update:model-value="setCustomization"
          />

          <ModifierRecipeImpactSelector
            v-if="modifierGroups.length"
            :groups="modifierGroups"
            :currency="currency"
            :model-value="customization.selected_modifiers"
            @update:model-value="setSelectedModifiers"
          />
          <p class="error" v-if="selectionError">{{ selectionError }}</p>

          <p class="hint" v-if="!modifierGroups.length && !ingredients.length">
            برای این آیتم تنظیم قابل تغییر تعریف نشده است.
          </p>

          <LivePricingBreakdown :breakdown="preview.pricingBreakdown" :currency="currency" />

          <button class="add-btn" type="button" @click="confirmAdd">افزودن به سبد ({{ formatMoney(preview.lineTotal, currency) }})</button>
        </div>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import IngredientQuantityEditor from './IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from './ModifierRecipeImpactSelector.vue'
import LivePricingBreakdown from './LivePricingBreakdown.vue'
import { getItemDetail } from '@/utils/api'
import { createDefaultCustomization, estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  item: { type: Object, default: null },
  currency: { type: String, default: 'TOMAN' },
  branch: { type: String, default: '' },
})

const emit = defineEmits(['close', 'confirm'])

const loading = ref(false)
const error = ref('')
const selectedItem = ref(null)
const ingredients = ref([])
const modifierGroups = ref([])
const qty = ref(1)
const customization = ref({
  ingredient_adjustments: [],
  selected_modifiers: [],
})
const selectionError = ref('')

const fallbackImage = 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=1000&auto=format&fit=crop&q=60'
const selectedItemImage = computed(() => resolveItemImage(selectedItem.value) || fallbackImage)

const preview = computed(() =>
  estimateLine({
    basePrice: Number(selectedItem.value?.base_price || 0),
    qty: qty.value,
    ingredients: ingredients.value,
    modifierGroups: modifierGroups.value,
    customization: customization.value,
  }),
)

function withVariantContext(customizationPayload = {}) {
  const fixed = selectedItem.value?.variant_fixed_attributes
  if (fixed && typeof fixed === 'object' && Object.keys(fixed).length) {
    return {
      ...customizationPayload,
      variant_fixed_attributes: { ...fixed },
    }
  }
  return customizationPayload
}

watch(
  () => [props.open, props.item?.slug],
  async () => {
    if (!props.open || !props.item?.slug) {
      return
    }

    loading.value = true
    error.value = ''
    selectionError.value = ''
    qty.value = 1
    selectedItem.value = mergeItemData(props.item, null)
    ingredients.value = []
    modifierGroups.value = []
    customization.value = {
      ingredient_adjustments: [],
      selected_modifiers: [],
    }

    try {
      const detail = await getItemDetail(props.item.slug, props.branch)
      selectedItem.value = mergeItemData(props.item, detail.item)
      ingredients.value = detail.ingredients || []
      modifierGroups.value = detail.modifier_groups || []
      customization.value = withVariantContext(
        createDefaultCustomization(ingredients.value, modifierGroups.value),
      )
    } catch (err) {
      error.value = err.message || 'دریافت تنظیمات آیتم ناموفق بود.'
    } finally {
      loading.value = false
    }
  },
  { deep: true },
)

function setSelectedModifiers(next) {
  customization.value = sanitizeCustomization(
    {
      ...customization.value,
      selected_modifiers: next,
    },
    ingredients.value,
  )
  customization.value = withVariantContext(customization.value)
  selectionError.value = ''
}

function setCustomization(next) {
  const sanitized = sanitizeCustomization(
    {
      ...customization.value,
      ...next,
      selected_modifiers: customization.value.selected_modifiers,
    },
    ingredients.value,
  )
  customization.value = withVariantContext(sanitized)
  selectionError.value = ''
}

function confirmAdd() {
  if (!selectedItem.value) {
    return
  }
  if (!validateSelections()) {
    return
  }

  emit('confirm', {
    item_slug: selectedItem.value.slug,
    item_title: selectedItem.value.title,
    item_image: resolveItemImage(selectedItem.value),
    base_price: Number(selectedItem.value.base_price || 0),
    qty: preview.value.qty,
    unit_price_preview: preview.value.unitPrice,
    line_total_preview: preview.value.lineTotal,
    customization: preview.value.customization,
    ingredient_catalog: ingredients.value,
    modifier_groups_catalog: modifierGroups.value,
  })
}

function validateSelections() {
  for (const group of modifierGroups.value || []) {
    const count = (customization.value.selected_modifiers || []).filter((row) => row.group === group.group_name).length
    if (count < Number(group.min_select || 0)) {
      selectionError.value = `برای گروه "${group.title}" حداقل ${group.min_select} انتخاب لازم است.`
      return false
    }
    if (count > Number(group.max_select || 1)) {
      selectionError.value = `برای گروه "${group.title}" حداکثر ${group.max_select} انتخاب مجاز است.`
      return false
    }
  }
  selectionError.value = ''
  return true
}

function resolveItemImage(item = null) {
  return String(item?.image || item?.item_image || item?.website_image || '').trim()
}

function mergeItemData(baseItem = null, detailItem = null) {
  const merged = {
    ...(baseItem || {}),
    ...(detailItem || {}),
  }
  const image = resolveItemImage(detailItem) || resolveItemImage(baseItem)
  if (image) {
    merged.image = image
  }
  return merged
}
</script>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  z-index: 125;
  background: rgb(15 23 42 / 0.28);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0.5rem;
}

.sheet-panel {
  width: min(560px, 100%);
  max-height: calc(100vh - 1rem);
  overflow: auto;
  border-radius: 32px;
  padding: 0.8rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.98);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.26);
  box-shadow: 0 24px 70px rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  display: grid;
  gap: 0.62rem;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sheet-head p {
  margin: 0;
  color: var(--accent-gold);
  font-size: 1rem;
}

.icon-btn {
  width: 33px;
  height: 33px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  background: rgb(var(--palette-eggshell-rgb) / 0.92);
  color: var(--accent-gold);
  font-size: 1.1rem;
}

.hero {
  display: grid;
  grid-template-columns: 116px 1fr;
  gap: 0.55rem;
  align-items: center;
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.76);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
  padding: 0.54rem;
}

.hero img {
  width: 116px;
  height: 116px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  border-radius: 24px;
}

.hero h3 {
  margin: 0;
}

.hero p {
  margin: 0.15rem 0 0;
  font-size: 0.76rem;
}

.content {
  display: grid;
  gap: 0.6rem;
}

.qty-row {
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.78);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  padding: 0.5rem 0.6rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.qty-row small {
  color: var(--text-muted);
}

.qty-actions {
  display: flex;
  align-items: center;
  gap: 0.34rem;
}

.qty-btn {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.38);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
  color: var(--accent-gold);
  font-size: 1.1rem;
}

.hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.add-btn {
  border: 0;
  border-radius: 999px;
  padding: 0.82rem;
  background: var(--accent-green);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.44);
  color: #fff;
  font-family: inherit;
  font-size: 0.94rem;
}

.error {
  margin: 0;
  color: var(--danger);
}
</style>
