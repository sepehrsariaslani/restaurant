<template>
  <section class="order-flow-page">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">ارسال با پیک</p>
        <h1 class="order-flow-title">آدرس تحویل را انتخاب کنید</h1>
        <p class="order-flow-subtitle">با انتخاب آدرس، شعبه پیشنهادی، هزینه ارسال و زمان تقریبی تحویل مشخص می‌شود.</p>
      </div>
      <a class="order-flow-secondary" href="/order/type">تغییر نوع سفارش</a>
    </header>

    <div class="order-flow-layout">
      <main class="order-flow-list">
        <section class="order-flow-card">
          <h2>اطلاعات مشتری</h2>
          <div class="order-flow-form">
            <label class="order-flow-field">
              <span>نام مشتری</span>
              <input class="order-flow-input" v-model="customerName" placeholder="مثلاً علی محمدی" />
            </label>
            <label class="order-flow-field">
              <span>موبایل</span>
              <input class="order-flow-input" dir="ltr" inputmode="numeric" v-model="mobile" placeholder="09123456789" />
            </label>
            <button class="order-flow-secondary" type="button" :disabled="profileLoading || normalizedMobile.length < 10" @click="loadProfile">
              {{ profileLoading ? 'در حال دریافت...' : 'نمایش آدرس‌های ذخیره شده' }}
            </button>
          </div>
          <p v-if="profileError" class="order-flow-alert danger">{{ profileError }}</p>
        </section>

        <section class="order-flow-card" v-if="savedAddresses.length">
          <h2>آدرس‌های ذخیره‌شده</h2>
          <div class="order-flow-list">
            <button
              v-for="address in savedAddresses"
              :key="address.id"
              type="button"
              class="order-flow-address-card"
              :class="{ active: selectedAddressId === address.id && !useNewAddress }"
              @click="selectAddress(address)"
            >
              <strong>{{ address.title || 'آدرس' }}</strong>
              <p>{{ address.address_line || '-' }}</p>
              <small>{{ address.phone || normalizedMobile }}</small>
            </button>
          </div>
          <button class="order-flow-secondary" type="button" @click="useNewAddress = true; selectedAddressId = ''">افزودن آدرس جدید</button>
        </section>

        <section class="order-flow-card" v-if="useNewAddress || !savedAddresses.length">
          <h2>ثبت آدرس جدید</h2>
          <div class="order-flow-form">
            <label class="order-flow-field"><span>عنوان آدرس</span><input class="order-flow-input" v-model="address.title" placeholder="خانه، محل کار..." /></label>
            <label class="order-flow-field"><span>آدرس دقیق</span><textarea class="order-flow-textarea" rows="3" v-model="address.address_line" placeholder="خیابان، کوچه، پلاک..." /></label>
            <div class="order-flow-grid order-flow-grid--2">
              <label class="order-flow-field"><span>پلاک</span><input class="order-flow-input" v-model="address.plaque" /></label>
              <label class="order-flow-field"><span>واحد</span><input class="order-flow-input" v-model="address.unit" /></label>
            </div>
            <p class="order-flow-alert">در صورت عدم دسترسی به نقشه، آدرس را کامل و دقیق بنویسید. نیازی به وارد کردن مختصات نیست.</p>
            <details class="advanced-location-box">
              <summary>تنظیمات پیشرفته موقعیت</summary>
              <div class="order-flow-grid order-flow-grid--2">
                <label class="order-flow-field"><span>عرض جغرافیایی</span><input class="order-flow-input" dir="ltr" v-model="address.lat" /></label>
                <label class="order-flow-field"><span>طول جغرافیایی</span><input class="order-flow-input" dir="ltr" v-model="address.lng" /></label>
              </div>
            </details>
          </div>
        </section>

        <section class="order-flow-card">
          <h2>شعبه ارسال و یادداشت پیک</h2>
          <p v-if="branchSuggestion">شعبه پیشنهادی: <strong>{{ branchSuggestion.title || branchSuggestion.name }}</strong></p>
          <p v-else>پس از انتخاب آدرس، نزدیک‌ترین یا اولین شعبه فعال برای ارسال پیشنهاد می‌شود.</p>
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

      <OrderContextSummary next-step="مشاهده منو و انتخاب غذا" :currency="currency">
        <button class="order-flow-primary" type="button" :disabled="!canContinue || outOfRange" @click="continueToMenu">مشاهده منو</button>
        <button v-if="outOfRange" class="order-flow-secondary" type="button" @click="resetAddress">انتخاب آدرس دیگر</button>
      </OrderContextSummary>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import { cartState, saveCheckoutDraft, saveOrderContext } from '@/stores/cartStore'
import { formatMoney, normalizeMobile as normalizeMobileUtil } from '@/utils/format'
import { getBranches, getCustomerCheckoutProfile, getMenuBoot } from '@/utils/api'
import './orderFlow.css'

const customerName = ref(cartState.checkoutDraft.customer_name || '')
const mobile = ref(cartState.checkoutDraft.mobile || '')
const savedAddresses = ref([])
const selectedAddressId = ref(cartState.checkoutDraft.delivery_address_id || '')
const useNewAddress = ref(cartState.checkoutDraft.use_new_address !== false)
const profileLoading = ref(false)
const profileError = ref('')
const branches = ref([])
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
const branchSuggestion = computed(() => branches.value.find((row) => row.delivery_available !== false && row.isOpen !== false) || branches.value[0] || null)
const outOfRange = computed(() => {
  const lat = Number(address.lat)
  const lng = Number(address.lng)
  if (!address.address_line) return false
  if ((address.lat || address.lng) && (!Number.isFinite(lat) || !Number.isFinite(lng))) return true
  return false
})
const etaMin = computed(() => Number(branchSuggestion.value?.delivery_eta_min || 35))
const etaMax = computed(() => Number(branchSuggestion.value?.delivery_eta_max || 45))
const deliveryFee = computed(() => Number(branchSuggestion.value?.delivery_fee || 0))
const etaText = computed(() => `${etaMin.value} تا ${etaMax.value} دقیقه`)
const deliveryFeeText = computed(() => deliveryFee.value ? formatMoney(deliveryFee.value, currency.value) : 'پس از تایید شعبه')
const canContinue = computed(() => Boolean(customerName.value.trim() && normalizedMobile.value.length >= 10 && address.address_line.trim()))

watch([customerName, mobile, selectedAddressId, useNewAddress, address, courierNote, branchSuggestion], persistContext, { deep: true })

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
  }
}

function persistContext() {
  const selectedBranch = branchSuggestion.value
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
    branch: selectedBranch?.id || selectedBranch?.name || '',
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

async function loadProfile() {
  if (normalizedMobile.value.length < 10) return
  profileLoading.value = true
  profileError.value = ''
  try {
    const payload = await getCustomerCheckoutProfile({ mobile: normalizedMobile.value, customer_name: customerName.value })
    savedAddresses.value = Array.isArray(payload.addresses) ? payload.addresses : []
    if (!customerName.value && payload.customer?.name) customerName.value = payload.customer.name
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
    currency.value = boot?.currency || 'IRR'
    persistContext()
  } catch (err) {
    profileError.value = err.message || 'دریافت تنظیمات ارسال ناموفق بود.'
  }
}

function continueToMenu() {
  if (!canContinue.value || outOfRange.value) return
  const branch = branchSuggestion.value?.id || branchSuggestion.value?.name || ''
  window.location.href = branch ? `/menu?branch=${encodeURIComponent(branch)}` : '/menu'
}

onMounted(() => {
  saveOrderContext({ order_type: 'delivery' })
  loadBoot()
  if (normalizedMobile.value.length >= 10) loadProfile()
})
</script>

<style scoped>
.advanced-location-box {
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 16px;
  padding: 0.75rem;
  background: rgb(var(--palette-june-bud-rgb) / 0.22);
}

.advanced-location-box summary {
  cursor: pointer;
  min-height: 44px;
  display: flex;
  align-items: center;
  font-weight: 800;
  color: var(--accent-green);
}
</style>
