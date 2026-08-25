<template>
  <div class="customize-page">
    <!-- ═══ Loading state ═══ -->
    <template v-if="loading">
      <div class="customize-loading">
        <div class="loading-top-bar shimmer"></div>
        <div class="loading-content">
          <div class="loading-card shimmer" v-for="n in 4" :key="n"></div>
        </div>
        <div class="loading-bottom-bar shimmer"></div>
      </div>
    </template>

    <!-- ═══ Error state ═══ -->
    <template v-else-if="error">
      <div class="customize-state-full">
        <span class="state-icon">⚠️</span>
        <h2>خطا در بارگذاری</h2>
        <p class="muted">{{ error }}</p>
        <button class="state-btn primary" @click="loadTemplate">تلاش مجدد</button>
        <a class="state-btn secondary" href="/menu">بازگشت به منو</a>
      </div>
    </template>

    <!-- ═══ Empty state ═══ -->
    <template v-else-if="isEmpty">
      <div class="customize-state-full">
        <span class="state-icon">🍽️</span>
        <h2>این محصول قابل سفارشی‌سازی نیست</h2>
        <p class="muted">برای این محصول تنظیمی تعریف نشده است.</p>
        <a class="state-btn primary" href="/menu">بازگشت به منو</a>
      </div>
    </template>

    <!-- ═══ Builder ═══ -->
    <template v-else-if="template">
      <!-- Sticky Top Bar -->
      <div class="customize-top-bar">
        <a href="/menu" class="top-bar__back">← بازگشت به منو</a>
        <BuilderProgress
          :steps="stepTitles"
          :current-index="currentStepIndex"
        />
        <h2 class="top-bar__title">{{ currentStep?.step_title || '' }}</h2>
      </div>

      <!-- Main Content -->
      <div class="customize-content">
        <!-- Review step -->
        <BuilderReviewStep
          v-if="isReviewStep"
          :template="template"
          :selections="selections"
          :total-price="displayPrice"
          :base-price="Number(template.base_price) || 0"
          :currency="currency"
          :is-submitting="isSubmitting"
          :submit-error="submitError"
          @submit="addToCart"
          @edit-step="goToStep"
        />

        <!-- Regular step content -->
        <BuilderStepContent
          v-else-if="currentStep"
          :step="currentStep"
          :selections="currentSelections"
          :show-allergens="showAllergens"
          :currency="currency"
          @update:selections="updateStepSelections"
        />
      </div>

      <!-- Sticky Bottom Bar -->
      <div class="customize-bottom-bar" v-if="!isReviewStep">
        <button
          type="button"
          class="nav-btn nav-btn--secondary"
          :disabled="isFirstStep"
          @click="goBack"
        >
          مرحله قبل
        </button>

        <div class="bottom-bar__price" v-if="showPriceLive && displayPrice > 0">
          {{ formatMoney(displayPrice, currency) }}
        </div>

        <button
          type="button"
          class="nav-btn nav-btn--primary"
          :disabled="!stepIsValid"
          @click="goNext"
        >
          {{ isLastStepBeforeReview ? 'مشاهده خلاصه' : 'مرحله بعد' }}
        </button>
      </div>

      <!-- Success toast -->
      <transition name="toast-slide">
        <div class="customize-toast" v-if="addSuccess">
          <span>محصول به سبد اضافه شد ✓</span>
          <a href="/cart">مشاهده سبد ←</a>
        </div>
      </transition>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import BuilderProgress from '@/components/BuilderProgress.vue'
import BuilderStepContent from '@/components/BuilderStepContent.vue'
import BuilderReviewStep from '@/components/BuilderReviewStep.vue'
import { getBuilderTemplate, computeBuilderPrice, saveBuilderSelection } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { upsertLine } from '@/stores/cartStore'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})

// ─── Product slug from URL ──────────────────────────────────────────
const productSlug = ref('')
const currency = ref('TOMAN')

// ─── Builder state ──────────────────────────────────────────────────
const loading = ref(true)
const error = ref('')
const template = ref(null)
const currentStepIndex = ref(0)
const selections = ref({})
const isSubmitting = ref(false)
const submitError = ref('')
const addSuccess = ref(false)
const livePrice = ref(null)

let priceDebounceTimer = null

// ─── Computed ───────────────────────────────────────────────────────
const steps = computed(() => template.value?.steps || [])
const stepTitles = computed(() => steps.value.map(s => s.step_title))
const currentStep = computed(() => steps.value[currentStepIndex.value] || null)
const isFirstStep = computed(() => currentStepIndex.value === 0)
const isLastStep = computed(() => currentStepIndex.value === steps.value.length - 1)
const isReviewStep = computed(() => isLastStep.value && template.value?.layout_mode === 'review_last')
const isLastStepBeforeReview = computed(() => currentStepIndex.value === steps.value.length - 2 && template.value?.layout_mode === 'review_last')
const isEmpty = computed(() => !loading.value && !error.value && (!template.value || !steps.value.length))
const showPriceLive = computed(() => Number(template.value?.show_price_live) === 1)
const showAllergens = computed(() => Number(template.value?.show_allergen_warnings) === 1)
const allowGoBack = computed(() => Number(template.value?.allow_go_back) !== 0)

const currentSelections = computed(() => {
  const key = currentStep.value?.step_key
  return key ? (selections.value[key] || []) : []
})

const stepIsValid = computed(() => {
  if (!currentStep.value) return true
  const min = Number(currentStep.value.min_select) || 0
  const isRequired = Number(currentStep.value.is_required) || 0
  if (!isRequired) return true
  const selectedPortions = currentSelections.value.reduce((sum, row) => sum + Number(row?.qty || 0), 0)
  return selectedPortions >= min
})

const displayPrice = computed(() => {
  if (livePrice.value != null) return livePrice.value
  if (template.value?.base_price) return Number(template.value.base_price) || 0
  return 0
})

// ─── Load template ──────────────────────────────────────────────────
async function loadTemplate() {
  loading.value = true
  error.value = ''

  try {
    const result = await getBuilderTemplate(productSlug.value)
    if (result?.status === 'error') {
      throw new Error(result.error?.message || result.message || 'خطا در بارگذاری')
    }
    const data = result?.data?.template || result?.template || result
    template.value = data

    // Pre-select defaults
    initDefaultSelections()

    // Init live price
    if (showPriceLive.value) {
      triggerPriceCompute()
    }
  } catch (err) {
    error.value = err.message || 'خطا در بارگذاری اطلاعات محصول'
    console.error('[CustomizePage] loadTemplate failed:', err)
  } finally {
    loading.value = false
  }
}

function initDefaultSelections() {
  const map = {}
  for (const step of steps.value) {
    if (!step.options) continue
    const defaults = step.options.filter(opt => Number(opt.is_default) === 1 && Number(opt.is_available) !== 0)
    if (defaults.length) {
      map[step.step_key] = defaults.map(opt => ({
        option_key: opt.option_key,
        qty: 1,
      }))
    }
  }
  selections.value = map
}

// ─── Navigation ─────────────────────────────────────────────────────
function goNext() {
  if (!stepIsValid.value) return

  pushStepToHistory(currentStepIndex.value + 1)

  if (isLastStepBeforeReview.value) {
    currentStepIndex.value = steps.value.length - 1
  } else if (!isLastStep.value) {
    currentStepIndex.value++
  }

  if (showPriceLive.value) triggerPriceCompute()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goBack() {
  if (isFirstStep.value) {
    window.location.href = '/menu'
    return
  }
  if (!allowGoBack.value) return

  pushStepToHistory(currentStepIndex.value - 1)
  currentStepIndex.value--

  if (showPriceLive.value) triggerPriceCompute()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goToStep(idx) {
  currentStepIndex.value = idx
  pushStepToHistory(idx)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function updateStepSelections(newSelections) {
  const key = currentStep.value?.step_key
  if (!key) return
  selections.value = { ...selections.value, [key]: newSelections }
  if (showPriceLive.value) triggerPriceCompute()
}

// ─── Live price ─────────────────────────────────────────────────────
function triggerPriceCompute() {
  clearTimeout(priceDebounceTimer)
  priceDebounceTimer = setTimeout(async () => {
    try {
      const result = await computeBuilderPrice(productSlug.value, buildSelectionsPayload())
      if (result?.status === 'success') {
        const price = result?.data?.final_price ?? result?.final_price
        if (price != null) livePrice.value = price
      }
    } catch (_) {
      // silently fail — price computed at submit
    }
  }, 300)
}

function buildSelectionsPayload() {
  const payload = {}
  for (const key of Object.keys(selections.value)) {
    const sels = selections.value[key]
    if (sels && sels.length) {
      payload[key] = sels.map(s => ({ option_key: s.option_key, qty: s.qty || 1 }))
    }
  }
  return payload
}

function buildSummaryText() {
  const parts = []
  for (const step of steps.value) {
    const sels = selections.value[step.step_key] || []
    for (const sel of sels) {
      const opt = step.options?.find(o => o.option_key === sel.option_key)
      if (opt) parts.push(`${opt.option_label}${Number(sel.qty || 0) > 1 ? ` × ${Number(sel.qty || 0).toLocaleString('fa-IR')}` : ''}`)
    }
  }
  return parts.join(' + ')
}

// ─── Add to cart ────────────────────────────────────────────────────
async function addToCart() {
  isSubmitting.value = true
  submitError.value = ''

  try {
    const result = await saveBuilderSelection({
      template: template.value.name,
      item: productSlug.value,
      base_price: Number(template.value.base_price) || 0,
      selections: buildSelectionsPayload(),
    })

    if (result?.status === 'error') {
      throw new Error(result.error?.message || result.message || 'خطا در ذخیره سفارش')
    }

    const finalPrice = result?.data?.final_price ?? result?.final_price ?? displayPrice.value

    const builderSelection = {
      selection_id: result?.data?.selection_id || result?.selection_id || '',
      template: template.value.name,
      selections: Object.entries(selections.value).flatMap(([stepKey, rows]) =>
        (rows || []).map((row) => ({
          step_key: stepKey,
          option_key: row.option_key,
          qty: Number(row.qty || 0),
        })),
      ),
      summary: result?.data?.builder_summary || buildSummaryText(),
    }

    upsertLine({
      item_slug: productSlug.value,
      item_title: template.value.title || template.value.name || productSlug.value,
      item_image: template.value.preview_image || '',
      base_price: Number(template.value.base_price || 0),
      qty: 1,
      unit_price_preview: finalPrice,
      line_total_preview: finalPrice,
      customization: {
        ingredient_adjustments: [],
        selected_modifiers: [],
        selected_alternatives: [],
        builder_selection: builderSelection,
        builder_summary: result?.data?.builder_summary || buildSummaryText(),
        builder_pricing_breakdown:
          result?.data?.builder_pricing_breakdown ||
          result?.builder_pricing_breakdown || {
            base_price: Number(template.value.base_price) || 0,
            options_total: Number(finalPrice || 0) - (Number(template.value.base_price) || 0),
            final_price: finalPrice,
          },
        builder_portion_rows:
          result?.data?.builder_portion_rows ||
          result?.builder_portion_rows || [],
        builder_template: template.value.name,
      },
      ingredient_catalog: [],
      modifier_groups_catalog: [],
    })

    addSuccess.value = true
    setTimeout(() => {
      window.location.href = '/cart'
    }, 1500)
  } catch (err) {
    submitError.value = err.message || 'خطا در افزودن به سبد'
    console.error('[CustomizePage] addToCart failed:', err)
  } finally {
    isSubmitting.value = false
  }
}

// ─── Browser history / back button ──────────────────────────────────
function pushStepToHistory(stepIdx) {
  try {
    const url = `${window.location.pathname}?step=${stepIdx}`
    history.pushState({ step: stepIdx }, '', url)
  } catch (_) {}
}

function handlePopState() {
  try {
    const params = new URLSearchParams(window.location.search)
    const stepParam = params.get('step')
    if (stepParam !== null) {
      const idx = parseInt(stepParam, 10)
      if (!isNaN(idx) && idx >= 0 && idx < steps.value.length) {
        currentStepIndex.value = idx
        return
      }
    }
    // No step param = step 0, but if we're not on step 0, go to step 0
    // Actually for first step back, go to menu
    if (currentStepIndex.value === 0) {
      window.location.href = '/menu'
    } else {
      currentStepIndex.value = 0
    }
  } catch (_) {}
}

// ─── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  productSlug.value = decodeURIComponent(window.location.pathname.replace('/customize/', '') || '')
  loadTemplate()
  window.addEventListener('popstate', handlePopState)
})

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState)
  clearTimeout(priceDebounceTimer)
})
</script>

<style scoped>
.customize-page {
  min-height: 100vh;
  padding-bottom: 80px;
  background: var(--surface, #f5f0eb);
}

/* ─── Loading skeleton ─── */
.customize-loading {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.loading-top-bar {
  height: 56px;
  background: rgb(var(--palette-eggshell-rgb) / 0.6);
  flex-shrink: 0;
}

.loading-content {
  flex: 1;
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.65rem;
}

.loading-card {
  height: 200px;
  border-radius: 20px;
  background: rgb(var(--palette-eggshell-rgb) / 0.6);
}

.loading-bottom-bar {
  height: 64px;
  background: #fff;
  flex-shrink: 0;
}

.shimmer {
  background: linear-gradient(90deg, rgb(var(--palette-eggshell-rgb) / 0.4) 25%, rgb(var(--palette-eggshell-rgb) / 0.8) 50%, rgb(var(--palette-eggshell-rgb) / 0.4) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ─── Full-state (error/empty) ─── */
.customize-state-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 2rem;
  gap: 0.5rem;
}

.state-icon {
  font-size: 2.5rem;
}

.customize-state-full h2 {
  margin: 0.5rem 0 0;
  font-size: 1.2rem;
  color: var(--ink-900, #141210);
}

.state-btn {
  margin-top: 1rem;
  padding: 0.65rem 1.5rem;
  border-radius: 14px;
  font-size: 0.85rem;
  font-weight: 700;
  font-family: inherit;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.state-btn.primary {
  background: var(--ink-800, #1e1a17);
  color: #fff;
  box-shadow: 0 8px 20px rgba(20, 15, 8, 0.2);
}

.state-btn.secondary {
  background: none;
  color: var(--ink-700, #2e2820);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
}

/* ─── Top bar ─── */
.customize-top-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  padding: 0.65rem 1rem 0.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.top-bar__back {
  font-size: 0.72rem;
  color: var(--text-muted, #7a6e64);
  text-decoration: none;
  font-weight: 600;
  align-self: flex-start;
}

.top-bar__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
  text-align: right;
}

/* ─── Main content ─── */
.customize-content {
  max-width: 720px;
  margin: 0 auto;
}

/* ─── Bottom bar ─── */
.customize-bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: var(--surface, #f5f0eb);
  border-top: 1px solid var(--theme-border, rgb(var(--palette-deep-sapphire-rgb) / 0.1));
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  gap: 0.5rem;
}

.nav-btn {
  border: none;
  border-radius: 14px;
  padding: 0.6rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.15s ease;
  white-space: nowrap;
}

.nav-btn--primary {
  background: var(--ink-800, #1e1a17);
  color: #fff;
  box-shadow: 0 8px 20px rgba(20, 15, 8, 0.18);
  flex: 1;
  max-width: 220px;
}

.nav-btn--secondary {
  background: none;
  color: var(--ink-700, #2e2820);
  border: 1.5px solid rgb(var(--palette-deep-saffron-rgb) / 0.35);
}

.nav-btn:disabled {
  opacity: 0.4;
  pointer-events: none;
}

.bottom-bar__price {
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
  font-variant-numeric: tabular-nums;
  flex: 1;
  text-align: center;
}

/* ─── Success toast ─── */
.customize-toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--ink-800, #1e1a17);
  color: #fff;
  padding: 0.75rem 1.25rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 12px 32px rgba(20, 15, 8, 0.3);
  z-index: 100;
  white-space: nowrap;
}

.customize-toast a {
  color: var(--accent-gold, #c8963e);
  text-decoration: none;
  font-weight: 700;
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.toast-slide-enter-from,
.toast-slide-leave-to {
  transform: translateX(-50%) translateY(16px);
  opacity: 0;
}

/* ─── Responsive ─── */
@media (min-width: 920px) {
  .customize-bottom-bar {
    padding: 0 1.5rem;
    max-width: 600px;
    margin: 0 auto;
    left: 0;
    right: 0;
  }
  .customize-top-bar {
    padding: 0.75rem 1.5rem 0.5rem;
  }
}

.muted {
  color: var(--text-muted, #7a6e64);
}
</style>
