<template>
  <teleport to="body">
    <transition name="overlay-fade">
      <div
        v-if="open"
        class="preview-overlay"
        :class="{ 'is-mobile': isMobile }"
        @click.self="close"
      >
        <transition :name="isMobile ? 'sheet-enter' : 'modal-enter'" appear>
          <div
            v-if="open"
            class="preview-panel"
            :class="{ 'is-mobile': isMobile }"
            ref="panelRef"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="'preview-title-' + (product?.slug || 'modal')"
            dir="rtl"
          >
            <!-- Header -->
            <PreviewHeader
              :title="product?.title || 'افزودن به سبد'"
              :loading="loading"
              @close="close"
              @back="close"
            />

            <!-- Loading Skeleton -->
            <div v-if="loading" class="preview-body preview-body--loading">
              <div class="skeleton-hero">
                <div class="skeleton-image shimmer"></div>
                <div class="skeleton-content">
                  <div class="skeleton-badge shimmer"></div>
                  <div class="skeleton-title shimmer"></div>
                  <div class="skeleton-text shimmer"></div>
                  <div class="skeleton-text shimmer short"></div>
                </div>
              </div>
              <div class="skeleton-qty shimmer"></div>
              <div class="skeleton-section-title shimmer"></div>
              <div class="skeleton-grid">
                <div v-for="n in 4" :key="n" class="skeleton-card shimmer"></div>
              </div>
              <div class="skeleton-footer">
                <div class="skeleton-price shimmer"></div>
                <div class="skeleton-cta shimmer"></div>
              </div>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="preview-body preview-body--error">
              <svg class="error-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <p class="error-title">خطا در بارگذاری اطلاعات محصول</p>
              <p class="error-msg">{{ error }}</p>
              <button class="error-retry" type="button" @click="$emit('retry')">تلاش مجدد</button>
            </div>

            <!-- Content -->
            <div v-else class="preview-body">
              <!-- Hero Card -->
              <HeroCard
                v-if="product"
                :product="product"
                :mobile="isMobile"
              />

              <!-- Quantity Selector -->
              <QuantitySelector
                v-model="quantity"
                :min="1"
                :max="99"
                :disabled="adding"
              />

              <!-- Ingredients Section -->
              <section v-if="ingredients.length" class="preview-section">
                <h3 class="section-heading">
                  مواد اولیه
                  <span class="section-count">{{ ingredients.length }} ماده</span>
                </h3>

                <IngredientSearch
                  v-model="searchQuery"
                  placeholder="جستجوی ماده..."
                />

                <IngredientGrid
                  :ingredients="filteredIngredients"
                  :columns="2"
                />

                <p v-if="!filteredIngredients.length" class="no-results">
                  ماده‌ای با این نام یافت نشد
                </p>
              </section>

              <!-- Empty ingredients -->
              <p v-else class="no-ingredients">
                مواد اولیه برای این محصول ثبت نشده است
              </p>

              <!-- Nutrition Summary -->
              <NutritionSummary
                v-if="product?.nutrition"
                :nutrition="product.nutrition"
              />
            </div>

            <!-- Footer -->
            <PreviewFooter
              v-if="!error"
              :price="product?.price || 0"
              :currency="product?.currency || 'TOMAN'"
              :quantity="quantity"
              :adding="adding"
              :disabled="loading"
              @add-to-cart="onAddToCart"
            />
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import PreviewHeader from './PreviewHeader.vue'
import HeroCard from './HeroCard.vue'
import QuantitySelector from './QuantitySelector.vue'
import IngredientSearch from './IngredientSearch.vue'
import IngredientGrid from './IngredientGrid.vue'
import NutritionSummary from './NutritionSummary.vue'
import PreviewFooter from './PreviewFooter.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  product: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
})

const emit = defineEmits(['close', 'add-to-cart', 'update:open', 'retry'])

const quantity = ref(1)
const adding = ref(false)
const searchQuery = ref('')
const panelRef = ref(null)
const isMobile = ref(false)

// Check mobile on mount and resize
function checkMobile() {
  isMobile.value = window.matchMedia('(max-width: 767px)').matches
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// Reset state when modal opens
watch(() => props.open, (val) => {
  if (val) {
    quantity.value = 1
    searchQuery.value = ''
    adding.value = false
    document.body.style.overflow = 'hidden'
    // Focus trap: focus the panel
    nextTick(() => {
      const el = panelRef.value
      if (el) {
        el.focus({ preventScroll: true })
      }
    })
  } else {
    document.body.style.overflow = ''
  }
})

// Escape key handler
function onKeydown(e) {
  if (e.key === 'Escape' && props.open) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

// Focus trap
function onTab(e) {
  if (!panelRef.value) return
  const focusable = panelRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onTab)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onTab)
})

// Computed
const ingredients = computed(() => props.product?.ingredients || [])

const filteredIngredients = computed(() => {
  if (!searchQuery.value) return ingredients.value
  const q = searchQuery.value.trim().toLowerCase()
  return ingredients.value.filter(i =>
    i.name?.toLowerCase().includes(q) ||
    i.description?.toLowerCase().includes(q)
  )
})

// Methods
function close() {
  emit('close')
  emit('update:open', false)
}

function onAddToCart() {
  adding.value = true
  emit('add-to-cart', {
    product: props.product,
    quantity: quantity.value,
  })
}
</script>

<style>
/* Overlay */
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 150;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.preview-overlay.is-mobile {
  align-items: flex-end;
  padding: 0;
}

/* Panel */
.preview-panel {
  width: min(100vw - 24px, 920px);
  max-height: calc(100dvh - 2rem);
  border-radius: var(--preview-radius);
  background: var(--preview-surface);
  box-shadow: var(--preview-shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  outline: none;
}

.preview-panel.is-mobile {
  width: 100%;
  max-height: 90dvh;
  border-radius: var(--preview-radius) var(--preview-radius) 0 0;
}

/* Body */
.preview-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding: 1.25rem;
}

.preview-body--loading {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.preview-body--error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 1.5rem;
  gap: 0.75rem;
}

/* Section heading */
.preview-section {
  margin-top: 1rem;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--preview-text);
  margin: 0.75rem 0 0;
}

.section-count {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--preview-muted);
  background: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.1);
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
}

/* No results / empty */
.no-results,
.no-ingredients {
  text-align: center;
  color: var(--preview-muted);
  font-size: 0.88rem;
  padding: 2rem 1rem;
}

/* Error state */
.error-icon {
  color: var(--danger, #dc2626);
}

.error-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--preview-text);
  margin: 0;
}

.error-msg {
  font-size: 0.82rem;
  color: var(--preview-muted);
  margin: 0;
}

.error-retry {
  margin-top: 0.5rem;
  padding: 0.55rem 1.5rem;
  border: none;
  border-radius: 999px;
  background: var(--preview-primary);
  color: var(--preview-on-accent);
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.error-retry:hover {
  filter: brightness(1.1);
}

.error-retry:focus-visible {
  outline: 2px solid var(--preview-primary);
  outline-offset: 2px;
}

/* ── Skeleton ── */
.skeleton-hero {
  display: grid;
  grid-template-columns: minmax(0, 55%) minmax(0, 45%);
  gap: 1.25rem;
  direction: rtl;
}

.skeleton-image {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: var(--preview-radius-sm);
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding-top: 0.5rem;
}

.skeleton-badge {
  width: 60px;
  height: 22px;
  border-radius: 999px;
}

.skeleton-title {
  width: 80%;
  height: 24px;
  border-radius: 8px;
}

.skeleton-text {
  width: 100%;
  height: 14px;
  border-radius: 6px;
}

.skeleton-text.short {
  width: 60%;
}

.skeleton-qty {
  height: 48px;
  border-radius: 999px;
}

.skeleton-section-title {
  width: 40%;
  height: 20px;
  border-radius: 6px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.skeleton-card {
  height: 160px;
  border-radius: var(--preview-radius-sm);
}

.skeleton-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 0;
  gap: 1rem;
}

.skeleton-price {
  width: 100px;
  height: 40px;
  border-radius: 12px;
}

.skeleton-cta {
  width: 140px;
  height: 48px;
  border-radius: 999px;
}

.shimmer {
  background: linear-gradient(90deg, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.06) 25%, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.12) 50%, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* ── Animations ── */
/* Overlay fade */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.15s ease;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

/* Modal enter (desktop) */
.modal-enter-enter-active {
  animation: modal-enter 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.modal-enter-leave-active {
  animation: modal-exit 0.15s ease-in forwards;
}

@keyframes modal-enter {
  from { opacity: 0; transform: scale(0.95) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes modal-exit {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.96) translateY(8px); }
}

/* Sheet enter (mobile bottom sheet) */
.sheet-enter-enter-active {
  animation: sheet-enter 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.sheet-enter-leave-active {
  animation: sheet-exit 0.15s ease-in forwards;
}

@keyframes sheet-enter {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
@keyframes sheet-exit {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .modal-enter-enter-active,
  .modal-enter-leave-active,
  .sheet-enter-enter-active,
  .sheet-enter-leave-active,
  .overlay-fade-enter-active,
  .overlay-fade-leave-active {
    animation: none !important;
    transition: none !important;
  }
  .shimmer {
    animation: none !important;
    background: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.08);
  }
}

/* Mobile adjustments */
@media (max-width: 767px) {
  .preview-panel {
    max-height: 90dvh;
  }
  .preview-body {
    padding: 0.75rem;
  }
  .section-heading {
    font-size: 0.95rem;
  }
}
</style>
