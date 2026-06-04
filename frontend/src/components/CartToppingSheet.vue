<template>
  <teleport to="body">
    <div class="sheet-overlay" v-if="open" @click.self="$emit('close')">
      <section class="sheet-panel">
        <header class="sheet-head">
          <button class="icon-btn" type="button" @click="$emit('close')">&#x2039;</button>
        </header>

        <div class="hero" v-if="line">
          <img :src="line.item_image || fallbackImage" :alt="line.item_title" />
          <div class="hero-meta">
            <strong>{{ line.item_title }}</strong>
            <small>{{ removedCount }} ماده حذف شده</small>
          </div>
        </div>

        <p class="muted" v-if="loading">در حال دریافت اطلاعات آیتم...</p>

        <div class="editor-wrap" v-else>
          <IngredientQuantityEditor
            :ingredients="ingredients"
            :currency="currency"
            :model-value="localCustomization"
            @update:model-value="localCustomization = $event"
          />
        </div>

        <button class="apply-btn" type="button" :disabled="loading || !line" @click="apply">اعمال تغییرات روی آیتم</button>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import IngredientQuantityEditor from './IngredientQuantityEditor.vue'
import { sanitizeCustomization } from '@/utils/itemConfig'

const props = defineProps({
  open: { type: Boolean, default: false },
  line: { type: Object, default: null },
  ingredients: { type: Array, default: () => [] },
  customization: { type: Object, default: () => ({}) },
  currency: { type: String, default: 'TOMAN' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'apply'])

const localCustomization = ref({
  ingredient_adjustments: [],
  selected_modifiers: [],
})

const fallbackImage = 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=900&auto=format&fit=crop&q=60'

watch(
  () => [props.open, props.customization, props.ingredients],
  () => {
    localCustomization.value = sanitizeCustomization(props.customization || {}, props.ingredients || [])
  },
  { deep: true, immediate: true },
)

const removedCount = computed(() => {
  const ingredientsMap = new Map((props.ingredients || []).map((row) => [String(row.key || row.name || '').trim(), row]))
  let count = 0
  for (const row of localCustomization.value.ingredient_adjustments || []) {
    const key = String(row.ingredient_key || '').trim()
    if (!key || Number(row.multiplier || 0) > 0) {
      continue
    }
    const ing = ingredientsMap.get(key)
    if (!ing) {
      continue
    }
    if (Number(ing.min_multiplier || 0) <= 0) {
      count += 1
    }
  }
  return count
})

function apply() {
  emit('apply', sanitizeCustomization(localCustomization.value, props.ingredients || []))
}
</script>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.28);
  z-index: 120;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0.5rem;
}

.sheet-panel {
  width: min(560px, 100%);
  max-height: calc(100vh - 1rem);
  overflow: auto;
  border-radius: 34px;
  padding: 0.8rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.97);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.26);
  box-shadow: 0 24px 68px rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  display: grid;
  gap: 0.65rem;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  background: rgb(var(--palette-eggshell-rgb) / 0.92);
  color: var(--accent-gold);
  font-size: 1.2rem;
}

.hero {
  display: grid;
  justify-items: center;
  text-align: center;
  gap: 0.45rem;
}

.hero img {
  width: min(300px, 90%);
  height: 170px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  border-radius: 28px;
}

.hero-meta {
  display: grid;
  gap: 0.18rem;
}

.hero-meta small {
  color: var(--text-muted);
}

.editor-wrap {
  border-radius: 22px;
  background: rgb(var(--palette-eggshell-rgb) / 0.84);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  padding: 0.64rem;
}

.apply-btn {
  position: sticky;
  bottom: 0;
  width: 100%;
  border: 0;
  border-radius: 999px;
  padding: 0.84rem;
  background: var(--accent-green);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.42);
  color: #fff;
  font-family: inherit;
  font-size: 0.95rem;
}

.apply-btn:disabled {
  opacity: 0.55;
}
</style>
