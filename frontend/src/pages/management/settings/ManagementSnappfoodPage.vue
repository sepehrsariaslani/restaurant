<template>
  <ManagementBreadcrumbs class="page-breadcrumbs" :items="breadcrumbItems" />
  <ManagementPageScaffold
    title="اتصال Food Partner"
    subtitle="نگاشت منوی اسنپ‌فود و ورود سفارش‌ها به همان سفارش فروش و فاکتور POS"
  >
    <template #actions>
      <button class="secondary-btn" type="button" @click="loadConfig" :disabled="loading || testingConnection">تازه‌سازی</button>
      <button class="secondary-btn" type="button" @click="testConnection" :disabled="testingConnection || !status.schema_ready">{{ testingConnection ? 'در حال تست...' : 'تست اتصال' }}</button>
      <a class="secondary-btn" href="https://partner.snappfood.ir/" target="_blank" rel="noopener noreferrer">ورود به پنل Partner</a>
      <a class="secondary-btn" href="https://vendors.snappfood.ir/installation-foodpartner/" target="_blank" rel="noopener noreferrer">راهنمای نصب Food Partner</a>
    </template>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="successMessage" class="success-message" role="status">{{ successMessage }}</p>

    <ManagementSurfaceCard class="connection-summary" title="وضعیت اتصال" subtitle="توکن هرگز در این صفحه نمایش داده نمی‌شود.">
      <div class="status-grid">
        <span class="status-pill" :class="status.has_token ? 'is-on' : 'is-off'">{{ status.has_token ? 'توکن ثبت شده' : 'توکن ثبت نشده' }}</span>
        <span class="status-pill" :class="status.vendor_id ? 'is-on' : 'is-warn'">{{ status.vendor_id ? `فروشنده: ${status.vendor_id}` : 'شناسه فروشنده ناقص' }}</span>
        <span class="status-pill" :class="status.enabled ? 'is-on' : 'is-off'">{{ status.enabled ? 'همگام‌سازی فعال' : 'همگام‌سازی خاموش' }}</span>
        <span class="status-pill" :class="status.auto_sync_invoices ? 'is-on' : 'is-warn'">{{ status.auto_sync_invoices ? 'فاکتور خودکار روشن' : 'فاکتور خودکار خاموش' }}</span>
        <span class="status-pill" :class="status.require_item_mapping ? 'is-warn' : 'is-on'">{{ status.require_item_mapping ? 'نگاشت اجباری' : 'ساخت خودکار کالا' }}</span>
        <span class="status-pill" :class="status.schema_ready ? 'is-on' : 'is-warn'">{{ status.schema_ready ? 'ساختار آماده' : 'ابتدا migrate' }}</span>
      </div>
      <p v-if="!status.schema_ready" class="schema-warning" role="alert">
        فیلدهای اتصال هنوز روی این سایت ساخته نشده‌اند. قبل از نگاشت کالا یا همگام‌سازی سفارش، migration اپ Restaurant را اجرا کنید.
      </p>
      <p v-else-if="!status.auto_sync_invoices" class="schema-warning" role="status">
        ساخت خودکار فاکتور خاموش است؛ برای ثبت فاکتور native در همان POS، گزینهٔ «برای سفارش واردشده فاکتور فروش ساخته شود» را روشن کنید.
      </p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft" class="section-picker-shell">
      <div class="simple-tabs" role="tablist" aria-label="بخش‌های اتصال Food Partner">
        <button v-for="tab in tabs" :key="tab.value" type="button" class="simple-tab" :class="{ active: activeTab === tab.value }" @click="activeTab = tab.value">
          {{ tab.label }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <template v-if="activeTab === 'connection'">
      <ManagementSurfaceCard title="تنظیمات اتصال" subtitle="این مقادیر از capture جدید Food Partner آمده‌اند؛ مسیر قدیمی سفارش در این اتصال استفاده نمی‌شود.">
        <div class="form-grid">
          <label>شناسه فروشنده<input v-model.trim="form.snapp_vendor_id" class="input" placeholder="اختیاری؛ بعد از ذخیرهٔ توکن خودکار تشخیص داده می‌شود" /></label>
          <div class="token-field">
            <label>Bearer token<input v-model="form.snapp_bearer_token" class="input" :type="tokenVisible ? 'text' : 'password'" autocomplete="new-password" placeholder="فقط در سمت سرور ذخیره می‌شود" /></label>
            <div class="token-actions">
              <button class="secondary-btn" type="button" @click="pasteToken">چسباندن از کلیپ‌بورد</button>
              <button class="secondary-btn" type="button" @click="tokenVisible = !tokenVisible">{{ tokenVisible ? 'مخفی‌کردن توکن' : 'نمایش توکن' }}</button>
            </div>
          </div>
          <label>گزارش سفارش<input v-model.trim="form.snapp_report_url" class="input" /></label>
          <label>پایه API منو<input v-model.trim="form.snapp_menu_api_base_url" class="input" /></label>
          <label>Origin (اختیاری)<input v-model.trim="form.snapp_origin_url" class="input" placeholder="https://dakhl-ordering.snappfood.ir" /></label>
          <label>Host domain (اختیاری)<input v-model.trim="form.snapp_hostdomain" class="input" /></label>
          <label>اندازه صفحه گزارش<input v-model.number="form.snapp_page_size" class="input" type="number" min="1" max="100" /></label>
          <label>ضریب مبلغ<input v-model.number="form.snapp_amount_multiplier" class="input" type="number" min="0.01" step="0.01" /></label>
          <label>Customer اصلی داخلی (اختیاری)<input v-model.trim="form.snapp_default_customer" class="input" placeholder="نام یا شناسه Customer؛ مثلاً Snappfood" /></label>
        </div>
        <div class="switch-grid">
          <label class="check-row"><input v-model="form.snapp_sync_enabled" type="checkbox" /> همگام‌سازی خودکار فعال باشد</label>
          <label class="check-row"><input v-model="form.snapp_auto_sync_invoices" type="checkbox" /> برای سفارش واردشده فاکتور فروش ساخته شود</label>
          <label class="check-row"><input v-model="form.snapp_require_item_mapping" type="checkbox" /> کالای نگاشت‌نشده سفارش را متوقف کند</label>
        </div>
        <p class="security-note">این دکمه فقط پنل رسمی Partner را باز می‌کند؛ Cookie، localStorage و Header مرورگر جمع‌آوری نمی‌شود. توکن را فقط از مسیر رسمی دریافت و در همین فیلد رمزنگاری‌شده ثبت کنید.</p>
        <div class="actions-row"><button class="primary-btn" type="button" @click="saveConfig" :disabled="saving || !status.schema_ready">{{ saving ? 'در حال ذخیره...' : 'ذخیره اتصال' }}</button></div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeTab === 'mapping'">
      <ManagementSurfaceCard title="نگاشت محصولات و variationها" subtitle="ابتدا منوی Food Partner را دریافت کنید، سپس هر ردیف را به Item داخلی وصل کنید.">
        <div class="mapping-toolbar">
          <button class="secondary-btn" type="button" @click="loadMappings(true)" :disabled="mappingLoading || !status.schema_ready">{{ mappingLoading ? 'در حال دریافت منو...' : 'دریافت منوی Food Partner' }}</button>
          <button class="secondary-btn" type="button" @click="loadCategories" :disabled="categoryLoading || !status.schema_ready">{{ categoryLoading ? 'در حال دریافت گروه‌ها...' : 'دریافت گروه‌های کالا' }}</button>
          <input v-model.trim="mappingSearch" class="input mapping-search" placeholder="جستجوی Item داخلی" @keyup.enter="searchMappingItems" />
          <button class="secondary-btn" type="button" @click="searchMappingItems" :disabled="itemSearchLoading || !status.schema_ready">{{ itemSearchLoading ? 'در حال جستجو...' : 'جستجوی Item' }}</button>
          <button class="secondary-btn" type="button" @click="runAutoMapping(false)" :disabled="autoMapping || !status.schema_ready">{{ autoMapping ? 'در حال نگاشت...' : 'نگاشت خودکار موارد قطعی' }}</button>
          <button class="secondary-btn" type="button" @click="runAutoMapping(true)" :disabled="autoMapping || !status.schema_ready">ساخت و نگاشت کالاهای غایب</button>
        </div>
        <p v-if="autoMapResult" class="sync-result">بررسی {{ autoMapResult.menu_count || 0 }} ردیف: {{ autoMapResult.already_mapped_count || 0 }} قبلاً نگاشت‌شده، {{ autoMapResult.mapped_count || 0 }} نگاشت جدید، {{ autoMapResult.created_count || 0 }} Item ساخته‌شده، {{ autoMapResult.unmatched_count || 0 }} بدون تطبیق، {{ autoMapResult.conflict_count || 0 }} مورد متعارض.</p>
        <ul v-if="autoMapResult?.unmatched?.length || autoMapResult?.conflicts?.length || autoMapResult?.errors?.length" class="error-list"><li v-for="(item, index) in [...(autoMapResult.unmatched || []), ...(autoMapResult.conflicts || []), ...(autoMapResult.errors || [])].slice(0, 8)" :key="index">{{ item.title || item.external_id || '—' }}: {{ item.reason || item.error || 'نیازمند بررسی دستی' }}</li></ul>
        <div v-if="categorySections.length" class="category-accordion">
          <section v-for="category in categorySections" :key="category.key" class="category-panel">
            <button class="category-trigger" type="button" @click="toggleCategory(category.key)" :aria-expanded="openCategories.has(category.key)">
              <span><strong>{{ category.title }}</strong><small>{{ category.category_id ? `شناسه: ${category.category_id}` : 'بدون گروه مشخص' }}</small></span>
              <span>{{ category.rows.length }} کالا · {{ openCategories.has(category.key) ? 'بستن' : 'بازکردن' }}</span>
            </button>
            <div v-if="openCategories.has(category.key)" class="category-panel-body">
              <p v-if="!category.rows.length" class="muted">برای این گروه هنوز محصولی از منوی Food Partner دریافت نشده است.</p>
              <div v-else class="mapping-list">
                <div v-for="row in category.rows" :key="`${row.external_id}-${row.title}`" class="mapping-row">
                  <div><strong>{{ row.title || 'بدون عنوان' }}</strong><small>variation: {{ row.variation_id || '—' }} · product: {{ row.product_id || '—' }} · قیمت: {{ row.price || '—' }}</small><small class="mapping-state" :class="row.mapping_status === 'Mapped' ? 'is-mapped' : 'is-unmapped'">{{ row.mapping_status === 'Mapped' ? `نگاشت واقعی: ${row.mapped_item?.item_name || row.mapped_item?.name || 'Item داخلی'}` : 'نگاشت واقعی ثبت نشده است' }}</small><small v-if="row.mapping_status !== 'Mapped' && row.suggested_item">پیشنهاد بر اساس نام (هنوز ثبت نشده): {{ row.suggested_item.item_name || row.suggested_item.name }}</small></div>
                  <SearchableDropdown
                    v-model="mappingDrafts[row.external_id]"
                    class="mapping-select"
                    :options="mappingItemOptions"
                    :search-fn="searchMappingItemOptions"
                    placeholder="انتخاب Item داخلی"
                    search-placeholder="جستجوی نام، کد یا شناسه کالا..."
                    no-results-text="کالایی پیدا نشد؛ عبارت دیگری جستجو کنید."
                    clearable
                    fixed-panel
                  />
                  <button class="secondary-btn" type="button" @click="saveMapping(row)" :disabled="mappingSaving === row.external_id">{{ mappingSaving === row.external_id ? '...' : 'ثبت نگاشت' }}</button>
                  <button v-if="!mappingDrafts[row.external_id]" class="secondary-btn" type="button" @click="createItemFromMapping(row)" :disabled="mappingCreating === row.external_id">{{ mappingCreating === row.external_id ? 'در حال ساخت...' : 'ساخت Item و ثبت نگاشت' }}</button>
                </div>
              </div>
            </div>
          </section>
        </div>
        <p class="muted" v-else>برای دیدن گروه‌ها و کالاها روی «دریافت گروه‌های کالا» بزنید.</p>
      </ManagementSurfaceCard>
    </template>

    <template v-else>
      <ManagementSurfaceCard title="آزمایش سفارش‌های دیروز و بازه‌های تاریخی" subtitle="ابتدا یک بازه را فقط preview کنید، سپس حداکثر سه سفارش را برای ورود تستی انتخاب کنید. همان سفارش‌های فروش و فاکتورهای POS ثبت می‌شوند.">
        <div class="date-range-toolbar">
          <label>از تاریخ<input v-model="orderWindow.from_date" class="input" type="date" /></label>
          <label>تا تاریخ<input v-model="orderWindow.to_date" class="input" type="date" /></label>
          <button class="secondary-btn" type="button" @click="setYesterday">دیروز</button>
          <button class="primary-btn" type="button" @click="previewOrders" :disabled="previewLoading || !status.schema_ready">{{ previewLoading ? 'در حال دریافت...' : 'پیش‌نمایش بازه' }}</button>
        </div>
        <p class="muted">مشتری اصلی فاکتور: <strong>{{ form.snapp_default_customer || 'هنوز تنظیم نشده' }}</strong> · مشتری Food Partner در مشتری ثانویه ثبت می‌شود · حداکثر ۳ سفارش تستی.</p>
        <div v-if="orderPreview.length" class="order-preview-list">
          <label v-for="order in orderPreview" :key="order.order_id" class="order-preview-row" :class="{ 'is-imported': order.already_imported }">
            <input type="checkbox" :checked="selectedOrderIds.has(order.order_id)" :disabled="order.already_imported || (!selectedOrderIds.has(order.order_id) && selectedOrderIds.size >= 3)" @change="toggleOrderSelection(order.order_id)" />
            <span class="order-preview-main"><strong>{{ order.bill_number || order.order_id }}</strong><small>{{ order.customer_name }} · {{ order.created_at }} · {{ order.items_count }} قلم · {{ order.final_amount }}</small><em v-if="order.already_imported">قبلاً وارد شده: {{ order.sales_order }}{{ order.sales_invoice ? ` · فاکتور: ${order.sales_invoice}` : '' }}</em><em v-else>{{ order.items.slice(0, 3).map((item) => `${item.title} × ${item.qty}`).join('، ') }}</em></span>
          </label>
        </div>
        <p v-else class="muted">هنوز سفارشی برای این بازه دریافت نشده است.</p>
        <div class="sync-card"><button class="primary-btn" type="button" @click="importSelectedOrders" :disabled="importing || !selectedOrderIds.size || !status.schema_ready">{{ importing ? 'در حال واردکردن...' : `واردکردن تستی (${selectedOrderIds.size}/۳)` }}</button><span v-if="syncResult" class="sync-result">{{ syncSummary }}</span></div>
        <div class="sync-card"><button class="secondary-btn" type="button" @click="syncToday" :disabled="syncing || !status.schema_ready">{{ syncing ? 'در حال همگام‌سازی...' : 'همگام‌سازی همه سفارش‌های امروز' }}</button></div>
        <ul v-if="syncResult?.errors?.length" class="error-list"><li v-for="(item, index) in syncResult.errors.slice(0, 5)" :key="index">{{ item.order_id || '—' }}: {{ shortError(item.error) }}</li></ul>
        <p class="muted">این عملیات idempotent است و orderId را برای جلوگیری از ثبت تکراری استفاده می‌کند.</p>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementBreadcrumbs from '@/components/management/ManagementBreadcrumbs.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  getSnappfoodIntegrationConfig,
  getSnappfoodCategories,
  getSnappfoodMappingRows,
  searchSnappfoodItems,
  autoMapSnappfoodItems,
  createSnappfoodItemFromMapping,
  importSnappfoodOrders,
  previewSnappfoodOrders,
  runSnappfoodSyncToday,
  saveSnappfoodIntegrationConfig,
  saveSnappfoodItemMapping,
  testSnappfoodConnection,
} from '@/utils/api'

const tabs = [
  { value: 'connection', label: 'اتصال' },
  { value: 'mapping', label: 'نگاشت کالاها' },
  { value: 'sync', label: 'همگام‌سازی سفارش' },
]
const breadcrumbItems = [{ label: 'مدیریت', href: '/management' }, { label: 'اتصال Food Partner' }]
const activeTab = ref('connection')
const loading = ref(false)
const testingConnection = ref(false)
const saving = ref(false)
const mappingLoading = ref(false)
const categoryLoading = ref(false)
const itemSearchLoading = ref(false)
const mappingSaving = ref('')
const mappingCreating = ref('')
const autoMapping = ref(false)
const syncing = ref(false)
const previewLoading = ref(false)
const importing = ref(false)
const error = ref('')
const successMessage = ref('')
const mappingSearch = ref('')
const syncResult = ref(null)
const autoMapResult = ref(null)
const mappingRows = reactive({ menu: [], items: [] })
const categories = ref([])
const openCategories = ref(new Set())
const orderPreview = ref([])
const selectedOrderIds = ref(new Set())
const orderWindow = reactive({ from_date: '', to_date: '' })
const mappingDrafts = reactive({})
const tokenVisible = ref(false)
const status = reactive({ has_token: false, vendor_id: '', enabled: false, require_item_mapping: true, auto_sync_invoices: true, schema_ready: false, schema_missing: [] })
const form = reactive({ snapp_vendor_id: '', snapp_bearer_token: '', snapp_report_url: 'https://snappfood.ir/vms/v3/restaurant/report', snapp_menu_api_base_url: 'https://apigw.snappfood.ir', snapp_origin_url: '', snapp_hostdomain: '', snapp_page_size: 50, snapp_amount_multiplier: 10, snapp_default_customer: '', snapp_sync_enabled: false, snapp_auto_sync_invoices: true, snapp_require_item_mapping: true })

const mappingItemOptions = computed(() => mappingRows.items.map((item) => ({
  value: item.name,
  label: `${item.item_name || item.name}${item.item_code ? ` · ${item.item_code}` : ''}`,
})))

const categorySections = computed(() => {
  const sections = []
  const byKey = new Map()
  const addSection = (key, title, categoryId = '') => {
    const normalizedKey = String(key || '').trim() || '__uncategorized__'
    if (!byKey.has(normalizedKey)) {
      const section = { key: normalizedKey, title: title || 'بدون گروه مشخص', category_id: categoryId || '', rows: [] }
      byKey.set(normalizedKey, section); sections.push(section)
    }
    return byKey.get(normalizedKey)
  }
  categories.value.forEach((category) => addSection(category.external_id || category.category_id, category.title, category.category_id || category.external_id))
  mappingRows.menu.forEach((row) => {
    const key = row.category_id || (row.category_title ? `title:${row.category_title}` : '__uncategorized__')
    const section = addSection(key, row.category_title || 'بدون گروه مشخص', row.category_id || '')
    section.rows.push(row)
  })
  return sections
})

const syncSummary = computed(() => {
  const row = syncResult.value || {}
  return `دریافت: ${row.fetched_count || 0} · سفارش جدید: ${row.created_count || 0} · فاکتور جدید: ${row.invoices_created_count || 0} · خطا: ${row.failed_count || 0}`
})

function applyStatus(data = {}) {
  Object.assign(status, data)
  form.snapp_vendor_id = data.vendor_id || ''
  form.snapp_report_url = data.report_url || form.snapp_report_url
  form.snapp_menu_api_base_url = data.menu_api_base_url || form.snapp_menu_api_base_url
  form.snapp_origin_url = data.origin_url || ''
  form.snapp_hostdomain = data.host_domain || ''
  form.snapp_page_size = Number(data.page_size || 50)
  form.snapp_amount_multiplier = Number(data.amount_multiplier || 10)
  form.snapp_default_customer = data.default_customer || ''
  form.snapp_sync_enabled = Boolean(data.enabled)
  form.snapp_auto_sync_invoices = data.auto_sync_invoices !== false
  form.snapp_require_item_mapping = data.require_item_mapping !== false
}

async function loadConfig() {
  loading.value = true; error.value = ''; successMessage.value = ''
  try { applyStatus(await getSnappfoodIntegrationConfig()) } catch (err) { error.value = err?.message || 'تنظیمات اتصال خوانده نشد.' } finally { loading.value = false }
}
async function testConnection() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  testingConnection.value = true; error.value = ''; successMessage.value = ''
  try {
    const result = await testSnappfoodConnection()
    successMessage.value = `اتصال موفق بود؛ ${result?.orders_count || 0} سفارش در صفحهٔ آزمایشی خوانده شد.`
  } catch (err) { error.value = err?.message || 'تست اتصال ناموفق بود.' } finally { testingConnection.value = false }
}
async function pasteToken() {
  error.value = ''; successMessage.value = ''
  if (!navigator.clipboard?.readText) {
    error.value = 'مرورگر اجازهٔ خواندن کلیپ‌بورد را نمی‌دهد؛ توکن را دستی در همین فیلد Paste کنید.'
    return
  }
  try {
    const value = (await navigator.clipboard.readText()).trim()
    if (!value) {
      error.value = 'کلیپ‌بورد خالی است.'
      return
    }
    form.snapp_bearer_token = value
    successMessage.value = 'توکن در فیلد قرار گرفت و هنوز به سرور ارسال نشده است.'
  } catch {
    error.value = 'دسترسی کلیپ‌بورد رد شد؛ توکن را دستی در همین فیلد Paste کنید.'
  }
}
async function saveConfig() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  saving.value = true; error.value = ''; successMessage.value = ''
  try {
    const hadVendorId = Boolean(form.snapp_vendor_id)
    const result = await saveSnappfoodIntegrationConfig({ ...form })
    applyStatus(result)
    form.snapp_bearer_token = ''
    successMessage.value = !hadVendorId && result?.vendor_id
      ? `تنظیمات ذخیره شد؛ شناسه فروشنده ${result.vendor_id} از توکن تشخیص داده شد.`
      : 'تنظیمات اتصال ذخیره شد.'
  } catch (err) { error.value = err?.message || 'ذخیره تنظیمات ناموفق بود.' } finally { saving.value = false }
}
async function loadMappings(refreshMenu = false) {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  mappingLoading.value = true; error.value = ''
  try {
    const data = await getSnappfoodMappingRows({ search: refreshMenu ? '' : mappingSearch.value, refresh_menu: refreshMenu ? 1 : 0 })
    mappingRows.menu = data?.menu || []; mappingRows.items = data?.items || []
    if (data?.status === 'error' || data?.error) {
      error.value = data.error || 'منوی Food Partner خوانده نشد.'
      return
    }
    mappingRows.menu.forEach((row) => { mappingDrafts[row.external_id] = row.mapped_item?.name || '' })
  } catch (err) { error.value = err?.message || 'منوی Food Partner خوانده نشد.' } finally { mappingLoading.value = false }
}
function toggleCategory(key) {
  const next = new Set(openCategories.value)
  if (next.has(key)) next.delete(key); else next.add(key)
  openCategories.value = next
}
async function loadCategories() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  categoryLoading.value = true; error.value = ''
  try {
    if (!mappingRows.menu.length) await loadMappings(true)
    const data = await getSnappfoodCategories()
    categories.value = data?.items || []
    if (data?.status === 'error' || data?.error) error.value = data.error || 'گروه‌های کالا خوانده نشدند.'
  } catch (err) { error.value = err?.message || 'گروه‌های کالا خوانده نشدند.' } finally { categoryLoading.value = false }
}
async function searchMappingItems() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  const search = mappingSearch.value.trim()
  if (!search) { error.value = 'برای جستجوی Item، نام یا شناسه را وارد کنید.'; return }
  itemSearchLoading.value = true; error.value = ''; successMessage.value = ''
  try {
    const data = await searchSnappfoodItems({ search, limit: 50 })
    mappingRows.items = data?.items || []
    if (data?.status === 'error' || data?.error) error.value = data.error || 'جستجوی Item ناموفق بود.'
    else successMessage.value = `${mappingRows.items.length} Item برای «${search}» پیدا شد.`
  } catch (err) { error.value = err?.message || 'جستجوی Item ناموفق بود.' } finally { itemSearchLoading.value = false }
}
async function searchMappingItemOptions(search = '') {
  const query = String(search || '').trim()
  if (query.length < 2) return []
  try {
    const data = await searchSnappfoodItems({ search: query, limit: 50 })
    return (data?.items || []).map((item) => ({
      value: item.name,
      label: `${item.item_name || item.name}${item.item_code ? ` · ${item.item_code}` : ''}`,
    }))
  } catch {
    return []
  }
}
async function saveMapping(row) {
  const itemName = mappingDrafts[row.external_id]
  if (!itemName) { error.value = 'برای ثبت نگاشت، ابتدا Item داخلی را انتخاب کنید.'; return }
  mappingSaving.value = row.external_id; error.value = ''
  try {
    const result = await saveSnappfoodItemMapping({ item_name: itemName, product_id: row.product_id, variation_id: row.variation_id, product_hash_id: row.product_hash_id, variation_hash_id: row.variation_hash_id, menu_item_id: row.menu_item_id || row.external_id })
    if (result?.status !== 'success') throw new Error(result?.message || 'سرور نگاشت را تأیید نکرد.')
    const selectedItem = mappingRows.items.find((item) => item.name === itemName)
    row.mapping_status = 'Mapped'
    row.mapped_item = selectedItem || { name: itemName, item_name: itemName }
    row.suggested_item = null
    mappingDrafts[row.external_id] = itemName
    successMessage.value = `نگاشت «${row.title}» ثبت شد.`
  } catch (err) { error.value = err?.message || 'ثبت نگاشت ناموفق بود.' } finally { mappingSaving.value = '' }
}
async function createItemFromMapping(row) {
  if (!row?.title || !row?.external_id) { error.value = 'عنوان و شناسهٔ Food Partner برای ساخت Item لازم است.'; return }
  mappingCreating.value = row.external_id; error.value = ''; successMessage.value = ''
  try {
    const result = await createSnappfoodItemFromMapping({ title: row.title, price: row.price, product_id: row.product_id, variation_id: row.variation_id, product_hash_id: row.product_hash_id, variation_hash_id: row.variation_hash_id, menu_item_id: row.external_id })
    mappingDrafts[row.external_id] = result?.item || ''
    successMessage.value = result?.created ? `Item «${row.title}» ساخته و نگاشت شد.` : `Item «${row.title}» قبلاً وجود داشت و نگاشت شد.`
    await loadMappings(true)
  } catch (err) { error.value = err?.message || 'ساخت Item و ثبت نگاشت ناموفق بود.' } finally { mappingCreating.value = '' }
}
async function runAutoMapping(createMissing = false) {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  if (createMissing && !window.confirm('برای کالاهایی که Item داخلی ندارند، Item native ساخته و به Food Partner متصل شود؟ سفارش یا فاکتوری ساخته نمی‌شود.')) return
  autoMapping.value = true; error.value = ''; successMessage.value = ''; autoMapResult.value = null
  try {
    const result = await autoMapSnappfoodItems({ create_missing: createMissing ? 1 : 0, refresh_menu: 1 })
    autoMapResult.value = result
    if (result?.status === 'error' || result?.error) error.value = result.error || 'نگاشت خودکار ناموفق بود.'
    else {
      successMessage.value = createMissing
        ? 'نگاشت خودکار و ساخت Itemهای غایب تمام شد.'
        : 'نگاشت خودکار موارد قطعی تمام شد.'
      await loadMappings(true)
    }
  } catch (err) { error.value = err?.message || 'نگاشت خودکار ناموفق بود.' } finally { autoMapping.value = false }
}
async function syncToday() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  syncing.value = true; error.value = ''; syncResult.value = null
  try { syncResult.value = await runSnappfoodSyncToday(); successMessage.value = 'همگام‌سازی امروز تمام شد.' } catch (err) { error.value = err?.message || 'همگام‌سازی ناموفق بود.' } finally { syncing.value = false }
}
function formatDateInput(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function setYesterday() {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  const value = formatDateInput(yesterday)
  orderWindow.from_date = value; orderWindow.to_date = value
  orderPreview.value = []; selectedOrderIds.value = new Set()
}
async function previewOrders(preserveSyncResult = false) {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  previewLoading.value = true; error.value = ''; successMessage.value = ''
  if (!preserveSyncResult) syncResult.value = null
  try {
    const data = await previewSnappfoodOrders({ ...orderWindow })
    orderPreview.value = data?.orders || []
    selectedOrderIds.value = new Set()
    if (data?.status === 'error' || data?.error) error.value = data.error || 'پیش‌نمایش سفارش‌ها ناموفق بود.'
    else successMessage.value = `${data?.orders?.length || 0} سفارش برای بازهٔ انتخابی پیدا شد.`
  } catch (err) { error.value = err?.message || 'پیش‌نمایش سفارش‌ها ناموفق بود.' } finally { previewLoading.value = false }
}
function toggleOrderSelection(orderId) {
  const next = new Set(selectedOrderIds.value)
  if (next.has(orderId)) next.delete(orderId)
  else if (next.size < 3) next.add(orderId)
  selectedOrderIds.value = next
}
async function importSelectedOrders() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  const orderIds = Array.from(selectedOrderIds.value).slice(0, 3)
  if (!orderIds.length) { error.value = 'حداقل یک سفارش را انتخاب کنید.'; return }
  importing.value = true; error.value = ''; successMessage.value = ''
  try {
    syncResult.value = await importSnappfoodOrders({ order_ids: orderIds, ...orderWindow })
    if (syncResult.value?.status === 'error' || syncResult.value?.error) error.value = syncResult.value.error || 'واردکردن سفارش‌ها ناموفق بود.'
    else {
      await previewOrders(true)
      successMessage.value = 'واردکردن تستی انجام شد و وضعیت سفارش‌ها تازه شد.'
    }
  } catch (err) { error.value = err?.message || 'واردکردن سفارش‌ها ناموفق بود.' } finally { importing.value = false }
}
function shortError(value) { return String(value || '').split('\n').filter(Boolean).slice(-1)[0] || 'خطای نامشخص' }
setYesterday()
onMounted(loadConfig)
</script>

<style scoped>
.category-accordion{display:grid;gap:10px;margin-top:16px}.category-panel{border:1px solid var(--border-color,#e5e7eb);border-radius:14px;overflow:hidden;background:var(--surface,#fff)}.category-trigger{width:100%;display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border:0;background:var(--surface-soft,#f6f7fb);color:inherit;text-align:right;cursor:pointer}.category-trigger span:first-child{display:grid;gap:4px}.category-trigger small{color:#6b7280;font-size:11px}.category-panel-body{padding:0 12px 12px}.date-range-toolbar{display:flex;align-items:end;flex-wrap:wrap;gap:10px;margin-top:18px}.date-range-toolbar label{display:grid;gap:6px;min-width:160px;font-size:12px}.order-preview-list{display:grid;gap:8px;margin-top:16px}.order-preview-row{display:flex;align-items:flex-start;gap:10px;border:1px solid var(--border-color,#e5e7eb);border-radius:12px;padding:12px;cursor:pointer}.order-preview-row.is-imported{opacity:.62;cursor:not-allowed}.order-preview-main{display:grid;gap:4px}.order-preview-main small,.order-preview-main em{color:#6b7280;font-size:11px;font-style:normal}.order-preview-main em{color:#166534}
.status-grid,.form-grid,.switch-grid{display:grid;gap:14px}.status-grid{grid-template-columns:repeat(5,minmax(0,1fr))}.form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.switch-grid{grid-template-columns:repeat(3,minmax(0,1fr));margin-top:18px}.status-pill{border-radius:999px;padding:9px 12px;background:var(--surface-soft,#f6f7fb);font-size:12px;text-align:center}.status-pill.is-on{color:#166534;background:#dcfce7}.status-pill.is-off{color:#6b7280}.status-pill.is-warn{color:#92400e;background:#fef3c7}.schema-warning{margin:14px 0 0;padding:12px 14px;border-radius:12px;background:#fff7ed;color:#9a3412;font-size:12px;line-height:1.8}.check-row{display:flex;gap:8px;align-items:center;font-size:13px}.security-note{margin:18px 0 0;padding:12px;border-radius:12px;background:#fff7ed;color:#9a3412;font-size:12px;line-height:1.8}.actions-row,.mapping-toolbar,.sync-card,.token-actions{display:flex;gap:10px;align-items:center;margin-top:20px}.token-field{min-width:0}.token-actions{margin-top:8px}.mapping-search{max-width:300px}.category-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.category-pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border-color,#e5e7eb);border-radius:999px;padding:7px 10px;background:var(--surface-soft,#f6f7fb);font-size:12px}.category-pill small{color:#6b7280}.mapping-list{display:grid;gap:10px;margin-top:16px}.mapping-row{display:grid;grid-template-columns:minmax(180px,1fr) minmax(220px,1.2fr) auto;gap:12px;align-items:center;border:1px solid var(--border-color,#e5e7eb);border-radius:14px;padding:12px}.mapping-row small{display:block;color:#6b7280;margin-top:4px}.mapping-select{min-width:0}.sync-result{font-size:13px;color:#166534}.error-list{margin:18px 0 0;color:#b91c1c;line-height:1.9;font-size:12px}@media(max-width:800px){.status-grid,.form-grid,.switch-grid{grid-template-columns:1fr}.mapping-row{grid-template-columns:1fr}.mapping-toolbar{align-items:stretch;flex-direction:column}.mapping-search{max-width:none}}
.mapping-state.is-mapped{color:#166534}.mapping-state.is-unmapped{color:#b45309}
.mapping-toolbar{flex-wrap:wrap}.mapping-toolbar .mapping-search{flex:1 1 240px}
</style>
