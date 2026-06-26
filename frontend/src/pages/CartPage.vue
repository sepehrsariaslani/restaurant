<template>
  <LiquidGlassBackdrop>
    <section class="cart-shell">
      <section class="cart-frame">
        <header class="top-row">
          <a class="icon-btn" href="/menu" aria-label="بازگشت به منو">←</a>
          <p>سبد خرید</p>
          <span class="top-spacer" aria-hidden="true"></span>
        </header>

        <h1>آیتم ها <span>{{ totalQty }}</span></h1>

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
            <span>جمع کل</span>
            <strong>{{ formatMoney(subtotal, currency) }}</strong>
          </div>
          <div class="sum-row">
            <span>اضافات و مالیات</span>
            <strong>{{ formatMoney(taxAmount, currency) }}</strong>
          </div>
          <div class="sum-row">
            <span>ارسال</span>
            <strong>{{ shippingAmount > 0 ? formatMoney(shippingAmount, currency) : 'رایگان' }}</strong>
          </div>
          <div class="sum-row" v-if="discountAmount > 0">
            <span>تخفیف</span>
            <strong>-{{ formatMoney(discountAmount, currency) }}</strong>
          </div>
          <div class="sum-row total">
            <span>خالص پرداختنی</span>
            <strong>{{ formatMoney(totalAmount, currency) }}</strong>
          </div>

          <a class="checkout-btn" :class="{ disabled: !cartState.lines.length }" href="/checkout" @click.prevent="cartState.lines.length && (window.location.href='/checkout')">ادامه و ثبت سفارش →</a>
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

    <teleport to="body">
      <div class="checkout-overlay" v-if="showCheckout" @click.self="showCheckout = false">
        <section class="checkout-panel">
          <header class="checkout-head">
            <h3>ثبت سفارش</h3>
            <button class="icon-btn" type="button" @click="showCheckout = false">×</button>
          </header>

          <div class="fields">
            <label>
              <span>نام مشتری</span>
              <input class="input" :value="checkoutForm.customer_name" @input="setCheckoutField('customer_name', $event.target.value)" />
            </label>

            <label>
              <span>موبایل</span>
              <input class="input" :value="checkoutForm.mobile" @input="setCheckoutField('mobile', $event.target.value)" />
            </label>

            <div class="profile-actions">
              <button class="ghost-btn" type="button" @click="loadCustomerProfile" :disabled="!canLookupProfile || customerLookupLoading">
                {{ customerLookupLoading ? 'در حال بررسی...' : 'نمایش آدرس های ذخیره شده' }}
              </button>
              <p class="hint" v-if="customerLookupError">{{ customerLookupError }}</p>
            </div>

            <div class="delivery-mode-grid delivery-mode-grid--three">
              <button
                type="button"
                class="mode-chip"
                :class="{ active: checkoutForm.delivery_mode === 'pickup' && checkoutForm.pickup_method !== 'car' }"
                @click="setDeliveryMode('pickup')"
              >
                حضوری
                <small>خودم تحویل می‌گیرم</small>
              </button>
              <button
                type="button"
                class="mode-chip"
                :class="{ active: checkoutForm.delivery_mode === 'pickup' && checkoutForm.pickup_method === 'car' }"
                @click="setDeliveryMode('pickup_car')"
              >
                کنار خودرو
                <small>تحویل کنار ماشین</small>
              </button>
              <button
                type="button"
                class="mode-chip"
                :class="{ active: checkoutForm.delivery_mode === 'delivery' }"
                @click="setDeliveryMode('delivery')"
              >
                ارسال
                <small>تحویل درب منزل</small>
              </button>
            </div>

            <section class="delivery-box pickup-car-box" v-if="checkoutForm.delivery_mode === 'pickup' && checkoutForm.pickup_method === 'car'">
              <header class="delivery-head">
                <h4>اطلاعات تحویل کنار خودرو</h4>
                <button class="ghost-btn" type="button" @click="switchToNewVehicle">ثبت خودروی جدید</button>
              </header>

              <p class="hint" v-if="savedVehicles.length">خودروی ذخیره‌شده را انتخاب کنید یا مشخصات جدید وارد کنید.</p>
              <p class="hint" v-else>برای تحویل کنار خودرو، مشخصات ماشین را وارد کنید تا سفارش‌های بعدی ذخیره بماند.</p>

              <div class="saved-addresses" v-if="savedVehicles.length">
                <label class="saved-address vehicle-option" v-for="vehicle in savedVehicles" :key="vehicle.id">
                  <input
                    type="radio"
                    name="saved-vehicle"
                    :value="vehicle.id"
                    :checked="!checkoutForm.use_new_vehicle && checkoutForm.vehicle_id === vehicle.id"
                    @change="selectSavedVehicle(vehicle.id)"
                  />
                  <div>
                    <strong>{{ vehicle.title || vehicle.plate || 'خودرو' }}</strong>
                    <p>{{ vehicle.type || 'خودرو' }} · {{ vehicle.color || 'رنگ نامشخص' }}</p>
                    <small>{{ vehicle.plate || '-' }}</small>
                  </div>
                </label>
              </div>

              <section class="new-address" v-if="checkoutForm.use_new_vehicle || !savedVehicles.length">
                <div class="coord-grid">
                  <label>
                    <span>عنوان خودرو</span>
                    <input class="input" :value="checkoutForm.vehicle_title" @input="setCheckoutField('vehicle_title', $event.target.value)" placeholder="مثلاً ماشین من" />
                  </label>
                  <label>
                    <span>نوع خودرو</span>
                    <input class="input" :value="checkoutForm.vehicle_type" @input="setCheckoutField('vehicle_type', $event.target.value)" placeholder="مثلاً پژو ۲۰۶" />
                  </label>
                </div>

                <div class="coord-grid">
                  <label>
                    <span>رنگ خودرو</span>
                    <input class="input" :value="checkoutForm.vehicle_color" @input="setCheckoutField('vehicle_color', $event.target.value)" placeholder="مثلاً سفید" />
                  </label>
                  <label>
                    <span>شماره پلاک</span>
                    <input class="input" :value="checkoutForm.vehicle_plate" @input="setCheckoutField('vehicle_plate', $event.target.value)" placeholder="مثلاً ۱۲ ب ۳۴۵ ۶۷" />
                  </label>
                </div>
              </section>

              <div class="pickup-time-grid">
                <button
                  type="button"
                  class="mode-chip"
                  :class="{ active: checkoutForm.pickup_eta_mode === 'now' }"
                  @click="setCheckoutFields({ pickup_eta_mode: 'now' })"
                >
                  الان در مسیرم
                </button>
                <button
                  type="button"
                  class="mode-chip"
                  :class="{ active: checkoutForm.pickup_eta_mode === '15min' }"
                  @click="setCheckoutFields({ pickup_eta_mode: '15min' })"
                >
                  تا ۱۵ دقیقه دیگر
                </button>
                <button
                  type="button"
                  class="mode-chip"
                  :class="{ active: checkoutForm.pickup_eta_mode === 'scheduled' }"
                  @click="setCheckoutFields({ pickup_eta_mode: 'scheduled' })"
                >
                  زمان‌بندی برای بعد
                </button>
              </div>

              <div class="coord-grid" v-if="checkoutForm.pickup_eta_mode === 'scheduled'">
                <label>
                  <span>ساعت رسیدن</span>
                  <input class="input" type="time" :value="checkoutForm.pickup_eta_time" @input="setCheckoutField('pickup_eta_time', $event.target.value)" />
                </label>
                <label>
                  <span>محل توقف</span>
                  <input class="input" :value="checkoutForm.pickup_parking_spot" @input="setCheckoutField('pickup_parking_spot', $event.target.value)" placeholder="مثلاً ورودی اصلی" />
                </label>
              </div>

              <label v-else>
                <span>محل توقف</span>
                <input class="input" :value="checkoutForm.pickup_parking_spot" @input="setCheckoutField('pickup_parking_spot', $event.target.value)" placeholder="مثلاً جلوی درب اصلی" />
              </label>

              <div class="pickup-checks">
                <label class="inline-toggle">
                  <input type="checkbox" :checked="checkoutForm.pickup_stay_in_car" @change="setCheckoutField('pickup_stay_in_car', $event.target.checked)" />
                  <span>داخل خودرو منتظر می‌مانم</span>
                </label>
                <label class="inline-toggle">
                  <input type="checkbox" :checked="checkoutForm.pickup_need_call" @change="setCheckoutField('pickup_need_call', $event.target.checked)" />
                  <span>قبل از خروج سفارش با من تماس بگیرید</span>
                </label>
              </div>

              <label>
                <span>یادداشت تحویل کنار خودرو</span>
                <textarea class="textarea" :value="checkoutForm.pickup_notes" @input="setCheckoutField('pickup_notes', $event.target.value)" placeholder="مثلاً کنار درب جنوبی منتظر می‌مانم" />
              </label>
            </section>

            <section class="delivery-box" v-if="checkoutForm.delivery_mode === 'delivery'">
              <header class="delivery-head">
                <h4>اطلاعات آدرس</h4>
                <button class="ghost-btn" type="button" @click="switchToNewAddress">ثبت آدرس جدید</button>
              </header>

              <p class="hint" v-if="savedAddresses.length">یک آدرس ذخیره شده انتخاب کنید یا آدرس جدید بسازید.</p>
              <p class="hint" v-else>آدرسی پیدا نشد. لطفا آدرس جدید ثبت کنید.</p>

              <div class="saved-addresses" v-if="savedAddresses.length">
                <label class="saved-address" v-for="addressRow in savedAddresses" :key="addressRow.id">
                  <input
                    type="radio"
                    name="saved-address"
                    :value="addressRow.id"
                    :checked="!checkoutForm.use_new_address && checkoutForm.delivery_address_id === addressRow.id"
                    @change="selectSavedAddress(addressRow.id)"
                  />
                  <div>
                    <strong>{{ addressRow.title || 'آدرس' }}</strong>
                    <p>{{ addressRow.address_line || '-' }}</p>
                    <small>{{ addressRow.phone || checkoutForm.mobile || '-' }}</small>
                  </div>
                </label>
              </div>

              <section class="new-address" v-if="checkoutForm.use_new_address || !savedAddresses.length">
                <AddressPickerMap v-model="addressPoint" :config="checkoutMapConfig" @status="mapStatus = $event" />

                <div class="coord-grid">
                  <label>
                    <span>Latitude</span>
                    <input class="input" :value="checkoutForm.address_lat" @input="setCheckoutField('address_lat', $event.target.value)" />
                  </label>
                  <label>
                    <span>Longitude</span>
                    <input class="input" :value="checkoutForm.address_lng" @input="setCheckoutField('address_lng', $event.target.value)" />
                  </label>
                </div>

                <label>
                  <span>عنوان آدرس</span>
                  <input class="input" :value="checkoutForm.address_title" @input="setCheckoutField('address_title', $event.target.value)" placeholder="مثلا: خانه" />
                </label>

                <label>
                  <span>شماره تماس تحویل گیرنده</span>
                  <input class="input" :value="checkoutForm.address_phone" @input="setCheckoutField('address_phone', $event.target.value)" />
                </label>

                <label>
                  <span>آدرس دقیق</span>
                  <textarea class="textarea" :value="checkoutForm.address_line" @input="setCheckoutField('address_line', $event.target.value)" />
                </label>

                <div class="coord-grid">
                  <label>
                    <span>پلاک</span>
                    <input class="input" :value="checkoutForm.address_plaque" @input="setCheckoutField('address_plaque', $event.target.value)" />
                  </label>
                  <label>
                    <span>واحد</span>
                    <input class="input" :value="checkoutForm.address_unit" @input="setCheckoutField('address_unit', $event.target.value)" />
                  </label>
                </div>

                <label>
                  <span>طبقه</span>
                  <input class="input" :value="checkoutForm.address_floor" @input="setCheckoutField('address_floor', $event.target.value)" />
                </label>

                <p class="hint" v-if="mapStatus === 'missing_api_key' || mapStatus === 'error'">
                  در صورت عدم دسترسی به نقشه، مختصات بالا را دستی وارد کنید.
                </p>
              </section>
            </section>

            <label>
              <span>کد تخفیف</span>
              <div class="coupon-row">
                <input class="input" v-model="couponCode" placeholder="مثلاً WELCOME" />
                <button class="ghost-btn" type="button" :disabled="couponLoading || !couponCode.trim()" @click="applyCoupon">
                  {{ couponLoading ? '...' : 'اعمال' }}
                </button>
              </div>
              <small class="hint" v-if="couponResult">{{ couponResult.message || 'کد تخفیف اعمال شد.' }}</small>
              <small class="hint" v-if="couponError" style="color:#b84f4f">{{ couponError }}</small>
            </label>

            <label>
              <span>توضیحات سفارش</span>
              <textarea class="textarea" :value="checkoutForm.note" @input="setCheckoutField('note', $event.target.value)" />
            </label>

            <label class="inline-toggle">
              <input
                type="checkbox"
                :checked="checkoutForm.include_service_items"
                @change="setCheckoutField('include_service_items', $event.target.checked)"
              />
              <span>اقلام همراه سفارش (مثل قاشق و چنگال) اضافه شود</span>
            </label>
          </div>

          <button class="submit-btn" :disabled="submitting" @click="submitOrder">{{ submitting ? 'در حال ثبت...' : 'ثبت سفارش' }}</button>
        </section>
      </div>
    </teleport>
  </LiquidGlassBackdrop>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import CartLineEditor from '@/components/CartLineEditor.vue'
import CartToppingSheet from '@/components/CartToppingSheet.vue'
import AddressPickerMap from '@/components/checkout/AddressPickerMap.vue'
import {
  cartState,
  cartSubtotal,
  clearCart,
  getLineById,
  removeLine,
  saveCheckoutDraft,
  saveLastOrder,
  setLineQty,
  upsertLine,
} from '@/stores/cartStore'
import {
  getCustomerCheckoutProfile,
  getItemDetail,
  getMenuBoot,
  placeOrder,
  saveCustomerDeliveryAddress,
  saveCustomerVehicle,
  validateCoupon,
} from '@/utils/api'
import { formatMoney, normalizeMobile } from '@/utils/format'
import { estimateLine, sanitizeCustomization } from '@/utils/itemConfig'

const currency = ref('TOMAN')
const submitting = ref(false)
const error = ref('')
const showCheckout = ref(false)
const customerLookupLoading = ref(false)
const customerLookupError = ref('')
const mapStatus = ref('')
const savedAddresses = ref([])
const savedVehicles = ref([])
const couponCode = ref('')
const couponLoading = ref(false)
const couponError = ref('')
const couponResult = ref(null)
let mobileLookupTimer = null

const checkoutMapConfig = ref({
  provider: 'neshan',
  api_key: '',
  script_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.js',
  style_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.css',
  default_lat: 35.6997,
  default_lng: 51.3381,
  default_zoom: 13,
})

const editorOpen = ref(false)
const editorLoading = ref(false)
const activeLineId = ref('')
const activeIngredients = ref([])
const activeModifierGroups = ref([])
const activeCustomization = ref({
  ingredient_adjustments: [],
  selected_modifiers: [],
})

const checkoutForm = ref({
  customer_name: cartState.checkoutDraft.customer_name || '',
  mobile: cartState.checkoutDraft.mobile || '',
  delivery_mode: cartState.checkoutDraft.delivery_mode || (cartState.checkoutDraft.order_type === 'delivery' ? 'delivery' : 'pickup'),
  pickup_method: cartState.checkoutDraft.pickup_method || 'counter',
  order_type: cartState.checkoutDraft.order_type || 'takeaway',
  delivery_address_id: cartState.checkoutDraft.delivery_address_id || '',
  use_new_address: cartState.checkoutDraft.use_new_address !== false,
  address_title: cartState.checkoutDraft.address_title || '',
  address_phone: cartState.checkoutDraft.address_phone || cartState.checkoutDraft.mobile || '',
  address_line: cartState.checkoutDraft.address_line || cartState.checkoutDraft.address || '',
  address_plaque: cartState.checkoutDraft.address_plaque || '',
  address_unit: cartState.checkoutDraft.address_unit || '',
  address_floor: cartState.checkoutDraft.address_floor || '',
  address_lat: cartState.checkoutDraft.address_lat || '',
  address_lng: cartState.checkoutDraft.address_lng || '',
  vehicle_id: cartState.checkoutDraft.vehicle_id || '',
  use_new_vehicle: cartState.checkoutDraft.use_new_vehicle !== false,
  vehicle_title: cartState.checkoutDraft.vehicle_title || '',
  vehicle_type: cartState.checkoutDraft.vehicle_type || '',
  vehicle_color: cartState.checkoutDraft.vehicle_color || '',
  vehicle_plate: cartState.checkoutDraft.vehicle_plate || '',
  pickup_eta_mode: cartState.checkoutDraft.pickup_eta_mode || 'now',
  pickup_eta_time: cartState.checkoutDraft.pickup_eta_time || '',
  pickup_parking_spot: cartState.checkoutDraft.pickup_parking_spot || '',
  pickup_stay_in_car: cartState.checkoutDraft.pickup_stay_in_car !== false,
  pickup_need_call: cartState.checkoutDraft.pickup_need_call === true,
  pickup_notes: cartState.checkoutDraft.pickup_notes || '',
  note: cartState.checkoutDraft.note || '',
  include_service_items: cartState.checkoutDraft.include_service_items !== false,
})

const subtotal = computed(() => cartSubtotal())
const taxAmount = computed(() => Math.round(subtotal.value * 0.04))
const shippingAmount = computed(() => 0)
const discountAmount = computed(() => Number(couponResult.value?.discount_amount || 0))
const totalAmount = computed(() => Math.max(subtotal.value + taxAmount.value + shippingAmount.value - discountAmount.value, 0))
const totalQty = computed(() => cartState.lines.reduce((sum, line) => sum + Number(line.qty || 0), 0))
const canLookupProfile = computed(() => normalizeMobile(checkoutForm.value.mobile || '').length >= 10)

const activeLine = computed(() => getLineById(activeLineId.value) || null)
const selectedSavedAddress = computed(() => {
  return savedAddresses.value.find((row) => row.id === checkoutForm.value.delivery_address_id) || null
})

const addressPoint = computed({
  get() {
    return {
      lat: checkoutForm.value.address_lat,
      lng: checkoutForm.value.address_lng,
    }
  },
  set(value) {
    setCheckoutFields({
      address_lat: value?.lat ?? '',
      address_lng: value?.lng ?? '',
    })
  },
})

watch(
  checkoutForm,
  (value) => {
    saveCheckoutDraft(value)
  },
  { deep: true },
)

watch(
  () => showCheckout.value,
  (open) => {
    if (open && canLookupProfile.value) {
      loadCustomerProfile()
    }
  },
)

watch(
  () => normalizeMobile(checkoutForm.value.mobile || ''),
  (mobile) => {
    setCheckoutField('address_phone', checkoutForm.value.address_phone || mobile)

    if (!showCheckout.value) {
      return
    }
    if (mobile.length < 10) {
      savedAddresses.value = []
      savedVehicles.value = []
      setCheckoutFields({ delivery_address_id: '', use_new_address: true, vehicle_id: '', use_new_vehicle: true })
      return
    }

    window.clearTimeout(mobileLookupTimer)
    mobileLookupTimer = window.setTimeout(() => {
      loadCustomerProfile()
    }, 420)
  },
)

function setCheckoutFields(payload) {
  checkoutForm.value = {
    ...checkoutForm.value,
    ...payload,
  }
}

function setCheckoutField(field, value) {
  setCheckoutFields({ [field]: value })
}

function setDeliveryMode(mode) {
  const isDelivery = mode === 'delivery'
  const isCarPickup = mode === 'pickup_car'
  setCheckoutFields({
    delivery_mode: isDelivery ? 'delivery' : 'pickup',
    pickup_method: isCarPickup ? 'car' : 'counter',
    order_type: isDelivery ? 'delivery' : 'takeaway',
    delivery_address_id: isDelivery ? checkoutForm.value.delivery_address_id : '',
    use_new_address: isDelivery ? checkoutForm.value.use_new_address : true,
  })
}

function selectSavedAddress(addressId) {
  const selected = savedAddresses.value.find((row) => row.id === addressId)
  if (!selected) {
    return
  }

  setCheckoutFields({
    delivery_address_id: selected.id,
    use_new_address: false,
    address_title: selected.title || checkoutForm.value.address_title,
    address_phone: selected.phone || checkoutForm.value.address_phone || checkoutForm.value.mobile,
    address_line: selected.address_line || checkoutForm.value.address_line,
    address_plaque: selected.plaque || '',
    address_unit: selected.unit || '',
    address_floor: selected.floor || '',
    address_lat: selected.lat ?? '',
    address_lng: selected.lng ?? '',
  })
}

function switchToNewAddress() {
  setCheckoutFields({
    use_new_address: true,
    delivery_address_id: '',
  })
}

async function saveVehicleToCustomerProfile() {
  const form = checkoutForm.value
  const mobile = normalizeMobile(form.mobile || '')
  if (!mobile || form.pickup_method !== 'car') return null

  const selected = !form.use_new_vehicle ? savedVehicles.value.find((row) => row.id === form.vehicle_id) : null
  const vehicleInfo = {
    id: selected?.id || form.vehicle_id || '',
    title: selected?.title || form.vehicle_title || '',
    type: selected?.type || form.vehicle_type || '',
    color: selected?.color || form.vehicle_color || '',
    plate: selected?.plate || form.vehicle_plate || '',
    is_primary: savedVehicles.value.length ? 0 : 1,
  }

  const saved = await saveCustomerVehicle({
    customer_info: {
      name: form.customer_name,
      mobile,
    },
    vehicle_info: vehicleInfo,
  })

  const vehicle = saved.vehicle || {}
  savedVehicles.value = Array.isArray(saved.vehicles) ? saved.vehicles : savedVehicles.value
  if (vehicle.id) {
    setCheckoutFields({
      vehicle_id: vehicle.id,
      use_new_vehicle: false,
      vehicle_title: vehicle.title || form.vehicle_title,
      vehicle_type: vehicle.type || form.vehicle_type,
      vehicle_color: vehicle.color || form.vehicle_color,
      vehicle_plate: vehicle.plate || form.vehicle_plate,
    })
  }
  return vehicle
}

function selectSavedVehicle(vehicleId) {
  const selected = savedVehicles.value.find((row) => row.id === vehicleId)
  if (!selected) return
  setCheckoutFields({
    vehicle_id: selected.id,
    use_new_vehicle: false,
    vehicle_title: selected.title || '',
    vehicle_type: selected.type || '',
    vehicle_color: selected.color || '',
    vehicle_plate: selected.plate || '',
  })
}

function switchToNewVehicle() {
  setCheckoutFields({
    vehicle_id: '',
    use_new_vehicle: true,
    vehicle_title: '',
    vehicle_type: '',
    vehicle_color: '',
    vehicle_plate: '',
  })
}

function openCheckout() {
  if (!cartState.lines.length) return
  window.location.href = '/checkout'
}

function cartItemsPayload() {
  return cartState.lines.map((line) => ({
    item_slug: line.item_slug,
    qty: line.qty,
    customization: line.customization,
    branch: line.branch || '',
  }))
}

async function applyCoupon() {
  if (!couponCode.value.trim()) return
  couponLoading.value = true
  couponError.value = ''
  couponResult.value = null
  try {
    couponResult.value = await validateCoupon({
      coupon_code: couponCode.value.trim(),
      items: cartItemsPayload(),
      mobile: normalizeMobile(checkoutForm.value.mobile || ''),
      subtotal: subtotal.value,
    })
  } catch (err) {
    couponError.value = err?.message || 'کد تخفیف معتبر نیست.'
  } finally {
    couponLoading.value = false
  }
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
  if (activeLineId.value === lineId) {
    closeEditor()
  }
  removeLine(lineId)
}

function closeEditor() {
  editorOpen.value = false
  editorLoading.value = false
  activeLineId.value = ''
  activeIngredients.value = []
  activeModifierGroups.value = []
  activeCustomization.value = {
    ingredient_adjustments: [],
    selected_modifiers: [],
  }
}

async function openCustomization(line) {
  if (!line?.id) {
    return
  }

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
  } catch (err) {
    // keep fallback catalogs when detail fetch fails
  } finally {
    editorLoading.value = false
  }
}

function applyCustomization(nextCustomization) {
  const line = activeLine.value
  if (!line) {
    return
  }

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

async function loadCustomerProfile() {
  if (!canLookupProfile.value) {
    return
  }

  customerLookupLoading.value = true
  customerLookupError.value = ''

  try {
    const payload = await getCustomerCheckoutProfile({
      mobile: normalizeMobile(checkoutForm.value.mobile),
      customer_name: checkoutForm.value.customer_name,
    })
    const addresses = Array.isArray(payload.addresses) ? payload.addresses : []
    const vehicles = Array.isArray(payload.vehicles) ? payload.vehicles : []
    savedAddresses.value = addresses
    savedVehicles.value = vehicles

    if (!checkoutForm.value.customer_name && payload.customer?.name) {
      setCheckoutField('customer_name', payload.customer.name)
    }

    if (!addresses.length) {
      setCheckoutFields({
        delivery_address_id: '',
        use_new_address: true,
      })
      return
    }

    const hasSelected = addresses.some((row) => row.id === checkoutForm.value.delivery_address_id)
    if (hasSelected && checkoutForm.value.use_new_address === false) {
      return
    }

    if (checkoutForm.value.use_new_address !== true && addresses[0]) {
      selectSavedAddress(addresses[0].id)
    }
  } catch (err) {
    customerLookupError.value = err.message || 'دریافت آدرس های مشتری ناموفق بود.'
  } finally {
    customerLookupLoading.value = false
  }
}

function parseCoordinate(value, min, max) {
  const number = Number(value)
  if (!Number.isFinite(number)) {
    return null
  }
  if (number < min || number > max) {
    return null
  }
  return Number(number.toFixed(6))
}

function validateCheckout() {
  const form = checkoutForm.value

  if (!form.customer_name.trim()) {
    return 'نام مشتری الزامی است.'
  }

  if (normalizeMobile(form.mobile).length < 10) {
    return 'موبایل معتبر وارد کنید.'
  }

  if (form.delivery_mode === 'pickup' && form.pickup_method === 'car') {
    if (form.use_new_vehicle || !form.vehicle_id) {
      if (!form.vehicle_type.trim()) {
        return 'نوع خودرو برای تحویل کنار خودرو الزامی است.'
      }
      if (!form.vehicle_color.trim()) {
        return 'رنگ خودرو برای تحویل کنار خودرو الزامی است.'
      }
      if (!form.vehicle_plate.trim()) {
        return 'شماره پلاک برای تحویل کنار خودرو الزامی است.'
      }
    }
    if (form.pickup_eta_mode === 'scheduled' && !form.pickup_eta_time) {
      return 'ساعت رسیدن برای پیکاپ زمان‌بندی‌شده الزامی است.'
    }
  }

  if (form.delivery_mode === 'delivery') {
    if (!form.use_new_address && !form.delivery_address_id) {
      return 'برای ارسال، یک آدرس ذخیره شده انتخاب کنید یا آدرس جدید ثبت کنید.'
    }

    if (form.use_new_address) {
      if (!form.address_title.trim()) {
        return 'عنوان آدرس الزامی است.'
      }
      if (normalizeMobile(form.address_phone).length < 10) {
        return 'شماره تماس تحویل گیرنده معتبر نیست.'
      }
      if (!form.address_line.trim()) {
        return 'آدرس دقیق برای ارسال الزامی است.'
      }
      if (!form.address_plaque.trim()) {
        return 'پلاک برای ارسال الزامی است.'
      }

      const lat = parseCoordinate(form.address_lat, -90, 90)
      const lng = parseCoordinate(form.address_lng, -180, 180)
      if (lat == null || lng == null) {
        return 'مختصات تحویل معتبر نیست. لطفا روی نقشه انتخاب کنید یا دستی وارد کنید.'
      }
    }
  }

  if (!cartState.lines.length) {
    return 'سبد سفارش خالی است.'
  }

  return ''
}

function pickupEtaText(form) {
  if (form.pickup_eta_mode === 'scheduled') {
    return form.pickup_eta_time ? `ساعت ${form.pickup_eta_time}` : 'زمان‌بندی‌شده'
  }
  if (form.pickup_eta_mode === '15min') {
    return 'تا ۱۵ دقیقه دیگر'
  }
  return 'الان در مسیرم'
}

function selectedVehicleSnapshot() {
  const form = checkoutForm.value
  const selected = !form.use_new_vehicle ? savedVehicles.value.find((row) => row.id === form.vehicle_id) : null
  return {
    id: selected?.id || form.vehicle_id || '',
    title: selected?.title || form.vehicle_title || '',
    type: selected?.type || form.vehicle_type || '',
    color: selected?.color || form.vehicle_color || '',
    plate: selected?.plate || form.vehicle_plate || '',
  }
}

function composeOrderNote(baseNote = '') {
  const form = checkoutForm.value
  const parts = []
  if (baseNote.trim()) {
    parts.push(baseNote.trim())
  }

  if (form.delivery_mode === 'pickup' && form.pickup_method === 'car') {
    const vehicle = selectedVehicleSnapshot()
    parts.push(
      [
        'تحویل کنار خودرو',
        `خودرو: ${vehicle.type || '-'} / ${vehicle.color || '-'} / پلاک ${vehicle.plate || '-'}`,
        `زمان رسیدن: ${pickupEtaText(form)}`,
        `محل توقف: ${form.pickup_parking_spot || '-'}`,
        form.pickup_stay_in_car ? 'مشتری داخل خودرو منتظر می‌ماند.' : '',
        form.pickup_need_call ? 'قبل از خروج سفارش تماس گرفته شود.' : '',
        form.pickup_notes ? `یادداشت خودرو: ${form.pickup_notes}` : '',
      ]
        .filter(Boolean)
        .join('\n'),
    )
  }

  return parts.join('\n\n')
}

function selectedAddressSnapshot() {
  const form = checkoutForm.value
  if (form.use_new_address) {
    return {
      title: form.address_title,
      phone: normalizeMobile(form.address_phone),
      address_line: form.address_line,
      plaque: form.address_plaque,
      unit: form.address_unit,
      floor: form.address_floor,
      lat: parseCoordinate(form.address_lat, -90, 90),
      lng: parseCoordinate(form.address_lng, -180, 180),
    }
  }

  const selected = selectedSavedAddress.value
  if (!selected) {
    return {
      title: '',
      phone: normalizeMobile(form.mobile),
      address_line: '',
      plaque: '',
      unit: '',
      floor: '',
      lat: null,
      lng: null,
    }
  }

  return {
    title: selected.title || '',
    phone: normalizeMobile(selected.phone || form.mobile),
    address_line: selected.address_line || '',
    plaque: selected.plaque || '',
    unit: selected.unit || '',
    floor: selected.floor || '',
    lat: parseCoordinate(selected.lat, -90, 90),
    lng: parseCoordinate(selected.lng, -180, 180),
  }
}

async function submitOrder() {
  const formError = validateCheckout()
  if (formError) {
    error.value = formError
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const form = checkoutForm.value
    const mobile = normalizeMobile(form.mobile)
    let deliveryAddressId = form.delivery_address_id
    let deliverySnapshot = selectedAddressSnapshot()

    if (form.delivery_mode === 'delivery' && form.use_new_address) {
      const saved = await saveCustomerDeliveryAddress({
        customer_info: {
          name: form.customer_name,
          mobile,
        },
        address_info: {
          title: form.address_title,
          phone: normalizeMobile(form.address_phone),
          address_line: form.address_line,
          plaque: form.address_plaque,
          unit: form.address_unit,
          floor: form.address_floor,
          lat: parseCoordinate(form.address_lat, -90, 90),
          lng: parseCoordinate(form.address_lng, -180, 180),
          is_primary: savedAddresses.value.length ? 0 : 1,
        },
      })

      const addressRow = saved.address || {}
      deliveryAddressId = addressRow.id || ''
      deliverySnapshot = {
        title: addressRow.title || form.address_title,
        phone: normalizeMobile(addressRow.phone || form.address_phone),
        address_line: addressRow.address_line || form.address_line,
        plaque: addressRow.plaque || form.address_plaque,
        unit: addressRow.unit || form.address_unit,
        floor: addressRow.floor || form.address_floor,
        lat: parseCoordinate(addressRow.lat ?? form.address_lat, -90, 90),
        lng: parseCoordinate(addressRow.lng ?? form.address_lng, -180, 180),
      }

      savedAddresses.value = Array.isArray(saved.addresses) ? saved.addresses : savedAddresses.value
      setCheckoutFields({
        delivery_address_id: deliveryAddressId,
        use_new_address: false,
      })
    }

    let pickupVehicle = selectedVehicleSnapshot()
    if (form.delivery_mode === 'pickup' && form.pickup_method === 'car') {
      pickupVehicle = await saveVehicleToCustomerProfile()
    }

    const response = await placeOrder({
      customer_info: {
        name: form.customer_name,
        mobile,
      },
      delivery_mode: form.delivery_mode,
      order_type: form.delivery_mode === 'delivery' ? 'delivery' : 'takeaway',
      delivery_address_id: form.delivery_mode === 'delivery' ? deliveryAddressId : '',
      delivery_address_snapshot: form.delivery_mode === 'delivery' ? deliverySnapshot : {},
      pickup_method: form.delivery_mode === 'pickup' ? form.pickup_method : '',
      pickup_vehicle_id: form.delivery_mode === 'pickup' && form.pickup_method === 'car' ? pickupVehicle?.id || form.vehicle_id : '',
      pickup_vehicle_snapshot: form.delivery_mode === 'pickup' && form.pickup_method === 'car' ? pickupVehicle || selectedVehicleSnapshot() : {},
      address: form.delivery_mode === 'delivery' ? deliverySnapshot.address_line : '',
      note: composeOrderNote(form.note),
      include_service_items: form.include_service_items ? 1 : 0,
      coupon_code: couponResult.value?.code || couponCode.value.trim() || '',
      items: cartItemsPayload(),
    })

    saveLastOrder({ order_code: response.order_code, mobile })
    clearCart()
    showCheckout.value = false
    closeEditor()

    window.location.href = `/order-success/${response.order_code}?mobile=${encodeURIComponent(mobile)}`
  } catch (err) {
    error.value = err.message || 'ثبت سفارش با خطا مواجه شد.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const boot = await getMenuBoot('')
    currency.value = 'TOMAN'
    if (boot.checkout_map && typeof boot.checkout_map === 'object') {
      checkoutMapConfig.value = {
        ...checkoutMapConfig.value,
        ...boot.checkout_map,
      }
    }
  } catch (err) {
    currency.value = 'TOMAN'
  }
})

onUnmounted(() => {
  window.clearTimeout(mobileLookupTimer)
})
</script>

<style scoped>
.cart-shell {
  width: min(580px, calc(100% - 1rem));
  margin: 0.7rem auto 1.6rem;
}

.cart-frame {
  border-radius: 36px;
  padding: 0.75rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.9);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  box-shadow: 0 24px 66px rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  display: grid;
  gap: 0.7rem;
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

.top-row p {
  margin: 0;
  color: var(--accent-gold);
  font-size: 1.05rem;
  flex: 1;
  text-align: center;
}

.icon-btn {
  width: 34px;
  height: 34px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.36);
  background: rgb(var(--palette-eggshell-rgb) / 0.86);
  color: var(--accent-gold);
  font-size: 1.1rem;
  line-height: 1;
  text-decoration: none;
}

.icon-btn:disabled {
  opacity: 0.45;
}

.top-spacer {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
}

h1 {
  margin: 0;
  font-size: 2rem;
}

h1 span {
  color: var(--accent-gold);
}

.line-list {
  display: grid;
  gap: 0.6rem;
}

.empty-box {
  border-radius: 20px;
  background: rgb(var(--palette-eggshell-rgb) / 0.74);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  padding: 1rem;
  text-align: center;
}

.go-menu {
  margin-top: 0.5rem;
  display: inline-flex;
  border-radius: 999px;
  background: var(--accent-green);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.44);
  color: #fff;
  padding: 0.5rem 0.9rem;
}

.grabber {
  width: 66px;
  height: 8px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.4);
  margin: 0 auto;
}

.summary-panel {
  margin-top: 0.15rem;
  border-radius: 32px;
  padding: 1rem 0.92rem;
  background: var(--accent-green80);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  color: #fff;
  display: grid;
  gap: 0.52rem;
}

.sum-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 1rem;
}

.sum-row span {
  color: rgb(var(--palette-eggshell-rgb) / 0.76);
}

.sum-row.total {
  margin-top: 0.32rem;
  font-size: 1.12rem;
}

.checkout-btn {
  margin-top: 0.55rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.42);
  background: rgb(var(--palette-deep-saffron-rgb) / 0.2);
  color: #fff;
  padding: 0.84rem;
  font-family: inherit;
  font-size: 0.96rem;
}

.checkout-btn:disabled {
  opacity: 0.45;
}

.error {
  margin: 0;
  color: #ffadad;
  font-size: 0.84rem;
}

.checkout-overlay {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0.5rem;
  background: rgb(15 23 42 / 0.28);
}

.checkout-panel {
  width: min(560px, 100%);
  max-height: calc(100vh - 1.2rem);
  overflow-y: auto;
  border-radius: 30px;
  background: rgb(var(--palette-eggshell-rgb) / 0.98);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  padding: 0.8rem;
  display: grid;
  gap: 0.68rem;
  box-sizing: border-box;
}

.checkout-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkout-head h3 {
  margin: 0;
  font-size: 1.25rem;
}

.fields {
  display: grid;
  gap: 0.6rem;
}

label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.86rem;
}

.inline-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.inline-toggle input {
  width: 1rem;
  height: 1rem;
}

.profile-actions {
  display: grid;
  gap: 0.35rem;
}

.delivery-mode-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
}

.delivery-mode-grid--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mode-chip {
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.35);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.62);
  color: var(--text-primary);
  padding: 0.58rem;
  font-family: inherit;
  display: grid;
  gap: 0.18rem;
  align-content: center;
  min-height: 48px;
}

.mode-chip small {
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 500;
}

.mode-chip.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
  color: var(--accent-green);
  box-shadow: inset 0 0 0 1px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.mode-chip.active small {
  color: var(--accent-green);
}

.delivery-box {
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.24);
  border-radius: 16px;
  padding: 0.6rem;
  display: grid;
  gap: 0.6rem;
}

.pickup-car-box {
  background: rgb(var(--palette-eggshell-rgb) / 0.56);
}

.delivery-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.delivery-head h4 {
  margin: 0;
  font-size: 0.95rem;
}

.saved-addresses {
  display: grid;
  gap: 0.45rem;
}

.saved-address {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: start;
  gap: 0.5rem;
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
  padding: 0.45rem;
  min-width: 0;
}

.saved-address p,
.saved-address small {
  margin: 0.2rem 0 0;
  overflow-wrap: break-word;
  word-break: break-word;
}

.vehicle-option strong {
  color: var(--accent-green);
}

.pickup-time-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.pickup-checks {
  display: grid;
  gap: 0.42rem;
  padding: 0.5rem;
  border-radius: 14px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.035);
}

.new-address {
  display: grid;
  gap: 0.55rem;
}

.coord-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.submit-btn {
  border: 0;
  border-radius: 999px;
  background: var(--accent-green);
  color: #fff;
  padding: 0.74rem;
  font-family: inherit;
}

@media (min-width: 950px) {
  .cart-shell {
    width: min(980px, calc(100% - 2rem));
  }

  .cart-frame {
    grid-template-columns: 1fr 0.74fr;
    align-items: start;
  }

  .top-row,
  h1,
  .line-list,
  .grabber {
    grid-column: 1;
  }

  .summary-panel {
    grid-column: 2;
    grid-row: 2 / span 3;
    position: sticky;
    top: 1rem;
  }
}

@media (max-width: 560px) {
  .delivery-mode-grid,
  .delivery-mode-grid--three,
  .pickup-time-grid,
  .coord-grid {
    grid-template-columns: 1fr;
  }

  .checkout-overlay {
    align-items: flex-end;
    justify-content: center;
    padding: 0;
  }

  .checkout-panel {
    width: 100%;
    max-height: calc(100vh - 1.2rem - env(safe-area-inset-bottom, 0px));
    border-radius: 20px 20px 0 0;
    padding: 0.6rem 0.6rem calc(0.6rem + env(safe-area-inset-bottom, 0px));
    box-sizing: border-box;
    overflow-x: hidden;
  }

  .checkout-head h3 {
    font-size: 1.1rem;
  }

  .fields {
    gap: 0.5rem;
  }

  .delivery-box {
    padding: 0.5rem;
    gap: 0.5rem;
  }

  .saved-address {
    grid-template-columns: auto 1fr;
    gap: 0.35rem;
    padding: 0.35rem;
    min-width: 0;
  }

  .mode-chip {
    padding: 0.45rem;
    font-size: 0.82rem;
  }

  .submit-btn {
    padding: 0.64rem;
    font-size: 0.9rem;
  }

  .input,
  .textarea {
    font-size: 0.86rem;
    padding: 0.45rem 0.55rem;
  }

  .cart-shell {
    width: 100%;
    margin: 0.3rem auto 1rem;
  }

  .cart-frame {
    border-radius: 24px;
    padding: 0.5rem;
  }

  h1 {
    font-size: 1.5rem;
  }

  .summary-panel {
    padding: 0.75rem 0.6rem;
    border-radius: 22px;
  }

  .sum-row {
    font-size: 0.9rem;
  }

  .checkout-btn {
    padding: 0.7rem;
    font-size: 0.88rem;
  }
}
</style>
