<template>
  <div class="detail-page" dir="rtl">
    <div class="state-shell" v-if="!item && (loading || error)">
      <div class="state-content">
        <p class="muted" v-if="loading">در حال دریافت جزئیات محصول...</p>
        <p class="error-msg" v-else-if="error">{{ error }}</p>
      </div>
    </div>

    <div class="detail-wrap" v-if="item">
      <div class="hero-area">
        <img :src="resolvedItemImage" :alt="item.title" class="hero-img" />
        <div class="hero-nav">
          <a href="/menu" class="nav-circle back-btn" aria-label="بازگشت">‹</a>
          <div class="nav-end-group">
            <button class="nav-circle heart-btn" type="button" aria-label="علاقه‌مندی">♡</button>
            <button class="nav-circle more-btn" type="button" aria-label="بیشتر">⋮</button>
          </div>
        </div>
      </div>

      <div class="content-card">
        <div class="title-row">
          <div class="title-block">
            <p class="item-category">{{ item.subcategory || item.category || 'منو' }}</p>
            <h1 class="item-title">{{ item.title }}</h1>
          </div>
          <div class="prep-badge" v-if="prepTimeText">
            <span class="prep-icon">⏱</span>
            <span class="prep-text">{{ prepTimeText }}</span>
          </div>
        </div>

        <p class="item-desc">{{ item.long_desc || item.short_desc || 'توضیح تکمیلی ثبت نشده است.' }}</p>

        <div class="tags-row" v-if="allergens.length">
          <span class="tag" v-for="a in allergens" :key="a">{{ a }}</span>
        </div>

        <div class="cta-bar">
          <div class="price-block">
            <small class="price-label">قیمت کل</small>
            <strong class="price-val">{{ formatMoney(linePreview.lineTotal, currency) }}</strong>
          </div>
          <div class="cart-actions">
            <div class="qty-control" v-if="hasIngredientCustomization || hasModifierCustomization">
              <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
              <span class="qty-num">{{ qty }}</span>
              <button class="qty-btn" type="button" @click="qty += 1">+</button>
            </div>
            <button class="add-to-cart-btn" type="button" @click="addToCart">
              {{ isEditing ? 'ذخیره تغییرات' : 'افزودن به سبد' }}
              <span class="cart-plus">+</span>
            </button>
          </div>
        </div>

        <div class="nutri-row" v-if="nutritionKcal !== '--' || macroCards.length">
          <div class="nutri-chip" v-if="nutritionKcal !== '--'">
            <small>کالری</small>
            <strong>{{ nutritionKcal }} kcal</strong>
          </div>
          <div class="nutri-chip" v-if="nutritionProteinPercent !== '--'">
            <small>پروتئین</small>
            <strong>{{ nutritionProteinPercent }}%</strong>
          </div>
          <div class="nutri-chip" v-for="m in macroCards" :key="m.key">
            <small>{{ m.label }}</small>
            <strong>{{ m.value }}</strong>
          </div>
        </div>

        <section class="detail-section" v-if="hasIngredientCustomization">
          <div class="section-head">
            <h3>مواد اولیه</h3>
            <small class="muted">{{ ingredients.length }}/{{ ingredients.length }} انتخاب شده</small>
          </div>
          <IngredientQuantityEditor
            :ingredients="ingredients"
            :model-value="customization"
            :currency="currency"
            @update:model-value="setCustomization"
          />
        </section>

        <section class="detail-section" v-if="hasModifierCustomization">
          <div class="section-head">
            <h3>گزینه‌های سفارشی</h3>
          </div>
          <div class="qty-header">
            <div>
              <small class="muted">تعداد سفارش</small>
              <strong>{{ qty }}</strong>
            </div>
            <div class="qty-ctrl-row">
              <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
              <button class="qty-btn" type="button" @click="qty += 1">+</button>
            </div>
          </div>
          <ModifierRecipeImpactSelector
            :groups="modifierGroups"
            :currency="currency"
            :model-value="customization.selected_modifiers"
            @update:model-value="setSelectedModifiers"
          />
          <p class="error-msg" v-if="selectionError">{{ selectionError }}</p>
        </section>

        <section class="detail-section">
          <LivePricingBreakdown :breakdown="linePreview.pricingBreakdown" :currency="currency" />
        </section>
      </div>
    </div>

    <section class="print-product-card">
      <header class="print-product-name">{{ item?.title || '-' }}</header>
      <main class="print-product-desc">{{ item?.long_desc || item?.short_desc || 'توضیحی ثبت نشده است.' }}</main>
      <footer class="print-product-price">{{ formatMoney(item?.base_price, currency) }}</footer>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import IngredientQuantityEditor from '@/components/IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from '@/components/ModifierRecipeImpactSelector.vue'
import LivePricingBreakdown from '@/components/LivePricingBreakdown.vue'
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
  return `${mins} دقیقه`
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
.detail-page {
  min-height: 100svh;
  background: var(--theme-background, #f6f1ea);
  direction: rtl;
}

.state-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60svh;
}

.state-content {
  text-align: center;
  padding: 2rem;
}

.detail-wrap {
  max-width: 640px;
  margin: 0 auto;
  padding-bottom: 3rem;
}

/* ─── Hero Image ─── */
.hero-area {
  position: relative;
  width: 100%;
}

.hero-img {
  width: 100%;
  height: min(420px, 60vw);
  object-fit: cover;
  object-position: center;
  display: block;
  border-radius: 0 0 32px 32px;
}

@media (max-width: 480px) {
  .hero-img {
    height: 280px;
  }
}

.hero-nav {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary, #3f2a1d);
  font-size: 1.2rem;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: background 0.2s;
}

.nav-circle:hover {
  background: rgba(255, 255, 255, 0.95);
}

.back-btn {
  font-size: 1.4rem;
  font-weight: 700;
}

.nav-end-group {
  display: flex;
  gap: 0.5rem;
}

/* ─── Content Card ─── */
.content-card {
  background: var(--glass-bg, #fdf8f1);
  border-radius: 28px 28px 0 0;
  margin-top: -24px;
  position: relative;
  padding: 1.4rem 1.2rem 1.5rem;
  display: grid;
  gap: 1rem;
  box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.06);
}

/* ─── Title Row ─── */
.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.title-block {
  flex: 1;
  min-width: 0;
}

.item-category {
  margin: 0 0 0.25rem;
  font-size: 0.78rem;
  color: var(--accent-gold, #c98d42);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.item-title {
  margin: 0;
  font-size: 1.55rem;
  font-weight: 800;
  color: var(--text-primary, #3f2a1d);
  line-height: 1.2;
}

.prep-badge {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: var(--accent-green40, rgba(111,74,49,0.1));
  border-radius: 999px;
  padding: 0.4rem 0.75rem;
  margin-top: 0.2rem;
}

.prep-icon {
  font-size: 0.9rem;
}

.prep-text {
  font-size: 0.8rem;
  color: var(--text-secondary, #654a38);
  font-weight: 600;
  white-space: nowrap;
}

.item-desc {
  margin: 0;
  font-size: 0.88rem;
  color: var(--text-muted, #846b58);
  line-height: 1.65;
}

/* ─── Tags ─── */
.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.tag {
  background: var(--accent-gold20, rgba(201,141,66,0.14));
  color: var(--text-secondary, #654a38);
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.74rem;
  font-weight: 500;
}

/* ─── CTA Bar ─── */
.cta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 20px;
  padding: 0.9rem 1rem;
}

.price-block {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.price-label {
  font-size: 0.7rem;
  color: var(--text-muted, #846b58);
}

.price-val {
  font-size: 1.28rem;
  color: var(--text-primary, #3f2a1d);
  font-weight: 800;
}

.cart-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.qty-control {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  padding: 0.2rem 0.4rem;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.qty-num {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary, #3f2a1d);
  min-width: 1.2rem;
  text-align: center;
}

.add-to-cart-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.6rem 1.1rem;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.28);
}

.cart-plus {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 900;
}

/* ─── Nutrition ─── */
.nutri-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.nutri-chip {
  flex: 1;
  min-width: 70px;
  border-radius: 14px;
  padding: 0.5rem 0.6rem;
  background: var(--accent-green80, rgba(111,74,49,0.9));
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.28);
  text-align: center;
  color: #fff;
}

.nutri-chip small {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.72);
}

.nutri-chip strong {
  font-size: 0.8rem;
}

/* ─── Sections ─── */
.detail-section {
  border-radius: 20px;
  border: 1px solid var(--theme-border, #d5c3af);
  background: rgba(255, 255, 255, 0.7);
  padding: 1rem;
  display: grid;
  gap: 0.7rem;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-head h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary, #3f2a1d);
}

.qty-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.qty-ctrl-row {
  display: flex;
  gap: 0.4rem;
}

.error-msg {
  margin: 0;
  color: var(--danger, #dc2626);
  font-size: 0.82rem;
}

/* ─── Print ─── */
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

  .detail-wrap,
  .state-shell {
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

@media (min-width: 640px) {
  .detail-wrap {
    padding: 0 1rem 3rem;
  }

  .hero-img {
    border-radius: 0 0 40px 40px;
  }

  .content-card {
    border-radius: 32px;
    margin: -2rem 0 0;
    padding: 1.6rem 1.5rem 2rem;
  }
}
</style>
