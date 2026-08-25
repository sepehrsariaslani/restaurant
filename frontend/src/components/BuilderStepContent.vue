<template>
  <div class="step-content">
    <header class="step-content__header" v-if="step">
      <h3 class="step-content__title">{{ step.step_title }}</h3>
      <p v-if="step.step_description" class="step-content__desc muted">
        {{ step.step_description }}
      </p>
      <p class="step-content__hint muted" v-if="selectionHint">
        {{ selectionHint }}
      </p>
    </header>

    <div class="step-content__grid">
      <BuilderOptionCard
        v-for="option in availableOptions"
        :key="option.option_key"
        :option="option"
        :selection-mode="step?.selection_mode || 'single'"
        :selected="isSelected(option)"
        :disabled="isOptionDisabled(option)"
        :show-allergens="showAllergens"
        :currency="currency"
        @select="toggleOption"
      />
    </div>

    <p v-if="validationMessage" class="step-content__error">
      {{ validationMessage }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BuilderOptionCard from './BuilderOptionCard.vue'

const props = defineProps({
  step: { type: Object, default: null },
  selections: { type: Array, default: () => [] },
  showAllergens: { type: Boolean, default: true },
  currency: { type: String, default: 'TOMAN' },
})

const emit = defineEmits(['update:selections'])

const availableOptions = computed(() => {
  if (!props.step?.options) return []
  return props.step.options.filter(opt => Number(opt.is_available) !== 0)
})

const selectionHint = computed(() => {
  if (!props.step) return ''
  const min = Number(props.step.min_select) || 0
  const max = Number(props.step.max_select) || 0
  if (min && max && min === max) return `لطفا دقیقا ${min} مورد انتخاب کنید`
  if (min && max) return `حداقل ${min} و حداکثر ${max} انتخاب کنید`
  if (min) return `حداقل ${min} مورد انتخاب کنید`
  if (max) return `حداکثر ${max} مورد انتخاب کنید`
  return ''
})

const validationMessage = computed(() => {
  if (!props.step) return ''
  const min = Number(props.step.min_select) || 0
  const isRequired = Number(props.step.is_required) || 0
  if (isRequired && props.selections.length < min) {
    const remaining = min - props.selections.length
    return `لطفا حداقل ${remaining} مورد دیگر انتخاب کنید`
  }
  return ''
})

function isSelected(option) {
  return props.selections.some(s => s.option_key === option.option_key)
}

function isOptionDisabled(option) {
  if (Number(option.is_available) === 0) return true
  const max = Number(props.step?.max_select) || 0
  if (!max) return false
  if (isSelected(option)) return false
  return props.selections.length >= max
}

function toggleOption(option) {
  const mode = props.step?.selection_mode || 'single'
  let next

  if (mode === 'single') {
    next = isSelected(option) ? [] : [{ option_key: option.option_key, qty: 1 }]
  } else {
    if (isSelected(option)) {
      next = props.selections.filter(s => s.option_key !== option.option_key)
    } else {
      const max = Number(props.step?.max_select) || 0
      if (max && props.selections.length >= max) return
      next = [...props.selections, { option_key: option.option_key, qty: 1 }]
    }
  }

  emit('update:selections', next)
}
</script>

<style scoped>
.step-content {
  padding: 0.75rem 1rem 1rem;
}

.step-content__header {
  margin-bottom: 0.75rem;
}

.step-content__title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
}

.step-content__desc {
  margin: 0.2rem 0 0;
  font-size: 0.82rem;
  line-height: 1.45;
}

.step-content__hint {
  margin: 0.3rem 0 0;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent-gold, #c8963e);
}

.step-content__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.65rem;
}

.step-content__error {
  margin: 0.65rem 0 0;
  font-size: 0.75rem;
  color: #d93025;
  font-weight: 600;
  text-align: center;
}

.muted {
  color: var(--text-muted, #7a6e64);
}

@media (min-width: 600px) {
  .step-content__grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 920px) {
  .step-content {
    padding: 0.75rem 1.5rem 1.5rem;
  }
  .step-content__grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
  }
}
</style>
