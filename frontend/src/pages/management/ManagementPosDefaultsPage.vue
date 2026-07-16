<template>
  <ManagementPageScaffold title="تنظیمات پیش‌فرض POS" subtitle="مشتری پیش‌فرض و جایگاه‌ها را برای هر نوع سفارش تنظیم کنید">
    <template #actions>
      <button class="primary-btn" type="button" @click="saveConfig" :disabled="saving">
        {{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}
      </button>
      <button class="secondary-btn" type="button" @click="loadConfig" :disabled="loading">
        {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
      </button>
    </template>

    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <!-- Default Order Mode -->
    <ManagementSurfaceCard title="نوع سفارش پیش‌فرض" subtitle="هنگام باز کردن فاکتور جدید، کدام حالت به صورت پیش‌فرض انتخاب شود">
      <div class="mode-selector">
        <button
          v-for="mode in orderModes"
          :key="mode.value"
          type="button"
          class="mode-btn"
          :class="{ active: localConfig.default_order_mode === mode.value }"
          @click="localConfig.default_order_mode = mode.value"
        >
          {{ mode.label }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <!-- Default Customer Settings -->
    <ManagementSurfaceCard title="مشتری پیش‌فرض" subtitle="برای هر نوع سفارش، مشتری پیش‌فرض را مشخص کنید">
      <div class="customer-settings-grid">
        <div v-for="mode in orderModes" :key="mode.value" class="customer-mode-card">
          <h3>{{ mode.label }}</h3>
          <label>
            نام مشتری
            <select
              class="input"
              :value="selectedCustomerKey(mode.value)"
              @change="applyCustomerSelection(mode.value, $event.target.value)"
            >
              <option value="">انتخاب از دیتابیس مشتری‌ها</option>
              <option v-for="customer in customerOptions" :key="customer.key" :value="customer.key">
                {{ customer.label }}
              </option>
            </select>
          </label>
          <label>
            شماره موبایل
            <input
              class="input"
              v-model="localConfig.default_customers[mode.value].mobile"
              placeholder="09120000000"
              type="tel"
              readonly
            />
          </label>
        </div>
      </div>
    </ManagementSurfaceCard>

    <!-- Takeaway Places -->
    <ManagementSurfaceCard title="جایگاه‌های بیرون بر (مشتری)" subtitle="لیست جایگاه‌هایی که در حالت بیرون بر نمایش داده می‌شود">
      <div class="places-editor">
        <p class="muted" v-if="!localConfig.takeaway_places.length">هیچ جایگاهی تعریف نشده است.</p>
        <div v-for="(place, idx) in localConfig.takeaway_places" :key="'takeaway-' + idx" class="place-row">
          <input
            class="input"
            v-model="localConfig.takeaway_places[idx]"
            :placeholder="`جایگاه ${idx + 1}`"
          />
          <button
            type="button"
            class="ghost-btn danger"
            @click="removeTakeawayPlace(idx)"
            title="حذف"
          >×</button>
        </div>
        <button type="button" class="secondary-btn" @click="addTakeawayPlace">+ افزودن جایگاه</button>

        <div class="default-place-select" v-if="localConfig.takeaway_places.length">
          <label>
            جایگاه پیش‌فرض:
            <select class="input" v-model="localConfig.default_takeaway_place">
              <option v-for="place in localConfig.takeaway_places" :key="place" :value="place">{{ place }}</option>
            </select>
          </label>
          <p class="muted hint">اگر فقط یک جایگاه داشته باشید، انتخابگر نمایش داده نمی‌شود.</p>
        </div>
      </div>
    </ManagementSurfaceCard>

    <!-- Delivery Courier -->
    <ManagementSurfaceCard title="پیک پیش‌فرض" subtitle="پیک فعال را از ناوگان داخلی انتخاب کنید">
      <div class="places-editor">
        <label>
          پیک پیش‌فرض
          <select class="input" v-model="localConfig.default_delivery_courier">
            <option value="">انتخاب پیک</option>
            <option v-for="courier in courierOptions" :key="courier.name" :value="courier.label">
              {{ courier.label }}{{ courier.mobile ? ` - ${courier.mobile}` : '' }}
            </option>
          </select>
        </label>
        <p class="muted hint" v-if="localConfig.default_delivery_courier">
          در POS، این پیک به‌صورت پیش‌فرض برای سفارش‌های بیرون‌بر (پیک) پیشنهاد می‌شود.
        </p>
        <a class="secondary-btn manage-link" href="/management/couriers">مدیریت پیک‌ها و ناوگان</a>
      </div>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementPOSConfig,
  listManagementCouriers,
  listManagementCustomers,
  setManagementPOSConfig,
} from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')
const customerOptions = ref([])
const courierOptions = ref([])

const orderModes = [
  { value: 'dine_in', label: 'سالن' },
  { value: 'takeaway', label: 'بیرون بر (مشتری)' },
  { value: 'delivery', label: 'بیرون بر (پیک)' },
]

const defaultConfig = {
  default_order_mode: 'dine_in',
  default_customers: {
    dine_in: { name: 'POS Customer', mobile: '09120000000' },
    takeaway: { name: 'POS Customer', mobile: '09120000000' },
    delivery: { name: 'POS Customer', mobile: '09120000000' },
  },
  takeaway_places: ['بیرون بر حضوری', 'تحویل کنار سالن'],
  default_takeaway_place: 'بیرون بر حضوری',
  delivery_places: ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس'],
  default_delivery_place: 'پیک 1',
  default_delivery_courier: '',
}

const localConfig = reactive({
  default_order_mode: 'dine_in',
  default_customers: {
    dine_in: { name: 'POS Customer', mobile: '09120000000' },
    takeaway: { name: 'POS Customer', mobile: '09120000000' },
    delivery: { name: 'POS Customer', mobile: '09120000000' },
  },
  takeaway_places: ['بیرون بر حضوری', 'تحویل کنار سالن'],
  default_takeaway_place: 'بیرون بر حضوری',
  delivery_places: ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس'],
  default_delivery_place: 'پیک 1',
  default_delivery_courier: '',
})

function applyConfig(cfg) {
  if (!cfg) return
  localConfig.default_order_mode = cfg.default_order_mode || 'dine_in'
  localConfig.default_customers = {
    dine_in: { name: 'POS Customer', mobile: '09120000000', ...(cfg.default_customers?.dine_in || {}) },
    takeaway: { name: 'POS Customer', mobile: '09120000000', ...(cfg.default_customers?.takeaway || {}) },
    delivery: { name: 'POS Customer', mobile: '09120000000', ...(cfg.default_customers?.delivery || {}) },
  }
  localConfig.takeaway_places = Array.isArray(cfg.takeaway_places) ? [...cfg.takeaway_places] : ['بیرون بر حضوری', 'تحویل کنار سالن']
  localConfig.default_takeaway_place = cfg.default_takeaway_place || (localConfig.takeaway_places[0] || '')
  localConfig.delivery_places = Array.isArray(cfg.delivery_places) ? [...cfg.delivery_places] : ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس']
  localConfig.default_delivery_place = cfg.default_delivery_place || (localConfig.delivery_places[0] || '')
  localConfig.default_delivery_courier = cfg.default_delivery_courier || ''
}

async function loadConfig() {
  error.value = ''
  successMessage.value = ''
  loading.value = true
  try {
    const data = await getManagementPOSConfig()
    applyConfig(data)
  } catch (err) {
    error.value = String(err?.message || err || 'خطا در دریافت تنظیمات')
  } finally {
    loading.value = false
  }
}

async function loadDirectoryData() {
  const [customersPayload, couriersPayload] = await Promise.all([
    listManagementCustomers({}),
    listManagementCouriers({ active_only: 1 }),
  ])
  customerOptions.value = (customersPayload?.customers || []).map((row) => ({
    key: `${row.customer_name || ''}::${row.mobile || ''}`,
    name: row.customer_name || '',
    mobile: row.mobile || '',
    label: `${row.customer_name || 'بدون نام'}${row.mobile ? ` - ${row.mobile}` : ''}`,
  }))
  courierOptions.value = (couriersPayload?.couriers || []).map((row) => ({
    name: row.name,
    label: row.courier_name || '',
    mobile: row.mobile || '',
  }))
}

async function saveConfig() {
  error.value = ''
  successMessage.value = ''
  saving.value = true
  try {
    const payload = {
      default_order_mode: localConfig.default_order_mode,
      default_customers: localConfig.default_customers,
      takeaway_places: localConfig.takeaway_places.filter(Boolean),
      default_takeaway_place: localConfig.default_takeaway_place,
      delivery_places: localConfig.delivery_places.filter(Boolean),
      default_delivery_place: localConfig.default_delivery_place,
      default_delivery_courier: localConfig.default_delivery_courier,
    }
    await setManagementPOSConfig(payload)
    successMessage.value = 'تنظیمات با موفقیت ذخیره شد.'
  } catch (err) {
    error.value = String(err?.message || err || 'خطا در ذخیره تنظیمات')
  } finally {
    saving.value = false
  }
}

function addTakeawayPlace() {
  localConfig.takeaway_places.push('')
}

function removeTakeawayPlace(idx) {
  localConfig.takeaway_places.splice(idx, 1)
  if (!localConfig.takeaway_places.includes(localConfig.default_takeaway_place)) {
    localConfig.default_takeaway_place = localConfig.takeaway_places[0] || ''
  }
}

function addDeliveryPlace() {
  localConfig.delivery_places.push('')
}

function removeDeliveryPlace(idx) {
  localConfig.delivery_places.splice(idx, 1)
  if (!localConfig.delivery_places.includes(localConfig.default_delivery_place)) {
    localConfig.default_delivery_place = localConfig.delivery_places[0] || ''
  }
}

function selectedCustomerKey(mode) {
  const row = localConfig.default_customers?.[mode] || {}
  return `${row.name || ''}::${row.mobile || ''}`
}

function applyCustomerSelection(mode, key) {
  const match = customerOptions.value.find((row) => row.key === key)
  if (!match) {
    localConfig.default_customers[mode] = { name: '', mobile: '' }
    return
  }
  localConfig.default_customers[mode] = {
    name: match.name || '',
    mobile: match.mobile || '',
  }
}

onMounted(() => {
  Promise.all([loadConfig(), loadDirectoryData()]).catch((err) => {
    error.value = String(err?.message || err || 'خطا در بارگذاری داده‌ها')
  })
})
</script>

<style scoped>
.mode-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mode-btn {
  padding: 10px 20px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}
.mode-btn:hover {
  border-color: #888;
}
.mode-btn.active {
  border-color: #4f46e5;
  background: #eef2ff;
  color: #4f46e5;
}
.customer-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.customer-mode-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}
.customer-mode-card h3 {
  margin: 0 0 12px;
  font-size: 15px;
}
.customer-mode-card label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}
.customer-mode-card .input {
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
}
.places-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.place-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.place-row .input {
  flex: 1;
}
.ghost-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 16px;
}
.ghost-btn.danger {
  color: #ef4444;
}
.ghost-btn.danger:hover {
  background: #fef2f2;
}
.secondary-btn {
  align-self: flex-start;
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}
.secondary-btn:hover {
  background: #f9fafb;
}
.default-place-select {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}
.default-place-select label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #444;
}
.default-place-select .input {
  max-width: 300px;
}
.hint {
  font-size: 12px;
  margin-top: 6px;
}
.manage-link {
  display: inline-flex;
  text-decoration: none;
}
</style>
