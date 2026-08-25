<template>
  <ManagementPageScaffold title="شعب" subtitle="گزارش تجمیعی و تفکیکی هر شعبه، فروش/مشتری امروز و انتقال مشتری بین شعب">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reload" :disabled="loading">{{ loading ? '...' : 'بروزرسانی' }}</button>
      <button type="button" class="primary-btn" @click="openForm()">شعبه جدید</button>
    </template>

    <div class="totals-grid">
      <div class="total-box"><small>تعداد شعب</small><strong>{{ formatQty(boot.branch_count || 0) }}</strong></div>
      <div class="total-box"><small>انبارهای ثبت‌شده</small><strong>{{ formatQty((boot.warehouses || []).length) }}</strong></div>
      <div class="total-box"><small>توصیه (پلن پایه)</small><strong>تا {{ formatQty(boot.max_recommended || 5) }} شعبه</strong></div>
    </div>

    <ManagementSurfaceCard title="گزارش تفکیکی شعب" subtitle="فروش، سفارش و مشتریان هر شعبه — گزارش عملکرد کامل در مرکز گزارش‌ها">
      <div class="toolbar">
        <label class="check-row"><input type="checkbox" v-model="showActiveOnly" @change="reload" /> فقط شعب فعال</label>
        <a class="link-btn" href="/management/reports/branch-performance">گزارش عملکرد شعب (BI)</a>
      </div>
      <p class="muted" v-if="loading">در حال دریافت...</p>
      <p class="error" v-if="error">{{ error }}</p>
      <p class="success-msg" v-if="message">{{ message }}</p>
      <div v-if="!loading && branches.length" class="table-wrap">
        <table class="data-table">
          <thead><tr><th>شعبه</th><th>سفارش‌های امروز</th><th>فروش امروز</th><th>مشتریان متصل</th><th>آدرس/تلفن</th><th>وضعیت</th><th></th></tr></thead>
          <tbody>
            <tr v-for="b in branches" :key="b.name">
              <td><strong>{{ b.label || b.company_name }}</strong><br><small class="muted">{{ b.name }} · {{ b.abbr }}</small></td>
              <td>{{ formatQty(b.today_orders) }}</td>
              <td>{{ formatMoneyValue(b.today_sales) }}</td>
              <td>{{ formatQty(b.customers) }}</td>
              <td><small class="muted">{{ b.address || '—' }}<template v-if="b.phone"> · {{ b.phone }}</template></small></td>
              <td><span class="pill" :class="{ ok: b.is_active, warn: !b.is_active }">{{ b.is_active ? 'فعال' : 'غیرفعال' }}</span></td>
              <td class="row-actions">
                <button type="button" class="tertiary-btn" @click="openForm(b)">ویرایش</button>
                <button type="button" class="tertiary-btn" @click="toggleBranch(b)">{{ b.is_active ? 'غیرفعال‌سازی' : 'فعال‌سازی' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted" v-else-if="!loading">شعبه‌ای تعریف نشده است.</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="انتقال مشتری بین شعب" subtitle="اتصال یک مشتری (باشگاه) به شعبه دیگر — کیف پول و کمپین‌ها به‌صورت مشترک بین همه شعب باقی می‌مانند">
      <div class="form-grid">
        <label>مشتری (نام Customer یا موبایل)<input class="input" v-model.trim="transferForm.customer" placeholder="Customer-0001 یا 09xxxxxxxxx" /></label>
        <label>شعبه مقصد
          <select class="input" v-model="transferForm.target_branch">
            <option value="">— انتخاب کنید —</option>
            <option v-for="b in activeBranches" :key="b.name" :value="b.name">{{ b.label || b.company_name }}</option>
          </select>
        </label>
      </div>
      <div class="btn-row">
        <button type="button" class="primary-btn" @click="doTransfer" :disabled="transferBusy">{{ transferBusy ? '...' : 'انتقال مشتری' }}</button>
      </div>
      <p class="error" v-if="transferError">{{ transferError }}</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="امکانات اشتراکی شعب" subtitle="این موارد به‌صورت خودکار بین همه شعب مشترک است">
      <ul class="shared-list">
        <li>✅ کیف پول و کارت اعتباری مشتریان بین همه شعب مشترک است.</li>
        <li>✅ کمپین‌ها و کوپن‌ها سراسری هستند و در هر شعبه قابل استفاده‌اند.</li>
        <li>✅ انبارداری به‌صورت متمرکز انجام می‌شود و هر انبار می‌تواند به شعبه لینک شود.</li>
        <li>✅ منوی مشترک/اختصاصی: هر آیتم منو می‌تواند مخصوص یک شعبه یا عمومی باشد.</li>
        <li>✅ گزارش تجمیعی: داشبورد مدیریت با فیلتر شعبه، تجمیع همه شعب را نشان می‌دهد.</li>
      </ul>
    </ManagementSurfaceCard>

    <div v-if="form" class="popup-backdrop" @click.self="form = null">
      <div class="popup">
        <h3>{{ form.name ? 'ویرایش شعبه' : 'شعبه جدید' }}</h3>
        <div class="form-grid">
          <label>نام شعبه (شرکت ERPNext) <span class="req">*</span><input class="input" v-model.trim="form.company_name" :disabled="!!form.name" /></label>
          <label>اختصار (abbr)<input class="input" v-model.trim="form.abbr" :disabled="!!form.name" /></label>
          <label>عنوان نمایشی عمومی<input class="input" v-model.trim="form.restaurant_public_title" /></label>
          <label>تلفن<input class="input" v-model.trim="form.restaurant_branch_phone" /></label>
          <label>عرض جغرافیایی<input class="input" type="number" step="0.000001" v-model.number="form.restaurant_branch_lat" /></label>
          <label>طول جغرافیایی<input class="input" type="number" step="0.000001" v-model.number="form.restaurant_branch_lng" /></label>
          <label class="full-row">آدرس<input class="input" v-model.trim="form.restaurant_branch_address" /></label>
          <label class="check-row"><input type="checkbox" v-model="form.restaurant_branch_active" :true-value="1" :false-value="0" /> فعال</label>
        </div>
        <p class="error" v-if="formError">{{ formError }}</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveForm" :disabled="saving">{{ saving ? '...' : 'ذخیره شعبه' }}</button>
          <button type="button" class="tertiary-btn" @click="form = null">انصراف</button>
        </div>
      </div>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementBranchBoot,
  listManagementBranches,
  saveManagementBranch,
  updateManagementBranchStatus,
  transferManagementCustomerBranch,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const boot = ref({ branches: [], branch_count: 0, warehouses: [], max_recommended: 5 })
const branches = ref([])
const loading = ref(false)
const error = ref('')
const message = ref('')
const showActiveOnly = ref(false)
const form = ref(null)
const formError = ref('')
const saving = ref(false)
const transferForm = reactive({ customer: '', target_branch: '' })
const transferBusy = ref(false)
const transferError = ref('')

const activeBranches = computed(() => branches.value.filter((b) => b.is_active))

function formatQty(v) { return Number(v || 0).toLocaleString('fa-IR') }
function formatMoneyValue(v) { return formatMoneyUtil(Number(v || 0)) }

async function reload() {
  loading.value = true
  error.value = ''
  try {
    boot.value = await getManagementBranchBoot()
    const payload = await listManagementBranches({ active_only: showActiveOnly.value ? 1 : 0 })
    branches.value = payload.branches || boot.value.branches || []
  } catch (err) {
    error.value = err.message || 'دریافت شعب ناموفق بود.'
  } finally { loading.value = false }
}

function openForm(b) {
  formError.value = ''
  form.value = b
    ? { name: b.name, company_name: b.company_name, abbr: b.abbr, restaurant_public_title: b.label || '', restaurant_branch_phone: b.phone || '', restaurant_branch_lat: b.lat || 0, restaurant_branch_lng: b.lng || 0, restaurant_branch_address: b.address || '', restaurant_branch_active: b.is_active, restaurant_is_branch: 1 }
    : { name: '', company_name: '', abbr: '', restaurant_public_title: '', restaurant_branch_phone: '', restaurant_branch_lat: 0, restaurant_branch_lng: 0, restaurant_branch_address: '', restaurant_branch_active: 1, restaurant_is_branch: 1 }
}

async function saveForm() {
  if (!form.value) return
  saving.value = true
  formError.value = ''
  try {
    await saveManagementBranch({ ...form.value })
    message.value = 'شعبه ذخیره شد.'
    form.value = null
    await reload()
  } catch (err) {
    formError.value = err.message || 'ذخیره شعبه ناموفق بود.'
  } finally { saving.value = false }
}

async function toggleBranch(b) {
  try {
    await updateManagementBranchStatus({ name: b.name, is_active: b.is_active ? 0 : 1 })
    await reload()
  } catch (err) { error.value = err.message || 'تغییر وضعیت ناموفق بود.' }
}

async function doTransfer() {
  transferError.value = ''
  if (!transferForm.customer || !transferForm.target_branch) {
    transferError.value = 'مشتری و شعبه مقصد الزامی است.'
    return
  }
  transferBusy.value = true
  try {
    const payload = await transferManagementCustomerBranch({ ...transferForm })
    message.value = `مشتری ${payload.customer} به «${payload.target_branch || transferForm.target_branch}» منتقل شد.`
    transferForm.customer = ''
    await reload()
  } catch (err) {
    transferError.value = err.message || 'انتقال مشتری ناموفق بود.'
  } finally { transferBusy.value = false }
}

onMounted(reload)
</script>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; margin-bottom: 0.75rem; }
.link-btn { font-size: 0.85rem; color: var(--mg-primary); text-decoration: underline; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.65rem; margin-bottom: 0.7rem; }
.form-grid label { display: grid; gap: 0.3rem; font-size: 0.86rem; }
.full-row { grid-column: 1 / -1; }
.row-actions { white-space: nowrap; display: flex; gap: 0.3rem; flex-wrap: wrap; }
.shared-list { margin: 0; padding-inline-start: 1.1rem; display: grid; gap: 0.45rem; font-size: 0.88rem; }
</style>
