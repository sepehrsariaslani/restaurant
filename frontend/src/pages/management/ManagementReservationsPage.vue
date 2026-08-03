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
        <select class="input" v-model="filters.status" @change="loadList">
          <option value="">همه وضعیت‌ها</option>
          <option v-for="s in boot.statuses || []" :key="s" :value="s">{{ s }}</option>
        </select>
        <select class="input" v-model="filters.table" @change="loadList">
          <option value="">همه جایگاه‌ها</option>
          <option v-for="t in boot.tables || []" :key="t.name" :value="t.name">{{ t.table_name || t.name }} ({{ t.location || '—' }})</option>
        </select>
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
      <div v-if="!loading && rows.length" class="table-wrap">
        <table class="data-table">
          <thead><tr><th>مهمان</th><th>تاریخ</th><th>ساعت</th><th>نفرات</th><th>جایگاه</th><th>منشأ</th><th>یادآوری</th><th>وضعیت</th><th></th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.name">
              <td><strong>{{ r.customer_name || '—' }}</strong><br><small class="muted">{{ r.mobile }}</small></td>
              <td>{{ r.reservation_date }}</td>
              <td>{{ r.reservation_time }}</td>
              <td>{{ formatQty(r.party_size) }}</td>
              <td>{{ r.table_label || '—' }}</td>
              <td><span class="pill">{{ r.source }}</span></td>
              <td><span class="pill" :class="{ ok: r.reminder_sent }">{{ r.reminder_sent ? 'ارسال‌شده' : '—' }}</span></td>
              <td><span class="pill" :class="statusClass(r.status)">{{ r.status }}</span></td>
              <td class="row-actions">
                <template v-if="r.status === 'در انتظار'">
                  <button type="button" class="tertiary-btn" @click="setStatus(r, 'تأییدشده')">تأیید</button>
                </template>
                <template v-if="r.status === 'تأییدشده'">
                  <button type="button" class="tertiary-btn" @click="setStatus(r, 'نشست')">نشست</button>
                  <button type="button" class="tertiary-btn" @click="setStatus(r, 'حاضر نشد')">حاضر نشد</button>
                </template>
                <button type="button" class="tertiary-btn" @click="openForm(r)">ویرایش</button>
                <button type="button" class="tertiary-btn danger" @click="setStatus(r, 'لغوشده')" v-if="r.status !== 'لغوشده'">لغو</button>
                <button type="button" class="tertiary-btn danger" @click="removeReservation(r)">حذف</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted" v-else-if="!loading">رزروی مطابق فیلتر یافت نشد.</p>
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
            <select class="input" v-model="form.restaurant_table">
              <option value="">— بدون تخصیص —</option>
              <option v-for="t in boot.tables || []" :key="t.name" :value="t.name">{{ t.table_name || t.name }} ({{ t.location || '—' }})</option>
            </select>
          </label>
          <label>منشأ
            <select class="input" v-model="form.source"><option v-for="s in boot.sources || []" :key="s" :value="s">{{ s }}</option></select>
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
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
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
