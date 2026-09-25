<template>
  <div class="cart-page">
    <section class="cart-shell">
      <section class="cart-frame">
        <header class="cart-heading">
          <a class="icon-btn" href="/menu" aria-label="بازگشت به منو">
            <ChevronRight :size="20" aria-hidden="true" />
          </a>
          <div class="cart-heading-copy">
            <p class="cart-eyebrow">سفارش شما</p>
            <h1>سبد سفارش</h1>
          </div>
          <span class="cart-count-label">{{ totalQty }} آیتم</span>
        </header>

        <OrderContextStrip :currency="currency" />

        <div class="cart-content" :class="{ 'cart-content--empty': !cartState.lines.length }">
          <section class="line-list">
            <CartLineEditor
              v-for="line in cartState.lines"
              :key="line.id"
              :line="line"
              :currency="currency"
              @qty-change="setQty(line.id, $event)"
              @remove="remove(line.id)"
              @edit-customization="openCustomization(line)"
            />

            <div class="empty-box" v-if="!cartState.lines.length">
              <ShoppingBag :size="40" aria-hidden="true" /><h2>سبد شما منتظر یک انتخاب خوشمزه است</h2><p class="muted">از منو شروع کنید و غذای دلخواهتان را اضافه کنید.</p>
              <a href="/menu" class="go-menu">مشاهده منو</a>
            </div>
          </section>

          <section v-if="cartState.lines.length" class="summary-panel">
          <h2 class="summary-title">خلاصه سفارش</h2>
          <div class="sum-row">
            <span>جمع اقلام</span>
            <strong>{{ formatMoney(totals.subtotal, currency) }}</strong>
          </div>
          <div class="sum-row" v-if="totals.delivery_fee > 0">
            <span>هزینه ارسال</span>
            <strong>{{ formatMoney(totals.delivery_fee, currency) }}</strong>
          </div>
          <div class="sum-row muted-fee" v-else>
            <span>ارسال</span>
            <strong>{{ cartState.orderContext.order_type === 'delivery' ? 'پس از تایید شعبه' : 'بدون هزینه ارسال' }}</strong>
          </div>
          <div class="sum-row total">
            <span>مبلغ قابل پرداخت</span>
            <strong>{{ formatMoney(totals.grand_total, currency) }}</strong>
          </div>

          <a class="checkout-btn" :class="{ disabled: !cartState.lines.length }" href="/checkout" @click.prevent="openCheckout">
            {{ hasContext ? 'ادامه سفارش' : 'انتخاب روش دریافت' }}
          </a>
          <p class="error" v-if="error">{{ error }}</p>
          </section>
        </div>
      </section>
    </section>

    <div v-if="cartState.lines.length" class="cart-mobile-checkout">
      <div><small>{{ totalQty.toLocaleString('fa-IR') }} آیتم</small><strong>{{ formatMoney(totals.grand_total, currency) }}</strong></div>
      <button class="checkout-btn" type="button" @click="openCheckout">{{ hasContext ? 'ادامه سفارش' : 'روش دریافت' }}<ChevronLeft :size="18" /></button>
    </div>

    <MenuQuickAddSheet
      :open="editorOpen"
      :item="editorItem"
      :editing-line="activeLine"
      :currency="currency"
      :branch="cartState.orderContext.branch || ''"
      @close="closeEditor"
      @confirm="applyCustomization"
    />
  </div>
</template>

<script setup>
import { ChevronLeft, ChevronRight, ShoppingBag } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import CartLineEditor from '@/components/CartLineEditor.vue'
import MenuQuickAddSheet from '@/components/MenuQuickAddSheet.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { cartState, getLineById, removeLine, setLineQty, upsertLine } from '@/stores/cartStore'
import { getMenuBoot } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { orderContextIssue } from '@/utils/customerOrderValidation'
import { buildEditedCartLine } from '@/utils/cartEditPayload'
import { calculateOrderTotals, orderContextChangeUrl, ORDER_FLOW_CURRENCY_FALLBACK } from '@/utils/orderFlow'

const currency = ref(ORDER_FLOW_CURRENCY_FALLBACK)
const error = ref('')
const editorOpen = ref(false)
const activeLineId = ref('')

const totalQty = computed(() => cartState.lines.reduce((sum, line) => sum + Number(line.qty || 0), 0))
const hasContext = computed(() => Boolean(cartState.orderContext?.order_type))
const activeLine = computed(() => getLineById(activeLineId.value) || null)
const editorItem = computed(() => activeLine.value ? {
  slug: activeLine.value.item_slug,
  title: activeLine.value.item_title,
  image: activeLine.value.item_image,
  base_price: activeLine.value.base_price,
} : null)
const totals = computed(() => calculateOrderTotals({ lines: cartState.lines, context: cartState.orderContext }))

function openCheckout() {
  if (!cartState.lines.length) return
  if (!hasContext.value) {
    window.location.href = '/order/type'
    return
  }
  window.location.href = orderContextIssue(cartState.orderContext) ? orderContextChangeUrl(cartState.orderContext) : '/checkout'
}

function setQty(lineId, qty) {
  const nextQty = Number(qty || 0)
  if (nextQty <= 0) {
    remove(lineId)
    return
  }
  setLineQty(lineId, nextQty)
}

function remove(lineId) {
  if (activeLineId.value === lineId) closeEditor()
  removeLine(lineId)
}

function closeEditor() {
  editorOpen.value = false
  activeLineId.value = ''
}

function openCustomization(line) {
  if (!line?.id) return
  activeLineId.value = line.id
  editorOpen.value = true
}

function applyCustomization(preview) {
  const line = activeLine.value
  if (!line) return
  upsertLine(buildEditedCartLine(line, preview))
  closeEditor()
}

onMounted(async () => {
  try {
    const boot = await getMenuBoot(cartState.orderContext.branch || '')
    currency.value = boot?.currency || ORDER_FLOW_CURRENCY_FALLBACK
  } catch {
    currency.value = ORDER_FLOW_CURRENCY_FALLBACK
  }
})
</script>

<style scoped>
.summary-title { font-size: 1.05rem; margin: 0; }
.cart-mobile-checkout { display: none; }
.empty-box { min-height: 300px; }
.empty-box h2 { font-size: 1.1rem; margin: 0; }

.cart-shell {
  width: min(980px, calc(100% - 2rem));
  margin: 1rem auto 6rem;
  color: var(--ds-color-text-primary, var(--text-primary));
}

.cart-frame {
  display: grid;
  gap: 1rem;
  padding-bottom: 1rem;
}

.icon-btn {
  width: 44px;
  height: 44px;
  text-decoration: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-surface-raised, #fff);
  box-shadow: var(--shadow-soft);
  color: var(--ds-color-action-primary, var(--accent-green));
}

.cart-heading {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 1rem;
}

.cart-heading-copy { min-width: 0; }

.cart-eyebrow {
  margin: 0 0 0.25rem;
  color: var(--ds-color-text-muted, var(--text-muted));
  font-size: 0.84rem;
}

.cart-frame h1 {
  margin: 0;
  font-size: clamp(1.5rem, 5vw, 2.35rem);
}

.cart-count-label {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  padding: 0.42rem 0.7rem;
  border-radius: 999px;
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
  font-weight: 800;
  font-size: 0.83rem;
}

.cart-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  align-items: start;
  gap: 1rem;
}

.cart-content--empty { grid-template-columns: 1fr; }

.line-list {
  display: grid;
  gap: 0.85rem;
}

.empty-box,
.summary-panel {
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.13));
  border-radius: 26px;
  background: var(--ds-color-surface-raised, rgb(var(--palette-eggshell-rgb) / 0.96));
  box-shadow: var(--shadow-soft);
  padding: 1rem;
}

.empty-box {
  text-align: center;
  display: grid;
  gap: 0.75rem;
  place-items: center;
}

.go-menu,
.checkout-btn {
  min-height: 48px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.72rem 1rem;
  font-weight: 850;
}

.go-menu {
  border: 1px solid color-mix(in srgb, var(--ds-color-status-success) 28%, var(--ds-color-border));
  background: var(--ds-color-status-success-soft);
  color: var(--ds-color-status-success);
  text-decoration: none;
}

.checkout-btn {
  border: 1px solid var(--ds-color-action-accent);
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  text-decoration: none;
  box-shadow: 0 10px 24px color-mix(in srgb, var(--ds-color-action-accent) 22%, transparent);
  transition: transform var(--ds-motion-fast) ease, filter var(--ds-motion-fast) ease;
}

.checkout-btn:hover {
  transform: translateY(-1px);
  filter: brightness(0.96);
}

.cart-shell :is(a, button):focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
}

.summary-panel {
  position: sticky;
  top: 5rem;
  display: grid;
  gap: 0.3rem;
  border-radius: 28px;
}

.sum-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.8rem;
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.1));
}

.sum-row.total {
  border-bottom: 0;
  font-size: 1.05rem;
}

.muted-fee strong {
  color: var(--text-muted);
  font-size: 0.86rem;
}

.checkout-btn {
  width: 100%;
  margin-top: 0.55rem;
}

.checkout-btn.disabled {
  opacity: 0.55;
  pointer-events: none;
}

.error {
  margin: 0.6rem 0 0;
  color: var(--ds-color-status-danger, var(--danger));
}

@media (max-width: 919px) {
  .cart-mobile-checkout { position: fixed; bottom: calc(5rem + env(safe-area-inset-bottom)); z-index: 110; inset-inline: .75rem; display: flex; align-items: center; gap: .75rem; padding: .75rem; border-radius: var(--ds-radius-md); border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
  .cart-mobile-checkout > div { display: grid; gap: .2rem; flex: 1; }
  .cart-mobile-checkout small { color: var(--ds-color-text-muted); }
  .cart-mobile-checkout strong { font-size: .9rem; white-space: nowrap; }
  .cart-mobile-checkout .checkout-btn { width: auto; margin: 0; gap: .4rem; border-radius: var(--ds-radius-md); }
  .summary-panel > .checkout-btn { display: none; }
  .cart-shell { padding-bottom: 5rem; }
}
@media (max-width: 760px) {
  .cart-shell {
    width: min(100% - 1rem, 100%);
    margin-top: 0.6rem;
    margin-bottom: calc(7.5rem + env(safe-area-inset-bottom));
  }

  .empty-box,
  .summary-panel {
    border-radius: 22px;
  }

  .cart-content { grid-template-columns: 1fr; }
  .summary-panel {
    position: static;
  }
  .cart-heading { gap: 0.65rem; }
}
</style>
