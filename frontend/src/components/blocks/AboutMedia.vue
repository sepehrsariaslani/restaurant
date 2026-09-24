<template>
  <div
    class="about-media"
    :class="{ 'about-media--story': variant === 'story' }"
    role="img"
    :aria-label="alt || title"
  >
    <img v-if="image && !imageFailed" :src="image" :alt="alt || title" loading="lazy" @error="imageFailed = true" />
    <div v-else class="about-media__placeholder" aria-hidden="true">
      <component :is="iconComponent" :size="44" stroke-width="1.6" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { BookOpen, Eye, Sparkles, Target } from 'lucide-vue-next'

const props = defineProps({
  image: { type: String, default: '' },
  alt: { type: String, default: '' },
  title: { type: String, default: '' },
  variant: { type: String, default: 'card' },
})

const imageFailed = ref(false)
const iconComponent = computed(() => {
  const title = String(props.title || '')
  if (title.includes('ماموریت') || title.includes('مأموریت')) return Target
  if (title.includes('چشم‌انداز') || title.includes('چشم انداز')) return Eye
  if (title.includes('داستان') || title.includes('تاریخ')) return BookOpen
  return Sparkles
})

watch(() => props.image, () => { imageFailed.value = false })
</script>

<style scoped>
.about-media {
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  border-radius: inherit;
  color: var(--ds-color-action-primary);
  background:
    radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--ds-color-action-accent) 20%, transparent), transparent 44%),
    color-mix(in srgb, var(--ds-color-action-primary) 10%, var(--ds-color-surface-raised));
}

.about-media--story {
  aspect-ratio: 4 / 3;
}

.about-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.about-media__placeholder {
  width: 100%;
  height: 100%;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  padding: 1rem;
  color: var(--ds-color-action-primary);
  text-align: center;
}

</style>
