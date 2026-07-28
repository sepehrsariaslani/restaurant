<template>
  <span class="table-status-badge" :class="toneClass">
    <component :is="statusIcon" :size="12" class="status-icon" v-if="statusIcon" />
    <span>{{ label }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckCircle2,
  Clock,
  CircleDashed,
  Utensils,
  XCircle,
  Ban,
  CheckCheck
} from 'lucide-vue-next'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
})

const normalizedStatus = computed(() => String(props.status || '').trim().toLowerCase())

const toneClass = computed(() => `is-${normalizedStatus.value || 'default'}`)

const statusIcon = computed(() => {
  switch (normalizedStatus.value) {
    case 'empty':
      return CircleDashed
    case 'waiting':
    case 'pending':
      return Clock
    case 'occupied':
    case 'active':
      return Utensils
    case 'confirmed':
      return CheckCircle2
    case 'cancelled':
      return XCircle
    case 'completed':
    case 'closed':
      return CheckCheck
    default:
      return null
  }
})

const label = computed(() => {
  switch (normalizedStatus.value) {
    case 'empty':
      return 'خالی'
    case 'waiting':
      return 'در انتظار'
    case 'occupied':
      return 'اشغال'
    case 'active':
      return 'فعال'
    case 'closed':
      return 'بسته'
    case 'pending':
      return 'در انتظار'
    case 'confirmed':
      return 'تایید شده'
    case 'cancelled':
      return 'لغو شده'
    case 'completed':
      return 'تکمیل شده'
    default:
      return props.status || '-'
  }
})
</script>

<style scoped>
.table-status-badge {
  min-height: 1.85rem;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0 0.65rem;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  border: 1px solid transparent;
  white-space: nowrap;
  letter-spacing: -0.2px;
}

.status-icon {
  opacity: 0.85;
}

/* Earthy Theme Colors
   Cowhide Cocoa: #442d1c
   Spiced Wine: #743014
   Toasted Caramel: #84592b
   Olive Harvest: #9d9167
   Golden Batter: #e8d1a7
*/

.is-empty {
  background: rgba(232, 209, 167, 0.25);
  color: #84592b;
  border-color: rgba(232, 209, 167, 0.6);
}

.is-waiting,
.is-pending {
  background: rgba(157, 145, 103, 0.15);
  color: #6a6042;
  border-color: rgba(157, 145, 103, 0.4);
}

.is-occupied,
.is-active,
.is-confirmed {
  background: rgba(132, 89, 43, 0.12);
  color: #743014;
  border-color: rgba(132, 89, 43, 0.25);
}

.is-cancelled {
  background: rgba(116, 48, 20, 0.08);
  color: #743014;
  border-color: rgba(116, 48, 20, 0.2);
}

.is-completed,
.is-closed {
  background: rgba(68, 45, 28, 0.06);
  color: #442d1c;
  border-color: rgba(68, 45, 28, 0.12);
}

:global(.dark) .is-empty {
  background: rgba(232, 209, 167, 0.1);
  color: #e8d1a7;
  border-color: rgba(232, 209, 167, 0.2);
}

:global(.dark) .is-waiting,
:global(.dark) .is-pending {
  background: rgba(157, 145, 103, 0.1);
  color: #d1c8a1;
  border-color: rgba(157, 145, 103, 0.2);
}

:global(.dark) .is-occupied,
:global(.dark) .is-active,
:global(.dark) .is-confirmed {
  background: rgba(132, 89, 43, 0.15);
  color: #e5ab75;
  border-color: rgba(132, 89, 43, 0.3);
}

:global(.dark) .is-cancelled {
  background: rgba(116, 48, 20, 0.15);
  color: #e37e5e;
  border-color: rgba(116, 48, 20, 0.3);
}

:global(.dark) .is-completed,
:global(.dark) .is-closed {
  background: rgba(255, 255, 255, 0.05);
  color: #a0978e;
  border-color: rgba(255, 255, 255, 0.1);
}
</style>
