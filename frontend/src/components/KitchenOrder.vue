<template>
  <div :class="['ko-card', `ko-${type}`, { 'ko-urgent': elapsed >= 12 && type !== 'ready' }]">
    <div class="ko-head">
      <div class="ko-code">
        <span class="ko-ch">{{ order.channel || 'حضوری' }}</span>
        <strong>{{ order.order_code || order.name }}</strong>
      </div>
      <div class="ko-time">{{ elapsed }}'</div>
    </div>
    <div class="ko-customer" v-if="order.customer_name">👤 {{ order.customer_name }}</div>
    <div class="ko-items">
      <div v-for="(it, i) in (order.items||[]).slice(0, 12)" :key="i" class="ko-item">
        <span class="ko-qty">{{ it.qty }}×</span>
        <span class="ko-name">{{ it.title || it.item_name }}</span>
        <span v-if="it.note" class="ko-note">{{ it.note }}</span>
      </div>
      <div v-if="(order.items||[]).length > 12" class="ko-more">+{{ (order.items||[]).length-12 }} مورد</div>
    </div>
    <div class="ko-foot">
      <button v-if="type==='new'" class="ko-btn ko-btn-green" @click.stop="$emit('click')">✓ شروع</button>
      <button v-if="type==='prep'" class="ko-btn ko-btn-blue" @click.stop="$emit('click')">✓ آماده شد</button>
      <button v-if="type==='ready'" class="ko-btn ko-btn-done" @click.stop="$emit('click')">✓ تحویل</button>
    </div>
  </div>
</template>

<script>
export default {
  props: { order: Object, type: String },
  emits: ['click'],
  computed: {
    elapsed() {
      const created = this.order?.created_at || this.order?.creation || ''
      if (!created) return 0
      return Math.floor((Date.now() - new Date(created).getTime()) / 60000)
    }
  }
}
</script>

<style scoped>
.ko-card{background:#1a1a1a;border-radius:10px;padding:0.65rem;border:1.5px solid #2a2a2a;animation:fadeIn 0.2s ease;transition:all 0.15s;cursor:pointer}
.ko-card:hover{transform:translateY(-1px)}
.ko-new{border-color:#fbbf2433}.ko-prep{border-color:#63b3ed33}.ko-ready{border-color:#4ade8033}
.ko-urgent{border-color:#f8717133 !important;background:#1f0a0a;animation:pulse 2s infinite}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.85}}
.ko-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.3rem}
.ko-code{display:flex;align-items:center;gap:0.35rem}
.ko-ch{font-size:0.58rem;background:rgba(255,255,255,0.06);padding:0.08rem 0.3rem;border-radius:4px;color:#7a6a5a}
.ko-code strong{font-size:0.82rem;color:#f0e6d9}
.ko-time{font-size:0.68rem;color:#6a5a4a;direction:ltr;font-weight:600}
.ko-urgent .ko-time{color:#fca5a5}
.ko-customer{font-size:0.7rem;color:#a48a72;margin-bottom:0.35rem}
.ko-items{display:flex;flex-direction:column;gap:0.2rem;margin-bottom:0.35rem}
.ko-item{display:flex;align-items:baseline;gap:0.25rem;font-size:0.78rem;color:#e0d6c9;flex-wrap:wrap}
.ko-qty{background:#2a1a0a;color:#e8964a;font-size:0.62rem;font-weight:700;padding:0.05rem 0.25rem;border-radius:3px;flex-shrink:0}
.ko-note{font-size:0.62rem;color:#fbbf24;font-style:italic}
.ko-more{font-size:0.65rem;color:#6a5a4a;text-align:center;padding-top:0.15rem}
.ko-foot{display:flex;gap:0.35rem;margin-top:0.15rem}
.ko-btn{flex:1;padding:0.45rem;border:none;border-radius:6px;font-size:0.7rem;font-weight:700;cursor:pointer;transition:0.15s;font-family:inherit}
.ko-btn:hover{filter:brightness(1.15)}
.ko-btn-green{background:#e8964a;color:#1a0a00}
.ko-btn-blue{background:#2563eb;color:#fff}
.ko-btn-done{background:#16a34a;color:#fff}
</style>
