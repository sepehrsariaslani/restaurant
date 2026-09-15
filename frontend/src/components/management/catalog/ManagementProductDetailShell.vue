<template>
  <section class="product-reference-shell product-reference-shell--detail">
    <div v-if="$slots.breadcrumb" class="product-reference-shell__breadcrumb">
      <slot name="breadcrumb" />
    </div>

    <header v-if="showHeader" class="product-reference-shell__header">
      <div>
        <span class="product-reference-shell__eyebrow">قالب مرجع جزئیات</span>
        <h2>{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="product-reference-shell__actions">
        <slot name="actions" />
      </div>
    </header>

    <div v-if="$slots.hero" class="product-reference-shell__hero">
      <slot name="hero" />
    </div>
    <div v-if="$slots.navigation" class="product-reference-shell__navigation">
      <slot name="navigation" />
    </div>

    <div v-if="$slots.status" class="product-reference-shell__status" aria-live="polite">
      <slot name="status" />
    </div>
    <div v-if="loading" class="product-reference-shell__feedback" role="status" aria-live="polite">
      {{ loadingLabel }}
    </div>
    <div v-else-if="error" class="product-reference-shell__feedback product-reference-shell__feedback--error" role="alert">
      <span>{{ error }}</span>
      <button type="button" class="secondary-btn" @click="$emit('retry')">{{ retryLabel }}</button>
    </div>

    <div class="product-reference-shell__body">
      <slot />
    </div>

    <slot name="overlays" />
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'جزئیات محصول',
  },
  subtitle: {
    type: String,
    default: '',
  },
  showHeader: {
    type: Boolean,
    default: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  loadingLabel: {
    type: String,
    default: 'در حال بارگذاری جزئیات...',
  },
  retryLabel: {
    type: String,
    default: 'تلاش دوباره',
  },
})

defineEmits(['retry'])
</script>

<style scoped>
.product-reference-shell {
  display: grid;
  gap: var(--ds-space-4, 1rem);
  min-width: 0;
}

.product-reference-shell__breadcrumb,
.product-reference-shell__hero,
.product-reference-shell__navigation,
.product-reference-shell__body,
.product-reference-shell__status {
  min-width: 0;
}

.product-reference-shell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ds-space-4, 1rem);
  padding: var(--ds-space-5, 1.25rem);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  background: var(--ds-color-surface);
  box-shadow: var(--ds-shadow-sm);
}

.product-reference-shell__header > div:first-child {
  display: grid;
  gap: var(--ds-space-1, .25rem);
}

.product-reference-shell__eyebrow {
  color: var(--ds-color-action-accent);
  font-size: .72rem;
  font-weight: 800;
}

.product-reference-shell h2 {
  margin: 0;
  color: var(--ds-color-text-primary);
  font-size: clamp(1.1rem, 2vw, 1.45rem);
}

.product-reference-shell__header p {
  margin: 0;
  color: var(--ds-color-text-secondary);
  line-height: 1.7;
}

.product-reference-shell__actions {
  display: flex;
  align-items: center;
  gap: var(--ds-space-2, .5rem);
}

.product-reference-shell__status {
  display: grid;
  gap: var(--ds-space-2, .5rem);
}

.product-reference-shell__feedback {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-3, .75rem);
  padding: .72rem .9rem;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  color: var(--ds-color-text-secondary);
  background: var(--ds-color-surface-muted);
}

.product-reference-shell__feedback--error {
  border-color: var(--ds-color-status-danger);
  color: var(--ds-color-status-danger);
  background: var(--ds-color-status-danger-soft);
}

@media (max-width: 760px) {
  .product-reference-shell__header {
    flex-direction: column;
  }

  .product-reference-shell__actions {
    width: 100%;
  }
}
</style>
