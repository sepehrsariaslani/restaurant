<template>
  <header class="preview-header" :class="{ 'is-loading': loading }">
    <button class="header-btn header-btn--back" type="button" @click="$emit('back')" aria-label="بازگشت">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
    </button>
    <h2 class="header-title" :title="title">{{ title }}</h2>
    <button class="header-btn header-btn--close" type="button" @click="$emit('close')" aria-label="بستن">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'افزودن به سبد' },
  subtitle: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

defineEmits(['close', 'back'])
</script>

<style scoped>
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 1rem;
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgb(var(--preview-surface-rgb, 255 255 255) / 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--preview-border);
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--preview-text);
  cursor: pointer;
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.header-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
}

.header-btn:focus-visible {
  outline: 2px solid var(--preview-primary);
  outline-offset: 2px;
}

.header-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--preview-text);
  text-align: center;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 0.5rem;
}

.is-loading .header-title {
  background: linear-gradient(90deg, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.08) 25%, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.16) 50%, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.08) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
  border-radius: 8px;
  height: 1em;
  width: 60%;
  margin: 0 auto;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
