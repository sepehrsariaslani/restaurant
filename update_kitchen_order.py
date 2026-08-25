import re

template = """<template>
  <article class="ko-card" :class="[`status-${type}`, { 'is-urgent': isUrgent }]">
    <header class="ko-header">
      <div class="ko-identity">
        <span class="ko-channel">{{ order.channel || 'حضوری' }}</span>
        <strong class="ko-code">{{ order.order_code || order.name }}</strong>
      </div>
      <div class="ko-time-badge" :class="{ 'urgent-time': isUrgent }">
        <Clock :size="12" class="icon-sm" />
        <span>{{ elapsed }}<small>د</small></span>
      </div>
    </header>

    <div class="ko-customer" v-if="order.customer_name">
      <UserRound :size="12" class="icon-sm" />
      <span>{{ order.customer_name }}</span>
    </div>

    <div class="ko-body">
      <div class="ko-items-list">
        <div v-for="(it, i) in (order.items || []).slice(0, 8)" :key="i" class="ko-item">
          <div class="ko-item-main">
            <span class="ko-qty">{{ toFaDigits(it.qty) }}×</span>
            <span class="ko-title">{{ it.title || it.item_name }}</span>
          </div>
          <div v-if="it.note" class="ko-note">
            <CornerDownLeft :size="12" class="note-icon" />
            <span>{{ it.note }}</span>
          </div>
        </div>
        <div v-if="(order.items || []).length > 8" class="ko-more">
          + {{ toFaDigits((order.items || []).length - 8) }} مورد دیگر
        </div>
      </div>
    </div>

    <footer class="ko-footer">
      <button v-if="type === 'new'" class="ko-action-btn btn-new" @click.stop="$emit('action')">
        <Play :size="14" />
        <span>شروع تولید</span>
      </button>
      <button v-if="type === 'prep'" class="ko-action-btn btn-prep" @click.stop="$emit('action')">
        <Check :size="14" />
        <span>آماده شد</span>
      </button>
      <button v-if="type === 'ready'" class="ko-action-btn btn-ready" @click.stop="$emit('action')">
        <CheckCheck :size="14" />
        <span>تحویل مشتری</span>
      </button>
    </footer>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { Clock, UserRound, CornerDownLeft, Play, Check, CheckCheck } from 'lucide-vue-next'

const props = defineProps({
  order: { type: Object, required: true },
  type: { type: String, default: 'new' }
})

defineEmits(['action'])

function toFaDigits(val) {
  return Number(val || 0).toLocaleString('fa-IR')
}

const elapsed = computed(() => {
  const created = props.order?.created_at || props.order?.creation || ''
  if (!created) return 0
  return Math.floor((Date.now() - new Date(created).getTime()) / 60000)
})

const isUrgent = computed(() => elapsed.value >= 12 && props.type !== 'ready')
</script>

<style scoped>
.ko-card {
  display: flex;
  flex-direction: column;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 1rem;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.ko-card::before {
  content: '';
  position: absolute;
  top: 0; right: 0; left: 0;
  height: 3px;
  background: transparent;
}

.ko-card:hover {
  border-color: var(--mg-border);
  box-shadow: var(--mg-shadow-sm);
}

/* Status variants */
.status-new::before { background: var(--mg-primary); }
.status-prep::before { background: var(--mg-danger); }
.status-ready::before { background: var(--mg-success); }

.is-urgent {
  background: var(--mg-danger-bg);
  border-color: rgba(166, 84, 63, 0.4);
}
.is-urgent::before {
  background: var(--mg-danger);
  animation: pulse-border 1.5s infinite;
}

@keyframes pulse-border {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.ko-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.ko-identity {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.ko-channel {
  font-size: 0.65rem;
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-muted);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 700;
}

.ko-code {
  font-size: 1rem;
  font-weight: 800;
  color: var(--mg-text-main);
}

.ko-time-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--mg-text-muted);
  background: var(--mg-bg-page);
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
}
.ko-time-badge.urgent-time {
  color: var(--mg-danger);
  background: rgba(166, 84, 63, 0.15);
}
.ko-time-badge small {
  font-size: 0.65rem;
  font-weight: 600;
  margin-right: 0.1rem;
}

.ko-customer {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--mg-secondary);
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.ko-body {
  flex: 1;
  background: var(--mg-bg-page);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.ko-items-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.ko-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.ko-item-main {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: var(--mg-text-main);
  font-weight: 700;
}

.ko-qty {
  color: var(--mg-primary);
  background: rgba(201, 120, 82, 0.1);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.8rem;
  line-height: 1.2;
}

.ko-note {
  display: flex;
  align-items: flex-start;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--mg-danger);
  padding-right: 1.8rem;
  font-weight: 600;
}
.note-icon {
  margin-top: 0.15rem;
  opacity: 0.8;
}

.ko-more {
  text-align: center;
  font-size: 0.75rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  padding-top: 0.25rem;
  border-top: 1px dashed var(--mg-border-light);
}

.ko-footer {
  margin-top: auto;
}

.ko-action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  height: 2.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new {
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-primary);
  color: var(--mg-primary);
}
.btn-new:hover { background: var(--mg-primary); color: #fff; }

.btn-prep {
  background: var(--mg-danger);
  color: #fff;
}
.btn-prep:hover { background: var(--mg-primary-hover); }

.btn-ready {
  background: var(--mg-success);
  color: #fff;
}
.btn-ready:hover { background: #5a6344; }

.icon-sm { opacity: 0.8; }
</style>
"""

with open("frontend/src/components/KitchenOrder.vue", "w") as f:
    f.write(template)

print("KitchenOrder generated")
