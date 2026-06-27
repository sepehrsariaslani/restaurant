<template>
  <section class="order-flow-page checkout-context-page">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">تکمیل سفارش</p>
        <h1 class="order-flow-title">قبل از ثبت سفارش همه چیز را بررسی کنید</h1>
        <p class="order-flow-subtitle">پرداخت آنلاین هنوز فعال نیست؛ سفارش ثبت می‌شود و پرداخت طبق روش انتخاب‌شده هنگام تحویل/در شعبه/سر میز انجام خواهد شد.</p>
      </div>
      <button class="order-flow-secondary" type="button" @click="goBack">بازگشت</button>
    </header>

    <section v-if="!cartLines.length" class="order-flow-card">
      <h2>سبد خرید خالی است</h2>
      <p>برای ثبت سفارش ابتدا آیتم‌هایی به سبد اضافه کنید.</p>
      <a class="order-flow-primary" href="/menu">رفتن به منو</a>
    </section>

    <section v-else-if="!hasContext" class="order-flow-card">
      <h2>نوع سفارش مشخص نیست</h2>
      <p>برای جلوگیری از اشتباه در شعبه، آدرس یا هزینه ارسال، ابتدا نوع سفارش را انتخاب کنید.</p>
      <a class="order-flow-primary" href="/order/type">انتخاب نوع سفارش</a>
    </section>

    <div v-else class="order-flow-layout">
      <main class="order-flow-list">
        <OrderContextStrip :currency="currency" />
        <section class="order-flow-card">
          <h2>اطلاعات مشتری</h2>
          <div class="order-flow-form">
            <label class="order-flow-field"><span>نام و نام خانوادگی</span><input class="order-flow-input" v-model="form.customer_name" /></label>
            <label class="order-flow-field"><span>شماره موبایل</span><input class="order-flow-input" dir="ltr" inputmode="numeric" v-model="form.mobile" /></label>
          </div>
        </section>

        <section class="order-flow-card">
          <div class="order-flow-card-head">
            <div>
              <h2>{{ orderTypeLabel }}</h2>
              <p>{{ orderTypeDescription }}</p>
            </div>
            <a class="order-flow-secondary" href="/order/type">تغییر</a>
          </div>
          <div class="order-flow-facts">
            <div class="order-flow-fact"><small>سفارش برای کجاست؟</small><strong>{{ destinationText }}</strong></div>
            <div class="order-flow-fact"><small>چه زمانی؟</small><strong>{{ timeText }}</strong></div>
            <div class="order-flow-fact"><small>شعبه</small><strong>{{ context.branch_title || context.branch || '-' }}</strong></div>
            <div class="order-flow-fact"><small>هزینه ارسال</small><strong>{{ context.order_type === 'delivery' ? deliveryFeeText : 'بدون هزینه ارسال' }}</strong></div>
          </div>
        </section>

        <section class="order-flow-card" v-if="context.order_type === 'delivery'">
          <h2>یادداشت پیک</h2>
          <textarea class="order-flow-textarea" rows="3" v-model="contextDraft.courier_note" placeholder="توضیح برای پیک" />
        </section>

        <section class="order-flow-card" v-else>
          <h2>یادداشت سفارش</h2>
          <textarea class="order-flow-textarea" rows="3" v-model="form.note" placeholder="توضیح برای آشپزخانه یا شعبه" />
        </section>

        <section class="order-flow-card">
          <h2>روش پرداخت</h2>
          <div class="payment-method-list">
            <label v-for="method in paymentMethods" :key="method.value" class="payment-method-card">
              <input type="radio" name="payment-method" :value="method.value" v-model="paymentMethod" />
              <span>
                <strong>{{ method.label }}</strong>
                <small>{{ method.description }}</small>
              </span>
            </label>
          </div>
        </section>

        <section class="order-flow-card">
          <h2>کد تخفیف</h2>
          <div class="order-flow-inline-actions">
            <input class="order-flow-input" style="flex:1" v-model="couponCode" dir="ltr" placeholder="کد تخفیف" @keydown.enter="applyCoupon" />
            <button class="order-flow-secondary" type="button" :disabled="couponLoading || !couponCode.trim()" @click="applyCoupon">{{ couponLoading ? '...' : 'اعمال' }}</button>
          </div>
          <p v-if="couponResult" class="order-flow-alert">{{ couponResult.message || 'کد تخفیف اعمال شد.' }}</p>
          <p v-if="couponError" class="order-flow-alert danger">{{ couponError }}</p>
        </section>

        <section class="order-flow-card">
          <h2>آیتم‌های سفارش</h2>
          <div class="summary-lines">
            <div v-for="line in cartLines" :key="line.id" class="order-flow-summary-line">
              <span>{{ line.qty }}× {{ line.item_title || line.title }}</span>
              <strong>{{ formatMoney(line.line_total_preview ?? (line.base_price * line.qty), currency) }}</strong>
            </div>
          </div>
        </section>

        <p v-if="submitError" class="order-flow-alert danger">{{ submitError }}</p>
      </main>

      <OrderContextSummary next-step="ثبت سفارش" :currency="currency">
        <div class="order-flow-summary-line"><span>جمع اقلام</span><strong>{{ formatMoney(totals.subtotal, currency) }}</strong></div>
        <div class="order-flow-summary-line" v-if="totals.discount"><span>تخفیف</span><strong>-{{ formatMoney(totals.discount, currency) }}</strong></div>
        <div class="order-flow-summary-line" v-if="totals.delivery_fee"><span>ارسال</span><strong>{{ formatMoney(totals.delivery_fee, currency) }}</strong></div>
        <div class="order-flow-summary-line"><span>مبلغ سفارش</span><strong>{{ formatMoney(totals.grand_total, currency) }}</strong></div>
        <p class="payment-note">{{ paymentNote }}</p>
        <button class="order-flow-primary" type="button" :disabled="submitting" @click="submitOrder">{{ submitting ? 'در حال ثبت...' : 'ثبت سفارش' }}</button>
      </OrderContextSummary>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { cartState, clearCart, saveCheckoutDraft, saveLastOrder, saveOrderContext } from '@/stores/cartStore'
import { getMenuBoot, placeOrder, saveCustomerDeliveryAddress, validateCoupon } from '@/utils/api'
import { formatMoney, normalizeMobile } from '@/utils/format'
import { calculateOrderTotals, ORDER_FLOW_CURRENCY_FALLBACK } from '@/utils/orderFlow'
import './orderFlow.css'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
function readAuth() {
  try { return JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}') } catch { return {} }
}

const auth = readAuth()
const currency = ref(ORDER_FLOW_CURRENCY_FALLBACK)
const form = reactive({
  customer_name: cartState.checkoutDraft.customer_name || auth.customer_name || '',
  mobile: cartState.checkoutDraft.mobile || auth.mobile || '',
  note: cartState.checkoutDraft.note || cartState.orderContext.customer_note || '',
})
const contextDraft = reactive({ courier_note: cartState.orderContext.courier_note || '' })
const couponCode = ref('')
const couponLoading = ref(false)
const couponError = ref('')
const couponResult = ref(null)
const submitting = ref(false)
const submitError = ref('')
const paymentMethod = ref('')

const context = computed(() => cartState.orderContext || {})
const hasContext = computed(() => Boolean(context.value.order_type))
const cartLines = computed(() => cartState.lines)
const discountAmount = computed(() => Number(couponResult.value?.discount_amount || 0))
const totals = computed(() => calculateOrderTotals({ lines: cartLines.value, context: context.value, discount: discountAmount.value }))
const deliveryFeeText = computed(() => totals.value.delivery_fee ? formatMoney(totals.value.delivery_fee, currency.value) : 'هزینه نهایی پس از تایید شعبه')

const orderTypeLabel = computed(() => ({ dine_in: 'حضوری داخل سالن', pickup: 'بیرون‌بر', delivery: 'ارسال با پیک' }[context.value.order_type] || 'سفارش'))
const paymentMethods = computed(() => {
  if (context.value.order_type === 'delivery') {
    return [{ value: 'pay_on_delivery', label: 'پرداخت هنگام تحویل', description: 'مبلغ سفارش را هنگام تحویل به پیک پرداخت می‌کنید.' }]
  }
  if (context.value.order_type === 'pickup') {
    return [{ value: 'pay_at_branch', label: 'پرداخت در شعبه هنگام تحویل', description: 'وقتی برای دریافت سفارش مراجعه می‌کنید پرداخت انجام می‌شود.' }]
  }
  return [{ value: 'pay_at_table', label: 'پرداخت سر میز یا صندوق', description: 'پس از سرو یا هنگام خروج پرداخت انجام می‌شود.' }]
})
const paymentNote = computed(() => paymentMethods.value.find((row) => row.value === paymentMethod.value)?.description || '')
const orderTypeDescription = computed(() => {
  if (context.value.order_type === 'pickup') return 'خودتان سفارش را از شعبه تحویل می‌گیرید؛ آدرس و پیک لازم نیست.'
  if (context.value.order_type === 'delivery') return 'سفارش با پیک به آدرس انتخاب‌شده ارسال می‌شود.'
  if (context.value.order_type === 'dine_in') return 'سفارش به میز داخل سالن متصل است؛ هزینه ارسال ندارد.'
  return ''
})
const destinationText = computed(() => {
  if (context.value.order_type === 'dine_in') return `${context.value.branch_title || context.value.branch || 'شعبه'} · میز ${context.value.table || '-'}`
  if (context.value.order_type === 'pickup') return `تحویل از ${context.value.branch_title || context.value.branch || 'شعبه انتخاب نشده'}`
  const address = context.value.address || {}
  return address.title || address.address_line || 'آدرس انتخاب نشده'
})
const timeText = computed(() => {
  if (context.value.order_type === 'pickup') return context.value.pickup_time_type === 'scheduled' && context.value.pickup_time ? `تحویل در ${context.value.pickup_time}` : `آماده‌سازی حدود ${context.value.prep_time_mins || 20} دقیقه`
  if (context.value.order_type === 'delivery') return context.value.eta_min && context.value.eta_max ? `${context.value.eta_min} تا ${context.value.eta_max} دقیقه` : 'پس از تایید شعبه'
  return context.value.prep_time_mins ? `آماده سرو حدود ${context.value.prep_time_mins} دقیقه` : 'پس از تایید آشپزخانه'
})

watch(form, () => saveCheckoutDraft({ customer_name: form.customer_name, mobile: normalizeMobile(form.mobile), note: form.note }), { deep: true })
watch(contextDraft, () => saveOrderContext({ courier_note: contextDraft.courier_note }), { deep: true })

function goBack() { window.history.back() }

async function applyCoupon() {
  if (!couponCode.value.trim()) return
  couponLoading.value = true
  couponError.value = ''
  couponResult.value = null
  try {
    couponResult.value = await validateCoupon({ coupon_code: couponCode.value.trim(), mobile: normalizeMobile(form.mobile), subtotal: totals.value.subtotal, branch: context.value.branch, items: cartItemsPayload() })
  } catch (err) {
    couponError.value = err.message || 'کد تخفیف معتبر نیست.'
  } finally {
    couponLoading.value = false
  }
}

function cartItemsPayload() {
  return cartLines.value.map((line) => ({ item_slug: line.item_slug, qty: line.qty, branch: line.branch || context.value.branch || '', customization: line.customization || {} }))
}

function validate() {
  if (!form.customer_name.trim()) return 'نام گیرنده الزامی است.'
  if (normalizeMobile(form.mobile).length < 10) return 'شماره موبایل معتبر وارد کنید.'
  if (!hasContext.value) return 'نوع سفارش مشخص نیست.'
  if (context.value.order_type === 'pickup' && !context.value.branch) return 'برای بیرون‌بر انتخاب شعبه الزامی است.'
  if (context.value.order_type === 'dine_in' && (!context.value.branch || !context.value.table)) return 'برای سفارش حضوری شعبه و میز الزامی است.'
  if (context.value.order_type === 'delivery') {
    const address = context.value.address || {}
    if (!address.address_line) return 'برای ارسال، آدرس تحویل الزامی است.'
    if (context.value.out_of_range) return 'این آدرس خارج از محدوده ارسال است.'
  }
  if (!cartLines.value.length) return 'سبد خرید خالی است.'
  return ''
}

async function persistDeliveryAddress(mobile) {
  if (context.value.order_type !== 'delivery') return { id: '', snapshot: {} }
  const address = context.value.address || {}
  if (address.id) return { id: address.id, snapshot: address }
  const saved = await saveCustomerDeliveryAddress({
    customer_info: { name: form.customer_name, mobile },
    address_info: {
      title: address.title || 'آدرس تحویل',
      phone: address.phone || mobile,
      address_line: address.address_line,
      plaque: address.plaque || '',
      unit: address.unit || '',
      floor: address.floor || '',
      lat: address.lat || null,
      lng: address.lng || null,
      is_primary: 0,
    },
  })
  return { id: saved?.address?.id || '', snapshot: saved?.address || address }
}

async function submitOrder() {
  const err = validate()
  if (err) { submitError.value = err; return }
  submitting.value = true
  submitError.value = ''
  const mobile = normalizeMobile(form.mobile)
  try {
    const delivery = await persistDeliveryAddress(mobile)
    const ctx = { ...context.value, courier_note: contextDraft.courier_note, customer_note: form.note, payment_method: paymentMethod.value }
    const response = await placeOrder({
      customer_info: { name: form.customer_name, mobile },
      order_context: ctx,
      delivery_mode: ctx.order_type === 'delivery' ? 'delivery' : 'pickup',
      order_type: ctx.order_type === 'dine_in' ? 'dine_in' : ctx.order_type === 'delivery' ? 'delivery' : 'takeaway',
      delivery_address_id: ctx.order_type === 'delivery' ? delivery.id : '',
      delivery_address_snapshot: ctx.order_type === 'delivery' ? delivery.snapshot : {},
      address: ctx.order_type === 'delivery' ? (delivery.snapshot?.address_line || '') : ctx.order_type === 'dine_in' ? `میز ${ctx.table}` : '',
      pickup_method: ctx.order_type === 'pickup' ? 'walk' : '',
      note: [form.note, ctx.courier_note ? `یادداشت پیک: ${ctx.courier_note}` : '', ctx.kitchen_note ? `یادداشت آشپزخانه: ${ctx.kitchen_note}` : ''].filter(Boolean).join('\n'),
      coupon_code: couponResult.value?.code || couponCode.value.trim() || '',
      items: cartItemsPayload(),
    })
    saveLastOrder({ order_code: response.order_code, mobile, payment_method: paymentMethod.value })
    clearCart()
    window.location.href = `/order-success/${response.order_code}?mobile=${encodeURIComponent(mobile)}`
  } catch (err) {
    submitError.value = err.message || 'ثبت سفارش با خطا مواجه شد. دوباره تلاش کنید.'
  } finally {
    submitting.value = false
  }
}

watch(paymentMethods, (methods) => {
  if (!methods.some((method) => method.value === paymentMethod.value)) {
    paymentMethod.value = methods[0]?.value || ''
  }
}, { immediate: true })

onMounted(async () => {
  try {
    const boot = await getMenuBoot(context.value.branch || '')
    currency.value = boot?.currency || ORDER_FLOW_CURRENCY_FALLBACK
  } catch {
    currency.value = ORDER_FLOW_CURRENCY_FALLBACK
  }
})
</script>

<style scoped>
.checkout-context-page .summary-lines {
  display: grid;
  gap: 0.1rem;
}

.payment-method-list {
  display: grid;
  gap: 0.65rem;
}

.payment-method-card {
  min-height: 58px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.7rem;
  align-items: flex-start;
  border: 1.5px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 18px;
  background: #fff;
  padding: 0.8rem;
  cursor: pointer;
}

.payment-method-card:has(input:checked) {
  border-color: var(--accent-gold);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.08);
}

.payment-method-card input {
  margin-top: 0.25rem;
  accent-color: var(--accent-green);
}

.payment-method-card strong,
.payment-method-card small {
  display: block;
}

.payment-method-card small,
.payment-note {
  color: var(--text-muted);
  line-height: 1.7;
}

.payment-note {
  margin: 0;
  padding: 0.7rem;
  border-radius: 16px;
  background: rgb(var(--palette-june-bud-rgb) / 0.45);
}
</style>
