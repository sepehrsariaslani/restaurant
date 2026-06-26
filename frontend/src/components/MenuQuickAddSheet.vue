<template>
  <teleport to="body">
    <div class="sheet-overlay" v-if="open" @click.self="onOverlayClick">
      <section class="sheet-panel" ref="panelRef" dir="rtl">
        <header class="sheet-head" ref="headRef">
          <div class="drag-handle" aria-hidden="true"></div>
          <div class="sheet-head__row">
            <button class="icon-btn back-btn" type="button" @click="$emit('close')" aria-label="بازگشت"><ChevronRight :size="20" /></button>
            <span class="sheet-title">افزودن به سبد</span>
            <button class="icon-btn close-btn" type="button" @click="$emit('close')" aria-label="بستن"><X :size="20" /></button>
          </div>
        </header>

        <div class="sheet-body" ref="bodyRef" @touchstart.passive="onPanelTouchStart" @touchmove.passive="onPanelTouchMove" @touchend.passive="onPanelTouchEnd">
          <div class="product-info-card" v-if="selectedItem">
            <!-- Image Column (right side in RTL) -->
            <div class="product-info__image-col">
              <img
                class="product-info__image"
                :src="selectedItemImage"
                :alt="selectedItem.title"
                loading="lazy"
              />
            </div>

            <!-- Text Content Column (left/center in RTL) -->
            <div class="product-info__content">
              <!-- Category chips -->
              <div class="product-info__chips" v-if="selectedItem.category_title || selectedItem.subcategory_title">
                <span
                  v-if="selectedItem.category_title"
                  class="product-info__chip product-info__chip--category"
                >{{ selectedItem.category_title }}</span>
                <span
                  v-if="selectedItem.subcategory_title"
                  class="product-info__chip product-info__chip--combo"
                >{{ selectedItem.subcategory_title }}</span>
              </div>

              <!-- Product title -->
              <h2 class="product-info__title">{{ selectedItem.title }}</h2>

              <!-- Short description -->
              <p v-if="selectedItem.short_desc || selectedItem.long_desc" class="product-info__desc">
                {{ selectedItem.short_desc || selectedItem.long_desc }}
              </p>
            </div>
          </div>

          <p class="muted" v-if="loading">در حال بارگذاری تنظیمات آیتم...</p>
          <p class="error" v-else-if="error">{{ error }}</p>

          <div class="content" v-else-if="selectedItem">
            <IngredientQuantityEditor
              v-if="ingredients.length"
              :ingredients="ingredients"
              :currency="currency"
              variant="preview"
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

            <!-- Nutrition summary bar -->
            <div class="nutrition-bar" v-if="nutritionItems.length">
              <div class="nutrition-bar__items">
                <div class="nutrition-item" v-for="entry in nutritionItems" :key="entry.key">
                  <component :is="entry.icon" class="nutrition-item__icon" :size="20" />
                  <span class="nutrition-item__value">{{ entry.value }}</span>
                  <span class="nutrition-item__label">{{ entry.label }}</span>
                </div>
              </div>
            </div>

            <!-- LivePricingBreakdown removed from preview
            <LivePricingBreakdown :breakdown="preview.pricingBreakdown" :currency="currency" />
            -->
          </div>

          <!-- Sticky Footer: Price + CTA (+ post-add qty control) -->
        </div>
        <footer class="sheet-footer">
          <div class="footer-price-card">
            <span class="footer-price-value">{{ formatMoney(preview.lineTotal, currency) }}</span>
          </div>

          <!-- State 1: Not yet added — show qty stepper + add button -->
          <template v-if="!hasAdded">
            <div class="footer-qty">
              <button class="qty-btn qty-minus" type="button" @click="qty = Math.max(1, qty - 1)" :disabled="qty <= 1" :class="{ 'is-disabled': qty <= 1 }">
                <Minus :size="13" />
              </button>
              <span class="qty-value">{{ qty }}</span>
              <button class="qty-btn qty-plus" type="button" @click="qty++">
                <Plus :size="13" />
              </button>
            </div>
            <button class="footer-cta" type="button" @click="confirmAdd">
              <ShoppingBasket class="footer-cta-icon" :size="16" />
              افزودن به سبد
            </button>
          </template>

          <!-- State 2: Already added — show qty control + added checkmark -->
          <template v-else>
            <div class="footer-qty footer-qty--added">
              <button class="qty-btn qty-minus" type="button" @click="decrementFromCart" :disabled="addedQty <= 1" :class="{ 'is-disabled': addedQty <= 1 }">
                <Minus :size="13" />
              </button>
              <span class="qty-value qty-value--added">{{ addedQty }}</span>
              <button class="qty-btn qty-plus" type="button" @click="incrementToCart">
                <Plus :size="13" />
              </button>
            </div>
            <button class="footer-cta footer-cta--done" type="button" @click="$emit('close')">
              <Check class="footer-cta-icon" :size="16" />
              ثبت شد
            </button>
          </template>
        </footer>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Flame, Dumbbell, Wheat, Droplets, X, ChevronRight, ShoppingBasket, Plus, Minus, Check } from 'lucide-vue-next'
import IngredientQuantityEditor from './IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from './ModifierRecipeImpactSelector.vue'
// LivePricingBreakdown removed from MenuQuickAddSheet preview
// import LivePricingBreakdown from './LivePricingBreakdown.vue'
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

// Post-add state
const hasAdded = ref(false)
const addedQty = ref(1)

// --- Drag-to-dismiss state ---
const panelRef = ref(null)
const bodyRef = ref(null)
let touchStartY = 0
let touchStartScrollTop = 0
let touchMoved = false
let touchStartTime = 0

function onPanelTouchStart(e) {
  if (!bodyRef.value) return
  touchStartY = e.touches[0].clientY
  touchStartScrollTop = bodyRef.value.scrollTop
  touchMoved = false
  touchStartTime = Date.now()
}

function onPanelTouchMove(e) {
  if (!bodyRef.value) return
  const dy = e.touches[0].clientY - touchStartY
  // Only track downward drag when panel is at the top of its scroll
  if (dy > 0 && touchStartScrollTop <= 0) {
    touchMoved = true
    panelRef.value.style.transform = `translateY(${Math.min(dy * 0.4, 120)}px)`
    panelRef.value.style.transition = 'none'
  }
}

function onPanelTouchEnd(e) {
  if (!bodyRef.value) return
  const dy = e.changedTouches[0].clientY - touchStartY
  const elapsed = Date.now() - touchStartTime
  panelRef.value.style.transform = ''
  panelRef.value.style.transition = ''

  // Dismiss if: dragged down > 80px, OR fast flick down > 50px in < 300ms
  const isFlick = dy > 50 && elapsed < 300
  const isDrag = dy > 80 && touchStartScrollTop <= 0

  if ((isDrag || isFlick) && touchMoved) {
    emit('close')
  }
}

function onOverlayClick(e) {
  // Only close on actual tap (not after a drag gesture)
  emit('close')
}

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

const nutritionItems = computed(() => {
  const n = preview.value?.nutrition || {}
  const rows = []
  const kcal = Number(n.kcal || 0)
  const protein = Number(n.protein_g || 0)
  const carb = Number(n.carb_g || 0)
  const fat = Number(n.fat_g || 0)
  if (Number.isFinite(kcal) && kcal > 0) rows.push({ key: 'kcal', icon: Flame, value: Math.round(kcal), label: 'کیلوکالری' })
  if (Number.isFinite(protein) && protein > 0) rows.push({ key: 'protein', icon: Dumbbell, value: `${Math.round(protein)} g`, label: 'پروتئین' })
  if (Number.isFinite(carb) && carb > 0) rows.push({ key: 'carb', icon: Wheat, value: `${Math.round(carb)} g`, label: 'کربوهیدرات' })
  if (Number.isFinite(fat) && fat > 0) rows.push({ key: 'fat', icon: Droplets, value: `${Math.round(fat)} g`, label: 'چربی' })
  return rows
})

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
    hasAdded.value = false
    addedQty.value = 1
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

  // Switch to post-add state: show qty control in footer
  hasAdded.value = true
  addedQty.value = qty.value
}

function incrementToCart() {
  addedQty.value++
  qty.value = addedQty.value
  // Re-emit with updated qty so the cart stays in sync
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

function decrementFromCart() {
  if (addedQty.value <= 1) return
  addedQty.value--
  qty.value = addedQty.value
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
  background: rgb(15 23 42 / 0.35);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0;
  touch-action: none;
}

@media (min-width: 820px) {
  .sheet-overlay {
    padding: 2rem;
    padding-bottom: max(2rem, env(safe-area-inset-bottom, 2rem));
  }

  .sheet-head .sheet-title {
    font-size: 1rem;
  }
}

.sheet-panel {
  width: min(640px, 100%);
  max-height: calc(100dvh - 0.5rem);
  max-height: calc(100svh - 0.5rem);
  border-radius: 22px 22px 0 0;
  padding: 0 0 1rem;
  background: var(--pos-surface-color, #ffffff);
  box-shadow: 0 -12px 48px rgba(0, 0, 0, 0.10);
  display: flex;
  flex-direction: column;
  will-change: transform;
}

.sheet-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  touch-action: pan-y;
  padding: 0 0.85rem 0.85rem;
  padding-top: 0.25rem;
  display: grid;
  gap: 0.55rem;
}

/* ── Sticky Footer ── */
.sheet-footer {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 136px 86px minmax(0, 1fr);
  grid-template-areas: "price qty cta";
  gap: 7px;
  padding: 0.35rem 1.25rem;
  padding-bottom: max(0.5rem, env(safe-area-inset-bottom, 0.5rem));
  background: var(--pos-surface-color, rgba(255, 255, 255, 0.97));
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.06);
  position: relative;
  z-index: 5;
  align-items: center;
}

.footer-price-card {
  grid-area: price;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.05rem;
  padding: 0.3rem 0.7rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.03);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  border-radius: 12px;
  min-width: 0;
  height: 36px;
  justify-content: center;
}

/* ── Quantity Stepper ── */
.footer-qty {
  grid-area: qty;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  background: var(--pos-surface-color, #ffffff);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 13px;
  gap: 0;
  overflow: hidden;
}

.qty-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.qty-btn.qty-plus {
  color: var(--accent-orange, #fd5010);
}

.qty-btn.qty-plus:hover {
  background: rgb(var(--accent-orange-rgb, 253 80 16) / 0.08);
}

.qty-btn.qty-minus {
  color: var(--accent-green);
}

.qty-btn.qty-minus:hover {
  background: rgb(var(--accent-green-rgb, 36 71 59) / 0.06);
}

.qty-btn.qty-minus.is-disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.qty-btn.qty-minus.is-disabled:hover {
  background: transparent;
}

.qty-value {
  flex: 1;
  text-align: center;
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--accent-green);
  font-variant-numeric: tabular-nums;
  min-width: 24px;
}

.footer-price-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 500;
  line-height: 1.2;
}

.footer-price-row {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
}

.footer-price-value {
  font-size: 1rem;
  font-weight: 800;
  color: var(--accent-green);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

.footer-cta {
  grid-area: cta;
  min-width: 0;
  height: 38px;
  border: none;
  border-radius: 13px;
  padding: 0 1rem;
  background: var(--accent-gold);
  color: #fff;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.38rem;
  box-shadow: 0 4px 18px rgb(var(--palette-deep-saffron-rgb) / 0.35);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.footer-cta-icon {
  width: 17px;
  height: 17px;
  flex-shrink: 0;
}

.footer-cta-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  color: #fff;
  flex-shrink: 0;
}

.footer-cta:hover {
  box-shadow: 0 6px 24px rgb(var(--palette-deep-saffron-rgb) / 0.45);
}

.footer-cta:active {
  transform: scale(0.97);
}

.sheet-head {
  position: relative;
  z-index: 2;
  background: var(--pos-surface-color, #ffffff);
  border-radius: 22px 22px 0 0;
  padding: 1.35rem 1rem 0.65rem;
  flex-shrink: 0;
}

.sheet-head__row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 42px;
  direction: ltr;
}

.sheet-head .back-btn {
  order: 1;
}

.sheet-head .close-btn {
  order: 3;
}

.sheet-head .sheet-title {
  position: absolute;
  inset-inline: 52px;
  left: 52px;
  right: 52px;
  order: 2;
  text-align: center;
  margin: 0;
  color: var(--accent-green);
  font-size: clamp(1.02rem, 3.4vw, 1.18rem);
  font-weight: 900;
  letter-spacing: -0.02em;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
}

.drag-handle {
  position: absolute;
  top: 0.48rem;
  left: 50%;
  transform: translateX(-50%);
  width: 42px;
  height: 5px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.icon-btn {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  background: var(--pos-surface-color, #ffffff);
  color: var(--accent-green);
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.15s ease;
}

.icon-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.04);
}

.icon-btn.close-btn {
  font-size: 1rem;
}

/* ── Product Info Card ── */
.product-info-card {
  display: flex;
  flex-direction: row-reverse;
  align-items: center;
  gap: 0.75rem;
  padding: 10px 12px;
  min-height: 108px;
  background: var(--pos-surface-color, var(--color-surface, #ffffff));
  border-radius: 22px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  box-shadow: 0 8px 22px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  position: relative;
}

/* ── Image column ── */
.product-info__image-col {
  flex-shrink: 0;
  width: 96px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-info__image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 16px;
  display: block;
}

/* ── Content column (centered) ── */
.product-info__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  gap: 0.24rem;
}

/* ── Category chips (centered above title) ── */
.product-info__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.35rem;
  margin-bottom: 0.15rem;
}

.product-info__chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
}

.product-info__chip--category {
  background: #fff0e8;
  color: #ff5a1f;
}

.product-info__chip--combo {
  background: #e8f0ec;
  color: #24473b;
}

/* ── Title (centered, 30px) ── */
.product-info__title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 900;
  color: var(--accent-green);
  line-height: 1.35;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-width: 100%;
}

/* ── Description (muted, centered) ── */
.product-info__desc {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, #7f918a);
  text-align: center;
  line-height: 1.55;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-width: 100%;
}

/* ── Mobile responsive ── */
@media (max-width: 600px) {
  .product-info-card {
    flex-direction: row-reverse;
    align-items: center;
    padding: 12px;
    gap: 0.72rem;
    min-height: auto;
    border-radius: 20px;
  }

  .product-info__image-col {
    width: 104px;
    height: 104px;
    justify-content: center;
  }

  .product-info__image {
    width: 104px;
    height: 104px;
    margin: 0 auto;
  }

  .product-info__title {
    font-size: 1rem;
    text-align: right;
  }

  .product-info__chips {
    justify-content: center;
  }

  .product-info__content {
    align-items: flex-start;
    text-align: right;
    gap: 0.22rem;
  }
}

@media (max-width: 600px) {
  .sheet-footer {
    padding: 0.42rem 0.85rem;
    padding-bottom: max(0.45rem, env(safe-area-inset-bottom, 0.45rem));
    gap: 6px;
    grid-template-columns: 1fr 76px minmax(0, 1fr);
    grid-template-areas: "price qty cta";
    align-items: stretch;
  }

  .footer-price-card {
    padding: 0.32rem 0.5rem;
    border-radius: 12px;
    height: 42px;
    min-width: 0;
  }

  .footer-price-label {
    font-size: 0.62rem;
  }

  .footer-price-value {
    font-size: 0.94rem;
    white-space: nowrap;
  }

  .footer-qty {
    height: 42px;
    width: 76px;
    min-width: 76px;
    border-radius: 12px;
    flex-shrink: 0;
  }

  .qty-btn {
    width: 23px;
  }

  .qty-value {
    font-size: 0.84rem;
    min-width: 18px;
  }

  .footer-cta {
    height: 42px;
    font-size: 0.78rem;
    padding: 0 0.65rem;
    border-radius: 12px;
    white-space: nowrap;
    min-width: 0;
  }

  .footer-cta-icon {
    width: 16px;
    height: 16px;
  }
}

@media (max-width: 390px) {
  .sheet-footer {
    padding: 0.36rem 0.65rem;
    padding-bottom: max(0.4rem, env(safe-area-inset-bottom, 0.4rem));
    gap: 5px;
    grid-template-columns: 1fr 70px minmax(0, 1fr);
  }

  .footer-price-card {
    padding: 0.3rem 0.42rem;
    height: 40px;
    border-radius: 11px;
  }

  .footer-price-label {
    font-size: 0.58rem;
  }

  .footer-price-value {
    font-size: 0.88rem;
  }

  .footer-qty {
    height: 40px;
    width: 70px;
    min-width: 70px;
    border-radius: 11px;
  }

  .qty-btn {
    width: 21px;
  }

  .qty-value {
    font-size: 0.78rem;
  }

  .footer-cta {
    height: 40px;
    font-size: 0.72rem;
    padding: 0 0.48rem;
    border-radius: 11px;
  }

  .footer-cta-icon {
    width: 15px;
    height: 15px;
  }
}

@media (max-width: 390px) {
  .sheet-head {
    padding: 1.25rem 0.85rem 0.55rem;
  }

  .sheet-head__row {
    min-height: 38px;
  }

  .sheet-head .sheet-title {
    left: 46px;
    right: 46px;
    inset-inline: 46px;
  }

  .sheet-head .sheet-title {
    font-size: 1rem;
  }

  .icon-btn {
    width: 38px;
    height: 38px;
    border-radius: 13px;
  }

  .product-info__image {
    width: 86px;
    height: 86px;
  }

  .product-info__title {
    font-size: 0.95rem;
  }

  .product-info-card {
    padding: 10px;
    gap: 0.5rem;
    border-radius: 18px;
  }
}

@media (max-width: 360px) {
  .product-info-card {
    padding: 16px;
    gap: 0.75rem;
  }

  .product-info__image {
    width: 110px;
    height: 110px;
  }

  .product-info__title {
    font-size: 1.15rem;
  }

  .product-info__chip {
    font-size: 0.62rem;
    padding: 2px 8px;
  }

  .sheet-footer {
    grid-template-columns: 1fr;
    grid-template-areas: "price" "qty" "cta";
    gap: 6px;
  }

  .footer-price-card {
    flex-direction: row;
    align-items: center;
    justify-content: center;
    padding: 0.36rem 0.6rem;
    height: 40px;
  }

  .footer-qty {
    height: 40px;
    border-radius: 12px;
    width: 100%;
  }

  .qty-btn {
    width: 24px;
  }

  .qty-value {
    font-size: 0.82rem;
  }

  .footer-cta {
    height: 42px;
    font-size: 0.78rem;
  }
}

.content {
  display: grid;
  gap: 0.6rem;
}

/* ── Nutrition Summary Bar ── */
.nutrition-bar {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgb(var(--palette-deep-sapphire-rgb, 36 71 59) / 0.04);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 36 71 59) / 0.08);
}

.nutrition-bar__items {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  gap: 0;
}

.nutrition-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.12rem;
  flex: 1;
  min-width: 0;
  position: relative;
}

.nutrition-item:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 10%;
  left: 0;
  width: 1px;
  height: 80%;
  background: rgb(var(--palette-deep-sapphire-rgb, 36 71 59) / 0.12);
}

.nutrition-item__icon {
  color: var(--accent-green);
  flex-shrink: 0;
}

.nutrition-item__value {
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--color-accent, #24473b);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.nutrition-item__label {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
}

@media (max-width: 360px) {
  .nutrition-bar__items {
    flex-wrap: wrap;
  }

  .nutrition-item {
    flex: 0 0 calc(50% - 0.25rem);
  }

  .nutrition-item:not(:last-child)::after {
    display: none;
  }
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
