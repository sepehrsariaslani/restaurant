<template>
  <ManagementPageScaffold title="مدیریت سالن و رزروها" subtitle="کنترل یکپارچه میزها، نشست‌های فعال و زمان‌بندی مهمانان">
    
    <div class="workspace-header">
      <div class="workspace-kpis">
        <div class="kpi-item">
          <span class="kpi-label">مجموع میزها</span>
          <strong class="kpi-value">{{ summary.totalTables.toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item kpi-empty">
          <span class="kpi-label">خالی</span>
          <strong class="kpi-value">{{ summary.emptyTables.toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="kpi-item kpi-waiting">
          <span class="kpi-label">در انتظار</span>
          <strong class="kpi-value">{{ summary.waitingTables.toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="kpi-item kpi-occupied">
          <span class="kpi-label">اشغال</span>
          <strong class="kpi-value">{{ summary.occupiedTables.toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <span class="kpi-label">سشن‌های فعال</span>
          <strong class="kpi-value">{{ summary.activeSessions.toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">رزروها</span>
          <strong class="kpi-value">{{ summary.reservations.toLocaleString('fa-IR') }}</strong>
        </div>
      </div>
      
      <div class="workspace-actions">
        <div class="search-wrapper">
          <Search :size="16" class="search-icon" />
          <input
            v-model.trim="search"
            class="input workspace-search"
            placeholder="جستجو (نام میز، موبایل، وضعیت...)"
            @keyup.enter="loadTables"
          />
        </div>
        <button class="icon-btn refresh-btn" type="button" :disabled="loading" @click="loadTables" title="بروزرسانی اطلاعات">
          <RefreshCcw :size="16" :class="{ 'is-spinning': loading }" />
        </button>
      </div>
    </div>

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

    <p class="muted-loading" v-if="loading && !tables.length">در حال همگام‌سازی سالن...</p>
    <div class="workspace-alerts" v-if="error || successMessage">
      <p class="error-alert" v-if="error"><AlertCircle :size="16" /> {{ error }}</p>
      <p class="success-alert" v-if="successMessage"><CheckCircle2 :size="16" /> {{ successMessage }}</p>
    </div>

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
/* Core Earthy Theme Variables for this workspace */
.workspace-header,
.workspace-tabs,
.workspace-floor,
.workspace-reservations,
.workspace-sessions {
  --cw-cocoa: #442D1C;
  --cw-wine: #743014;
  --cw-caramel: #84592B;
  --cw-olive: #9D9167;
  --cw-batter: #E8D1A7;
  --cw-surface: #FDFBF7;
  --cw-bg: #F4EFE6;
  --cw-border: rgba(132, 89, 43, 0.15);
}

:global(.dark) .workspace-header,
:global(.dark) .workspace-tabs,
:global(.dark) .workspace-floor,
:global(.dark) .workspace-reservations,
:global(.dark) .workspace-sessions {
  --cw-surface: #2B1D14;
  --cw-bg: #1A130D;
  --cw-border: rgba(232, 209, 167, 0.1);
  --cw-cocoa: #E8D1A7; /* Invert text to light accent */
}

/* Header Area */
.workspace-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 12px rgba(68, 45, 28, 0.03);
}

.workspace-kpis {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.kpi-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.kpi-label {
  font-size: 0.7rem;
  color: var(--cw-olive);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kpi-value {
  font-size: 1.15rem;
  color: var(--cw-cocoa);
  font-weight: 800;
  line-height: 1;
}

.kpi-empty .kpi-value { color: var(--cw-caramel); }
.kpi-waiting .kpi-value { color: var(--cw-olive); }
.kpi-occupied .kpi-value { color: var(--cw-wine); }

.kpi-divider {
  width: 1px;
  height: 24px;
  background: var(--cw-border);
}

.workspace-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-grow: 1;
  max-width: 400px;
}

.search-wrapper {
  position: relative;
  flex-grow: 1;
}

.search-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--cw-olive);
}

.workspace-search {
  width: 100%;
  padding-right: 2.25rem;
  background: var(--cw-bg);
  border: 1px solid var(--cw-border);
  border-radius: 8px;
  color: var(--cw-cocoa);
}

.workspace-search:focus {
  border-color: var(--cw-caramel);
  box-shadow: 0 0 0 3px rgba(132, 89, 43, 0.1);
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  border: 1px solid var(--cw-border);
  background: var(--cw-surface);
  color: var(--cw-caramel);
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover:not(:disabled) {
  background: rgba(132, 89, 43, 0.08);
  color: var(--cw-wine);
}

.is-spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Tabs */
.workspace-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid var(--cw-border);
  padding-bottom: 1px;
  overflow-x: auto;
}

.workspace-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--cw-olive);
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -3px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.workspace-tab:hover {
  color: var(--cw-caramel);
  background: rgba(132, 89, 43, 0.04);
  border-radius: 8px 8px 0 0;
}

.workspace-tab.active {
  color: var(--cw-wine);
  border-bottom-color: var(--cw-wine);
}

.tab-badge {
  background: rgba(157, 145, 103, 0.15);
  color: inherit;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 800;
}
.workspace-tab.active .tab-badge {
  background: rgba(116, 48, 20, 0.1);
}

/* Floor Workspace */
.workspace-floor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 1.5rem;
  align-items: start;
}

.floor-filters {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.floor-filter-label {
  font-size: 0.75rem;
  color: var(--cw-olive);
  font-weight: 600;
}

.floor-chip {
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  color: var(--cw-cocoa);
  padding: 0.35rem 0.8rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.floor-chip:hover {
  border-color: var(--cw-caramel);
}

.floor-chip.active {
  background: var(--cw-caramel);
  border-color: var(--cw-caramel);
  color: white;
}
:global(.dark) .floor-chip.active {
  color: #1A130D;
}

.floor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}

.floor-detail-area {
  position: sticky;
  top: 1.5rem;
  height: calc(100vh - 3rem);
  overflow-y: auto;
  border-radius: 16px;
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  box-shadow: 0 10px 30px rgba(68, 45, 28, 0.05);
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background: var(--cw-surface);
  border: 1px dashed var(--cw-border);
  border-radius: 12px;
  color: var(--cw-olive);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1rem;
  opacity: 0.5;
}
.empty-state strong {
  font-size: 1.1rem;
  color: var(--cw-cocoa);
  margin-bottom: 0.5rem;
}
.empty-state p {
  font-size: 0.85rem;
}

.workspace-alerts {
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.error-alert, .success-alert {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
}
.error-alert {
  background: rgba(116, 48, 20, 0.1);
  color: var(--cw-wine);
  border: 1px solid rgba(116, 48, 20, 0.2);
}
.success-alert {
  background: rgba(132, 89, 43, 0.1);
  color: var(--cw-caramel);
  border: 1px solid rgba(132, 89, 43, 0.2);
}
.muted-loading {
  color: var(--cw-olive);
  font-size: 0.85rem;
  font-weight: 600;
}
.mt-2 { margin-top: 1rem; }

@media (max-width: 1024px) {
  .workspace-floor {
    grid-template-columns: 1fr;
  }
  .floor-detail-area {
    position: static;
    height: auto;
    overflow-y: visible;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .workspace-actions {
    max-width: none;
  }
  .kpi-divider { display: none; }
  .workspace-kpis {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }
}
</style>
