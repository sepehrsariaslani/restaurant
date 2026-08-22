<template>
  <article
    class="product-card"
    :class="[`layout--${layout}`, { 'is-added': justAdded }]"
    :style="cardStyle"
    role="article"
  >
    <!-- ════ LAYOUT: compact (CSS Grid — 3-column desktop) ════ -->
    <template v-if="layout === 'compact'">
      <!-- Image Column (rightmost in RTL grid) -->
      <a class="compact-image-col" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img
          class="card-image"
          :src="resolvedImage"
          :alt="item.title"
          loading="lazy"
          :class="{ 'img-dimmed': isTemporarilyUnavailable }"
        />
        <span v-if="unavailableReason" class="unavailable-badge stock-out-badge">{{ unavailableReason }}</span>
        <span v-else-if="isComingSoon" class="unavailable-badge">به‌زودی</span>
        <span v-if="isTemporarilyUnavailable && !isComingSoon" class="unavailable-badge">ناموجود</span>
      </a>

      <!-- Content Column (center) -->
      <div class="compact-content">
        <div class="pills-row" v-if="visibleTags.length">
          <span v-for="tag in visibleTags" :key="`compact-${tag}`" class="pill pill--tag">{{ tag }}</span>
        </div>
        <a class="card-title-link" :href="`/item/${item.slug}`">
          <h3 class="card-title">{{ item.title }}</h3>
        </a>
        <p v-if="item.short_desc || item.description" class="card-description">{{ item.short_desc || item.description }}</p>
        <span v-if="nutritionText" class="card-nutrition">{{ nutritionText }}</span>
        <div class="card-price-row">
          <span v-if="unavailableReason" class="card-price stock-out-label">{{ unavailableReason }}</span>
          <span v-else-if="isComingSoon" class="card-price soon-label">به‌زودی</span>
          <span v-else class="card-price">{{ displayBasePriceText }}</span>
        </div>
      </div>

      <!-- Actions Column (leftmost in RTL grid) -->
      <div class="compact-actions">
        <button v-if="showBomButton" class="bom-btn bom-btn--compact" type="button" :aria-label="`مشاهده BOM ${item.title}`" @click.prevent="handleBomPreview">
          <Layers :size="12" />
          BOM
        </button>
        <div class="qty-pill qty-pill--compact" v-if="cartQty > 0 && !hasCustomization && !isUnavailable">
          <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)"><Minus :size="13" /></button>
          <strong>{{ cartQty }}</strong>
          <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)"><Plus :size="13" /></button>
        </div>
        <button
          v-else-if="!isUnavailable"
          class="add-btn"
          type="button"
          :aria-label="`افزودن ${item.title} به سبد`"
          @click.prevent="handleAdd"
        >
          <span class="add-icon"><Check v-if="justAdded" :size="16" /><Plus v-else :size="17" /></span>
        </button>
      </div>
    </template>

    <!-- ════ LAYOUT: featured ════ -->
    <template v-else-if="layout === 'featured'">
      <a class="featured-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="featured-img" loading="lazy" :class="{ 'img-dimmed': isTemporarilyUnavailable }" />
        <span class="prep-badge" v-if="item.prep_time_mins">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          {{ item.prep_time_mins }} دقیقه
        </span>
        <span class="unavailable-badge" v-if="isTemporarilyUnavailable">ناموجود</span>
      </a>
      <div class="featured-body">
        <div class="tag-row" v-if="visibleTags.length">
          <span class="mini-pill tag-pill" v-for="tag in visibleTags" :key="`featured-${tag}`">{{ tag }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || 'توضیحی برای این آیتم ثبت نشده است.' }}</p>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="featured-foot">
          <div>
            <small class="muted" v-if="!isComingSoon">قیمت</small>
            <strong class="price stock-out-label" v-if="unavailableReason">{{ unavailableReason }}</strong>
            <strong class="price soon-label" v-else-if="isComingSoon">به‌زودی</strong>
            <strong class="price" v-else :class="{ 'price-strikethrough': isTemporarilyUnavailable }">{{ displayBasePriceText }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="foot-actions">
            <button class="bom-btn btn-sm" type="button" :aria-label="`مشاهده BOM ${item.title}`" @click.prevent="handleBomPreview" v-if="showBomButton">
              <Layers :size="13" />
              BOM
            </button>
            <div class="qty-pill" v-if="cartQty > 0 && !hasCustomization && !isUnavailable">
              <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)"><Minus :size="13" /></button>
              <strong>{{ cartQty }}</strong>
              <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)"><Plus :size="13" /></button>
            </div>
            <button v-if="isCustomizable && !isTemporarilyUnavailable" class="add-btn add-btn--pill customize-btn" type="button" :aria-label="`سفارشی‌سازی ${item.title}`" @click.prevent="handleCustomize">
              <span>بساز</span>
              <span class="add-circle"><Pencil :size="14" /></span>
            </button>
            <button v-else-if="!isUnavailable" class="add-btn add-btn--pill" type="button" :class="{ added: justAdded }" :aria-label="`افزودن به سبد`" @click.prevent="handleAdd">
              <span>{{ justAdded ? 'افزوده شد' : 'افزودن به سبد' }}</span>
              <span class="add-circle"><Check v-if="justAdded" :size="15" /><Plus v-else :size="16" /></span>
            </button>
            <span v-if="isTemporarilyUnavailable" class="unavailable-pill">ناموجود</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ════ LAYOUT: list ════ -->
    <template v-else-if="layout === 'list'">
      <a class="list-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="list-img" loading="lazy" :class="{ 'img-dimmed': isTemporarilyUnavailable }" />
        <span class="prep-badge list-prep-badge" v-if="item.prep_time_mins">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          {{ item.prep_time_mins }} دقیقه
        </span>
        <span class="unavailable-badge list-badge" v-if="isTemporarilyUnavailable">ناموجود</span>
      </a>
      <div class="list-body">
        <div class="list-labels" v-if="visibleTags.length">
          <span class="mini-pill tag-pill" v-for="tag in visibleTags" :key="`list-${tag}`">{{ tag }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || '' }}</p>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="list-foot">
          <div v-if="isComingSoon">
            <strong class="price stock-out-label" v-if="unavailableReason">{{ unavailableReason }}</strong>
            <strong class="price soon-label" v-else>به‌زودی</strong>
          </div>
          <div v-else>
            <strong class="price" :class="{ 'price-strikethrough': isTemporarilyUnavailable }">{{ displayBasePriceText }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="qty-pill compact" v-if="cartQty > 0 && !hasCustomization && !isUnavailable">
            <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)"><Minus :size="13" /></button>
            <strong>{{ cartQty }}</strong>
            <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)"><Plus :size="13" /></button>
          </div>
          <button v-if="showBomButton" class="bom-btn btn-sm" type="button" :aria-label="`مشاهده BOM ${item.title}`" @click.prevent="handleBomPreview">
            <Layers :size="13" />
            BOM
          </button>
          <button v-if="isCustomizable && !isTemporarilyUnavailable" class="add-btn customize-btn" type="button" :aria-label="`سفارشی‌سازی ${item.title}`" @click.prevent="handleCustomize">
            <span class="add-icon"><Pencil :size="15" /></span>
          </button>
          <button v-else-if="!isUnavailable" class="add-btn" type="button" :class="{ added: justAdded }" :aria-label="`افزودن ${item.title} به سبد`" @click.prevent="handleAdd">
            <span class="add-icon"><Check v-if="justAdded" :size="16" /><Plus v-else :size="17" /></span>
          </button>
        </div>
      </div>
    </template>

    <!-- ════ LAYOUT: grid ════ -->
    <template v-else>
      <a class="grid-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="grid-img" loading="lazy" :class="{ 'img-dimmed': isTemporarilyUnavailable }" />
        <span class="coming-soon-ribbon stock-out-ribbon" v-if="unavailableReason">{{ unavailableReason }}</span>
        <span class="coming-soon-ribbon" v-else-if="isComingSoon">به‌زودی</span>
        <span class="prep-badge grid-prep-badge" v-if="item.prep_time_mins">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          {{ item.prep_time_mins }} دقیقه
        </span>
        <span class="unavailable-badge grid-badge" v-if="isTemporarilyUnavailable">ناموجود</span>
        <button class="like-btn grid-like" type="button" :aria-label="`علاقه‌مندی`" @click.prevent="toggleLike">
          <svg width="17" height="17" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
      </a>
      <div class="grid-body">
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || 'توضیحی ثبت نشده.' }}</p>
        <div class="tag-row" v-if="visibleTags.length">
          <span class="mini-pill tag-pill" v-for="tag in visibleTags" :key="`grid-${tag}`">{{ tag }}</span>
        </div>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="grid-foot">
          <div v-if="isComingSoon">
            <strong class="price stock-out-label" v-if="unavailableReason">{{ unavailableReason }}</strong>
            <strong class="price soon-label" v-else>به‌زودی</strong>
          </div>
          <div v-else>
            <strong class="price" :class="{ 'price-strikethrough': isTemporarilyUnavailable }">{{ displayBasePriceText }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="foot-actions">
            <button v-if="showBomButton" type="button" class="bom-btn btn-sm" @click.prevent="handleBomPreview" :aria-label="`مشاهده BOM ${item.title}`">
              <Layers :size="13" />
              BOM
            </button>
            <a :href="`/item/${item.slug}`" class="detail-link">جزئیات</a>
            <div class="qty-pill compact" v-if="cartQty > 0 && !hasCustomization && !isUnavailable">
              <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)"><Minus :size="13" /></button>
              <strong>{{ cartQty }}</strong>
              <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)"><Plus :size="13" /></button>
            </div>
            <button v-if="isCustomizable && !isTemporarilyUnavailable" class="add-btn customize-btn" type="button" :aria-label="`سفارشی‌سازی ${item.title}`" @click.prevent="handleCustomize">
              <span class="add-icon"><Pencil :size="15" /></span>
            </button>
            <button v-else-if="!isUnavailable" class="add-btn" type="button" :class="{ added: justAdded, loading: isAdding }" :aria-label="`افزودن ${item.title} به سبد`" @click.prevent="handleAdd">
              <span class="add-icon"><Check v-if="justAdded" :size="16" /><Plus v-else :size="17" /></span>
            </button>
          </div>
        </div>
        <small class="review-badge" v-if="reviewCount > 0"><Star :size="12" /> {{ reviewCount }} نظر</small>
      </div>
    </template>
  </article>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatMoney } from '@/utils/format'
import { getReviewCount } from '@/utils/reviewsStore'
import { Check, Layers, Minus, Pencil, Plus, Star } from 'lucide-vue-next'

const props = defineProps({
  item: { type: Object, required: true },
  currency: { type: String, default: 'TOMAN' },
  canViewBom: { type: Boolean, default: false },
  cartQty: { type: Number, default: 0 },
  layout: {
    type: String,
    default: 'compact',
    validator: (v) => ['featured', 'list', 'grid', 'compact'].includes(v),
  },
  theme: { type: Object, default: () => ({}) },
})

const showBomButton = computed(() => props.canViewBom && Number(props.item?.has_bom) === 1)

function handleBomPreview() {
  emit('bom-preview', props.item)
}

const emit = defineEmits(['quick-add', 'quick-increase', 'quick-decrease', 'bom-preview'])
const justAdded = ref(false)
const isAdding = ref(false)
const liked = ref(false)
let addTimer = null
onUnmounted(() => { clearTimeout(addTimer) })

// Wishlist persistence
const WISHLIST_KEY = 'restaurant_wishlist_v1'
function loadWishlist() {
  try { return JSON.parse(localStorage.getItem(WISHLIST_KEY) || '[]') } catch (_) { return [] }
}
function saveWishlist(list) {
  try { localStorage.setItem(WISHLIST_KEY, JSON.stringify(list)) } catch (_) {}
}
function toggleLike() {
  const slug = props.item?.slug || ''
  if (!slug) return
  const list = loadWishlist()
  const idx = list.indexOf(slug)
  if (idx >= 0) { list.splice(idx, 1); liked.value = false }
  else { list.push(slug); liked.value = true }
  saveWishlist(list)
}

onMounted(() => {
  const slug = props.item?.slug || ''
  liked.value = slug ? loadWishlist().includes(slug) : false
})

// Review count
const reviewCount = computed(() => getReviewCount(props.item?.slug || ''))

function handleAdd() {
  if (isComingSoon.value) return
  emit('quick-add', props.item)
  justAdded.value = true
  isAdding.value = true
  clearTimeout(addTimer)
  addTimer = setTimeout(() => { justAdded.value = false; isAdding.value = false }, 1800)
}

// Dynamic theme colors — read from site management settings
const cardStyle = computed(() => {
  const t = props.theme || {}
  return {
    '--color-primary': t.primary_color || t.primary || 'var(--accent-gold)',
    '--color-primary-dark': t.primary_color_dark || t.primary_dark || 'var(--accent-gold80)',
    '--color-accent': t.accent_color || t.accent || 'var(--accent-green)',
    '--color-text-primary': t.text_primary || 'var(--text-primary)',
    '--color-text-secondary': t.text_secondary || 'var(--text-secondary)',
    '--color-text-muted': t.text_muted || 'var(--text-muted)',
    '--color-surface': t.surface || '#ffffff',
    '--color-surface-alt': t.surface_alt || 'var(--theme-surface-alt)',
    '--color-border': t.border || 'var(--glass-border)',
    '--color-success': t.success || 'var(--success, var(--accent-green))',
    '--color-success-bg': t.success_bg || 'var(--accent-green20)',
    '--add-btn-bg': t.add_btn_bg || t.primary_color || 'var(--accent-gold)',
  }
})

const resolvedImage = computed(
  () => props.item.image || '/NooshYar%20Image.png',
)

const visibleTags = computed(() => {
  const rows = Array.isArray(props.item?.tags) ? props.item.tags : []
  return rows
    .map((tag) => String(tag || '').trim())
    .filter(Boolean)
    .slice(0, 1)
})

const nutritionText = computed(() => {
  const kcal = Number(props.item?.nutrition?.kcal ?? props.item?.nutrition_kcal ?? 0)
  const protein = Number(props.item?.nutrition?.protein_g ?? props.item?.nutrition_protein_g ?? 0)
  const parts = []
  if (Number.isFinite(kcal) && kcal > 0) parts.push(`${Math.round(kcal).toLocaleString('fa-IR')} کیلوکالری`)
  if (Number.isFinite(protein) && protein > 0) parts.push(`${Math.round(protein).toLocaleString('fa-IR')} گرم پروتئین`)
  return parts.join(' • ')
})

const hasCustomization = computed(() => Number(props.item?.has_customization || 0) === 1)
const isComingSoon = computed(() => Number(props.item?.coming_soon ?? props.item?.restaurant_coming_soon ?? 0) === 1)
const isStockOut = computed(() => Number(props.item?.stock_out || 0) === 1)
const isOutOfStock = computed(() => Number(props.item?.out_of_stock ?? props.item?.restaurant_out_of_stock ?? 0) === 1)
const unavailableReason = computed(() => {
  if (isOutOfStock.value) return 'ناموجود'
  if (isStockOut.value) return 'اتمام'
  return ''
})
const isTemporarilyUnavailable = computed(() => {
  if (Number(props.item?.is_temporarily_unavailable || 0) !== 1) return false
  const until = props.item?.unavailable_until || ''
  if (!until) return true
  const untilDate = new Date(until)
  return untilDate > new Date()
})
const isUnavailable = computed(() => isComingSoon.value || isTemporarilyUnavailable.value)
const isCustomizable = computed(() =>
  Number(props.item?.restaurant_is_customizable || 0) === 1 &&
  Number(props.item?.restaurant_builder_active || 1) === 1,
)
const displayBasePriceText = computed(() => {
  const basePrice = formatMoney(props.item?.base_price || 0, props.currency)
  return isCustomizable.value ? `از ${basePrice}` : basePrice
})

function handleCustomize() {
  if (!props.item?.slug) return
  window.location.href = `/item/${props.item.slug}`
}
</script>

<style scoped>
/* ─── Shared ─── */
.product-card { position: relative; overflow: hidden; }

.product-card.is-added {
  outline: 2px solid var(--color-success, #2e7d32);
  outline-offset: 2px;
}

.price { font-size: 1.05rem; font-weight: 700; color: var(--ink-900, #141210); font-variant-numeric: tabular-nums; }
.soon-label {
  font-size: 0.95rem;
  color: var(--text-muted, #7a6e64);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.desc  { margin: 0; font-size: 0.79rem; line-height: 1.55; }
.muted { color: var(--text-muted, #7a6e64); }
.foot-actions { display: flex; align-items: center; gap: 0.42rem; }
.nutrition-line { margin: 0.22rem 0 0; font-size: 0.72rem; color: var(--text-muted, #7a6e64); line-height: 1.6; }
.in-cart-badge { display: block; margin-top: 0.12rem; font-size: 0.68rem; color: var(--accent-green, #2f6f5c); }

.mini-pill {
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.16);
  padding: 0.16rem 0.48rem;
  font-size: 0.67rem;
  color: var(--ink-600, #4a4038);
}
.mini-pill.tag-pill { background: rgb(var(--palette-deep-sapphire-rgb) / 0.12); color: rgb(var(--palette-deep-sapphire-rgb) / 1); }

.tag-row { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.2rem; }

/* Like button */
.like-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 1.5px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgb(var(--palette-eggshell-rgb) / 0.74);
  color: var(--accent-gold);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.18s ease;
  flex-shrink: 0;
}
.like-btn:hover { background: rgb(var(--palette-deep-saffron-rgb) / 0.14); transform: scale(1.1); }

/* Glass-style add button */
.add-btn {
  width: 42px; height: 42px;
  border-radius: 14px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-eggshell-rgb) / 0.92);
  backdrop-filter: blur(8px);
  color: var(--palette-deep-sapphire);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 14px rgb(var(--palette-deep-sapphire-rgb) / 0.10);
  transition: background 0.22s ease,
              transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.22s ease;
  flex-shrink: 0;
}
.add-btn:hover {
  background: rgb(var(--palette-eggshell-rgb) / 1);
  box-shadow: 0 6px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  transform: scale(1.08);
}
.add-btn:active {
  transform: scale(0.94);
  box-shadow: 0 2px 8px rgb(var(--palette-deep-sapphire-rgb) / 0.10);
}
.add-btn.added {
  background: var(--palette-deep-sapphire);
  color: #fff;
  border-color: var(--palette-deep-sapphire);
  box-shadow: 0 4px 16px rgb(var(--palette-deep-sapphire-rgb) / 0.30);
}
.add-btn:focus-visible {
  outline: 2px solid var(--palette-deep-saffron);
  outline-offset: 2px;
}

.add-icon {
  font-size: 1.35rem; line-height: 1;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.add-btn.added .add-icon { transform: scale(1.25); }

/* Pill variant (featured) */
.add-btn--pill {
  width: auto; border-radius: 22px;
  padding: 0 1.2rem 0 1.4rem;
  font-size: 0.88rem; font-family: inherit; font-weight: 600;
  height: 44px;
  gap: 0.55rem;
}
.add-btn--pill .add-circle {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.10);
  color: var(--palette-deep-sapphire);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
  transition: background 0.22s ease, color 0.22s ease;
}
.add-btn--pill.added .add-circle {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .add-btn,
  .add-btn .add-icon {
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
  }
  .add-btn:hover,
  .add-btn:active {
    transform: none;
  }
  .add-btn.loading .add-icon {
    animation: none;
  }
}
/* Mobile: smaller touch target */
@media (max-width: 768px) {
  .add-btn {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }
  .add-btn--pill {
    height: 42px;
    padding: 0 1rem 0 1.2rem;
    font-size: 0.82rem;
  }
}

/* customize button */
.customize-btn {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
}
.customize-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb));
}
.customize-btn.btn-sm {
  padding: 0 0.5rem;
  height: 32px;
  font-size: 0.78rem;
}
.customize-btn.btn-sm .add-icon {
  font-size: 1rem;
}
.detail-link {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  padding: 0.3rem 0.72rem;
  font-size: 0.76rem; color: var(--ink-600, #4a4038);
  text-decoration: none;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  transition: background 0.18s ease;
}
.detail-link:hover { background: rgb(var(--palette-eggshell-rgb) / 0.92); }

/* BOM button */
.bom-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.34);
  padding: 0.3rem 0.72rem;
  font-size: 0.76rem;
  font-weight: 600;
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  transition: background 0.18s ease, box-shadow 0.18s ease;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.4;
}
.bom-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  box-shadow: 0 2px 8px rgb(var(--palette-deep-sapphire-rgb) / 0.15);
}
.bom-btn:active {
  transform: scale(0.96);
}
.bom-btn.btn-sm {
  padding: 0.22rem 0.55rem;
  font-size: 0.7rem;
  height: 30px;
}
.bom-btn.bom-btn--compact {
  width: 36px;
  height: 36px;
  padding: 0;
  justify-content: center;
  border-radius: 13px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  font-size: 0;
}
.bom-btn.bom-btn--compact:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}
.bom-btn.bom-btn--compact svg {
  margin: 0;
}

.bom-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.34);
  padding: 0.3rem 0.72rem;
  font-size: 0.76rem;
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
  text-decoration: none;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  transition: background 0.18s ease;
  cursor: pointer;
  font-family: inherit;
}
.bom-link:hover { background: rgb(var(--palette-eggshell-rgb) / 0.92); }

.qty-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgb(var(--palette-eggshell-rgb) / 0.78);
  padding: 0.2rem 0.35rem;
  min-height: 36px;
}

.qty-pill.compact,
.qty-pill--compact {
  min-height: 34px;
}

.qty-pill--compact {
  flex-direction: column-reverse;
  gap: 0.18rem;
  padding: 0.28rem 0.2rem;
  border-radius: 16px;
}

.qty-pill--compact strong {
  font-size: 0.76rem;
  line-height: 1;
  color: var(--color-accent, var(--accent-green));
}

.qty-step {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.38);
  background: #fff;
  color: var(--ink-800, #1e1a17);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.qty-pill--compact .qty-step {
  width: 24px;
  height: 24px;
  font-size: 0.92rem;
}

/* ─── LAYOUT: compact (modern healthy food card) ─── */
.layout--compact {
  display: grid;
  grid-template-columns: 102px minmax(0, 1fr) 34px;
  gap: 10px;
  align-items: center;
  direction: rtl;
  background: var(--color-surface, #ffffff);
  border-radius: 22px;
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.07);
  border: 1px solid var(--color-border, var(--glass-border));
  padding: 12px;
  min-height: 132px;
  position: relative;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.layout--compact:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 30px rgb(var(--palette-deep-sapphire-rgb) / 0.10);
}

/* Image column (rightmost in RTL — grid column 1) */
.compact-image-col {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-width: 0;
  text-decoration: none;
}

.card-title-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.card-image {
  width: 100%;
  max-width: 102px;
  height: 102px;
  object-fit: contain;
  border-radius: 16px;
  flex-shrink: 0;
  background: transparent;
  box-shadow: none;
}

/* Content column (center — grid column 2) */
.compact-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  text-align: right;
  overflow: hidden;
  gap: 3px;
}

/* Actions column (leftmost in RTL — grid column 3) */
.compact-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
  align-self: stretch;
}

/* Pill chips */
.pills-row {
  display: flex;
  gap: 5px;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-bottom: 2px;
}

.pill {
  display: inline-block;
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 9.5px;
  font-weight: 700;
  line-height: 1.35;
  flex-shrink: 0;
}

.pill--tag {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

/* Title */
.card-title {
  font-size: 15px;
  font-weight: 900;
  color: var(--color-accent, var(--accent-green));
  text-align: right;
  line-height: 1.35;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-width: 100%;
}

/* Description */
.card-description {
  font-size: 11px;
  color: var(--color-text-secondary, var(--text-secondary));
  text-align: right;
  line-height: 1.48;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Nutrition row */
.card-nutrition {
  font-size: 10px;
  color: var(--color-text-muted, var(--text-muted));
  text-align: right;
  white-space: normal;
  max-width: 100%;
  font-variant-numeric: tabular-nums;
  line-height: 1.55;
}

/* Price */
.card-price-row {
  margin-top: auto;
}

.card-price {
  font-size: 14px;
  font-weight: 900;
  color: var(--color-accent, var(--accent-green));
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.card-price.soon-label {
  font-size: 14px;
  color: var(--text-muted, #7a6e64);
  font-weight: 600;
}

/* Add button — compact accent */
.add-btn {
  width: 36px;
  height: 36px;
  background: var(--add-btn-bg, var(--accent-gold));
  color: #ffffff;
  border: none;
  border-radius: 13px;
  box-shadow: 0 8px 16px rgb(var(--palette-deep-saffron-rgb) / 0.22);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 500;
  transition: all 0.15s ease-out;
  flex-shrink: 0;
}

.add-btn:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.add-btn:active {
  transform: scale(0.95);
  filter: brightness(0.95);
}

.add-btn.added {
  background: var(--color-accent, var(--accent-green));
  box-shadow: 0 4px 16px rgb(var(--palette-deep-sapphire-rgb) / 0.25);
}

.add-icon {
  font-size: 17px;
  line-height: 1;
  font-weight: 500;
}

/* Unavailable badge */
.unavailable-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  right: auto;
  border-radius: 999px;
  background: var(--accent-red, #dc2626);
  color: #fff;
  padding: 0.15rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 700;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.img-dimmed { opacity: 0.65; }
.price-strikethrough { text-decoration: line-through; opacity: 0.6; }

/* ─── Responsive: compact layout ─── */
@media (max-width: 600px) {
  .layout--compact {
    grid-template-columns: 86px minmax(0, 1fr) 32px;
    min-height: 122px;
    padding: 10px;
    gap: 8px;
    border-radius: 20px;
  }

  .compact-image-col {
    flex: 0 0 auto;
  }

  .card-image {
    max-width: 86px;
    height: 86px;
    border-radius: 16px;
  }

  .card-title {
    font-size: 13.5px;
  }

  .card-description {
    font-size: 10px;
    -webkit-line-clamp: 1;
  }

  .card-price {
    font-size: 13px;
  }

  .add-btn {
    width: 36px;
    height: 36px;
    border-radius: 13px;
  }

  .add-icon {
    font-size: 17px;
  }

  .pill {
    font-size: 9.5px;
    padding: 3px 6px;
  }

  .card-nutrition {
    font-size: 9.5px;
  }
}

@media (max-width: 360px) {
  .layout--compact {
    grid-template-columns: 76px minmax(0, 1fr) 30px;
    min-height: 112px;
    padding: 9px;
    gap: 6px;
  }

  .card-image {
    max-width: 76px;
    height: 76px;
  }

  .card-description {
    -webkit-line-clamp: 1;
  }
}

/* ─── LAYOUT: featured ─── */
.layout--featured {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 42px;
  box-shadow: 0 20px 44px rgb(15 23 42 / 0.1);
  display: flex; flex-direction: column;
}

.featured-cover {
  display: block;
  height: 280px;
  border-radius: 42px 42px 0 0;
  overflow: hidden;
  position: relative;
  text-decoration: none;
}

.featured-img {
  width: 100%; height: 100%;
  object-fit: contain;
  object-position: center;
  background: transparent;
  transition: transform 0.38s ease;
  transform-origin: center 45%;
}
.layout--featured:hover .featured-img { transform: scale(1.05); }

.prep-badge {
  position: absolute; top: 0.75rem; left: 0.75rem;
  border-radius: 999px;
  background: #fff;
  padding: 0.28rem 0.72rem;
  font-size: 0.72rem; font-weight: 600; color: var(--ink-700, #2e2820);
  display: flex; align-items: center; gap: 0.3rem;
  z-index: 2;
}

.list-prep-badge {
  top: 0.5rem; left: 0.5rem;
  padding: 0.2rem 0.55rem;
  font-size: 0.68rem;
}

.grid-prep-badge {
  top: 0.5rem; left: 0.5rem;
  padding: 0.2rem 0.55rem;
  font-size: 0.68rem;
}

.featured-body {
  padding: 1.1rem 1.2rem 1.3rem;
  display: flex; flex-direction: column; gap: 0.42rem;
}
.featured-body h3 {
  margin: 0; font-size: 1.5rem; font-weight: 700; line-height: 1.2;
  color: var(--ink-900, #141210);
}
.featured-foot {
  margin-top: 0.4rem;
  display: flex; align-items: flex-end; justify-content: space-between; gap: 0.6rem;
}
.featured-foot .price { font-size: 1.35rem; }
.featured-foot small { display: block; font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.1rem; }

/* ─── LAYOUT: list ─── */
.layout--list {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 24px;
  box-shadow: 0 14px 36px #19282229;
  display: grid; grid-template-columns: 120px 1fr;
  gap: 0.75rem; padding: 0.75rem;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.layout--list:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 40px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.list-cover { display: block; width: 90px; height: 100%; border-radius: 18px; overflow: hidden; }

.list-img {
  width: 95% ;
  height:95% ;
  object-fit: contain ;
  object-position: center;
  background: transparent;
  border-radius: 18px ;
  transition: transform 0.28s ease ;
}

.layout--list:hover .list-img { transform: scale(1.02); }

.list-body { display: flex; flex-direction: column; gap: 0.22rem; min-width: 0; }
.list-labels { display: flex; gap: 0.28rem; flex-wrap: wrap; }
.list-body h3 { margin: 0; font-size: 0.97rem; font-weight: 700; color: var(--ink-900); }
.list-body .desc { min-height: 1.8rem; }
.list-foot {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: auto; padding-top: 0.2rem;
}

/* ─── LAYOUT: grid ─── */
.layout--grid {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 32px;
  box-shadow: 0 24px 56px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  display: flex; flex-direction: column;
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}
.layout--grid:hover {
  transform: translateY(-4px);
  box-shadow: 0 32px 72px rgb(var(--palette-deep-sapphire-rgb) / 0.22);
}

.grid-cover {
  position: relative; height: 190px;
  border-radius: 32px 32px 0 0; overflow: hidden;
  display: block; text-decoration: none;
}
.grid-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  background: transparent;
  transition: transform 0.34s ease;
}
.layout--grid:hover .grid-img { transform: scale(1.05); }

.grid-body {
  padding: 0.9rem; display: flex; flex-direction: column;
  gap: 0.28rem; flex: 1;
}
.grid-body h3 { margin: 0; font-size: 1.05rem; font-weight: 700; color: var(--ink-900); }
.grid-body .desc { flex: 1; min-height: 2.4rem; }
.grid-foot {
  display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;
}

/* ─── Coming soon ribbon ─── */
.stock-out-badge {
  background: var(--mg-danger, #a6543f) !important;
  color: #fff !important;
}

.stock-out-label {
  color: var(--mg-danger, #a6543f) !important;
}

.stock-out-ribbon {
  background: var(--mg-danger, #a6543f) !important;
  color: #fff !important;
}

.coming-soon-ribbon {
  position: absolute; top: 0.6rem; left: 0.6rem;
  border-radius: 999px; padding: 0.18rem 0.65rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.85);
  color: #fff;
  font-size: 0.68rem; font-weight: 700;
  z-index: 2;
}

/* ─── Grid like button ─── */
.grid-like {
  position: absolute; top: 0.5rem; right: 0.5rem;
  z-index: 2;
  width: 34px; height: 34px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(4px);
}

/* ─── Review badge ─── */
.review-badge {
  display: block;
  font-size: 0.68rem;
  color: var(--text-muted, #7a6e64);
  margin-top: 0.25rem;
}

/* ─── Add button loading state ─── */
.add-btn.loading {
  pointer-events: none;
  opacity: 0.7;
}
.add-btn.loading .add-icon {
  display: inline-block;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ─── Unavailable state ─── */
.img-dimmed { opacity: 0.65; }
.price-strikethrough { text-decoration: line-through; opacity: 0.6; }

.unavailable-badge {
  position: absolute;
  top: 0.6rem;
  left: 0.6rem;
  border-radius: 999px;
  background: var(--accent-red, #dc2626);
  color: #fff;
  padding: 0.2rem 0.6rem;
  font-size: 0.72rem;
  font-weight: 700;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.unavailable-badge.list-badge {
  top: 0.5rem;
  left: 0.5rem;
}

.unavailable-badge.grid-badge {
  top: 0.5rem;
  left: 0.5rem;
}

.unavailable-pill {
  border-radius: 999px;
  background: rgb(var(--danger-rgb) / 0.12);
  color: var(--danger);
  padding: 0.25rem 0.6rem;
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  height: 36px;
}
</style>
