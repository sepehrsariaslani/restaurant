<template>
  <div class="builder-overlay" dir="rtl" @click.self="onOverlayClick">
    <section
      class="builder-wizard"
      ref="panelRef"
      role="dialog"
      aria-modal="true"
      aria-label="سفارشی‌سازی محصول"
    >
      <header class="wizard-header" @touchstart.passive="onPanelTouchStart" @touchmove.passive="onPanelTouchMove" @touchend.passive="onPanelTouchEnd">
        <div class="drag-handle" aria-hidden="true"></div>
      <button class="header-icon-btn" type="button" @click="$emit('close')" aria-label="بستن">
        <XIcon class="icon-md" />
      </button>
      <div class="header-title">
        <strong>{{ template?.title || product.item_name || 'سفارش سفارشی' }}</strong>
        <small>{{ steps.length }} مرحله برای ساخت سفارش شما</small>
      </div>
      <button class="header-icon-btn" type="button" @click="goToReview" aria-label="رفتن به جمع‌بندی">
        <ArrowLeftIcon class="icon-md" />
      </button>
      </header>

      <nav class="stepper" v-if="steps.length" aria-label="مراحل سفارشی‌سازی">
      <button
        v-for="(step, index) in steps"
        :key="step.step_key || index"
        type="button"
        class="stepper-item"
        :class="{ active: index === currentStepIndex, done: isStepComplete(step), disabled: !canGoToStep(index) }"
        :disabled="!canGoToStep(index)"
        @click="goToStep(index)"
      >
        <span class="step-dot">
          <CheckIcon v-if="isStepComplete(step)" class="icon-xs" />
          <span v-else>{{ index + 1 }}</span>
        </span>
        <small>{{ shortStepTitle(step.step_title, index) }}</small>
      </button>
      </nav>

      <main
        class="wizard-main"
        ref="mainRef"
        @touchstart.passive="onPanelTouchStart"
        @touchmove.passive="onPanelTouchMove"
        @touchend.passive="onPanelTouchEnd"
      >
      <section class="hero-card">
        <div class="hero-copy">
          <span class="eyebrow">محصول سفارشی</span>
          <h2>{{ product.item_name || product.title || 'سفارش شما' }}</h2>
          <p>{{ currentStep?.step_description || 'گزینه‌های هر مرحله را انتخاب کنید تا سفارش اختصاصی شما ساخته شود.' }}</p>
          <strong class="hero-price">از {{ formatPrice(basePrice) }} تومان</strong>
        </div>
        <div class="hero-image-wrap">
          <img v-if="productImage" :src="productImage" :alt="product.item_name || product.title" />
          <ImageIcon v-else class="hero-placeholder" />
        </div>
      </section>

      <section v-if="!steps.length" class="empty-state">
        <AlertCircleIcon class="icon-lg" />
        <h3>برای این محصول هنوز مرحله‌ای تعریف نشده است.</h3>
        <p>لطفاً از بخش مدیریت، قالب سفارشی‌سازی محصول را کامل کنید.</p>
      </section>

      <template v-else>
        <section
          v-for="(step, index) in visibleSections"
          :key="step.step_key || index"
          class="builder-section"
          :class="{ 'is-current': index === currentStepIndex }"
        >
          <div class="section-head">
            <div>
              <h3>{{ index + 1 }}. {{ step.step_title }}</h3>
              <small>{{ stepHelpText(step) }}</small>
            </div>
            <button
              v-if="index !== currentStepIndex"
              class="jump-btn"
              type="button"
              :disabled="!canGoToStep(index)"
              @click="goToStep(index)"
            >
              انتخاب
            </button>
          </div>

          <div class="search-shell">
            <SearchIcon class="icon-sm" />
            <input v-model.trim="searchByStep[step.step_key]" type="search" placeholder="جستجوی مواد..." />
          </div>

          <div class="options-grid" :class="`mode-${step.selection_mode || 'single'}`">
            <article
              v-for="option in filteredStepOptions(step)"
              :key="option.option_key"
              class="option-card"
              :class="{ selected: isOptionSelected(option), disabled: !option.is_available }"
            >
              <button class="option-hit" type="button" :disabled="!option.is_available" @click="toggleOption(option, step)">
                <span class="selected-mark" v-if="isOptionSelected(option)"><CheckIcon class="icon-xs" /></span>
                <span v-if="option.price_delta > 0" class="price-chip">+{{ formatPrice(option.price_delta) }}</span>
                <span class="option-image">
                  <img v-if="option.image" :src="option.image" :alt="option.option_label" />
                  <ImageIcon v-else class="option-placeholder" />
                </span>
                <strong>{{ option.option_label }}</strong>
                <small v-if="option.option_description">{{ option.option_description }}</small>
                <small v-else-if="option.allergens?.length">آلرژی: {{ option.allergens.join('، ') }}</small>
              </button>

              <div class="option-qty" v-if="isOptionSelected(option)">
                <button type="button" @click="changeQty(option, -1)" :disabled="getQty(option) <= 1">
                  <MinusIcon class="icon-xs" />
                </button>
                <span>{{ getQty(option) }}</span>
                <button type="button" class="plus" @click="changeQty(option, 1)" :disabled="getQty(option) >= maxOptionQty(option)">
                  <PlusIcon class="icon-xs" />
                </button>
              </div>
              <button v-else class="quick-plus" type="button" @click="toggleOption(option, step)">
                <PlusIcon class="icon-xs" />
              </button>
            </article>
          </div>

          <p v-if="stepError && index === currentStepIndex" class="step-error">
            <AlertCircleIcon class="icon-sm" />
            {{ stepError }}
          </p>
        </section>

        <section class="review-card" ref="reviewRef">
          <header>
            <h3>{{ steps.length }}. جمع‌بندی سفارش</h3>
            <small>انتخاب‌های شما و قیمت نهایی</small>
          </header>

          <div class="selected-tags" v-if="selectedRows.length">
            <span v-for="row in selectedRows" :key="`${row.step_key}-${row.option_key}`">
              {{ row.option_label }}<b v-if="row.qty > 1"> × {{ row.qty }}</b>
            </span>
          </div>
          <p v-else class="muted">هنوز گزینه‌ای انتخاب نشده است.</p>

          <div class="price-lines">
            <div><span>قیمت پایه</span><strong>{{ formatPrice(basePrice) }} تومان</strong></div>
            <div><span>افزودنی‌ها</span><strong>{{ formatPrice(optionsTotal) }} تومان</strong></div>
            <div class="total"><span>جمع کل</span><strong>{{ formatPrice(finalPrice) }} تومان</strong></div>
          </div>

          <div class="nutrition-strip" v-if="nutritionItems.length">
            <div v-for="item in nutritionItems" :key="item.label">
              <small>{{ item.label }}</small>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </section>
      </template>
      </main>

      <footer class="wizard-footer">
      <div class="footer-price">
        <small>قیمت نهایی</small>
        <strong>{{ formatPrice(finalPrice) }} تومان</strong>
      </div>
      <div class="footer-actions">
        <button class="collapse-btn" type="button" @click="scrollTop" aria-label="رفتن به بالا">
          <ChevronUpIcon class="icon-sm" />
        </button>
        <button class="add-cart-btn" type="button" :disabled="!allRequiredComplete" @click="submitOrder">
          <ShoppingBagIcon class="icon-sm" />
          افزودن به سبد
        </button>
      </div>
      </footer>

      <transition name="fade">
      <div class="success-overlay" v-if="showSuccess">
        <div class="success-content">
          <CheckCircleIcon class="icon-xl" />
          <h3>به سبد خرید اضافه شد</h3>
          <p>{{ product.item_name || product.title }} آماده سفارش است.</p>
        </div>
      </div>
      </transition>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import {
  AlertCircle as AlertCircleIcon,
  ArrowLeft as ArrowLeftIcon,
  Check as CheckIcon,
  CheckCircle as CheckCircleIcon,
  ChevronUp as ChevronUpIcon,
  Image as ImageIcon,
  Minus as MinusIcon,
  Plus as PlusIcon,
  Search as SearchIcon,
  ShoppingBag as ShoppingBagIcon,
  X as XIcon,
} from 'lucide-vue-next'

const props = defineProps({
  product: { type: Object, required: true },
  template: { type: Object, default: null },
  basePrice: { type: Number, default: 0 },
  currency: { type: String, default: 'TOMAN' },
  loadingPrice: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'cart', 'add-to-cart', 'selection-change'])

const currentStepIndex = ref(0)
const selections = reactive({})
const searchByStep = reactive({})
const stepError = ref('')
const showSuccess = ref(false)
const reviewRef = ref(null)
const panelRef = ref(null)
const mainRef = ref(null)

let touchStartY = 0
let touchStartScrollTop = 0
let touchMoved = false
let touchStartTime = 0

const steps = computed(() => {
  if (!props.template?.steps) return []
  return props.template.steps.map((step) => ({
    ...step,
    step_key: step.step_key || `step-${step.sort_order || 0}`,
    options: Array.isArray(step.options)
      ? step.options.map((option) => ({
          ...option,
          parent_step_key: step.step_key || `step-${step.sort_order || 0}`,
          price_delta: Number(option.price_delta ?? option.base_price_delta ?? 0) || 0,
          is_available: option.is_available !== false,
        }))
      : [],
  }))
})

const currentStep = computed(() => steps.value[currentStepIndex.value] || { options: [] })
const visibleSections = computed(() => steps.value)
const productImage = computed(() => props.product?.image || props.product?.item_image || props.product?.website_image || '')

const selectedRows = computed(() => Object.entries(selections)
  .filter(([, row]) => row.qty > 0)
  .map(([key, row]) => ({
    step_key: row.option.parent_step_key,
    option_key: key,
    option_label: row.option.option_label,
    qty: row.qty,
    price_delta: Number(row.option.price_delta || 0),
    price_type: row.option.price_type || 'fixed',
    price_percentage: Number(row.option.price_percentage || 0),
    image: row.option.image || '',
  })))

const optionsTotal = computed(() => selectedRows.value.reduce((sum, row) => {
  if (row.price_type === 'percentage') return sum + ((props.basePrice || 0) * row.price_percentage / 100) * row.qty
  if (row.price_type === 'multiply') return sum + (props.basePrice || 0) * row.price_delta * row.qty
  return sum + row.price_delta * row.qty
}, 0))

const finalPrice = computed(() => Math.round((props.basePrice || 0) + optionsTotal.value))

const allRequiredComplete = computed(() => steps.value.every((step) => isStepComplete(step) || !step.is_required))

const nutritionItems = computed(() => {
  const nutrition = props.product?.nutrition || {}
  return [
    { label: 'کالری', value: nutrition.kcal ? `${Math.round(nutrition.kcal)} kcal` : '' },
    { label: 'پروتئین', value: nutrition.protein_g ? `${Math.round(nutrition.protein_g)} g` : '' },
    { label: 'کربوهیدرات', value: nutrition.carb_g ? `${Math.round(nutrition.carb_g)} g` : '' },
  ].filter((row) => row.value)
})

function shortStepTitle(title = '', index = 0) {
  const text = String(title || '').trim()
  if (!text) return `مرحله ${index + 1}`
  return text.length > 10 ? text.slice(0, 10) : text
}

function stepHelpText(step) {
  const min = Number(step.min_select || 0)
  const max = Number(step.max_select || 0)
  if (step.selection_mode === 'quantity') return max ? `حداقل ${min} تا ${max} مورد` : `حداقل ${min} مورد`
  if (step.selection_mode === 'multiple') return max ? `انتخاب ${min} تا ${max} مورد` : `حداقل ${min} مورد را انتخاب کنید`
  return step.is_required ? 'یک گزینه را انتخاب کنید' : 'انتخاب این مرحله اختیاری است'
}

function filteredStepOptions(step) {
  const term = String(searchByStep[step.step_key] || '').trim().toLowerCase()
  const options = (step.options || []).filter((option) => option.is_available !== false)
  if (!term) return options
  return options.filter((option) => String(option.option_label || '').toLowerCase().includes(term))
}

function isStepComplete(step) {
  const selectedCount = (step.options || []).filter((option) => getQty(option) > 0).length
  const min = Number(step.min_select || (step.is_required ? 1 : 0))
  return selectedCount >= min
}

function canGoToStep(index) {
  if (index <= currentStepIndex.value) return true
  if (props.template?.allow_skip_steps) return true
  for (let i = 0; i < index; i += 1) {
    const step = steps.value[i]
    if (step?.is_required && !isStepComplete(step)) return false
  }
  return true
}

function goToStep(index) {
  if (!canGoToStep(index)) return
  currentStepIndex.value = index
  stepError.value = ''
  nextTick(() => {
    document.querySelectorAll('.builder-section')?.[index]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function isOptionSelected(option) {
  return getQty(option) > 0
}

function getQty(option) {
  return Number(selections[option.option_key]?.qty || 0)
}

function maxOptionQty(option) {
  return Math.max(Number(option.max_qty || 1), 1)
}

function toggleOption(option, step = currentStep.value) {
  stepError.value = ''
  const key = option.option_key
  if (!selections[key]) selections[key] = { qty: 0, option }
  const current = selections[key].qty

  if (current > 0) {
    selections[key].qty = 0
    emitSelectionChange()
    return
  }

  if ((step.selection_mode || 'single') === 'single') {
    for (const rowKey of Object.keys(selections)) {
      if (selections[rowKey]?.option?.parent_step_key === option.parent_step_key) {
        selections[rowKey].qty = 0
      }
    }
  }

  selections[key] = { qty: 1, option }
  emitSelectionChange()
}

function changeQty(option, delta) {
  const key = option.option_key
  if (!selections[key]) selections[key] = { qty: 0, option }
  const next = Math.min(Math.max(Number(selections[key].qty || 0) + delta, 0), maxOptionQty(option))
  selections[key].qty = next
  emitSelectionChange()
}

function emitSelectionChange() {
  emit('selection-change', selectedRows.value)
}

function firstInvalidRequiredStepIndex() {
  return steps.value.findIndex((step) => step.is_required && !isStepComplete(step))
}

function submitOrder() {
  const invalidIndex = firstInvalidRequiredStepIndex()
  if (invalidIndex >= 0) {
    currentStepIndex.value = invalidIndex
    stepError.value = `لطفاً مرحله «${steps.value[invalidIndex].step_title}» را کامل کنید.`
    goToStep(invalidIndex)
    return
  }

  const payload = {
    template: props.template?.name,
    item: props.product.name || props.product.item_code,
    base_price: props.basePrice,
    final_price: finalPrice.value,
    options_total: Math.round(optionsTotal.value),
    selections: selectedRows.value,
  }
  emit('add-to-cart', payload)
  showSuccess.value = true
  setTimeout(() => { showSuccess.value = false }, 1600)
}

function goToReview() {
  reviewRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function scrollTop() {
  mainRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function onOverlayClick() {
  emit('close')
}

function onPanelTouchStart(event) {
  if (!panelRef.value) return
  touchStartY = event.touches?.[0]?.clientY || 0
  touchStartScrollTop = mainRef.value?.scrollTop || 0
  touchMoved = false
  touchStartTime = Date.now()
}

function onPanelTouchMove(event) {
  if (!panelRef.value) return
  const currentY = event.touches?.[0]?.clientY || 0
  const deltaY = currentY - touchStartY
  const isAtTop = (mainRef.value?.scrollTop || 0) <= 0 && touchStartScrollTop <= 0
  if (deltaY > 0 && isAtTop) {
    touchMoved = true
    const distance = Math.min(deltaY * 0.55, 180)
    panelRef.value.style.transform = `translate3d(0, ${distance}px, 0) scale(${Math.max(0.985, 1 - distance / 6000)})`
    panelRef.value.style.transition = 'none'
  }
}

function onPanelTouchEnd(event) {
  if (!panelRef.value) return
  const endY = event.changedTouches?.[0]?.clientY || 0
  const deltaY = endY - touchStartY
  const elapsed = Date.now() - touchStartTime
  panelRef.value.style.transform = ''
  panelRef.value.style.transition = ''

  const isFlickDown = deltaY > 56 && elapsed < 280
  const isPulledEnough = deltaY > 96 && touchMoved
  if (isFlickDown || isPulledEnough) {
    emit('close')
  }
}

function formatPrice(value) {
  return Math.round(value || 0).toLocaleString('fa-IR')
}

watch(
  () => props.template,
  () => {
    currentStepIndex.value = 0
    stepError.value = ''
    for (const key of Object.keys(selections)) delete selections[key]
    emitSelectionChange()
  },
  { deep: true },
)
</script>

<style scoped>
.builder-overlay {
  position: fixed;
  inset: 0;
  z-index: 1300;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background:
    radial-gradient(circle at 50% 100%, rgba(47, 125, 66, 0.18), transparent 34%),
    rgba(19, 27, 22, 0.46);
  backdrop-filter: blur(14px) saturate(1.1);
  -webkit-backdrop-filter: blur(14px) saturate(1.1);
  padding: 0;
  touch-action: none;
}

.builder-wizard {
  width: min(100%, 640px);
  max-height: calc(100dvh - 0.45rem);
  max-height: calc(100svh - 0.45rem);
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  background: #fffaf5;
  color: #214032;
  overflow: hidden;
  border-radius: 26px 26px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 -18px 70px rgba(12, 18, 14, 0.24);
  will-change: transform;
  animation: sheet-rise 260ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

@keyframes sheet-rise {
  from { opacity: 0; transform: translate3d(0, 36px, 0) scale(0.985); }
  to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
}

.wizard-header {
  position: relative;
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) 44px;
  align-items: center;
  gap: 0.5rem;
  padding: calc(env(safe-area-inset-top) + 1.15rem) 1rem 0.65rem;
  background: rgba(255, 250, 245, 0.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(111, 74, 49, 0.08);
}

.drag-handle {
  position: absolute;
  top: calc(env(safe-area-inset-top) + 0.45rem);
  left: 50%;
  width: 46px;
  height: 5px;
  border-radius: 999px;
  transform: translateX(-50%);
  background: rgba(33, 64, 50, 0.16);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.7) inset;
}

.header-title {
  text-align: center;
  display: grid;
  gap: 0.15rem;
}

.header-title strong { font-size: 1rem; font-weight: 900; color: #1f4d37; }
.header-title small { font-size: 0.72rem; color: #8c8075; }

.header-icon-btn {
  width: 42px;
  height: 42px;
  border: 1px solid rgba(33, 64, 50, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.6);
  color: #2f4638;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease;
}
.header-icon-btn:hover { background: #fff; box-shadow: 0 8px 20px rgba(33, 64, 50, 0.08); }
.header-icon-btn:active { transform: scale(0.94); }

.stepper {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(58px, 1fr);
  gap: 0.2rem;
  padding: 0.75rem 0.75rem 0.55rem;
  overflow-x: auto;
  scrollbar-width: none;
  background: #fffaf5;
}
.stepper::-webkit-scrollbar { display: none; }

.stepper-item {
  position: relative;
  border: 0;
  background: transparent;
  display: grid;
  justify-items: center;
  gap: 0.35rem;
  color: #94887d;
  font-family: inherit;
  min-width: 58px;
}

.stepper-item:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 15px;
  left: calc(-50% + 12px);
  width: calc(100% - 24px);
  height: 2px;
  background: #e6ded6;
}

.step-dot {
  position: relative;
  z-index: 1;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eee8e2;
  color: #7b7167;
  font-weight: 900;
  box-shadow: 0 2px 8px rgba(37, 66, 50, 0.08);
}

.stepper-item.active .step-dot,
.stepper-item.done .step-dot {
  background: #2f7d42;
  color: #fff;
}

.stepper-item small { font-size: 0.67rem; white-space: nowrap; }
.stepper-item.active small { color: #1f4d37; font-weight: 800; }
.stepper-item.disabled { opacity: 0.5; }

.wizard-main {
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  touch-action: pan-y;
  padding: 0.55rem 1rem 7rem;
  scroll-behavior: smooth;
}

.hero-card,
.review-card,
.builder-section {
  border: 1px solid #efe2d5;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 30px rgba(59, 42, 28, 0.07);
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 44%;
  gap: 0.8rem;
  padding: 1rem;
  margin-bottom: 1rem;
  overflow: hidden;
}

.hero-copy { display: grid; align-content: center; gap: 0.45rem; }
.eyebrow { color: #2f7d42; font-size: 0.75rem; font-weight: 900; }
.hero-copy h2 { margin: 0; font-size: 1.15rem; color: #214032; }
.hero-copy p { margin: 0; color: #86786c; font-size: 0.78rem; line-height: 1.75; }
.hero-price { color: #f97316; font-size: 0.85rem; }

.hero-image-wrap {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-image-wrap img {
  width: 100%;
  max-height: 150px;
  object-fit: contain;
  filter: drop-shadow(0 18px 18px rgba(70, 50, 30, 0.16));
}
.hero-placeholder { width: 64px; height: 64px; color: #d5c8bc; }

.builder-section {
  padding: 1rem 0 0.9rem;
  margin-bottom: 1rem;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
}
.builder-section.is-current { scroll-margin-top: 7rem; }

.section-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.65rem;
}
.section-head h3 { margin: 0 0 0.12rem; color: #214032; font-size: 0.96rem; }
.section-head small { color: #998d82; font-size: 0.72rem; }
.jump-btn {
  border: 1px solid #d9eadb;
  background: #f6fff7;
  color: #2f7d42;
  border-radius: 999px;
  padding: 0.38rem 0.8rem;
  font-family: inherit;
  font-weight: 800;
}

.search-shell {
  height: 38px;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid #f0e7de;
  background: #fff;
  color: #9a8f85;
  border-radius: 999px;
  padding: 0 0.75rem;
  margin-bottom: 0.7rem;
}
.search-shell input {
  border: 0;
  outline: 0;
  min-width: 0;
  flex: 1;
  font-family: inherit;
  background: transparent;
  color: #214032;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.option-card {
  position: relative;
  min-height: 164px;
  border-radius: 16px;
  border: 1px solid #f0e5da;
  background: #fff;
  box-shadow: 0 10px 22px rgba(33, 64, 50, 0.06);
  overflow: hidden;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}
.option-card:hover { transform: translateY(-2px); box-shadow: 0 16px 34px rgba(33, 64, 50, 0.1); }
.option-card.selected {
  border-color: #72a86c;
  box-shadow: 0 12px 28px rgba(47, 125, 66, 0.14);
}
.option-card:active { transform: scale(0.985); }
.option-card.disabled { opacity: 0.55; }

.option-hit {
  width: 100%;
  min-height: 136px;
  border: 0;
  background: transparent;
  display: grid;
  justify-items: center;
  gap: 0.28rem;
  padding: 0.72rem 0.6rem 0.35rem;
  font-family: inherit;
  color: inherit;
}

.option-image {
  width: 76px;
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.option-image img { width: 100%; height: 100%; object-fit: contain; }
.option-placeholder { color: #d5c8bc; }
.option-card strong { color: #4a3d31; font-size: 0.8rem; line-height: 1.55; }
.option-card small { color: #a0968c; font-size: 0.68rem; }

.selected-mark {
  position: absolute;
  top: 0.45rem;
  right: 0.45rem;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #2f7d42;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.price-chip {
  position: absolute;
  top: 0.45rem;
  left: 0.45rem;
  color: #f97316;
  font-size: 0.67rem;
  font-weight: 900;
}

.option-qty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0 0.6rem 0.65rem;
}
.option-qty button,
.quick-plus {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  border: 1px solid #f0e3d6;
  background: #fff6ee;
  color: #f97316;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.option-qty button.plus,
.quick-plus {
  background: #ff7a18;
  border-color: #ff7a18;
  color: #fff;
}
.quick-plus { position: absolute; left: 0.6rem; bottom: 0.65rem; }
.option-qty span { min-width: 18px; text-align: center; font-weight: 900; color: #4b3d31; }

.step-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #b42318;
  font-size: 0.78rem;
  margin: 0.75rem 0 0;
}

.review-card {
  padding: 1rem;
  margin: 1rem 0;
  scroll-margin-top: 7rem;
}
.review-card header { display: flex; align-items: start; justify-content: space-between; gap: 1rem; margin-bottom: 0.75rem; }
.review-card h3 { margin: 0; color: #214032; font-size: 0.98rem; }
.review-card small, .muted { color: #95887d; font-size: 0.74rem; }
.selected-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.8rem; }
.selected-tags span { background: #f7f2ec; border: 1px solid #ede2d7; border-radius: 999px; padding: 0.35rem 0.65rem; color: #55483d; font-size: 0.72rem; }
.price-lines { display: grid; gap: 0.45rem; }
.price-lines div { display: flex; justify-content: space-between; color: #6c5e52; font-size: 0.82rem; }
.price-lines .total { border-top: 1px dashed #eaded2; padding-top: 0.55rem; color: #214032; font-weight: 900; }
.price-lines .total strong { color: #f97316; }
.nutrition-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-top: 0.9rem; }
.nutrition-strip div { background: #fffaf5; border: 1px solid #f0e6dc; border-radius: 12px; padding: 0.55rem; text-align: center; display: grid; gap: 0.15rem; }
.nutrition-strip strong { color: #214032; font-size: 0.78rem; }

.empty-state { min-height: 45vh; display: grid; align-content: center; justify-items: center; text-align: center; gap: 0.5rem; color: #7b7167; }
.empty-state h3 { margin: 0; color: #214032; }
.empty-state p { margin: 0; font-size: 0.82rem; }

.wizard-footer {
  padding: 0.7rem 1rem calc(env(safe-area-inset-bottom) + 0.7rem);
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.4fr);
  gap: 0.65rem;
  align-items: center;
  background: rgba(255, 250, 245, 0.94);
  border-top: 1px solid #eee2d6;
  box-shadow: 0 -12px 28px rgba(48, 35, 24, 0.08);
  backdrop-filter: blur(14px);
}
.footer-price { display: grid; gap: 0.15rem; }
.footer-price small { color: #94887d; font-size: 0.72rem; }
.footer-price strong { color: #214032; font-size: 0.92rem; }
.footer-actions { display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 0.5rem; }
.collapse-btn,
.add-cart-btn { min-height: 44px; border: 0; border-radius: 14px; font-family: inherit; font-weight: 900; }
.collapse-btn { background: #fff; border: 1px solid #eee2d6; color: #735f4e; }
.add-cart-btn { position: relative; overflow: hidden; background: linear-gradient(135deg, #ff7a18, #fb6514); color: #fff; display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem; box-shadow: 0 12px 24px rgba(249, 115, 22, 0.28); }
.add-cart-btn::after {
  content: '';
  position: absolute;
  inset: -40% auto -40% -30%;
  width: 34%;
  transform: skewX(-18deg) translateX(-120%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.34), transparent);
  transition: transform 520ms ease;
}
.add-cart-btn:not(:disabled):hover::after { transform: skewX(-18deg) translateX(420%); }
.add-cart-btn:not(:disabled):active { transform: scale(0.985); }
.add-cart-btn:disabled { opacity: 0.45; box-shadow: none; }

.success-overlay { position: fixed; inset: 0; display: grid; place-items: center; background: rgba(20, 30, 24, 0.25); backdrop-filter: blur(8px); z-index: 5; }
.success-content { width: min(320px, calc(100vw - 2rem)); background: #fff; border-radius: 24px; padding: 1.25rem; text-align: center; color: #214032; box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18); }
.success-content .icon-xl { color: #2f7d42; width: 48px; height: 48px; }

.icon-xs { width: 14px; height: 14px; }
.icon-sm { width: 18px; height: 18px; }
.icon-md { width: 22px; height: 22px; }
.icon-lg { width: 32px; height: 32px; }
.icon-xl { width: 48px; height: 48px; }
.fade-enter-active, .fade-leave-active { transition: opacity 180ms ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (min-width: 900px) {
  .builder-overlay {
    align-items: center;
    padding: 2rem;
  }

  .builder-wizard {
    width: min(1120px, calc(100vw - 4rem));
    max-height: min(880px, calc(100dvh - 4rem));
    border-radius: 30px;
    box-shadow: 0 34px 110px rgba(8, 20, 13, 0.34), 0 0 0 1px rgba(255, 255, 255, 0.46) inset;
    animation-name: modal-bloom;
  }

  @keyframes modal-bloom {
    from { opacity: 0; transform: translate3d(0, 18px, 0) scale(0.972); }
    to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
  }

  .drag-handle { display: none; }
  .wizard-header { padding: 1rem 1.25rem 0.85rem; }
  .header-title strong { font-size: 1.12rem; }
  .header-title small { font-size: 0.78rem; }

  .stepper {
    grid-auto-columns: minmax(78px, 1fr);
    padding: 0.85rem 1.25rem 0.7rem;
    border-bottom: 1px solid rgba(111, 74, 49, 0.06);
  }

  .wizard-main {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    align-items: start;
    gap: 1rem 1.2rem;
    padding: 1rem 1.25rem 1.25rem;
  }

  .hero-card {
    grid-column: 1 / -1;
    grid-template-columns: minmax(0, 1fr) 260px;
    min-height: 178px;
    margin: 0;
  }

  .hero-copy h2 { font-size: 1.45rem; }
  .hero-copy p { font-size: 0.9rem; max-width: 62ch; }
  .hero-image-wrap img { max-height: 180px; }

  .builder-section {
    grid-column: 1;
    margin: 0;
    padding: 0.25rem 0 0.6rem;
  }
  .builder-section.is-current { scroll-margin-top: 1rem; }

  .options-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.85rem;
  }

  .option-card { min-height: 172px; }
  .option-hit { min-height: 142px; }

  .review-card {
    grid-column: 2;
    grid-row: 2 / span 40;
    position: sticky;
    top: 0;
    margin: 0;
    align-self: start;
    border-radius: 22px;
  }

  .wizard-footer {
    padding: 0.85rem 1.25rem 1rem;
    grid-template-columns: 240px minmax(0, 1fr);
  }
  .footer-actions { grid-template-columns: 48px minmax(0, 260px); justify-content: end; }
  .footer-price strong { font-size: 1.08rem; }
}

@media (min-width: 1280px) {
  .builder-wizard { width: min(1220px, calc(100vw - 5rem)); }
  .wizard-main { grid-template-columns: minmax(0, 1fr) 390px; }
  .options-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

@media (prefers-reduced-motion: reduce) {
  .builder-wizard,
  .option-card,
  .header-icon-btn,
  .add-cart-btn::after,
  .fade-enter-active,
  .fade-leave-active {
    animation: none !important;
    transition: none !important;
  }
}
</style>
