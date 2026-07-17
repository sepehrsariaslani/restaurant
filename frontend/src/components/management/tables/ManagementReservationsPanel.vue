<template>
  <section class="workspace-split-layout">
    <div class="list-area">
      <div class="list-header">
        <h3 class="list-title">لیست رزروها</h3>
        <span class="list-count">{{ filteredRows.length.toLocaleString('fa-IR') }} رزرو</span>
      </div>

      <div class="list-filters">
        <select v-model="statusFilter" class="input filter-select">
          <option value="">همه وضعیت‌ها</option>
          <option value="pending">در انتظار</option>
          <option value="confirmed">تایید شده</option>
          <option value="completed">انجام شده</option>
          <option value="cancelled">لغو شده</option>
        </select>
        <select v-model="linkFilter" class="input filter-select">
          <option value="all">همه میزها</option>
          <option value="linked">دارای میز تخصیص‌یافته</option>
          <option value="unlinked">بدون میز</option>
        </select>
      </div>

      <div class="master-list">
        <button
          v-for="row in filteredRows"
          :key="row.name"
          class="list-item"
          :class="{ active: row.name === selectedName }"
          type="button"
          @click="$emit('select', row.name)"
        >
          <div class="list-item-head">
            <strong class="item-title">{{ row.customer_name || 'بدون نام' }}</strong>
            <ManagementTableStatusBadge :status="row.status" />
          </div>
          <div class="list-item-body">
            <div class="item-meta">
              <CalendarClock :size="14" class="meta-icon" />
              <span>{{ formatReservationDate(row.reservation_date) }}</span>
              <span v-if="row.reservation_time">{{ row.reservation_time }}</span>
            </div>
            <div class="item-meta" v-if="row.guest_count">
              <Users :size="14" class="meta-icon" />
              <span>{{ Number(row.guest_count || 0).toLocaleString('fa-IR') }} نفر</span>
            </div>
            <div class="item-meta table-meta" :class="{ 'has-table': row.table }">
              <Armchair :size="14" class="meta-icon" />
              <span>{{ tableLabelMap[row.table] || row.table || 'بدون میز' }}</span>
            </div>
          </div>
        </button>
        <div v-if="!filteredRows.length" class="list-empty">
          <p>رزروی با این مشخصات یافت نشد.</p>
        </div>
      </div>
    </div>

    <aside class="detail-area">
      <div class="inspection-panel">
        <div v-if="!reservationDraft?.name" class="inspection-empty">
          <div class="empty-illustration"><CalendarDays :size="32" /></div>
          <strong>یک رزرو را انتخاب کنید</strong>
          <p>برای ویرایش اطلاعات رزرو، تخصیص میز و مدیریت وضعیت، یک رزرو را از لیست باز کنید.</p>
        </div>
        
        <template v-else>
          <header class="inspection-head">
            <div class="head-info">
              <span class="head-kicker">جزئیات رزرو</span>
              <h2>{{ reservationDraft.customer_name || reservationDraft.name }}</h2>
            </div>
            <ManagementTableStatusBadge :status="reservationDraft.status" />
          </header>

          <div class="inspection-body">
            <section class="inspection-section">
              <h3 class="section-title">اطلاعات پایه</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>نام مشتری</label>
                  <input class="input" :value="reservationDraft.customer_name" @input="emitField('customer_name', $event.target.value)" />
                </div>
                <div class="form-group">
                  <label>موبایل مشتری</label>
                  <input class="input" dir="ltr" :value="reservationDraft.mobile" @input="emitField('mobile', $event.target.value)" />
                </div>
                <div class="form-group">
                  <label>تاریخ رزرو</label>
                  <input class="input" type="date" :value="reservationDraft.reservation_date" @input="emitField('reservation_date', $event.target.value)" />
                </div>
                <div class="form-group">
                  <label>ساعت رزرو</label>
                  <input class="input" type="time" :value="reservationDraft.reservation_time" @input="emitField('reservation_time', $event.target.value)" />
                </div>
                <div class="form-group">
                  <label>تعداد مهمانان</label>
                  <input class="input" type="number" min="1" :value="reservationDraft.guest_count" @input="emitField('guest_count', Number($event.target.value || 1))" />
                </div>
                <div class="form-group">
                  <label>شعبه (اختیاری)</label>
                  <input class="input" :value="reservationDraft.branch" @input="emitField('branch', $event.target.value)" />
                </div>
              </div>
            </section>

            <section class="inspection-section mt-4">
              <h3 class="section-title">مدیریت عملیات</h3>
              <div class="form-grid">
                <div class="form-group full-width">
                  <label>تخصیص میز در سالن</label>
                  <select class="input" :value="reservationDraft.table" @change="emitField('table', $event.target.value)">
                    <option value="">بدون میز (آزاد)</option>
                    <option v-for="table in tables" :key="table.name" :value="table.name">
                      {{ table.table_number || table.name }} {{ table.location ? `(${table.location})` : '' }}
                    </option>
                  </select>
                </div>
                <div class="form-group full-width">
                  <label>وضعیت رزرو</label>
                  <select class="input" :value="reservationDraft.status" @change="emitField('status', $event.target.value)">
                    <option value="pending">در انتظار بررسی</option>
                    <option value="confirmed">تایید شده</option>
                    <option value="completed">انجام شده (مهمان نشست)</option>
                    <option value="cancelled">لغو شده</option>
                  </select>
                </div>
                <div class="form-group full-width">
                  <label>یادداشت رزرو</label>
                  <textarea class="input" rows="3" :value="reservationDraft.note" @input="emitField('note', $event.target.value)" placeholder="درخواست‌های ویژه، مناسبت‌ها و..."></textarea>
                </div>
              </div>
            </section>
          </div>

          <footer class="inspection-footer">
            <button class="primary-btn flex-1" type="button" :disabled="saving" @click="$emit('save')">
              <Save :size="16" />
              <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره رزرو' }}</span>
            </button>
            <button
              class="secondary-btn flex-1"
              type="button"
              :disabled="!reservationDraft.table"
              @click="$emit('jump-table', reservationDraft.table)"
              title="پیدا کردن این میز در نمای سالن"
            >
              <LayoutGrid :size="16" />
              <span>مشاهده در سالن</span>
            </button>
          </footer>
        </template>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CalendarClock, Users, Armchair, CalendarDays, Save, LayoutGrid } from 'lucide-vue-next'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  tables: { type: Array, default: () => [] },
  tableLabelMap: { type: Object, default: () => ({}) },
  selectedName: { type: String, default: '' },
  reservationDraft: { type: Object, default: () => ({}) },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'update-field', 'save', 'jump-table'])

const statusFilter = ref('')
const linkFilter = ref('all')

const filteredRows = computed(() =>
  (props.rows || []).filter((row) => {
    if (statusFilter.value && row.status !== statusFilter.value) return false
    const isLinked = Boolean(String(row.table || '').trim())
    if (linkFilter.value === 'linked' && !isLinked) return false
    if (linkFilter.value === 'unlinked' && isLinked) return false
    return true
  }),
)

function emitField(key, value) {
  emit('update-field', { key, value })
}

function formatReservationDate(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: 'short',
      day: 'numeric',
    }).format(new Date(text))
  } catch (_) {
    return text
  }
}
</script>

<style scoped>
.workspace-split-layout {
  display: grid;
  grid-template-columns: minmax(320px, 380px) minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

/* Master List Area */
.list-area {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.25rem;
}

.list-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--cw-cocoa);
  font-weight: 800;
}

.list-count {
  font-size: 0.8rem;
  color: var(--cw-olive);
  font-weight: 600;
  background: var(--cw-surface);
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  border: 1px solid var(--cw-border);
}

.list-filters {
  display: flex;
  gap: 0.5rem;
  padding: 0 0.25rem;
}

.filter-select {
  flex: 1;
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  color: var(--cw-cocoa);
  border-radius: 8px;
  padding: 0.4rem 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.master-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.list-empty {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--cw-olive);
  background: var(--cw-surface);
  border-radius: 12px;
  border: 1px dashed var(--cw-border);
  font-size: 0.85rem;
}

.list-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: right;
  width: 100%;
}

.list-item:hover {
  border-color: var(--cw-caramel);
  transform: translateX(-2px);
}

.list-item.active {
  background: rgba(132, 89, 43, 0.05);
  border-color: var(--cw-caramel);
  box-shadow: 2px 0 0 0 var(--cw-caramel) inset;
}

.list-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.item-title {
  font-size: 1rem;
  color: var(--cw-cocoa);
  font-weight: 700;
}

.list-item-body {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--cw-olive);
}

.meta-icon {
  opacity: 0.7;
}

.table-meta {
  color: #b84f4f; /* unlinked state */
}
.table-meta.has-table {
  color: var(--cw-caramel);
  font-weight: 600;
}

/* Detail Area - Inspection Panel Styles */
.detail-area {
  position: sticky;
  top: 1.5rem;
  height: calc(100vh - 3rem);
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(68, 45, 28, 0.05);
  overflow: hidden;
}

.inspection-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.inspection-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: var(--cw-olive);
}

.empty-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(157, 145, 103, 0.1);
  margin-bottom: 1rem;
  color: var(--cw-olive);
}

.inspection-empty strong {
  color: var(--cw-cocoa);
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.inspection-empty p {
  font-size: 0.85rem;
  line-height: 1.6;
}

.inspection-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--cw-border);
  background: rgba(132, 89, 43, 0.02);
}

.head-info {
  display: flex;
  flex-direction: column;
}

.head-kicker {
  font-size: 0.7rem;
  color: var(--cw-olive);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.head-info h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--cw-cocoa);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.inspection-section {
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(68, 45, 28, 0.02);
}

.section-title {
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(132, 89, 43, 0.1);
  font-size: 0.9rem;
  color: var(--cw-cocoa);
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 0.75rem;
  color: var(--cw-olive);
  font-weight: 600;
}

.input {
  background: var(--cw-bg);
  border: 1px solid var(--cw-border);
  color: var(--cw-cocoa);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-family: inherit;
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--cw-caramel);
  box-shadow: 0 0 0 3px rgba(132, 89, 43, 0.1);
}

.input:disabled {
  opacity: 0.6;
  background: rgba(157, 145, 103, 0.05);
}

.mt-4 { margin-top: 1.5rem; }

.inspection-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--cw-border);
  background: var(--cw-surface);
  display: flex;
  gap: 0.75rem;
}

.flex-1 {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.4rem;
  height: 2.5rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

@media (max-width: 980px) {
  .workspace-split-layout {
    grid-template-columns: 1fr;
  }
  .detail-area {
    position: static;
    height: auto;
  }
  .master-list {
    max-height: 400px;
  }
}
</style>
