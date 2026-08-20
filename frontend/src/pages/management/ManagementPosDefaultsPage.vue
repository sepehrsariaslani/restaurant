<template>
  <ManagementBreadcrumbs class="page-breadcrumbs" :items="breadcrumbItems" />
  <ManagementPageScaffold title="پیش‌فرض‌های POS" subtitle="تنظیمات پیش‌فرض صندوق فروش: مشتری، جایگاه، پرداخت و چاپ">
    <template #actions>
      <button class="secondary-btn" type="button" @click="loadConfig" :disabled="loading">
        {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
      </button>
    </template>

    <p class="error" v-if="error">{{ error }}</p>

    <!-- ─── اطلاعات کلی ─── -->
    <ManagementSurfaceCard
      v-if="!loading"
      class="product-general-card product-general-card--compact"
      title="اطلاعات کلی"
      subtitle="خلاصه وضعیت پیش‌فرض‌های صندوق"
    >
      <div class="product-general-layout">
        <aside class="product-general-media" aria-label="وضعیت پیش‌فرض‌ها">
          <div class="general-image-shell pos-general-shell">
            <Settings2 :size="30" :stroke-width="1.6" />
          </div>
        </aside>

        <div class="product-general-main">
          <div class="product-general-fields">
            <div class="pg-status-row">
              <span class="pg-status-pill is-on">نوع سفارش: {{ currentModeLabel }}</span>
              <span class="pg-status-pill is-code" :title="'روش پرداخت پیش‌فرض'">
                پرداخت: {{ paymentLabel }}
              </span>
              <span class="pg-status-pill" :class="printProfiles.length > 1 ? 'is-soon' : 'is-off'">
                {{ printProfiles.length }} پروفایل چاپ
              </span>
              <span class="pg-status-pill is-warn" v-if="!printProfiles.length">چاپ تنظیم نشده</span>
            </div>

            <label class="pg-name-field">
              نوع سفارش پیش‌فرض
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
              <small class="field-help">هنگام باز کردن فاکتور جدید، کدام حالت به صورت پیش‌فرض انتخاب شود.</small>
            </label>
          </div>
        </div>
      </div>
    </ManagementSurfaceCard>

    <!-- ─── انتخاب بخش ─── -->
    <ManagementSurfaceCard tone="soft" class="section-picker-shell">
      <div class="section-picker">
        <div class="simple-tabs" role="tablist" aria-label="بخش‌های تنظیمات POS">
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
        <button class="secondary-btn" type="button" @click="loadConfig" :disabled="loading">
          {{ loading ? 'در حال بروزرسانی...' : 'تازه‌سازی' }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری تنظیمات...</p>

    <!-- ─── مشتری پیش‌فرض ─── -->
    <template v-if="activeTab === 'general'">
      <ManagementSurfaceCard title="مشتری پیش‌فرض" subtitle="برای هر نوع سفارش، مشتری پیش‌فرض را مشخص کنید">
        <div class="identity-grid">
          <label v-for="mode in orderModes" :key="mode.value">
            <span class="field-label">{{ mode.label }}</span>
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
            <small class="field-help" v-if="localConfig.default_customers[mode.value]?.name">
              {{ localConfig.default_customers[mode.value].name }}
              {{ localConfig.default_customers[mode.value].mobile ? ` - ${localConfig.default_customers[mode.value].mobile}` : '' }}
            </small>
            <small class="field-help" v-else>با فاکتور جدید، «مشتری POS» به عنوان مشتری ثبت می‌شود.</small>
          </label>
        </div>
      </ManagementSurfaceCard>
    </template>

    <!-- ─── جایگاه‌ها و پیک ─── -->
    <template v-if="activeTab === 'places'">
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
    </template>

    <!-- ─── پرداخت ─── -->
    <template v-if="activeTab === 'payment'">
      <ManagementSurfaceCard title="روش پرداخت پیش‌فرض" subtitle="روش پرداخت اصلی را برای فاکتورهای جدید POS انتخاب کنید">
        <div class="payment-default-settings">
          <label>
            روش پرداخت اصلی
            <SearchableDropdown
              v-model="localConfig.default_payment_option"
              :options="paymentOptions"
              placeholder="انتخاب روش پرداخت"
              search-placeholder="جستجوی روش پرداخت..."
            />
          </label>
          <p class="muted hint" v-if="!paymentOptions.length">روش پرداختی از پروفایل POS دریافت نشد؛ ابتدا روش‌های پرداخت پروفایل را تنظیم کنید.</p>
          <p class="muted hint" v-else>این انتخاب در فرم تسویه به‌عنوان روش اصلی پیشنهاد می‌شود و همچنان قابل تغییر است.</p>
        </div>
      </ManagementSurfaceCard>
    </template>

    <!-- ─── چاپ و پرینترها ─── -->
    <template v-if="activeTab === 'print'">
      <ManagementSurfaceCard
        title="چاپ و پرینترها"
        subtitle="پروفایل‌های چاپ: چاپ مشتری (با قیمت)، آشپزخانه و بار (بدون قیمت) برای گروه‌های محصول انتخابی"
      >
        <div class="print-profiles">
          <p class="muted hint">
            هر پروفایل یک «دستور چاپ» جداگانه است. هنگام ثبت و تسویه فاکتور، چاپ مشتری (فیش عادی) و
            برای هر پروفایل آشپزخانه/بار فعال، یک چاپ جداگانه ارسال می‌شود که فقط آیتم‌های همان گروه‌ها را
            دارد و قیمت نمایش نمی‌دهد. با «چاپ تست» هر پروفایل، پرینتر مقصد را یکبار انتخاب کنید؛ مرورگر انتخاب را برای دفعات بعد حفظ می‌کند.
          </p>

          <div v-if="!printProfiles.length" class="muted empty-state">
            هنوز پروفایل چاپی تعریف نشده است. با دکمه زیر یک پروفایل اضافه کنید.
          </div>

          <div
            v-for="(profile, idx) in printProfiles"
            :key="profile.profile_id"
            class="print-profile-card"
            :class="{ 'profile-disabled': !profile.enabled }"
          >
            <header class="print-profile-head">
              <div class="print-profile-title">
                <strong>{{ profile.label || 'پروفایل چاپ' }}</strong>
                <span class="print-kind-badge" :class="`kind-${profile.kind}`">
                  {{ printKindLabel(profile.kind) }}
                </span>
                <span v-if="!profile.enabled" class="print-kind-badge kind-off">غیرفعال</span>
              </div>
              <div class="print-profile-actions">
                <label class="print-enable-toggle" title="فعال/غیرفعال">
                  <input type="checkbox" v-model="profile.enabled" />
                  فعال
                </label>
                <button
                  type="button"
                  class="secondary-btn print-test-btn"
                  title="یک فیش آزمایشی به این پرینتر بفرست"
                  @click="testPrintProfile(profile)"
                >
                  چاپ تست
                </button>
                <button
                  v-if="profile.kind !== 'customer'"
                  type="button"
                  class="ghost-btn danger"
                  title="حذف پروفایل"
                  @click="removePrintProfile(idx)"
                >×</button>
              </div>
            </header>

            <div class="print-profile-fields">
              <label>
                نام پروفایل
                <input class="input" v-model="profile.label" placeholder="مثلاً: چاپ آشپزخانه" />
              </label>
              <label>
                نوع چاپ
                <select class="input" v-model="profile.kind" :disabled="profile.kind === 'customer'">
                  <option value="customer">مشتری (فیش عادی با قیمت)</option>
                  <option value="kitchen">آشپزخانه (بدون قیمت)</option>
                  <option value="bar">بار (بدون قیمت)</option>
                </select>
              </label>
              <label>
                نام پرینتر
                <input
                  class="input"
                  v-model="profile.printer_name"
                  placeholder="مثلاً: EPSON-TM20 / Kitchen Printer"
                />
              </label>
              <label class="print-price-toggle" v-if="profile.kind !== 'customer'">
                <input type="checkbox" v-model="profile.show_prices" />
                نمایش قیمت در این چاپ
              </label>
            </div>

            <div class="print-groups">
              <span class="print-groups-label">گروه‌های محصول برای این چاپ:</span>
              <div class="print-groups-chips">
                <button
                  v-for="group in printItemGroups"
                  :key="group.name"
                  type="button"
                  class="print-group-chip"
                  :class="{ active: isGroupSelected(profile, group.name) }"
                  @click="toggleGroup(profile, group.name)"
                >
                  {{ group.title }}
                </button>
                <span v-if="!printItemGroups.length" class="muted">گروه محصولی یافت نشد.</span>
              </div>
              <p v-if="profile.kind !== 'customer' && !profile.item_groups.length" class="muted hint">
                هنوز گروهی انتخاب نشده — این چاپ فقط وقتی ارسال می‌شود که حداقل یکی از آیتم‌های فاکتور در این گروه‌ها باشد.
              </p>
            </div>
          </div>

          <button type="button" class="secondary-btn" @click="addPrintProfile">+ افزودن پروفایل چاپ</button>
        </div>
      </ManagementSurfaceCard>
    </template>

    <!-- ─── نوار ذخیره ─── -->
    <div class="sticky-save-bar" :class="{ 'is-dirty': hasUnsavedChanges }" role="status" aria-live="polite">
      <div v-if="hasUnsavedChanges">
        <strong>تغییرات ذخیره نشده دارید</strong>
        <small>با Ctrl/⌘ + S هم می‌توانید ذخیره کنید.</small>
      </div>
      <button class="primary-btn save-spark-btn" type="button" @click="saveConfig" :disabled="saving">
        {{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}
      </button>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Settings2 } from 'lucide-vue-next'
import ManagementBreadcrumbs from '@/components/management/ManagementBreadcrumbs.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
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
const paymentOptions = ref([])
const printProfiles = ref([])
const printItemGroups = ref([])
let printProfileSeq = 1

const activeTab = ref('general')

const tabOptions = [
  { value: 'general', label: 'عمومی' },
  { value: 'places', label: 'جایگاه‌ها و پیک' },
  { value: 'payment', label: 'پرداخت' },
  { value: 'print', label: 'چاپ' },
]

const breadcrumbItems = [
  { label: 'مدیریت', href: '/management' },
  { label: 'پیش‌فرض‌های POS' },
]

const orderModes = [
  { value: 'dine_in', label: 'سالن' },
  { value: 'takeaway', label: 'بیرون بر (مشتری)' },
  { value: 'delivery', label: 'بیرون بر (پیک)' },
]

const currentModeLabel = computed(() => {
  const mode = orderModes.find((m) => m.value === localConfig.default_order_mode)
  return mode?.label || 'سالن'
})

const paymentLabel = computed(() => {
  const value = String(localConfig.default_payment_option || localConfig.default_payment_method || '').trim()
  return value || '—'
})

function getTabBadge(tabValue) {
  if (tabValue === 'print') {
    const count = printProfiles.value.length
    return count ? count.toLocaleString('fa-IR') : ''
  }
  if (tabValue === 'places') {
    return localConfig.takeaway_places.length.toLocaleString('fa-IR')
  }
  return ''
}

const localConfig = reactive({
  default_order_mode: 'dine_in',
  default_customers: {
    dine_in: { name: 'POS Customer', mobile: '' },
    takeaway: { name: 'POS Customer', mobile: '' },
    delivery: { name: 'POS Customer', mobile: '' },
  },
  takeaway_places: ['بیرون بر حضوری', 'تحویل کنار سالن'],
  default_takeaway_place: 'بیرون بر حضوری',
  delivery_places: ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس'],
  default_delivery_place: 'پیک 1',
  default_delivery_courier: '',
  default_payment_option: '',
  default_payment_method: 'cash',
})

// تشخیص تغییرات ذخیره‌نشده
const hasUnsavedChanges = ref(false)
let dirtyTimer = null
function markDirty() {
  if (dirtyTimer) clearTimeout(dirtyTimer)
  dirtyTimer = setTimeout(() => {
    hasUnsavedChanges.value = true
  }, 60)
}
watch(localConfig, markDirty, { deep: true })
watch(printProfiles, markDirty, { deep: true })

function onWindowKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && String(event.key).toLowerCase() === 's') {
    event.preventDefault()
    if (!saving.value) {
      saveConfig()
    }
  }
}

function printKindLabel(kind) {
  if (kind === 'customer') return 'مشتری'
  if (kind === 'bar') return 'بار'
  return 'آشپزخانه'
}

function defaultPrintProfiles() {
  return [
    {
      profile_id: `print-customer`,
      label: 'چاپ مشتری',
      kind: 'customer',
      printer_name: '',
      item_groups: [],
      show_prices: true,
      enabled: true,
    },
  ]
}

function addPrintProfile() {
  const seq = printProfileSeq++
  printProfiles.value.push({
    profile_id: `print-profile-${Date.now()}-${seq}`,
    label: seq === 1 ? 'چاپ آشپزخانه' : `چاپ ${seq === 2 ? 'بار' : `پروفایل ${seq}`}`,
    kind: seq === 2 ? 'bar' : 'kitchen',
    printer_name: '',
    item_groups: [],
    show_prices: false,
    enabled: true,
  })
}

function removePrintProfile(idx) {
  const profile = printProfiles.value[idx]
  if (profile?.kind === 'customer') {
    return
  }
  printProfiles.value.splice(idx, 1)
}

// چاپ آزمایشی برای هر پروفایل: یک فیش تست ارسال می‌کند تا پرینتر مقصد را یکبار انتخاب کنی
// (مرورگر انتخاب را برای دفعات بعد به خاطر می‌سپارد)
function testPrintProfile(profile) {
  const kindLabel = printKindLabel(profile?.kind || 'kitchen')
  const printerName = String(profile?.printer_name || '').trim()
  const now = new Date()
  const dateLabel = now.toLocaleDateString('fa-IR')
  const timeLabel = now.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })
  const groupNames = (profile?.item_groups || []).join('، ') || 'همه'

  const html = `
    <!doctype html>
    <html lang="fa" dir="rtl">
      <head>
        <meta charset="utf-8" />
        <title>${(printerName || `چاپ ${kindLabel}`).replace(/[<>&"]/g, '')}</title>
        <style>
          @page { size: 80mm auto; margin: 3mm; }
          html, body { margin: 0; padding: 0; direction: rtl; font-family: Tahoma, Arial, sans-serif; color: #222; }
          .sheet { width: 74mm; margin: 0 auto; padding: 4mm 0; font-size: 12px; line-height: 1.6; }
          .title { text-align: center; font-size: 15px; font-weight: 800; margin-bottom: 4px; }
          .meta { text-align: center; font-size: 10px; color: #666; margin: 1px 0; }
          .sep { border-top: 1px dashed #999; margin: 6px 0; }
          .row { display: flex; justify-content: space-between; gap: 6px; font-size: 11px; }
          .footer { text-align: center; font-size: 10px; color: #666; margin-top: 8px; border-top: 1px dashed #999; padding-top: 4px; }
        </style>
      </head>
      <body>
        <div class="sheet">
          <div class="title">چاپ تست — ${kindLabel}</div>
          ${printerName ? `<div class="meta">پرینتر: ${printerName}</div>` : ''}
          <div class="meta">${dateLabel} — ${timeLabel}</div>
          <div class="sep"></div>
          <div class="row"><span>آیتم آزمایشی ۱</span><span>× ۱</span></div>
          <div class="row"><span>آیتم آزمایشی ۲</span><span>× ۲</span></div>
          <div class="sep"></div>
          <div class="row"><span>گروه‌های این پروفایل:</span></div>
          <div class="meta">${groupNames}</div>
          <div class="footer">این فیش آزمایشی است — اگر روی پرینتر درست چاپ شد، پروفایل آماده است</div>
        </div>
      </body>
    </html>
  `

  try {
    const frame = document.createElement('iframe')
    frame.style.position = 'fixed'
    frame.style.insetInlineStart = '-10000px'
    frame.style.bottom = '0'
    frame.style.width = '1px'
    frame.style.height = '1px'
    frame.style.border = '0'
    frame.setAttribute('aria-hidden', 'true')
    document.body.appendChild(frame)
    const frameDoc = frame.contentDocument
    if (!frameDoc) {
      frame.remove()
      error.value = 'ارسال دستور چاپ ممکن نشد.'
      return
    }
    frameDoc.open()
    frameDoc.write(html)
    frameDoc.close()
    window.setTimeout(() => {
      try {
        frame.contentWindow?.focus?.()
        frame.contentWindow?.print()
      } catch (printError) {
        console.error(printError)
      }
      window.setTimeout(() => frame.remove(), 1200)
    }, 400)
  } catch (err) {
    error.value = 'ارسال دستور چاپ ممکن نشد.'
  }
}

function isGroupSelected(profile, groupName) {
  return (profile.item_groups || []).includes(groupName)
}

function toggleGroup(profile, groupName) {
  if (!profile.item_groups) {
    profile.item_groups = []
  }
  const idx = profile.item_groups.indexOf(groupName)
  if (idx === -1) {
    profile.item_groups.push(groupName)
  } else {
    profile.item_groups.splice(idx, 1)
  }
}

function applyConfig(cfg) {
  if (!cfg) return
  localConfig.default_order_mode = cfg.default_order_mode || 'dine_in'
  localConfig.default_customers = {
    dine_in: { name: 'POS Customer', mobile: '', ...(cfg.default_customers?.dine_in || {}) },
    takeaway: { name: 'POS Customer', mobile: '', ...(cfg.default_customers?.takeaway || {}) },
    delivery: { name: 'POS Customer', mobile: '', ...(cfg.default_customers?.delivery || {}) },
  }
  localConfig.takeaway_places = Array.isArray(cfg.takeaway_places) ? [...cfg.takeaway_places] : ['بیرون بر حضوری', 'تحویل کنار سالن']
  localConfig.default_takeaway_place = cfg.default_takeaway_place || (localConfig.takeaway_places[0] || '')
  localConfig.delivery_places = Array.isArray(cfg.delivery_places) ? [...cfg.delivery_places] : ['پیک 1', 'پیک 2', 'پیک 3', 'ارسال اکسپرس']
  localConfig.default_delivery_place = cfg.default_delivery_place || (localConfig.delivery_places[0] || '')
  localConfig.default_delivery_courier = cfg.default_delivery_courier || ''
  localConfig.default_payment_option = cfg.default_payment_option || ''
  localConfig.default_payment_method = cfg.default_payment_method || 'cash'
  paymentOptions.value = (cfg.payment_options || [])
    .map((row) => {
      const value = String(row?.mode_of_payment || row?.payment_method || row?.name || '').trim()
      return value ? { value, label: value } : null
    })
    .filter(Boolean)
  printItemGroups.value = Array.isArray(cfg.print_item_groups) ? cfg.print_item_groups : []
  const storedProfiles = Array.isArray(cfg.print_profiles) ? cfg.print_profiles : []
  if (storedProfiles.length) {
    printProfiles.value = storedProfiles.map((profile, index) => ({
      profile_id: profile.profile_id || `print-${index}-${Date.now()}`,
      label: profile.label || 'پروفایل چاپ',
      kind: profile.kind || 'kitchen',
      printer_name: profile.printer_name || '',
      item_groups: Array.isArray(profile.item_groups) ? [...profile.item_groups] : [],
      show_prices: Boolean(profile.show_prices),
      enabled: profile.enabled !== 0,
    }))
  } else {
    printProfiles.value = defaultPrintProfiles()
  }
  hasUnsavedChanges.value = false
}

async function loadConfig() {
  error.value = ''
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
      default_payment_option: localConfig.default_payment_option,
      default_payment_method: localConfig.default_payment_method,
      print_profiles: printProfiles.value.map((profile) => ({
        profile_id: profile.profile_id,
        label: profile.label || '',
        kind: profile.kind || 'kitchen',
        printer_name: profile.printer_name || '',
        item_groups: profile.item_groups || [],
        show_prices: Boolean(profile.show_prices),
        enabled: profile.enabled ? 1 : 0,
      })),
    }
    await setManagementPOSConfig(payload)
    hasUnsavedChanges.value = false
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
  window.addEventListener('keydown', onWindowKeydown)
  Promise.all([loadConfig(), loadDirectoryData()]).catch((err) => {
    error.value = String(err?.message || err || 'خطا در بارگذاری داده‌ها')
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onWindowKeydown)
  if (dirtyTimer) clearTimeout(dirtyTimer)
})
</script>

<style scoped>
.page-breadcrumbs {
  margin-bottom: 0.35rem;
  padding-inline: 0.15rem;
}

/* ─── اطلاعات کلی (مثل صفحه جزئیات محصول) ─── */
.product-general-layout {
  display: grid;
  grid-template-columns: minmax(108px, 0.5fr) minmax(360px, 1.5fr);
  gap: 0.72rem;
  align-items: center;
}

.pos-general-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface) 92%);
  border: 1px dashed color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  border-radius: 14px;
}

.product-general-fields {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.52rem;
  align-content: start;
}

.product-general-fields label {
  display: grid;
  gap: 0.24rem;
  color: var(--mg-text-muted);
  font-size: 0.8rem;
  font-weight: 800;
  min-width: 0;
}

.pg-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.pg-status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.14rem 0.55rem;
  font-size: 0.66rem;
  font-weight: 800;
  white-space: nowrap;
}

.pg-status-pill.is-on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
}

.pg-status-pill.is-off {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent);
}

.pg-status-pill.is-soon {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.pg-status-pill.is-warn {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
}

.pg-status-pill.is-code {
  direction: ltr;
  color: var(--mg-text-muted);
  background: var(--mg-bg-soft);
  font-weight: 600;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-text-muted);
}

.field-help {
  font-size: 0.72rem;
  color: var(--mg-text-muted);
  opacity: 0.9;
  font-weight: 400;
}

/* ─── انتخاب بخش ─── */
.section-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 0.75rem;
  border-radius: var(--mg-radius-md);
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-sm);
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
  color: var(--mg-text-muted);
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

.simple-tab:hover {
  background: color-mix(in srgb, var(--mg-primary) 6%, transparent);
  color: var(--mg-text-main);
}

.simple-tab.active {
  background: color-mix(in srgb, var(--mg-primary) 13%, transparent);
  border-color: color-mix(in srgb, var(--mg-primary) 30%, transparent);
  color: var(--mg-primary);
}

.tab-badge {
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.3rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 14%, transparent);
  color: var(--mg-primary);
  font-size: 0.64rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* ─── فرم‌ها ─── */
.identity-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.5rem;
}

.identity-grid label {
  display: grid;
  gap: 0.22rem;
  color: var(--mg-text-muted);
  font-size: 0.78rem;
  font-weight: 700;
  min-width: 0;
}

@media (max-width: 900px) {
  .identity-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .identity-grid {
    grid-template-columns: 1fr;
  }
  .product-general-layout {
    grid-template-columns: 1fr;
  }
  .pos-general-shell {
    min-height: 90px;
  }
}

/* ─── نوار ذخیره پایین ─── */
.sticky-save-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 13000;
  margin: 0;
  width: 100%;
  border: none;
  border-top: 1px solid color-mix(in srgb, var(--mg-primary) 24%, transparent);
  border-radius: 0;
  background: color-mix(in srgb, var(--mg-bg-surface) 94%, transparent);
  backdrop-filter: blur(18px);
  box-shadow: 0 -12px 40px rgb(0 0 0 / 0.14);
  padding: 0.6rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
}

.sticky-save-bar:not(.is-dirty) {
  border-color: var(--mg-border-light);
  box-shadow: 0 12px 40px rgb(0 0 0 / 0.12);
  justify-content: flex-end;
}

.sticky-save-bar:not(.is-dirty) .save-spark-btn {
  opacity: 0.75;
}

.sticky-save-bar > div {
  display: grid;
  gap: 0.1rem;
}

.sticky-save-bar strong {
  color: var(--mg-text-main);
  font-size: 0.84rem;
}

.sticky-save-bar small {
  color: var(--mg-text-muted);
  font-size: 0.72rem;
}

/* ─── حالت‌ها ─── */
.mode-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mode-btn {
  padding: 0.4rem 0.9rem;
  border: 2px solid var(--mg-border-light);
  border-radius: 999px;
  background: var(--mg-bg-surface);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 700;
  font-family: inherit;
  color: var(--mg-text-muted);
  transition: all 0.18s;
}
.mode-btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
}
.mode-btn.active {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 13%, transparent);
  color: var(--mg-primary);
}

/* ─── پرداخت ─── */
.payment-default-settings {
  display: grid;
  gap: 0.45rem;
  max-width: 520px;
}

.payment-default-settings > label {
  display: grid;
  gap: 0.3rem;
  color: var(--mg-text-main);
  font-size: 0.8rem;
  font-weight: 800;
}

.payment-default-settings :deep(.searchable-dropdown) {
  width: 100%;
}

/* ─── جایگاه‌ها ─── */
.places-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 560px;
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
  color: var(--mg-danger);
}
.default-place-select {
  display: grid;
  gap: 6px;
  margin-top: 8px;
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
.error {
  margin: 0;
}
.muted {
  color: var(--mg-text-muted);
}

/* ─── پروفایل‌های چاپ ─── */
.print-profiles {
  display: grid;
  gap: 0.8rem;
}

.empty-state {
  font-size: 0.8rem;
}

.print-profile-card {
  border: 1px solid var(--mg-border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-card, var(--mg-bg-surface)) 95%, transparent);
  padding: 0.75rem 0.85rem;
  display: grid;
  gap: 0.6rem;
}

.print-profile-card.profile-disabled {
  opacity: 0.72;
}

.print-profile-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.print-profile-title {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
}

.print-kind-badge {
  font-size: 0.66rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 0.08rem 0.5rem;
  background: var(--mg-bg-soft, #eef0e8);
  color: var(--mg-text-muted);
}

.print-kind-badge.kind-customer {
  background: color-mix(in srgb, var(--mg-primary) 14%, transparent);
  color: var(--mg-primary);
}

.print-kind-badge.kind-kitchen {
  background: color-mix(in srgb, var(--mg-olive, #8a8b63) 16%, transparent);
  color: var(--mg-olive, #8a8b63);
}

.print-kind-badge.kind-bar {
  background: color-mix(in srgb, var(--mg-success, #6f7b56) 16%, transparent);
  color: var(--mg-success, #6f7b56);
}

.print-kind-badge.kind-off {
  background: var(--mg-bg-soft, #eee);
  color: var(--mg-text-muted);
}

.print-profile-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.print-enable-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  color: var(--mg-text-muted);
  cursor: pointer;
}

.print-test-btn {
  font-size: 0.7rem;
  padding: 0.15rem 0.55rem;
  border-radius: 7px;
}

.print-profile-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.55rem;
}

.print-profile-fields label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--mg-text-muted);
}

.print-price-toggle {
  display: inline-flex !important;
  align-items: center;
  gap: 0.4rem;
  align-self: end;
  padding-bottom: 0.45rem;
  cursor: pointer;
}

.print-groups {
  display: grid;
  gap: 0.4rem;
}

.print-groups-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--mg-text-muted);
}

.print-groups-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.print-group-chip {
  border: 1px solid var(--mg-border);
  background: transparent;
  color: var(--mg-text-main);
  font-size: 0.7rem;
  font-family: inherit;
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.print-group-chip:hover {
  background: color-mix(in srgb, var(--mg-primary) 7%, transparent);
}

.print-group-chip.active {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 14%, transparent);
  color: var(--mg-primary);
  font-weight: 700;
}
</style>
