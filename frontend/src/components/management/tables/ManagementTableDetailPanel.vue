<template>
  <aside class="inspection-panel">
    <div v-if="!detail?.table" class="inspection-empty">
      <div class="empty-illustration"></div>
      <strong>میزی انتخاب نشده</strong>
      <p>برای مشاهده و ویرایش جزئیات، رزروها و نشست‌های فعال، یک میز را از سالن انتخاب کنید.</p>
    </div>

    <template v-else>
      <header class="inspection-head">
        <div class="head-info">
          <span class="head-kicker">جزئیات میز</span>
          <h2>{{ tableDraft.table_number || detail.table.name }}</h2>
          <span class="head-location">{{ tableDraft.location || 'بدون لوکیشن' }}</span>
        </div>
        <ManagementTableStatusBadge :status="tableDraft.status || detail.table.status" />
      </header>

      <div class="inspection-body">
        <!-- Table Form -->
        <section class="inspection-section">
          <h3 class="section-title">تنظیمات میز</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>شماره / نام میز</label>
              <input class="input" :value="tableDraft.table_number" @input="emitField('table_number', $event.target.value)" />
            </div>
            <div class="form-group">
              <label>وضعیت فعلی</label>
              <select class="input" :value="tableDraft.status" @change="emitField('status', $event.target.value)">
                <option value="empty">خالی</option>
                <option value="waiting">در انتظار</option>
                <option value="occupied">اشغال</option>
              </select>
            </div>
            <div class="form-group full-width">
              <label>موقعیت فیزیکی</label>
              <input class="input" :value="tableDraft.location" @input="emitField('location', $event.target.value)" placeholder="مثال: سالن اصلی، تراس، پنجره..." />
            </div>
            <div class="form-group full-width">
              <label>یادداشت میز</label>
              <textarea class="input" rows="2" :value="tableDraft.notes" @input="emitField('notes', $event.target.value)" placeholder="یادداشت‌های داخلی..."></textarea>
            </div>
            <div class="form-group full-width checkbox-group">
              <label class="check-label">
                <input
                  type="checkbox"
                  :checked="Number(tableDraft.is_active || 0) === 1"
                  @change="emitField('is_active', $event.target.checked ? 1 : 0)"
                />
                <span>میز فعال است و در سالن نمایش داده می‌شود</span>
              </label>
            </div>
          </div>
        </section>

        <!-- Active Session -->
        <section class="inspection-section" v-if="detail.session">
          <div class="section-header-row">
            <h3 class="section-title">نشست فعال</h3>
            <ManagementTableStatusBadge :status="detail.session.status" />
          </div>
          
          <div class="data-list">
            <div class="data-row">
              <span class="data-icon"><UserRound :size="16" /></span>
              <span class="data-value">{{ detail.session.customer_name || 'مشتری ثبت نشده' }}</span>
            </div>
            <div class="data-row" v-if="detail.session.customer_mobile">
              <span class="data-icon"><Smartphone :size="16" /></span>
              <span class="data-value" dir="ltr">{{ detail.session.customer_mobile }}</span>
            </div>
            <div class="data-row" v-if="detail.session.guest_count">
              <span class="data-icon"><Users :size="16" /></span>
              <span class="data-value">{{ Number(detail.session.guest_count || 0).toLocaleString('fa-IR') }} مهمان</span>
            </div>
            <div class="data-row" v-if="detail.session.opened_at">
              <span class="data-icon"><Clock3 :size="16" /></span>
              <span class="data-value">شروع: {{ formatDateTime(detail.session.opened_at) }}</span>
            </div>
            
            <div class="data-highlight mt-2">
              <span class="highlight-label">مبلغ کل سفارش‌ها:</span>
              <strong class="highlight-value">{{ formatMoney(detail.session.total_confirmed_amount || 0, currency) }}</strong>
            </div>
          </div>
        </section>

        <!-- Linked Reservation -->
        <section class="inspection-section" v-if="detail.reservation">
          <div class="section-header-row">
            <h3 class="section-title">رزرو مرتبط</h3>
            <ManagementTableStatusBadge :status="detail.reservation.status" />
          </div>
          
          <div class="data-list">
            <div class="data-row">
              <span class="data-icon"><CalendarClock :size="16" /></span>
              <span class="data-value">
                {{ formatReservationDate(detail.reservation.reservation_date) }}
                <template v-if="detail.reservation.reservation_time"> ساعت {{ detail.reservation.reservation_time }}</template>
              </span>
            </div>
            <div class="data-row">
              <span class="data-icon"><UserRound :size="16" /></span>
              <span class="data-value">{{ detail.reservation.customer_name || 'بدون نام' }}</span>
            </div>
            <div class="data-row" v-if="detail.reservation.mobile">
              <span class="data-icon"><Smartphone :size="16" /></span>
              <span class="data-value" dir="ltr">{{ detail.reservation.mobile }}</span>
            </div>
            <div class="data-row" v-if="detail.reservation.guest_count">
              <span class="data-icon"><Users :size="16" /></span>
              <span class="data-value">{{ Number(detail.reservation.guest_count || 0).toLocaleString('fa-IR') }} نفر</span>
            </div>
          </div>
          <button class="ghost-btn icon-text-btn mt-3" type="button" @click="$emit('open-reservations', detail.table)">
            <ArrowUpRight :size="14" />
            <span>مدیریت این رزرو</span>
          </button>
        </section>
      </div>

      <footer class="inspection-footer">
        <button class="primary-btn flex-1" type="button" :disabled="saving || !hasChanges" @click="$emit('save')">
          <Save :size="16" />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره میز' }}</span>
        </button>
        <div class="footer-actions-row">
          <button class="secondary-btn flex-1" type="button" @click="$emit('go-pos', detail.table)">
            <LayoutGrid :size="16" />
            <span>ثبت سفارش (POS)</span>
          </button>
          <button v-if="detail.session" class="danger-btn flex-1" type="button" @click="$emit('clear-session', detail.table)" title="بستن و خالی کردن میز">
            <LogOut :size="16" />
            <span>تخلیه</span>
          </button>
        </div>
      </footer>
    </template>
  </aside>
</template>

<script setup>
import {
  ArrowUpRight,
  CalendarClock,
  Clock3,
  LayoutGrid,
  LogOut,
  Save,
  Smartphone,
  UserRound,
  Users,
} from 'lucide-vue-next'
import { formatMoney } from '@/utils/format'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

const props = defineProps({
  detail: { type: Object, default: null },
  tableDraft: { type: Object, required: true },
  currency: { type: String, default: 'IRR' },
  saving: { type: Boolean, default: false },
  hasChanges: { type: Boolean, default: false },
})

const emit = defineEmits(['update-field', 'save', 'clear-session', 'go-pos', 'open-reservations'])

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

function formatReservationDate(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(new Date(text))
  } catch (_) {
    return text
  }
}
</script>

<style scoped>
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

.head-location {
  font-size: 0.95rem;
  color: var(--cw-text-muted);
  margin-top: 0.25rem;
  font-weight: 600;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.inspection-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--cw-border-light);
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--cw-text-main);
  font-weight: 800;
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
  box-shadow: 0 0 0 3px var(--cw-danger-bg); /* fallback tint */
  outline: none;
}

.input:disabled {
  opacity: 0.6;
  background: var(--cw-surface);
}

.checkbox-group {
  margin-top: 0.5rem;
}

.check-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--cw-text-main);
  font-weight: 600;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  background: var(--cw-page-bg);
  padding: 1.25rem;
  border-radius: var(--cw-radius-sm);
  border: 1px solid var(--cw-border-light);
}

.data-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  font-size: 0.95rem;
  color: var(--cw-text-main);
  font-weight: 600;
}

.data-icon {
  color: var(--cw-secondary);
  display: flex;
}

.data-highlight {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--cw-surface);
  padding: 1rem 1.25rem;
  border-radius: var(--cw-radius-sm);
  border: 1px dashed var(--cw-border);
}

.highlight-label {
  font-size: 0.9rem;
  color: var(--cw-text-muted);
  font-weight: 700;
}

.highlight-value {
  font-size: 1.4rem;
  color: var(--cw-primary);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.mt-2 { margin-top: 0.75rem; }
.mt-3 { margin-top: 1.25rem; }

.icon-text-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--cw-primary);
  font-size: 0.9rem;
  font-weight: 800;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.icon-text-btn:hover {
  color: var(--cw-primary-hover);
}

.inspection-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--cw-border-light);
  background: var(--cw-surface);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-actions-row {
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

.danger-btn {
  background: var(--cw-danger-bg);
  color: var(--cw-danger);
}
.danger-btn:hover {
  opacity: 0.8;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 720px) {
  .form-grid, .footer-actions-row {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
