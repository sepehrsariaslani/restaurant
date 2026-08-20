<template>
  <label class="toggle-switch" :class="{ checked: modelValue, disabled, compact }">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="switch-track" aria-hidden="true">
      <span class="switch-thumb"></span>
    </span>
    <span class="switch-copy">
      <strong>{{ label }}</strong>
      <small v-if="hint">{{ hint }}</small>
    </span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    required: true,
  },
  hint: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.toggle-switch {
  min-height: 3.25rem;
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 12px;
  background: var(--mg-bg-surface, #fff);
  color: var(--mg-text-main);
  padding: 0.55rem 0.65rem;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}

.toggle-switch:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 24%, transparent);
  box-shadow: var(--mg-shadow-sm);
}

.toggle-switch.checked {
  border-color: color-mix(in srgb, var(--mg-primary) 26%, transparent);
  background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface));
}

.toggle-switch.compact {
  min-height: 2.25rem;
  width: max-content;
  padding: 0.3rem 0.45rem;
  grid-template-columns: auto;
  justify-items: center;
}

.toggle-switch.disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.toggle-switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.switch-track {
  width: 2.7rem;
  height: 1.55rem;
  border-radius: 999px;
  background: var(--mg-border, #cbd5e1);
  display: inline-flex;
  align-items: center;
  padding: 0.18rem;
  transition: background-color 0.18s ease;
}

.toggle-switch.compact .switch-track {
  width: 2.35rem;
  height: 1.35rem;
}

.toggle-switch.compact .switch-thumb {
  width: 0.95rem;
  height: 0.95rem;
}

.switch-thumb {
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 2px 5px rgb(15 23 42 / 0.18);
  transform: translateX(0);
  transition: transform 0.18s ease;
}

.toggle-switch.checked .switch-track {
  background: var(--mg-primary);
}

.toggle-switch.checked .switch-thumb {
  transform: translateX(-1.15rem);
}

.toggle-switch.compact.checked .switch-thumb {
  transform: translateX(-1rem);
}

.switch-copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.toggle-switch.compact .switch-copy {
  display: none;
}

.switch-copy strong {
  font-size: 0.85rem;
  line-height: 1.5;
}

.switch-copy small {
  color: var(--mg-text-muted);
  font-size: 0.74rem;
  line-height: 1.6;
}

.toggle-switch:focus-within {
  outline: 3px solid color-mix(in srgb, var(--mg-primary) 18%, transparent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .toggle-switch,
  .switch-track,
  .switch-thumb {
    transition-duration: 0.01ms;
  }
}
</style>
