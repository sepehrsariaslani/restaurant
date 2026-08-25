<template>
  <div class="nutrition-card" v-if="hasNutrition">
    <div class="nutrition-card__header">
      <span class="nutrition-card__fire">🔥</span>
      <span class="nutrition-card__label">کالری</span>
    </div>
    <div class="nutrition-card__kcal">
      <strong class="nutrition-card__kcal-num">{{ kcalDisplay }}</strong>
      <span class="nutrition-card__kcal-unit">کیلوکالری</span>
    </div>
    <div class="nutrition-card__macros" v-if="macroList.length">
      <span
        class="macro-chip"
        v-for="m in macroList"
        :key="m.key"
      >
        <small class="macro-chip__label">{{ m.label }}</small>
        <strong class="macro-chip__value">{{ m.value }}</strong>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  nutrition: {
    type: Object,
    default: null,
  },
})

const kcal = computed(() => {
  const v = Number(props.nutrition?.kcal ?? 0)
  return Number.isFinite(v) && v > 0 ? Math.round(v) : 0
})

const kcalDisplay = computed(() => kcal.value)

const macroList = computed(() => {
  const n = props.nutrition || {}
  const macros = [
    { key: 'protein_g', label: 'پروتئین', suffix: 'g' },
    { key: 'carb_g', label: 'کربوهیدرات', suffix: 'g' },
    { key: 'fat_g', label: 'چربی', suffix: 'g' },
    { key: 'sugar_g', label: 'قند', suffix: 'g' },
  ]
  return macros
    .map((m) => {
      const v = Number(n[m.key] ?? 0)
      if (!Number.isFinite(v) || v <= 0) return null
      return { key: m.key, label: m.label, value: `${Math.round(v)} ${m.suffix}` }
    })
    .filter(Boolean)
})

const hasNutrition = computed(() => kcal.value > 0 || macroList.value.length > 0)
</script>

<style scoped>
.nutrition-card {
  border-radius: 18px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  background: rgb(var(--palette-eggshell-rgb) / 0.65);
  backdrop-filter: blur(8px);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.nutrition-card__header {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.nutrition-card__fire {
  font-size: 1.1rem;
}

.nutrition-card__label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink-800, #1e1a17);
}

.nutrition-card__kcal {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.nutrition-card__kcal-num {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--ink-900, #141210);
  line-height: 1;
}

.nutrition-card__kcal-unit {
  font-size: 0.78rem;
  color: var(--text-muted, #7a6e64);
}

.nutrition-card__macros {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.macro-chip {
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
  padding: 0.35rem 0.65rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.05rem;
  min-width: 60px;
}

.macro-chip__label {
  font-size: 0.68rem;
  color: var(--text-muted, #7a6e64);
}

.macro-chip__value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink-800, #1e1a17);
}
</style>
