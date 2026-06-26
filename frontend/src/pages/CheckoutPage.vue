<template>
  <div class="checkout-page" dir="rtl">
    <header class="page-header">
      <button class="back-btn" type="button" @click="goBack" aria-label="بازگشت">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">تکمیل سفارش</h1>
      <span class="header-spacer"></span>
    </header>

    <div class="checkout-body">

      <!-- Cart is empty -->
      <section v-if="!cartLines.length" class="empty-card">
        <div class="empty-icon">🛒</div>
        <h3>سبد خرید خالی است</h3>
        <p>برای ثبت سفارش ابتدا آیتم‌هایی به سبد اضافه کنید.</p>
        <a href="/menu" class="primary-btn">رفتن به منو</a>
      </section>

      <template v-else>

        <!-- ── Step 1: Customer Info ─────────────────────────── -->
        <section class="section-card">
          <h2 class="section-title">
            <span class="step-badge">۱</span>
            اطلاعات گیرنده
          </h2>
          <div class="field-group">
            <label class="field-label">نام و نام خانوادگی</label>
            <input v-model="form.customer_name" class="field-input" placeholder="مثلاً علی محمدی" />
          </div>
          <div class="field-group">
            <label class="field-label">شماره موبایل</label>
            <input v-model="form.mobile" class="field-input" dir="ltr" inputmode="numeric" placeholder="09123456789" />
          </div>
          <button v-if="form.mobile.length >= 10" class="load-profile-btn" type="button" :disabled="profileLoading" @click="loadProfile">
            {{ profileLoading ? 'در حال بررسی...' : '📋 بارگذاری آدرس‌های ذخیره شده' }}
          </button>
          <p v-if="profileError" class="hint-error">{{ profileError }}</p>
        </section>

        <!-- ── Step 2: Delivery Mode ──────────────────────────── -->
        <section class="section-card">
          <h2 class="section-title">
            <span class="step-badge">۲</span>
            نحوه دریافت سفارش
          </h2>
          <div class="mode-grid">
            <button type="button" class="mode-card" :class="{ active: form.delivery_mode === 'delivery' }" @click="form.delivery_mode = 'delivery'">
              <span class="mode-icon">🛵</span>
              <strong>تحویل درب منزل</strong>
              <small>ارسال به آدرس شما</small>
            </button>
            <button type="button" class="mode-card" :class="{ active: form.delivery_mode === 'pickup' }" @click="form.delivery_mode = 'pickup'">
              <span class="mode-icon">🏃</span>
              <strong>بیرون‌بر</strong>
              <small>تحویل از رستوران</small>
            </button>
          </div>
        </section>

        <!-- ── Step 3: Delivery Address ───────────────────────── -->
        <section class="section-card" v-if="form.delivery_mode === 'delivery'">
          <h2 class="section-title">
            <span class="step-badge">۳</span>
            آدرس تحویل
          </h2>

          <div v-if="savedAddresses.length" class="saved-list">
            <label v-for="addr in savedAddresses" :key="addr.id" class="saved-item">
              <input type="radio" name="addr" :value="addr.id" v-model="form.delivery_address_id" @change="form.use_new_address = false" />
              <div class="saved-body">
                <strong>{{ addr.title || 'آدرس' }}</strong>
                <p>{{ addr.address_line }}</p>
                <small>{{ addr.phone }}</small>
              </div>
            </label>
            <button class="ghost-btn" type="button" @click="form.use_new_address = true; form.delivery_address_id = ''">+ آدرس جدید</button>
          </div>

          <div v-if="!savedAddresses.length || form.use_new_address" class="new-address-form">
            <div class="field-group">
              <label class="field-label">عنوان آدرس</label>
              <input v-model="form.address_title" class="field-input" placeholder="مثلاً خانه، محل کار" />
            </div>
            <div class="field-group">
              <label class="field-label">آدرس دقیق</label>
              <textarea v-model="form.address_line" class="field-textarea" rows="2" placeholder="خیابان، کوچه، پلاک..." />
            </div>
            <div class="field-row">
              <div class="field-group">
                <label class="field-label">پلاک</label>
                <input v-model="form.address_plaque" class="field-input" placeholder="مثلاً ۱۲" />
              </div>
              <div class="field-group">
                <label class="field-label">واحد</label>
                <input v-model="form.address_unit" class="field-input" placeholder="مثلاً ۳" />
              </div>
            </div>
            <div class="field-group">
              <label class="field-label">شماره تماس گیرنده</label>
              <input v-model="form.address_phone" class="field-input" dir="ltr" inputmode="numeric" placeholder="09123456789" />
            </div>
          </div>
        </section>

        <!-- ── Step 4: Coupon ─────────────────────────────────── -->
        <section class="section-card">
          <h2 class="section-title">
            <span class="step-badge">{{ form.delivery_mode === 'delivery' ? '۴' : '۳' }}</span>
            کد تخفیف
          </h2>
          <div class="coupon-row">
            <input v-model="couponCode" class="field-input coupon-input" placeholder="کد تخفیف را وارد کنید" dir="ltr" @keydown.enter="applyCoupon" />
            <button class="apply-btn" type="button" :disabled="couponLoading || !couponCode.trim()" @click="applyCoupon">
              {{ couponLoading ? '...' : 'اعمال' }}
            </button>
          </div>
          <div v-if="couponResult" class="coupon-success">
            <span>✅ {{ couponResult.message || 'کد تخفیف اعمال شد' }}</span>
            <button class="remove-coupon" type="button" @click="removeCoupon">×</button>
          </div>
          <p v-if="couponError" class="hint-error">{{ couponError }}</p>
        </section>

        <!-- ── Step 5: Notes ──────────────────────────────────── -->
        <section class="section-card">
          <h2 class="section-title">
            <span class="step-badge">{{ form.delivery_mode === 'delivery' ? '۵' : '۴' }}</span>
            یادداشت سفارش
          </h2>
          <textarea v-model="form.note" class="field-textarea" rows="3" placeholder="توضیح خاص برای آشپزخانه یا تحویل‌دهنده... (اختیاری)" />
        </section>

        <!-- ── Cart Summary ────────────────────────────────────── -->
        <section class="section-card summary-card">
          <h2 class="section-title">خلاصه سفارش</h2>
          <div class="summary-lines">
            <div v-for="line in cartLines" :key="line.id" class="summary-line">
              <div class="summary-line-info">
                <span class="qty-badge">{{ line.qty }}×</span>
                <span>{{ line.title }}</span>
              </div>
              <span>{{ formatMoney(line.line_total_preview ?? (line.base_price * line.qty), currency) }}</span>
            </div>
          </div>
          <div class="divider"></div>
          <div class="total-rows">
            <div class="total-row">
              <span>جمع اقلام</span>
              <span>{{ formatMoney(subtotal, currency) }}</span>
            </div>
            <div class="total-row" v-if="discountAmount > 0">
              <span>تخفیف کد</span>
              <span class="discount-val">-{{ formatMoney(discountAmount, currency) }}</span>
            </div>
            <div class="total-row" v-if="deliveryFee > 0">
              <span>هزینه ارسال</span>
              <span>{{ formatMoney(deliveryFee, currency) }}</span>
            </div>
            <div class="total-row grand">
              <strong>مبلغ قابل پرداخت</strong>
              <strong>{{ formatMoney(grandTotal, currency) }}</strong>
            </div>
          </div>
        </section>

        <!-- ── Error ──────────────────────────────────────────── -->
        <p v-if="submitError" class="submit-error">⚠️ {{ submitError }}</p>

        <!-- ── Submit ─────────────────────────────────────────── -->
        <button class="submit-btn" type="button" :disabled="submitting" @click="submitOrder">
          <span v-if="submitting" class="spinner"></span>
          <span v-else>ثبت و پرداخت سفارش</span>
        </button>

        <div class="bottom-spacer"></div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { cartState, clearCart, saveLastOrder } from '@/stores/cartStore'
import { formatMoney } from '@/utils/format'
import { placeOrder, validateCoupon, getCustomerCheckoutProfile, saveCustomerDeliveryAddress } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'

function readAuth() {
  try {
    return JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
  } catch { return {} }
}

const auth = readAuth()
const currency = ref('TOMAN')

const form = ref({
  customer_name: auth.customer_name || '',
  mobile: auth.mobile || '',
  delivery_mode: 'delivery',
  delivery_address_id: '',
  use_new_address: false,
  address_title: '',
  address_line: '',
  address_plaque: '',
  address_unit: '',
  address_floor: '',
  address_phone: auth.mobile || '',
  note: '',
})

const savedAddresses = ref([])
const profileLoading = ref(false)
const profileError = ref('')
const couponCode = ref('')
const couponLoading = ref(false)
const couponError = ref('')
const couponResult = ref(null)
const submitting = ref(false)
const submitError = ref('')

const cartLines = computed(() => cartState.lines)

const subtotal = computed(() =>
  cartLines.value.reduce((s, l) => s + Number(l.line_total_preview ?? (l.base_price * l.qty) ?? 0), 0)
)

const discountAmount = computed(() => Number(couponResult.value?.discount_amount || 0))
const deliveryFee = computed(() => form.value.delivery_mode === 'delivery' ? 0 : 0)
const grandTotal = computed(() => Math.max(0, subtotal.value - discountAmount.value + deliveryFee.value))

function goBack() { window.history.back() }

function normalizeMobile(v) {
  const d = String(v || '').replace(/\D/g, '')
  if (d.startsWith('98') && d.length === 12) return '0' + d.slice(2)
  if (d.startsWith('9') && d.length === 10) return '0' + d
  return d
}

async function loadProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const payload = await getCustomerCheckoutProfile({
      mobile: normalizeMobile(form.value.mobile),
      customer_name: form.value.customer_name,
    })
    const addresses = Array.isArray(payload?.addresses) ? payload.addresses : []
    savedAddresses.value = addresses
    if (!form.value.customer_name && payload?.customer?.name) {
      form.value.customer_name = payload.customer.name
    }
    if (addresses.length) {
      form.value.delivery_address_id = addresses[0].id
      form.value.use_new_address = false
    } else {
      form.value.use_new_address = true
    }
  } catch (err) {
    profileError.value = err.message || 'بارگذاری پروفایل ناموفق بود.'
  } finally {
    profileLoading.value = false
  }
}

async function applyCoupon() {
  if (!couponCode.value.trim()) return
  couponLoading.value = true
  couponError.value = ''
  couponResult.value = null
  try {
    couponResult.value = await validateCoupon({
      coupon_code: couponCode.value.trim(),
      mobile: normalizeMobile(form.value.mobile),
      subtotal: subtotal.value,
      items: cartLines.value.map(l => ({ item_code: l.item_code || l.id, qty: l.qty })),
    })
  } catch (err) {
    couponError.value = err.message || 'کد تخفیف معتبر نیست.'
  } finally {
    couponLoading.value = false
  }
}

function removeCoupon() {
  couponResult.value = null
  couponCode.value = ''
  couponError.value = ''
}

function validateForm() {
  if (!form.value.customer_name.trim()) return 'نام گیرنده الزامی است.'
  if (normalizeMobile(form.value.mobile).length < 10) return 'شماره موبایل معتبر وارد کنید.'
  if (form.value.delivery_mode === 'delivery') {
    if (!form.value.use_new_address && !form.value.delivery_address_id) return 'یک آدرس انتخاب کنید یا آدرس جدید ثبت کنید.'
    if (form.value.use_new_address || !savedAddresses.value.length) {
      if (!form.value.address_line.trim()) return 'آدرس دقیق الزامی است.'
      if (!form.value.address_plaque.trim()) return 'پلاک الزامی است.'
    }
  }
  if (!cartLines.value.length) return 'سبد خرید خالی است.'
  return ''
}

async function submitOrder() {
  const err = validateForm()
  if (err) { submitError.value = err; return }
  submitting.value = true
  submitError.value = ''
  const mobile = normalizeMobile(form.value.mobile)
  try {
    let deliveryAddressId = form.value.delivery_address_id
    let deliverySnapshot = {}

    if (form.value.delivery_mode === 'delivery' && (form.value.use_new_address || !savedAddresses.value.length)) {
      try {
        const saved = await saveCustomerDeliveryAddress({
          customer_info: { name: form.value.customer_name, mobile },
          address_info: {
            title: form.value.address_title || 'آدرس جدید',
            phone: normalizeMobile(form.value.address_phone || mobile),
            address_line: form.value.address_line,
            plaque: form.value.address_plaque,
            unit: form.value.address_unit,
            floor: form.value.address_floor,
            lat: null,
            lng: null,
            is_primary: 0,
          },
        })
        deliveryAddressId = saved?.address?.id || ''
        deliverySnapshot = saved?.address || {}
      } catch (_) {
        deliverySnapshot = {
          address_line: form.value.address_line,
          plaque: form.value.address_plaque,
          unit: form.value.address_unit,
          phone: normalizeMobile(form.value.address_phone || mobile),
          title: form.value.address_title,
        }
      }
    } else if (form.value.delivery_mode === 'delivery' && form.value.delivery_address_id) {
      const selected = savedAddresses.value.find(a => a.id === form.value.delivery_address_id)
      deliverySnapshot = selected || {}
    }

    const response = await placeOrder({
      customer_info: { name: form.value.customer_name, mobile },
      delivery_mode: form.value.delivery_mode,
      order_type: form.value.delivery_mode === 'delivery' ? 'delivery' : 'takeaway',
      delivery_address_id: form.value.delivery_mode === 'delivery' ? deliveryAddressId : '',
      delivery_address_snapshot: form.value.delivery_mode === 'delivery' ? deliverySnapshot : {},
      pickup_method: form.value.delivery_mode === 'pickup' ? 'walk' : '',
      address: form.value.delivery_mode === 'delivery' ? (deliverySnapshot?.address_line || form.value.address_line) : '',
      note: form.value.note,
      coupon_code: couponResult.value?.code || couponCode.value.trim() || '',
      items: cartLines.value.map(l => ({
        item_code: l.item_code || l.id || l.slug,
        item_name: l.title,
        qty: l.qty,
        rate: l.base_price || 0,
        customization: l.customization || {},
      })),
    })

    saveLastOrder({ order_code: response.order_code, mobile })
    clearCart()
    window.location.href = `/order-success/${response.order_code}?mobile=${encodeURIComponent(mobile)}`
  } catch (err) {
    submitError.value = err.message || 'ثبت سفارش با خطا مواجه شد. دوباره تلاش کنید.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.checkout-page {
  min-height: 100vh;
  background: #f7f0e8;
  dir: rtl;
  font-family: inherit;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: #fff;
  border-bottom: 1px solid #e8ddd3;
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f7f0e8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #3f2a1d;
  flex-shrink: 0;
}

.page-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #3f2a1d;
  flex: 1;
  text-align: center;
  margin: 0;
}

.header-spacer { width: 36px; flex-shrink: 0; }

.checkout-body {
  max-width: 640px;
  margin: 0 auto;
  padding: 1.25rem 1rem 6rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-card {
  background: #fff;
  border-radius: 16px;
  padding: 3rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  margin-top: 2rem;
}

.empty-icon { font-size: 3.5rem; }

.empty-card h3 { font-size: 1.15rem; color: #3f2a1d; margin: 0; }
.empty-card p { color: #9e8878; margin: 0; font-size: 0.9rem; }

.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(111,74,49,0.06);
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #3f2a1d;
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.step-badge {
  background: #6f4a31;
  color: #fff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.field-group { margin-bottom: 0.85rem; }
.field-label { display: block; font-size: 0.82rem; color: #9e8878; margin-bottom: 0.35rem; font-weight: 600; }

.field-input, .field-textarea {
  width: 100%;
  border: 1.5px solid #e8ddd3;
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  font-size: 0.95rem;
  color: #3f2a1d;
  background: #faf7f4;
  transition: border-color 0.2s;
  box-sizing: border-box;
  font-family: inherit;
}

.field-input:focus, .field-textarea:focus {
  outline: none;
  border-color: #6f4a31;
  background: #fff;
}

.field-textarea { resize: vertical; min-height: 70px; }

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.load-profile-btn {
  width: 100%;
  padding: 0.65rem;
  border: 1.5px dashed #c4a882;
  border-radius: 10px;
  background: transparent;
  color: #6f4a31;
  font-size: 0.87rem;
  cursor: pointer;
  margin-top: 0.25rem;
  transition: background 0.2s;
}

.load-profile-btn:hover { background: #faf0e6; }
.load-profile-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.hint-error { color: #b84f4f; font-size: 0.82rem; margin: 0.35rem 0 0; }

.mode-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.mode-card {
  border: 2px solid #e8ddd3;
  border-radius: 14px;
  background: #faf7f4;
  padding: 1rem 0.75rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  text-align: center;
  transition: all 0.2s;
}

.mode-card.active {
  border-color: #6f4a31;
  background: #fdf5ee;
}

.mode-icon { font-size: 1.8rem; }
.mode-card strong { font-size: 0.9rem; color: #3f2a1d; }
.mode-card small { font-size: 0.75rem; color: #9e8878; }

.saved-list { display: flex; flex-direction: column; gap: 0.6rem; }

.saved-item {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.85rem;
  border: 1.5px solid #e8ddd3;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.saved-item:has(input:checked) { border-color: #6f4a31; background: #fdf5ee; }
.saved-item input { margin-top: 3px; accent-color: #6f4a31; }
.saved-body strong { display: block; font-size: 0.9rem; color: #3f2a1d; }
.saved-body p { margin: 0.2rem 0 0; font-size: 0.82rem; color: #5a4030; }
.saved-body small { font-size: 0.78rem; color: #9e8878; }

.ghost-btn {
  background: transparent;
  border: 1.5px dashed #c4a882;
  border-radius: 10px;
  padding: 0.6rem 1rem;
  color: #6f4a31;
  font-size: 0.85rem;
  cursor: pointer;
  margin-top: 0.25rem;
  width: 100%;
}

.new-address-form { margin-top: 0.75rem; }

.coupon-row {
  display: flex;
  gap: 0.6rem;
}

.coupon-input { flex: 1; }

.apply-btn {
  background: #6f4a31;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.7rem 1.2rem;
  font-size: 0.9rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}

.apply-btn:hover { background: #5a3a27; }
.apply-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.coupon-success {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #e8f5e9;
  border-radius: 10px;
  padding: 0.6rem 0.9rem;
  margin-top: 0.5rem;
  font-size: 0.88rem;
  color: #2e7d32;
}

.remove-coupon {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
}

.summary-card { }

.summary-lines { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }

.summary-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #5a4030;
}

.summary-line-info { display: flex; align-items: center; gap: 0.5rem; }

.qty-badge {
  background: #f7f0e8;
  color: #6f4a31;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  min-width: 24px;
  text-align: center;
}

.divider { height: 1px; background: #e8ddd3; margin: 0.75rem 0; }

.total-rows { display: flex; flex-direction: column; gap: 0.5rem; }

.total-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #5a4030;
}

.total-row.grand {
  font-size: 1.05rem;
  color: #3f2a1d;
  margin-top: 0.25rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e8ddd3;
}

.discount-val { color: #2e7d32; }

.submit-error {
  background: #fdecea;
  color: #b84f4f;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  margin: 0;
}

.submit-btn {
  width: 100%;
  background: #6f4a31;
  color: #fff;
  border: none;
  border-radius: 14px;
  padding: 1.1rem;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-btn:hover { background: #5a3a27; }
.submit-btn:active { transform: scale(0.98); }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid rgba(255,255,255,0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.primary-btn {
  display: inline-block;
  background: #6f4a31;
  color: #fff;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.95rem;
  margin-top: 0.25rem;
}

.bottom-spacer { height: 2rem; }
</style>
