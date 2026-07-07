<template>
  <div v-if="rows.length" class="mobile-card-list">
    <article
      v-for="(row, index) in rows"
      :key="resolveRowKey(row, index)"
      :class="['mobile-card', cardClass]"
      :tabindex="cardClickable ? 0 : undefined"
      @click="handleCardClick($event, row)"
      @keydown.enter.prevent="handleCardKeydown(row)"
      @keydown.space.prevent="handleCardKeydown(row)"
    >
      <slot name="card" :row="row" :index="index" />
    </article>
  </div>
  <p v-else class="muted">{{ emptyText }}</p>
</template>

<script setup>
const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: [String, Function],
    default: '',
  },
  emptyText: {
    type: String,
    default: 'داده‌ای برای نمایش وجود ندارد.',
  },
  cardClass: {
    type: String,
    default: '',
  },
  cardClickable: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['card-click'])

function resolveRowKey(row, rowIndex) {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row, rowIndex)
  }
  if (typeof props.rowKey === 'string' && props.rowKey) {
    return row?.[props.rowKey] ?? rowIndex
  }
  return row?.name || row?.id || rowIndex
}

function handleCardClick(event, row) {
  if (!props.cardClickable) {
    return
  }
  const target = event?.target
  if (target?.closest?.('a, button, input, select, textarea, label, [role="button"], [data-no-card-click="1"]')) {
    return
  }
  emit('card-click', row)
}

function handleCardKeydown(row) {
  if (!props.cardClickable) {
    return
  }
  emit('card-click', row)
}
</script>

<style scoped>
.mobile-card-list {
  display: grid;
  gap: 0.6rem;
}

.mobile-card {
  border: 1px solid rgba(11, 68, 139, 0.12);
  border-radius: 0.95rem;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.65rem;
  display: grid;
  gap: 0.45rem;
}

.mobile-card[tabindex] {
  cursor: pointer;
}

.mobile-card[tabindex]:hover {
  border-color: rgba(11, 68, 139, 0.28);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.1);
}
</style>
