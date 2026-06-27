<template>
  <LiquidGlassBackdrop>
    <section class="cart-shell">
      <section class="cart-frame">
        <header class="top-row">
          <a class="icon-btn" href="/menu" aria-label="بازگشت به منو">←</a>
          <p>سبد خرید</p>
          <span class="top-spacer" aria-hidden="true"></span>
        </header>

        <h1>آیتم‌ها <span>{{ totalQty }}</span></h1>

        <OrderContextStrip :currency="currency" />

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
            <p class="muted">سبد سفارش خالی است.</p>
            <a href="/menu" class="go-menu">ورود به منو</a>
          </div>
        </section>

        <div class="grabber"></div>

        <section class="summary-panel">
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
            {{ hasContext ? 'ادامه به تکمیل سفارش →' : 'انتخاب نوع سفارش →' }}
          </a>
          <p class="error" v-if="error">{{ error }}</p>
        </section>
      </section>
    </section>

    <CartToppingSheet
      :open="editorOpen"
      :line="activeLine"
      :ingredients="activeIngredients"
      :customization="activeCustomization"
      :currency="currency"
      :loading="editorLoading"
      @close="closeEditor"
      @apply="applyCustomization"
    />
  </LiquidGlassBackdrop>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import CartLineEditor from '@/components/CartLineEditor.vue'
import CartToppingSheet from '@/components/CartToppingSheet.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { cartState, getLineById, removeLine, setLineQty, upsertLine } from '@/stores/cartStore'
import { getItemDetail, getMenuBoot } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { calculateOrderTotals, ORDER_FLOW_CURRENCY_FALLBACK } from '@/utils/orderFlow'

const currency = ref(ORDER_FLOW_CURRENCY_FALLBACK)
const error = ref('')
const editorOpen = ref(false)
const editorLoading = ref(false)
const activeLineId = ref('')
const activeIngredients = ref([])
const activeModifierGroups = ref([])
const activeCustomization = ref({ ingredient_adjustments: [], selected_modifiers: [] })

const totalQty = computed(() => cartState.lines.reduce((sum, line) => sum + Number(line.qty || 0), 0))
const hasContext = computed(() => Boolean(cartState.orderContext?.order_type))
const activeLine = computed(() => getLineById(activeLineId.value) || null)
const totals = computed(() => calculateOrderTotals({ lines: cartState.lines, context: cartState.orderContext }))

function openCheckout() {
  if (!cartState.lines.length) return
  if (!hasContext.value) {
    window.location.href = '/order/type'
    return
  }
  window.location.href = '/checkout'
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
  editorLoading.value = false
  activeLineId.value = ''
  activeIngredients.value = []
  activeModifierGroups.value = []
  activeCustomization.value = { ingredient_adjustments: [], selected_modifiers: [] }
}

async function openCustomization(line) {
  if (!line?.id) return
  activeLineId.value = line.id
  editorOpen.value = true
  editorLoading.value = true

  const fallbackIngredients = Array.isArray(line.ingredient_catalog) ? line.ingredient_catalog : []
  const fallbackModifiers = Array.isArray(line.modifier_groups_catalog) ? line.modifier_groups_catalog : []
  activeIngredients.value = fallbackIngredients
  activeModifierGroups.value = fallbackModifiers
  activeCustomization.value = sanitizeCustomization(line.customization || {}, fallbackIngredients)

  try {
    const detail = await getItemDetail(line.item_slug)
    const ingredients = detail.ingredients || fallbackIngredients
    const modifiers = detail.modifier_groups || fallbackModifiers
    activeIngredients.value = ingredients
    activeModifierGroups.value = modifiers
    activeCustomization.value = sanitizeCustomization(line.customization || {}, ingredients)
  } catch (_) {
    // Keep fallback catalogs when detail fetch fails; cart editing remains available.
  } finally {
    editorLoading.value = false
  }
}

function applyCustomization(nextCustomization) {
  const line = activeLine.value
  if (!line) return

  const cleanCustomization = sanitizeCustomization(nextCustomization || {}, activeIngredients.value)
  const preview = estimateLine({
    basePrice: Number(line.base_price || 0),
    qty: Number(line.qty || 1),
    ingredients: activeIngredients.value,
    modifierGroups: activeModifierGroups.value,
    customization: cleanCustomization,
  })

  upsertLine({
    ...line,
    id: line.id,
    qty: preview.qty,
    customization: preview.customization,
    unit_price_preview: preview.unitPrice,
    line_total_preview: preview.lineTotal,
    ingredient_catalog: activeIngredients.value,
    modifier_groups_catalog: activeModifierGroups.value,
  })

  editorOpen.value = false
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
.cart-shell {
  width: min(980px, calc(100% - 2rem));
  margin: 1rem auto 6rem;
  color: var(--text-primary);
}

.cart-frame {
  display: grid;
  gap: 1rem;
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.icon-btn,
.top-spacer {
  width: 44px;
  height: 44px;
}

.icon-btn {
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  box-shadow: var(--shadow-soft);
  color: var(--accent-green);
  font-weight: 900;
}

.top-row p {
  margin: 0;
  font-weight: 800;
}

.cart-frame h1 {
  margin: 0;
  font-size: clamp(1.5rem, 5vw, 2.35rem);
}

.cart-frame h1 span {
  color: var(--accent-gold);
}

.line-list {
  display: grid;
  gap: 0.85rem;
}

.empty-box,
.summary-panel {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.13);
  border-radius: 26px;
  background: rgb(var(--palette-eggshell-rgb) / 0.96);
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
  min-height: 46px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.72rem 1rem;
  background: var(--accent-green);
  color: #fff;
  font-weight: 850;
}

.grabber {
  width: 48px;
  height: 5px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  margin: 0 auto;
}

.summary-panel {
  display: grid;
  gap: 0.15rem;
}

.sum-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.8rem;
  padding: 0.7rem 0;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
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
  color: var(--danger);
}

@media (max-width: 640px) {
  .cart-shell {
    width: min(100% - 1rem, 100%);
    margin-top: 0.6rem;
  }

  .empty-box,
  .summary-panel {
    border-radius: 22px;
  }
}
</style>
