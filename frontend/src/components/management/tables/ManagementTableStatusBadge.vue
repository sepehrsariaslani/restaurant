<template>
  <span class="table-status-badge" :class="toneClass">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
})

const normalizedStatus = computed(() => String(props.status || '').trim().toLowerCase())

const toneClass = computed(() => `is-${normalizedStatus.value || 'default'}`)

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
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.72rem;
  font-size: 0.72rem;
  font-weight: 900;
  line-height: 1;
  border: 1px solid transparent;
  white-space: nowrap;
}

.is-empty {
  background: rgb(var(--palette-june-bud-rgb, 174 214 97) / 0.16);
  color: #557032;
  border-color: rgb(var(--palette-june-bud-rgb, 174 214 97) / 0.26);
}

.is-waiting,
.is-pending {
  background: rgb(var(--palette-deep-saffron-rgb, 244 180 0) / 0.14);
  color: #8a5a00;
  border-color: rgb(var(--palette-deep-saffron-rgb, 244 180 0) / 0.28);
}

.is-occupied,
.is-active,
.is-confirmed {
  background: rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.1);
  color: var(--brand-700, #6f4a31);
  border-color: rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.18);
}

.is-cancelled {
  background: rgb(184 79 79 / 0.12);
  color: #a33d3d;
  border-color: rgb(184 79 79 / 0.28);
}

.is-completed,
.is-closed {
  background: rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.06);
  color: var(--text-muted, #6b7280);
  border-color: rgb(var(--palette-deep-sapphire-rgb, 15 23 42) / 0.12);
}

@media (prefers-color-scheme: dark) {
  .is-empty {
    color: #cde7a5;
  }

  .is-waiting,
  .is-pending {
    color: #ffd37a;
  }

  .is-occupied,
  .is-active,
  .is-confirmed {
    color: #e7c2a5;
  }

  .is-cancelled {
    color: #ffb0b0;
  }

  .is-completed,
  .is-closed {
    color: #d0d7e2;
  }
}
</style>
