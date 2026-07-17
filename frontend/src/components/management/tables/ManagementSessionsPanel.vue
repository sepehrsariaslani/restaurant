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

.master-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  padding-right: 0.25rem; /* for scrollbar spacing */
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

.font-bold {
  font-weight: 700;
  color: var(--cw-wine);
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

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.kpi-box {
  background: var(--cw-bg);
  border: 1px solid var(--cw-border);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.kpi-box.highlight {
  background: rgba(132, 89, 43, 0.05);
  border-color: rgba(132, 89, 43, 0.2);
}

.kpi-box.highlight .kpi-box-value {
  color: var(--cw-wine);
}

.kpi-box-label {
  font-size: 0.75rem;
  color: var(--cw-olive);
  font-weight: 600;
}

.kpi-box-value {
  font-size: 1.1rem;
  color: var(--cw-cocoa);
  font-weight: 800;
}

.opacity-50 { opacity: 0.5; }

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
