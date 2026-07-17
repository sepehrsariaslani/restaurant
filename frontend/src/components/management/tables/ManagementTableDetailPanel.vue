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
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(157, 145, 103, 0.1);
  margin-bottom: 1rem;
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
  border-radius: 16px 16px 0 0;
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

.head-location {
  font-size: 0.8rem;
  color: var(--cw-caramel);
  margin-top: 0.15rem;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.inspection-section {
  background: var(--cw-surface);
  border: 1px solid var(--cw-border);
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(68, 45, 28, 0.02);
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(132, 89, 43, 0.1);
}

.section-title {
  margin: 0;
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

.checkbox-group {
  margin-top: 0.5rem;
}

.check-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.data-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--cw-cocoa);
}

.data-icon {
  color: var(--cw-caramel);
  opacity: 0.8;
  display: flex;
}

.data-highlight {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(132, 89, 43, 0.05);
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid rgba(132, 89, 43, 0.1);
}

.highlight-label {
  font-size: 0.8rem;
  color: var(--cw-olive);
  font-weight: 600;
}

.highlight-value {
  font-size: 1.1rem;
  color: var(--cw-wine);
  font-weight: 800;
}

.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }

.icon-text-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--cw-caramel);
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0;
}

.icon-text-btn:hover {
  color: var(--cw-wine);
}

.inspection-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--cw-border);
  background: var(--cw-surface);
  border-radius: 0 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-actions-row {
  display: flex;
  gap: 0.75rem;
}

.flex-1 {
  flex: 1;
  display: flex;
  justify-content: center;
}

.danger-btn {
  background: rgba(116, 48, 20, 0.05);
  color: var(--cw-wine);
  border: 1px solid rgba(116, 48, 20, 0.2);
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
}

.danger-btn:hover {
  background: rgba(116, 48, 20, 0.1);
  border-color: rgba(116, 48, 20, 0.3);
}
</style>
