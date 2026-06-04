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
  background: rgb(12 18 32 / 0.48);
  backdrop-filter: blur(2px);
  display: grid;
  place-items: center;
  z-index: 1200;
  padding: 1rem;
}

.popup-shell {
  width: min(920px, 100%);
  max-height: min(86vh, 860px);
  overflow: auto;
  border-radius: 18px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  background: linear-gradient(180deg, rgb(var(--palette-eggshell-rgb) / 0.98), rgb(var(--palette-eggshell-rgb) / 1));
  box-shadow: 0 28px 60px rgb(0 0 0 / 0.2);
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
  padding: 0.65rem 0.8rem;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.popup-foot {
  border-bottom: 0;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
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
  font-size: 0.92rem;
}

.popup-meta small {
  color: var(--text-muted);
  font-size: 0.77rem;
}

.popup-body {
  padding: 0.7rem 0.8rem;
  display: grid;
  gap: 0.55rem;
}

.close-btn {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  background: rgb(var(--palette-eggshell-rgb) / 0.88);
  color: var(--text-muted);
  border-radius: 10px;
  width: 30px;
  height: 30px;
  cursor: pointer;
}

@media (max-width: 720px) {
  .popup-overlay {
    padding: 0.5rem;
  }

  .popup-shell {
    max-height: 92vh;
    border-radius: 14px;
  }
}
</style>
