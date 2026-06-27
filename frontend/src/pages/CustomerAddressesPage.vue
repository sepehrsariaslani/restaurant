<template>
  <div class="customer-page addresses-page" dir="rtl">
    <section class="customer-page__hero">
      <div class="customer-page__topbar">
        <button class="customer-page__back" @click="goBack" aria-label="بازگشت">
          <ChevronRight :size="20" />
        </button>
        <div class="customer-page__titles">
          <p class="customer-page__eyebrow"><MapPin :size="14" /> مدیریت آدرس‌ها</p>
          <h1 class="customer-page__title">آدرس‌های من</h1>
          <p class="customer-page__subtitle">آدرس‌های تحویل خود را برای سفارش‌های سریع‌تر نگه دارید.</p>
        </div>
        <button class="customer-page__action" @click="openAddForm">
          <Plus :size="16" />
          <span>جدید</span>
        </button>
      </div>
    </section>

    <div class="customer-page__body">
      <p v-if="error" class="customer-section__hint customer-danger-text">{{ error }}</p>

      <div v-if="addresses.length === 0" class="customer-glass-card customer-empty">
        <div class="customer-icon-badge"><MapPinned :size="28" /></div>
        <h3>آدرسی ثبت نشده</h3>
        <p>برای تحویل سریع‌تر، آدرس خانه یا محل کارتان را ذخیره کنید.</p>
        <button class="primary-btn" @click="openAddForm">افزودن آدرس جدید</button>
      </div>

      <div v-else class="customer-stack">
        <article
          v-for="addr in addresses"
          :key="addr.id"
          class="address-card customer-glass-card"
          :class="{ 'is-selected': selectedId === addr.id }"
          @click="selectedId = addr.id"
        >
          <div class="address-card__radio">
            <span class="address-card__dot" :class="{ 'is-active': selectedId === addr.id }"></span>
          </div>

          <div class="address-card__body">
            <div class="address-card__head">
              <div>
                <strong>{{ addr.label }}</strong>
                <p>{{ addr.address }}</p>
              </div>
              <span class="customer-kicker">{{ addr.type }}</span>
            </div>
            <small v-if="addr.detail">{{ addr.detail }}</small>
          </div>

          <div class="address-card__actions">
            <button class="icon-action" @click.stop="editAddress(addr)" aria-label="ویرایش آدرس">
              <Pencil :size="16" />
            </button>
            <button class="icon-action icon-action--danger" @click.stop="deleteAddress(addr.id)" aria-label="حذف آدرس">
              <Trash2 :size="16" />
            </button>
          </div>
        </article>

        <button class="add-address-row customer-glass-card" @click="openAddForm">
          <Plus :size="18" />
          افزودن آدرس جدید
        </button>
      </div>
    </div>

    <Teleport to="body">
      <div class="modal-overlay" v-if="showForm" @click.self="closeForm">
        <div class="modal-sheet customer-glass-card" dir="rtl">
          <div class="modal-sheet__head">
            <div>
              <p class="customer-page__eyebrow modal-eyebrow"><MapPin :size="14" /> فرم آدرس</p>
              <h3 class="modal-title">{{ editingId ? 'ویرایش آدرس' : 'آدرس جدید' }}</h3>
            </div>
            <button class="icon-action" @click="closeForm" aria-label="بستن">
              <X :size="16" />
            </button>
          </div>

          <div class="customer-field">
            <label>نوع آدرس</label>
            <div class="customer-chip-row">
              <button
                v-for="t in types"
                :key="t"
                class="customer-chip"
                :class="{ 'is-active': newAddr.type === t }"
                @click="newAddr.type = t"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <div class="customer-field">
            <label>نام یا عنوان</label>
            <input class="customer-input" v-model="newAddr.label" placeholder="مثلاً: خانه، محل کار" />
          </div>

          <div class="customer-field">
            <label>آدرس کامل</label>
            <textarea class="customer-textarea" v-model="newAddr.address" placeholder="شهر، خیابان، کوچه..." rows="3"></textarea>
          </div>

          <div class="customer-field">
            <label>واحد / طبقه / جزئیات بیشتر</label>
            <input class="customer-input" v-model="newAddr.detail" placeholder="مثلاً: واحد ۳" />
          </div>

          <div class="customer-field location-field">
            <div class="location-field__head">
              <div>
                <label>لوکیشن روی نقشه</label>
                <p>برای ارسال دقیق، موقعیت را روی نقشه انتخاب کنید یا از GPS دستگاه استفاده کنید.</p>
              </div>
              <button class="customer-page__ghost-action locate-btn" type="button" :disabled="locating" @click="useCurrentLocation">
                <Crosshair :size="16" />
                <span>{{ locating ? 'در حال دریافت...' : 'موقعیت من' }}</span>
              </button>
            </div>

            <AddressPickerMap
              v-if="showForm"
              v-model="addressLocation"
              :config="mapConfig"
              @status="mapStatus = $event"
            />

            <details class="location-coordinates">
              <summary>تنظیمات پیشرفته موقعیت</summary>
              <div class="location-coordinates__grid">
                <label>
                  <span>عرض جغرافیایی</span>
                  <input class="customer-input" v-model="newAddr.lat" inputmode="decimal" dir="ltr" placeholder="35.699700" />
                </label>
                <label>
                  <span>طول جغرافیایی</span>
                  <input class="customer-input" v-model="newAddr.lng" inputmode="decimal" dir="ltr" placeholder="51.338100" />
                </label>
              </div>
            </details>
            <p v-if="locationError" class="location-error">{{ locationError }}</p>
            <p v-else-if="hasLocation" class="location-ok">
              <MapPinCheck :size="15" />
              لوکیشن آدرس ثبت شده و قابل استفاده روی نقشه است.
            </p>
            <p v-else class="location-hint">برای ذخیره آدرس، انتخاب لوکیشن الزامی است.</p>
          </div>

          <div class="modal-actions">
            <button class="customer-page__ghost-action modal-cancel" @click="closeForm">انصراف</button>
            <button class="primary-btn modal-save" @click="saveAddress" :disabled="!canSaveAddress">ذخیره آدرس</button>
          </div>
        </div>
      </div>
    </Teleport>

    <div class="customer-bottom-cta" v-if="addresses.length > 0">
      <button class="customer-primary-cta" @click="confirmSelection">
        <Check :size="18" />
        تأیید این آدرس
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, ChevronRight, Crosshair, MapPin, MapPinCheck, MapPinned, Pencil, Plus, Trash2, X } from 'lucide-vue-next'
import AddressPickerMap from '@/components/checkout/AddressPickerMap.vue'
import { getCustomerCheckoutProfile, getMenuBoot, saveCustomerDeliveryAddress } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const STORAGE_KEY = 'customer_addresses_v1'
function loadAddresses() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] } }
function saveAddresses(list) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {} }
function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return {
      mobile: auth.mobile || localStorage.getItem('customer_phone') || '',
      name: auth.customer_name || localStorage.getItem('customer_name') || '',
    }
  } catch { return { mobile: '', name: '' } }
}
function normalizeAddress(row) {
  const address = row.address || row.address_line1 || row.address_line || ''
  const lat = firstNonEmpty(row.lat, row.latitude)
  const lng = firstNonEmpty(row.lng, row.longitude)
  return {
    ...row,
    id: row.id || row.name || Date.now(),
    label: row.label || row.address_title || row.title || row.type || 'آدرس',
    type: row.type || row.address_type || 'سایر',
    address,
    detail: row.detail || row.address_line2 || '',
    lat,
    lng,
  }
}

function firstNonEmpty(...values) {
  const value = values.find((item) => item !== undefined && item !== null && String(item).trim() !== '')
  return value === undefined ? '' : value
}

function isValidCoordinate(value, min, max) {
  const number = Number(value)
  return Number.isFinite(number) && number >= min && number <= max
}

function normalizeCoordinate(value) {
  const number = Number(value)
  return Number.isFinite(number) ? Number(number.toFixed(6)) : ''
}

const addresses = ref(loadAddresses().map(normalizeAddress))
const selectedId = ref(addresses.value[0]?.id || null)
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref(null)
const locating = ref(false)
const locationError = ref('')
const mapStatus = ref('')
const mapConfig = ref({
  provider: 'neshan',
  api_key: '',
  script_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.js',
  style_url: 'https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.css',
  default_lat: 35.6997,
  default_lng: 51.3381,
  default_zoom: 13,
})
const types = ['خانه', 'محل کار', 'سایر']

const newAddr = ref({ label: 'خانه', type: 'خانه', address: '', detail: '', lat: '', lng: '' })

const hasLocation = computed(() => (
  isValidCoordinate(newAddr.value.lat, -90, 90) && isValidCoordinate(newAddr.value.lng, -180, 180)
))
const canSaveAddress = computed(() => newAddr.value.address.trim() && hasLocation.value)
const addressLocation = computed({
  get() {
    return { lat: newAddr.value.lat, lng: newAddr.value.lng }
  },
  set(value = {}) {
    newAddr.value.lat = normalizeCoordinate(value.lat)
    newAddr.value.lng = normalizeCoordinate(value.lng)
    locationError.value = ''
  },
})

function goBack() { window.history.back() }
function openAddForm() {
  editingId.value = null
  locationError.value = ''
  mapStatus.value = ''
  newAddr.value = { label: 'خانه', type: 'خانه', address: '', detail: '', lat: '', lng: '' }
  showForm.value = true
}
function editAddress(addr) {
  const normalized = normalizeAddress(addr)
  editingId.value = normalized.id
  locationError.value = ''
  mapStatus.value = ''
  newAddr.value = { ...normalized }
  showForm.value = true
}
function closeForm() { showForm.value = false; editingId.value = null; locationError.value = '' }

function useCurrentLocation() {
  locationError.value = ''
  if (!navigator.geolocation) {
    locationError.value = 'مرورگر شما دسترسی به موقعیت مکانی را پشتیبانی نمی‌کند.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      newAddr.value.lat = normalizeCoordinate(position.coords.latitude)
      newAddr.value.lng = normalizeCoordinate(position.coords.longitude)
      locating.value = false
      locationError.value = ''
    },
    () => {
      locating.value = false
      locationError.value = 'دسترسی به موقعیت مکانی ممکن نشد. لطفاً اجازه GPS را فعال کنید یا نقطه را روی نقشه انتخاب کنید.'
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
  )
}

async function saveAddress() {
  if (!newAddr.value.address.trim()) return
  if (!hasLocation.value) {
    locationError.value = 'برای ذخیره آدرس باید لوکیشن معتبر انتخاب شود.'
    return
  }
  const auth = readAuth()
  if (!auth.mobile) {
    error.value = 'برای ذخیره آدرس ابتدا وارد شوید.'
    window.location.href = '/customer/login?redirect=/customer/addresses'
    return
  }
  const localId = editingId.value || Date.now()
  try {
    const result = await saveCustomerDeliveryAddress({
      customer_info: { name: auth.name || 'مشتری', mobile: auth.mobile },
      address_info: {
        id: editingId.value || '',
        label: newAddr.value.label,
        type: newAddr.value.type,
        address: newAddr.value.address,
        detail: newAddr.value.detail,
        address_line: newAddr.value.address,
        address_line1: newAddr.value.address,
        address_line2: newAddr.value.detail,
        lat: normalizeCoordinate(newAddr.value.lat),
        lng: normalizeCoordinate(newAddr.value.lng),
      },
    })
    addresses.value = (result?.addresses || []).map(normalizeAddress)
    if (!addresses.value.length) addresses.value.push({ ...newAddr.value, id: localId })
  } catch {
    if (editingId.value) {
      const idx = addresses.value.findIndex((a) => a.id === editingId.value)
      if (idx >= 0) addresses.value[idx] = { ...newAddr.value, id: editingId.value }
    } else {
      addresses.value.push({ ...newAddr.value, id: localId })
    }
  }
  saveAddresses(addresses.value)
  closeForm()
}

function deleteAddress(id) {
  if (!confirm('این آدرس حذف شود؟')) return
  addresses.value = addresses.value.filter((a) => a.id !== id)
  if (selectedId.value === id) selectedId.value = addresses.value[0]?.id || null
  saveAddresses(addresses.value)
}

function confirmSelection() {
  const addr = addresses.value.find((a) => a.id === selectedId.value)
  if (addr) {
    try { localStorage.setItem('selected_address', JSON.stringify(addr)) } catch {}
    window.history.back()
  }
}

onMounted(async () => {
  try {
    const boot = await getMenuBoot('')
    if (boot?.checkout_map && typeof boot.checkout_map === 'object') {
      mapConfig.value = { ...mapConfig.value, ...boot.checkout_map }
    }
  } catch {}

  const auth = readAuth()
  if (!auth.mobile) return
  loading.value = true
  try {
    const data = await getCustomerCheckoutProfile({ mobile: auth.mobile, customer_name: auth.name })
    addresses.value = (data?.addresses || []).map(normalizeAddress)
    selectedId.value = addresses.value[0]?.id || null
    saveAddresses(addresses.value)
  } catch (err) {
    error.value = err?.message || 'خطا در دریافت آدرس‌ها'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.address-card {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 1rem;
  cursor: pointer;
  border: 1px solid transparent;
}

.address-card.is-selected {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  box-shadow: 0 12px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.address-card__radio {
  padding-top: 0.35rem;
}

.address-card__dot {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border: 2px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  display: inline-flex;
  position: relative;
}

.address-card__dot.is-active {
  border-color: var(--accent-green);
}

.address-card__dot.is-active::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: inherit;
  background: var(--accent-green);
}

.address-card__body {
  flex: 1;
  min-width: 0;
}

.address-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.address-card__head strong {
  display: block;
  font-size: 0.96rem;
}

.address-card__head p {
  margin: 0.3rem 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.address-card__body small {
  display: block;
  margin-top: 0.35rem;
  color: var(--text-muted);
}

.address-card__actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.icon-action {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-action--danger {
  color: var(--danger);
  border-color: rgb(var(--danger-rgb) / 0.18);
  background: rgb(var(--danger-rgb) / 0.08);
}

.add-address-row {
  min-height: 58px;
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--accent-green);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.38);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 220;
  padding: 1rem;
}

.modal-sheet {
  width: min(620px, 100%);
  padding: 1.2rem;
  border-radius: 28px;
}

.modal-sheet__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.modal-title {
  margin: 0.3rem 0 0;
  font-size: 1.1rem;
}

.modal-eyebrow {
  color: var(--text-muted);
}

.location-field {
  padding: 0.85rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  border-radius: 22px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.035);
}

.location-field__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.8rem;
}

.location-field__head label {
  margin-bottom: 0.25rem;
}

.location-field__head p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.78rem;
  line-height: 1.7;
}

.locate-btn {
  flex-shrink: 0;
  min-width: auto;
  min-height: 40px;
  text-decoration: none;
}

.location-coordinates {
  margin-top: 0.75rem;
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 14px;
  padding: 0.65rem;
}

.location-coordinates summary {
  min-height: 44px;
  display: flex;
  align-items: center;
  cursor: pointer;
  color: var(--accent-green);
  font-weight: 800;
}

.location-coordinates__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
  margin-top: 0.5rem;
}

.location-coordinates label span {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 700;
}

.location-error,
.location-hint,
.location-ok {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
  line-height: 1.7;
}

.location-error {
  color: var(--danger);
}

.location-hint {
  color: var(--text-muted);
}

.location-ok {
  color: var(--success);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.modal-cancel,
.modal-save {
  flex: 1;
}

@media (max-width: 520px) {
  .location-field__head,
  .modal-actions {
    flex-direction: column;
  }

  .locate-btn,
  .modal-cancel,
  .modal-save {
    width: 100%;
  }

  .location-coordinates__grid {
    grid-template-columns: 1fr;
  }
}
</style>
