<template>
  <label class="management-note-field" :class="{ 'is-disabled': disabled, 'is-required': required }">
    <span class="note-field-head">
      <span class="note-field-label">
        <span class="note-field-icon" aria-hidden="true">✎</span>
        <span>{{ label }}</span>
        <b v-if="required" class="note-field-required">*</b>
      </span>
      <small v-if="hint" class="note-field-hint">{{ hint }}</small>
    </span>

    <textarea
      v-if="multiline"
      ref="fieldRef"
      class="input note-field-control"
      :value="modelValue"
      :rows="rows"
      :maxlength="maxlength || undefined"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :required="required"
      @input="emitValue"
      @focus="emit('focus', $event)"
      @blur="emit('blur', $event)"
    ></textarea>
    <input
      v-else
      ref="fieldRef"
      class="input note-field-control"
      type="text"
      :value="modelValue"
      :maxlength="maxlength || undefined"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :required="required"
      @input="emitValue"
      @focus="emit('focus', $event)"
      @blur="emit('blur', $event)"
    />

    <span v-if="maxlength || showCount" class="note-field-footer">
      <small v-if="helperText" class="note-field-helper">{{ helperText }}</small>
      <small v-if="maxlength || showCount" class="note-field-count">
        {{ valueLength }}<span v-if="maxlength"> / {{ maxlength }}</span>
      </small>
    </span>
  </label>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: 'یادداشت' },
  placeholder: { type: String, default: 'یادداشت یا توضیحی وارد کنید...' },
  hint: { type: String, default: '' },
  helperText: { type: String, default: '' },
  rows: { type: [Number, String], default: 3 },
  maxlength: { type: [Number, String], default: 0 },
  showCount: { type: Boolean, default: false },
  multiline: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])
const fieldRef = ref(null)
const valueLength = computed(() => String(props.modelValue ?? '').length)

function emitValue(event) {
  emit('update:modelValue', event.target.value)
}

defineExpose({ fieldRef })
</script>

<style scoped>
.management-note-field {
  display: grid;
  min-width: 0;
  gap: 0.38rem;
  color: var(--mg-text-main, #34261f);
  font-size: 0.78rem;
}

.note-field-head,
.note-field-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
}

.note-field-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 800;
}

.note-field-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.35rem;
  height: 1.35rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary, #c97852) 25%, transparent);
  border-radius: 0.45rem;
  background: color-mix(in srgb, var(--mg-primary, #c97852) 9%, transparent);
  color: var(--mg-primary, #c97852);
  font-size: 0.86rem;
  line-height: 1;
}

.note-field-required {
  color: var(--mg-danger, #a6543f);
}

.note-field-hint,
.note-field-helper,
.note-field-count {
  color: var(--mg-text-muted, #746454);
  font-size: 0.68rem;
  font-weight: 500;
  line-height: 1.5;
}

.note-field-control {
  min-height: 42px;
  resize: vertical;
  border-color: var(--mg-border, #d8c8b4);
  background: var(--mg-bg-surface, #fbf7f1);
  color: var(--mg-text-main, #34261f);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

textarea.note-field-control {
  min-height: 76px;
  line-height: 1.75;
}

.note-field-control::placeholder {
  color: var(--mg-text-muted, #746454);
  opacity: 0.68;
}

.note-field-control:focus {
  border-color: var(--mg-primary, #c97852);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-primary, #c97852) 14%, transparent);
  outline: none;
}

.note-field-control:disabled,
.note-field-control:read-only {
  cursor: not-allowed;
  opacity: 0.68;
}

.note-field-footer {
  min-height: 0.9rem;
}

.note-field-count {
  margin-inline-start: auto;
  direction: ltr;
}

.is-disabled {
  opacity: 0.7;
}

@media (max-width: 620px) {
  .note-field-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.18rem;
  }
}
</style>
