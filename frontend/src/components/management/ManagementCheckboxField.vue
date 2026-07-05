<template>
  <label
    class="checkbox-field"
    :class="{
      checked: modelValue,
      disabled,
      compact,
    }"
  >
    <span class="checkbox-box" aria-hidden="true">
      <input
        type="checkbox"
        :checked="modelValue"
        :disabled="disabled"
        @change="$emit('update:modelValue', $event.target.checked)"
      />
      <span class="checkbox-indicator">✓</span>
    </span>

    <span class="checkbox-copy">
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
.checkbox-field {
  min-height: 3rem;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.8rem;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 14px;
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}

.checkbox-field:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.24);
  box-shadow: 0 10px 22px rgb(15 23 42 / 0.06);
}

.checkbox-field.checked {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.22);
  background: var(--module-50, rgb(139 94 52 / 0.075));
}

.checkbox-field.disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.checkbox-field.compact {
  min-height: 2.6rem;
  padding: 0.52rem 0.62rem;
}

.checkbox-box {
  position: relative;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 0.42rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.26);
  background: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.checkbox-box input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.checkbox-indicator {
  font-size: 0.8rem;
  line-height: 1;
  color: transparent;
  transition: color 0.18s ease;
}

.checkbox-field.checked .checkbox-box {
  background: var(--module-500, #8b5e34);
  border-color: var(--module-500, #8b5e34);
}

.checkbox-field.checked .checkbox-indicator {
  color: #fff;
}

.checkbox-copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.checkbox-copy strong {
  font-size: 0.84rem;
  line-height: 1.5;
  color: var(--text-primary, #0f172a);
}

.checkbox-copy small {
  font-size: 0.74rem;
  line-height: 1.55;
  color: var(--text-muted, #64748b);
}

.checkbox-field:focus-within {
  outline: 3px solid rgb(var(--palette-deep-sapphire-rgb, 124 90 66) / 0.18);
  outline-offset: 2px;
}
</style>
