<template>
  <article class="ko-card" :class="[`status-${type}`, { 'is-urgent': isUrgent }]">
    <!-- Meta row -->
    <header class="ko-meta">
      <div class="ko-meta-left">
        <span class="ko-channel">{{ order.channel || 'حضوری' }}</span>
        <strong class="ko-code">{{ order.order_code || order.name }}</strong>
      </div>
      <div class="ko-time" :class="{ 'is-urgent': isUrgent }">
        <Clock :size="14" class="icon-sm" />
        <span>{{ elapsed }}<small>د</small></span>
      </div>
    </header>

    <!-- Identity row -->
    <div class="ko-identity" v-if="order.customer_name">
      <div class="ko-customer">
        <UserRound :size="14" class="icon-sm" />
        <span class="customer-name">{{ order.customer_name }}</span>
      </div>
      <div class="ko-item-count">
        <Layers :size="14" class="icon-sm" />
        <span>{{ toFaDigits(totalQty) }} مورد</span>
      </div>
    </div>
    <div class="ko-identity" v-else>
      <div class="ko-item-count">
        <Layers :size="14" class="icon-sm" />
        <span>{{ toFaDigits(totalQty) }} مورد</span>
      </div>
    </div>

    <!-- Items Preview -->
    <div class="ko-body">
      <div class="ko-items-list">
        <div v-for="(it, i) in (order.items || []).slice(0, previewCount)" :key="i" class="ko-item">
          <div class="ko-item-main">
            <span class="ko-qty">{{ toFaDigits(it.qty) }}</span>
            <span class="ko-title">{{ it.title || it.item_name }}</span>
          </div>
          <div v-if="it.note" class="ko-note">
            <CornerDownLeft :size="12" class="note-icon" />
            <span>{{ it.note }}</span>
          </div>
        </div>
        <div v-if="(order.items || []).length > previewCount" class="ko-more">
          + {{ toFaDigits((order.items || []).length - previewCount) }} آیتم دیگر
        </div>
      </div>
    </div>

    <footer class="ko-footer" v-if="type !== 'closed'">
      <button v-if="type === 'new'" class="ko-btn btn-new" @click.stop="$emit('action')">
        <Play :size="16" />
        <span>شروع تولید</span>
      </button>
      <button v-if="type === 'prep'" class="ko-btn btn-prep" @click.stop="$emit('action')">
        <Check :size="16" />
        <span>آماده شد</span>
      </button>
      <button v-if="type === 'ready'" class="ko-btn btn-ready" @click.stop="$emit('action')">
        <CheckCheck :size="16" />
        <span>تحویل مشتری</span>
      </button>
    </footer>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { Clock, UserRound, CornerDownLeft, Play, Check, CheckCheck, Layers } from 'lucide-vue-next'

const props = defineProps({
  order: { type: Object, required: true },
  type: { type: String, default: 'new' }
})

defineEmits(['action'])

const previewCount = 6

function toFaDigits(val) {
  return Number(val || 0).toLocaleString('fa-IR')
}

const totalQty = computed(() => {
  return (props.order.items || []).reduce((sum, it) => sum + (it.qty || 1), 0)
})

const elapsed = computed(() => {
  const created = props.order?.created_at || props.order?.creation || ''
  if (!created) return 0
  const safeDateStr = String(created).replace(' ', 'T')
  return Math.floor((Date.now() - new Date(safeDateStr).getTime()) / 60000)
})

const isUrgent = computed(() => elapsed.value >= 12 && props.type !== 'ready' && props.type !== 'closed')
</script>

<style scoped>
.ko-card {
  display: flex;
  flex-direction: column;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

/* Status variants */
.ko-card.status-new { border-top: 3px solid var(--mg-primary); }
.ko-card.status-prep { border-top: 3px solid var(--mg-danger); }
.ko-card.status-ready { border-top: 3px solid var(--mg-success); background: rgba(111, 123, 86, 0.03); }
.ko-card.status-closed { border-top: 3px solid var(--mg-border); opacity: 0.75; }

.ko-card:hover {
  border-color: var(--mg-border);
  box-shadow: var(--mg-shadow-sm);
}

.ko-card.is-urgent {
  border-color: rgba(166, 84, 63, 0.5);
  box-shadow: 0 0 0 1px rgba(166, 84, 63, 0.2);
  animation: urgent-pulse 2s infinite;
}

@keyframes urgent-pulse {
  0% { box-shadow: 0 0 0 0px rgba(166, 84, 63, 0.2); }
  50% { box-shadow: 0 0 0 4px rgba(166, 84, 63, 0); }
  100% { box-shadow: 0 0 0 0px rgba(166, 84, 63, 0); }
}

.ko-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem 0.5rem;
}

.ko-meta-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ko-channel {
  font-size: 0.65rem;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-muted);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 700;
}

.ko-code {
  font-size: 1.05rem;
  font-weight: 900;
  color: var(--mg-text-main);
  letter-spacing: -0.01em;
}

.ko-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-secondary);
  background: var(--mg-surface-alt);
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
  border: 1px solid var(--mg-border-light);
}

.ko-time.is-urgent {
  color: var(--mg-danger);
  background: var(--mg-danger-bg);
  border-color: rgba(166, 84, 63, 0.2);
}

.ko-time small {
  font-size: 0.65rem;
  font-weight: 600;
  margin-right: 0.1rem;
}

.ko-identity {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem 0.75rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.ko-customer {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--mg-text-main);
  font-weight: 700;
}

.customer-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 130px;
}

.ko-item-count {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--mg-secondary);
}

.ko-body {
  flex: 1;
  padding: 0.75rem 1rem;
}

.ko-items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ko-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ko-item-main {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.ko-qty {
  flex: 0 0 auto;
  min-width: 1.4rem;
  height: 1.4rem;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
}

.status-new .ko-qty {
  color: var(--mg-primary);
  background: rgba(201, 120, 82, 0.08);
  border-color: rgba(201, 120, 82, 0.2);
}

.ko-title {
  font-size: 0.9rem;
  color: var(--mg-text-main);
  font-weight: 700;
  line-height: 1.4;
  padding-top: 0.1rem;
}

.ko-note {
  display: flex;
  align-items: flex-start;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--mg-danger);
  padding-right: 1.9rem;
  font-weight: 600;
}

.note-icon {
  margin-top: 0.15rem;
  opacity: 0.8;
}

.ko-more {
  text-align: center;
  font-size: 0.8rem;
  color: var(--mg-secondary);
  font-weight: 700;
  padding-top: 0.4rem;
  border-top: 1px dashed var(--mg-border-light);
  margin-top: 0.2rem;
}

.ko-footer {
  padding: 0.75rem 1rem 1rem;
  margin-top: auto;
}

.ko-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  height: 2.8rem;
  border: none;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new {
  background: var(--mg-surface-alt);
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
