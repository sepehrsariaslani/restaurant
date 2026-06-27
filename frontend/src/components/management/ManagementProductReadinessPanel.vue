<template>
  <section class="readiness-panel" aria-label="چک‌لیست کیفیت نمایش محصول">
    <header>
      <div>
        <strong>چک‌لیست آماده‌سازی منو</strong>
        <small>قبل از انتشار محصول، این موارد را سریع بررسی کنید.</small>
      </div>
      <span :class="['readiness-score', score === checks.length ? 'complete' : '']">
        {{ score.toLocaleString('fa-IR') }} / {{ checks.length.toLocaleString('fa-IR') }}
      </span>
    </header>
    <div class="readiness-list">
      <article v-for="check in checks" :key="check.key" :class="['readiness-item', { ok: check.ok }]">
        <span class="readiness-dot" aria-hidden="true"></span>
        <div>
          <strong>{{ check.label }}</strong>
          <small>{{ check.detail }}</small>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  checks: {
    type: Array,
    default: () => [],
  },
  score: {
    type: Number,
    default: 0,
  },
})
</script>

<style scoped>
.readiness-panel {
  margin: 0.82rem 0;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  background: linear-gradient(145deg, var(--bg-card, #fff), var(--bg-subtle, #f8fafc));
  padding: 0.7rem;
  display: grid;
  gap: 0.58rem;
}

.readiness-panel header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.55rem;
}

.readiness-panel header > div {
  display: grid;
  gap: 0.15rem;
}

.readiness-panel strong {
  color: var(--text-primary, #0f172a);
  font-size: 0.82rem;
}

.readiness-panel small {
  color: var(--text-muted);
  font-size: 0.72rem;
  line-height: 1.55;
}

.readiness-score {
  border-radius: 999px;
  background: rgb(218 138 47 / 0.12);
  color: #8a4b12;
  padding: 0.28rem 0.52rem;
  font-size: 0.72rem;
  font-weight: 900;
  white-space: nowrap;
}

.readiness-score.complete {
  background: rgb(var(--success-rgb) / 0.12);
  color: var(--success);
}

.readiness-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.42rem;
}

.readiness-item {
  display: flex;
  align-items: flex-start;
  gap: 0.42rem;
  border: 1px dashed color-mix(in srgb, var(--border, #e2e8f0) 70%, var(--text-muted, #64748b));
  border-radius: 10px;
  background: var(--bg-card, #fff);
  padding: 0.52rem;
}

.readiness-dot {
  width: 0.72rem;
  height: 0.72rem;
  margin-top: 0.18rem;
  border-radius: 999px;
  background: rgb(218 138 47 / 0.72);
  box-shadow: 0 0 0 4px rgb(218 138 47 / 0.1);
  flex-shrink: 0;
}

.readiness-item.ok {
  border-style: solid;
  border-color: rgb(var(--success-rgb) / 0.24);
}

.readiness-item.ok .readiness-dot {
  background: var(--success);
  box-shadow: 0 0 0 4px rgb(var(--success-rgb) / 0.12);
}
</style>
