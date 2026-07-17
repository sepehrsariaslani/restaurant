<template>
  <section class="workspace-split-layout">
    <div class="list-area">
      <div class="list-header">
        <h3 class="list-title">لیست سشن‌ها</h3>
        <span class="list-count">{{ rows.length.toLocaleString('fa-IR') }} سشن</span>
      </div>

      <div class="master-list">
        <button
          v-for="row in rows"
          :key="row.name"
          class="list-item"
          :class="{ active: row.name === selectedName }"
          type="button"
          @click="$emit('select', row.name)"
        >
          <div class="list-item-head">
            <strong class="item-title">{{ tableLabelMap[row.table] || row.table || '-' }}</strong>
            <ManagementTableStatusBadge :status="row.status" />
          </div>
          <div class="list-item-body">
            <div class="item-meta">
              <Clock3 :size="14" class="meta-icon" />
              <span>{{ formatDateTime(row.opened_at) }}</span>
            </div>
            <div class="item-meta" v-if="row.total_confirmed_amount > 0">
              <Receipt :size="14" class="meta-icon" />
              <span class="font-bold">{{ formatMoney(row.total_confirmed_amount, currency) }}</span>
            </div>
            <div class="item-meta" v-if="row.customer_name">
              <UserRound :size="14" class="meta-icon" />
              <span>{{ row.customer_name }}</span>
            </div>
          </div>
        </button>
      </div>
    </div>

    <aside class="detail-area">
      <div class="inspection-panel">
        <div v-if="!sessionDraft?.name" class="inspection-empty">
          <div class="empty-illustration"><History :size="32" /></div>
          <strong>یک سشن را انتخاب کنید</strong>
          <p>برای بررسی وضعیت، مدیریت مشتری و یادداشت‌ها، یک سشن را از لیست باز کنید.</p>
        </div>
        
        <template v-else>
          <header class="inspection-head">
            <div class="head-info">
              <span class="head-kicker">جزئیات سشن</span>
              <h2>{{ tableLabelMap[sessionDraft.table] || sessionDraft.table || sessionDraft.name }}</h2>
            </div>
            <ManagementTableStatusBadge :status="sessionDraft.status" />
          </header>

          <div class="inspection-body">
            <div class="kpi-grid">
              <div class="kpi-box">
                <span class="kpi-box-label">شروع سشن</span>
                <strong class="kpi-box-value">{{ formatDateTime(sessionDraft.opened_at) }}</strong>
              </div>
              <div class="kpi-box" :class="{'opacity-50': !sessionDraft.closed_at}">
                <span class="kpi-box-label">پایان سشن</span>
                <strong class="kpi-box-value">{{ sessionDraft.closed_at ? formatDateTime(sessionDraft.closed_at) : 'در جریان' }}</strong>
              </div>
              <div class="kpi-box highlight">
                <span class="kpi-box-label">مبلغ تاییدشده</span>
                <strong class="kpi-box-value">{{ formatMoney(sessionDraft.total_confirmed_amount || 0, currency) }}</strong>
              </div>
              <div class="kpi-box">
                <span class="kpi-box-label">مشتری</span>
                <strong class="kpi-box-value">{{ sessionDraft.customer_name || 'ثبت نشده' }}</strong>
              </div>
            </div>

            <section class="inspection-section mt-4">
              <h3 class="section-title">ویرایش سشن</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>وضعیت فعلی</label>
                  <select class="input" :value="sessionDraft.status" @change="emitField('status', $event.target.value)">
                    <option value="active">فعال (در جریان)</option>
                    <option value="closed">بسته شده</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>تعداد نفرات</label>
                  <input class="input" :value="sessionDraft.guest_count || 0" readonly disabled title="از طریق رزرو یا POS تنظیم می‌شود" />
                </div>
                <div class="form-group full-width">
                  <label>شماره تماس مشتری</label>
                  <input class="input" :value="sessionDraft.customer_mobile || ''" readonly disabled dir="ltr" />
                </div>
                <div class="form-group full-width">
                  <label>یادداشت میز / سشن</label>
                  <textarea class="input" rows="3" :value="sessionDraft.note" @input="emitField('note', $event.target.value)" placeholder="هرگونه توضیحات خاص..."></textarea>
                </div>
              </div>
            </section>
          </div>

          <footer class="inspection-footer">
            <button class="primary-btn flex-1" type="button" :disabled="saving" @click="$emit('save')">
              <Save :size="16" />
              <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</span>
            </button>
            <button class="secondary-btn flex-1" type="button" :disabled="!sessionDraft.table" @click="$emit('jump-table', sessionDraft.table)">
              <LayoutGrid :size="16" />
              <span>پیدا کردن در سالن</span>
            </button>
          </footer>
        </template>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { Clock3, Receipt, UserRound, History, Save, LayoutGrid } from 'lucide-vue-next'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'
import { formatMoney } from '@/utils/format'

defineProps({
  rows: { type: Array, default: () => [] },
  tableLabelMap: { type: Object, default: () => ({}) },
  selectedName: { type: String, default: '' },
  sessionDraft: { type: Object, default: () => ({}) },
  currency: { type: String, default: 'IRR' },
  saving: { type: Boolean, default: false },
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
.workspace-split-layout {
  display: grid;
  grid-template-columns: 420px minmax(0, 1fr);
  gap: 2.5rem;
  align-items: start;
}

/* Master List Area */
.list-area {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-title {
  margin: 0;
  font-size: 1.4rem;
  color: var(--cw-text-main);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.list-count {
  font-size: 0.85rem;
  color: var(--cw-text-muted);
  font-weight: 700;
  background: var(--cw-surface-alt);
  padding: 0.35rem 0.85rem;
  border-radius: 99px;
  border: 1px solid var(--cw-border-light);
}

.list-filters {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  flex: 1;
  background: var(--cw-surface-alt);
  border: 1px solid var(--cw-border-light);
  color: var(--cw-text-main);
  border-radius: var(--cw-radius-sm);
  padding: 0.6rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 700;
  outline: none;
}
.filter-select:focus {
  border-color: var(--cw-primary);
}

.master-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding-right: 0.5rem;
}

.list-empty {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--cw-secondary);
  background: var(--cw-surface-alt);
  border-radius: var(--cw-radius-md);
  border: 1px dashed var(--cw-border);
  font-size: 0.95rem;
  font-weight: 600;
}

.list-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: var(--cw-surface-alt);
  border: 1px solid var(--cw-border-light);
  border-radius: var(--cw-radius-md);
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: right;
  width: 100%;
}

.list-item:hover {
  border-color: var(--cw-border);
  transform: translateX(-3px);
  box-shadow: var(--cw-shadow-sm);
}

.list-item.active {
  background: var(--cw-surface);
  border-color: var(--cw-primary);
  box-shadow: 4px 0 0 0 var(--cw-primary) inset, var(--cw-shadow-sm);
}

.list-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.item-title {
  font-size: 1.15rem;
  color: var(--cw-text-main);
  font-weight: 800;
}

.list-item-body {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--cw-text-muted);
  font-weight: 600;
}

.meta-icon {
  color: var(--cw-secondary);
}

.font-bold {
  font-weight: 800;
  color: var(--cw-primary);
  font-size: 0.95rem;
}

.table-meta {
  color: var(--cw-danger);
}
.table-meta.has-table {
  color: var(--cw-text-main);
}

/* Detail Area uses same inspection panel styles as detail panel */
.detail-area {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
}

.inspection-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--cw-surface-alt);
  border-radius: var(--cw-radius-md);
  border: 1px solid var(--cw-border-light);
  box-shadow: var(--cw-shadow);
  overflow: hidden;
}

.inspection-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--cw-secondary);
}

.empty-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--cw-surface);
  margin-bottom: 1.5rem;
  color: var(--cw-secondary);
  border: 1px solid var(--cw-border-light);
}

.inspection-empty strong {
  color: var(--cw-text-main);
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
}

.inspection-empty p {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--cw-text-muted);
}

.inspection-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.75rem 2rem;
  border-bottom: 1px solid var(--cw-border-light);
  background: var(--cw-surface);
}

.head-info {
  display: flex;
  flex-direction: column;
}

.head-kicker {
  font-size: 0.8rem;
  color: var(--cw-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 800;
  margin-bottom: 0.4rem;
}

.head-info h2 {
  margin: 0;
  font-size: 1.8rem;
  color: var(--cw-text-main);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.kpi-box {
  background: var(--cw-page-bg);
  border: 1px solid var(--cw-border-light);
  border-radius: var(--cw-radius-sm);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.kpi-box.highlight {
  background: var(--cw-surface);
  border-color: var(--cw-border);
}

.kpi-box.highlight .kpi-box-value {
  color: var(--cw-primary);
}

.kpi-box-label {
  font-size: 0.85rem;
  color: var(--cw-text-muted);
  font-weight: 700;
}

.kpi-box-value {
  font-size: 1.3rem;
  color: var(--cw-text-main);
  font-weight: 900;
}

.opacity-50 { opacity: 0.5; }

.inspection-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--cw-text-main);
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--cw-border-light);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 0.85rem;
  color: var(--cw-text-muted);
  font-weight: 700;
}

.input {
  background: var(--cw-page-bg);
  border: 1px solid var(--cw-border-light);
  color: var(--cw-text-main);
  border-radius: var(--cw-radius-sm);
  padding: 0.75rem 1rem;
  font-family: inherit;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--cw-primary);
  outline: none;
}

.input:disabled {
  opacity: 0.6;
  background: var(--cw-surface);
}

.mt-4 { margin-top: 2rem; }

.inspection-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--cw-border-light);
  background: var(--cw-surface);
  display: flex;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  height: 3.2rem;
  border-radius: var(--cw-radius-sm);
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.primary-btn {
  background: var(--cw-primary);
  color: #fff;
}
.primary-btn:hover:not(:disabled) {
  background: var(--cw-primary-hover);
}
:global(.dark) .primary-btn { color: #1A130D; }

.secondary-btn {
  background: var(--cw-surface-alt);
  border: 1px solid var(--cw-border);
  color: var(--cw-text-main);
}
.secondary-btn:hover:not(:disabled) {
  background: var(--cw-surface);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .workspace-split-layout {
    grid-template-columns: 1fr;
  }
  .detail-area {
    position: static;
    height: auto;
  }
  .master-list {
    max-height: 500px;
  }
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .inspection-footer {
    flex-direction: column;
  }
}
</style>
