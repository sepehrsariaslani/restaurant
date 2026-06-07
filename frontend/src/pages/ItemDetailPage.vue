<template>
  <div class="detail-page" dir="rtl">
    <div class="state-shell" v-if="!item && (loading || error)">
      <div class="state-content">
        <p class="muted" v-if="loading">در حال دریافت جزئیات محصول...</p>
        <p class="error-msg" v-else-if="error">{{ error }}</p>
      </div>
    </div>

    <div class="detail-wrap" v-if="item">
      <!-- ─── Gallery ─── -->
      <div class="hero-area">
        <div class="gallery-track" :style="{ transform: `translateX(${galleryOffset}%)` }">
          <img
            v-for="(src, idx) in galleryImages"
            :key="idx"
            :src="src"
            :alt="`${item.title} - ${idx + 1}`"
            class="gallery-img"
          />
        </div>

        <!-- Swipe navigation arrows (only if multiple images) -->
        <template v-if="galleryImages.length > 1">
          <button class="gallery-arrow gallery-arrow--prev" @click="prevImage" aria-label="قبلی">›</button>
          <button class="gallery-arrow gallery-arrow--next" @click="nextImage" aria-label="بعدی">‹</button>
          <div class="gallery-dots">
            <span
              v-for="(_, idx) in galleryImages"
              :key="idx"
              class="gallery-dot"
              :class="{ active: galleryIndex === idx }"
              @click="galleryIndex = idx"
            ></span>
          </div>
        </template>

        <!-- Nav bar over image -->
        <div class="hero-nav">
          <a href="/menu" class="nav-circle back-btn" aria-label="بازگشت">‹</a>
          <div class="nav-end-group">
            <button class="nav-circle more-btn" type="button" aria-label="بیشتر">⋮</button>
          </div>
        </div>
      </div>

      <!-- ─── Content card ─── -->
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

        <!-- Rating summary -->
        <div class="rating-row" v-if="reviewCount > 0">
          <div class="stars-display">
            <span v-for="s in 5" :key="s" class="star" :class="{ filled: s <= Math.round(averageRating) }">★</span>
          </div>
          <span class="rating-num">{{ averageRating }}</span>
          <span class="rating-count">({{ reviewCount }} نظر)</span>
        </div>

        <p class="item-desc">{{ item.long_desc || item.short_desc || 'توضیح تکمیلی ثبت نشده است.' }}</p>

        <div class="tags-row" v-if="allergens.length">
          <span class="tag" v-for="a in allergens" :key="a">{{ a }}</span>
        </div>

        <!-- ─── Nutrition ─── -->
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

        <!-- ─── Ingredients ─── -->
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

        <!-- ─── Modifiers ─── -->
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

        <!-- ─── Reviews section ─── -->
        <section class="reviews-section">
          <div class="reviews-header">
            <h3>نظرات مشتریان</h3>
            <span class="reviews-count" v-if="reviewCount > 0">{{ reviewCount }} نظر</span>
          </div>

          <!-- Existing reviews -->
          <div class="reviews-list" v-if="reviews.length">
            <div class="review-card" v-for="rv in reviews.slice(0, showAllReviews ? reviews.length : 3)" :key="rv.id">
              <div class="review-top">
                <div class="review-avatar">{{ rv.author.slice(0, 1) }}</div>
                <div class="review-meta">
                  <strong class="review-author">{{ rv.author }}</strong>
                  <div class="review-stars">
                    <span v-for="s in 5" :key="s" class="star sm" :class="{ filled: s <= rv.rating }">★</span>
                  </div>
                </div>
                <span class="review-date">{{ formatReviewDate(rv.date) }}</span>
              </div>
              <p class="review-comment" v-if="rv.comment">{{ rv.comment }}</p>
            </div>
            <button
              v-if="reviews.length > 3 && !showAllReviews"
              class="show-more-btn"
              type="button"
              @click="showAllReviews = true"
            >
              نمایش همه {{ reviews.length }} نظر
            </button>
          </div>

          <p class="no-reviews" v-else>هنوز نظری ثبت نشده. اولین نفر باشید!</p>

          <!-- Add review form -->
          <div class="add-review">
            <h4>ثبت نظر</h4>
            <div class="star-picker">
              <button
                v-for="s in 5"
                :key="s"
                type="button"
                class="star-btn"
                :class="{ filled: s <= newReview.rating }"
                @click="newReview.rating = s"
              >★</button>
            </div>
            <input
              class="review-input"
              v-model.trim="newReview.author"
              placeholder="نام شما (اختیاری)"
            />
            <textarea
              class="review-textarea"
              v-model.trim="newReview.comment"
              placeholder="نظر خود را بنویسید..."
              rows="3"
            ></textarea>
            <button class="submit-review-btn" type="button" @click="submitReview">ثبت نظر</button>
            <p class="review-success" v-if="reviewSubmitted">✓ نظر شما ثبت شد. ممنون!</p>
          </div>
        </section>
      </div>
    </div>

    <!-- ─── Sticky bottom bar ─── -->
    <div class="sticky-bottom-bar" v-if="item" dir="rtl">
      <button
        class="wishlist-btn"
        type="button"
        :class="{ loved: isWishlisted }"
        @click="toggleWishlist"
        :aria-label="isWishlisted ? 'حذف از علاقه‌مندی‌ها' : 'افزودن به علاقه‌مندی‌ها'"
      >
        <span class="heart-icon">{{ isWishlisted ? '♥' : '♡' }}</span>
      </button>

      <div class="qty-control" v-if="hasIngredientCustomization || hasModifierCustomization">
        <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
        <span class="qty-num">{{ qty }}</span>
        <button class="qty-btn" type="button" @click="qty += 1">+</button>
      </div>

      <div class="price-and-add">
        <div class="bottom-price">
          <small>قیمت کل</small>
          <strong>{{ formatMoney(linePreview.lineTotal, currency) }}</strong>
        </div>
        <button class="add-to-cart-btn" type="button" @click="addToCart">
          {{ isEditing ? 'ذخیره تغییرات' : 'افزودن به سبد' }}
          <span class="cart-plus">+</span>
        </button>
      </div>
    </div>

    <!-- Print card -->
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
import { getItemReviews, addItemReview, getAverageRating, getReviewCount } from '@/utils/reviewsStore'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
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
const customization = ref({ ingredient_adjustments: [], selected_modifiers: [] })
const selectionError = ref('')

// Gallery
const galleryIndex = ref(0)
const galleryImages = computed(() => {
  const main = resolveItemImage(item.value)
  const extra = Array.isArray(item.value?.extra_images) ? item.value.extra_images : []
  const all = [main, ...extra].filter(Boolean)
  return all.length ? all : [fallbackImage]
})
const galleryOffset = computed(() => galleryIndex.value * -100)
function prevImage() { galleryIndex.value = (galleryIndex.value + 1) % galleryImages.value.length }
function nextImage() { galleryIndex.value = (galleryIndex.value - 1 + galleryImages.value.length) % galleryImages.value.length }

// Touch swipe
let touchStartX = 0
function onTouchStart(e) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(dx) > 40) { dx > 0 ? nextImage() : prevImage() }
}

// Wishlist
const WISHLIST_KEY = 'restaurant_wishlist_v1'
function loadWishlist() {
  try { return JSON.parse(localStorage.getItem(WISHLIST_KEY) || '[]') } catch (_) { return [] }
}
const isWishlisted = ref(false)
function toggleWishlist() {
  const slug = item.value?.slug || ''
  if (!slug) return
  const list = loadWishlist()
  const idx = list.indexOf(slug)
  if (idx >= 0) { list.splice(idx, 1); isWishlisted.value = false }
  else { list.push(slug); isWishlisted.value = true }
  try { localStorage.setItem(WISHLIST_KEY, JSON.stringify(list)) } catch (_) {}
}

// Reviews
const reviews = ref([])
const showAllReviews = ref(false)
const averageRating = ref(0)
const reviewCount = ref(0)
const newReview = ref({ author: '', rating: 5, comment: '' })
const reviewSubmitted = ref(false)

function refreshReviews() {
  const slug = item.value?.slug || ''
  reviews.value = getItemReviews(slug)
  averageRating.value = getAverageRating(slug)
  reviewCount.value = getReviewCount(slug)
}

function submitReview() {
  const slug = item.value?.slug || ''
  if (!slug) return
  addItemReview(slug, { ...newReview.value })
  refreshReviews()
  newReview.value = { author: '', rating: 5, comment: '' }
  reviewSubmitted.value = true
  setTimeout(() => { reviewSubmitted.value = false }, 3000)
}

function formatReviewDate(dateStr = '') {
  try {
    const d = new Date(dateStr)
    if (isNaN(d)) return ''
    return d.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' })
  } catch (_) { return '' }
}

// ─── existing logic ───────────────────────────────────────────────
const query = parseQuery()
const editLineId = ref((props.boot.edit_line || query.edit || '').trim())
const isEditing = computed(() => Boolean(editLineId.value))
const activeBranch = ref(
  String(props.boot.active_branch || props.boot?.table_context?.table?.branch || query.branch || '').trim(),
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

const nutritionKcal = computed(() => {
  const value = Number(item.value?.nutrition?.kcal ?? item.value?.nutrition_kcal ?? 0)
  return Number.isFinite(value) && value > 0 ? Math.round(value) : '--'
})

const nutritionProteinPercent = computed(() => {
  const value = Number(item.value?.nutrition?.protein_percent ?? item.value?.nutrition_protein_percent ?? 0)
  return Number.isFinite(value) && value > 0 ? Math.round(value) : '--'
})

const prepTimeText = computed(() => {
  const mins = Number(item.value?.prep_time_mins || 0)
  return Number.isFinite(mins) && mins > 0 ? `${mins} دقیقه` : ''
})

const macroCards = computed(() => {
  const nutrition = item.value?.nutrition || {}
  return [
    { key: 'protein_g', label: 'Protein', suffix: 'g' },
    { key: 'carb_g', label: 'Carbs', suffix: 'g' },
    { key: 'sugar_g', label: 'Sugar', suffix: 'g' },
    { key: 'fat_g', label: 'Fat', suffix: 'g' },
  ]
    .map((macro) => {
      const value = Number(nutrition[macro.key] ?? item.value?.[`nutrition_${macro.key}`] ?? 0)
      if (!Number.isFinite(value) || value <= 0) return null
      return { key: macro.key, label: macro.label, value: `${Math.round(value)} ${macro.suffix}` }
    })
    .filter(Boolean)
})

function resolveSlug() {
  const fromBoot = String(props.boot.item_slug || '').trim()
  if (fromBoot) return fromBoot
  const path = window.location.pathname.replace(/^\/+|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[parts.length - 2] === 'item') return parts[parts.length - 1]
  return ''
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function normalizeModifierGroups(rawGroups = []) {
  return (rawGroups || []).map((group) => {
    const groupName = String(group?.group_name || group?.name || group?.title || '').trim()
    if (!groupName) return null
    const options = (group.options || []).map((option) => {
      const optionName = String(option?.name || option?.option_name || option?.option_key || '').trim()
      if (!optionName) return null
      const minQty = Math.max(toNumber(option.min_qty, 1), 0)
      const maxQty = Math.max(toNumber(option.max_qty, 9), minQty)
      const qtyStep = Math.max(toNumber(option.qty_step, 1), 0.0001)
      return { ...option, name: optionName, min_qty: minQty, max_qty: maxQty, qty_step: qtyStep, option_qty: Math.max(toNumber(option.option_qty, 1), 0.0001), price_delta: toNumber(option.price_delta, 0) }
    }).filter(Boolean)
    return { ...group, group_name: groupName, title: String(group.title || groupName).trim(), selection_mode: String(group.selection_mode || 'single').trim() || 'single', min_select: Math.max(toNumber(group.min_select, 0), 0), max_select: Math.max(toNumber(group.max_select, 1), 1), is_variant_attribute_selector: Number(group.is_variant_attribute_selector || 0), options }
  }).filter(Boolean)
}

function normalizeSelectedModifiers(selectedRows = [], groups = []) {
  const groupMap = new Map(groups.map((group) => [group.group_name, group]))
  const deduped = new Map()
  for (const row of selectedRows || []) {
    const groupName = String(row?.group || row?.group_name || '').trim()
    const optionName = String(row?.option || row?.option_name || '').trim()
    if (!groupName || !optionName) continue
    const group = groupMap.get(groupName)
    if (!group) continue
    const option = (group.options || []).find((entry) => entry.name === optionName)
    if (!option) continue
    const minQty = Math.max(toNumber(option.min_qty, 1), 0)
    const maxQty = Math.max(toNumber(option.max_qty, 9), minQty)
    const step = Math.max(toNumber(option.qty_step, 1), 0.0001)
    let qty2 = toNumber(row.qty, minQty || 1)
    if (qty2 <= 0) qty2 = minQty || step
    const snapped = minQty + Math.round((qty2 - minQty) / step) * step
    const clamped = Math.min(Math.max(snapped, minQty), maxQty)
    deduped.set(`${groupName}::${optionName}`, { group: groupName, option: optionName, qty: Number(clamped.toFixed(4)) })
  }
  return Array.from(deduped.values())
}

function setCustomization(next) {
  const sanitized = sanitizeCustomization({ ...customization.value, ...next, selected_modifiers: customization.value.selected_modifiers }, ingredients.value)
  customization.value = { ...sanitized, selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

function withVariantContext(customizationPayload = {}) {
  const fixed = item.value?.variant_fixed_attributes
  if (fixed && typeof fixed === 'object' && Object.keys(fixed).length) return { ...customizationPayload, variant_fixed_attributes: { ...fixed } }
  return customizationPayload
}

function setSelectedModifiers(next) {
  const sanitized = sanitizeCustomization({ ...customization.value, selected_modifiers: next, selected_alternatives: customization.value.selected_alternatives }, ingredients.value)
  customization.value = { ...withVariantContext(sanitized), selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

function validateSelections() {
  const selectedRows = normalizeSelectedModifiers(customization.value.selected_modifiers || [], modifierGroups.value)
  customization.value = { ...customization.value, selected_modifiers: selectedRows }
  for (const group of modifierGroups.value) {
    const count = selectedRows.filter((row) => row.group === group.group_name).length
    if (count < Number(group.min_select || 0)) { selectionError.value = `برای گروه "${group.title}" حداقل ${group.min_select} انتخاب لازم است.`; return false }
    if (count > Number(group.max_select || 1)) { selectionError.value = `برای گروه "${group.title}" حداکثر ${group.max_select} انتخاب مجاز است.`; return false }
  }
  selectionError.value = ''
  return true
}

function hydrateForEdit(currentSlug) {
  if (!editLineId.value) return
  const line = getLineById(editLineId.value)
  if (!line || line.item_slug !== currentSlug) { editLineId.value = ''; return }
  qty.value = Math.max(Number(line.qty || 1), 1)
  const sanitized = sanitizeCustomization(line.customization || {}, ingredients.value)
  customization.value = { ...withVariantContext(sanitized), selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

async function loadItem() {
  const slug = resolveSlug()
  if (!slug) { error.value = 'آدرس محصول معتبر نیست.'; return }
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
    customization.value = { ...defaultsWithVariant, selected_modifiers: normalizeSelectedModifiers(defaultsWithVariant.selected_modifiers, modifierGroups.value) }
    hydrateForEdit(slug)
    isWishlisted.value = loadWishlist().includes(slug)
    refreshReviews()
  } catch (err) {
    error.value = err.message || 'دریافت جزئیات آیتم ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function addToCart() {
  if (!item.value || !validateSelections()) return
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
  if ((event?.ctrlKey || event?.metaKey) && key === 'p') { event.preventDefault(); window.print() }
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
  padding-bottom: 5.5rem;
}

.state-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60svh;
}

.state-content { text-align: center; padding: 2rem; }

.detail-wrap {
  max-width: 640px;
  margin: 0 auto;
}

/* ─── Gallery ─── */
.hero-area {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 0 0 32px 32px;
  background: var(--theme-surface-alt, #f1e7db);
}

.gallery-track {
  display: flex;
  transition: transform 0.35s cubic-bezier(.4,0,.2,1);
  height: min(420px, 60vw);
}

@media (max-width: 480px) {
  .gallery-track { height: 280px; }
}

.gallery-img {
  min-width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
  flex-shrink: 0;
}

.gallery-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(8px);
  border: none;
  cursor: pointer;
  font-size: 1.3rem;
  color: var(--text-primary, #3f2a1d);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 2;
}
.gallery-arrow--prev { left: 0.75rem; }
.gallery-arrow--next { right: 0.75rem; }

.gallery-dots {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.35rem;
  z-index: 2;
}

.gallery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.55);
  cursor: pointer;
  transition: background 0.2s, width 0.2s;
}
.gallery-dot.active { background: #fff; width: 20px; border-radius: 4px; }

.hero-nav {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 3;
}

.nav-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(8px);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary, #3f2a1d);
  font-size: 1.2rem;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: background 0.2s;
}
.nav-circle:hover { background: rgba(255,255,255,0.95); }
.back-btn { font-size: 1.4rem; font-weight: 700; }
.nav-end-group { display: flex; gap: 0.5rem; }

/* ─── Content Card ─── */
.content-card {
  background: var(--glass-bg, #fdf8f1);
  border-radius: 28px 28px 0 0;
  margin-top: -24px;
  position: relative;
  padding: 1.4rem 1.2rem 1.5rem;
  display: grid;
  gap: 1rem;
  box-shadow: 0 -8px 32px rgba(0,0,0,0.06);
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}
.title-block { flex: 1; min-width: 0; }
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
.prep-icon { font-size: 0.9rem; }
.prep-text { font-size: 0.8rem; color: var(--text-secondary, #654a38); font-weight: 600; white-space: nowrap; }

/* Rating row */
.rating-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.stars-display { display: flex; gap: 0.1rem; }
.star { color: #ddd; font-size: 1rem; }
.star.filled { color: #f5a623; }
.star.sm { font-size: 0.75rem; }
.rating-num { font-size: 0.88rem; font-weight: 700; color: var(--text-primary, #3f2a1d); }
.rating-count { font-size: 0.78rem; color: var(--text-muted, #846b58); }

.item-desc {
  margin: 0;
  font-size: 0.88rem;
  color: var(--text-muted, #846b58);
  line-height: 1.65;
}

.tags-row { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.tag {
  background: var(--accent-gold20, rgba(201,141,66,0.14));
  color: var(--text-secondary, #654a38);
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.74rem;
  font-weight: 500;
}

/* Nutrition */
.nutri-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.nutri-chip {
  flex: 1;
  min-width: 70px;
  border-radius: 14px;
  padding: 0.5rem 0.6rem;
  background: var(--accent-green40, rgba(111,74,49,0.1));
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  text-align: center;
}
.nutri-chip small { font-size: 0.68rem; color: var(--text-muted, #846b58); }
.nutri-chip strong { font-size: 0.82rem; color: var(--text-primary, #3f2a1d); }

/* Sections */
.detail-section {
  border-top: 1px solid var(--glass-border, #e5ddd4);
  padding-top: 0.9rem;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}
.section-head h3 { margin: 0; font-size: 0.95rem; color: var(--text-primary, #3f2a1d); }

.qty-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.qty-ctrl-row { display: flex; gap: 0.4rem; }
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

.error-msg { color: #c0392b; font-size: 0.83rem; margin: 0; }
.muted { color: var(--text-muted, #846b58); font-size: 0.82rem; }

/* ─── Reviews ─── */
.reviews-section {
  border-top: 1px solid var(--glass-border, #e5ddd4);
  padding-top: 1rem;
  display: grid;
  gap: 0.9rem;
}
.reviews-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.reviews-header h3 { margin: 0; font-size: 0.95rem; color: var(--text-primary, #3f2a1d); }
.reviews-count {
  font-size: 0.75rem;
  background: var(--accent-green40, rgba(111,74,49,0.12));
  color: var(--text-secondary, #654a38);
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
  font-weight: 600;
}

.reviews-list { display: grid; gap: 0.65rem; }

.review-card {
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 16px;
  padding: 0.9rem;
  display: grid;
  gap: 0.5rem;
}
.review-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.review-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  flex-shrink: 0;
}
.review-meta { flex: 1; display: grid; gap: 0.1rem; }
.review-author { font-size: 0.85rem; color: var(--text-primary, #3f2a1d); }
.review-stars { display: flex; gap: 0.05rem; }
.review-date { font-size: 0.72rem; color: var(--text-muted, #846b58); white-space: nowrap; }
.review-comment { margin: 0; font-size: 0.84rem; color: var(--text-secondary, #654a38); line-height: 1.55; }

.show-more-btn {
  background: none;
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 999px;
  padding: 0.4rem 0.9rem;
  font-size: 0.8rem;
  color: var(--accent-green, #6f4a31);
  cursor: pointer;
  font-weight: 600;
  margin-top: 0.25rem;
  justify-self: center;
}

.no-reviews { margin: 0; font-size: 0.84rem; color: var(--text-muted, #846b58); text-align: center; padding: 0.5rem; }

.add-review {
  background: var(--glass-bg, #fdf8f1);
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 16px;
  padding: 1rem;
  display: grid;
  gap: 0.6rem;
}
.add-review h4 { margin: 0; font-size: 0.88rem; color: var(--text-primary, #3f2a1d); }

.star-picker { display: flex; gap: 0.25rem; flex-direction: row-reverse; justify-content: flex-end; }
.star-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #ddd;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.15s;
}
.star-btn.filled { color: #f5a623; }

.review-input,
.review-textarea {
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 12px;
  padding: 0.6rem 0.8rem;
  font-family: inherit;
  font-size: 0.85rem;
  background: #fff;
  color: var(--text-primary, #3f2a1d);
  width: 100%;
  box-sizing: border-box;
  outline: none;
  direction: rtl;
}
.review-textarea { resize: vertical; min-height: 72px; }

.submit-review-btn {
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.6rem 1.4rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  justify-self: flex-start;
}

.review-success {
  margin: 0;
  font-size: 0.82rem;
  color: #27ae60;
  font-weight: 600;
}

/* ─── Sticky Bottom Bar ─── */
.sticky-bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid var(--glass-border, #e5ddd4);
  box-shadow: 0 -8px 24px rgba(0,0,0,0.1);
  padding: 0.6rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  z-index: 120;
  max-width: 640px;
  margin: 0 auto;
  border-radius: 24px 24px 0 0;
}

.wishlist-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1.5px solid var(--glass-border, #e5ddd4);
  background: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color 0.2s, background 0.2s;
}
.wishlist-btn.loved {
  border-color: #e74c3c;
  background: rgba(231, 76, 60, 0.06);
}
.heart-icon { font-size: 1.2rem; line-height: 1; }
.wishlist-btn:not(.loved) .heart-icon { color: var(--text-muted, #846b58); }
.wishlist-btn.loved .heart-icon { color: #e74c3c; }

.qty-control {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 999px;
  padding: 0.25rem 0.5rem;
  flex-shrink: 0;
}
.qty-num {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary, #3f2a1d);
  min-width: 1.2rem;
  text-align: center;
}

.price-and-add {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.bottom-price {
  display: flex;
  flex-direction: column;
}
.bottom-price small { font-size: 0.68rem; color: var(--text-muted, #846b58); }
.bottom-price strong { font-size: 1.1rem; color: var(--text-primary, #3f2a1d); font-weight: 800; }

.add-to-cart-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.7rem 1.2rem;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(111,74,49,0.28);
}
.cart-plus {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255,255,255,0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 900;
}

/* Print */
.print-product-card { display: none; }
@media print {
  .sticky-bottom-bar, .hero-nav, .gallery-arrow, .gallery-dots { display: none !important; }
  .print-product-card { display: block; padding: 1rem; }
  .print-product-name { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
  .print-product-desc { font-size: 0.9rem; color: #555; margin-bottom: 0.5rem; }
  .print-product-price { font-size: 1rem; font-weight: 600; }
}
</style>
