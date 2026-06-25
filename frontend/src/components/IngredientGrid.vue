<template>
  <div class="ingredient-grid" :style="{ gridTemplateColumns: `repeat(${columns}, 1fr)` }">
    <div
      v-for="(ingredient, idx) in ingredients"
      :key="ingredient.name || idx"
      class="ingredient-card"
    >
      <div class="card-img-wrap">
        <img
          v-if="ingredient.image"
          :src="ingredient.image"
          :alt="ingredient.name"
          class="card-img"
          loading="lazy"
        />
        <div v-else class="card-img-placeholder">
          {{ (ingredient.name || '?').slice(0, 1) }}
        </div>
      </div>
      <div class="card-info">
        <span class="card-name">{{ ingredient.name }}</span>
        <span class="card-qty">{{ ingredient.qty }} {{ ingredient.uom }}</span>
        <span v-if="ingredient.kcal" class="card-kcal">{{ ingredient.kcal }} kcal</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ingredients: {
    type: Array,
    default: () => [],
  },
  columns: {
    type: Number,
    default: 2,
  },
})
</script>

<style scoped>
.ingredient-grid {
  display: grid;
  gap: 0.75rem;
}

.ingredient-card {
  background: var(--preview-surface);
  border: 1px solid var(--preview-border);
  border-radius: var(--preview-radius-sm);
  padding: 0.65rem;
  transition: transform 0.2s ease-out, box-shadow 0.2s ease-out;
}

@media (hover: hover) {
  .ingredient-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  }
}

.card-img-wrap {
  width: 100%;
  height: 90px;
  border-radius: var(--preview-radius-xs);
  overflow: hidden;
  background: linear-gradient(135deg, rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.06), rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.04));
}

.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.card-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--preview-muted);
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  margin-top: 0.45rem;
}

.card-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--preview-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-qty {
  font-size: 0.78rem;
  color: var(--preview-muted);
}

.card-kcal {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--preview-accent);
}

@media (max-width: 767px) {
  .card-img-wrap {
    height: 80px;
  }
}
</style>
