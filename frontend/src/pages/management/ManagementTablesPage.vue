<template>
  <ManagementPageScaffold title="مدیریت میزها" subtitle="کنترل زنده سالن، رزروها و نشست‌های فعال">
    <ManagementSurfaceCard tone="accent">
      <div class="hero-toolbar">
        <div class="hero-stats">
          <article class="stat-card">
            <small>کل میزها</small>
            <strong>{{ summary.totalTables.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--success">
            <small>میز خالی</small>
            <strong>{{ summary.emptyTables.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--warning">
            <small>در انتظار</small>
            <strong>{{ summary.waitingTables.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card stat-card--danger">
            <small>اشغال</small>
            <strong>{{ summary.occupiedTables.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card">
            <small>رزروها</small>
            <strong>{{ summary.reservations.toLocaleString('fa-IR') }}</strong>
          </article>
          <article class="stat-card">
            <small>سشن‌های فعال</small>
            <strong>{{ summary.activeSessions.toLocaleString('fa-IR') }}</strong>
          </article>
        </div>

        <div class="hero-actions">
          <input
            v-model.trim="search"
            class="input hero-search"
            placeholder="جستجو بر اساس میز، لوکیشن، مشتری، موبایل یا وضعیت"
            @keyup.enter="loadTables"
          />
          <button class="primary-btn" type="button" :disabled="loading" @click="loadTables">
            {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
          </button>
        </div>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft" class="section-picker-shell">
      <div class="section-picker">
        <div class="simple-tabs" role="tablist" aria-label="بخش‌های مدیریت میزها">
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
            <span class="tab-badge">{{ tab.badge.toLocaleString('fa-IR') }}</span>
          </button>
        </div>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری اطلاعات میزها...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <template v-if="!loading">
      <section v-if="activeTab === 'floor'" class="floor-layout">
        <div class="floor-main">
          <div class="floor-toolbar">
            <strong>نمای سالن</strong>
            <small>{{ floorCards.length.toLocaleString('fa-IR') }} میز در این نما دیده می‌شود</small>
          </div>

          <div v-if="floorCards.length" class="floor-grid">
            <ManagementTableCard
              v-for="card in floorCards"
              :key="card.name"
              :card="card"
              :currency="currency"
              :selected="selectedTableName === card.name"
              @select="selectTable"
              @go-pos="goToPos"
              @clear-session="clearTableSession"
            />
          </div>
          <div v-else class="empty-surface">
            <strong>میزی پیدا نشد</strong>
            <p>با جستجوی فعلی چیزی برای نمایش باقی نمانده است.</p>
          </div>
        </div>

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
      </section>

      <ManagementReservationsPanel
        v-else-if="activeTab === 'reservations'"
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

      <ManagementSessionsPanel
        v-else
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
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
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
const filteredReservations = computed(() => filterReservationsBySearch(reservations.value, tables.value, search.value))
const filteredSessions = computed(() => filterSessionsBySearch(sessions.value, tables.value, reservations.value, search.value))

const tabOptions = computed(() => [
  { value: 'floor', label: 'نمای سالن', badge: summary.value.totalTables },
  { value: 'reservations', label: 'رزروها', badge: filteredReservations.value.length },
  { value: 'sessions', label: 'سشن‌ها', badge: filteredSessions.value.length },
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
    error.value = loadError.message || 'بارگذاری میزها ناموفق بود.'
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
  await withSaveState(session.name, () => closeTableSession(session.name), 'میز با موفقیت خالی شد.')
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
.hero-toolbar,
.hero-stats,
.hero-actions,
.floor-layout,
.floor-main,
.floor-grid,
.section-picker,
.simple-tabs {
  display: grid;
}

.hero-toolbar {
  gap: 0.8rem;
}

.hero-stats {
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.6rem;
}

.stat-card {
  border-radius: 14px;
  padding: 0.72rem;
  background: rgb(var(--palette-eggshell-rgb, 248 244 237) / 0.7);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.14);
  display: grid;
  gap: 0.2rem;
}

.stat-card small {
  color: var(--text-muted, #6b7280);
  font-size: 0.73rem;
}

.stat-card strong {
  font-size: 1rem;
}

.stat-card--success {
  background: rgb(var(--palette-june-bud-rgb, 174 214 97) / 0.16);
}

.stat-card--warning {
  background: rgb(var(--palette-deep-saffron-rgb, 244 180 0) / 0.12);
}

.stat-card--danger {
  background: rgb(184 79 79 / 0.12);
}

.hero-actions {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.6rem;
  align-items: center;
}

.hero-search {
  min-width: 0;
}

.section-picker {
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
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
  color: var(--text-muted, #6b7280);
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

.simple-tab.active {
  background: var(--surface-raised, #fff);
  color: var(--brand-600, #8b5e3c);
  border-color: rgb(139 94 60 / 0.2);
  box-shadow: 0 8px 18px rgb(15 23 42 / 0.06);
}

.tab-badge {
  min-width: 1.32rem;
  min-height: 1.32rem;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  padding: 0 0.34rem;
  background: rgb(139 94 60 / 0.1);
  color: inherit;
  font-size: 0.72rem;
  font-weight: 800;
}

.floor-layout {
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 420px);
  gap: 0.95rem;
  align-items: start;
}

.floor-main {
  gap: 0.8rem;
}

.floor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
}

.floor-toolbar small {
  color: var(--text-muted, #6b7280);
}

.floor-grid {
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 0.85rem;
}

.empty-surface {
  min-height: 220px;
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.05);
  display: grid;
  align-content: center;
  justify-items: center;
  text-align: center;
  gap: 0.4rem;
  padding: 1rem;
}

.empty-surface p,
.success,
.error {
  margin: 0;
}

.empty-surface p {
  color: var(--text-muted, #6b7280);
}

.success {
  color: var(--accent-green, #4b7d3b);
}

.error {
  color: var(--danger, #b84f4f);
}

@media (max-width: 1180px) {
  .hero-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .floor-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-actions {
    grid-template-columns: 1fr;
  }

  .section-picker {
    align-items: stretch;
  }

  .simple-tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.2rem;
  }

  .simple-tab {
    flex: 0 0 auto;
    white-space: nowrap;
  }
}
</style>
