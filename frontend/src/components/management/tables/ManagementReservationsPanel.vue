<template>
  <section class="panel-shell">
    <div class="panel-toolbar">
      <div class="toolbar-filters">
        <select v-model="statusFilter" class="input compact-filter">
          <option value="">همه وضعیت‌ها</option>
          <option value="pending">در انتظار</option>
          <option value="confirmed">تایید شده</option>
          <option value="cancelled">لغو شده</option>
          <option value="completed">تکمیل شده</option>
        </select>
        <select v-model="linkFilter" class="input compact-filter">
          <option value="all">همه</option>
          <option value="linked">دارای میز</option>
          <option value="unlinked">بدون میز</option>
        </select>
      </div>
      <small class="toolbar-count">{{ filteredRows.length.toLocaleString('fa-IR') }} رزرو</small>
    </div>

    <div class="panel-layout">
      <div class="reservation-list">
        <button
          v-for="row in filteredRows"
          :key="row.name"
          class="reservation-row"
          :class="{ active: row.name === selectedName }"
          type="button"
          @click="$emit('select', row.name)"
        >
          <div class="reservation-row__head">
            <strong>{{ row.customer_name || 'بدون نام' }}</strong>
            <ManagementTableStatusBadge :status="row.status" />
          </div>
          <div class="reservation-row__meta">
            <span>{{ tableLabelMap[row.table] || row.table || 'بدون میز' }}</span>
            <span>{{ formatReservationDate(row.reservation_date) }}</span>
            <span v-if="row.reservation_time">{{ row.reservation_time }}</span>
            <span v-if="row.guest_count">{{ Number(row.guest_count || 0).toLocaleString('fa-IR') }} نفر</span>
          </div>
        </button>
      </div>

      <div class="reservation-editor">
        <div v-if="!reservationDraft?.name" class="editor-empty">
          <strong>یک رزرو را انتخاب کن</strong>
          <p>برای ویرایش رزرو یا رفتن به میز مرتبط، یکی از رزروهای سمت راست را باز کن.</p>
        </div>
        <template v-else>
          <div class="editor-head">
            <div>
              <small>رزرو انتخاب‌شده</small>
              <strong>{{ reservationDraft.customer_name || reservationDraft.name }}</strong>
            </div>
            <ManagementTableStatusBadge :status="reservationDraft.status" />
          </div>

          <div class="editor-grid">
            <label>
              نام مشتری
              <input class="input" :value="reservationDraft.customer_name" @input="emitField('customer_name', $event.target.value)" />
            </label>
            <label>
              موبایل
              <input class="input" :value="reservationDraft.mobile" @input="emitField('mobile', $event.target.value)" />
            </label>
            <label>
              شعبه
              <input class="input" :value="reservationDraft.branch" @input="emitField('branch', $event.target.value)" />
            </label>
            <label>
              میز
              <select class="input" :value="reservationDraft.table" @change="emitField('table', $event.target.value)">
                <option value="">بدون میز</option>
                <option v-for="table in tables" :key="table.name" :value="table.name">
                  {{ table.table_number || table.name }}
                </option>
              </select>
            </label>
            <label>
              تاریخ
              <input class="input" type="date" :value="reservationDraft.reservation_date" @input="emitField('reservation_date', $event.target.value)" />
            </label>
            <label>
              ساعت
              <input class="input" type="time" :value="reservationDraft.reservation_time" @input="emitField('reservation_time', $event.target.value)" />
            </label>
            <label>
              تعداد نفرات
              <input class="input" type="number" min="1" :value="reservationDraft.guest_count" @input="emitField('guest_count', Number($event.target.value || 1))" />
            </label>
            <label>
              وضعیت
              <select class="input" :value="reservationDraft.status" @change="emitField('status', $event.target.value)">
                <option value="pending">در انتظار</option>
                <option value="confirmed">تایید شده</option>
                <option value="cancelled">لغو شده</option>
                <option value="completed">تکمیل شده</option>
              </select>
            </label>
          </div>

          <label class="full-width">
            یادداشت
            <textarea class="input" rows="3" :value="reservationDraft.note" @input="emitField('note', $event.target.value)"></textarea>
          </label>

          <div class="editor-actions">
            <button class="primary-btn" type="button" :disabled="saving" @click="$emit('save')">
              {{ saving ? 'در حال ذخیره...' : 'ذخیره رزرو' }}
            </button>
            <button
              class="secondary-btn"
              type="button"
              :disabled="!reservationDraft.table"
              @click="$emit('jump-table', reservationDraft.table)"
            >
              رفتن به میز
            </button>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  tables: {
    type: Array,
    default: () => [],
  },
  tableLabelMap: {
    type: Object,
    default: () => ({}),
  },
  selectedName: {
    type: String,
    default: '',
  },
  reservationDraft: {
    type: Object,
    default: () => ({}),
  },
  saving: {
    type: Boolean,
    default: false,
  },
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
.panel-shell,
.panel-layout,
.reservation-list,
.reservation-editor,
.editor-grid {
  display: grid;
}

.panel-shell {
  gap: 0.9rem;
}

.panel-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
  justify-content: space-between;
}

.toolbar-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.compact-filter {
  min-width: 150px;
}

.toolbar-count {
  color: var(--text-muted, #6b7280);
}

.panel-layout {
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 0.85rem;
}

.reservation-list,
.reservation-editor {
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.05);
}

.reservation-list {
  gap: 0.6rem;
  padding: 0.8rem;
  align-content: start;
  max-height: 720px;
  overflow: auto;
}

.reservation-row {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  border-radius: 8px;
  background: transparent;
  text-align: right;
  padding: 0.8rem;
  display: grid;
  gap: 0.45rem;
  cursor: pointer;
}

.reservation-row.active {
  border-color: rgb(139 94 60 / 0.3);
  background: rgb(139 94 60 / 0.05);
}

.reservation-row__head,
.editor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
}

.reservation-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.55rem;
  color: var(--text-muted, #6b7280);
  font-size: 0.76rem;
}

.reservation-editor {
  padding: 1rem;
  gap: 0.85rem;
}

.editor-empty {
  min-height: 260px;
  display: grid;
  align-content: center;
  gap: 0.4rem;
  text-align: center;
}

.editor-empty p {
  margin: 0;
  color: var(--text-muted, #6b7280);
}

.editor-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.editor-grid label,
.full-width {
  display: grid;
  gap: 0.35rem;
  color: var(--text-muted, #6b7280);
  font-size: 0.8rem;
}

.editor-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

@media (max-width: 980px) {
  .panel-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .editor-actions {
    display: grid;
  }
}
</style>
