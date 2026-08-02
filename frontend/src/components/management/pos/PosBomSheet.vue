<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="pos-bom-overlay"
      role="presentation"
      @click.self="$emit('close')"
    >
      <section
        class="pos-bom-modal"
        dir="rtl"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @click.stop
      >
        <header class="pos-bom-header">
          <div class="pos-bom-heading">
            <div class="pos-bom-heading-icon" aria-hidden="true">
              <SlidersHorizontal :size="21" :stroke-width="2.2" />
            </div>
            <div class="pos-bom-heading-copy">
              <span class="pos-bom-kicker">BOM / سفارشی‌سازی</span>
              <h2 :id="titleId">{{ item?.title || 'تنظیم آیتم' }}</h2>
              <div class="pos-bom-meta" v-if="item">
                <span v-if="item.category_title || item.category">
                  {{ item.category_title || item.category }}
                </span>
                <span v-if="item.base_price || item.standard_rate">
                  قیمت پایه: {{ formatMoney(item.base_price || item.standard_rate || 0, currency) }}
                </span>
              </div>
            </div>
          </div>
          <button
            type="button"
            class="pos-bom-close"
            aria-label="بستن پنجره BOM"
            title="بستن"
            @click="$emit('close')"
          >
            <X :size="19" :stroke-width="2.3" />
          </button>
        </header>

        <div class="pos-bom-body">
          <div v-if="loading" class="pos-bom-loading" aria-live="polite">
            <div class="pos-bom-skeleton pos-bom-skeleton--summary"></div>
            <div class="pos-bom-skeleton-grid">
              <div class="pos-bom-skeleton" v-for="n in 4" :key="n"></div>
            </div>
            <p>در حال دریافت تنظیمات BOM...</p>
          </div>

          <div v-else-if="error" class="pos-bom-state pos-bom-state--error" role="alert">
            <div class="pos-bom-state-icon"><AlertCircle :size="25" /></div>
            <strong>دریافت تنظیمات آیتم ناموفق بود</strong>
            <p>{{ error }}</p>
            <button type="button" class="pos-bom-secondary-btn" @click="$emit('close')">بستن</button>
          </div>

          <template v-else-if="item">
            <section class="pos-bom-overview" aria-label="خلاصه آیتم">
              <div class="pos-bom-overview-item">
                <span class="overview-icon"><Package :size="16" /></span>
                <span>
                  <small>مواد اولیه</small>
                  <strong>{{ faCount(ingredients.length) }} مورد</strong>
                </span>
              </div>
              <div class="pos-bom-overview-item">
                <span class="overview-icon overview-icon--accent"><ListChecks :size="16" /></span>
                <span>
                  <small>گروه انتخاب</small>
                  <strong>{{ faCount(modifierGroups.length) }} گروه</strong>
                </span>
              </div>
              <div class="pos-bom-overview-item pos-bom-overview-item--price">
                <span>
                  <small>قیمت واحد نهایی</small>
                  <strong>{{ formatMoney(preview.unitPrice || 0, currency) }}</strong>
                </span>
              </div>
            </section>

            <section class="pos-bom-quantity-card">
              <div class="pos-bom-section-title">
                <div class="pos-bom-section-icon"><Package :size="17" /></div>
                <div>
                  <h3>تعداد سفارش</h3>
                  <p>مقدار این آیتم را برای فاکتور مشخص کنید.</p>
                </div>
              </div>
              <div class="pos-bom-stepper" aria-label="تعداد سفارش">
                <button
                  type="button"
                  aria-label="کم کردن تعداد"
                  title="کم کردن"
                  :disabled="Number(qty || 1) <= 1"
                  @click="$emit('update:qty', Math.max(Number(qty || 1) - 1, 1))"
                >
                  <Minus :size="17" :stroke-width="2.5" />
                </button>
                <strong>{{ faCount(qty || 1) }}</strong>
                <button
                  type="button"
                  aria-label="زیاد کردن تعداد"
                  title="زیاد کردن"
                  @click="$emit('update:qty', Number(qty || 1) + 1)"
                >
                  <Plus :size="17" :stroke-width="2.5" />
                </button>
              </div>
            </section>

            <section v-if="ingredients.length" class="pos-bom-editor-card">
              <header class="pos-bom-editor-head">
                <div class="pos-bom-section-title">
                  <div class="pos-bom-section-icon pos-bom-section-icon--green"><Wheat :size="17" /></div>
                  <div>
                    <h3>مواد اولیه</h3>
                    <p>مقدار، حذف یا افزودن مواد تشکیل‌دهنده را تنظیم کنید.</p>
                  </div>
                </div>
                <span class="pos-bom-count-badge">{{ faCount(ingredients.length) }} مورد</span>
              </header>
              <div class="pos-bom-editor-body">
                <IngredientQuantityEditor
                  :ingredients="ingredients"
                  :model-value="customization"
                  :currency="currency"
                  compact
                  @update:model-value="$emit('update-customization', $event)"
                />
              </div>
            </section>

            <section v-if="modifierGroups.length" class="pos-bom-editor-card">
              <header class="pos-bom-editor-head">
                <div class="pos-bom-section-title">
                  <div class="pos-bom-section-icon pos-bom-section-icon--gold"><ListChecks :size="17" /></div>
                  <div>
                    <h3>انتخاب‌ها و افزودنی‌ها</h3>
                    <p>سایز، طعم یا گزینه‌های قابل انتخاب را مشخص کنید.</p>
                  </div>
                </div>
                <span class="pos-bom-count-badge pos-bom-count-badge--gold">{{ faCount(modifierGroups.length) }} گروه</span>
              </header>
              <div class="pos-bom-editor-body">
                <ModifierRecipeImpactSelector
                  :groups="modifierGroups"
                  :currency="currency"
                  :model-value="customization.selected_modifiers"
                  compact
                  @update:model-value="$emit('update-modifiers', $event)"
                />
              </div>
            </section>

            <div v-if="!ingredients.length && !modifierGroups.length" class="pos-bom-state pos-bom-state--empty">
              <div class="pos-bom-state-icon"><Package :size="24" /></div>
              <strong>تنظیم قابل تغییری برای این آیتم ثبت نشده است</strong>
              <p>با این حال می‌توانید تعداد را تغییر دهید و آیتم را به فاکتور اضافه کنید.</p>
            </div>

            <section class="pos-bom-total-card" aria-label="خلاصه قیمت">
              <div>
                <span>قیمت هر واحد</span>
                <strong>{{ formatMoney(preview.unitPrice || 0, currency) }}</strong>
              </div>
              <div class="pos-bom-total-divider"></div>
              <div class="pos-bom-total-card--main">
                <span>مجموع این آیتم</span>
                <strong>{{ formatMoney(preview.lineTotal || 0, currency) }}</strong>
              </div>
            </section>
          </template>
        </div>

        <footer class="pos-bom-footer">
          <div class="pos-bom-footer-total">
            <span>مبلغ آیتم</span>
            <strong>{{ formatMoney(preview.lineTotal || 0, currency) }}</strong>
          </div>
          <div class="pos-bom-footer-actions">
            <button type="button" class="pos-bom-secondary-btn" @click="$emit('close')">انصراف</button>
            <button
              type="button"
              class="pos-bom-confirm-btn"
              :disabled="loading || !!error || !item"
              @click="$emit('confirm')"
            >
              <Check v-if="!loading" :size="17" :stroke-width="2.5" />
              <span>{{ loading ? 'در حال دریافت...' : confirmLabel }}</span>
            </button>
          </div>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import {
  AlertCircle,
  Check,
  ListChecks,
  Minus,
  Package,
  Plus,
  SlidersHorizontal,
  Wheat,
  X,
} from 'lucide-vue-next'
import IngredientQuantityEditor from '@/components/IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from '@/components/ModifierRecipeImpactSelector.vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  item: { type: Object, default: null },
  ingredients: { type: Array, default: () => [] },
  modifierGroups: { type: Array, default: () => [] },
  customization: {
    type: Object,
    default: () => ({
      ingredient_adjustments: [],
      selected_modifiers: [],
      selected_alternatives: [],
    }),
  },
  qty: { type: Number, default: 1 },
  preview: {
    type: Object,
    default: () => ({ unitPrice: 0, lineTotal: 0 }),
  },
  currency: { type: String, default: 'IRR' },
  confirmLabel: { type: String, default: 'افزودن به سبد' },
})

const emit = defineEmits(['close', 'update:qty', 'update-customization', 'update-modifiers', 'confirm'])
const titleId = `pos-bom-title-${Math.random().toString(36).slice(2, 9)}`
let previousBodyOverflow = ''

function faCount(value) {
  const number = Number(value || 0)
  return Number.isFinite(number) ? number.toLocaleString('fa-IR') : '۰'
}

function onWindowKeydown(event) {
  if (props.open && event.key === 'Escape') {
    event.preventDefault()
    emit('close')
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (typeof document === 'undefined') return
    if (isOpen) {
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', onWindowKeydown)
    } else {
      document.body.style.overflow = previousBodyOverflow
      document.removeEventListener('keydown', onWindowKeydown)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = previousBodyOverflow
  document.removeEventListener('keydown', onWindowKeydown)
})
</script>

<style scoped>
.pos-bom-overlay {
  --pos-surface-color: var(--mg-bg-surface);
  --surface: var(--mg-bg-surface);
  --surface-alt: var(--mg-bg-page);
  --text-primary: var(--mg-text-main);
  --text-muted: var(--mg-text-muted);
  --ink-900: var(--mg-text-main);
  --ink-800: var(--mg-text-main);
  --ink-700: var(--mg-text-muted);
  --accent-green: var(--mg-primary);
  --accent-gold: var(--mg-success);
  --palette-deep-sapphire-rgb: var(--mg-primary-rgb);
  --palette-deep-saffron-rgb: var(--mg-success-rgb);
  --palette-eggshell-rgb: 251 247 241;
  --danger: var(--mg-danger);
  --danger-rgb: var(--mg-danger-rgb);
  position: fixed;
  inset: 0;
  z-index: 11000;
  overflow: hidden;
  touch-action: none;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgb(24 18 14 / 0.52);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  animation: pos-bom-overlay-in 0.18s ease-out;
}

.pos-bom-modal {
  width: min(940px, 100%);
  height: min(900px, calc(100dvh - 2rem));
  max-height: min(900px, calc(100dvh - 2rem));
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: var(--mg-text-main);
  background: linear-gradient(180deg, var(--mg-bg-surface) 0%, var(--mg-bg-page) 100%);
  border: 1px solid color-mix(in srgb, var(--mg-border) 88%, transparent);
  border-radius: 26px;
  box-shadow: 0 34px 90px rgb(30 20 13 / 0.34), 0 0 0 1px rgb(255 255 255 / 0.08) inset;
  animation: pos-bom-modal-in 0.22s ease-out;
}

.pos-bom-header {
  flex: 0 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.05rem 1.2rem 0.95rem;
  background: color-mix(in srgb, var(--mg-bg-surface) 94%, var(--mg-primary) 6%);
  border-bottom: 1px solid color-mix(in srgb, var(--mg-border) 72%, transparent);
}

.pos-bom-heading {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.78rem;
}

.pos-bom-heading-icon,
.pos-bom-section-icon,
.pos-bom-state-icon,
.overview-icon {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pos-bom-heading-icon {
  width: 46px;
  height: 46px;
  border-radius: 15px;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, var(--mg-bg-surface) 88%);
  border: 1px solid color-mix(in srgb, var(--mg-primary) 26%, transparent);
}

.pos-bom-heading-copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.pos-bom-kicker {
  color: var(--mg-primary);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.pos-bom-heading-copy h2 {
  margin: 0;
  overflow: hidden;
  color: var(--mg-text-main);
  font-size: clamp(1rem, 2vw, 1.25rem);
  font-weight: 900;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pos-bom-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.7rem;
  color: var(--mg-text-muted);
  font-size: 0.7rem;
}

.pos-bom-close {
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid color-mix(in srgb, var(--mg-border) 82%, transparent);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  cursor: pointer;
  transition: 0.16s ease;
}

.pos-bom-close:hover,
.pos-bom-close:focus-visible {
  color: var(--mg-danger);
  border-color: color-mix(in srgb, var(--mg-danger) 42%, transparent);
  background: color-mix(in srgb, var(--mg-danger) 8%, var(--mg-bg-surface) 92%);
}

.pos-bom-body {
  min-height: 0;
  height: 0;
  flex: 1 1 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  touch-action: pan-y;
  padding: 0.95rem 1.1rem 1.1rem;
  display: grid;
  align-content: start;
  gap: 0.75rem;
  scrollbar-width: thin;
  scrollbar-color: var(--mg-border) transparent;
}

.pos-bom-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
}

.pos-bom-overview-item {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.48rem;
  padding: 0.62rem 0.7rem;
  border: 1px solid color-mix(in srgb, var(--mg-border) 62%, transparent);
  border-radius: 15px;
  background: color-mix(in srgb, var(--mg-bg-surface) 84%, var(--mg-bg-page) 16%);
}

.pos-bom-overview-item > span:last-child {
  min-width: 0;
  display: grid;
  gap: 0.08rem;
}

.pos-bom-overview-item small {
  color: var(--mg-text-muted);
  font-size: 0.67rem;
}

.pos-bom-overview-item strong {
  overflow: hidden;
  color: var(--mg-text-main);
  font-size: 0.78rem;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-icon {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

.overview-icon--accent {
  color: var(--mg-success);
  background: color-mix(in srgb, var(--mg-success) 13%, transparent);
}

.pos-bom-overview-item--price {
  justify-content: space-between;
}

.pos-bom-overview-item--price strong {
  color: var(--mg-primary);
}

.pos-bom-quantity-card,
.pos-bom-editor-card,
.pos-bom-total-card {
  border: 1px solid color-mix(in srgb, var(--mg-border) 66%, transparent);
  border-radius: 19px;
  background: color-mix(in srgb, var(--mg-bg-surface) 93%, var(--mg-bg-page) 7%);
  box-shadow: 0 8px 22px rgb(52 38 31 / 0.045);
}

.pos-bom-quantity-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 0.9rem;
}

.pos-bom-section-title {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.pos-bom-section-title > div:last-child {
  min-width: 0;
}

.pos-bom-section-title h3 {
  margin: 0;
  color: var(--mg-text-main);
  font-size: 0.86rem;
  font-weight: 900;
}

.pos-bom-section-title p {
  margin: 0.15rem 0 0;
  color: var(--mg-text-muted);
  font-size: 0.68rem;
  line-height: 1.55;
}

.pos-bom-section-icon {
  width: 33px;
  height: 33px;
  border-radius: 11px;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

.pos-bom-section-icon--green {
  color: var(--mg-success);
  background: color-mix(in srgb, var(--mg-success) 13%, transparent);
}

.pos-bom-section-icon--gold {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.pos-bom-stepper {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.24rem;
  border: 1px solid color-mix(in srgb, var(--mg-border) 80%, transparent);
  border-radius: 13px;
  background: var(--mg-bg-page);
}

.pos-bom-stepper button {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 9px;
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
  cursor: pointer;
  transition: 0.15s ease;
}

.pos-bom-stepper button:hover:not(:disabled),
.pos-bom-stepper button:focus-visible {
  border-color: color-mix(in srgb, var(--mg-primary) 30%, transparent);
  background: color-mix(in srgb, var(--mg-primary) 10%, var(--mg-bg-surface) 90%);
}

.pos-bom-stepper button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.pos-bom-stepper strong {
  min-width: 32px;
  color: var(--mg-text-main);
  font-size: 0.92rem;
  text-align: center;
}

.pos-bom-editor-card {
  overflow: hidden;
}

.pos-bom-editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.78rem 0.9rem;
  border-bottom: 1px solid color-mix(in srgb, var(--mg-border) 48%, transparent);
  background: color-mix(in srgb, var(--mg-bg-page) 42%, var(--mg-bg-surface) 58%);
}

.pos-bom-count-badge {
  flex: 0 0 auto;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  color: var(--mg-success);
  background: color-mix(in srgb, var(--mg-success) 12%, transparent);
  font-size: 0.66rem;
  font-weight: 800;
  white-space: nowrap;
}

.pos-bom-count-badge--gold {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.pos-bom-editor-body {
  padding: 0.78rem;
}

.pos-bom-total-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.78rem 0.95rem;
  background: linear-gradient(135deg, color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface) 91%), color-mix(in srgb, var(--mg-success) 8%, var(--mg-bg-surface) 92%));
}

.pos-bom-total-card > div:not(.pos-bom-total-divider) {
  min-width: 0;
  display: grid;
  gap: 0.16rem;
}

.pos-bom-total-card span {
  color: var(--mg-text-muted);
  font-size: 0.68rem;
}

.pos-bom-total-card strong {
  color: var(--mg-text-main);
  font-size: 0.9rem;
  font-weight: 900;
}

.pos-bom-total-card--main strong {
  color: var(--mg-primary);
  font-size: 1.04rem;
}

.pos-bom-total-divider {
  width: 1px;
  align-self: stretch;
  background: color-mix(in srgb, var(--mg-border) 72%, transparent);
}

.pos-bom-state {
  min-height: 190px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 0.38rem;
  padding: 1.25rem;
  border: 1px dashed color-mix(in srgb, var(--mg-border) 84%, transparent);
  border-radius: 19px;
  text-align: center;
  background: color-mix(in srgb, var(--mg-bg-surface) 82%, var(--mg-bg-page) 18%);
}

.pos-bom-state-icon {
  width: 46px;
  height: 46px;
  border-radius: 15px;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 11%, transparent);
}

.pos-bom-state--error .pos-bom-state-icon {
  color: var(--mg-danger);
  background: color-mix(in srgb, var(--mg-danger) 10%, transparent);
}

.pos-bom-state strong {
  color: var(--mg-text-main);
  font-size: 0.88rem;
}

.pos-bom-state p {
  max-width: 560px;
  margin: 0;
  color: var(--mg-text-muted);
  font-size: 0.75rem;
  line-height: 1.75;
}

.pos-bom-loading {
  display: grid;
  gap: 0.7rem;
  padding: 0.2rem 0;
  color: var(--mg-text-muted);
  font-size: 0.75rem;
  text-align: center;
}

.pos-bom-skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

.pos-bom-skeleton {
  height: 110px;
  border-radius: 17px;
  background: linear-gradient(100deg, color-mix(in srgb, var(--mg-bg-page) 82%, var(--mg-bg-surface) 18%) 25%, color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface) 92%) 50%, color-mix(in srgb, var(--mg-bg-page) 82%, var(--mg-bg-surface) 18%) 75%);
  background-size: 220% 100%;
  animation: pos-bom-shimmer 1.25s infinite;
}

.pos-bom-skeleton--summary {
  height: 76px;
}

.pos-bom-loading p {
  margin: 0;
}

.pos-bom-footer {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.78rem 1.1rem;
  border-top: 1px solid color-mix(in srgb, var(--mg-border) 72%, transparent);
  background: color-mix(in srgb, var(--mg-bg-surface) 92%, var(--mg-bg-page) 8%);
  box-shadow: 0 -10px 28px rgb(52 38 31 / 0.06);
}

.pos-bom-footer-total {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.pos-bom-footer-total span {
  color: var(--mg-text-muted);
  font-size: 0.68rem;
}

.pos-bom-footer-total strong {
  color: var(--mg-primary);
  font-size: 1.08rem;
  font-weight: 900;
  white-space: nowrap;
}

.pos-bom-footer-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.pos-bom-secondary-btn,
.pos-bom-confirm-btn {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  border-radius: 12px;
  padding: 0.55rem 0.9rem;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  cursor: pointer;
  transition: 0.16s ease;
}

.pos-bom-secondary-btn {
  border: 1px solid color-mix(in srgb, var(--mg-border) 90%, transparent);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
}

.pos-bom-secondary-btn:hover,
.pos-bom-secondary-btn:focus-visible {
  border-color: color-mix(in srgb, var(--mg-primary) 35%, transparent);
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface) 93%);
}

.pos-bom-confirm-btn {
  min-width: 150px;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 88%, #000 12%);
  background: var(--mg-primary);
  color: #fff;
  box-shadow: 0 7px 18px color-mix(in srgb, var(--mg-primary) 24%, transparent);
}

.pos-bom-confirm-btn:hover:not(:disabled),
.pos-bom-confirm-btn:focus-visible {
  filter: brightness(0.96);
  transform: translateY(-1px);
  box-shadow: 0 9px 22px color-mix(in srgb, var(--mg-primary) 32%, transparent);
}

.pos-bom-confirm-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.pos-bom-overlay button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--mg-primary) 38%, transparent);
  outline-offset: 2px;
}

/* The shared editors use their own public-menu tokens. Map them to the
   management palette and keep their compact cards readable in this modal. */
.pos-bom-modal :deep(.is-compact .ingredient-card),
.pos-bom-modal :deep(.is-compact .group) {
  background: color-mix(in srgb, var(--mg-bg-page) 72%, var(--mg-bg-surface) 28%);
  border-color: color-mix(in srgb, var(--mg-border) 68%, transparent);
}

.pos-bom-modal :deep(.is-compact .card-name),
.pos-bom-modal :deep(.is-compact .quantity-copy strong),
.pos-bom-modal :deep(.is-compact .section-title),
.pos-bom-modal :deep(.is-compact .section h3),
.pos-bom-modal :deep(.is-compact .group h4) {
  color: var(--mg-text-main);
}

.pos-bom-modal :deep(.is-compact .card-qty),
.pos-bom-modal :deep(.is-compact .section-count),
.pos-bom-modal :deep(.is-compact .group small),
.pos-bom-modal :deep(.is-compact .choice-submeta small) {
  color: var(--mg-text-muted);
}

.pos-bom-modal :deep(.is-compact .option-choice),
.pos-bom-modal :deep(.is-compact .quantity-row),
.pos-bom-modal :deep(.is-compact .qty-pill),
.pos-bom-modal :deep(.is-compact .qty-btn) {
  color: var(--mg-text-main);
  background: var(--mg-bg-surface);
  border-color: color-mix(in srgb, var(--mg-border) 68%, transparent);
}

.pos-bom-modal :deep(.is-compact .option-choice.active),
.pos-bom-modal :deep(.is-compact .quantity-row.active) {
  background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface) 91%);
  border-color: color-mix(in srgb, var(--mg-primary) 42%, transparent);
}

@keyframes pos-bom-overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pos-bom-modal-in {
  from { opacity: 0; transform: translateY(12px) scale(0.985); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes pos-bom-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -20% 0; }
}

@media (max-width: 720px) {
  .pos-bom-overlay {
    align-items: flex-end;
    padding: 0;
  }

  .pos-bom-modal {
    width: 100%;
    height: min(94dvh, 900px);
    max-height: min(94dvh, 900px);
    border-radius: 25px 25px 0 0;
  }

  .pos-bom-header {
    padding: 0.9rem 0.85rem 0.78rem;
  }

  .pos-bom-body {
    padding: 0.75rem 0.7rem 0.9rem;
  }

  .pos-bom-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pos-bom-overview-item--price {
    grid-column: 1 / -1;
  }

  .pos-bom-footer {
    padding: 0.7rem 0.75rem max(0.75rem, env(safe-area-inset-bottom));
    align-items: stretch;
  }

  .pos-bom-footer-total {
    align-self: center;
  }

  .pos-bom-footer-actions {
    flex: 1 1 auto;
  }

  .pos-bom-secondary-btn,
  .pos-bom-confirm-btn {
    min-height: 44px;
    flex: 1 1 0;
    padding-inline: 0.6rem;
  }

  .pos-bom-confirm-btn {
    min-width: 0;
  }
}

@media (max-width: 430px) {
  .pos-bom-heading-icon {
    width: 40px;
    height: 40px;
    border-radius: 13px;
  }

  .pos-bom-heading {
    gap: 0.55rem;
  }

  .pos-bom-heading-copy h2 {
    font-size: 0.94rem;
  }

  .pos-bom-meta {
    font-size: 0.64rem;
  }

  .pos-bom-quantity-card,
  .pos-bom-editor-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .pos-bom-stepper {
    align-self: stretch;
    justify-content: space-between;
  }

  .pos-bom-stepper strong {
    flex: 1;
  }

  .pos-bom-editor-head {
    gap: 0.55rem;
  }

  .pos-bom-count-badge {
    align-self: flex-start;
  }

  .pos-bom-total-card {
    gap: 0.55rem;
    padding-inline: 0.72rem;
  }

  .pos-bom-total-card strong {
    font-size: 0.82rem;
  }

  .pos-bom-total-card--main strong {
    font-size: 0.92rem;
  }

  .pos-bom-footer {
    gap: 0.55rem;
  }

  .pos-bom-footer-total strong {
    font-size: 0.94rem;
  }

  .pos-bom-footer-actions {
    gap: 0.3rem;
  }

  .pos-bom-secondary-btn,
  .pos-bom-confirm-btn {
    font-size: 0.7rem;
  }
}
</style>
