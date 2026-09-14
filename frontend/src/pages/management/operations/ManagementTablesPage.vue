<template>
  <ManagementPageScaffold title="" subtitle="" :show-title="false">
    <div class="workspace-header">
      <div class="header-intro">
        <h1 class="page-title">مدیریت سالن و رزروها</h1>
        <p class="page-subtitle">کنترل یکپارچه میزها، نشست‌های فعال و زمان‌بندی مهمانان</p>
      </div>
      
      <div class="header-actions">
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model.trim="search"
            class="search-input"
            placeholder="جستجو (نام میز، موبایل، وضعیت...)"
            @keyup.enter="loadTables"
          />
        </div>
        <button class="primary-btn add-table-btn" type="button" @click="openCreateTable">
          + افزودن میز
        </button>
        <button class="refresh-btn" type="button" :disabled="loading" @click="loadTables" title="بروزرسانی اطلاعات">
          <RefreshCcw :size="18" :class="{ 'is-spinning': loading }" />
        </button>
      </div>
    </div>

    <!-- Composed KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi-hero">
        <div class="kpi-hero-val">{{ summary.totalTables.toLocaleString('fa-IR') }}</div>
        <div class="kpi-hero-label">مجموع میزها</div>
      </div>
      <div class="kpi-tiles">
        <div class="kpi-tile">
          <span class="kpi-dot empty"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ summary.emptyTables.toLocaleString('fa-IR') }}</span>
            <span class="kpi-label">خالی</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot waiting"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ summary.waitingTables.toLocaleString('fa-IR') }}</span>
            <span class="kpi-label">در انتظار</span>
          </div>
        </div>
        <div class="kpi-tile">
          <span class="kpi-dot occupied"></span>
          <div class="kpi-info">
            <span class="kpi-val">{{ summary.occupiedTables.toLocaleString('fa-IR') }}</span>
            <span class="kpi-label">اشغال</span>
          </div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-tile">
          <div class="kpi-info">
            <span class="kpi-val">{{ summary.activeSessions.toLocaleString('fa-IR') }}</span>
            <span class="kpi-label">سشن فعال</span>
          </div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-info">
            <span class="kpi-val">{{ summary.reservations.toLocaleString('fa-IR') }}</span>
            <span class="kpi-label">رزروها</span>
          </div>
        </div>
      </div>
    </div>

    <div class="workspace-tabs-container">
      <div class="workspace-tabs" role="tablist">
        <button
          v-for="tab in tabOptions"
          :key="tab.value"
          class="workspace-tab"
          :class="{ active: activeTab === tab.value }"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="activeTab = tab.value"
        >
          <component :is="tab.icon" :size="16" class="tab-icon" />
          <span>{{ tab.label }}</span>
          <span class="tab-badge" v-if="tab.badge">{{ tab.badge.toLocaleString('fa-IR') }}</span>
        </button>
      </div>
    </div>

    <p class="muted-loading" v-if="loading && !tables.length">در حال همگام‌سازی سالن...</p>
    <div class="workspace-alerts" v-if="error || successMessage">
      <p class="error-alert" v-if="error"><AlertCircle :size="16" /> {{ error }}</p>
      <p class="success-alert" v-if="successMessage"><CheckCircle2 :size="16" /> {{ successMessage }}</p>
    </div>

    <section v-if="creatingTable" class="create-table-card">
      <div>
        <h2>افزودن میز جدید</h2>
        <p>میز تازه را به سالن اضافه کنید؛ بعداً می‌توانید اطلاعات آن را ویرایش یا حذف کنید.</p>
      </div>
      <div class="create-table-form">
        <label>شماره / نام میز <input v-model.trim="newTable.table_number" class="input" placeholder="مثال: ۱۲ یا تراس ۱" /></label>
        <label>موقعیت <input v-model.trim="newTable.location" class="input" placeholder="سالن اصلی، تراس..." /></label>
        <label>یادداشت <input v-model.trim="newTable.notes" class="input" placeholder="اختیاری" /></label>
        <label class="check-label"><input v-model="newTable.is_active" type="checkbox" /> میز فعال باشد</label>
      </div>
      <div class="form-actions">
        <button class="primary-btn" type="button" :disabled="creatingTableSaving || !newTable.table_number" @click="createTable">
          {{ creatingTableSaving ? 'در حال ثبت...' : 'ثبت میز' }}
        </button>
        <button class="secondary-btn" type="button" :disabled="creatingTableSaving" @click="creatingTable = false">انصراف</button>
      </div>
    </section>

    <template v-if="!loading || tables.length">
      <section v-if="activeTab === 'floor'" class="workspace-floor">
        <div class="floor-grid-area">
          <div class="floor-filters" v-if="floorCards.length || search">
            <span class="floor-filter-label">فیلتر وضعیت:</span>
            <button class="floor-chip" :class="{ active: !statusFilter }" @click="statusFilter = ''">همه</button>
            <button class="floor-chip" :class="{ active: statusFilter === 'empty' }" @click="statusFilter = 'empty'">خالی</button>
            <button class="floor-chip" :class="{ active: statusFilter === 'occupied' }" @click="statusFilter = 'occupied'">اشغال / فعال</button>
            <button class="floor-chip" :class="{ active: statusFilter === 'waiting' }" @click="statusFilter = 'waiting'">در انتظار</button>
          </div>

          <div v-if="filteredFloorCards.length" class="floor-grid">
            <ManagementTableCard
              v-for="card in filteredFloorCards"
              :key="card.name"
              :card="card"
              :currency="currency"
              :selected="selectedTableName === card.name"
              @select="selectTable"
              @go-pos="goToPos"
            @clear-session="clearTableSession"
          />
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon-wrapper"><Armchair :size="32" /></div>
            <strong>میزی یافت نشد</strong>
            <p>در این نما با فیلترهای فعلی موردی وجود ندارد.</p>
            <button v-if="search || statusFilter" class="secondary-btn mt-2" @click="search = ''; statusFilter = ''">پاک کردن فیلترها</button>
          </div>
        </div>

        <aside class="floor-detail-area">
          <ManagementTableDetailPanel
            :detail="selectedTableDetail"
            :table-draft="tableDraft"
            :currency="currency"
            :saving="Boolean(savingMap[selectedTableName])"
            :has-changes="hasTableChanges"
            @update-field="updateTableDraftField"
            @save="saveTable()"
            @clear-session="clearTableSession"
            @go-pos="goToPos"
            @open-reservations="openReservationsForTable"
            @delete="deleteTable"
          />
        </aside>
      </section>

      <section v-else-if="activeTab === 'reservations'" class="workspace-reservations">
        <ManagementReservationsPanel
          :rows="filteredReservations"
          :tables="tables"
          :table-label-map="tableLabelMap"
          :selected-name="selectedReservationName"
          :reservation-draft="reservationDraft"
          :saving="Boolean(savingMap[selectedReservationName])"
          @select="selectReservation"
          @update-field="updateReservationDraftField"
          @save="saveReservation()"
          @jump-table="jumpToTable"
        />
      </section>

      <section v-else class="workspace-sessions">
        <ManagementSessionsPanel
          :rows="filteredSessions"
          :table-label-map="tableLabelMap"
          :selected-name="selectedSessionName"
          :session-draft="sessionDraft"
          :currency="currency"
          :saving="Boolean(savingMap[selectedSessionName])"
          @select="selectSession"
          @update-field="updateSessionDraftField"
          @save="saveSession()"
          @jump-table="jumpToTable"
        />
      </section>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Search, RefreshCcw, LayoutDashboard, CalendarDays, History, AlertCircle, CheckCircle2, Armchair } from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementReservationsPanel from '@/components/management/tables/ManagementReservationsPanel.vue'
import ManagementSessionsPanel from '@/components/management/tables/ManagementSessionsPanel.vue'
import ManagementTableCard from '@/components/management/tables/ManagementTableCard.vue'
import ManagementTableDetailPanel from '@/components/management/tables/ManagementTableDetailPanel.vue'
import {
  closeTableSession,
  createManagementTable,
  deleteManagementTable,
  getManagementTables,
  updateManagementTable,
  updateManagementTableReservation,
  updateManagementTableSession,
} from '@/utils/api'
import {
  buildFloorTableCards,
  buildSelectedTableDetail,
  buildTableLabelMap,
  buildTablesSummary,
  filterReservationsBySearch,
  filterSessionsBySearch,
  filterTablesBySearch,
  sortReservations,
} from '@/utils/managementTables'

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const search = ref('')
const statusFilter = ref('')
const currency = ref('IRR')
const activeTab = ref('floor')
const creatingTable = ref(false)
const creatingTableSaving = ref(false)
const newTable = reactive({ table_number: '', location: '', notes: '', is_active: true })

const tables = ref([])
const reservations = ref([])
const sessions = ref([])
const savingMap = reactive({})

const selectedTableName = ref('')
const selectedReservationName = ref('')
const selectedSessionName = ref('')

const tableDraft = reactive(createTableDraft())
const reservationDraft = reactive(createReservationDraft())
const sessionDraft = reactive(createSessionDraft())

const tableLabelMap = computed(() => buildTableLabelMap(tables.value))
const summary = computed(() => buildTablesSummary({ tables: tables.value, reservations: reservations.value, sessions: sessions.value }))
const filteredTableRows = computed(() => filterTablesBySearch(tables.value, sessions.value, reservations.value, search.value))
const floorCards = computed(() => buildFloorTableCards({ tables: filteredTableRows.value, sessions: sessions.value, reservations: reservations.value }))

const filteredFloorCards = computed(() => {
  if (!statusFilter.value) return floorCards.value
  return floorCards.value.filter(card => {
    if (statusFilter.value === 'empty') return card.status === 'empty'
    if (statusFilter.value === 'occupied') return card.status === 'occupied' || card.status === 'active'
    if (statusFilter.value === 'waiting') return card.status === 'waiting'
    return true
  })
})

const filteredReservations = computed(() => filterReservationsBySearch(reservations.value, tables.value, search.value))
const filteredSessions = computed(() => filterSessionsBySearch(sessions.value, tables.value, reservations.value, search.value))

const tabOptions = computed(() => [
  { value: 'floor', label: 'نمای سالن', icon: LayoutDashboard, badge: summary.value.totalTables },
  { value: 'reservations', label: 'رزروها', icon: CalendarDays, badge: filteredReservations.value.length },
  { value: 'sessions', label: 'سشن‌ها', icon: History, badge: filteredSessions.value.length },
])

const selectedTable = computed(() => tables.value.find((row) => row.name === selectedTableName.value) || null)
const selectedTableCard = computed(() =>
  buildFloorTableCards({
    tables: selectedTable.value ? [selectedTable.value] : [],
    sessions: sessions.value,
    reservations: reservations.value,
  })[0] || null,
)
const selectedTableDetail = computed(() =>
  buildSelectedTableDetail({
    table: selectedTable.value,
    session: selectedTableCard.value?.session || null,
    reservation: selectedTableCard.value?.reservation || null,
  }),
)

const selectedReservation = computed(() => reservations.value.find((row) => row.name === selectedReservationName.value) || null)
const selectedSession = computed(() => sessions.value.find((row) => row.name === selectedSessionName.value) || null)

const hasTableChanges = computed(() => {
  if (!selectedTable.value) return false
  return ['table_number', 'status', 'location', 'notes', 'is_active', 'active_session'].some((key) => String(tableDraft[key] ?? '') !== String(selectedTable.value[key] ?? ''))
})

watch(selectedTable, (row) => {
  Object.assign(tableDraft, createTableDraft(), row || {})
}, { immediate: true })

watch(selectedReservation, (row) => {
  Object.assign(reservationDraft, createReservationDraft(), row || {})
}, { immediate: true })

watch(selectedSession, (row) => {
  Object.assign(sessionDraft, createSessionDraft(), row || {})
}, { immediate: true })

function createTableDraft() {
  return {
    name: '',
    table_number: '',
    status: 'empty',
    is_active: 1,
    location: '',
    active_session: '',
    notes: '',
  }
}

function createReservationDraft() {
  return {
    name: '',
    customer_name: '',
    mobile: '',
    branch: '',
    table: '',
    reservation_date: '',
    reservation_time: '',
    guest_count: 1,
    status: 'pending',
    note: '',
  }
}

function createSessionDraft() {
  return {
    name: '',
    table: '',
    status: 'active',
    opened_at: '',
    closed_at: '',
    total_confirmed_amount: 0,
    note: '',
    customer_name: '',
    customer_mobile: '',
    guest_count: 0,
  }
}

function ensureSelections() {
  if (tables.value.length && !tables.value.some((row) => row.name === selectedTableName.value)) {
    selectedTableName.value = tables.value[0].name
  }
  const sortedReservations = sortReservations(reservations.value)
  if (sortedReservations.length && !reservations.value.some((row) => row.name === selectedReservationName.value)) {
    selectedReservationName.value = sortedReservations[0].name
  }
  if (sessions.value.length && !sessions.value.some((row) => row.name === selectedSessionName.value)) {
    selectedSessionName.value = sessions.value[0].name
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
    ensureSelections()
  } catch (loadError) {
    error.value = loadError.message || 'بارگذاری اطلاعات سالن ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function withSaveState(key, action, successText = 'تغییرات با موفقیت ذخیره شد.') {
  if (!key) return
  savingMap[key] = true
  error.value = ''
  successMessage.value = ''
  try {
    await action()
    successMessage.value = successText
    await loadTables()
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره اطلاعات ناموفق بود.'
  } finally {
    savingMap[key] = false
  }
}

function updateTableDraftField({ key, value }) {
  tableDraft[key] = value
}

function updateReservationDraftField({ key, value }) {
  reservationDraft[key] = value
}

function updateSessionDraftField({ key, value }) {
  sessionDraft[key] = value
}

function selectTable(table) {
  selectedTableName.value = table?.name || ''
}

function selectReservation(name) {
  selectedReservationName.value = name || ''
}

function selectSession(name) {
  selectedSessionName.value = name || ''
}

function openCreateTable() {
  Object.assign(newTable, { table_number: '', location: '', notes: '', is_active: true })
  creatingTable.value = true
  activeTab.value = 'floor'
}

async function createTable() {
  if (!newTable.table_number || creatingTableSaving.value) return
  creatingTableSaving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const result = await createManagementTable({ ...newTable, is_active: newTable.is_active ? 1 : 0 })
    creatingTable.value = false
    successMessage.value = `میز «${result?.table?.table_number || newTable.table_number}» با موفقیت اضافه شد.`
    await loadTables()
    selectedTableName.value = result?.table?.name || selectedTableName.value
  } catch (createError) {
    error.value = createError.message || 'افزودن میز ناموفق بود.'
  } finally {
    creatingTableSaving.value = false
  }
}

async function deleteTable(table) {
  const target = table?.name ? table : selectedTable.value
  if (!target?.name) return
  if (!window.confirm(`میز «${target.table_number || target.name}» حذف شود؟`)) return
  await withSaveState(target.name, () => deleteManagementTable(target.name), 'میز با موفقیت حذف شد.')
  selectedTableName.value = ''
}

async function saveTable(row = tableDraft) {
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

async function saveReservation(row = reservationDraft) {
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

async function saveSession(row = sessionDraft) {
  await withSaveState(row.name, () =>
    updateManagementTableSession({
      name: row.name,
      status: row.status,
      note: row.note,
    }),
  )
}

function resolveActiveSession(table) {
  if (!table) return null
  const explicitSession = sessions.value.find((row) => row.name === table.active_session)
  if (explicitSession) return explicitSession
  return sessions.value.find((row) => row.table === table.name && row.status === 'active') || null
}

async function clearTableSession(table) {
  const targetTable = table?.name ? table : selectedTable.value
  const session = resolveActiveSession(targetTable)
  if (!session?.name) {
    error.value = 'برای این میز سشن فعالی پیدا نشد.'
    return
  }
  if (!window.confirm(`سشن فعال ${targetTable.table_number || targetTable.name} بسته شود؟`)) return
  await withSaveState(session.name, () => closeTableSession(session.name), 'سشن با موفقیت بسته و میز خالی شد.')
}

function goToPos(table) {
  const target = String(table?.name || table?.table_number || '').trim()
  const query = target ? `?table=${encodeURIComponent(target)}` : ''
  window.location.assign(`/management/pos${query}`)
}

function openReservationsForTable(table) {
  activeTab.value = 'reservations'
  const linked = reservations.value.find((row) => row.table === table?.name)
  selectedReservationName.value = linked?.name || ''
  if (!linked && table?.table_number) {
    search.value = table.table_number
  }
}

function jumpToTable(tableName) {
  activeTab.value = 'floor'
  selectedTableName.value = tableName || ''
}

loadTables()
</script>

<style scoped>
.workspace-intro {
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  color: var(--mg-text-muted);
  font-size: 1rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.add-table-btn {
  white-space: nowrap;
}

.create-table-card {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  background: var(--mg-bg-surface);
  box-shadow: var(--mg-shadow-sm);
}

.create-table-card h2 {
  margin: 0 0 0.35rem;
  color: var(--mg-text-main);
  font-size: 1.15rem;
}

.create-table-card p {
  margin: 0;
  color: var(--mg-text-muted);
}

.create-table-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
}

.create-table-form label {
  display: grid;
  gap: 0.4rem;
  color: var(--mg-text-muted);
  font-size: 0.82rem;
}

.create-table-form .check-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  align-self: end;
}

.delete-table-btn {
  margin: 0.75rem 1.5rem 1.25rem;
  justify-content: center;
}

@media (max-width: 700px) {
  .create-table-form {
    grid-template-columns: 1fr;
  }
  .header-actions {
    width: 100%;
  }
  .search-box {
    flex: 1;
    width: auto;
  }
  .add-table-btn {
    min-height: 3rem;
  }
}

.search-box {
  position: relative;
  width: 320px;
}

.search-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mg-secondary);
}

.search-input {
  width: 100%;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.85rem 1rem 0.85rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.95rem;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--mg-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--mg-danger-bg); /* Reusing a subtle bg tint */
}

.refresh-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  width: 3.2rem;
  height: 3.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:hover {
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
}

/* KPI Strip */
.kpi-strip {
  display: flex;
  gap: 1rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}

.kpi-hero {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.5rem 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-sm);
  min-width: 220px;
}

.kpi-hero-val {
  font-size: 3rem;
  font-weight: 900;
  color: var(--mg-text-main);
  line-height: 1;
}

.kpi-hero-label {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
  margin-top: 0.5rem;
  font-weight: 700;
}

.kpi-tiles {
  display: flex;
  gap: 1rem;
  flex: 1;
  flex-wrap: wrap;
}

.kpi-tile {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
  min-width: 140px;
  border: 1px solid var(--mg-border-light);
}

.kpi-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-top: 0.4rem;
  flex-shrink: 0;
}

.kpi-dot.empty { background: var(--mg-secondary); }
.kpi-dot.waiting { background: #dda77b; } /* Sand/amber */
.kpi-dot.occupied { background: var(--mg-primary); }

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-val {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-top: 0.25rem;
}

.kpi-divider {
  width: 1px;
  background: var(--mg-border-light);
  margin: 0.5rem 0.5rem;
}

/* Tabs Container */
.workspace-tabs-container {
  display: flex;
  margin-bottom: 2rem;
}

.workspace-tabs {
  display: inline-flex;
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 0.35rem;
  gap: 0.25rem;
  border: 1px solid var(--mg-border-light);
  overflow-x: auto;
  max-width: 100%;
}

.workspace-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  border-radius: var(--mg-radius-sm);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.workspace-tab:hover {
  color: var(--mg-text-main);
}

.workspace-tab.active {
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
  box-shadow: var(--mg-shadow-sm);
}

.tab-badge {
  background: var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.15rem 0.6rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 800;
}

.workspace-tab.active .tab-badge {
  background: var(--mg-danger-bg);
  color: var(--mg-primary);
}

/* Floor Grid Area */
.workspace-floor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 2.5rem;
  align-items: start;
}

.floor-filters {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.floor-filter-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-left: 0.5rem;
}

.floor-chip {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.4rem 1rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.floor-chip:hover {
  border-color: var(--mg-border);
}

.floor-chip.active {
  background: var(--mg-text-main);
  border-color: var(--mg-text-main);
  color: var(--mg-bg-surface);
}
:global(.dark) .floor-chip.active {
  background: var(--mg-text-main);
  color: var(--mg-bg-surface);
}

.floor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.floor-detail-area {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  background: var(--mg-bg-surface);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1.5rem;
  opacity: 0.6;
}
.empty-state strong {
  font-size: 1.2rem;
  color: var(--mg-text-main);
  margin-bottom: 0.5rem;
  font-weight: 800;
}
.empty-state p {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
}
.secondary-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
  padding: 0.6rem 1.2rem;
  border-radius: var(--mg-radius-sm);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.secondary-btn:hover {
  background: var(--mg-bg-surface);
}

.workspace-alerts {
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.error-alert, .success-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}
.error-alert {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  border: 1px solid rgba(155, 61, 53, 0.2);
}
.success-alert {
  background: rgba(110, 118, 74, 0.1);
  color: var(--mg-success);
  border: 1px solid rgba(110, 118, 74, 0.25);
}
.muted-loading {
  color: var(--mg-secondary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 2rem;
}
.mt-2 { margin-top: 1rem; }

@media (max-width: 1200px) {
  .workspace-floor {
    grid-template-columns: 1fr;
  }
  .floor-detail-area {
    position: static;
    height: auto;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box { width: 100%; }
  .header-actions {
    flex-wrap: wrap;
  }
  .refresh-btn { flex: 1; }
  .kpi-divider { display: none; }
  .kpi-tiles {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
  .kpi-hero {
    min-width: 100%;
    align-items: center;
  }
}
</style>
