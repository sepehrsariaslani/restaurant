<template>
  <div class="bom-preview-page" dir="rtl">
    <!-- Permission denied state -->
    <BomPermissionDenied v-if="!hasAccess && !loading" />

    <!-- Main content (authorized users only) -->
    <template v-else>
      <!-- Loading skeleton -->
      <div class="bom-preview-skeleton" v-if="loading">
        <div class="skeleton-top-bar shimmer"></div>
        <div class="skeleton-hero shimmer"></div>
        <div class="skeleton-info">
          <div class="skeleton-line shimmer" style="width: 30%"></div>
          <div class="skeleton-line shimmer" style="width: 70%"></div>
          <div class="skeleton-line shimmer" style="width: 40%"></div>
          <div class="skeleton-line shimmer" style="width: 90%"></div>
          <div class="skeleton-line shimmer" style="width: 80%"></div>
          <div class="skeleton-line shimmer" style="width: 60%"></div>
        </div>
      </div>

      <!-- Error state -->
      <div class="bom-error-state" v-else-if="error">
        <svg class="error-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <p class="error-msg">{{ error }}</p>
        <div class="error-actions">
          <button class="retry-btn" @click="loadBomData" :disabled="loading">تلاش مجدد</button>
          <a href="/menu" class="back-link">بازگشت به منو</a>
        </div>
      </div>

      <!-- Empty state (no BOM) -->
      <div class="bom-empty-state" v-else-if="product && !product.has_bom">
        <svg class="empty-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        <h3>فرمول ساخت برای این محصول ثبت نشده است.</h3>
        <a href="/menu" class="back-link">بازگشت به منو</a>
      </div>

      <!-- Success state: full product + BOM view -->
      <div class="bom-content" v-else-if="product">
        <!-- Sticky top bar -->
        <div class="bom-top-bar">
          <a href="/menu" class="bom-back-link" aria-label="بازگشت به منو">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
            بازگشت به منو
          </a>
          <span class="bom-page-title">جزئیات محصول و فرمول ساخت</span>
        </div>

        <!-- Mobile layout -->
        <div class="bom-mobile-layout mobile-only">
          <!-- Product image -->
          <div class="bom-hero-image">
            <img :src="productImage" :alt="product.item_name" />
          </div>

          <!-- Product info -->
          <div class="bom-product-info">
            <p class="bom-category">{{ product.category || 'منو' }}</p>
            <h1 class="bom-product-title">{{ product.item_name }}</h1>

            <div class="bom-price-row">
              <span class="bom-price">{{ formatMoney(product.base_price, currency) }}</span>
            </div>

            <div class="bom-prep-time" v-if="product.prep_time_mins">
              <span class="prep-icon">⏱</span>
              <span>{{ product.prep_time_mins }} دقیقه</span>
            </div>

            <p class="bom-description" v-if="product.description">{{ product.description }}</p>

            <!-- Nutrition chips -->
            <div class="bom-nutrition-row" v-if="hasNutrition">
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.kcal">
                <small>کالری</small>
                <strong>{{ product.nutrition.kcal }} کیلوکالری</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.protein_g">
                <small>پروتئین</small>
                <strong>{{ product.nutrition.protein_g }}g</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.carb_g">
                <small>کربوهیدرات</small>
                <strong>{{ product.nutrition.carb_g }}g</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.fat_g">
                <small>چربی</small>
                <strong>{{ product.nutrition.fat_g }}g</strong>
              </div>
            </div>
          </div>

          <!-- Formula section -->
          <div class="bom-section" v-if="product.formula_description">
            <h3 class="bom-section-title">فرمول ساخت</h3>
            <p class="bom-formula-text">{{ product.formula_description }}</p>
          </div>

          <!-- Gramezh table -->
          <div class="bom-section" v-if="gramezh.length">
            <h3 class="bom-section-title">مواد اولیه (گرم)</h3>
            <GramezhTable :items="gramezh" :currency="currency" />
          </div>

          <!-- BOM Tree -->
          <div class="bom-section" v-if="bomTreeData.length">
            <h3 class="bom-section-title">ساختار مواد (BOM)</h3>
            <BomTree :nodes="bomTreeData" :depth="0" :default-expanded="true" />
          </div>

          <!-- Empty BOM tree message -->
          <div class="bom-section" v-else-if="product.has_bom">
            <h3 class="bom-section-title">ساختار مواد (BOM)</h3>
            <p class="bom-empty-bom">ماده‌ای در این BOM ثبت نشده است.</p>
          </div>

          <!-- Preparation notes -->
          <div class="bom-section" v-if="prepNotes">
            <h3 class="bom-section-title">یادداشت‌های آماده‌سازی</h3>
            <p class="bom-prep-text">{{ prepNotes }}</p>
          </div>
        </div>

        <!-- Desktop layout -->
        <div class="bom-desktop-layout desktop-only">
          <div class="bom-desktop-image-col">
            <div class="bom-desktop-image">
              <img :src="productImage" :alt="product.item_name" />
            </div>
          </div>
          <div class="bom-desktop-info-col">
            <a href="/menu" class="bom-desktop-back-link" aria-label="بازگشت به منو">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 18l-6-6 6-6" />
              </svg>
              بازگشت به منو
            </a>

            <p class="bom-category">{{ product.category || 'منو' }}</p>
            <h1 class="bom-product-title">{{ product.item_name }}</h1>

            <div class="bom-price-row">
              <span class="bom-price">{{ formatMoney(product.base_price, currency) }}</span>
            </div>

            <div class="bom-prep-time" v-if="product.prep_time_mins">
              <span class="prep-icon">⏱</span>
              <span>{{ product.prep_time_mins }} دقیقه</span>
            </div>

            <p class="bom-description" v-if="product.description">{{ product.description }}</p>

            <!-- Nutrition -->
            <div class="bom-nutrition-row" v-if="hasNutrition">
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.kcal">
                <small>کالری</small>
                <strong>{{ product.nutrition.kcal }} کیلوکالری</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.protein_g">
                <small>پروتئین</small>
                <strong>{{ product.nutrition.protein_g }}g</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.carb_g">
                <small>کربوهیدرات</small>
                <strong>{{ product.nutrition.carb_g }}g</strong>
              </div>
              <div class="nutri-chip" v-if="product.nutrition && product.nutrition.fat_g">
                <small>چربی</small>
                <strong>{{ product.nutrition.fat_g }}g</strong>
              </div>
            </div>

            <!-- Formula -->
            <div class="bom-section" v-if="product.formula_description">
              <h3 class="bom-section-title">فرمول ساخت</h3>
              <p class="bom-formula-text">{{ product.formula_description }}</p>
            </div>

            <!-- Gramezh -->
            <div class="bom-section" v-if="gramezh.length">
              <h3 class="bom-section-title">مواد اولیه (گرم)</h3>
              <GramezhTable :items="gramezh" :currency="currency" />
            </div>

            <!-- BOM Tree -->
            <div class="bom-section" v-if="bomTreeData.length">
              <h3 class="bom-section-title">ساختار مواد (BOM)</h3>
              <BomTree :nodes="bomTreeData" :depth="0" :default-expanded="true" />
            </div>

            <div class="bom-section" v-else-if="product.has_bom">
              <h3 class="bom-section-title">ساختار مواد (BOM)</h3>
              <p class="bom-empty-bom">ماده‌ای در این BOM ثبت نشده است.</p>
            </div>

            <!-- Prep notes -->
            <div class="bom-section" v-if="prepNotes">
              <h3 class="bom-section-title">یادداشت‌های آماده‌سازی</h3>
              <p class="bom-prep-text">{{ prepNotes }}</p>
            </div>

            <!-- Qty + Add to cart (desktop) -->
            <div class="bom-desktop-cart-row">
              <div class="qty-control">
                <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
                <span class="qty-num">{{ qty }}</span>
                <button class="qty-btn" type="button" @click="qty += 1">+</button>
              </div>
              <div class="bom-desktop-price">
                <small>قیمت کل</small>
                <strong>{{ formatMoney(product.base_price * qty, currency) }}</strong>
              </div>
              <button class="bom-add-btn" type="button" :disabled="isAdding" @click="addToCart">
                {{ addSuccess ? 'افزوده شد ✓' : 'افزودن به سبد' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Mobile sticky bottom bar -->
        <div class="bom-sticky-bottom mobile-only" v-if="product">
          <div class="bom-bottom-price">
            <small>قیمت</small>
            <strong>{{ formatMoney(product.base_price, currency) }}</strong>
          </div>
          <button class="bom-add-btn" type="button" :disabled="isAdding" @click="addToCart">
            {{ addSuccess ? 'افزوده شد ✓' : 'افزودن به سبد' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BomTree from '@/components/BomTree.vue'
import GramezhTable from '@/components/GramezhTable.vue'
import BomPermissionDenied from '@/components/BomPermissionDenied.vue'
import { getBomPreview } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { upsertLine } from '@/stores/cartStore'

const loading = ref(true)
const error = ref('')
const product = ref(null)
const bomTree = ref(null)
const gramezh = ref([])
const prepNotes = ref('')
const hasAccess = ref(false)
const isAdding = ref(false)
const addSuccess = ref(false)
const qty = ref(1)

const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60'

const productImage = computed(() => {
  const img = product.value?.image || ''
  return img || fallbackImage
})

const currency = computed(() => product.value?.currency || 'TOMAN')

const bomTreeData = computed(() => bomTree.value?.children || [])

const hasNutrition = computed(() => {
  const n = product.value?.nutrition
  return n && (n.kcal || n.protein_g || n.carb_g || n.fat_g)
})

function resolveProductSlug() {
  const pathname = String(window.location.pathname || '')
  return pathname.replace('/bom-preview/', '').replace(/^\/+|\/+$/g, '')
}

async function loadBomData() {
  const slug = resolveProductSlug()
  if (!slug) {
    error.value = 'آدرس محصول معتبر نیست.'
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await getBomPreview(slug)
    product.value = data.product || null
    bomTree.value = data.bom_tree || null
    gramezh.value = data.gramezh || []
    prepNotes.value = data.prep_notes || ''
  } catch (err) {
    error.value = err.message || 'دریافت اطلاعات محصول ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function addToCart() {
  if (!product.value) return
  isAdding.value = true
  try {
    upsertLine({
      item_slug: product.value.slug,
      item_title: product.value.item_name,
      item_image: product.value.image || '',
      base_price: product.value.base_price,
      qty: qty.value,
      unit_price_preview: product.value.base_price,
      line_total_preview: product.value.base_price * qty.value,
      customization: null,
      ingredient_catalog: [],
      modifier_groups_catalog: [],
    })
    addSuccess.value = true
    setTimeout(() => { addSuccess.value = false }, 2000)
  } catch (_) {
    // silently fail
  } finally {
    isAdding.value = false
  }
}

onMounted(() => {
  const user = (typeof window !== 'undefined' && (window.frappe?.session_user || window.frappe?.boot?.user?.name)) || ''
  hasAccess.value = Boolean(user && user !== 'Guest')
  if (hasAccess.value) {
    loadBomData()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.bom-preview-page {
  min-height: 100svh;
  background: var(--theme-background, #f6f1ea);
  direction: rtl;
  padding-bottom: max(5.5rem, calc(5.5rem + env(safe-area-inset-bottom)));
}

/* ─── Responsive visibility ─── */
.mobile-only { display: block; }
.desktop-only { display: none; }

@media (min-width: 768px) {
  .bom-preview-page {
    padding-bottom: 2rem;
  }
  .mobile-only { display: none !important; }
  .desktop-only { display: block; }
}

/* ─── Top bar ─── */
.bom-top-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--theme-border);
}

.bom-back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--ink-700);
  text-decoration: none;
  font-weight: 500;
}

.bom-page-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink-600);
}

/* ─── Skeleton ─── */
.bom-preview-skeleton {
  padding: 0;
}

.skeleton-top-bar {
  height: 52px;
  background: var(--surface-alt);
  margin-bottom: 0;
}

.skeleton-hero {
  width: 100%;
  height: 280px;
  background: var(--surface-alt);
}

.skeleton-info {
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: var(--surface-alt);
}

.shimmer {
  background: linear-gradient(90deg, var(--surface-alt) 25%, var(--surface) 50%, var(--surface-alt) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ─── Error state ─── */
.bom-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  padding: 2rem;
  text-align: center;
}

.error-icon {
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.error-msg {
  font-size: 0.9rem;
  color: var(--ink-700);
  margin: 0 0 1.5rem;
}

.error-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.retry-btn {
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  border: none;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.retry-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb));
}

/* ─── Empty state ─── */
.bom-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  padding: 2rem;
  text-align: center;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.bom-empty-state h3 {
  font-size: 1rem;
  color: var(--ink-700);
  margin: 0 0 1.5rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
}

.back-link:hover {
  background: rgb(var(--palette-deep-sapphire-rgb));
}

/* ─── Mobile layout ─── */
.bom-mobile-layout {
  max-width: 640px;
  margin: 0 auto;
}

.bom-hero-image {
  width: 100%;
  height: 280px;
  overflow: hidden;
}

.bom-hero-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

.bom-product-info {
  padding: 1rem 1rem 0.5rem;
}

.bom-category {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0 0 0.2rem;
}

.bom-product-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--ink-900);
  margin: 0 0 0.5rem;
  line-height: 1.3;
}

.bom-price-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}

.bom-price-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.bom-price {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--ink-900);
  font-variant-numeric: tabular-nums;
}

.bom-prep-time {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.82rem;
  color: var(--ink-600);
  margin-bottom: 0.5rem;
}

.bom-description {
  font-size: 0.85rem;
  color: var(--ink-700);
  line-height: 1.6;
  margin: 0 0 0.75rem;
}

.bom-nutrition-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.nutri-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.35rem 0.65rem;
  border-radius: 10px;
  background: var(--surface-alt);
  min-width: 60px;
}

.nutri-chip small {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.nutri-chip strong {
  font-size: 0.8rem;
  color: var(--ink-800);
  font-variant-numeric: tabular-nums;
}

/* ─── Sections ─── */
.bom-section {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--theme-border);
}

.bom-section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ink-800);
  margin: 0 0 0.6rem;
  padding-bottom: 0.4rem;
  border-bottom: 2px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  display: inline-block;
}

.bom-formula-text {
  font-size: 0.85rem;
  color: var(--ink-700);
  line-height: 1.7;
  margin: 0;
}

.bom-prep-text {
  font-size: 0.85rem;
  color: var(--ink-700);
  line-height: 1.7;
  margin: 0;
  white-space: pre-line;
}

.bom-empty-bom {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}

/* ─── Desktop layout ─── */
@media (min-width: 768px) {
  .bom-desktop-layout {
    display: grid;
    grid-template-columns: 60% 40%;
    gap: 2.5rem;
    width: 100%;
    max-width: min(1440px, 96vw);
    margin: 2rem auto;
    padding: 0 2rem;
    align-items: start;
  }

  .bom-desktop-image-col {
    position: sticky;
    top: 2rem;
  }

  .bom-desktop-image {
    border-radius: 24px;
    overflow: hidden;
    background: #fff;
    border: 1px solid var(--theme-border);
  }

  .bom-desktop-image img {
    width: 100%;
    height: auto;
    max-height: 500px;
    object-fit: contain;
    object-position: center;
    display: block;
  }

  .bom-desktop-info-col {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .bom-desktop-back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.85rem;
    color: var(--ink-700);
    text-decoration: none;
    font-weight: 500;
  }

  .bom-desktop-info-col .bom-category {
    margin-top: 0.5rem;
  }

  .bom-desktop-info-col .bom-product-title {
    font-size: 1.8rem;
  }

  .bom-desktop-info-col .bom-price {
    font-size: 1.4rem;
  }

  .bom-desktop-cart-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--theme-border);
  }

  .qty-control {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border-radius: 999px;
    border: 1px solid var(--theme-border);
    background: var(--surface);
    padding: 0.25rem 0.4rem;
  }

  .qty-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: var(--surface-alt);
    color: var(--ink-800);
    font-size: 1.1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .qty-num {
    font-size: 1rem;
    font-weight: 700;
    min-width: 24px;
    text-align: center;
    font-variant-numeric: tabular-nums;
  }

  .bom-desktop-price {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .bom-desktop-price small {
    font-size: 0.7rem;
    color: var(--text-muted);
  }

  .bom-desktop-price strong {
    font-size: 1.1rem;
    color: var(--ink-900);
    font-variant-numeric: tabular-nums;
  }
}

/* ─── Sticky bottom bar (mobile) ─── */
.bom-sticky-bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  padding-bottom: calc(0.75rem + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-top: 1px solid var(--theme-border);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.08);
}

.bom-bottom-price {
  display: flex;
  flex-direction: column;
}

.bom-bottom-price small {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.bom-bottom-price strong {
  font-size: 1.1rem;
  color: var(--ink-900);
  font-variant-numeric: tabular-nums;
}

.bom-add-btn {
  padding: 0.7rem 1.8rem;
  border-radius: 999px;
  border: none;
  background: var(--ink-800);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
  white-space: nowrap;
}

.bom-add-btn:hover {
  transform: scale(1.03);
}

.bom-add-btn:active {
  transform: scale(0.97);
}

.bom-add-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
