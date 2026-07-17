<template>
  <article class="floor-card" :class="[statusClass, { 'is-selected': selected, 'is-inactive': Number(card.is_active || 0) !== 1 }]">
    <button class="card-hitbox" type="button" @click="$emit('select', card)" :aria-label="`جزئیات ${card.table_number || card.name}`"></button>

    <header class="card-header">
      <div class="card-identity">
        <h3>{{ card.table_number || card.name }}</h3>
        <span class="card-location" v-if="card.location">{{ card.location }}</span>
      </div>
      <ManagementTableStatusBadge :status="card.statusTone || card.status" class="card-badge" />
    </header>

    <div class="card-metrics">
      <div class="metric-row" v-if="card.customerName">
        <UserRound :size="14" class="metric-icon" />
        <span class="metric-text font-medium">{{ card.customerName }}</span>
      </div>
      <div class="metric-row" v-if="card.guestCount">
        <Users :size="14" class="metric-icon" />
        <span class="metric-text">{{ Number(card.guestCount || 0).toLocaleString('fa-IR') }} نفر</span>
      </div>
      
      <!-- Session specific metrics -->
      <template v-if="card.session?.name">
        <div class="metric-row highlight-metric">
          <Receipt :size="14" class="metric-icon" />
          <span class="metric-text font-bold" dir="ltr">{{ formatMoney(card.sessionTotal, currency) }}</span>
        </div>
        <div class="metric-row time-metric">
          <Clock3 :size="14" class="metric-icon" />
          <span class="metric-text">{{ formatTimeOnly(card.openedAt) }}</span>
        </div>
      </template>

<script setup>
import { computed } from 'vue'
import {
  CalendarClock,
  CircleOff,
  Clock3,
  LayoutGrid,
  Settings2,
  Receipt,
  LogOut,
  UserRound,
  Users,
} from 'lucide-vue-next'
import { formatMoney } from '@/utils/format'
import ManagementTableStatusBadge from './ManagementTableStatusBadge.vue'

const props = defineProps({
  card: { type: Object, required: true },
  currency: { type: String, default: 'IRR' },
  selected: { type: Boolean, default: false },
})

defineEmits(['select', 'go-pos', 'clear-session'])

const statusClass = computed(() => `status-${String(props.card.statusTone || props.card.status || 'empty').toLowerCase()}`)

function formatTimeOnly(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(text))
  } catch (_) {
    return text.split(' ')[1] || text
  }
}
</script>

<style scoped>
.floor-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  padding: 1.15rem;
  border-radius: 14px;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.floor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(68, 45, 28, 0.06);
}

.floor-card.is-selected {
  border-color: var(--mg-primary);
  box-shadow: 0 0 0 2px rgba(132, 89, 43, 0.2), 0 12px 32px rgba(68, 45, 28, 0.08);
}

.floor-card.is-inactive {
  opacity: 0.6;
  filter: grayscale(0.4);
}

/* Status variants for subtle background tinting */
.status-empty { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(232, 209, 167, 0.05)); }
.status-waiting { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(157, 145, 103, 0.05)); }
.status-occupied, .status-active { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(132, 89, 43, 0.05)); border-color: rgba(132, 89, 43, 0.25); }

:global(.dark) .status-empty { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(232, 209, 167, 0.02)); }
:global(.dark) .status-waiting { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(157, 145, 103, 0.02)); }
:global(.dark) .status-occupied, :global(.dark) .status-active { background: linear-gradient(to bottom right, var(--mg-bg-surface), rgba(132, 89, 43, 0.05)); }


.card-hitbox {
  position: absolute;
  inset: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  z-index: 1;
}

.card-header,
.card-metrics,
.card-footer {
  position: relative;
  z-index: 2;
  pointer-events: none; /* Let clicks pass to hitbox unless on a button */
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.card-identity {
  display: flex;
  flex-direction: column;
}

.card-identity h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--mg-text-main);
  letter-spacing: -0.02em;
}

.card-location {
  font-size: 0.75rem;
  color: var(--mg-olive);
  margin-top: 0.1rem;
}

.card-badge {
  transform: scale(0.9);
  transform-origin: top left;
}

.card-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
}

.metric-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--mg-olive);
  font-size: 0.8rem;
}

.metric-icon {
  opacity: 0.7;
}

.metric-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.font-medium { font-weight: 600; color: var(--mg-text-main); }
.font-bold { font-weight: 800; color: var(--mg-danger); font-size: 0.9rem; }

.highlight-metric {
  margin-top: 0.2rem;
  padding-top: 0.4rem;
  border-top: 1px dashed rgba(157, 145, 103, 0.2);
}

.time-metric { color: var(--mg-primary); font-size: 0.75rem; }
.res-metric { color: var(--mg-primary); font-weight: 600; }
.inactive-metric { color: #b84f4f; }

.card-footer {
  display: flex;
  gap: 0.4rem;
  margin-top: 1.25rem;
  pointer-events: auto; /* Buttons need pointer events */
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  height: 2.25rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--mg-border);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
}

.action-btn:hover {
  background: rgba(132, 89, 43, 0.05);
  border-color: var(--mg-primary);
}

.pos-btn {
  flex: 1;
  background: var(--mg-primary);
  color: white;
  border-color: var(--mg-primary);
}
.pos-btn:hover {
  background: #744e26;
  color: white;
}
:global(.dark) .pos-btn {
  color: #1A130D;
}

.detail-btn, .clear-btn {
  width: 2.25rem;
  padding: 0;
  color: var(--mg-olive);
}

.detail-btn:hover { color: var(--mg-primary); }

.clear-btn {
  color: var(--mg-danger);
  border-color: rgba(116, 48, 20, 0.2);
  background: rgba(116, 48, 20, 0.02);
}

.clear-btn:hover {
  background: rgba(116, 48, 20, 0.08);
  border-color: rgba(116, 48, 20, 0.3);
}

@media (max-width: 480px) {
  .floor-card {
    min-height: 160px;
    padding: 1rem;
  }
}
</style>
