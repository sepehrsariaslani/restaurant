<template>
  <div
    class="category-media"
    :class="{ 'category-media--circle': variant === 'circle' }"
    aria-hidden="true"
  >
    <img
      v-if="image && !imageFailed"
      class="category-media__image"
      :src="image"
      alt=""
      loading="lazy"
      @error="imageFailed = true"
    />
    <component
      v-else
      :is="iconComponent"
      class="category-media__icon"
      :size="variant === 'circle' ? 30 : 38"
      stroke-width="1.8"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Bean, Coffee, CupSoda, Salad, Sandwich, Soup } from 'lucide-vue-next'

const props = defineProps({
  image: { type: String, default: '' },
  icon: { type: String, default: '' },
  variant: { type: String, default: 'grid' },
})

const imageFailed = ref(false)
const iconMap = { bean: Bean, coffee: Coffee, cupsoda: CupSoda, salad: Salad, sandwich: Sandwich, soup: Soup }

const iconComponent = computed(() => {
  const key = String(props.icon || '')
    .trim()
    .replace(/^Lucide/, '')
    .replace(/[^a-z]/gi, '')
    .toLowerCase()
  return iconMap[key] || Soup
})

watch(() => props.image, () => { imageFailed.value = false })
</script>

<style scoped>
.category-media {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 1px solid var(--blk-border, var(--ds-color-border));
  border-radius: var(--blk-radius-sm, 12px);
  color: var(--ds-color-action-primary);
  background:
    radial-gradient(circle at 78% 18%, color-mix(in srgb, var(--ds-color-action-accent) 17%, transparent), transparent 43%),
    color-mix(in srgb, var(--ds-color-action-primary) 9%, var(--ds-color-surface-raised));
}

.category-media--circle {
  width: 88px;
  flex: 0 0 88px;
  aspect-ratio: 1;
  border-radius: 50%;
  transition: transform 160ms ease, border-color 160ms ease;
}

.category-media__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.category-media__icon {
  filter: drop-shadow(0 4px 8px color-mix(in srgb, var(--ds-color-action-primary) 14%, transparent));
}
</style>
