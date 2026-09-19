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
          <label>شناسه فروشنده<input v-model.trim="form.snapp_vendor_id" class="input" placeholder="مثلاً 466275" /></label>
          <label>Bearer token<input v-model="form.snapp_bearer_token" class="input" type="password" autocomplete="new-password" placeholder="فقط در سمت سرور ذخیره می‌شود" /></label>
          <label>گزارش سفارش<input v-model.trim="form.snapp_report_url" class="input" /></label>
          <label>پایه API منو<input v-model.trim="form.snapp_menu_api_base_url" class="input" /></label>
          <label>Origin (اختیاری)<input v-model.trim="form.snapp_origin_url" class="input" placeholder="https://dakhl-ordering.snappfood.ir" /></label>
          <label>Host domain (اختیاری)<input v-model.trim="form.snapp_hostdomain" class="input" /></label>
          <label>اندازه صفحه گزارش<input v-model.number="form.snapp_page_size" class="input" type="number" min="1" max="100" /></label>
          <label>ضریب مبلغ<input v-model.number="form.snapp_amount_multiplier" class="input" type="number" min="0.01" step="0.01" /></label>
          <label>Customer اصلی داخلی (اختیاری)<input v-model.trim="form.snapp_default_customer" class="input" placeholder="نام رکورد Customer؛ مثلاً Snappfood" /></label>
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
        <div class="mapping-toolbar"><button class="secondary-btn" type="button" @click="loadMappings(true)" :disabled="mappingLoading || !status.schema_ready">{{ mappingLoading ? 'در حال دریافت منو...' : 'دریافت منوی Food Partner' }}</button><input v-model.trim="mappingSearch" class="input mapping-search" placeholder="جستجوی Item داخلی" @keyup.enter="loadMappings(false)" /></div>
        <p class="muted" v-if="!mappingRows.menu.length">برای دیدن product/variationها روی «دریافت منوی Food Partner» بزنید.</p>
        <div v-else class="mapping-list">
          <div v-for="row in mappingRows.menu" :key="`${row.external_id}-${row.title}`" class="mapping-row">
            <div><strong>{{ row.title || 'بدون عنوان' }}</strong><small>variation: {{ row.variation_id || '—' }} · product: {{ row.product_id || '—' }}</small></div>
            <select class="input mapping-select" v-model="mappingDrafts[row.external_id]">
              <option value="">انتخاب Item داخلی</option>
              <option v-for="item in mappingRows.items" :key="item.name" :value="item.name">{{ item.item_name }} · {{ item.item_code }}</option>
            </select>
            <button class="secondary-btn" type="button" @click="saveMapping(row)" :disabled="mappingSaving === row.external_id">{{ mappingSaving === row.external_id ? '...' : 'ثبت نگاشت' }}</button>
          </div>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else>
      <ManagementSurfaceCard title="همگام‌سازی سفارش‌های امروز" subtitle="پس از تکمیل توکن و نگاشت کالاها، سفارش‌ها در همان سفارش‌های فروش و فاکتورهای POS ثبت می‌شوند.">
        <div class="sync-card"><button class="primary-btn" type="button" @click="syncToday" :disabled="syncing || !status.schema_ready">{{ syncing ? 'در حال همگام‌سازی...' : 'همگام‌سازی امروز' }}</button><span v-if="syncResult" class="sync-result">{{ syncSummary }}</span></div>
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
import {
  getSnappfoodIntegrationConfig,
  getSnappfoodMappingRows,
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
const mappingSaving = ref('')
const syncing = ref(false)
const error = ref('')
const successMessage = ref('')
const mappingSearch = ref('')
const syncResult = ref(null)
const mappingRows = reactive({ menu: [], items: [] })
const mappingDrafts = reactive({})
const status = reactive({ has_token: false, vendor_id: '', enabled: false, require_item_mapping: true, auto_sync_invoices: true, schema_ready: false, schema_missing: [] })
const form = reactive({ snapp_vendor_id: '', snapp_bearer_token: '', snapp_report_url: 'https://snappfood.ir/vms/v3/restaurant/report', snapp_menu_api_base_url: 'https://apigw.snappfood.ir', snapp_origin_url: '', snapp_hostdomain: '', snapp_page_size: 50, snapp_amount_multiplier: 10, snapp_default_customer: '', snapp_sync_enabled: false, snapp_auto_sync_invoices: true, snapp_require_item_mapping: true })

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
async function saveConfig() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  saving.value = true; error.value = ''; successMessage.value = ''
  try { applyStatus(await saveSnappfoodIntegrationConfig({ ...form })); form.snapp_bearer_token = ''; successMessage.value = 'تنظیمات اتصال ذخیره شد.' } catch (err) { error.value = err?.message || 'ذخیره تنظیمات ناموفق بود.' } finally { saving.value = false }
}
async function loadMappings(refreshMenu = false) {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  mappingLoading.value = true; error.value = ''
  try {
    const data = await getSnappfoodMappingRows({ search: mappingSearch.value, refresh_menu: refreshMenu ? 1 : 0 })
    mappingRows.menu = data?.menu || []; mappingRows.items = data?.items || []
    mappingRows.menu.forEach((row) => { mappingDrafts[row.external_id] = row.suggested_item?.name || '' })
  } catch (err) { error.value = err?.message || 'منوی Food Partner خوانده نشد.' } finally { mappingLoading.value = false }
}
async function saveMapping(row) {
  const itemName = mappingDrafts[row.external_id]
  if (!itemName) { error.value = 'برای ثبت نگاشت، ابتدا Item داخلی را انتخاب کنید.'; return }
  mappingSaving.value = row.external_id; error.value = ''
  try { await saveSnappfoodItemMapping({ item_name: itemName, product_id: row.product_id, variation_id: row.variation_id, product_hash_id: row.product_hash_id, variation_hash_id: row.variation_hash_id, menu_item_id: row.external_id }); successMessage.value = `نگاشت «${row.title}» ثبت شد.` } catch (err) { error.value = err?.message || 'ثبت نگاشت ناموفق بود.' } finally { mappingSaving.value = '' }
}
async function syncToday() {
  if (!status.schema_ready) { error.value = 'ابتدا migration اپ Restaurant را روی سایت اجرا کنید.'; return }
  syncing.value = true; error.value = ''; syncResult.value = null
  try { syncResult.value = await runSnappfoodSyncToday(); successMessage.value = 'همگام‌سازی امروز تمام شد.' } catch (err) { error.value = err?.message || 'همگام‌سازی ناموفق بود.' } finally { syncing.value = false }
}
function shortError(value) { return String(value || '').split('\n').filter(Boolean).slice(-1)[0] || 'خطای نامشخص' }
onMounted(loadConfig)
</script>

<style scoped>
.status-grid,.form-grid,.switch-grid{display:grid;gap:14px}.status-grid{grid-template-columns:repeat(5,minmax(0,1fr))}.form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.switch-grid{grid-template-columns:repeat(3,minmax(0,1fr));margin-top:18px}.status-pill{border-radius:999px;padding:9px 12px;background:var(--surface-soft,#f6f7fb);font-size:12px;text-align:center}.status-pill.is-on{color:#166534;background:#dcfce7}.status-pill.is-off{color:#6b7280}.status-pill.is-warn{color:#92400e;background:#fef3c7}.schema-warning{margin:14px 0 0;padding:12px 14px;border-radius:12px;background:#fff7ed;color:#9a3412;font-size:12px;line-height:1.8}.check-row{display:flex;gap:8px;align-items:center;font-size:13px}.security-note{margin:18px 0 0;padding:12px;border-radius:12px;background:#fff7ed;color:#9a3412;font-size:12px;line-height:1.8}.actions-row,.mapping-toolbar,.sync-card{display:flex;gap:10px;align-items:center;margin-top:20px}.mapping-search{max-width:300px}.mapping-list{display:grid;gap:10px;margin-top:16px}.mapping-row{display:grid;grid-template-columns:minmax(180px,1fr) minmax(220px,1.2fr) auto;gap:12px;align-items:center;border:1px solid var(--border-color,#e5e7eb);border-radius:14px;padding:12px}.mapping-row small{display:block;color:#6b7280;margin-top:4px}.mapping-select{min-width:0}.sync-result{font-size:13px;color:#166534}.error-list{margin:18px 0 0;color:#b91c1c;line-height:1.9;font-size:12px}@media(max-width:800px){.status-grid,.form-grid,.switch-grid{grid-template-columns:1fr}.mapping-row{grid-template-columns:1fr}.mapping-toolbar{align-items:stretch;flex-direction:column}.mapping-search{max-width:none}}
</style>
