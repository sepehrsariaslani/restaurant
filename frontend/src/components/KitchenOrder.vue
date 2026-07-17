<template>
  <article class="ko-card" :class="[`status-${type}`, { 'is-urgent': isUrgent }]">
    
    <div class="ko-header" :class="`ko-header-${type}`">
      <div class="ko-identity">
        <span class="ko-code">{{ order.order_code || order.name }}</span>
        <span class="ko-channel" v-if="order.channel">{{ order.channel }}</span>
      </div>
      <div class="ko-time" :class="{ 'is-urgent-time': isUrgent }">
        <Clock :size="14" class="icon-sm" />
        <span class="ko-time-val">{{ elapsed }}<small>د</small></span>
      </div>
    </div>

    <div class="ko-meta" v-if="order.customer_name">
      <div class="ko-customer">
        <UserRound :size="14" class="icon-sm" />
        <span class="customer-name">{{ order.customer_name }}</span>
      </div>
      <div class="ko-item-count">
        <span>{{ toFaDigits(totalQty) }} مورد</span>
      </div>
    </div>
    <div class="ko-meta ko-meta-empty" v-else>
      <div class="ko-item-count">
        <span>{{ toFaDigits(totalQty) }} مورد</span>
      </div>
    </div>

    <div class="ko-body">
      <div class="ko-items">
        <div v-if="(order.items || []).length === 0" class="ko-empty-items">
          بدون آیتم مشخص
        </div>
        <div v-for="(it, i) in (order.items || []).slice(0, 6)" :key="i" class="ko-item">
          <div class="ko-item-main">
            <span class="ko-qty" :class="`ko-qty-${type}`">{{ toFaDigits(it.qty) }}</span>
            <span class="ko-title">{{ it.title || it.item_name || 'آیتم نامشخص' }}</span>
          </div>
          <div v-if="it.note" class="ko-note">
            <CornerDownLeft :size="12" class="note-icon" />
            <span>{{ it.note }}</span>
          </div>
        </div>
        <div v-if="(order.items || []).length > 6" class="ko-more">
          + {{ toFaDigits((order.items || []).length - 6) }} آیتم دیگر
        </div>
      </div>
    </div>

    <footer class="ko-footer" v-if="type !== 'closed'">
      <button v-if="type === 'new'" class="ko-btn ko-btn-new" @click.stop="$emit('action')">
        <Play :size="16" />
        <span>شروع تولید</span>
      </button>
      <button v-if="type === 'prep'" class="ko-btn ko-btn-prep" @click.stop="$emit('action')">
        <Check :size="16" />
        <span>آماده شد</span>
      </button>
      <button v-if="type === 'ready'" class="ko-btn ko-btn-ready" @click.stop="$emit('action')">
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
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(52, 38, 31, 0.03);
}

.ko-card:hover {
  border-color: var(--mg-border);
  box-shadow: var(--mg-shadow-sm);
}

.ko-card.is-urgent {
  border-color: rgba(166, 84, 63, 0.4);
  box-shadow: 0 0 0 1px rgba(166, 84, 63, 0.1);
  animation: urgent-pulse 2s infinite;
}

@keyframes urgent-pulse {
  0% { box-shadow: 0 0 0 0px rgba(166, 84, 63, 0.2); }
  50% { box-shadow: 0 0 0 4px rgba(166, 84, 63, 0); }
  100% { box-shadow: 0 0 0 0px rgba(166, 84, 63, 0); }
}

.ko-card.status-ready {
  background: var(--mg-success-bg);
  border-color: rgba(111, 123, 86, 0.2);
}

.ko-card.status-closed {
  opacity: 0.75;
}

/* Header */
.ko-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid var(--mg-border-light);
}
.ko-header-new { background: rgba(201, 120, 82, 0.06); border-bottom-color: rgba(201, 120, 82, 0.15); }
.ko-header-prep { background: rgba(166, 84, 63, 0.06); border-bottom-color: rgba(166, 84, 63, 0.15); }
.ko-header-ready { background: rgba(111, 123, 86, 0.1); border-bottom-color: rgba(111, 123, 86, 0.2); }
.ko-header-closed { background: var(--mg-surface-alt); }

.ko-identity {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ko-code {
  font-size: 1.1rem;
  font-weight: 900;
  color: var(--mg-text-main);
  letter-spacing: -0.01em;
}
.ko-header-ready .ko-code { color: var(--mg-success); }

.ko-channel {
  font-size: 0.65rem;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-muted);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 800;
}

.ko-time {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  font-weight: 900;
  color: var(--mg-secondary);
}
.ko-time.is-urgent-time { color: var(--mg-danger); }

.ko-time small {
  font-size: 0.65rem;
  font-weight: 700;
  margin-right: 0.1rem;
}

/* Meta */
.ko-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0.85rem 0;
}
.ko-meta-empty {
  justify-content: flex-end;
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
  max-width: 180px;
}
.ko-item-count {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--mg-secondary);
  background: var(--mg-surface-alt);
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  border: 1px solid var(--mg-border-light);
}

/* Body */
.ko-body {
  padding: 0.75rem 0.85rem;
}

.ko-items {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.ko-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ko-item-main {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.ko-qty {
  flex: 0 0 auto;
  min-width: 1.6rem;
  height: 1.6rem;
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 900;
}
.ko-qty-new { color: var(--mg-primary); border-color: rgba(201, 120, 82, 0.3); background: rgba(201, 120, 82, 0.08); }
.ko-qty-prep { color: var(--mg-danger); border-color: rgba(166, 84, 63, 0.3); background: rgba(166, 84, 63, 0.08); }
.ko-qty-ready { color: var(--mg-success); border-color: rgba(111, 123, 86, 0.3); background: rgba(111, 123, 86, 0.08); }

.ko-title {
  font-size: 0.95rem;
  color: var(--mg-text-main);
  font-weight: 800;
  line-height: 1.4;
  padding-top: 0.1rem;
}

.ko-note {
  display: flex;
  align-items: flex-start;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--mg-danger);
  padding-right: 2.2rem;
  font-weight: 700;
}
.note-icon {
  margin-top: 0.15rem;
  opacity: 0.8;
}

.ko-more {
  text-align: center;
  font-size: 0.8rem;
  color: var(--mg-secondary);
  font-weight: 800;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--mg-border-light);
  margin-top: 0.2rem;
}

.ko-empty-items {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-style: italic;
  text-align: center;
  padding: 0.5rem;
}

/* Footer */
.ko-footer {
  padding: 0 0.85rem 0.85rem;
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

.ko-btn-new {
  background: var(--mg-bg-surface);
  border: 2px solid var(--mg-primary);
  color: var(--mg-primary);
}
.ko-btn-new:hover { background: var(--mg-primary); color: #fff; }

.ko-btn-prep {
  background: var(--mg-danger);
  color: #fff;
}
.ko-btn-prep:hover { background: var(--mg-primary-hover); }

.ko-btn-ready {
  background: var(--mg-success);
  color: #fff;
}
.ko-btn-ready:hover { background: #5a6344; }

.icon-sm { opacity: 0.8; }
</style>

