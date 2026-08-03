<template>
  <ManagementPageScaffold title="مدیریت پیک‌ها و ناوگان" subtitle="پیک‌های داخلی، وسیله‌های فعال و پیش‌نیاز گزارش‌های تحویل">
    <template #actions>
      <button class="secondary-btn" type="button" @click="loadAll" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <ManagementSurfaceCard tone="accent" title="خلاصه ناوگان" subtitle="نمای سریع از پیک‌ها و وسیله‌های فعال">
      <div class="summary-grid">
        <article class="summary-card">
          <small>کل پیک‌ها</small>
          <strong>{{ toFa(summary.courier_count) }}</strong>
        </article>
        <article class="summary-card">
          <small>پیک فعال</small>
          <strong>{{ toFa(summary.active_courier_count) }}</strong>
        </article>
        <article class="summary-card">
          <small>کل وسیله‌ها</small>
          <strong>{{ toFa(summary.vehicle_count) }}</strong>
        </article>
        <article class="summary-card">
          <small>وسیله فعال</small>
          <strong>{{ toFa(summary.active_vehicle_count) }}</strong>
        </article>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft" class="section-picker-shell">
      <div class="section-picker">
        <div class="simple-tabs" role="tablist" aria-label="بخش‌های مدیریت پیک">
          <button
            v-for="tab in tabOptions"
            :key="tab.value"
            class="simple-tab"
            :class="{ active: activeTab === tab.value }"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.value"
            @click="activeTab = tab.value"
          >
            <span>{{ tab.label }}</span>
            <span v-if="getTabBadge(tab.value)" class="tab-badge">{{ getTabBadge(tab.value) }}</span>
          </button>
        </div>
        <button class="secondary-btn" type="button" @click="loadAll" :disabled="loading">
          {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <section v-if="activeTab === 'couriers'" class="panel-grid">
      <ManagementSurfaceCard title="لیست پیک‌ها" subtitle="تعریف پیک، اولویت تخصیص و زون سرویس">
        <div class="toolbar-row">
          <input
            v-model.trim="courierSearch"
            class="input"
            placeholder="جستجو بر اساس نام، کد، موبایل، پلاک یا زون"
            @keyup.enter="loadCouriers"
          />
          <button class="secondary-btn" type="button" @click="resetCourierForm">پیک جدید</button>
        </div>

        <div class="editor-grid">
          <label>
            نام پیک
            <input v-model.trim="courierForm.courier_name" class="input" />
          </label>
          <label>
            کد پیک
            <input v-model.trim="courierForm.courier_code" class="input" />
          </label>
          <label>
            موبایل
            <input v-model.trim="courierForm.mobile" class="input" dir="ltr" />
          </label>
          <label>
            کد دسترسی اپ پیک
            <input v-model.trim="courierForm.access_code" class="input" dir="ltr" placeholder="برای ورود به /courier" />
          </label>
          <label>
            نوع وسیله اصلی
            <input v-model.trim="courierForm.vehicle_type" class="input" />
          </label>
          <label>
            پلاک وسیله اصلی
            <input v-model.trim="courierForm.plate_number" class="input" />
          </label>
          <label>
            ناحیه / زون
            <input v-model.trim="courierForm.zone" class="input" />
          </label>
          <label>
            اولویت تخصیص
            <input v-model.number="courierForm.assignment_priority" class="input" type="number" min="0" />
          </label>
          <label class="check-row">
            <input v-model="courierForm.is_active" type="checkbox" />
            فعال
          </label>
        </div>

        <ManagementNoteField
          v-model="courierForm.notes"
          class="full-width"
          label="یادداشت"
          rows="3"
          placeholder="یادداشت داخلی پیک..."
        />

        <div class="form-actions">
          <button class="primary-btn" type="button" :disabled="savingCourier" @click="saveCourier">
            {{ savingCourier ? 'در حال ذخیره...' : courierForm.name ? 'ذخیره تغییرات پیک' : 'ثبت پیک' }}
          </button>
          <button
            v-if="courierForm.name"
            class="ghost-btn danger"
            type="button"
            :disabled="savingCourier"
            @click="removeCourier(courierForm.name)"
          >
            حذف پیک
          </button>
        </div>

        <ManagementDataTable :columns="courierColumns" :rows="couriers" row-key="name">
          <template #cell-courier_name="{ row }">
            <button class="mini-link-btn" type="button" @click="editCourier(row)">{{ row.courier_name }}</button>
          </template>
          <template #cell-mobile="{ value }">{{ value || '-' }}</template>
          <template #cell-zone="{ value }">{{ value || '-' }}</template>
          <template #cell-assignment_priority="{ value }">{{ toFa(value) }}</template>
          <template #cell-vehicle_count="{ value }">{{ toFa(value) }}</template>
          <template #cell-is_active="{ value }">{{ value ? 'فعال' : 'غیرفعال' }}</template>
        </ManagementDataTable>
      </ManagementSurfaceCard>
    </section>

    <section v-else-if="activeTab === 'rules'" class="panel-grid">
      <ManagementSurfaceCard title="قوانین پیک‌ها" subtitle="تب مستقل برای منطق عملیاتی و ساختار مدیریت تحویل">
        <div class="rules-grid">
          <article class="rule-card">
            <strong>ترتیب تخصیص</strong>
            <p>پیک‌ها بر اساس اولویت تخصیص و سپس نام مرتب می‌شوند. عدد کمتر، اولویت بالاتر دارد.</p>
          </article>
          <article class="rule-card">
            <strong>نمایش در POS</strong>
            <p>در POS و پیش‌فرض‌های POS فقط پیک‌های فعال برای انتخاب نمایش داده می‌شوند.</p>
          </article>
          <article class="rule-card">
            <strong>اولویت ناوگان</strong>
            <p>برای هر پیک، وسیله‌ای که به‌عنوان وسیله اصلی ثبت شده باشد بالاتر از بقیه نمایش داده می‌شود.</p>
          </article>
          <article class="rule-card">
            <strong>آماده توسعه گزارش</strong>
            <p>این تب جدا شده تا بعداً گزارش سفارش، پیک، وسیله، مسیر و مسافت روی همین ساختار سوار شود.</p>
          </article>
        </div>

        <div class="rules-note">
          <strong>وضعیت فعلی:</strong>
          <span>
            {{ toFa(summary.active_courier_count) }} پیک فعال و {{ toFa(summary.active_vehicle_count) }} وسیله فعال
            در سیستم موجود است.
          </span>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="بهینه‌سازی مسیر تحویل" subtitle="چیدمان سفارش‌های در حال ارسال هر پیک بر اساس نزدیک‌ترین مسیر؛ ترتیب در اپ پیک اعمال می‌شود">
        <div class="dispatch-box">
          <select v-model="routeForm.courier" class="input">
            <option value="">— انتخاب پیک —</option>
            <option v-for="courier in courierOptions" :key="courier.name" :value="courier.name">{{ courier.label || courier.name }}</option>
          </select>
          <button class="secondary-btn" type="button" :disabled="routeOptimizing || !routeForm.courier" @click="runRouteOptimization">
            {{ routeOptimizing ? 'در حال محاسبه...' : 'بهینه‌سازی مسیر' }}
          </button>
          <span v-if="routeMessage" class="ok-text">{{ routeMessage }}</span>
        </div>
        <div v-if="routeOrders.length" class="route-list">
          <div v-for="(row, idx) in routeOrders" :key="row.order || idx" class="route-item">
            <span class="route-index">{{ toFa(idx + 1) }}</span>
            <div>
              <strong>{{ row.order }}</strong>
              <small class="muted">{{ row.customer || '—' }}</small>
            </div>
            <small v-if="row.has_location === false" class="muted">بدون مختصات</small>
          </div>
        </div>
        <p class="muted provider-hint">ترتیب محاسبه‌شده روی هر سفارش ذخیره می‌شود (route index) و اپ پیک سفارش‌ها را به همین ترتیب نمایش می‌دهد. سفارش‌های بدون مختصات در انتهای مسیر می‌مانند.</p>
      </ManagementSurfaceCard>
    </section>

    <section v-else-if="activeTab === 'fleet'" class="panel-grid">
      <ManagementSurfaceCard title="ناوگان داخلی" subtitle="هر وسیله به یک پیک متصل می‌شود و می‌تواند وسیله اصلی او باشد">
        <div class="toolbar-row">
          <input
            v-model.trim="vehicleSearch"
            class="input"
            placeholder="جستجو بر اساس عنوان، نوع وسیله یا پلاک"
            @keyup.enter="loadVehicles"
          />
          <button class="secondary-btn" type="button" @click="resetVehicleForm">وسیله جدید</button>
        </div>

        <div class="editor-grid">
          <label>
            پیک
            <select v-model="vehicleForm.courier" class="input">
              <option value="">انتخاب پیک</option>
              <option v-for="courier in courierOptions" :key="courier.name" :value="courier.name">
                {{ courier.label }}
              </option>
            </select>
          </label>
          <label>
            نوع وسیله
            <input v-model.trim="vehicleForm.vehicle_type" class="input" />
          </label>
          <label>
            پلاک
            <input v-model.trim="vehicleForm.plate_number" class="input" />
          </label>
          <label>
            عنوان
            <input v-model.trim="vehicleForm.title" class="input" placeholder="اختیاری - خودکار هم ساخته می‌شود" />
          </label>
          <label class="check-row">
            <input v-model="vehicleForm.is_primary" type="checkbox" />
            وسیله اصلی پیک
          </label>
          <label class="check-row">
            <input v-model="vehicleForm.is_active" type="checkbox" />
            فعال
          </label>
        </div>

        <ManagementNoteField
          v-model="vehicleForm.notes"
          class="full-width"
          label="یادداشت"
          rows="3"
          placeholder="یادداشت داخلی وسیله..."
        />

        <div class="form-actions">
          <button class="primary-btn" type="button" :disabled="savingVehicle" @click="saveVehicle">
            {{ savingVehicle ? 'در حال ذخیره...' : vehicleForm.name ? 'ذخیره تغییرات وسیله' : 'ثبت وسیله' }}
          </button>
          <button
            v-if="vehicleForm.name"
            class="ghost-btn danger"
            type="button"
            :disabled="savingVehicle"
            @click="removeVehicle(vehicleForm.name)"
          >
            حذف وسیله
          </button>
        </div>

        <ManagementDataTable :columns="vehicleColumns" :rows="vehicles" row-key="name">
          <template #cell-title="{ row }">
            <button class="mini-link-btn" type="button" @click="editVehicle(row)">{{ row.title }}</button>
          </template>
          <template #cell-courier_label="{ value }">{{ value || '-' }}</template>
          <template #cell-is_primary="{ value }">{{ value ? 'اصلی' : '-' }}</template>
          <template #cell-is_active="{ value }">{{ value ? 'فعال' : 'غیرفعال' }}</template>
        </ManagementDataTable>
      </ManagementSurfaceCard>
    </section>

    <section v-else-if="activeTab === 'zones'" class="panel-grid">
      <ManagementSurfaceCard title="محدوده‌های سفارش‌گیری" subtitle="زون‌های دایره‌ای روی مختصات جغرافیایی؛ سفارش ارسال فقط داخل محدوده فعال پذیرفته می‌شود">
        <div class="editor-grid">
          <label>
            نام محدوده
            <input v-model.trim="zoneForm.zone_name" class="input" placeholder="مثلاً محدوده مرکز شهر" />
          </label>
          <label>
            عرض جغرافیایی مرکز (lat)
            <input v-model.number="zoneForm.center_lat" class="input" dir="ltr" type="number" step="0.000001" placeholder="35.6892" />
          </label>
          <label>
            طول جغرافیایی مرکز (lng)
            <input v-model.number="zoneForm.center_lng" class="input" dir="ltr" type="number" step="0.000001" placeholder="51.3890" />
          </label>
          <label>
            شعاع (کیلومتر)
            <input v-model.number="zoneForm.radius_km" class="input" type="number" min="0.1" step="0.1" />
          </label>
          <label>
            هزینه ارسال (ریال)
            <input v-model.number="zoneForm.delivery_fee" class="input" type="number" min="0" />
          </label>
          <label>
            حداقل سفارش (ریال)
            <input v-model.number="zoneForm.min_order_amount" class="input" type="number" min="0" />
          </label>
          <label class="check-row">
            <input v-model="zoneForm.is_active" type="checkbox" />
            فعال
          </label>
        </div>

        <ManagementNoteField
          v-model="zoneForm.notes"
          class="full-width"
          label="یادداشت"
          rows="2"
          placeholder="یادداشت داخلی محدوده..."
        />

        <div class="form-actions">
          <button class="primary-btn" type="button" :disabled="savingZone" @click="saveZone">
            {{ savingZone ? 'در حال ذخیره...' : zoneForm.name ? 'ذخیره تغییرات محدوده' : 'ثبت محدوده' }}
          </button>
          <button
            v-if="zoneForm.name"
            class="ghost-btn danger"
            type="button"
            :disabled="savingZone"
            @click="removeZone(zoneForm.name)"
          >
            حذف محدوده
          </button>
          <button class="secondary-btn" type="button" @click="resetZoneForm">محدوده جدید</button>
          <label class="check-row zone-toggle">
            <input v-model="providerForm.zone_control_enabled" type="checkbox" />
            کنترل محدوده هنگام ثبت سفارش ارسال فعال باشد
          </label>
          <button class="tertiary-btn" type="button" :disabled="savingProvider" @click="saveProviderSettings">ذخیره</button>
        </div>

        <ManagementDataTable :columns="zoneColumns" :rows="zones" row-key="name">
          <template #cell-zone_name="{ row }">
            <button class="mini-link-btn" type="button" @click="editZone(row)">{{ row.zone_name }}</button>
          </template>
          <template #cell-center="{ row }"><span dir="ltr">{{ row.center_lat }}, {{ row.center_lng }}</span></template>
          <template #cell-radius_km="{ value }">{{ toFa(value) }} km</template>
          <template #cell-delivery_fee="{ value }">{{ toFa(value) }}</template>
          <template #cell-min_order_amount="{ value }">{{ value ? toFa(value) : '-' }}</template>
          <template #cell-is_active="{ value }">{{ value ? 'فعال' : 'غیرفعال' }}</template>
        </ManagementDataTable>

        <div class="zone-check">
          <strong>تست محدوده:</strong>
          <input v-model.number="zoneCheck.lat" class="input" dir="ltr" type="number" step="0.000001" placeholder="lat" />
          <input v-model.number="zoneCheck.lng" class="input" dir="ltr" type="number" step="0.000001" placeholder="lng" />
          <button class="secondary-btn" type="button" :disabled="zoneChecking" @click="runZoneCheck">
            {{ zoneChecking ? '...' : 'بررسی' }}
          </button>
          <span v-if="zoneCheckResult" :class="zoneCheckResult.allowed ? 'ok-text' : 'warn-text'" class="zone-check-result">
            <template v-if="zoneCheckResult.allowed">
              داخل محدوده «{{ zoneCheckResult.matches[0].zone }}» — هزینه ارسال {{ toFa(zoneCheckResult.matches[0].delivery_fee) }}
            </template>
            <template v-else>خارج از همه محدوده‌های فعال</template>
          </span>
        </div>
      </ManagementSurfaceCard>
    </section>

    <section v-else-if="activeTab === 'provider'" class="panel-grid">
      <ManagementSurfaceCard title="اپ مخصوص پیک‌ها" subtitle="پییک با موبایل و کد دسترسی وارد می‌شود و سفارش‌های تخصیص‌یافته را مدیریت می‌کند">
        <div class="rules-grid">
          <article class="rule-card">
            <strong>نشانی اپ پیک</strong>
            <p><code class="link-code" dir="ltr">{{ courierAppUrl }}</code></p>
          </article>
          <article class="rule-card">
            <strong>ورود پیک</strong>
            <p>برای هر پیک در تب «لیست پیک‌ها» کد دسترسی تعریف کنید؛ پیک با موبایل + کد دسترسی لاگین می‌کند.</p>
          </article>
          <article class="rule-card">
            <strong>جریان تحویل</strong>
            <p>تحویل به پیک (courier_handoff) ← پیکاپ (در مسیر) ← تحویل‌شده. گزارش عملکرد در «مرکز گزارش‌ها ← عملکرد پیک‌ها».</p>
          </article>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="پلتفرم‌های ثالث پیک" subtitle="اتصال به اسنپ‌باکس، الوپیک یا سایر سرویس‌دهندگان برای دیسپچ خودکار سفارش">
        <div class="editor-grid">
          <label>
            پلتفرم
            <select v-model="providerForm.provider" class="input">
              <option value="">— غیرفعال —</option>
              <option v-for="p in providerOptions" :key="p" :value="p">{{ p }}</option>
            </select>
          </label>
          <label>
            توکن / کلید API {{ providerForm.token_set ? '(ثبت‌شده — برای تغییر مقدار جدید وارد کنید)' : '' }}
            <input v-model.trim="providerForm.token" class="input" dir="ltr" type="password" autocomplete="off" />
          </label>
          <label>
            نشانی سرویس (در صورت سفارشی)
            <input v-model.trim="providerForm.base_url" class="input" dir="ltr" placeholder="https://..." />
          </label>
        </div>
        <div class="form-actions">
          <button class="primary-btn" type="button" :disabled="savingProvider" @click="saveProviderSettings">
            {{ savingProvider ? 'در حال ذخیره...' : 'ذخیره تنظیمات پلتفرم' }}
          </button>
        </div>

        <div class="dispatch-box">
          <strong>ارسال سفارش به پلتفرم:</strong>
          <input v-model.trim="dispatchForm.order_name" class="input" dir="ltr" placeholder="کد سفارش، مثلاً SO-1024" />
          <button class="secondary-btn" type="button" :disabled="dispatching" @click="runDispatch">
            {{ dispatching ? 'در حال ارسال...' : 'دیسپچ' }}
          </button>
          <span v-if="dispatchResult" class="ok-text">{{ dispatchResult }}</span>
        </div>
        <p class="muted provider-hint">آساین پیک داخلی به سفارش: در کارت سفارش‌های ارسالی (POS/سفارش‌ها) یا API «assign_management_order_courier». وضعیت خودکار به «تحویل به پیک» می‌رود و در اپ پیک دیده می‌شود.</p>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  deleteManagementCourier,
  deleteManagementCourierVehicle,
  listManagementCouriers,
  listManagementCourierVehicles,
  saveManagementCourier,
  saveManagementCourierVehicle,
  listManagementDeliveryZones,
  saveManagementDeliveryZone,
  deleteManagementDeliveryZone,
  checkManagementDeliveryPoint,
  getManagementDeliveryProviderSettings,
  setManagementDeliveryProviderSettings,
  dispatchManagementDeliveryProvider,
  optimizeManagementCourierRoute,
} from '@/utils/api'

const loading = ref(false)
const savingCourier = ref(false)
const savingVehicle = ref(false)
const error = ref('')
const successMessage = ref('')
const courierSearch = ref('')
const vehicleSearch = ref('')
const couriers = ref([])
const vehicles = ref([])
const summary = reactive({
  courier_count: 0,
  active_courier_count: 0,
  vehicle_count: 0,
  active_vehicle_count: 0,
})
const activeTab = ref('couriers')

const courierForm = reactive(createCourierForm())
const vehicleForm = reactive(createVehicleForm())
const routeForm = reactive({ courier: '' })
const routeOptimizing = ref(false)
const routeMessage = ref('')
const routeOrders = ref([])

async function runRouteOptimization() {
  if (!routeForm.courier) return
  routeOptimizing.value = true
  routeMessage.value = ''
  routeOrders.value = []
  error.value = ''
  try {
    const payload = await optimizeManagementCourierRoute({ courier: routeForm.courier })
    routeOrders.value = Array.isArray(payload?.orders) ? payload.orders : []
    const optimized = Number(payload?.optimized) || routeOrders.value.length
    routeMessage.value = optimized
      ? `${toFa(optimized)} سفارش به ترتیب مسیر چیده شد.`
      : 'سفارش در حال ارسالی برای این پیک وجود ندارد.'
  } catch (err) {
    error.value = err?.message || 'بهینه‌سازی مسیر انجام نشد.'
  } finally {
    routeOptimizing.value = false
  }
}
const tabOptions = [
  { value: 'couriers', label: 'لیست پیک‌ها' },
  { value: 'rules', label: 'قوانین پیک‌ها' },
  { value: 'fleet', label: 'ناوگان داخلی' },
  { value: 'zones', label: 'محدوده‌های سفارش‌گیری' },
  { value: 'provider', label: 'اپ پیک و پلتفرم‌ها' },
]

const courierAppUrl = `${window.location.origin}/courier`

const courierColumns = [
  { key: 'courier_name', label: 'پیک' },
  { key: 'courier_code', label: 'کد' },
  { key: 'mobile', label: 'موبایل' },
  { key: 'zone', label: 'زون' },
  { key: 'assignment_priority', label: 'اولویت' },
  { key: 'vehicle_count', label: 'تعداد وسیله' },
  { key: 'is_active', label: 'وضعیت' },
]

const vehicleColumns = [
  { key: 'title', label: 'وسیله' },
  { key: 'courier_label', label: 'پیک' },
  { key: 'vehicle_type', label: 'نوع' },
  { key: 'plate_number', label: 'پلاک' },
  { key: 'is_primary', label: 'اصلی' },
  { key: 'is_active', label: 'وضعیت' },
]

const courierOptions = computed(() =>
  couriers.value.map((row) => ({ name: row.name, label: row.courier_name })),
)

function createCourierForm() {
  return {
    name: '',
    courier_name: '',
    courier_code: '',
    mobile: '',
    access_code: '',
    vehicle_type: '',
    plate_number: '',
    zone: '',
    assignment_priority: 10,
    is_active: true,
    notes: '',
  }
}

function createVehicleForm() {
  return {
    name: '',
    courier: '',
    title: '',
    vehicle_type: '',
    plate_number: '',
    is_primary: false,
    is_active: true,
    notes: '',
  }
}

function assignSummary(payload = {}) {
  summary.courier_count = Number(payload.courier_count || 0)
  summary.active_courier_count = Number(payload.active_courier_count || 0)
  summary.vehicle_count = Number(payload.vehicle_count || 0)
  summary.active_vehicle_count = Number(payload.active_vehicle_count || 0)
}

function getTabBadge(tab) {
  if (tab === 'couriers') return toFa(summary.courier_count)
  if (tab === 'fleet') return toFa(summary.vehicle_count)
  return ''
}

function resetCourierForm() {
  Object.assign(courierForm, createCourierForm())
}

function resetVehicleForm() {
  Object.assign(vehicleForm, createVehicleForm())
}

function editCourier(row) {
  Object.assign(courierForm, {
    ...createCourierForm(),
    ...row,
    is_active: Boolean(row.is_active),
  })
}

function editVehicle(row) {
  Object.assign(vehicleForm, {
    ...createVehicleForm(),
    ...row,
    courier: row.courier || '',
    is_primary: Boolean(row.is_primary),
    is_active: Boolean(row.is_active),
  })
}

async function loadCouriers() {
  const payload = await listManagementCouriers({ search: courierSearch.value })
  couriers.value = Array.isArray(payload?.couriers) ? payload.couriers : []
  assignSummary(payload?.summary || {})
}

async function loadVehicles() {
  const payload = await listManagementCourierVehicles({ search: vehicleSearch.value })
  vehicles.value = Array.isArray(payload?.vehicles) ? payload.vehicles : []
  assignSummary(payload?.summary || {})
}

async function loadAll() {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await Promise.all([loadCouriers(), loadVehicles()])
  } catch (errObj) {
    error.value = errObj?.message || 'بارگذاری اطلاعات پیک‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function saveCourier() {
  savingCourier.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await saveManagementCourier({ ...courierForm, is_active: courierForm.is_active ? 1 : 0 })
    successMessage.value = 'پیک با موفقیت ذخیره شد.'
    resetCourierForm()
    await loadAll()
  } catch (errObj) {
    error.value = errObj?.message || 'ذخیره پیک ناموفق بود.'
  } finally {
    savingCourier.value = false
  }
}

async function saveVehicle() {
  savingVehicle.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await saveManagementCourierVehicle({
      ...vehicleForm,
      is_primary: vehicleForm.is_primary ? 1 : 0,
      is_active: vehicleForm.is_active ? 1 : 0,
    })
    successMessage.value = 'وسیله با موفقیت ذخیره شد.'
    resetVehicleForm()
    await loadAll()
  } catch (errObj) {
    error.value = errObj?.message || 'ذخیره وسیله ناموفق بود.'
  } finally {
    savingVehicle.value = false
  }
}

async function removeCourier(name) {
  if (!window.confirm('این پیک حذف شود؟')) return
  error.value = ''
  successMessage.value = ''
  try {
    await deleteManagementCourier(name)
    successMessage.value = 'پیک حذف شد.'
    resetCourierForm()
    await loadAll()
  } catch (errObj) {
    error.value = errObj?.message || 'حذف پیک ناموفق بود.'
  }
}

async function removeVehicle(name) {
  if (!window.confirm('این وسیله حذف شود؟')) return
  error.value = ''
  successMessage.value = ''
  try {
    await deleteManagementCourierVehicle(name)
    successMessage.value = 'وسیله حذف شد.'
    resetVehicleForm()
    await loadAll()
  } catch (errObj) {
    error.value = errObj?.message || 'حذف وسیله ناموفق بود.'
  }
}

function toFa(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

// ---------------------------------------------------------------------------
// Delivery zones (geo radius) + third-party providers
// ---------------------------------------------------------------------------
const zones = ref([])
const savingZone = ref(false)
const zoneForm = reactive(createZoneForm())
const zoneCheck = reactive({ lat: null, lng: null })
const zoneChecking = ref(false)
const zoneCheckResult = ref(null)
const providerForm = reactive({ provider: '', token: '', base_url: '', token_set: false, zone_control_enabled: false })
const providerOptions = ref([])
const savingProvider = ref(false)
const dispatchForm = reactive({ order_name: '' })
const dispatching = ref(false)
const dispatchResult = ref('')

const zoneColumns = [
  { key: 'zone_name', label: 'محدوده' },
  { key: 'center', label: 'مرکز' },
  { key: 'radius_km', label: 'شعاع' },
  { key: 'delivery_fee', label: 'هزینه ارسال' },
  { key: 'min_order_amount', label: 'حداقل سفارش' },
  { key: 'is_active', label: 'وضعیت' },
]

function createZoneForm() {
  return {
    name: '',
    zone_name: '',
    center_lat: null,
    center_lng: null,
    radius_km: 3,
    delivery_fee: 0,
    min_order_amount: 0,
    is_active: true,
    notes: '',
  }
}

function resetZoneForm() {
  Object.assign(zoneForm, createZoneForm())
}

function editZone(row) {
  Object.assign(zoneForm, {
    ...createZoneForm(),
    ...row,
    is_active: Boolean(row.is_active),
  })
}

async function loadZones() {
  const payload = await listManagementDeliveryZones({ include_inactive: 1 })
  zones.value = Array.isArray(payload?.zones) ? payload.zones : []
}

async function saveZone() {
  savingZone.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await saveManagementDeliveryZone({ ...zoneForm, is_active: zoneForm.is_active ? 1 : 0 })
    successMessage.value = 'محدوده سفارش‌گیری ذخیره شد.'
    resetZoneForm()
    await loadZones()
  } catch (errObj) {
    error.value = errObj?.message || 'ذخیره محدوده ناموفق بود.'
  } finally {
    savingZone.value = false
  }
}

async function removeZone(name) {
  if (!window.confirm('این محدوده حذف شود؟')) return
  error.value = ''
  successMessage.value = ''
  try {
    await deleteManagementDeliveryZone(name)
    successMessage.value = 'محدوده حذف شد.'
    resetZoneForm()
    await loadZones()
  } catch (errObj) {
    error.value = errObj?.message || 'حذف محدوده ناموفق بود.'
  }
}

async function runZoneCheck() {
  zoneChecking.value = true
  zoneCheckResult.value = null
  try {
    zoneCheckResult.value = await checkManagementDeliveryPoint({ lat: zoneCheck.lat, lng: zoneCheck.lng })
  } catch (errObj) {
    zoneCheckResult.value = { allowed: false, matches: [] }
    error.value = errObj?.message || 'بررسی محدوده ناموفق بود.'
  } finally {
    zoneChecking.value = false
  }
}

async function loadProviderSettings() {
  const payload = await getManagementDeliveryProviderSettings()
  providerForm.provider = payload?.provider || ''
  providerForm.token_set = !!payload?.token_set
  providerForm.base_url = payload?.base_url || ''
  providerForm.token = ''
  providerForm.zone_control_enabled = !!payload?.zone_control_enabled
  providerOptions.value = Array.isArray(payload?.providers) ? payload.providers : []
}

async function saveProviderSettings() {
  savingProvider.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = { provider: providerForm.provider, base_url: providerForm.base_url, zone_control_enabled: providerForm.zone_control_enabled ? 1 : 0 }
    if (providerForm.token) payload.token = providerForm.token
    await setManagementDeliveryProviderSettings(payload)
    providerForm.token = ''
    providerForm.token_set = true
    successMessage.value = 'تنظیمات پلتفرم دیسپچ ذخیره شد.'
  } catch (errObj) {
    error.value = errObj?.message || 'ذخیره تنظیمات پلتفرم ناموفق بود.'
  } finally {
    savingProvider.value = false
  }
}

async function runDispatch() {
  dispatching.value = true
  dispatchResult.value = ''
  error.value = ''
  try {
    const payload = await dispatchManagementDeliveryProvider({ order_name: dispatchForm.order_name })
    dispatchResult.value = `ثبت شد — مرجع: ${payload?.reference || '-'}`
    dispatchForm.order_name = ''
  } catch (errObj) {
    error.value = errObj?.message || 'دیسپچ سفارش ناموفق بود.'
  } finally {
    dispatching.value = false
  }
}

onMounted(() => {
  loadAll()
  loadZones()
  loadProviderSettings()
})
</script>

<style scoped>
.panel-grid {
  display: grid;
  gap: 20px;
}

.section-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.simple-tabs {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  flex-wrap: wrap;
}

.simple-tab {
  min-height: 2.75rem;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--text-muted, var(--mg-text-muted));
  padding: 0.34rem 0.68rem;
  font-size: 0.78rem;
  font-weight: 850;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.34rem;
  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
  touch-action: manipulation;
}

.simple-tab:active {
  transform: scale(0.98);
}

.simple-tab.active {
  background: var(--surface-raised, #fff);
  color: var(--brand-600, #8b5e3c);
  border-color: rgb(139 94 60 / 0.2);
  box-shadow: 0 8px 18px rgb(15 23 42 / 0.06);
}

.tab-badge {
  min-width: 1.32rem;
  min-height: 1.32rem;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  padding: 0 0.34rem;
  background: rgb(139 94 60 / 0.1);
  color: inherit;
  font-size: 0.72rem;
  font-weight: 800;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  border: 1px solid var(--border-color, var(--mg-border-light));
  border-radius: 8px;
  padding: 14px;
  display: grid;
  gap: 6px;
}

.summary-card small {
  color: var(--text-muted, var(--mg-text-muted));
}

.summary-card strong {
  font-size: 22px;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rule-card {
  border: 1px solid var(--border-color, var(--mg-border-light));
  border-radius: 8px;
  padding: 14px;
  display: grid;
  gap: 8px;
  background: var(--surface-raised, #fff);
}

.rule-card p {
  margin: 0;
  color: var(--text-muted, var(--mg-text-muted));
  line-height: 1.8;
}

.rules-note {
  margin-top: 14px;
  border: 1px dashed var(--border-color, var(--mg-border-light));
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.toolbar-row,
.form-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.editor-grid label,
.full-width {
  display: grid;
  gap: 6px;
  color: var(--text-muted, var(--mg-text-muted));
  font-size: 13px;
}

.full-width {
  margin-bottom: 14px;
}

.check-row {
  display: flex !important;
  align-items: center;
  gap: 8px;
}

.mini-link-btn {
  background: transparent;
  border: 0;
  color: var(--brand-600, #8b5e3c);
  cursor: pointer;
  font: inherit;
  padding: 0;
}

@media (max-width: 900px) {
  .summary-grid,
  .editor-grid,
  .rules-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .section-picker {
    flex-direction: column;
    align-items: stretch;
  }

  .section-picker > .secondary-btn {
    width: 100%;
    justify-content: center;
  }

  .simple-tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.2rem;
    scrollbar-width: thin;
  }

  .simple-tab {
    flex: 0 0 auto;
    white-space: nowrap;
  }
}
.zone-check,
.dispatch-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color, #e5dfd2);
  font-size: 0.85rem;
}
.zone-check .input,
.dispatch-box .input {
  width: auto;
  min-width: 130px;
}
.route-list {
  margin-top: 12px;
  display: grid;
  gap: 6px;
}
.route-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border-color, #e5dfd2);
  background: var(--surface-soft, #f7f3ea);
  font-size: 0.85rem;
}
.route-item > div {
  display: grid;
  gap: 2px;
  flex: 1;
}

.route-item select.input,
.route-item .input {
  width: auto;
  min-width: 0;
  padding: 6px 9px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #ded5c4);
  background: var(--surface-card, #fff);
  font-size: 0.82rem;
}
.route-index {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--mg-primary, #c97852);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 0.8rem;
  flex-shrink: 0;
}
.zone-check-result,
.provider-hint {
  font-size: 0.85rem;
}
.zone-toggle {
  font-size: 0.85rem;
}
.muted {
  color: var(--text-muted, #6b7a72);
}
.link-code {
  direction: ltr;
  display: inline-block;
  background: var(--surface-soft, #f0ede4);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.8rem;
}
.ok-text {
  color: var(--accent-green, #2f6f5c);
}
.warn-text {
  color: #b84f4f;
}
</style>
