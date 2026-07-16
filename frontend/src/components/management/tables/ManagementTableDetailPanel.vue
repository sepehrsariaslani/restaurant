<template>
  <aside class="detail-panel">
    <div v-if="!detail?.table" class="detail-empty">
      <strong>یک میز را انتخاب کن</strong>
      <p>برای مشاهده جزئیات، مشتری، رزرو و عملیات همان میز روی یکی از کارت‌ها بزن.</p>
    </div>

    <template v-else>
      <header class="detail-head">
        <div class="detail-head__copy">
          <small>میز انتخاب‌شده</small>
          <strong>{{ tableDraft.table_number || detail.table.name }}</strong>
          <span>{{ tableDraft.location || 'بدون لوکیشن' }}</span>
        </div>
        <ManagementTableStatusBadge :status="tableDraft.status || detail.table.status" />
      </header>

      <section class="detail-card">
        <div class="detail-grid">
          <label>
            شماره میز
            <input class="input" :value="tableDraft.table_number" @input="emitField('table_number', $event.target.value)" />
          </label>
          <label>
            وضعیت
            <select class="input" :value="tableDraft.status" @change="emitField('status', $event.target.value)">
              <option value="empty">خالی</option>
              <option value="waiting">در انتظار</option>
              <option value="occupied">اشغال</option>
            </select>
          </label>
          <label>
            لوکیشن
            <input class="input" :value="tableDraft.location" @input="emitField('location', $event.target.value)" />
          </label>
          <label class="check-row">
            <input
              type="checkbox"
              :checked="Number(tableDraft.is_active || 0) === 1"
              @change="emitField('is_active', $event.target.checked ? 1 : 0)"
            />
            <span>فعال</span>
          </label>
        </div>

        <label class="full-width">
          یادداشت میز
          <textarea class="input" rows="3" :value="tableDraft.notes" @input="emitField('notes', $event.target.value)"></textarea>
        </label>
      </section>

      <section class="detail-card" v-if="detail.session">
        <div class="section-head">
          <strong>سشن فعال</strong>
          <ManagementTableStatusBadge :status="detail.session.status" />
        </div>
        <div class="detail-list">
          <div class="detail-list__row">
            <UserRound :size="15" />
            <span>{{ detail.session.customer_name || 'مشتری ثبت نشده' }}</span>
          </div>
          <div class="detail-list__row" v-if="detail.session.customer_mobile">
            <Smartphone :size="15" />
            <span>{{ detail.session.customer_mobile }}</span>
          </div>
          <div class="detail-list__row" v-if="detail.session.guest_count">
            <Users :size="15" />
            <span>{{ Number(detail.session.guest_count || 0).toLocaleString('fa-IR') }} نفر</span>
          </div>
          <div class="detail-list__row" v-if="detail.session.opened_at">
            <Clock3 :size="15" />
            <span>{{ formatDateTime(detail.session.opened_at) }}</span>
          </div>
          <div class="detail-list__row">
            <Receipt :size="15" />
            <span>{{ formatMoney(detail.session.total_confirmed_amount || 0, currency) }}</span>
          </div>
        </div>
      </section>

      <section class="detail-card" v-if="detail.reservation">
        <div class="section-head">
          <strong>رزرو مرتبط</strong>
          <ManagementTableStatusBadge :status="detail.reservation.status" />
        </div>
        <div class="detail-list">
          <div class="detail-list__row">
            <CalendarClock :size="15" />
            <span>
              {{ formatReservationDate(detail.reservation.reservation_date) }}
              <template v-if="detail.reservation.reservation_time"> - {{ detail.reservation.reservation_time }}</template>
            </span>
          </div>
          <div class="detail-list__row">
            <UserRound :size="15" />
            <span>{{ detail.reservation.customer_name || 'بدون نام' }}</span>
          </div>
          <div class="detail-list__row" v-if="detail.reservation.mobile">
            <Smartphone :size="15" />
            <span>{{ detail.reservation.mobile }}</span>
          </div>
          <div class="detail-list__row" v-if="detail.reservation.guest_count">
            <Users :size="15" />
            <span>{{ Number(detail.reservation.guest_count || 0).toLocaleString('fa-IR') }} نفر</span>
          </div>
        </div>
        <button class="secondary-btn inline-action" type="button" @click="$emit('open-reservations', detail.table)">
          <ArrowUpRight :size="14" />
          <span>باز کردن در تب رزروها</span>
        </button>
      </section>

      <footer class="detail-actions">
        <button class="primary-btn" type="button" :disabled="saving || !hasChanges" @click="$emit('save')">
          <Save :size="16" />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</span>
        </button>
        <button class="secondary-btn" type="button" @click="$emit('go-pos', detail.table)">
          <ArrowUpRight :size="16" />
          <span>رفتن به POS</span>
        </button>
        <button v-if="detail.session" class="ghost-btn danger-btn" type="button" @click="$emit('clear-session', detail.table)">
          <Trash2 :size="16" />
          <span>خالی کردن میز</span>
        </button>
      </footer>
    </template>
  </aside>
</template>

<script setup>
import {
  ArrowUpRight,
  CalendarClock,
  Clock3,
  Receipt,
  Save,
  Smartphone,
  Trash2,
  UserRound,
  Users,
} from 'lucide-vue-next'
import { formatMoney } from '@/utils/format'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

const props = defineProps({
  detail: {
    type: Object,
    default: null,
  },
  tableDraft: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'IRR',
  },
  saving: {
    type: Boolean,
    default: false,
  },
  hasChanges: {
    type: Boolean,
    default: false,
  },
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
.detail-panel {
  display: grid;
  gap: 0.85rem;
  align-content: start;
}

.detail-empty,
.detail-card {
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.05);
}

.detail-empty {
  padding: 1.25rem;
  display: grid;
  gap: 0.4rem;
  min-height: 240px;
  align-content: center;
  text-align: center;
}

.detail-empty p {
  margin: 0;
  color: var(--text-muted, #6b7280);
  line-height: 1.8;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
}

.detail-head__copy {
  display: grid;
  gap: 0.2rem;
}

.detail-head__copy small,
.detail-head__copy span {
  color: var(--text-muted, #6b7280);
}

.detail-card {
  padding: 1rem;
  display: grid;
  gap: 0.85rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.detail-grid label,
.full-width {
  display: grid;
  gap: 0.38rem;
  color: var(--text-muted, #6b7280);
  font-size: 0.8rem;
}

.check-row {
  display: flex !important;
  align-items: center;
  gap: 0.55rem;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.detail-list {
  display: grid;
  gap: 0.55rem;
}

.detail-list__row {
  display: inline-flex;
  align-items: center;
  gap: 0.48rem;
  color: var(--text-secondary, #374151);
  min-width: 0;
}

.detail-list__row span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.detail-actions > button,
.inline-action {
  min-height: 2.3rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.danger-btn {
  color: var(--danger, #b84f4f);
  border-color: rgb(184 79 79 / 0.22);
}

@media (max-width: 720px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-actions {
    display: grid;
  }
}
</style>
