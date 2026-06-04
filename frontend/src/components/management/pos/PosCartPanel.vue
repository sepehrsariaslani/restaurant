<template>
  <section class="cart-panel">
    <div class="mode-row">
      <button
        v-for="mode in orderModes"
        :key="mode.value"
        type="button"
        :class="{ active: orderMode === mode.value }"
        @click="$emit('update:orderMode', mode.value)"
      >
        {{ mode.label }}
      </button>
    </div>

    <label class="field">
      <span>جایگاه</span>
      <SearchableDropdown
        :model-value="place"
        :options="normalizedPlaceOptions"
        placeholder="انتخاب کنید"
        search-placeholder="جستجوی جایگاه..."
        include-empty-option
        empty-label="انتخاب کنید"
        tone="dark"
        @update:model-value="$emit('update:place', $event)"
      />
    </label>

    <div class="cart-head">
      <h3>سبد خرید</h3>
      <button type="button" class="clear-btn" @click="$emit('clear-cart')">حذف همه</button>
    </div>

    <div class="cart-list" v-if="cartLines.length">
      <article
        v-for="line in cartLines"
        :key="line.line_id"
        class="cart-row"
        :class="{ active: selectedLineId === line.line_id }"
        @click="$emit('update:selectedLineId', line.line_id)"
      >
        <div class="line-main">
          <strong>{{ line.title }}</strong>
          <small>{{ formatMoney(rowTotal(line), currency) }}</small>
          <small class="line-custom" v-if="canEditCustomization(line)">سفارشی سازی فعال</small>
          <ul class="line-custom-list" v-if="customizationSummary(line).length">
            <li v-for="(entry, idx) in customizationSummary(line)" :key="`${line.line_id}-custom-${idx}`">{{ entry }}</li>
          </ul>
          <small class="line-note" v-if="line.note">{{ line.note }}</small>
        </div>

        <div class="line-actions">
          <button
            v-if="canEditCustomization(line)"
            type="button"
            class="icon bom"
            title="ویرایش سفارشی سازی"
            @click.stop="$emit('edit-line-customization', line)"
          >
            BOM
          </button>
          <button type="button" class="icon" title="ویرایش" @click.stop="$emit('edit-line-note', line)">✎</button>
          <div class="counter">
            <button type="button" @click.stop="$emit('decrement-line', line)">-</button>
            <span>{{ qtyText(line.qty) }}</span>
            <button type="button" @click.stop="$emit('increment-line', line)">+</button>
          </div>
          <button type="button" class="icon danger" title="حذف" @click.stop="$emit('remove-line', line)">×</button>
        </div>
      </article>
    </div>
    <p class="hint" v-else>سبد خرید خالی است.</p>

    <section class="financial-box">
      <div class="financial-head">
        <h4 class="financial-title">متغیرهای مالی</h4>
      </div>

      <label class="wallet-row">
        <span>استفاده از کیف پول ({{ formatMoney(financial.walletBalance || 0, currency) }})</span>
        <input
          type="checkbox"
          :checked="Boolean(financial.useWallet)"
          @change="patchFinancial({ useWallet: $event.target.checked })"
        />
      </label>

      <div class="discount-row">
        <span class="discount-label">تخفیف</span>
        <div class="discount-input-group">
          <PersianNumberInput
            :model-value="financial.discountValue"
            input-class="dark-input discount-input"
            placeholder="0"
            :min="0"
            style="flex: 1; min-width: 0;"
            @update:model-value="patchFinancial({ discountValue: $event })"
          />
          <button type="button" class="discount-type-btn" @click="toggleDiscountType">
            {{ financial.discountType === 'percent' ? '%' : '﷼' }}
          </button>
        </div>
      </div>

      <template v-if="showAdvancedFinancial">
        <label class="field inline">
          <span>کد تخفیف / معرف</span>
          <div class="code-row">
            <input
              class="input dark-input"
              :value="financial.couponCode"
              @input="patchFinancial({ couponCode: $event.target.value })"
              placeholder="کد"
            />
            <button type="button" class="check-btn" @click="$emit('verify-coupon')">بررسی</button>
          </div>
        </label>

        <label class="field">
          <span>معاف از مالیات</span>
          <input
            type="checkbox"
            :checked="Boolean(financial.taxExempt)"
            @change="patchFinancial({ taxExempt: $event.target.checked })"
          />
        </label>

        <label class="field">
          <span>ارزش افزوده</span>
          <PersianNumberInput
            :model-value="financial.taxAmount"
            input-class="dark-input"
            placeholder="0"
            :min="0"
            :disabled="Boolean(financial.taxExempt)"
            @update:model-value="patchFinancial({ taxAmount: $event })"
          />
        </label>

        <label class="field">
          <span>انعام</span>
          <PersianNumberInput
            :model-value="financial.tipAmount"
            input-class="dark-input"
            placeholder="0"
            :min="0"
            @update:model-value="patchFinancial({ tipAmount: $event })"
          />
        </label>

        <div class="radio-group">
          <span>حق سرویس</span>
          <label>
            <input
              type="radio"
              name="service-type"
              value="fixed"
              :checked="financial.serviceType === 'fixed'"
              @change="patchFinancial({ serviceType: 'fixed' })"
            />
            مبلغی
          </label>
          <label>
            <input
              type="radio"
              name="service-type"
              value="percent"
              :checked="financial.serviceType === 'percent'"
              @change="patchFinancial({ serviceType: 'percent' })"
            />
            درصدی
          </label>
        </div>
        <PersianNumberInput
          :model-value="financial.serviceValue"
          input-class="dark-input"
          placeholder="0"
          :min="0"
          @update:model-value="patchFinancial({ serviceValue: $event })"
        />
      </template>

      <label class="field">
        <span>یادداشت سفارش</span>
        <input class="input dark-input" :value="note" @input="$emit('update:note', $event.target.value)" />
      </label>
    </section>

    <div class="summary-box">
      <div class="sum-line"><span>جمع کالاها</span><strong>{{ formatMoney(totals.itemsTotal || 0, currency) }}</strong></div>
      <div class="sum-line"><span>تخفیف</span><strong>- {{ formatMoney(totals.discountAmount || 0, currency) }}</strong></div>
      <div class="sum-line"><span>کیف پول</span><strong>- {{ formatMoney(totals.walletApplied || 0, currency) }}</strong></div>
      <div class="sum-line"><span>مالیات</span><strong>{{ formatMoney(totals.taxAmount || 0, currency) }}</strong></div>
      <div class="sum-line"><span>انعام</span><strong>{{ formatMoney(totals.tipAmount || 0, currency) }}</strong></div>
      <div class="sum-line"><span>حق سرویس</span><strong>{{ formatMoney(totals.serviceAmount || 0, currency) }}</strong></div>
      <div class="sum-line payable">
        <span>مبلغ قابل پرداخت</span>
        <strong>{{ formatMoney(totals.payableAmount || 0, currency) }}</strong>
      </div>
    </div>

    <footer class="checkout-actions">
      <button type="button" class="save-btn" :disabled="submitting || !cartLines.length" @click="$emit('submit-order')">
        {{ submitting ? 'در حال ثبت...' : orderMode === 'dine_in' ? 'افزودن به میز' : 'ثبت سفارش' }}
      </button>
      <button
        type="button"
        class="pay-btn"
        :disabled="submitting || !cartLines.length || orderMode === 'dine_in'"
        @click="openPaymentPopup"
      >
        {{ submitting ? 'در حال پرداخت...' : orderMode === 'dine_in' ? 'تسویه از تب میزها' : 'تسویه فاکتور' }}
      </button>
      <button
        type="button"
        class="print-btn"
        :disabled="orderMode === 'dine_in' ? !canPrintTableOrders : !cartLines.length"
        @click="$emit('print-ticket')"
      >
        {{ orderMode === 'dine_in' ? 'چاپ تاییدشده‌ها' : 'چاپ فاکتور' }}
      </button>

      <label>
        <input
          type="checkbox"
          :checked="Boolean(financial.printProduction)"
          @change="patchFinancial({ printProduction: $event.target.checked })"
        />
        چاپ صورتحساب تولید
      </label>
      <label>
        <input
          type="checkbox"
          :checked="Boolean(financial.createNextInvoice)"
          @change="patchFinancial({ createNextInvoice: $event.target.checked })"
        />
        ساخت صورتحساب بعدی
      </label>
    </footer>
  </section>

  <div v-if="showPaymentPopup" class="pay-popup-backdrop" @click.self="showPaymentPopup = false">
    <section class="pay-popup" dir="rtl">
      <header class="pay-popup-head">
        <h3>تسویه فاکتور</h3>
        <button type="button" class="pay-popup-close" @click="showPaymentPopup = false">×</button>
      </header>

      <div class="pay-total-banner">
        <span>مبلغ قابل پرداخت</span>
        <strong>{{ formatMoney(totals.payableAmount || 0, currency) }}</strong>
      </div>

      <div class="pay-splits">
        <div v-for="(split, idx) in paymentSplits" :key="idx" class="pay-split-row">
          <select class="dark-input pay-method-select" v-model="split.method">
            <option value="cash">💵 نقدی</option>
            <option value="card" v-if="paymentBoot?.supports_card">💳 کارتخوان</option>
            <option value="wallet">👛 کیف پول</option>
          </select>
          <PersianNumberInput
            :model-value="split.amount"
            input-class="pay-amount-input"
            placeholder="مبلغ"
            :min="0"
            show-words
            @update:model-value="split.amount = $event"
          />
          <button
            v-if="paymentSplits.length > 1"
            type="button"
            class="pay-split-remove"
            @click="removeSplit(idx)"
          >×</button>
        </div>
      </div>

      <button type="button" class="pay-add-split-btn" @click="addSplit">
        + افزودن روش پرداخت دیگر
      </button>

      <div class="pay-remaining-row" :class="{ zero: splitRemaining <= 0, over: splitRemaining < 0 }">
        <span>{{ splitRemaining < 0 ? 'مازاد پرداختی' : splitRemaining === 0 ? 'تسویه کامل ✓' : 'باقیمانده' }}</span>
        <strong>{{ formatMoney(Math.abs(splitRemaining), currency) }}</strong>
      </div>

      <div class="pay-split-summary" v-if="paymentSplits.length > 1">
        <div v-for="(split, idx) in paymentSplits" :key="`s-${idx}`" class="pay-split-summary-row">
          <span>{{ splitMethodLabel(split.method) }}</span>
          <span>{{ formatMoney(split.amount || 0, currency) }}</span>
        </div>
      </div>

      <footer class="pay-popup-footer">
        <button type="button" class="pay-cancel-btn" @click="showPaymentPopup = false">انصراف</button>
        <button
          type="button"
          class="pay-confirm-btn"
          :disabled="splitRemaining > 0.001 || submitting"
          @click="confirmPayment"
        >
          {{ submitting ? 'در حال ثبت...' : 'تأیید و ثبت پرداخت' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import { formatMoney, formatStatus } from '@/utils/format'

const props = defineProps({
  cartLines: {
    type: Array,
    default: () => [],
  },
  selectedLineId: {
    type: String,
    default: '',
  },
  currency: {
    type: String,
    default: 'IRR',
  },
  orderMode: {
    type: String,
    default: 'dine_in',
  },
  place: {
    type: String,
    default: '',
  },
  placeOptions: {
    type: Array,
    default: () => [],
  },
  tableOrders: {
    type: Array,
    default: () => [],
  },
  tablePreviewLoading: {
    type: Boolean,
    default: false,
  },
  selectedTableLabel: {
    type: String,
    default: '',
  },
  canPrintTableOrders: {
    type: Boolean,
    default: false,
  },
  note: {
    type: String,
    default: '',
  },
  paymentMethod: {
    type: String,
    default: 'cash',
  },
  paymentReference: {
    type: String,
    default: '',
  },
  paymentRrn: {
    type: String,
    default: '',
  },
  paymentBoot: {
    type: Object,
    default: () => ({}),
  },
  financial: {
    type: Object,
    default: () => ({}),
  },
  totals: {
    type: Object,
    default: () => ({}),
  },
  submitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:selectedLineId',
  'update:orderMode',
  'update:place',
  'update:note',
  'update:paymentMethod',
  'update:paymentReference',
  'update:paymentRrn',
  'patch-financial',
  'increment-line',
  'decrement-line',
  'remove-line',
  'edit-line-note',
  'edit-line-customization',
  'clear-cart',
  'submit-order',
  'submit-and-pay',
  'print-ticket',
  'verify-credit',
  'verify-coupon',
  'update-table-order-item',
  'print-confirmed-table',
])

const showAdvancedFinancial = ref(true)
const showPaymentPopup = ref(false)
const paymentSplits = ref([{ method: 'cash', amount: 0 }])

const splitTotal = computed(() => paymentSplits.value.reduce((sum, s) => sum + Number(s.amount || 0), 0))
const splitRemaining = computed(() => Number(props.totals?.payableAmount || 0) - splitTotal.value)

const orderModes = [
  { value: 'dine_in', label: 'سالن' },
  { value: 'takeaway', label: 'بیرون بر (مشتری)' },
  { value: 'delivery', label: 'بیرون بر (پیک)' },
]

const pendingTableOrders = computed(() =>
  (props.tableOrders || []).filter((order) => String(order.status || '').toLowerCase() === 'pending'),
)

const confirmedTableOrders = computed(() =>
  (props.tableOrders || []).filter((order) => String(order.status || '').toLowerCase() !== 'pending'),
)

const normalizedPlaceOptions = computed(() =>
  (props.placeOptions || []).map((option) => ({
    value: option,
    label: option,
  })),
)

const paymentMethodOptions = computed(() => {
  const options = [{ value: 'cash', label: 'نقدی' }]
  if (Boolean(props.paymentBoot?.supports_card)) {
    options.push({ value: 'card', label: 'کارتخوان' })
  }
  return options
})

watch(
  () => [props.paymentMethod, Boolean(props.paymentBoot?.supports_card)],
  ([method, supportsCard]) => {
    if (method === 'card' && !supportsCard) {
      emit('update:paymentMethod', 'cash')
    }
  },
  { immediate: true },
)

function patchFinancial(partial) {
  emit('patch-financial', partial)
}

function toggleDiscountType() {
  const next = props.financial.discountType === 'fixed' ? 'percent' : 'fixed'
  patchFinancial({ discountType: next })
}

function openPaymentPopup() {
  const total = Number(props.totals?.payableAmount || 0)
  paymentSplits.value = [{ method: props.paymentMethod || 'cash', amount: total }]
  showPaymentPopup.value = true
}

function addSplit() {
  const remaining = Math.max(splitRemaining.value, 0)
  paymentSplits.value.push({ method: 'cash', amount: remaining })
}

function removeSplit(idx) {
  paymentSplits.value.splice(idx, 1)
}

function splitMethodLabel(method) {
  if (method === 'card') return '💳 کارتخوان'
  if (method === 'wallet') return '👛 کیف پول'
  return '💵 نقدی'
}

function confirmPayment() {
  const validSplits = paymentSplits.value.filter((s) => Number(s.amount || 0) > 0)
  const primary = validSplits.reduce(
    (a, b) => (Number(b.amount || 0) > Number(a.amount || 0) ? b : a),
    validSplits[0] || { method: 'cash', amount: 0 },
  )
  emit('update:paymentMethod', primary.method)
  emit('submit-and-pay', { splits: validSplits })
  showPaymentPopup.value = false
}

function rowTotal(line) {
  return Number(line.qty || 0) * Number(line.price || line.unit_price || 0)
}

function qtyText(value) {
  return Number(value || 0).toFixed(3).replace(/\.000$/, '')
}

function formatCompactNumber(value, decimals = 2) {
  const parsed = Number(value || 0)
  if (!Number.isFinite(parsed)) {
    return '0'
  }
  return parsed.toFixed(decimals).replace(/\.?0+$/, '')
}

function formatDateTime(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}

function ingredientBaseMultiplier(ingredient = {}) {
  return Number(ingredient?.is_included_by_default || 0) === 1 ? 1 : 0
}

function customizationSummary(line) {
  const customization = line?.customization || {}
  const ingredientMap = new Map(
    (line?.customization_ingredients || [])
      .map((row) => ({
        key: String(row?.key || '').trim(),
        name: String(row?.name || '').trim(),
        customer_label: String(row?.customer_label || '').trim(),
        is_included_by_default: Number(row?.is_included_by_default || 0),
      }))
      .filter((row) => row.key)
      .map((row) => [row.key, row]),
  )
  const lines = []

  for (const row of customization.ingredient_adjustments || []) {
    const ingredientKey = String(row?.ingredient_key || '').trim()
    if (!ingredientKey) {
      continue
    }
    const selected = Number(row?.multiplier || 0)
    if (!Number.isFinite(selected)) {
      continue
    }

    const ingredient = ingredientMap.get(ingredientKey)
    const label = ingredient?.customer_label || ingredient?.name || ingredientKey
    if (!ingredient) {
      if (selected > 0) {
        lines.push(`• ${label}: x${formatCompactNumber(selected)}`)
      }
      continue
    }

    const base = ingredientBaseMultiplier(ingredient)
    if (Math.abs(selected - base) < 0.001) {
      continue
    }
    if (base <= 0 && selected > 0) {
      lines.push(`+ افزودن ${label} x${formatCompactNumber(selected)}`)
      continue
    }
    if (base > 0 && selected <= 0) {
      lines.push(`- حذف ${label}`)
      continue
    }
    if (selected > base) {
      lines.push(`+ افزایش ${label} (${formatCompactNumber(base)} → ${formatCompactNumber(selected)})`)
    } else {
      lines.push(`- کاهش ${label} (${formatCompactNumber(base)} → ${formatCompactNumber(selected)})`)
    }
  }

  for (const row of customization.selected_modifiers || []) {
    const group = String(row?.group || row?.group_name || '').trim()
    const option = String(row?.option || row?.option_name || '').trim()
    if (!group || !option) {
      continue
    }
    const qty = Math.max(Number(row?.qty || 1), 1)
    lines.push(`+ ${group} / ${option}${qty > 1 ? ` x${formatCompactNumber(qty)}` : ''}`)
  }

  for (const row of customization.selected_alternatives || []) {
    const ingredientKey = String(row?.ingredient_key || '').trim()
    const alternative = String(row?.alternative_item || '').trim()
    if (!ingredientKey || !alternative) {
      continue
    }
    const ingredient = ingredientMap.get(ingredientKey)
    const label = ingredient?.customer_label || ingredient?.name || ingredientKey
    lines.push(`↺ جایگزین ${label} با ${alternative}`)
  }

  return lines
}

function canEditCustomization(line) {
  const customization = line?.customization || {}
  return Boolean(
    line?.has_customization ||
      Number((line?.customization_ingredients || []).length || 0) > 0 ||
      Number((customization.ingredient_adjustments || []).length || 0) > 0 ||
      Number((customization.selected_modifiers || []).length || 0) > 0 ||
      Number((customization.selected_alternatives || []).length || 0) > 0,
  )
}

function focusDiscountInput() {
  discountInputRef.value?.focus()
  discountInputRef.value?.select?.()
}

defineExpose({
  focusDiscountInput,
})
</script>

<style scoped>
.cart-panel {
  border-radius: 18px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  padding: 0.7rem;
  color: var(--pos-text);
  display: grid;
  gap: 0.55rem;
  max-height: 78vh;
  overflow: auto;
}

.mode-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.35rem;
}

.mode-row button {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-text);
  border-radius: 10px;
  padding: 0.42rem 0.3rem;
  cursor: pointer;
}

.mode-row button.active {
  background: var(--pos-primary);
  color: var(--pos-white);
  font-weight: 600;
}

.field {
  display: grid;
  gap: 0.22rem;
  font-size: 0.76rem;
}

.field.inline {
  gap: 0.35rem;
}

.table-orders-box {
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  padding: 0.5rem;
  display: grid;
  gap: 0.45rem;
  background: var(--pos-soft);
}

.table-orders-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.table-orders-head h3 {
  margin: 0;
  font-size: 0.82rem;
}

.table-order-columns {
  display: grid;
  gap: 0.45rem;
}

.table-order-column {
  border: 1px dashed var(--pos-border);
  border-radius: 10px;
  padding: 0.4rem;
  display: grid;
  gap: 0.35rem;
}

.table-order-column.confirmed {
  background: rgb(var(--pos-success-rgb, 11 125 74) / 0.08);
}

.table-order-column > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.table-order-list {
  display: grid;
  gap: 0.35rem;
}

.table-order-card {
  border: 1px solid var(--pos-border);
  border-radius: 9px;
  padding: 0.35rem;
  display: grid;
  gap: 0.28rem;
  background: var(--pos-white);
}

.table-order-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.table-order-card ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.2rem;
}

.table-order-card li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
  font-size: 0.74rem;
}

.item-counter {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
}

.item-counter button {
  width: 22px;
  height: 22px;
  border: 1px solid var(--pos-border);
  border-radius: 7px;
  background: #fff;
  color: var(--pos-primary);
  cursor: pointer;
}

.cart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cart-head h3 {
  margin: 0;
  font-size: 0.86rem;
}

.clear-btn {
  border: 1px solid var(--pos-accent);
  background: var(--pos-accent);
  color: var(--pos-white);
  border-radius: 9px;
  padding: 0.3rem 0.6rem;
  cursor: pointer;
}

.cart-list {
  display: grid;
  gap: 0.4rem;
  max-height: none;
  overflow: visible;
}

.cart-row {
  border-radius: 12px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  padding: 0.45rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.4rem;
  cursor: pointer;
}

.cart-row.active {
  border-color: var(--pos-primary);
  box-shadow: inset 0 0 0 1px var(--pos-primary);
}

.line-main {
  display: grid;
  gap: 0.15rem;
}

.line-main strong {
  font-size: 0.8rem;
}

.line-main small {
  font-size: 0.72rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.8);
}

.line-note {
  color: var(--pos-accent) !important;
}

.line-custom {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.92) !important;
}

.line-custom-list {
  margin: 0.1rem 0 0;
  padding-right: 1rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.86);
  font-size: 0.7rem;
  line-height: 1.45;
  display: grid;
  gap: 0.12rem;
}

.line-custom-list li {
  list-style: none;
}

.line-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.counter {
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
}

.counter button,
.icon,
.check-btn {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-primary);
  border-radius: 8px;
  cursor: pointer;
}

.counter button {
  width: 24px;
  height: 24px;
}

.counter span {
  min-width: 38px;
  text-align: center;
  font-size: 0.76rem;
}

.icon {
  width: 24px;
  height: 24px;
  padding: 0;
}

.icon.bom {
  width: auto;
  min-width: 34px;
  padding: 0 0.25rem;
  font-size: 0.66rem;
  font-weight: 700;
  border-color: var(--pos-accent);
  color: var(--pos-accent);
}

.icon.danger {
  color: var(--pos-accent);
}

.hint {
  margin: 0;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
}

.financial-box {
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  padding: 0.5rem;
  display: grid;
  gap: 0.35rem;
}

.financial-title {
  margin: 0;
  font-size: 0.79rem;
  color: var(--pos-primary);
}

.financial-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
}

.toggle-advanced-btn {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-primary);
  border-radius: 8px;
  padding: 0.24rem 0.5rem;
  font-size: 0.7rem;
  cursor: pointer;
}

.wallet-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  font-size: 0.76rem;
  margin-bottom: 0.45rem;
}

.code-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.32rem;
}

.code-row.two {
  grid-template-columns: 1fr 1fr;
}

.check-btn {
  padding: 0.36rem 0.55rem;
}

.discount-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  font-size: 0.76rem;
}

.discount-label {
  flex-shrink: 0;
  color: var(--pos-primary);
  font-weight: 600;
}

.discount-input-group {
  display: flex;
  align-items: center;
  gap: 0;
  flex: 1;
  max-width: 180px;
}

.discount-input {
  border-radius: 8px 0 0 8px !important;
  border-left: none !important;
  flex: 1;
  min-width: 0;
}

.discount-type-btn {
  height: 100%;
  min-height: 32px;
  padding: 0 0.6rem;
  border: 1px solid var(--pos-border);
  border-radius: 0 8px 8px 0;
  background: var(--pos-soft);
  color: var(--pos-primary);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}

.discount-type-btn:hover {
  background: var(--pos-border);
}

.summary-box {
  border-radius: 12px;
  border: 1px solid var(--pos-border);
  background: var(--pos-soft);
  padding: 0.5rem;
  display: grid;
  gap: 0.28rem;
}

.sum-line {
  display: flex;
  justify-content: space-between;
  gap: 0.4rem;
  font-size: 0.78rem;
}

.sum-line.payable {
  border-top: 1px dashed var(--pos-border);
  padding-top: 0.38rem;
  font-size: 0.86rem;
}

.sum-line.payable strong {
  color: var(--pos-primary);
}

.checkout-actions {
  position: sticky;
  bottom: 0;
  background: var(--pos-white);
  border-top: 1px solid var(--pos-border);
  padding-top: 0.45rem;
  display: grid;
  gap: 0.35rem;
}

.save-btn,
.pay-btn,
.print-btn {
  border: 0;
  border-radius: 10px;
  color: #fff;
  padding: 0.56rem;
  cursor: pointer;
}

.save-btn {
  background: var(--pos-primary);
}

.pay-btn {
  background: var(--pos-accent);
}

.print-btn {
  background: var(--pos-primary);
}

.checkout-actions label {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.74rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.88);
}

.dark-input {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-text);
}

.dark-input::placeholder {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

@media (max-width: 980px) {
  .cart-panel {
    max-height: none;
  }

  .checkout-actions {
    position: static;
  }
}

.pay-popup-backdrop {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgb(0 0 0 / 0.55);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.pay-popup {
  background: #fff;
  border-radius: 20px;
  width: min(440px, 100%);
  box-shadow: 0 24px 60px rgb(0 0 0 / 0.22);
  display: grid;
  gap: 0.75rem;
  padding: 1.2rem;
  color: var(--pos-text);
}

.pay-popup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pay-popup-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  color: var(--pos-primary);
}

.pay-popup-close {
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--pos-border);
  border-radius: 50%;
  background: #fff;
  color: var(--pos-text);
  font-size: 1.1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pay-total-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--pos-soft);
  border: 1px solid var(--pos-border);
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  font-size: 0.82rem;
}

.pay-total-banner strong {
  font-size: 1.05rem;
  color: var(--pos-primary);
}

.pay-splits {
  display: grid;
  gap: 0.45rem;
}

.pay-split-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.4rem;
}

.pay-split-row:has(.pay-split-remove:not(.pay-split-remove)) {
  grid-template-columns: auto 1fr;
}

.pay-method-select {
  border-radius: 9px;
  padding: 0.38rem 0.5rem;
  font-size: 0.8rem;
  min-width: 120px;
}

.pay-amount-input {
  border-radius: 9px;
  padding: 0.38rem 0.5rem;
  font-size: 0.88rem;
  text-align: left;
}

.pay-split-remove {
  width: 26px;
  height: 26px;
  border: 1px solid var(--pos-accent);
  border-radius: 50%;
  background: #fff;
  color: var(--pos-accent);
  font-size: 1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pay-add-split-btn {
  border: 1px dashed var(--pos-border);
  border-radius: 10px;
  background: transparent;
  color: var(--pos-primary);
  font-size: 0.78rem;
  padding: 0.4rem;
  cursor: pointer;
  transition: background 0.15s;
}

.pay-add-split-btn:hover {
  background: var(--pos-soft);
}

.pay-remaining-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  border-radius: 10px;
  background: rgb(var(--pos-accent-rgb, 201 141 66) / 0.1);
  border: 1px solid rgb(var(--pos-accent-rgb, 201 141 66) / 0.25);
  font-size: 0.82rem;
  color: var(--pos-accent);
  transition: all 0.2s;
}

.pay-remaining-row.zero {
  background: rgb(11 125 74 / 0.08);
  border-color: rgb(11 125 74 / 0.25);
  color: var(--pos-success-color, #0b7d4a);
}

.pay-remaining-row.over {
  background: rgb(171 53 53 / 0.08);
  border-color: rgb(171 53 53 / 0.25);
  color: var(--pos-danger-color, #ab3535);
}

.pay-split-summary {
  border: 1px solid var(--pos-border);
  border-radius: 10px;
  padding: 0.5rem 0.65rem;
  display: grid;
  gap: 0.3rem;
}

.pay-split-summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.85);
}

.pay-popup-footer {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 0.5rem;
  padding-top: 0.25rem;
}

.pay-cancel-btn {
  border: 1px solid var(--pos-border);
  background: #fff;
  color: var(--pos-text);
  border-radius: 11px;
  padding: 0.6rem;
  cursor: pointer;
  font-size: 0.84rem;
}

.pay-confirm-btn {
  border: 0;
  border-radius: 11px;
  background: var(--pos-primary);
  color: #fff;
  padding: 0.6rem;
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 700;
  transition: opacity 0.15s;
}

.pay-confirm-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
