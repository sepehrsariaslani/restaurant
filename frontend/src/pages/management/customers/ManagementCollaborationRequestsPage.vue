<template>
  <ManagementPageScaffold title="درخواست‌های همکاری" subtitle="درخواست سازمان‌ها، باشگاه‌ها و مربی‌ها را بررسی کنید و موارد تأییدشده را به مشتری اصلی وصل کنید.">
    <template #actions><button type="button" class="secondary-btn" :disabled="loading" @click="load">{{ loading ? 'در حال دریافت…' : 'بروزرسانی' }}</button></template>

    <div class="collab-admin-kpis">
      <article class="total-box"><small>کل درخواست‌ها</small><strong>{{ rows.length.toLocaleString('fa-IR') }}</strong></article>
      <article class="total-box"><small>نیازمند بررسی</small><strong>{{ pendingCount.toLocaleString('fa-IR') }}</strong></article>
      <article class="total-box"><small>تأییدشده</small><strong>{{ approvedCount.toLocaleString('fa-IR') }}</strong></article>
    </div>

    <ManagementSurfaceCard title="درخواست‌های ورودی" subtitle="انتخاب هر ردیف، اطلاعات و برنامهٔ پیشنهادی همان مجموعه را نمایش می‌دهد.">
      <div class="toolbar collab-admin-toolbar">
        <label class="collab-status-filter">وضعیت
          <select v-model="statusFilter" class="input" @change="load"><option value="">همهٔ وضعیت‌ها</option><option>جدید</option><option>در حال بررسی</option><option>تأییدشده</option><option>ردشده</option></select>
        </label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </div>
      <p v-if="loading" class="muted" role="status">در حال دریافت درخواست‌ها…</p>
      <ManagementListView v-else :columns="columns" :rows="rows" row-key="name" :row-clickable="true" @row-click="selectRow">
        <template #cell-organization_name="{ row }"><strong>{{ row.organization_name }}</strong><small class="d-block muted">{{ row.collaboration_type }}</small></template>
        <template #cell-contact_name="{ row }">{{ row.contact_name }}<small class="d-block muted" dir="ltr">{{ row.mobile }}</small></template>
        <template #cell-frequency="{ row }">{{ row.frequency || 'توافق شود' }}</template>
        <template #cell-status="{ value }"><span class="pill" :class="statusTone(value)">{{ value }}</span></template>
        <template #cell-creation="{ value }">{{ formatDate(value) }}</template>
        <template #empty>درخواستی برای این فیلتر پیدا نشد.</template>
      </ManagementListView>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard v-if="selected" class="collab-request-detail" :title="selected.organization_name" :subtitle="`${selected.collaboration_type} · ${selected.name}`">
      <template #head><button type="button" class="tertiary-btn" @click="selected = null">بستن جزئیات</button></template>
      <div class="request-detail-grid">
        <div><small>رابط مجموعه</small><strong>{{ selected.contact_name }}</strong></div>
        <div><small>شماره تماس</small><strong dir="ltr">{{ selected.mobile }}</strong></div>
        <div><small>ایمیل</small><strong dir="ltr">{{ selected.email || 'ثبت نشده' }}</strong></div>
        <div><small>تعداد اعضا / کارکنان</small><strong>{{ countLabel(selected.expected_members) }}</strong></div>
        <div><small>وعده در هر نوبت</small><strong>{{ countLabel(selected.meal_count) }}</strong></div>
        <div><small>تناوب و زمان پیشنهادی</small><strong>{{ selected.frequency || 'توافق شود' }}<template v-if="selected.delivery_time"> · {{ selected.delivery_time }}</template></strong></div>
        <div class="request-detail-wide"><small>نشانی</small><strong>{{ selected.address || '—' }}</strong></div>
        <div class="request-detail-wide"><small>روزهای هفته</small><strong>{{ weekdayLabel(selected.weekdays) }}</strong></div>
        <div class="request-detail-wide"><small>توضیحات</small><p>{{ selected.details || 'توضیح دیگری ثبت نشده است.' }}</p></div>
        <div v-if="selected.customer" class="request-detail-wide linked-customer"><small>مشتری متصل‌شده</small><a :href="`/management/customer?customer=${encodeURIComponent(selected.customer)}`">{{ selected.customer }}</a><span>برای فعال‌کردن سفارش سازمانی، قرارداد و معین‌ها را از بخش باشگاه مشتریان تنظیم کنید.</span></div>
      </div>

      <label class="collab-review-note"><span>یادداشت پیگیری</span><textarea v-model="reviewNote" class="input" rows="2" maxlength="1000" placeholder="نتیجهٔ تماس یا موارد نیازمند پیگیری" /></label>
      <div v-if="selected.collaboration_type === 'مربی و شاگردان'" class="coach-terms-grid">
        <div class="coach-customer-picker">
          <label>انتخاب Customer موجود
            <div class="coach-customer-search"><input v-model.trim="coachCustomerSearch" class="input" placeholder="شماره، نام، ایمیل یا شناسه" @keydown.enter.prevent="searchCoachCustomers" /><button type="button" class="secondary-btn" :disabled="searchingCustomers || coachCustomerSearch.length < 2" @click="searchCoachCustomers">{{ searchingCustomers ? '…' : 'جستجو' }}</button></div>
          </label>
          <div v-if="coachCustomerCandidates.length" class="coach-customer-results"><button v-for="row in coachCustomerCandidates" :key="row.name" type="button" :class="{ selected: coachCustomer === row.name }" @click="coachCustomer = row.name"><strong>{{ row.customer_name || row.name }}</strong><small dir="ltr">{{ row.mobile_no || '—' }} · {{ row.email_id || row.name }}</small></button></div>
          <p v-if="coachCustomer">انتخاب‌شده: <strong>{{ coachCustomer }}</strong></p>
          <small>شمارهٔ فرم همکاری به‌تنهایی حساب مشتری را متصل نمی‌کند. مربی باید یک حساب Customer موجود باشد.</small>
        </div>
        <label class="coach-group-field">Customer Group مربی<select v-model="coachCustomerGroup" class="input" required><option value="">انتخاب گروه مشتری</option><option v-for="group in customerGroups" :key="group.name" :value="group.name">{{ group.customer_group_name || group.name }}<template v-if="Number(group.restaurant_default_discount_percent || 0)"> · تخفیف {{ Number(group.restaurant_default_discount_percent).toLocaleString('fa-IR') }}٪</template></option></select></label>
        <label>تخفیف اعضای دعوت‌شده (%)<input v-model.number="coachDiscountPercent" class="input" type="number" min="0" max="50" step="0.5" /></label>
        <label>سهم کش‌بک مربی (%)<input v-model.number="coachCommissionPercent" class="input" type="number" min="0" max="50" step="0.5" /></label>
        <p>درصد گروه به خریدهای خود مربی تعلق دارد. تخفیف شاگرد و کوپن جمع نمی‌شوند؛ برنده از سرور انتخاب می‌شود. سهم مربی پس از تحویل و تسویه به کش‌بک قابل خرج و غیرقابل‌برداشت می‌رود.</p>
      </div>
      <p v-if="message" class="success-message" role="status">{{ message }}</p>
      <div v-if="actionError" class="error" role="alert">{{ actionError }}</div>
      <div class="collab-review-actions">
        <button type="button" class="secondary-btn" :disabled="saving" @click="review('review')">در حال بررسی</button>
        <button v-if="selected.status !== 'تأییدشده'" type="button" class="primary-btn" :disabled="saving || (selected.collaboration_type === 'مربی و شاگردان' && !coachCustomer)" @click="review('approve')">{{ saving ? 'در حال ثبت…' : selected.collaboration_type === 'مربی و شاگردان' ? 'تأیید مربی انتخاب‌شده' : 'تأیید و ایجاد پروفایل مشتری' }}</button>
        <button v-if="selected.status !== 'ردشده'" type="button" class="danger-btn" :disabled="saving" @click="review('reject')">رد درخواست</button>
      </div>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import { listManagementCollaborationRequests, listManagementCustomerGroups, reviewManagementCollaborationRequest, searchManagementCoachCustomers } from '@/utils/api'

const columns = [
  { key: 'organization_name', label: 'مجموعه' },
  { key: 'contact_name', label: 'رابط' },
  { key: 'frequency', label: 'برنامهٔ پیشنهادی' },
  { key: 'status', label: 'وضعیت' },
  { key: 'creation', label: 'زمان ثبت' },
]
const rows = ref([])
const statusFilter = ref('')
const selected = ref(null)
const reviewNote = ref('')
const coachDiscountPercent = ref(5)
const coachCommissionPercent = ref(5)
const coachCustomerGroup = ref('')
const customerGroups = ref([])
const coachCustomerSearch = ref('')
const coachCustomerCandidates = ref([])
const coachCustomer = ref('')
const searchingCustomers = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const actionError = ref('')
const message = ref('')
const pendingCount = computed(() => rows.value.filter((row) => ['جدید', 'در حال بررسی'].includes(row.status)).length)
const approvedCount = computed(() => rows.value.filter((row) => row.status === 'تأییدشده').length)

function statusTone(status) { return status === 'تأییدشده' ? 'ok' : status === 'ردشده' ? 'warn' : '' }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('fa-IR') : '—' }
function countLabel(value) { return Number(value) > 0 ? Number(value).toLocaleString('fa-IR') + ' نفر' : 'توافق شود' }
function weekdayLabel(value) {
  try { const days = JSON.parse(value || '[]'); return Array.isArray(days) && days.length ? days.join('، ') : '—' } catch { return '—' }
}
function selectRow(row) { selected.value = row; reviewNote.value = row.review_note || ''; coachDiscountPercent.value = 5; coachCommissionPercent.value = 5; coachCustomerGroup.value = customerGroups.value[0]?.name || ''; coachCustomer.value = row.customer || ''; coachCustomerSearch.value = row.mobile || ''; coachCustomerCandidates.value = []; actionError.value = ''; message.value = '' }

async function searchCoachCustomers() {
  if (coachCustomerSearch.value.length < 2 || searchingCustomers.value) return
  searchingCustomers.value = true; actionError.value = ''
  try { const data = await searchManagementCoachCustomers(coachCustomerSearch.value); coachCustomerCandidates.value = data?.customers || [] }
  catch (err) { actionError.value = err?.message || 'جستجوی مشتری ناموفق بود.' }
  finally { searchingCustomers.value = false }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [payload, groupPayload] = await Promise.all([
      listManagementCollaborationRequests({ status: statusFilter.value }),
      listManagementCustomerGroups(),
    ])
    rows.value = payload?.requests || []
    customerGroups.value = groupPayload?.groups || []
    if (!coachCustomerGroup.value) coachCustomerGroup.value = customerGroups.value[0]?.name || ''
    if (selected.value) selected.value = rows.value.find((row) => row.name === selected.value.name) || null
  } catch (err) { error.value = err?.message || 'دریافت درخواست‌ها انجام نشد.' }
  finally { loading.value = false }
}

async function review(decision) {
  if (!selected.value || saving.value) return
  saving.value = true
  actionError.value = ''
  message.value = ''
  try {
    const payload = await reviewManagementCollaborationRequest({ name: selected.value.name, decision, note: reviewNote.value, coach_discount_percent: coachDiscountPercent.value, coach_commission_percent: coachCommissionPercent.value, customer_group: coachCustomerGroup.value, customer: coachCustomer.value })
    const updated = payload?.request
    if (updated) {
      const index = rows.value.findIndex((row) => row.name === updated.name)
      if (index >= 0) rows.value[index] = updated
      selected.value = updated
    }
    message.value = decision === 'approve' ? 'درخواست تأیید شد و پروفایل مشتری در سیستم ایجاد شد.' : decision === 'reject' ? 'درخواست رد شد.' : 'وضعیت درخواست به «در حال بررسی» تغییر کرد.'
  } catch (err) { actionError.value = err?.message || 'ثبت نتیجهٔ بررسی انجام نشد.' }
  finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.collab-admin-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; }
.collab-admin-toolbar { align-items: flex-end; }
.collab-status-filter { display: grid; gap: .35rem; min-width: min(100%, 220px); color: var(--mg-text-muted); font-size: .78rem; font-weight: 800; }
.collab-status-filter .input, .collab-review-note .input { min-height: 42px; border: 1px solid var(--mg-border-light); border-radius: 10px; background: var(--mg-bg-surface); color: var(--mg-text-main); padding: .55rem .7rem; font: inherit; }
.request-detail-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin-bottom: 1rem; }
.request-detail-grid > div { display: grid; align-content: start; gap: .25rem; min-width: 0; padding: .75rem; border: 1px solid var(--mg-border-light); border-radius: 12px; background: var(--mg-bg-surface); }
.request-detail-grid small, .collab-review-note > span { color: var(--mg-text-muted); font-size: .73rem; }
.request-detail-grid strong { overflow-wrap: anywhere; color: var(--mg-text-main); font-size: .86rem; line-height: 1.7; }
.request-detail-wide { grid-column: 1 / -1; }
.request-detail-grid p { margin: 0; color: var(--mg-text-main); font-size: .84rem; line-height: 1.8; white-space: pre-wrap; }
.linked-customer { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: .4rem 1rem; border-color: color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light)) !important; }
.linked-customer small { grid-column: 1 / -1; }
.linked-customer a { color: var(--mg-primary); font-weight: 800; }
.linked-customer span { color: var(--mg-text-muted); font-size: .74rem; }
.collab-review-note { display: grid; gap: .4rem; margin: .5rem 0 1rem; }
.collab-review-note .input { resize: vertical; }
.coach-terms-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; margin-bottom: 1rem; }
.coach-customer-picker { grid-column: 1 / -1; display: grid; gap: .4rem; }
.coach-customer-picker label { display: grid; gap: .35rem; color: var(--mg-text-muted); font-size: .75rem; }
.coach-customer-picker small, .coach-customer-picker p { margin: 0; color: var(--mg-text-muted); font-size: .72rem; line-height: 1.7; }
.coach-customer-search { display: flex; gap: .45rem; }
.coach-customer-search .input { flex: 1; min-width: 0; min-height: 42px; border: 1px solid var(--mg-border-light); border-radius: 10px; padding: .5rem .65rem; background: var(--mg-bg-surface); color: var(--mg-text-main); font: inherit; }
.coach-customer-results { display: grid; max-height: 190px; overflow: auto; border: 1px solid var(--mg-border-light); border-radius: 10px; }
.coach-customer-results button { display: grid; gap: .18rem; padding: .55rem .7rem; border: 0; border-bottom: 1px solid var(--mg-border-light); background: var(--mg-bg-surface); color: var(--mg-text-main); text-align: start; cursor: pointer; }
.coach-customer-results button.selected { background: color-mix(in srgb, var(--mg-primary) 10%, var(--mg-bg-surface)); }
.coach-customer-results strong { font-size: .78rem; }
.coach-terms-grid label { display: grid; gap: .35rem; color: var(--mg-text-muted); font-size: .75rem; }
.coach-group-field { grid-column: 1 / -1; }
.coach-terms-grid .input { min-height: 42px; border: 1px solid var(--mg-border-light); border-radius: 10px; background: var(--mg-bg-surface); color: var(--mg-text-main); padding: .5rem .65rem; font: inherit; }
.coach-terms-grid p { grid-column: 1 / -1; margin: 0; color: var(--mg-text-muted); font-size: .76rem; line-height: 1.8; }
.collab-review-actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.danger-btn { min-height: 42px; padding: .55rem .8rem; border: 1px solid var(--mg-danger, #bd3b32); border-radius: 10px; background: transparent; color: var(--mg-danger, #bd3b32); font: inherit; font-weight: 800; cursor: pointer; }
.collab-review-actions button:disabled { opacity: .55; cursor: wait; }
@media (max-width: 700px) { .request-detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 470px) { .collab-admin-kpis { grid-template-columns: 1fr; } .request-detail-grid { grid-template-columns: 1fr; } .request-detail-wide { grid-column: auto; } }
</style>
