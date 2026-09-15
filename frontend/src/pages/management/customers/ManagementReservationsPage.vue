<template>
  <ManagementPageScaffold title="رزرواسیون" subtitle="رزرو آنلاین و تلفنی میز، فیلتر بر اساس تاریخ/جایگاه/وضعیت و یادآوری پیامکی خودکار">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reload" :disabled="loading">{{ loading ? '...' : 'بروزرسانی' }}</button>
      <button type="button" class="primary-btn" @click="openForm()">رزرو جدید</button>
    </template>

    <div class="totals-grid">
      <div class="total-box"><small>رزروهای امروز</small><strong>{{ formatQty(todayTotal) }}</strong></div>
      <div class="total-box" v-for="(count, status) in boot.today_counts || {}" :key="status"><small>{{ status }} (امروز)</small><strong>{{ formatQty(count) }}</strong></div>
    </div>

    <ManagementSurfaceCard title="فیلتر رزروها" subtitle="جستجو بر اساس تاریخ، جایگاه و وضعیت">
      <div class="toolbar">
        <label class="date-label">از تاریخ<input class="input" type="date" v-model="filters.date_from" @change="loadList" /></label>
        <label class="date-label">تا تاریخ<input class="input" type="date" v-model="filters.date_to" @change="loadList" /></label>
        <SearchableDropdown v-model="filters.status" :options="statusOptions" placeholder="همه وضعیت‌ها" search-placeholder="جستجوی وضعیت..." @update:model-value="loadList" />
        <SearchableDropdown v-model="filters.table" :options="tableOptions" placeholder="همه جایگاه‌ها" search-placeholder="جستجوی میز یا سالن..." @update:model-value="loadList" />
        <input class="input" v-model.trim="filters.search" placeholder="جستجوی نام یا موبایل..." @keyup.enter="loadList" />
        <button type="button" class="secondary-btn" @click="loadList">جستجو</button>
      </div>
      <p class="muted hint-line">
        لینک رزرو آنلاین برای مشتریان: <code class="link-code">{{ publicUrl }}</code> —
        یادآوری پیامکی {{ boot.settings?.reminder_hours || 2 }} ساعت قبل از رزرو به‌صورت خودکار ارسال می‌شود (در تنظیمات رزرو).
      </p>
      <p class="muted" v-if="loading">در حال دریافت رزروها...</p>
      <p class="error" v-if="error">{{ error }}</p>
      <p class="success-msg" v-if="message">{{ message }}</p>
      <ManagementListView
        v-if="!loading"
        :columns="reservationColumns"
        :rows="rows"
        row-key="name"
        :row-clickable="true"
        @row-click="openForm"
      >
        <template #cell-customer_name="{ row }">
          <strong>{{ row.customer_name || '—' }}</strong><br><small class="muted">{{ row.mobile }}</small>
        </template>
        <template #cell-party_size="{ value }">{{ formatQty(value) }}</template>
        <template #cell-table_label="{ value }">{{ value || '—' }}</template>
        <template #cell-source="{ value }"><span class="pill">{{ value || '—' }}</span></template>
        <template #cell-reminder_sent="{ row }"><span class="pill" :class="{ ok: row.reminder_sent }">{{ row.reminder_sent ? 'ارسال‌شده' : '—' }}</span></template>
        <template #cell-status="{ row }"><span class="pill" :class="statusClass(row.status)">{{ row.status }}</span></template>
        <template #cell-actions="{ row }">
          <span class="row-actions">
            <template v-if="row.status === 'در انتظار'">
              <button type="button" class="tertiary-btn" @click="setStatus(row, 'تأییدشده')">تأیید</button>
            </template>
            <template v-if="row.status === 'تأییدشده'">
              <button type="button" class="tertiary-btn" @click="setStatus(row, 'نشست')">نشست</button>
              <button type="button" class="tertiary-btn" @click="setStatus(row, 'حاضر نشد')">حاضر نشد</button>
            </template>
            <button type="button" class="tertiary-btn" @click="openForm(row)">ویرایش</button>
            <button type="button" class="tertiary-btn danger" @click="setStatus(row, 'لغوشده')" v-if="row.status !== 'لغوشده'">لغو</button>
            <button type="button" class="tertiary-btn danger" @click="removeReservation(row)">حذف</button>
          </span>
        </template>
        <template #empty>رزروی مطابق فیلتر یافت نشد.</template>
      </ManagementListView>
    </ManagementSurfaceCard>

    <div v-if="form" class="popup-backdrop" @click.self="form = null">
      <div class="popup">
        <h3>{{ form.name ? 'ویرایش رزرو' : 'رزرو جدید (تلفنی/صندوق)' }}</h3>
        <div class="form-grid">
          <label>نام مهمان <span class="req">*</span><input class="input" v-model.trim="form.customer_name" /></label>
          <label>موبایل <span class="req">*</span><input class="input" v-model.trim="form.mobile" inputmode="tel" /></label>
          <label>تاریخ رزرو <span class="req">*</span><input class="input" type="date" v-model="form.reservation_date" /></label>
          <label>ساعت<input class="input" type="time" v-model="form.reservation_time" /></label>
          <label>تعداد نفرات<input class="input" type="number" min="1" v-model.number="form.party_size" /></label>
          <label>جایگاه (میز/اتاق/سالن)
            <SearchableDropdown v-model="form.restaurant_table" :options="tableAssignmentOptions" placeholder="— بدون تخصیص —" search-placeholder="جستجوی میز یا سالن..." />
          </label>
          <label>منشأ
            <SearchableDropdown v-model="form.source" :options="sourceOptions" placeholder="انتخاب منشأ" search-placeholder="جستجوی منشأ..." />
          </label>
          <ManagementNoteField
            v-model="form.note"
            class="full-row"
            label="یادداشت"
            rows="2"
            placeholder="درخواست ویژه یا توضیحات رزرو..."
          />
        </div>
        <p class="error" v-if="formError">{{ formError }}</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveForm" :disabled="saving">{{ saving ? '...' : 'ذخیره رزرو' }}</button>
          <button type="button" class="tertiary-btn" @click="form = null">انصراف</button>
        </div>
      </div>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  getManagementReservationBoot,
  listManagementReservations,
  saveManagementReservation,
  updateManagementReservationStatus,
  deleteManagementReservation,
} from '@/utils/api'

const boot = ref({ statuses: [], sources: [], tables: [], today_counts: {}, settings: {} })
const rows = ref([])
const loading = ref(false)
const error = ref('')
const message = ref('')
const filters = reactive({ date_from: '', date_to: '', status: '', table: '', search: '' })
const form = ref(null)
const formError = ref('')
const saving = ref(false)
const reservationColumns = [
  { key: 'customer_name', label: 'مهمان' },
  { key: 'reservation_date', label: 'تاریخ' },
  { key: 'reservation_time', label: 'ساعت' },
  { key: 'party_size', label: 'نفرات' },
  { key: 'table_label', label: 'جایگاه' },
  { key: 'source', label: 'منشأ' },
  { key: 'reminder_sent', label: 'یادآوری' },
  { key: 'status', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const statusOptions = computed(() => [
  { value: '', label: 'همه وضعیت‌ها' },
  ...(boot.value.statuses || []).map((status) => ({ value: status, label: status })),
])
const tableOptionRows = computed(() => (boot.value.tables || []).map((table) => ({
  value: table.name,
  label: String(table.table_name || table.name) + ' (' + String(table.location || '—') + ')',
})))
const tableOptions = computed(() => [{ value: '', label: 'همه جایگاه‌ها' }, ...tableOptionRows.value])
const tableAssignmentOptions = computed(() => [{ value: '', label: '— بدون تخصیص —' }, ...tableOptionRows.value])
const sourceOptions = computed(() => (boot.value.sources || []).map((source) => ({ value: source, label: source })))

const publicUrl = computed(() => `${window.location.origin}/reserve`)
const todayTotal = computed(() => Object.values(boot.value.today_counts || {}).reduce((a, b) => a + Number(b || 0), 0))

function formatQty(v) { return Number(v || 0).toLocaleString('fa-IR') }
function statusClass(s) {
  if (s === 'تأییدشده' || s === 'نشست') return 'ok'
  if (s === 'لغوشده' || s === 'حاضر نشد') return 'warn'
  return ''
}

async function loadBoot() {
  try { boot.value = await getManagementReservationBoot() } catch (err) { error.value = err.message || '' }
}
async function loadList() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementReservations({ ...filters, limit: 200 })
    rows.value = payload.reservations || payload.rows || []
  } catch (err) {
    error.value = err.message || 'دریافت رزروها ناموفق بود.'
  } finally { loading.value = false }
}
async function reload() { await loadBoot(); await loadList() }

function openForm(r) {
  formError.value = ''
  form.value = r
    ? { ...r }
    : { name: '', customer_name: '', mobile: '', reservation_date: boot.value.today || '', reservation_time: '19:00', party_size: 2, restaurant_table: '', source: 'تلفنی', note: '' }
}

async function saveForm() {
  if (!form.value) return
  saving.value = true
  formError.value = ''
  try {
    await saveManagementReservation({ ...form.value })
    message.value = 'رزرو ذخیره شد.'
    form.value = null
    await reload()
  } catch (err) {
    formError.value = err.message || 'ذخیره رزرو ناموفق بود.'
  } finally { saving.value = false }
}

async function setStatus(r, status) {
  try {
    await updateManagementReservationStatus({ name: r.name, status })
    await reload()
  } catch (err) { error.value = err.message || 'تغییر وضعیت ناموفق بود.' }
}

async function removeReservation(r) {
  if (!window.confirm(`رزرو «${r.customer_name}» حذف شود؟`)) return
  try { await deleteManagementReservation(r.name); await reload() } catch (err) { error.value = err.message || '' }
}

onMounted(reload)
</script>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.75rem; }
.toolbar .input { min-width: 140px; flex: 0 1 auto; }
.date-label { display: inline-flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--mg-text-muted); }
.link-code { direction: ltr; display: inline-block; background: rgba(90, 74, 58, 0.08); border-radius: 6px; padding: 0.1rem 0.45rem; font-size: 0.8rem; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.65rem; margin-bottom: 0.7rem; }
.form-grid label { display: grid; gap: 0.3rem; font-size: 0.86rem; }
.full-row { grid-column: 1 / -1; }
.row-actions { white-space: nowrap; display: flex; gap: 0.3rem; flex-wrap: wrap; }
</style>
