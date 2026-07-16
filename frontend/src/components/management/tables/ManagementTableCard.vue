<template>
  <article class="table-card" :class="{ 'is-selected': selected, 'is-inactive': Number(card.is_active || 0) !== 1 }">
    <button class="card-hitbox" type="button" @click="$emit('select', card)" :aria-label="`جزئیات ${card.table_number || card.name}`"></button>

    <header class="table-card__head">
      <div class="table-card__identity">
        <strong>{{ card.table_number || card.name }}</strong>
        <small>{{ card.location || 'بدون لوکیشن' }}</small>
      </div>
      <ManagementTableStatusBadge :status="card.statusTone || card.status" />
    </header>

    <div class="table-card__body">
      <div class="table-card__metric" v-if="card.customerName">
        <UserRound :size="14" />
        <span>{{ card.customerName }}</span>
      </div>
      <div class="table-card__metric" v-if="card.guestCount">
        <Users :size="14" />
        <span>{{ Number(card.guestCount || 0).toLocaleString('fa-IR') }} نفر</span>
      </div>
      <div class="table-card__metric" v-if="card.sessionTotal">
        <Receipt :size="14" />
        <span>{{ formatMoney(card.sessionTotal, currency) }}</span>
      </div>
      <div class="table-card__metric" v-if="card.openedAt">
        <Clock3 :size="14" />
        <span>{{ formatDateTime(card.openedAt) }}</span>
      </div>
      <div class="table-card__metric" v-if="card.reservation?.reservation_time">
        <CalendarClock :size="14" />
        <span>رزرو {{ card.reservation.reservation_time }}</span>
      </div>
      <div class="table-card__metric" v-if="Number(card.is_active || 0) !== 1">
        <CircleOff :size="14" />
        <span>غیرفعال</span>
      </div>
    </div>

    <footer class="table-card__foot">
      <button class="secondary-btn compact-btn" type="button" @click.stop="$emit('go-pos', card)">
        <ArrowUpRight :size="14" />
        <span>POS</span>
      </button>
      <button class="secondary-btn compact-btn" type="button" @click.stop="$emit('select', card)">
        <PanelRightOpen :size="14" />
        <span>جزئیات</span>
      </button>
      <button
        v-if="card.session?.name"
        class="ghost-btn compact-btn danger-btn"
        type="button"
        @click.stop="$emit('clear-session', card)"
      >
        <Trash2 :size="14" />
        <span>خالی کردن</span>
      </button>
    </footer>
  </article>
</template>

<script setup>
import {
  ArrowUpRight,
  CalendarClock,
  CircleOff,
  Clock3,
  PanelRightOpen,
  Receipt,
  Trash2,
  UserRound,
  Users,
} from 'lucide-vue-next'
import { formatMoney } from '@/utils/format'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

defineProps({
  card: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'IRR',
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['select', 'go-pos', 'clear-session'])

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
.table-card {
  position: relative;
  display: grid;
  gap: 0.9rem;
  min-height: 210px;
  padding: 1rem;
  border-radius: 10px;
  background: var(--surface-raised, rgb(255 255 255 / 0.92));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.05);
  overflow: hidden;
}

.table-card.is-selected {
  border-color: rgb(139 94 60 / 0.34);
  box-shadow: 0 18px 36px rgb(111 74 49 / 0.12);
}

.table-card.is-inactive {
  opacity: 0.76;
}

.card-hitbox {
  position: absolute;
  inset: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.table-card__head,
.table-card__foot,
.table-card__body {
  position: relative;
  z-index: 1;
}

.table-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.table-card__identity {
  display: grid;
  gap: 0.24rem;
}

.table-card__identity strong {
  font-size: 1.05rem;
  line-height: 1.2;
}

.table-card__identity small {
  color: var(--text-muted, #6b7280);
  font-size: 0.74rem;
}

.table-card__body {
  display: grid;
  gap: 0.5rem;
  align-content: start;
}

.table-card__metric {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  color: var(--text-secondary, #374151);
  font-size: 0.79rem;
  min-width: 0;
}

.table-card__metric span {
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-card__foot {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: auto;
}

.compact-btn {
  min-height: 2.1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding-inline: 0.72rem;
}

.danger-btn {
  color: var(--danger, #b84f4f);
  border-color: rgb(184 79 79 / 0.22);
}

@media (max-width: 640px) {
  .table-card {
    min-height: 190px;
  }

  .table-card__foot {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-card__foot > :last-child {
    grid-column: 1 / -1;
  }
}
</style>
