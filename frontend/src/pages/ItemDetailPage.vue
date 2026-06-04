<template>
  <LiquidGlassBackdrop>
    <section class="detail-shell" v-if="item">
      <LiquidGlassCard class="phone-frame">
        <header class="top-bar">
          <a class="icon-btn" href="/menu">&#x2039;</a>
          <p class="category-pill">{{ item.subcategory || item.category || 'Menu Item' }}</p>
          <a class="icon-btn" :href="`/item/${item.slug}`">&#x21E7;</a>
        </header>

        <img :src="resolvedItemImage" :alt="item.title" class="hero-image" />

        <section class="headline-row">
          <div>
            <h1>{{ item.title }}</h1>
            <p class="muted">{{ item.short_desc || 'آیتم سفارشی با BOM Template' }}</p>
          </div>
          <strong class="price">{{ formatMoney(item.base_price, currency) }}</strong>
        </section>

        <section class="nutrition-row">
          <div class="nutri-chip">
            <small>کالری</small>
            <strong>{{ nutritionKcal }} kcal</strong>
          </div>
          <div class="nutri-chip">
            <small>پروتئین</small>
            <strong>{{ nutritionProteinPercent === '--' ? '--' : `${nutritionProteinPercent}%` }}</strong>
          </div>
          <div class="nutri-chip" v-if="prepTimeText">
            <small>زمان مورد نیاز</small>
            <strong>{{ prepTimeText }}</strong>
          </div>
        </section>

        <section class="description-card">
          <h3>جزئیات</h3>
          <p>{{ item.long_desc || item.short_desc || 'توضیح تکمیلی ثبت نشده است.' }}</p>
          <div class="meta-tags" v-if="allergens.length">
            <span class="badge" v-for="allergen in allergens" :key="allergen">{{ allergen }}</span>
          </div>
        </section>

        <section class="nutrition-macro" v-if="macroCards.length">
          <article class="macro-item" v-for="macro in macroCards" :key="macro.key">
            <small>{{ macro.label }}</small>
            <strong>{{ macro.value }}</strong>
          </article>
        </section>

        <section id="ingredients" class="stack-card" v-if="hasIngredientCustomization">
          <IngredientQuantityEditor
            :ingredients="ingredients"
            :model-value="customization"
            :currency="currency"
            @update:model-value="setCustomization"
          />
        </section>

        <section id="customize" class="stack-card" v-if="hasModifierCustomization">
          <div class="qty-header">
            <div>
              <small class="muted">تعداد سفارش</small>
              <strong>{{ qty }}</strong>
            </div>
            <div class="qty-control">
              <button class="icon-btn" type="button" @click="qty = Math.max(qty - 1, 1)">-</button>
              <button class="icon-btn" type="button" @click="qty += 1">+</button>
            </div>
          </div>

          <ModifierRecipeImpactSelector
            :groups="modifierGroups"
            :currency="currency"
            :model-value="customization.selected_modifiers"
            @update:model-value="setSelectedModifiers"
          />
          <p class="error" v-if="selectionError">{{ selectionError }}</p>
        </section>

        <section class="stack-card">
          <LivePricingBreakdown :breakdown="linePreview.pricingBreakdown" :currency="currency" />
        </section>

        <StickyAddToCartBar
          :total="linePreview.lineTotal"
          :currency="currency"
          :button-text="isEditing ? 'ذخیره تغییرات' : 'افزودن به سبد'"
          hint="قیمت نهایی سفارش در سرور دوباره اعتبارسنجی می‌شود"
          @action="addToCart"
        />
      </LiquidGlassCard>

      <section class="print-product-card">
        <header class="print-product-name">{{ item.title || '-' }}</header>
        <main class="print-product-desc">{{ item.long_desc || item.short_desc || 'توضیحی ثبت نشده است.' }}</main>
        <footer class="print-product-price">{{ formatMoney(item.base_price, currency) }}</footer>
      </section>
    </section>

    <section class="detail-shell" v-else>
      <LiquidGlassCard class="phone-frame state-box">
        <p class="muted" v-if="loading">در حال دریافت جزئیات محصول...</p>
        <p class="error" v-else-if="error">{{ error }}</p>
      </LiquidGlassCard>
    </section>
  </LiquidGlassBackdrop>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import LiquidGlassCard from '@/components/LiquidGlassCard.vue'
import IngredientQuantityEditor from '@/components/IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from '@/components/ModifierRecipeImpactSelector.vue'
import LivePricingBreakdown from '@/components/LivePricingBreakdown.vue'
import StickyAddToCartBar from '@/components/StickyAddToCartBar.vue'
import { getItemDetail } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { createDefaultCustomization, estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { getLineById, upsertLine } from '@/stores/cartStore'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const fallbackImage = 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=1000&auto=format&fit=crop&q=60'

const loading = ref(false)
const error = ref('')
const item = ref(null)
const ingredients = ref([])
const modifierGroups = ref([])
const allergens = ref([])
const currency = ref('TOMAN')
const qty = ref(1)
const customization = ref({
  ingredient_adjustments: [],
  selected_modifiers: [],
})
const selectionError = ref('')

const query = parseQuery()
const editLineId = ref((props.boot.edit_line || query.edit || '').trim())
const isEditing = computed(() => Boolean(editLineId.value))
const activeBranch = ref(
  String(
    props.boot.active_branch ||
      props.boot?.table_context?.table?.branch ||
      query.branch ||
      '',
  ).trim(),
)

const linePreview = computed(() =>
  estimateLine({
    basePrice: Number(item.value?.base_price || 0),
    qty: qty.value,
    ingredients: ingredients.value,
    modifierGroups: modifierGroups.value,
    customization: customization.value,
  }),
)

const hasIngredientCustomization = computed(() => Array.isArray(ingredients.value) && ingredients.value.length > 0)
const hasModifierCustomization = computed(() => Array.isArray(modifierGroups.value) && modifierGroups.value.length > 0)
const resolvedItemImage = computed(() => resolveItemImage(item.value) || fallbackImage)

const nutritionKcal = computed(() => {
  const value = Number(item.value?.nutrition?.kcal ?? item.value?.nutrition_kcal ?? 0)
  if (!Number.isFinite(value) || value <= 0) {
    return '--'
  }
  return Math.round(value)
})

const nutritionProteinPercent = computed(() => {
  const value = Number(item.value?.nutrition?.protein_percent ?? item.value?.nutrition_protein_percent ?? 0)
  if (!Number.isFinite(value) || value <= 0) {
    return '--'
  }
  return Math.round(value)
})

const prepTimeText = computed(() => {
  const mins = Number(item.value?.prep_time_mins || 0)
  if (!Number.isFinite(mins) || mins <= 0) {
    return ''
  }
  return `${mins} min`
})

const macroCards = computed(() => {
  const nutrition = item.value?.nutrition || {}
  const macros = [
    { key: 'protein_g', label: 'Protein', suffix: 'g' },
    { key: 'carb_g', label: 'Carbs', suffix: 'g' },
    { key: 'sugar_g', label: 'Sugar', suffix: 'g' },
    { key: 'fat_g', label: 'Fat', suffix: 'g' },
  ]

  return macros
    .map((macro) => {
      const value = Number(nutrition[macro.key] ?? item.value?.[`nutrition_${macro.key}`] ?? 0)
      if (!Number.isFinite(value) || value <= 0) {
        return null
      }
      return {
        key: macro.key,
        label: macro.label,
        value: `${Math.round(value)} ${macro.suffix}`,
      }
    })
    .filter(Boolean)
})

function resolveSlug() {
  const fromBoot = String(props.boot.item_slug || '').trim()
  if (fromBoot) {
    return fromBoot
  }

  const path = window.location.pathname.replace(/^\/+|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[parts.length - 2] === 'item') {
    return parts[parts.length - 1]
  }
  return ''
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function normalizeModifierGroups(rawGroups = []) {
  return (rawGroups || [])
    .map((group) => {
      const groupName = String(group?.group_name || group?.name || group?.title || '').trim()
      if (!groupName) {
        return null
      }

      const options = (group.options || [])
        .map((option) => {
          const optionName = String(option?.name || option?.option_name || option?.option_key || '').trim()
          if (!optionName) {
            return null
          }

          const minQty = Math.max(toNumber(option.min_qty, 1), 0)
          const maxQty = Math.max(toNumber(option.max_qty, 9), minQty)
          const qtyStep = Math.max(toNumber(option.qty_step, 1), 0.0001)

          return {
            ...option,
            name: optionName,
            min_qty: minQty,
            max_qty: maxQty,
            qty_step: qtyStep,
            option_qty: Math.max(toNumber(option.option_qty, 1), 0.0001),
            price_delta: toNumber(option.price_delta, 0),
          }
        })
        .filter(Boolean)

      return {
        ...group,
        group_name: groupName,
        title: String(group.title || groupName).trim(),
        selection_mode: String(group.selection_mode || 'single').trim() || 'single',
        min_select: Math.max(toNumber(group.min_select, 0), 0),
        max_select: Math.max(toNumber(group.max_select, 1), 1),
        is_variant_attribute_selector: Number(group.is_variant_attribute_selector || 0),
        options,
      }
    })
    .filter(Boolean)
}

function normalizeSelectedModifiers(selectedRows = [], groups = []) {
  const groupMap = new Map(groups.map((group) => [group.group_name, group]))
  const deduped = new Map()

  for (const row of selectedRows || []) {
    const groupName = String(row?.group || row?.group_name || '').trim()
    const optionName = String(row?.option || row?.option_name || '').trim()
    if (!groupName || !optionName) {
      continue
    }

    const group = groupMap.get(groupName)
    if (!group) {
      continue
    }

    const option = (group.options || []).find((entry) => entry.name === optionName)
    if (!option) {
      continue
    }

    const minQty = Math.max(toNumber(option.min_qty, 1), 0)
    const maxQty = Math.max(toNumber(option.max_qty, 9), minQty)
    const step = Math.max(toNumber(option.qty_step, 1), 0.0001)
    let qty = toNumber(row.qty, minQty || 1)
    if (qty <= 0) {
      qty = minQty || step
    }

    const snapped = minQty + Math.round((qty - minQty) / step) * step
    const clamped = Math.min(Math.max(snapped, minQty), maxQty)

    deduped.set(`${groupName}::${optionName}`, {
      group: groupName,
      option: optionName,
      qty: Number(clamped.toFixed(4)),
    })
  }

  return Array.from(deduped.values())
}

function setCustomization(next) {
  const sanitized = sanitizeCustomization({
    ...customization.value,
    ...next,
    selected_modifiers: customization.value.selected_modifiers,
  }, ingredients.value)
  customization.value = {
    ...sanitized,
    selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value),
  }
}

function withVariantContext(customizationPayload = {}) {
  const fixed = item.value?.variant_fixed_attributes
  if (fixed && typeof fixed === 'object' && Object.keys(fixed).length) {
    return {
      ...customizationPayload,
      variant_fixed_attributes: { ...fixed },
    }
  }
  return customizationPayload
}

function setSelectedModifiers(next) {
  const sanitized = sanitizeCustomization(
    {
      ...customization.value,
      selected_modifiers: next,
      selected_alternatives: customization.value.selected_alternatives,
    },
    ingredients.value,
  )
  customization.value = {
    ...withVariantContext(sanitized),
    selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value),
  }
}

function validateSelections() {
  const selectedRows = normalizeSelectedModifiers(customization.value.selected_modifiers || [], modifierGroups.value)
  customization.value = {
    ...customization.value,
    selected_modifiers: selectedRows,
  }

  for (const group of modifierGroups.value) {
    const count = selectedRows.filter((row) => row.group === group.group_name).length

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

function hydrateForEdit(currentSlug) {
  if (!editLineId.value) {
    return
  }

  const line = getLineById(editLineId.value)
  if (!line || line.item_slug !== currentSlug) {
    editLineId.value = ''
    return
  }

  qty.value = Math.max(Number(line.qty || 1), 1)
  const sanitized = sanitizeCustomization(line.customization || {}, ingredients.value)
  customization.value = {
    ...withVariantContext(sanitized),
    selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value),
  }
}

async function loadItem() {
  const slug = resolveSlug()
  if (!slug) {
    error.value = 'آدرس محصول معتبر نیست.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await getItemDetail(slug, activeBranch.value)
    item.value = data.item
    ingredients.value = data.ingredients || []
    modifierGroups.value = normalizeModifierGroups(data.modifier_groups || [])
    allergens.value = data.allergens || []
    currency.value = 'TOMAN'

    const defaults = createDefaultCustomization(ingredients.value, modifierGroups.value)
    const defaultsWithVariant = withVariantContext(defaults)
    customization.value = {
      ...defaultsWithVariant,
      selected_modifiers: normalizeSelectedModifiers(defaultsWithVariant.selected_modifiers, modifierGroups.value),
    }
    hydrateForEdit(slug)
  } catch (err) {
    error.value = err.message || 'دریافت جزئیات آیتم ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function addToCart() {
  if (!item.value || !validateSelections()) {
    return
  }

  const cleanCustomization = sanitizeCustomization(customization.value, ingredients.value)

  upsertLine({
    id: editLineId.value || undefined,
    item_slug: item.value.slug,
    item_title: item.value.title,
    item_image: resolveItemImage(item.value),
    base_price: Number(item.value.base_price || 0),
    qty: linePreview.value.qty,
    unit_price_preview: linePreview.value.unitPrice,
    line_total_preview: linePreview.value.lineTotal,
    customization: cleanCustomization,
    ingredient_catalog: ingredients.value,
    modifier_groups_catalog: modifierGroups.value,
  })

  window.location.href = '/cart'
}

function resolveItemImage(source = null) {
  return String(source?.image || source?.item_image || source?.website_image || '').trim()
}

function handlePrintShortcut(event) {
  const key = String(event?.key || '').toLowerCase()
  if ((event?.ctrlKey || event?.metaKey) && key === 'p') {
    event.preventDefault()
    window.print()
  }
}

onMounted(() => {
  loadItem()
  window.addEventListener('keydown', handlePrintShortcut)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handlePrintShortcut)
})
</script>

<style scoped>
.detail-shell {
  width: min(560px, calc(100% - 1rem));
  margin: 0.8rem auto 2.2rem;
}

.phone-frame {
  padding: 0.76rem;
  display: grid;
  gap: 0.68rem;
  border-radius: 34px;
}

.state-box {
  min-height: 200px;
  align-content: center;
  text-align: center;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  background: rgba(255, 255, 255, 0.74);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-size: 1.05rem;
  box-shadow: 0 8px 18px rgb(var(--palette-deep-saffron-rgb) / 0.16);
}

.category-pill {
  margin: 0;
  color: var(--accent-gold);
  font-size: 0.82rem;
}

.hero-image {
  width: min(100%, 380px);
  border-radius: 28px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  justify-self: center;
}

.headline-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.headline-row h1 {
  margin: 0;
  font-size: 1.7rem;
  line-height: 1.08;
}

.headline-row p {
  margin: 0.24rem 0 0;
  font-size: 0.82rem;
}

.price {
  font-size: 1.24rem;
  color: var(--accent-gold);
}

.nutrition-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.nutri-chip {
  border-radius: 16px;
  padding: 0.52rem;
  color: var(--palette-eggshell);
  background: var(--accent-green80);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.32);
  box-shadow: 0 12px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  text-align: center;
}

.nutri-chip small {
  display: block;
  color: var(--glass-highlight);
  font-size: 0.68rem;
}

.nutri-chip strong {
  font-size: 0.84rem;
}

.description-card,
.stack-card,
.nutrition-macro {
  border-radius: 22px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  background: rgba(255, 255, 255, .56);
  box-shadow: 0 14px 36px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  padding: 0.72rem;
}

.description-card h3 {
  margin: 0;
  font-size: 1rem;
}

.description-card p {
  margin: 0.38rem 0 0;
  color: var(--text-muted);
  line-height: 1.7;
  font-size: 0.84rem;
}

.meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.45rem;
}

.nutrition-macro {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.4rem;
}

.macro-item {
  border-radius: 14px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.1);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  text-align: center;
  padding: 0.42rem;
}

.macro-item small {
  display: block;
  color: var(--text-muted);
  font-size: 0.7rem;
}

.qty-header {
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.qty-control {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.error {
  margin: 0.45rem 0 0;
  color: var(--danger);
}

.print-product-card {
  display: none;
}

@media print {
  @page {
    size: 5cm 8cm;
    margin: 0;
  }

  :global(body) {
    margin: 0 !important;
    background: #fff !important;
  }

  .detail-shell {
    width: 5cm !important;
    margin: 0 !important;
  }

  .detail-shell > :not(.print-product-card) {
    display: none !important;
  }

  .print-product-card {
    display: flex !important;
    flex-direction: column;
    justify-content: space-between;
    width: 5cm;
    height: 8cm;
    box-sizing: border-box;
    padding: 0.35cm;
    border: 1px solid #000;
    color: #000;
    direction: rtl;
    break-inside: avoid;
  }

  .print-product-name {
    margin: 0;
    font-size: 14pt;
    line-height: 1.3;
    font-weight: 700;
    text-align: center;
  }

  .print-product-desc {
    margin: 0;
    font-size: 10pt;
    line-height: 1.6;
    text-align: center;
    overflow: hidden;
  }

  .print-product-price {
    margin: 0;
    font-size: 13pt;
    font-weight: 800;
    text-align: center;
  }
}

@media (min-width: 900px) {
  .detail-shell {
    width: min(980px, calc(100% - 2rem));
  }

  .phone-frame {
    padding: 0.9rem;
  }
}
</style>
