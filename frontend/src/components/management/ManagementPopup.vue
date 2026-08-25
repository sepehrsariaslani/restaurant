<template>
  <Teleport to="body">
    <div v-if="open" class="popup-overlay" @click="handleBackdropClick">
      <section class="popup-shell" :class="`size-${size}`" role="dialog" aria-modal="true" :aria-label="title" @click.stop>
        <header class="popup-head">
          <div class="popup-meta">
            <strong>{{ title }}</strong>
            <small v-if="subtitle">{{ subtitle }}</small>
          </div>
          <button type="button" class="close-btn" @click="close">×</button>
        </header>

        <div class="popup-body">
          <slot />
        </div>

        <footer class="popup-foot">
          <slot name="footer" :close="close" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'پنجره',
  },
  subtitle: {
    type: String,
    default: '',
  },
  closeOnBackdrop: {
    type: Boolean,
    default: true,
  },
  closeOnEscape: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: 'md',
  },
})

const emit = defineEmits(['update:open'])

function close() {
  emit('update:open', false)
}

function handleBackdropClick() {
  if (!props.closeOnBackdrop) {
    return
  }
  close()
}

function onKeydown(event) {
  if (!props.open || !props.closeOnEscape) {
    return
  }
  if (event.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgb(31 21 14 / 0.55);
  backdrop-filter: blur(5px);
  display: grid;
  place-items: center;
  z-index: 1200;
  padding: 1rem;
}

.popup-shell {
  width: min(920px, 100%);
  max-height: min(86vh, 860px);
  overflow-y: auto;
  overflow-x: visible;
  border-radius: 18px;
  border: 1px solid color-mix(in srgb, var(--mg-border) 82%, transparent);
  background: linear-gradient(180deg, var(--mg-bg-surface), var(--mg-bg-page));
  color: var(--mg-text-main);
  box-shadow: 0 28px 60px rgb(30 20 13 / 0.3);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
}

.popup-shell.size-sm {
  width: min(680px, 100%);
}

.popup-shell.size-md {
  width: min(920px, 100%);
}

.popup-shell.size-lg {
  width: min(1120px, 100%);
}

.popup-shell.size-xl {
  width: min(1320px, 100%);
}

.popup-head,
.popup-foot {
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.popup-foot {
  border-bottom: 0;
  border-top: 1px solid var(--mg-border-light);
}

.popup-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 0.5rem;
}

.popup-meta {
  display: grid;
  gap: 0.12rem;
}

.popup-meta strong {
  font-size: 0.95rem;
  color: var(--mg-text-main);
}

.popup-meta small {
  color: var(--mg-text-muted);
  font-size: 0.78rem;
}

.popup-body {
  padding: 0.7rem 0.8rem;
  display: grid;
  gap: 0.55rem;
}

.close-btn {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  border-radius: 10px;
  width: 30px;
  height: 30px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.12s ease;
}

.close-btn:hover {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

@media (max-width: 720px) {
  .popup-overlay {
    padding: 0;
    place-items: end center;
  }

  .popup-shell {
    max-height: 92vh;
    border-radius: 22px 22px 0 0;
    border-bottom: 0;
    padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
    width: 100%;
  }
}
</style>
