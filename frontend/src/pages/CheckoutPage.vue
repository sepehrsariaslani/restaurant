<template>
  <section class="order-flow-page checkout-context-page order-flow-page--mobile-cta">
    <header class="order-flow-hero checkout-hero">
      <div>
        <p class="order-flow-eyebrow">تکمیل سفارش</p>
        <h1 class="order-flow-title">تأیید و ثبت سفارش</h1>
        <p class="order-flow-subtitle">یک نگاه آخر به غذاها، محل تحویل و مبلغ سفارش.</p>
      </div>
      <button class="order-flow-secondary" type="button" @click="goBack">بازگشت</button>
    </header>

    <nav v-if="cartLines.length && hasContext" class="order-flow-steps" aria-label="مراحل سفارش">
      <span class="order-flow-step is-complete">۱. نوع سفارش</span>
      <span class="order-flow-step is-complete">۲. مقصد و شعبه</span>
      <span class="order-flow-step is-complete">۳. انتخاب غذا</span>
      <span class="order-flow-step active" aria-current="step">۴. تأیید سفارش</span>
    </nav>

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
          <main class="order-flow-list checkout-list">
        <OrderContextStrip :currency="currency" />
            <section v-if="!form.customer_name.trim() || !isValidCustomerMobile(form.mobile) || !isCustomerLoggedIn" class="order-flow-card checkout-confirmation-card">
              <div class="checkout-card-heading"><div><p class="checkout-card-kicker">۱. اطلاعات تماس</p><h2>اطلاعات مشتری</h2></div></div>
          <div class="order-flow-form">
                <label class="order-flow-field"><span>نام و نام خانوادگی</span><input class="order-flow-input" autocomplete="name" v-model="form.customer_name" /></label>
                <label class="order-flow-field"><span>شماره موبایل</span><input class="order-flow-input" dir="ltr" inputmode="numeric" autocomplete="tel" v-model="form.mobile" /></label>
          </div>
        </section>

        <section v-else class="order-flow-card checkout-confirmation-card checkout-customer-summary">
          <div>
            <p class="checkout-card-kicker">۱. اطلاعات تماس</p>
            <h2>{{ isCustomerLoggedIn ? 'اطلاعات حساب شما' : 'اطلاعات ثبت‌شده سفارش' }}</h2>
            <p>{{ isCustomerLoggedIn ? 'با حساب واردشده سفارش می‌دهید؛ نیازی به وارد کردن دوباره اطلاعات نیست.' : 'این اطلاعات را در مرحله انتخاب آدرس ثبت کرده‌اید.' }}</p>
          </div>
          <div class="checkout-customer-identity">
            <strong>{{ form.customer_name || 'مشتری' }}</strong>
            <span dir="ltr">{{ form.mobile }}</span>
          </div>
          <a v-if="context.order_type === 'delivery'" class="order-flow-secondary" href="/order/delivery">ویرایش اطلاعات و آدرس</a>
          <a v-else-if="isCustomerLoggedIn" class="order-flow-secondary" href="/customer/profile">ویرایش اطلاعات حساب</a>
        </section>

            <section class="order-flow-card checkout-confirmation-card">
              <div class="checkout-card-heading">
                <div>
                  <p class="checkout-card-kicker">۲. شیوه دریافت</p>
                  <h2>{{ orderTypeLabel }}</h2>
                  <p>{{ orderTypeDescription }}</p>
                </div>
                <a class="order-flow-secondary" href="/order/type">ویرایش نوع سفارش</a>
              </div>
              <div class="order-flow-facts checkout-facts">
            <div class="order-flow-fact"><small>سفارش برای کجاست؟</small><strong>{{ destinationText }}</strong></div>
            <div class="order-flow-fact"><small>چه زمانی؟</small><strong>{{ timeText }}</strong></div>
                <div class="order-flow-fact"><small>شعبه</small><strong>{{ context.branch_title || context.branch || '-' }}</strong></div>
            <div v-if="context.order_type === 'pickup'" class="order-flow-fact"><small>نحوه تحویل</small><strong>{{ pickupMethod === 'car' ? `کنار خودرو · ${vehicleForm.type || 'خودرو'} · ${vehicleForm.color || 'رنگ ثبت نشده'} · پلاک ${vehicleForm.plate || 'ثبت نشده'}` : 'از پیشخوان شعبه' }}</strong></div>
            <div class="order-flow-fact"><small>هزینه ارسال</small><strong>{{ context.order_type === 'delivery' ? deliveryFeeText : 'بدون هزینه ارسال' }}</strong></div>
          </div>
        </section>

        <section v-if="context.order_type === 'pickup' && pickupMethod === 'car'" class="order-flow-card checkout-confirmation-card">
          <h2>خودروی شما</h2>
          <p>{{ vehicleForm.type }} · {{ vehicleForm.color }} · پلاک {{ vehicleForm.plate }}</p>
          <a class="order-flow-secondary" href="/order/pickup?method=car">ویرایش خودرو و زمان تحویل</a>
        </section>

            <section class="order-flow-card checkout-confirmation-card" v-if="context.order_type === 'delivery'">
          <h2>یادداشت پیک</h2>
          <textarea class="order-flow-textarea" rows="3" v-model="contextDraft.courier_note" placeholder="توضیح برای پیک" />
        </section>

            <section class="order-flow-card checkout-confirmation-card" v-else>
          <h2>یادداشت سفارش</h2>
          <textarea class="order-flow-textarea" rows="3" v-model="form.note" placeholder="توضیح برای آشپزخانه یا شعبه" />
        </section>

            <section class="order-flow-card checkout-confirmation-card">
              <div class="checkout-card-heading"><div><p class="checkout-card-kicker">{{ context.order_type === 'pickup' ? '۴. پرداخت' : '۳. پرداخت' }}</p><h2>روش پرداخت</h2></div></div>
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

            <section class="order-flow-card checkout-confirmation-card">
          <h2>کد تخفیف</h2>
          <div class="order-flow-inline-actions">
            <input class="order-flow-input" style="flex:1" v-model="couponCode" dir="ltr" placeholder="کد تخفیف" @keydown.enter="applyCoupon" />
            <button class="order-flow-secondary" type="button" :disabled="couponLoading || !couponCode.trim()" @click="applyCoupon">{{ couponLoading ? '...' : 'اعمال' }}</button>
          </div>
          <p v-if="couponResult" class="order-flow-alert">{{ couponResult.message || 'کد تخفیف اعمال شد.' }}</p>
          <p v-if="couponError" class="order-flow-alert danger">{{ couponError }}</p>
        </section>

        <section class="order-flow-card checkout-confirmation-card">
          <div class="checkout-card-heading"><div><p class="checkout-card-kicker">{{ orderReviewStep }}. مرور سفارش</p><h2>آیتم‌های سفارش</h2></div><a class="order-flow-secondary" href="/cart">ویرایش سبد</a></div>
          <div class="checkout-product-summary">
            <article v-for="line in cartLines" :key="line.id" class="checkout-product-row">
              <img :src="productImage(line)" :alt="line.item_title || line.title" width="68" height="68" loading="lazy" />
              <div><strong>{{ line.item_title || line.title }}</strong><small>{{ line.qty }} عدد · {{ formatMoney(line.unit_price_preview ?? line.base_price, currency) }}</small></div>
              <strong>{{ formatMoney(line.line_total_preview ?? (line.base_price * line.qty), currency) }}</strong>
            </article>
          </div>
        </section>

        <p v-if="submitError" class="order-flow-alert danger">{{ submitError }}</p>
      </main>

      <OrderContextSummary next-step="ثبت سفارش" :currency="currency">
        <div class="checkout-total-row"><span>جمع اقلام</span><strong>{{ formatMoney(totals.subtotal, currency) }}</strong></div>
        <div class="checkout-total-row" v-if="totals.discount"><span>تخفیف</span><strong>-{{ formatMoney(totals.discount, currency) }}</strong></div>
        <div class="checkout-total-row" v-if="totals.delivery_fee"><span>ارسال</span><strong>{{ formatMoney(totals.delivery_fee, currency) }}</strong></div>
        <div class="checkout-total-row checkout-total-row--grand"><span>مبلغ سفارش</span><strong>{{ formatMoney(totals.grand_total, currency) }}</strong></div>
        <p class="payment-note">{{ paymentNote }}</p>
        <button class="order-flow-primary" type="button" :disabled="submitting" @click="submitOrder">{{ submitting ? 'در حال ثبت...' : 'ثبت سفارش' }}</button>
      </OrderContextSummary>
    </div>

    <div v-if="cartLines.length && hasContext" class="order-mobile-cta checkout-mobile-cta" role="region" aria-label="ثبت نهایی سفارش">
      <div><small>مبلغ نهایی</small><strong>{{ formatMoney(totals.grand_total, currency) }}</strong></div>
      <button class="order-flow-primary" type="button" :disabled="submitting" @click="submitOrder">{{ submitting ? 'در حال ثبت...' : 'ثبت سفارش' }}</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { cartState, clearCart, saveCheckoutDraft, saveLastOrder, saveOrderContext } from '@/stores/cartStore'
import { getCustomerCheckoutProfile, getMenuBoot, placeOrder, saveCustomerDeliveryAddress, validateCoupon } from '@/utils/api'
import { formatMoney, normalizeMobile } from '@/utils/format'
import { hasDeliveryCoordinates, isValidCustomerMobile } from '@/utils/customerOrderValidation'
import { calculateOrderTotals, ORDER_FLOW_CURRENCY_FALLBACK } from '@/utils/orderFlow'
import './orderFlow.css'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
function readAuth() {
  try { return JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}') } catch { return {} }
}

const auth = readAuth()
const isCustomerLoggedIn = computed(() => Boolean(auth.mobile && auth.customer_token))
const currency = ref(ORDER_FLOW_CURRENCY_FALLBACK)
const form = reactive({
  customer_name: auth.customer_name || localStorage.getItem('customer_name') || cartState.checkoutDraft.customer_name || '',
  mobile: auth.mobile || localStorage.getItem('customer_phone') || cartState.checkoutDraft.mobile || '',
  note: cartState.checkoutDraft.note || cartState.orderContext.customer_note || '',
})
const contextDraft = reactive({ courier_note: cartState.orderContext.courier_note || '' })
const pickupMethod = ref(cartState.orderContext.pickup_method || 'walk')
const customerVehicles = ref([])
const selectedVehicleId = ref(cartState.orderContext.pickup_vehicle?.id || '')
const saveVehicleForFuture = ref(Boolean(cartState.orderContext.pickup_vehicle?.save_for_future))
const vehicleForm = reactive({
  type: cartState.orderContext.pickup_vehicle?.type || '',
  color: cartState.orderContext.pickup_vehicle?.color || '',
  plate: cartState.orderContext.pickup_vehicle?.plate || '',
})
const couponCode = ref('')
const couponLoading = ref(false)
const couponError = ref('')
const couponResult = ref(null)
const submitting = ref(false)
const submitError = ref('')
const paymentMethod = ref('')

const context = computed(() => cartState.orderContext || {})
const hasContext = computed(() => Boolean(context.value.order_type))
const orderReviewStep = computed(() => context.value.order_type === 'pickup' ? '۵' : '۴')
const cartLines = computed(() => cartState.lines)
const discountAmount = computed(() => Number(couponResult.value?.discount_amount || 0))
const totals = computed(() => calculateOrderTotals({ lines: cartLines.value, context: context.value, discount: discountAmount.value }))
const deliveryFeeText = computed(() => totals.value.delivery_fee ? formatMoney(totals.value.delivery_fee, currency.value) : 'هزینه نهایی پس از تایید شعبه')
const productImage = (line = {}) => String(line.item_image || line.image || line.item?.image || '').trim() || 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=240&auto=format&fit=crop&q=60'

const orderTypeLabel = computed(() => ({ dine_in: 'حضوری داخل سالن', pickup: pickupMethod.value === 'car' ? 'درب ماشین' : 'تحویل حضوری', delivery: 'ارسال با پیک' }[context.value.order_type] || 'سفارش'))
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
  if (context.value.order_type === 'dine_in') return `${context.value.branch_title || context.value.branch || 'شعبه'} · ${context.value.table_title || `میز ${context.value.table || '-'}`}`
  if (context.value.order_type === 'pickup') return `تحویل از ${context.value.branch_title || context.value.branch || 'شعبه انتخاب نشده'}`
  const address = context.value.address || {}
  return address.title || address.address_line || 'آدرس انتخاب نشده'
})
const timeText = computed(() => {
  if (context.value.order_type === 'pickup') return context.value.pickup_time_type === 'scheduled' && context.value.pickup_time ? `تحویل در ${context.value.pickup_time}` : `آماده‌سازی حدود ${context.value.prep_time_mins || 20} دقیقه`
  if (context.value.order_type === 'delivery') return context.value.eta_min && context.value.eta_max ? `${context.value.eta_min} تا ${context.value.eta_max} دقیقه` : 'پس از تایید شعبه'
  return context.value.prep_time_mins ? `آماده سرو حدود ${context.value.prep_time_mins} دقیقه` : 'پس از تایید آشپزخانه'
})

function selectVehicle(vehicle) {
  selectedVehicleId.value = vehicle.id || ''
  vehicleForm.type = vehicle.type || ''
  vehicleForm.color = vehicle.color || ''
  vehicleForm.plate = vehicle.plate || ''
}

function startNewVehicle() {
  selectedVehicleId.value = ''
  vehicleForm.type = ''
  vehicleForm.color = ''
  vehicleForm.plate = ''
}

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
  if (!form.customer_name.trim() && !isCustomerLoggedIn.value) return 'نام گیرنده الزامی است.'
  if (!isValidCustomerMobile(form.mobile)) return 'شماره موبایل معتبر وارد کنید.'
  if (!hasContext.value) return 'نوع سفارش مشخص نیست.'
  if (context.value.order_type === 'pickup' && !context.value.branch) return 'برای بیرون‌بر انتخاب شعبه الزامی است.'
  if (context.value.order_type === 'pickup' && context.value.pickup_time_type === 'scheduled' && !context.value.pickup_time) return 'زمان تحویل را انتخاب کنید.'
  if (context.value.order_type === 'pickup' && pickupMethod.value === 'car') {
    if (!vehicleForm.type.trim()) return 'نوع یا مدل خودرو را وارد کنید.'
    if (!vehicleForm.color.trim()) return 'رنگ خودرو را وارد کنید.'
    if (!vehicleForm.plate.trim()) return 'شماره پلاک خودرو را وارد کنید.'
  }
  if (context.value.order_type === 'dine_in' && (!context.value.branch || !context.value.table)) return 'برای سفارش حضوری شعبه و میز الزامی است.'
  if (context.value.order_type === 'delivery') {
    const address = context.value.address || {}
    if (!address.address_line) return 'برای ارسال، آدرس تحویل الزامی است.'
    if (!hasDeliveryCoordinates(address)) return 'موقعیت آدرس را روی نقشه انتخاب کنید.'
    if (!context.value.branch) return 'برای ارسال، انتخاب شعبه الزامی است.'
    if (context.value.out_of_range) return 'این آدرس خارج از محدوده ارسال است.'
  }
  if (!cartLines.value.length) return 'سبد خرید خالی است.'
  return ''
}

async function persistDeliveryAddress(mobile) {
  if (context.value.order_type !== 'delivery') return { id: '', snapshot: {} }
  const address = context.value.address || {}
  if (address.id) return { id: address.id, snapshot: address }
  if (!isCustomerLoggedIn.value || !address.save_for_future) return { id: '', snapshot: address }
  const saved = await saveCustomerDeliveryAddress({
    customer_info: { name: form.customer_name.trim() || 'مشتری', mobile },
    address_info: {
      title: address.title || 'آدرس تحویل',
      phone: address.phone || mobile,
      address_line: address.address_line,
      plaque: address.plaque || '',
      unit: address.unit || '',
      floor: address.floor || '',
      lat: address.lat ?? null,
      lng: address.lng ?? null,
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
  const customerName = form.customer_name.trim() || (isCustomerLoggedIn.value ? 'مشتری' : '')
  try {
    const delivery = await persistDeliveryAddress(mobile)
    const pickupVehicle = pickupMethod.value === 'car' ? {
      id: selectedVehicleId.value,
      type: vehicleForm.type.trim(),
      color: vehicleForm.color.trim(),
      plate: vehicleForm.plate.trim(),
      title: `${vehicleForm.type.trim()} · ${vehicleForm.plate.trim()}`,
      save_for_future: saveVehicleForFuture.value,
    } : null
    const ctx = {
      ...context.value,
      courier_note: contextDraft.courier_note,
      customer_note: form.note,
      payment_method: paymentMethod.value,
      pickup_method: context.value.order_type === 'pickup' ? pickupMethod.value : '',
      pickup_vehicle: pickupVehicle,
    }
    const response = await placeOrder({
      customer_info: { name: customerName, mobile },
      order_context: ctx,
      delivery_mode: ctx.order_type === 'delivery' ? 'delivery' : 'pickup',
      order_type: ctx.order_type === 'dine_in' ? 'dine_in' : ctx.order_type === 'delivery' ? 'delivery' : 'takeaway',
      delivery_address_id: ctx.order_type === 'delivery' ? delivery.id : '',
      delivery_address_snapshot: ctx.order_type === 'delivery' ? delivery.snapshot : {},
      address: ctx.order_type === 'delivery' ? (delivery.snapshot?.address_line || '') : ctx.order_type === 'dine_in' ? `میز ${ctx.table}` : '',
      pickup_method: ctx.order_type === 'pickup' ? pickupMethod.value : '',
      pickup_vehicle_id: pickupVehicle?.id || '',
      pickup_vehicle_snapshot: pickupVehicle || {},
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
    const [boot, profile] = await Promise.all([
      getMenuBoot(context.value.branch || ''),
      isCustomerLoggedIn.value
        ? getCustomerCheckoutProfile({ mobile: form.mobile, customer_name: form.customer_name })
        : Promise.resolve(null),
    ])
    currency.value = boot?.currency || ORDER_FLOW_CURRENCY_FALLBACK
    if (profile) {
      const customer = profile.customer || {}
      form.customer_name = customer.name || form.customer_name || 'مشتری'
      form.mobile = customer.mobile || form.mobile
      customerVehicles.value = Array.isArray(profile.vehicles) ? profile.vehicles : []
      if (!vehicleForm.type && !selectedVehicleId.value && customerVehicles.value.length && pickupMethod.value === 'car') {
        selectVehicle(customerVehicles.value[0])
      }
    }
  } catch {
    currency.value = ORDER_FLOW_CURRENCY_FALLBACK
  }
})
</script>

<style scoped>
.checkout-hero { background: linear-gradient(145deg, rgb(var(--palette-eggshell-rgb) / 0.98), rgb(var(--palette-june-bud-rgb) / 0.52)); }
.checkout-list { gap: 1rem; }
.checkout-confirmation-card { padding: clamp(1rem, 2.4vw, 1.3rem); border-radius: 26px; }
.checkout-card-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.checkout-card-kicker { margin: 0 0 0.22rem; color: var(--accent-gold); font-weight: 850; font-size: 0.78rem; }
.checkout-facts { margin-top: 0; }
.checkout-product-summary { display: grid; gap: 0.7rem; }
.checkout-product-row { display: grid; grid-template-columns: 68px minmax(0, 1fr) auto; align-items: center; gap: 0.75rem; padding: 0.65rem 0; border-bottom: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.16); }
.checkout-product-row:last-child { border-bottom: 0; padding-bottom: 0; }
.checkout-product-row img { width: 68px; height: 68px; object-fit: cover; border-radius: 18px; background: rgb(var(--palette-june-bud-rgb) / 0.55); }
.checkout-product-row > div { min-width: 0; display: grid; gap: 0.25rem; }
.checkout-product-row small { color: var(--text-muted); font-size: 0.8rem; }
.checkout-product-row > strong { white-space: nowrap; font-size: 0.9rem; }
.checkout-total-row { display: flex; align-items: center; justify-content: space-between; gap: 0.7rem; padding: 0.65rem 0; border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1); }
.checkout-total-row--grand { padding-top: 0.95rem; border-bottom: 0; font-size: 1.1rem; }
.checkout-context-page .summary-lines {
  display: grid;
  gap: 0.1rem;
}

.checkout-customer-summary { display: grid; gap: .7rem; }
.checkout-customer-identity { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem 1rem; padding: .8rem; border-radius: 16px; background: var(--ds-color-surface-muted); }
.checkout-customer-identity span { direction: ltr; text-align: left; }
.pickup-method-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }
.pickup-method-card, .saved-vehicle-card { min-height: 60px; display: flex; align-items: flex-start; gap: .7rem; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: 16px; background: var(--ds-color-surface-raised); cursor: pointer; }
.pickup-method-card.active, .saved-vehicle-card.active { border-color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.pickup-method-card input, .pickup-save-vehicle input { margin-top: .2rem; accent-color: var(--ds-color-action-primary); }
.pickup-method-card strong, .pickup-method-card small, .saved-vehicle-card strong, .saved-vehicle-card small { display: block; }
.pickup-method-card small, .saved-vehicle-card small, .pickup-vehicle-hint { color: var(--text-muted); line-height: 1.7; }
.pickup-vehicle-panel { display: grid; gap: .7rem; margin-top: .8rem; padding: .85rem; border-radius: 18px; background: var(--ds-color-surface-muted); }
.pickup-vehicle-hint { margin: 0; }
.saved-vehicle-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .55rem; }
.saved-vehicle-card { width: 100%; text-align: right; color: inherit; }
.pickup-vehicle-fields { margin: 0; }
.pickup-save-vehicle { display: flex; align-items: center; gap: .55rem; min-height: 44px; }
.pickup-method-card:focus-within, .saved-vehicle-card:focus-visible, .pickup-vehicle-panel :deep(input:focus-visible) { outline: 2px solid var(--ds-color-focus-ring); outline-offset: 2px; }

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
  background: var(--ds-color-surface-raised);
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

.checkout-context-page .order-flow-form .order-flow-field {
  max-width: 34rem;
}

.checkout-context-page .order-flow-form .order-flow-input:not(:focus) {
  border-color: color-mix(in srgb, var(--ds-color-border) 35%, var(--ds-color-text-muted) 65%);
}

.checkout-context-page .payment-method-card {
  border-color: color-mix(in srgb, var(--ds-color-border) 35%, var(--ds-color-text-muted) 65%);
  background: var(--ds-color-surface-raised);
}

@media (max-width: 560px) {
  .checkout-card-heading { gap: 0.6rem; }
  .pickup-method-grid { grid-template-columns: 1fr; }
  .checkout-card-heading .order-flow-secondary { min-height: 38px; padding-inline: 0.72rem; font-size: 0.76rem; }
  .checkout-product-row { grid-template-columns: 60px minmax(0, 1fr); }
  .checkout-product-row img { width: 60px; height: 60px; }
  .checkout-product-row > strong { grid-column: 2; }
}
</style>
