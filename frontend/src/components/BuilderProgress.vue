<template>
  <div class="builder-progress" role="navigation" aria-label="پیشرفت ساخت محصول">
    <div class="progress-dots">
      <template v-for="(step, idx) in steps" :key="idx">
        <div
          class="progress-dot"
          :class="{
            completed: idx < currentIndex,
            current: idx === currentIndex,
            future: idx > currentIndex,
          }"
        >
          <svg
            v-if="idx < currentIndex"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <div
          class="progress-line"
          :class="{ filled: idx < currentIndex }"
          v-if="idx < steps.length - 1"
        />
      </template>
    </div>
    <p class="progress-text">
      مرحله {{ currentIndex + 1 }} از {{ steps.length }}
    </p>
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
})
</script>

<style scoped>
.builder-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 0;
}

.progress-dots {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.progress-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted, #7a6e64);
  border: 1.5px solid rgb(var(--palette-deep-saffron-rgb) / 0.25);
  background: rgb(var(--palette-eggshell-rgb) / 0.5);
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.progress-dot.completed {
  background: var(--accent-gold, #c8963e);
  border-color: var(--accent-gold, #c8963e);
  color: #fff;
}

.progress-dot.current {
  width: 34px;
  height: 34px;
  background: var(--accent-gold, #c8963e);
  border-color: var(--accent-gold, #c8963e);
  color: #fff;
  box-shadow: 0 0 0 3px rgb(var(--palette-deep-saffron-rgb) / 0.2);
}

.progress-dot.future {
  opacity: 0.6;
}

.progress-line {
  width: 24px;
  height: 2px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.15);
  border-radius: 1px;
  flex-shrink: 0;
}

.progress-line.filled {
  background: var(--accent-gold, #c8963e);
}

.progress-text {
  font-size: 0.72rem;
  color: var(--text-muted, #7a6e64);
  margin: 0;
  font-weight: 500;
}

@media (min-width: 920px) {
  .progress-dot {
    width: 32px;
    height: 32px;
    font-size: 0.78rem;
  }
  .progress-dot.current {
    width: 38px;
    height: 38px;
  }
  .progress-line {
    width: 32px;
  }
}
</style>
