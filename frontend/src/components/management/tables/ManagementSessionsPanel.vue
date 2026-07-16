<template>
  <section class="panel-shell">
    <div class="panel-toolbar">
      <small class="toolbar-count">{{ rows.length.toLocaleString('fa-IR') }} سشن</small>
    </div>

    <div class="panel-layout">
      <div class="session-list">
        <button
          v-for="row in rows"
          :key="row.name"
          class="session-row"
          :class="{ active: row.name === selectedName }"
          type="button"
          @click="$emit('select', row.name)"
        >
          <div class="session-row__head">
            <strong>{{ tableLabelMap[row.table] || row.table || '-' }}</strong>
            <ManagementTableStatusBadge :status="row.status" />
          </div>
          <div class="session-row__meta">
            <span>{{ formatDateTime(row.opened_at) }}</span>
            <span>{{ formatMoney(row.total_confirmed_amount || 0, currency) }}</span>
            <span v-if="row.customer_name">{{ row.customer_name }}</span>
          </div>
        </button>
      </div>

      <div class="session-editor">
        <div v-if="!sessionDraft?.name" class="editor-empty">
          <strong>یک سشن را انتخاب کن</strong>
          <p>برای بررسی وضعیت و ذخیره یادداشت یا رفتن به میز مرتبط، یکی از سشن‌ها را باز کن.</p>
        </div>
        <template v-else>
          <div class="editor-head">
            <div>
              <small>سشن انتخاب‌شده</small>
              <strong>{{ tableLabelMap[sessionDraft.table] || sessionDraft.table || sessionDraft.name }}</strong>
            </div>
            <ManagementTableStatusBadge :status="sessionDraft.status" />
          </div>

          <div class="detail-grid">
            <div class="info-card">
              <small>شروع</small>
              <strong>{{ formatDateTime(sessionDraft.opened_at) }}</strong>
            </div>
            <div class="info-card">
              <small>پایان</small>
              <strong>{{ formatDateTime(sessionDraft.closed_at) }}</strong>
            </div>
            <div class="info-card">
              <small>مبلغ تاییدشده</small>
              <strong>{{ formatMoney(sessionDraft.total_confirmed_amount || 0, currency) }}</strong>
            </div>
            <div class="info-card">
              <small>مشتری</small>
              <strong>{{ sessionDraft.customer_name || 'ثبت نشده' }}</strong>
            </div>
          </div>

          <div class="editor-grid">
            <label>
              وضعیت
              <select class="input" :value="sessionDraft.status" @change="emitField('status', $event.target.value)">
                <option value="active">فعال</option>
                <option value="closed">بسته</option>
              </select>
            </label>
            <label>
              موبایل مشتری
              <input class="input" :value="sessionDraft.customer_mobile || ''" readonly />
            </label>
            <label>
              تعداد نفرات
              <input class="input" :value="sessionDraft.guest_count || 0" readonly />
            </label>
          </div>

          <label class="full-width">
            یادداشت
            <textarea class="input" rows="4" :value="sessionDraft.note" @input="emitField('note', $event.target.value)"></textarea>
          </label>

          <div class="editor-actions">
            <button class="primary-btn" type="button" :disabled="saving" @click="$emit('save')">
              {{ saving ? 'در حال ذخیره...' : 'ذخیره سشن' }}
            </button>
            <button class="secondary-btn" type="button" :disabled="!sessionDraft.table" @click="$emit('jump-table', sessionDraft.table)">
              رفتن به میز
            </button>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'
import { formatMoney } from '@/utils/format'

defineProps({
  rows: {
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
  sessionDraft: {
    type: Object,
    default: () => ({}),
  },
  currency: {
    type: String,
    default: 'IRR',
  },
  saving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select', 'update-field', 'save', 'jump-table'])

function emitField(key, value) {
  emit('update-field', { key, value })
}

function formatDateTime(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(text))
  } catch (_) {
    return text
  }
}
</script>

<style scoped>
.panel-shell,
.panel-layout,
.session-list,
.session-editor,
.detail-grid,
.editor-grid {
  display: grid;
}

.panel-shell {
  gap: 0.9rem;
}

.panel-toolbar {
  display: flex;
  justify-content: flex-end;
}

.toolbar-count {
  color: var(--text-muted, #6b7280);
}

.panel-layout {
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 0.85rem;
}

.session-list,
.session-editor {
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.05);
}

.session-list {
  padding: 0.8rem;
  gap: 0.6rem;
  max-height: 720px;
  overflow: auto;
  align-content: start;
}

.session-row {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  border-radius: 8px;
  background: transparent;
  padding: 0.8rem;
  display: grid;
  gap: 0.4rem;
  text-align: right;
  cursor: pointer;
}

.session-row.active {
  border-color: rgb(139 94 60 / 0.3);
  background: rgb(139 94 60 / 0.05);
}

.session-row__head,
.editor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
}

.session-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.55rem;
  color: var(--text-muted, #6b7280);
  font-size: 0.76rem;
}

.session-editor {
  padding: 1rem;
  gap: 0.9rem;
}

.editor-empty {
  min-height: 240px;
  display: grid;
  align-content: center;
  text-align: center;
  gap: 0.45rem;
}

.editor-empty p {
  margin: 0;
  color: var(--text-muted, #6b7280);
}

.detail-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.info-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.08);
  border-radius: 8px;
  padding: 0.75rem;
  display: grid;
  gap: 0.24rem;
}

.info-card small {
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
  .detail-grid,
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .editor-actions {
    display: grid;
  }
}
</style>
