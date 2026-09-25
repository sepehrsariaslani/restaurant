<template>
  <div class="customer-page addresses-page" dir="rtl">
    <CustomerPageHeader eyebrow="حساب من" title="آدرس‌های من" subtitle="یک بار ذخیره کنید، سفارش بعدی سریع‌تر می‌رسد." fallback-href="/customer/dashboard">
      <template #eyebrow-icon><MapPin :size="16" /></template>
      <template #action><button class="customer-page__action" type="button" @click="openEditor()"><Plus :size="18" />جدید</button></template>
    </CustomerPageHeader>
    <main class="customer-page__body">
      <p v-if="loading" class="address-message" role="status">در حال دریافت آدرس‌ها…</p>
      <p v-if="error" class="address-error" role="alert">{{ error }} <button v-if="!showForm" type="button" @click="loadAddresses">تلاش دوباره</button></p>
      <p v-if="message" class="address-message" role="status">{{ message }}</p>
      <section v-if="showForm" class="address-editor customer-glass-card">
        <div class="address-editor-head"><h2>{{ editingId ? 'ویرایش آدرس' : 'آدرس جدید' }}</h2><button class="customer-page__ghost-action" type="button" @click="showForm = false" aria-label="بستن فرم آدرس"><X :size="20" /></button></div>
        <div class="address-map-head"><span>اول محل دقیق تحویل را انتخاب کنید</span><button type="button" class="customer-page__ghost-action" :disabled="locating" @click="useCurrentLocation"><Crosshair :size="17" />{{ locating ? 'در حال دریافت…' : 'موقعیت من' }}</button></div>
        <AddressPickerMap v-model="addressLocation" :config="mapConfig" @status="mapStatus = $event" />
        <p v-if="locationError" class="address-error" role="alert">{{ locationError }}</p>
        <details :open="mapStatus === 'error'" class="address-manual"><summary>ورود دستی مختصات</summary><div class="address-grid">
          <label class="customer-field">عرض جغرافیایی<input class="customer-input" v-model="draft.lat" inputmode="decimal" dir="ltr" /></label>
          <label class="customer-field">طول جغرافیایی<input class="customer-input" v-model="draft.lng" inputmode="decimal" dir="ltr" /></label>
        </div></details>
        <form class="address-form" @submit.prevent="saveAddress">
          <label class="customer-field">عنوان آدرس<input class="customer-input" v-model.trim="draft.title" placeholder="خانه یا محل کار" required /></label>
          <label class="customer-field">نشانی کامل<textarea class="customer-textarea" v-model.trim="draft.address_line" placeholder="خیابان، کوچه و جزئیات مسیر" rows="3" required /></label>
          <div class="address-grid">
            <label class="customer-field">پلاک<input class="customer-input" v-model="draft.plaque" /></label>
            <label class="customer-field">واحد<input class="customer-input" v-model="draft.unit" /></label>
          </div>
          <div class="address-editor-actions"><button class="customer-page__ghost-action" type="button" @click="showForm = false">انصراف</button><button class="address-save" type="submit" :disabled="saving || !canSaveAddress">{{ saving ? 'در حال ذخیره…' : 'ذخیره آدرس' }}</button></div>
          <p v-if="!hasLocation" class="address-message">برای ذخیره، نقطهٔ تحویل را روی نقشه انتخاب کنید.</p>
        </form>
      </section>
      <div v-else-if="!loading && !error && !addresses.length" class="customer-empty customer-glass-card"><MapPin :size="32" /><h2>اولین آدرس را اضافه کنید</h2><p>خانه یا محل کار؛ هرجا که دوست دارید غذا برسد.</p><button class="address-save" type="button" @click="openEditor()">افزودن آدرس</button></div>
      <div v-else-if="!showForm" class="address-list">
        <article v-for="address in addresses" :key="address.id" class="address-card customer-glass-card">
          <div class="address-card-heading"><span class="customer-icon-badge"><MapPin :size="22" /></span><h2>{{ address.title }}</h2><button class="customer-page__ghost-action" type="button" :aria-label="`ویرایش ${address.title}`" @click="openEditor(address)"><Pencil :size="17" /></button></div>
          <p>{{ address.address_line }}</p><small v-if="address.plaque || address.unit">{{ address.plaque ? `پلاک ${address.plaque}` : '' }} {{ address.unit ? `· واحد ${address.unit}` : '' }}</small>
          <button v-if="auth.customer_token" class="address-archive" type="button" :disabled="archiving === address.id" @click="archive(address)"><Trash2 :size="16" />حذف از آدرس‌های من</button>
          <button class="address-use" type="button" @click="useAddress(address)">سفارش به این آدرس <ChevronLeft :size="17" /></button>
        </article>
      </div>
    </main>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ChevronLeft, Crosshair, MapPin, Pencil, Plus, Trash2, X } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import AddressPickerMap from '@/components/checkout/AddressPickerMap.vue'
import { getCustomerCheckoutProfile, getMenuBoot, saveCustomerDeliveryAddress, archiveCustomerAddress } from '@/utils/api'
import { hasDeliveryCoordinates } from '@/utils/customerOrderValidation'
import { saveCheckoutDraft, saveOrderContext } from '@/stores/cartStore'
let auth = {}
try { auth = JSON.parse(localStorage.getItem('restaurant-customer-auth-v1') || '{}') } catch {}
const addresses = ref([]), loading = ref(true), error = ref(''), message = ref(''), showForm = ref(false), saving = ref(false)
const archiving = ref('')
const editingId = ref(''), locating = ref(false), locationError = ref(''), mapStatus = ref(''), mapConfig = ref({})
const emptyAddress = () => ({ title: 'خانه', address_line: '', plaque: '', unit: '', floor: '', phone: auth.mobile || '', lat: '', lng: '' })
const draft = reactive(emptyAddress())
const hasLocation = computed(() => hasDeliveryCoordinates(draft))
const canSaveAddress = computed(() => Boolean(draft.title.trim() && draft.address_line.trim() && hasLocation.value))
const addressLocation = computed({ get: () => ({ lat: draft.lat, lng: draft.lng }), set: (point) => { draft.lat = point.lat; draft.lng = point.lng; locationError.value = '' } })
function openEditor(address = null) { editingId.value = address?.id || ''; Object.keys(draft).forEach(key => delete draft[key]); Object.assign(draft, emptyAddress(), address || {}); error.value = ''; message.value = ''; locationError.value = ''; showForm.value = true }
async function loadAddresses() {
  if (!auth.mobile || !auth.customer_token) { window.location.replace('/customer/login?redirect=%2Fcustomer%2Faddresses'); return }
  loading.value = true; error.value = ''
  try { const data = await getCustomerCheckoutProfile({ mobile: auth.mobile }); addresses.value = data.addresses || [] }
  catch (err) { error.value = err.message || 'آدرس‌ها دریافت نشدند.' }
  finally { loading.value = false }
}
async function saveAddress() {
  if (!canSaveAddress.value || saving.value) return
  saving.value = true; error.value = ''
  try {
    const result = await saveCustomerDeliveryAddress({ customer_info: { name: auth.customer_name || localStorage.getItem('customer_name') || 'مشتری', mobile: auth.mobile }, address_info: { ...draft, id: editingId.value } })
    if (!result?.address?.id) throw new Error('سرور ذخیره آدرس را تأیید نکرد؛ دوباره تلاش کنید.')
    addresses.value = result.addresses || [result.address]
    showForm.value = false; message.value = 'آدرس در حساب شما ذخیره شد.'
  } catch (err) { error.value = err.message || 'آدرس ذخیره نشد؛ اطلاعات فرم حفظ شده است.' }
  finally { saving.value = false }
}
async function archive(address) {
  if (!window.confirm(`آدرس «${address.title}» از فهرست شما حذف شود؟`)) return
  archiving.value = address.id; error.value = ''
  try { await archiveCustomerAddress(address.id); addresses.value = addresses.value.filter(row => row.id !== address.id); message.value = 'آدرس از فهرست شما حذف شد.' }
  catch (err) { error.value = err.message || 'حذف آدرس انجام نشد.' }
  finally { archiving.value = '' }
}
function useAddress(address) {
  saveOrderContext({ order_type: 'delivery', address: { ...address }, table: '', pickup_vehicle: null })
  saveCheckoutDraft({ delivery_address_id: address.id, use_new_address: false })
  window.location.href = '/order/delivery'
}
function useCurrentLocation() {
  locationError.value = ''
  if (!navigator.geolocation) { locationError.value = 'موقعیت من در این مرورگر در دسترس نیست؛ روی نقشه انتخاب کنید.'; return }
  locating.value = true
  navigator.geolocation.getCurrentPosition((position) => { draft.lat = position.coords.latitude; draft.lng = position.coords.longitude; locating.value = false }, () => { locating.value = false; locationError.value = 'دریافت موقعیت ممکن نشد؛ روی نقشه انتخاب کنید.' }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 })
}
onMounted(() => {
  loadAddresses()
  getMenuBoot('').then((boot) => { mapConfig.value = boot.checkout_map || {} }).catch(() => {})
})
</script>
<style scoped>
.address-archive { display: flex; align-items: center; gap: .4rem; min-height: 44px; font: inherit; font-size: .8rem; border: 0; background: transparent; color: var(--ds-color-status-danger); cursor: pointer; }

.address-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.address-card, .address-editor { padding: 1.25rem; }
.address-card-heading, .address-editor-head, .address-map-head { display: flex; align-items: center; gap: .75rem; justify-content: space-between; }
.address-card-heading h2 { flex: 1; font-size: 1rem; margin: 0; }
.address-card p { color: var(--ds-color-text-secondary); line-height: 1.9; }
.address-card small { color: var(--ds-color-text-muted); }
.address-use { display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: 48px; margin-top: 1rem; padding: .6rem 0 0; border: 0; border-top: 1px solid var(--ds-color-border); background: transparent; color: var(--ds-color-action-primary); font: inherit; font-weight: 700; cursor: pointer; }
.address-editor { display: grid; gap: 1rem; }
.address-editor-head h2 { margin: 0; font-size: 1.15rem; }
.address-form { display: grid; gap: 1rem; }
.address-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; }
.address-editor-actions { display: flex; justify-content: flex-end; gap: .75rem; }
.address-save { min-height: 48px; padding: .7rem 1.4rem; border: 0; border-radius: var(--ds-radius-md); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font: inherit; font-weight: 700; cursor: pointer; }
.address-save:disabled { opacity: .5; cursor: default; }
.address-message { color: var(--ds-color-text-muted); font-size: .88rem; }
.address-error { color: var(--ds-color-status-danger); line-height: 1.8; }
.address-error button { min-height: 44px; font: inherit; color: inherit; border: 0; background: transparent; text-decoration: underline; }
.address-manual summary { min-height: 44px; color: var(--ds-color-text-muted); cursor: pointer; }
@media(max-width: 640px) { .address-list { grid-template-columns: 1fr; } .address-map-head { flex-wrap: wrap; font-size: .85rem; } }
</style>
