<template>
  <section class="order-flow-page order-flow-page--mobile-cta">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">ارسال با پیک</p>
        <h1 class="order-flow-title">آدرس تحویل را انتخاب کنید</h1>
        <p class="order-flow-subtitle">آدرس و شعبهِ آماده‌سازی را انتخاب کنید تا هزینه ارسال و زمان تقریبی تحویل مشخص شود.</p>
      </div>
      <a class="order-flow-secondary" href="/order/type">تغییر نوع سفارش</a>
    </header>

    <nav class="order-flow-steps" aria-label="مراحل سفارش">
      <span class="order-flow-step is-complete">۱. نوع سفارش</span>
      <span class="order-flow-step active" aria-current="step">۲. آدرس و شعبه</span>
      <span class="order-flow-step">۳. منوی شعبه</span>
      <span class="order-flow-step">۴. ثبت سفارش</span>
    </nav>

    <div class="order-flow-layout">
      <main class="order-flow-list">
        <div v-if="!isCustomerLoggedIn" class="delivery-signin-hint">
          <span>آدرس ذخیره‌شده دارید؟</span><a href="/customer/login?redirect=%2Forder%2Fdelivery">ورود به حساب</a>
        </div>
        <p v-if="profileLoading" class="order-flow-alert" role="status">در حال دریافت آدرس‌های شما…</p>
        <p v-if="profileError" class="order-flow-alert danger" role="alert">{{ profileError }}</p>

        <section class="order-flow-card" v-if="savedAddresses.length">
          <h2>آدرس‌های ذخیره‌شده</h2>
          <div class="order-flow-list">
            <button
              v-for="address in savedAddresses"
              :key="address.id"
              type="button"
              class="order-flow-address-card"
              :class="{ active: selectedAddressId === address.id && !useNewAddress }"
              :aria-pressed="selectedAddressId === address.id && !useNewAddress"
              @click="selectAddress(address)"
            >
              <strong>{{ address.title || 'آدرس' }}</strong>
              <p>{{ address.address_line || '-' }}</p>
              <small>{{ address.phone || normalizedMobile }}</small>
            </button>
          </div>
          <button class="order-flow-secondary" type="button" @click="resetAddress">افزودن آدرس جدید</button>
        </section>

        <section class="order-flow-card" v-if="useNewAddress || !savedAddresses.length">
          <h2>ثبت آدرس جدید</h2>
          <div class="order-flow-form">
            <div class="delivery-location-toolbar">
              <div><strong>نقطه تحویل روی نقشه</strong><small>نشانگر را روی محل دقیق خانه بگذارید؛ این موقعیت برای پیک لازم است.</small></div>
              <button class="order-flow-secondary" type="button" :disabled="locating" @click="useCurrentLocation">{{ locating ? 'در حال دریافت موقعیت...' : 'انتخاب موقعیت من' }}</button>
            </div>
            <AddressPickerMap v-model="addressLocation" :config="deliveryMapConfig" @status="mapStatus = $event" />
            <p v-if="locationError" class="order-flow-alert danger">{{ locationError }}</p>
            <p v-else-if="hasCoordinates" class="order-flow-alert">موقعیت آدرس روی نقشه ثبت شد.</p>
            <p v-else class="order-flow-alert danger">برای ارسال، انتخاب موقعیت روی نقشه یا ثبت مختصات الزامی است.</p>
            <details class="advanced-location-box" :open="mapStatus === 'error'">
              <summary>تنظیمات پیشرفته موقعیت</summary>
              <div class="order-flow-grid order-flow-grid--2">
                <label class="order-flow-field"><span>عرض جغرافیایی</span><input class="order-flow-input" dir="ltr" v-model="address.lat" /></label>
                <label class="order-flow-field"><span>طول جغرافیایی</span><input class="order-flow-input" dir="ltr" v-model="address.lng" /></label>
              </div>
            </details>
            <label class="order-flow-field"><span>عنوان آدرس</span><input class="order-flow-input" v-model="address.title" placeholder="خانه، محل کار..." /></label>
            <label class="order-flow-field"><span>آدرس دقیق</span><textarea class="order-flow-textarea" rows="3" v-model="address.address_line" placeholder="خیابان، کوچه، پلاک..." /></label>
            <div class="order-flow-grid order-flow-grid--2">
              <label class="order-flow-field"><span>پلاک</span><input class="order-flow-input" v-model="address.plaque" /></label>
              <label class="order-flow-field"><span>واحد</span><input class="order-flow-input" v-model="address.unit" /></label>
            </div>

          </div>
        </section>

        <label v-if="isCustomerLoggedIn && useNewAddress" class="delivery-save-address">
          <input v-model="saveAddressForFuture" type="checkbox" /> ذخیره این آدرس در حساب من
        </label>

        <section class="order-flow-card">
          <h2>انتخاب شعبه برای آماده‌سازی</h2>
          <p>از میان شعبه‌های فعالِ قابل‌ارسال، محل آماده‌سازی سفارشتان را انتخاب کنید.</p>
          <div class="order-flow-list company-choice-list">
            <button
              v-for="company in deliveryCompanies"
              :key="branchKey(company)"
              type="button"
              class="order-flow-branch-card"
              :class="{ active: selectedCompanyId === branchKey(company) }"
              @click="selectedCompanyId = branchKey(company)"
            >
              <div class="order-flow-card-head">
                <div><h3>{{ company.title || company.name }}</h3><p>{{ company.address || 'آدرس شعبه ثبت نشده است.' }}</p></div>
                <span class="order-flow-pill">ارسال فعال</span>
              </div>
              <div class="order-flow-branch-meta"><span class="order-flow-pill">{{ deliveryTimeFor(company) }}</span><span class="order-flow-pill">{{ deliveryFeeFor(company) }}</span></div>
            </button>
          </div>
          <p v-if="!deliveryCompanies.length" class="order-flow-alert danger">فعلاً شعبه فعالی برای ارسال وجود ندارد.</p>
        </section>

        <section class="order-flow-card">
          <h2>جزئیات ارسال و یادداشت پیک</h2>
          <p v-if="selectedCompany">شعبه انتخاب‌شده: <strong>{{ selectedCompany.title || selectedCompany.name }}</strong></p>
          <p v-else>برای ادامه، شعبهِ آماده‌سازی را انتخاب کنید.</p>
          <div class="order-flow-branch-meta" style="margin:.75rem 0">
            <span class="order-flow-pill">زمان پیشنهادی: {{ etaText }}</span>
            <span class="order-flow-pill">هزینه ارسال: {{ deliveryFeeText }}</span>
          </div>
          <p class="order-flow-alert">هزینه و زمان نهایی ارسال پس از تایید شعبه قطعی می‌شود.</p>
          <p v-if="outOfRange" class="order-flow-alert danger">این آدرس خارج از محدوده ارسال است.</p>
          <label class="order-flow-field">
            <span>یادداشت پیک</span>
            <textarea class="order-flow-textarea" rows="3" v-model="courierNote" placeholder="مثلاً زنگ واحد خراب است، تماس بگیرید" />
          </label>
        </section>
      </main>

      <OrderContextSummary :next-step="nextStep" :currency="currency">
        <button class="order-flow-primary" type="button" :disabled="!canContinue || outOfRange || savingAddress" @click="continueToMenu">{{ savingAddress ? 'در حال ذخیره آدرس…' : continueLabel }}</button>
        <button v-if="outOfRange" class="order-flow-secondary" type="button" @click="resetAddress">انتخاب آدرس دیگر</button>
      </OrderContextSummary>
    </div>

    <div class="order-mobile-cta" role="region" aria-label="ادامه سفارش ارسال">
      <div>
        <small>{{ selectedCompany ? (selectedCompany.title || selectedCompany.name) : 'شعبه انتخاب نشده' }}</small>
        <strong>{{ address.address_line || 'آدرس تحویل را انتخاب کنید' }}</strong>
      </div>
      <button class="order-flow-primary" type="button" :disabled="!canContinue || outOfRange || savingAddress" @click="continueToMenu">{{ savingAddress ? 'در حال ذخیره آدرس…' : continueLabel }}</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import AddressPickerMap from '@/components/checkout/AddressPickerMap.vue'
import { cartState, saveCheckoutDraft, saveOrderContext } from '@/stores/cartStore'
import { formatMoney, normalizeMobile as normalizeMobileUtil } from '@/utils/format'
import { isCustomerDeliveryCompany, resolveDeliveryCompanySelection } from '@/utils/orderBranches'
import { getBranches, getCustomerCheckoutProfile, getMenuBoot, saveCustomerDeliveryAddress } from '@/utils/api'
import { hasDeliveryCoordinates, deliveryOutsideRadius } from '@/utils/customerOrderValidation'
import './orderFlow.css'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
function readAuth() {
  try { return JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}') } catch { return {} }
}
const auth = readAuth()
const isCustomerLoggedIn = computed(() => Boolean(auth.mobile))
const customerName = ref(auth.customer_name || localStorage.getItem('customer_name') || cartState.checkoutDraft.customer_name || '')
const mobile = ref(auth.mobile || localStorage.getItem('customer_phone') || cartState.checkoutDraft.mobile || '')
const savedAddresses = ref([])
const mapStatus = ref('')
const saveAddressForFuture = ref(true)
const savingAddress = ref(false)
const selectedAddressId = ref(cartState.checkoutDraft.delivery_address_id || '')
const useNewAddress = ref(cartState.checkoutDraft.use_new_address !== false)
const profileLoading = ref(false)
const profileError = ref('')
const locating = ref(false)
const locationError = ref('')
const mapConfig = ref({
  provider: 'neshan',
  api_key: '',
  script_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.js',
  style_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.css',
  default_lat: 35.6997,
  default_lng: 51.3381,
  default_zoom: 13,
})
const branches = ref([])
const selectedCompanyId = ref(cartState.orderContext.branch || '')
const currency = ref('IRR')
const courierNote = ref(cartState.orderContext.courier_note || '')
const address = reactive({
  title: cartState.orderContext.address?.title || cartState.checkoutDraft.address_title || '',
  phone: cartState.orderContext.address?.phone || cartState.checkoutDraft.address_phone || '',
  address_line: cartState.orderContext.address?.address_line || cartState.checkoutDraft.address_line || '',
  plaque: cartState.orderContext.address?.plaque || cartState.checkoutDraft.address_plaque || '',
  unit: cartState.orderContext.address?.unit || cartState.checkoutDraft.address_unit || '',
  floor: cartState.orderContext.address?.floor || cartState.checkoutDraft.address_floor || '',
  lat: cartState.orderContext.address?.lat ?? cartState.checkoutDraft.address_lat ?? '',
  lng: cartState.orderContext.address?.lng ?? cartState.checkoutDraft.address_lng ?? '',
})

const normalizedMobile = computed(() => normalizeMobileUtil(mobile.value || ''))
const hasCoordinates = computed(() => hasDeliveryCoordinates(address))
const addressLocation = computed({
  get: () => ({ lat: address.lat, lng: address.lng }),
  set: (point = {}) => {
    address.lat = point.lat ?? ''
    address.lng = point.lng ?? ''
    locationError.value = ''
  },
})
function branchKey(branch = {}) { return branch.id || branch.name || '' }
const deliveryCompanies = computed(() => branches.value.filter(isCustomerDeliveryCompany))
const selectedCompany = computed(() => deliveryCompanies.value.find((row) => branchKey(row) === selectedCompanyId.value) || null)
const deliveryMapConfig = computed(() => hasDeliveryCoordinates(selectedCompany.value || {})
  ? { ...mapConfig.value, default_lat: selectedCompany.value.lat, default_lng: selectedCompany.value.lng }
  : mapConfig.value)
const outOfRange = computed(() => deliveryOutsideRadius(address, selectedCompany.value || {}))
const etaMin = computed(() => Number(selectedCompany.value?.delivery_eta_min || 35))
const etaMax = computed(() => Number(selectedCompany.value?.delivery_eta_max || 45))
const deliveryFee = computed(() => Number(selectedCompany.value?.delivery_fee || 0))
const etaText = computed(() => `${etaMin.value} تا ${etaMax.value} دقیقه`)
const deliveryFeeText = computed(() => deliveryFee.value ? formatMoney(deliveryFee.value, currency.value) : 'پس از تایید شعبه')
const canContinue = computed(() => Boolean(address.address_line.trim() && hasCoordinates.value && selectedCompany.value))
const hasCartLines = computed(() => cartState.lines.length > 0)
const continueLabel = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'ادامه به منوی شعبه')
const nextStep = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'مشاهده منو و انتخاب غذا')
const deliveryTimeFor = (company) => `${Number(company?.delivery_eta_min || 35)} تا ${Number(company?.delivery_eta_max || 45)} دقیقه`
const deliveryFeeFor = (company) => Number(company?.delivery_fee || 0) ? formatMoney(company.delivery_fee, currency.value) : 'هزینه پس از تأیید'

watch([customerName, mobile, selectedAddressId, useNewAddress, address, courierNote, selectedCompany, saveAddressForFuture], persistContext, { deep: true })

function selectedAddressPayload() {
  return {
    id: useNewAddress.value ? '' : selectedAddressId.value,
    title: address.title || 'آدرس تحویل',
    phone: normalizeMobileUtil(address.phone || mobile.value),
    address_line: address.address_line,
    plaque: address.plaque,
    unit: address.unit,
    floor: address.floor,
    lat: address.lat,
    lng: address.lng,
    save_for_future: isCustomerLoggedIn.value && saveAddressForFuture.value,
  }
}

function persistContext() {
  const selectedBranch = selectedCompany.value
  saveCheckoutDraft({
    customer_name: customerName.value,
    mobile: normalizedMobile.value,
    delivery_mode: 'delivery',
    order_type: 'delivery',
    delivery_address_id: useNewAddress.value ? '' : selectedAddressId.value,
    use_new_address: useNewAddress.value,
    address_title: address.title,
    address_phone: normalizeMobileUtil(address.phone || mobile.value),
    address_line: address.address_line,
    address_plaque: address.plaque,
    address_unit: address.unit,
    address_floor: address.floor,
    address_lat: address.lat,
    address_lng: address.lng,
    note: cartState.checkoutDraft.note || '',
  })
  saveOrderContext({
    order_type: 'delivery',
    branch: selectedCompany.value?.id || selectedCompany.value?.name || '',
    branch_title: selectedBranch?.title || selectedBranch?.name || '',
    address: selectedAddressPayload(),
    eta_min: etaMin.value,
    eta_max: etaMax.value,
    delivery_fee: deliveryFee.value,
    courier_note: courierNote.value,
    out_of_range: outOfRange.value,
  })
}

function selectAddress(row) {
  selectedAddressId.value = row.id
  useNewAddress.value = false
  Object.assign(address, {
    title: row.title || '',
    phone: row.phone || normalizedMobile.value,
    address_line: row.address_line || '',
    plaque: row.plaque || '',
    unit: row.unit || '',
    floor: row.floor || '',
    lat: row.lat ?? '',
    lng: row.lng ?? '',
  })
}

function resetAddress() {
  selectedAddressId.value = ''
  useNewAddress.value = true
  Object.assign(address, { title: '', phone: normalizedMobile.value, address_line: '', plaque: '', unit: '', floor: '', lat: '', lng: '' })
}

function useCurrentLocation() {
  locationError.value = ''
  if (!navigator.geolocation) {
    locationError.value = 'مرورگر شما دسترسی به موقعیت مکانی را پشتیبانی نمی‌کند.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      address.lat = Number(position.coords.latitude.toFixed(6))
      address.lng = Number(position.coords.longitude.toFixed(6))
      locating.value = false
    },
    () => {
      locating.value = false
      locationError.value = 'دریافت موقعیت ممکن نشد؛ اجازه GPS را فعال کنید یا نقطه را روی نقشه بگذارید.'
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
  )
}

async function loadProfile() {
  if (normalizedMobile.value.length < 10) return
  profileLoading.value = true
  profileError.value = ''
  try {
    const payload = await getCustomerCheckoutProfile({ mobile: normalizedMobile.value, customer_name: customerName.value })
    savedAddresses.value = Array.isArray(payload.addresses) ? payload.addresses : []
    if (!customerName.value && payload.customer?.name) customerName.value = payload.customer.name
    if (isCustomerLoggedIn.value && !customerName.value) customerName.value = 'مشتری'
    if (savedAddresses.value.length && !selectedAddressId.value && !address.address_line) selectAddress(savedAddresses.value[0])
  } catch (err) {
    profileError.value = err.message || 'دریافت آدرس‌های مشتری ناموفق بود.'
  } finally {
    profileLoading.value = false
  }
}

async function loadBoot() {
  try {
    const [branchPayload, boot] = await Promise.all([getBranches(), getMenuBoot('')])
    branches.value = Array.isArray(branchPayload?.branches) ? branchPayload.branches : []
    selectedCompanyId.value = resolveDeliveryCompanySelection(branches.value, selectedCompanyId.value)
    currency.value = boot?.currency || 'IRR'
    if (boot?.checkout_map && typeof boot.checkout_map === 'object') {
      mapConfig.value = { ...mapConfig.value, ...boot.checkout_map }
    }
    persistContext()
  } catch (err) {
    profileError.value = err.message || 'دریافت تنظیمات ارسال ناموفق بود.'
  }
}

async function continueToMenu() {
  if (!canContinue.value || outOfRange.value || savingAddress.value) return
  profileError.value = ''
  if (isCustomerLoggedIn.value && useNewAddress.value && saveAddressForFuture.value) {
    savingAddress.value = true
    try {
      const result = await saveCustomerDeliveryAddress({ customer_info: { name: customerName.value || 'مشتری', mobile: normalizedMobile.value }, address_info: selectedAddressPayload() })
      if (!result?.address?.id) throw new Error('آدرس ذخیره نشد؛ دوباره تلاش کنید.')
      savedAddresses.value = result.addresses || []
      selectAddress(result.address)
    } catch (err) { profileError.value = err.message || 'ذخیره آدرس انجام نشد.'; return }
    finally { savingAddress.value = false }
  }
  persistContext()
  if (hasCartLines.value) {
    window.location.href = '/checkout'
    return
  }
  const branch = selectedCompany.value?.id || selectedCompany.value?.name || ''
  window.location.href = branch ? `/menu?branch=${encodeURIComponent(branch)}` : '/menu'
}

onMounted(() => {
  saveOrderContext({ order_type: 'delivery' })
  loadBoot()
  if (isCustomerLoggedIn.value) loadProfile()
})
</script>

<style scoped>
.delivery-signin-hint, .delivery-save-address { display: flex; align-items: center; gap: .6rem; min-height: 44px; font-size: .9rem; }
.delivery-signin-hint a { color: var(--ds-color-action-primary); font-weight: 700; padding: .5rem; }
.delivery-save-address input { width: 20px; height: 20px; }

.advanced-location-box {
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 16px;
  padding: 0.75rem;
  background: rgb(var(--palette-june-bud-rgb) / 0.22);
}

.delivery-customer-summary { display: flex; flex-wrap: wrap; align-items: center; gap: .6rem 1rem; padding: .75rem; border-radius: 16px; background: var(--ds-color-surface-muted); }
.delivery-customer-summary span { direction: ltr; }
.delivery-location-toolbar { display: flex; align-items: center; justify-content: space-between; gap: .75rem; }
.delivery-location-toolbar > div { display: grid; gap: .2rem; }
.delivery-location-toolbar small { color: var(--text-muted); line-height: 1.6; }
@media (max-width: 560px) { .delivery-location-toolbar { align-items: stretch; flex-direction: column; } }

.advanced-location-box summary {
  cursor: pointer;
  min-height: 44px;
  display: flex;
  align-items: center;
  font-weight: 800;
  color: var(--accent-green);
}
</style>
