<template>
  <GlassCard class="sticky-wrap">
    <p class="muted">جمع فعلی</p>
    <h3>{{ formatMoney(subtotal, currency) }}</h3>
    <p class="muted" v-if="hint">{{ hint }}</p>
    <button class="primary-btn" :disabled="disabled" @click="$emit('action')">
      {{ buttonText }}
    </button>
  </GlassCard>
</template>

<script setup>
import GlassCard from './GlassCard.vue'
import { formatMoney } from '@/utils/format'

defineProps({
  subtotal: {
    type: Number,
    default: 0,
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
  buttonText: {
    type: String,
    default: 'ادامه',
  },
  hint: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['action'])
</script>

<style scoped>
.sticky-wrap {
  position: sticky;
  top: 5.8rem;
  display: grid;
  gap: 0.45rem;
}

.sticky-wrap p,
.sticky-wrap h3 {
  margin: 0;
}

.sticky-wrap h3 {
  font-size: 1.35rem;
}
</style>
