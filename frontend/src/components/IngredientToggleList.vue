<template>
  <div class="section">
    <h3 class="section-title">داخلش هست / نیست</h3>
    <div class="stack" v-if="ingredients.length">
      <label class="ingredient-row" v-for="ingredient in ingredients" :key="ingredient.name">
        <div>
          <strong>{{ ingredient.name }}</strong>
          <p class="muted" v-if="Number(ingredient.is_included_by_default) === 1">
            پیش فرض در آیتم موجود است
          </p>
          <p class="muted" v-else>
            اختیاری - {{ formatMoney(ingredient.extra_when_added, currency) }}
          </p>
        </div>

        <template v-if="Number(ingredient.is_included_by_default) === 1">
          <button
            v-if="Number(ingredient.can_remove) === 1"
            type="button"
            class="secondary-btn"
            @click="toggleRemove(ingredient.name)"
          >
            {{ isRemoved(ingredient.name) ? 'برگردان' : 'حذف شود' }}
          </button>
          <span v-else class="badge">قابل حذف نیست</span>
        </template>

        <template v-else>
          <button type="button" class="secondary-btn" @click="toggleAdd(ingredient.name)">
            {{ isAdded(ingredient.name) ? 'حذف از افزودنی' : 'افزودن' }}
          </button>
        </template>
      </label>
    </div>
    <p v-else class="muted">برای این آیتم ingredient قابل شخصی سازی تعریف نشده است.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'
import { sanitizeCustomization } from '@/utils/itemConfig'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  ingredients: {
    type: Array,
    default: () => [],
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

const emit = defineEmits(['update:modelValue'])

const customization = computed(() => sanitizeCustomization(props.modelValue || {}))

function applyUpdate(next) {
  emit('update:modelValue', sanitizeCustomization(next))
}

function isRemoved(name) {
  return customization.value.removed_ingredients.includes(name)
}

function isAdded(name) {
  return customization.value.added_ingredients.includes(name)
}

function toggleRemove(name) {
  const removed = new Set(customization.value.removed_ingredients)
  if (removed.has(name)) {
    removed.delete(name)
  } else {
    removed.add(name)
  }

  applyUpdate({
    ...customization.value,
    removed_ingredients: Array.from(removed),
  })
}

function toggleAdd(name) {
  const added = new Set(customization.value.added_ingredients)
  if (added.has(name)) {
    added.delete(name)
  } else {
    added.add(name)
  }

  applyUpdate({
    ...customization.value,
    added_ingredients: Array.from(added),
  })
}
</script>

<style scoped>
.section {
  display: grid;
  gap: 0.6rem;
}

.stack {
  display: grid;
  gap: 0.55rem;
}

.ingredient-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.62rem 0.7rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.45);
}

.ingredient-row p {
  margin: 0.2rem 0 0;
  font-size: 0.84rem;
}
</style>
