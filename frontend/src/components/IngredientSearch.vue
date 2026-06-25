<template>
  <div class="ingredient-search">
    <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input
      type="search"
      :value="modelValue"
      :placeholder="placeholder"
      class="search-input"
      @input="onInput"
    />
    <button
      v-if="modelValue"
      class="search-clear"
      type="button"
      @click="clear"
      aria-label="پاک کردن"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'جستجوی ماده...' },
  debounce: { type: Number, default: 200 },
})

const emit = defineEmits(['update:modelValue'])

let timer = null
const localValue = ref(props.modelValue)

watch(() => props.modelValue, (v) => {
  localValue.value = v
})

function onInput(e) {
  localValue.value = e.target.value
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    emit('update:modelValue', localValue.value)
  }, props.debounce)
}

function clear() {
  localValue.value = ''
  emit('update:modelValue', '')
  if (timer) clearTimeout(timer)
}
</script>

<style scoped>
.ingredient-search {
  display: flex;
  align-items: center;
  padding: 0.55rem 0.85rem;
  border-radius: var(--preview-radius-xs);
  border: 1px solid var(--preview-border);
  background: var(--preview-surface);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  margin: 0.75rem 0;
}

.ingredient-search:focus-within {
  border-color: var(--preview-primary);
  box-shadow: 0 0 0 3px rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.10);
}

.search-icon {
  color: var(--preview-muted);
  flex-shrink: 0;
  opacity: 0.7;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 0.88rem;
  color: var(--preview-text);
  outline: none;
  padding: 0 0.5rem;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--preview-muted);
  opacity: 0.6;
}

.search-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--preview-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease;
}

.search-clear:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
}

.search-clear:focus-visible {
  outline: 2px solid var(--preview-primary);
  outline-offset: 2px;
}
</style>
