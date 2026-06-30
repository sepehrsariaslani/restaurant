<template>
  <ManagementPageScaffold title="مدیریت میزها" subtitle="مدیریت میزها، رزروها و سشن‌های فعال سالن">
    <ManagementSurfaceCard tone="accent">
      <div class="hero-toolbar">
        <div class="hero-stats">
          <article class="stat-card">
            <small>کل میزها</small>
            <strong>{{ tables.length.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--success">
            <small>میز خالی</small>
            <strong>{{ emptyTablesCount.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--warning">
            <small>در انتظار</small>
            <strong>{{ waitingTablesCount.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--danger">
            <small>اشغال</small>
            <strong>{{ occupiedTablesCount.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card">
            <small>رزروها</small>
            <strong>{{ reservations.length.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card">
            <small>سشن‌ها</small>
            <strong>{{ sessions.length.toLocaleString('fa-IR') }}</strong>
          </article>
        </div>

        <div class="hero-actions">
          <input
            v-model.trim="search"
            class="input hero-search"
            placeholder="جستجو بر اساس شماره میز، لوکیشن، مشتری یا موبایل"
            @keyup.enter="loadTables"
          />
          <button class="primary-btn" type="button" :disabled="loading" @click="loadTables">
            {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
          </button>
        </div>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری اطلاعات میزها...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <section class="grid-2" v-if="!loading">
      <ManagementSurfaceCard title="میزها" subtitle="ویرایش سریع وضعیت، شماره و لوکیشن میز">
        <ManagementDataTable :columns="tableColumns" :rows="filteredTables" row-key="name">
          <template #cell-table_number="{ row }">
            <input class="input inline-input" v-model.trim="row.table_number" />
          </template>
          <template #cell-status="{ row }">
            <select class="select inline-input" v-model="row.status">
              <option value="empty">خالی</option>
              <option value="waiting">در انتظار</option>
              <option value="occupied">اشغال</option>
            </select>
          </template>
          <template #cell-location="{ row }">
            <input class="input inline-input" v-model.trim="row.location" />
          </template>
          <template #cell-is_active="{ row }">
            <label class="check-inline">
              <input type="checkbox" v-model="row.is_active" :true-value="1" :false-value="0" />
              <span>{{ Number(row.is_active || 0) === 1 ? 'فعال' : 'غیرفعال' }}</span>
            </label>
          </template>
          <template #cell-active_session="{ value }">
            <span>{{ value || '-' }}</span>
          </template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button class="secondary-btn" type="button" :disabled="savingMap[row.name]" @click="saveTable(row)">
                {{ savingMap[row.name] ? 'در حال ذخیره...' : 'ذخیره' }}
              </button>
            </div>
          </template>
        </ManagementDataTable>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="رزرو میزها" subtitle="به‌روزرسانی رزروهای ثبت‌شده">
        <ManagementDataTable :columns="reservationColumns" :rows="filteredReservations" row-key="name">
          <template #cell-customer_name="{ row }">
            <input class="input inline-input" v-model.trim="row.customer_name" />
          </template>
          <template #cell-mobile="{ row }">
            <input class="input inline-input" v-model.trim="row.mobile" />
          </template>
          <template #cell-branch="{ row }">
            <input class="input inline-input" v-model.trim="row.branch" />
          </template>
          <template #cell-table="{ row }">
            <select class="select inline-input" v-model="row.table">
              <option value="">بدون میز</option>
              <option v-for="table in tables" :key="`table-opt-${table.name}`" :value="table.name">
                {{ table.table_number || table.name }}
              </option>
            </select>
          </template>
          <template #cell-reservation_date="{ row }">
            <input class="input inline-input" type="date" v-model="row.reservation_date" />
          </template>
          <template #cell-reservation_time="{ row }">
            <input class="input inline-input" type="time" v-model="row.reservation_time" />
          </template>
          <template #cell-guest_count="{ row }">
            <input class="input inline-input" type="number" min="1" v-model.number="row.guest_count" />
          </template>
          <template #cell-status="{ row }">
            <select class="select inline-input" v-model="row.status">
              <option value="pending">pending</option>
              <option value="confirmed">confirmed</option>
              <option value="cancelled">cancelled</option>
              <option value="completed">completed</option>
            </select>
          </template>
          <template #cell-actions="{ row }">
            <div class="row-actions">
              <button class="secondary-btn" type="button" :disabled="savingMap[row.name]" @click="saveReservation(row)">
                {{ savingMap[row.name] ? 'در حال ذخیره...' : 'ذخیره' }}
              </button>
            </div>
          </template>
        </ManagementDataTable>
      </ManagementSurfaceCard>
    </section>

    <ManagementSurfaceCard v-if="!loading" title="سشن میزها" subtitle="کنترل وضعیت نشست‌های فعال/بسته و مبلغ تاییدشده">
      <ManagementDataTable :columns="sessionColumns" :rows="filteredSessions" row-key="name">
        <template #cell-table="{ value }">
          <span>{{ tableLabelMap[value] || value || '-' }}</span>
        </template>
        <template #cell-status="{ row }">
          <select class="select inline-input" v-model="row.status">
            <option value="active">active</option>
            <option value="closed">closed</option>
          </select>
        </template>
        <template #cell-opened_at="{ value }">
          <span>{{ formatDateTime(value) }}</span>
        </template>
        <template #cell-closed_at="{ value }">
          <span>{{ formatDateTime(value) }}</span>
        </template>
        <template #cell-total_confirmed_amount="{ value }">
          <span>{{ formatMoney(value, currency) }}</span>
        </template>
        <template #cell-note="{ row }">
          <input class="input inline-input" v-model.trim="row.note" />
        </template>
        <template #cell-actions="{ row }">
          <div class="row-actions">
            <button class="secondary-btn" type="button" :disabled="savingMap[row.name]" @click="saveSession(row)">
              {{ savingMap[row.name] ? 'در حال ذخیره...' : 'ذخیره' }}
            </button>
          </div>
        </template>
      </ManagementDataTable>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementTables,
  updateManagementTable,
  updateManagementTableReservation,
  updateManagementTableSession,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const search = ref('')
const currency = ref('IRR')

const tables = ref([])
const reservations = ref([])
const sessions = ref([])
const savingMap = reactive({})

const tableColumns = [
  { key: 'table_number', label: 'شماره میز' },
  { key: 'status', label: 'وضعیت' },
  { key: 'location', label: 'لوکیشن/شعبه' },
  { key: 'is_active', label: 'فعال' },
  { key: 'active_session', label: 'سشن فعال' },
  { key: 'actions', label: 'عملیات' },
]

const reservationColumns = [
  { key: 'customer_name', label: 'مشتری' },
  { key: 'mobile', label: 'موبایل' },
  { key: 'branch', label: 'شعبه' },
  { key: 'table', label: 'میز' },
  { key: 'reservation_date', label: 'تاریخ' },
  { key: 'reservation_time', label: 'ساعت' },
  { key: 'guest_count', label: 'نفرات' },
  { key: 'status', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

const sessionColumns = [
  { key: 'table', label: 'میز' },
  { key: 'status', label: 'وضعیت' },
  { key: 'opened_at', label: 'شروع' },
  { key: 'closed_at', label: 'پایان' },
  { key: 'total_confirmed_amount', label: 'مبلغ تاییدشده' },
  { key: 'note', label: 'یادداشت' },
  { key: 'actions', label: 'عملیات' },
]

const normalizedSearch = computed(() => String(search.value || '').trim().toLowerCase())

const tableLabelMap = computed(() => {
  return tables.value.reduce((acc, row) => {
    acc[row.name] = row.table_number || row.name
    return acc
  }, {})
})

const filteredTables = computed(() => {
  if (!normalizedSearch.value) return tables.value
  return tables.value.filter((row) => {
    const haystack = [row.table_number, row.location, row.status, row.notes]
      .map((value) => String(value || '').toLowerCase())
      .join(' ')
    return haystack.includes(normalizedSearch.value)
  })
})

const filteredReservations = computed(() => {
  if (!normalizedSearch.value) return reservations.value
  return reservations.value.filter((row) => {
    const haystack = [row.customer_name, row.mobile, row.branch, row.table, row.status, row.note]
      .map((value) => String(value || '').toLowerCase())
      .join(' ')
    return haystack.includes(normalizedSearch.value)
  })
})

const filteredSessions = computed(() => {
  if (!normalizedSearch.value) return sessions.value
  return sessions.value.filter((row) => {
    const haystack = [row.table, row.status, row.note]
      .map((value) => String(value || '').toLowerCase())
      .join(' ')
    return haystack.includes(normalizedSearch.value)
  })
})

const emptyTablesCount = computed(() => tables.value.filter((row) => String(row.status || '').toLowerCase() === 'empty').length)
const waitingTablesCount = computed(() => tables.value.filter((row) => String(row.status || '').toLowerCase() === 'waiting').length)
const occupiedTablesCount = computed(() => tables.value.filter((row) => String(row.status || '').toLowerCase() === 'occupied').length)

function formatDateTime(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(text))
  } catch (_) {
    return text
  }
}

async function loadTables() {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = await getManagementTables()
    tables.value = Array.isArray(payload?.tables) ? payload.tables : []
    reservations.value = Array.isArray(payload?.reservations) ? payload.reservations : []
    sessions.value = Array.isArray(payload?.sessions) ? payload.sessions : []
    currency.value = String(payload?.currency || 'IRR').trim() || 'IRR'
  } catch (loadError) {
    error.value = loadError.message || 'بارگذاری میزها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function withSaveState(key, action) {
  savingMap[key] = true
  error.value = ''
  successMessage.value = ''
  try {
    await action()
    successMessage.value = 'تغییرات با موفقیت ذخیره شد.'
    await loadTables()
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره اطلاعات ناموفق بود.'
  } finally {
    savingMap[key] = false
  }
}

async function saveTable(row) {
  await withSaveState(row.name, () =>
    updateManagementTable({
      name: row.name,
      table_number: row.table_number,
      status: row.status,
      is_active: Number(row.is_active || 0) ? 1 : 0,
      location: row.location,
      notes: row.notes,
      active_session: row.active_session,
    }),
  )
}

async function saveReservation(row) {
  await withSaveState(row.name, () =>
    updateManagementTableReservation({
      name: row.name,
      customer_name: row.customer_name,
      mobile: row.mobile,
      branch: row.branch,
      table: row.table,
      reservation_date: row.reservation_date,
      reservation_time: row.reservation_time,
      guest_count: Number(row.guest_count || 1),
      status: row.status,
      note: row.note,
    }),
  )
}

async function saveSession(row) {
  await withSaveState(row.name, () =>
    updateManagementTableSession({
      name: row.name,
      status: row.status,
      note: row.note,
    }),
  )
}

loadTables()
</script>

<style scoped>
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.hero-toolbar {
  display: grid;
  gap: 0.75rem;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.6rem;
}

.stat-card {
  border-radius: 14px;
  padding: 0.65rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.62);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  display: grid;
  gap: 0.18rem;
}

.stat-card small {
  color: var(--text-muted);
  font-size: 0.73rem;
}

.stat-card strong {
  font-size: 1rem;
}

.stat-card--success {
  background: rgb(var(--palette-june-bud-rgb) / 0.16);
}

.stat-card--warning {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.12);
}

.stat-card--danger {
  background: rgb(184 79 79 / 0.12);
}

.hero-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.hero-search {
  flex: 1;
}

.inline-input {
  min-width: 110px;
}

.row-actions {
  display: inline-flex;
  gap: 0.35rem;
}

.check-inline {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
}

.success {
  margin: 0;
  color: var(--accent-green);
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 1180px) {
  .hero-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
