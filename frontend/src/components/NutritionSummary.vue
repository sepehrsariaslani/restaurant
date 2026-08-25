<template>
  <div v-if="hasData" class="nutrition-summary">
    <div v-if="nutrition.kcal" class="nutrition-item nutrition-kcal">
      <span class="nutrition-icon">🔥</span>
      <span class="nutrition-value">{{ Math.round(nutrition.kcal) }}</span>
      <span class="nutrition-unit">kcal</span>
    </div>
    <div v-if="nutrition.protein_g" class="nutrition-item">
      <span class="nutrition-value">{{ Math.round(nutrition.protein_g) }}</span>
      <span class="nutrition-unit">پروتئین</span>
    </div>
    <div v-if="nutrition.carb_g" class="nutrition-item">
      <span class="nutrition-value">{{ Math.round(nutrition.carb_g) }}</span>
      <span class="nutrition-unit">کربوهیدرات</span>
    </div>
    <div v-if="nutrition.fat_g" class="nutrition-item">
      <span class="nutrition-value">{{ Math.round(nutrition.fat_g) }}</span>
      <span class="nutrition-unit">چربی</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  nutrition: {
    type: Object,
    default: () => ({}),
  },
})

const hasData = computed(() => {
  const n = props.nutrition
  return n && (n.kcal > 0 || n.protein_g > 0 || n.carb_g > 0 || n.fat_g > 0)
})
</script>

<style scoped>
.nutrition-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  padding: 0.75rem 1rem;
  border-radius: var(--preview-radius-sm);
  background: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.06);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.14);
  margin: 0.75rem 0;
}

.nutrition-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--preview-text);
  font-variant-numeric: tabular-nums;
}

.nutrition-icon {
  font-size: 0.85rem;
}

.nutrition-unit {
  font-weight: 500;
  color: var(--preview-muted);
  font-size: 0.75rem;
}
</style>
