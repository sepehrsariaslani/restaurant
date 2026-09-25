<template>
  <article class="home-product-card" :class="{ 'is-added': justAdded }">
    <a class="home-product-card__media" :href="itemUrl" :aria-label="`مشاهده ${item.title}`">
      <span class="home-product-card__shine" aria-hidden="true"></span>
      <img class="home-product-card__image" :src="resolvedImage" :alt="item.title" loading="lazy" />
    </a>

    <div class="home-product-card__body">
      <div class="home-product-card__info">
        <span class="home-product-card__offer">{{ offerText }}</span>
        <p class="home-product-card__category">{{ categoryLabel }}</p>
        <h3 class="home-product-card__title">{{ item.title }}</h3>
        <div class="home-product-card__tags" v-if="displayTags.length">
          <span v-for="tag in displayTags" :key="tag" class="home-product-card__tag">{{ tag }}</span>
        </div>
      </div>

      <div class="home-product-card__divider" aria-hidden="true"></div>

      <div class="home-product-card__action">
        <strong class="home-product-card__price">{{ formattedPrice }}</strong>
        <button class="home-product-card__add" type="button" :class="{ added: justAdded }" :aria-label="`افزودن ${item.title} به سبد`" @click="handleQuickAdd">
          <span class="home-product-card__add-icon">{{ justAdded ? '✓' : '+' }}</span>
          <span class="home-product-card__add-label">{{ justAdded ? 'افزوده شد' : 'افزودن' }}</span>
        </button>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

const emit = defineEmits(['quick-add'])
const justAdded = ref(false)
let addTimer = null

const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=70'
const itemUrl = computed(() => `/item/${props.item.slug}`)
const resolvedImage = computed(() => props.item.image || fallbackImage)
const formattedPrice = computed(() => formatMoney(props.item.base_price, props.currency))
const categoryLabel = computed(() => props.item.category_title || props.item.category || props.item.item_group || '')
const offerText = computed(() => {
  const prep = Number(props.item.prep_time_mins || 0)
  return prep > 0 ? `آماده در ${prep} دقیقه` : 'محبوب امروز'
})

function pushUniqueTag(list, value) {
  const label = String(value || '').trim()
  if (!label || list.includes(label)) return
  list.push(label)
}

const displayTags = computed(() => {
  const result = []
  pushUniqueTag(result, props.item.category_title || props.item.category || props.item.item_group)
  pushUniqueTag(result, props.item.subcategory_title || props.item.subcategory || props.item.item_subgroup)

  const raw = props.item.tags || props.item.item_tags || []
  const tags = Array.isArray(raw) ? raw : []
  for (const tag of tags) {
    pushUniqueTag(result, typeof tag === 'string' ? tag : tag?.title || tag?.tag_title || tag?.tag || tag?.name)
  }

  return result.slice(0, 2)
})

function handleQuickAdd() {
  emit('quick-add', props.item)
  justAdded.value = true
  clearTimeout(addTimer)
  addTimer = setTimeout(() => {
    justAdded.value = false
  }, 1600)
}

onUnmounted(() => {
  clearTimeout(addTimer)
})
</script>

<style scoped>
.home-product-card {
  --home-card-bg: var(--ds-color-product-media-surface);
  --home-card-accent: var(--ds-color-product-accent);
  --home-card-surface: var(--ds-color-text-primary);
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 100%;
  overflow: hidden;
  border-radius: 1.45rem;
  background: var(--home-card-bg);
  border: 1px solid var(--ds-color-border);
  box-shadow: var(--ds-shadow-sm);
  isolation: isolate;
  transform: translateZ(0);
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}

.home-product-card::before {
  content: '';
  position: absolute;
  inset: 0.48rem;
  border-radius: 1.1rem;
  border: 1px solid var(--ds-color-border);
  pointer-events: none;
  z-index: 2;
}

.home-product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--ds-shadow-md);
}

.home-product-card__media {
  position: relative;
  display: block;
  margin: 0.55rem 0.55rem 0;
  min-height: 168px;
  max-height: 240px;
  aspect-ratio: 1.25 / 1;
  overflow: hidden;
  border-radius: 1.05rem 1.05rem 1.35rem 1.35rem;
  background: var(--ds-color-product-media-surface);
  box-shadow: inset 0 0 0 1px var(--ds-color-border);
  text-decoration: none;
}

.home-product-card__shine {
  display: none;
}

.home-product-card__image {
  position: absolute;
  inset: 0.55rem;
  width: calc(100% - 1.1rem);
  height: calc(100% - 1.1rem);
  object-fit: contain;
  object-position: center;
  filter: drop-shadow(0 8px 12px color-mix(in srgb, var(--ds-color-text-primary) 12%, transparent));
  transition: filter 0.28s ease;
  z-index: 1;
}

.home-product-card:hover .home-product-card__image {
  filter: drop-shadow(0 10px 14px color-mix(in srgb, var(--ds-color-text-primary) 16%, transparent));
}

.home-product-card__offer {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 1.45rem;
  margin-bottom: 0.45rem;
  padding: 0.12rem 0.58rem;
  border-radius: 999px;
  background: var(--ds-color-product-accent-soft);
  color: var(--ds-color-product-accent);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  text-align: center;
}

.home-product-card__body {
  position: relative;
  z-index: 3;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 1px auto;
  gap: 0.65rem;
  align-items: end;
  padding: 0.8rem 0.9rem 0.95rem;
  color: var(--home-card-surface);
}

.home-product-card__info {
  min-width: 0;
}

.home-product-card__category {
  margin: 0 0 0.15rem;
  color: var(--ds-color-text-muted);
  font-size: 0.66rem;
  font-weight: 800;
}

.home-product-card__title {
  margin: 0;
  color: var(--home-card-surface);
  font-size: clamp(1.05rem, 2vw, 1.35rem);
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: -0.03em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.home-product-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.28rem;
  margin-top: 0.55rem;
}

.home-product-card__tag {
  display: inline-flex;
  align-items: center;
  max-width: 7.8rem;
  min-height: 1.35rem;
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  background: var(--ds-color-surface-muted);
  color: var(--ds-color-text-secondary);
  font-size: 0.64rem;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border: 1px solid var(--ds-color-border);
}

.home-product-card__divider {
  width: 1px;
  height: 4.35rem;
  background: var(--ds-color-border);
}

.home-product-card__action {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.34rem;
  min-width: 5.8rem;
}

.home-product-card__price {
  color: var(--ds-color-product-accent);
  font-size: clamp(1rem, 2vw, 1.32rem);
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -0.04em;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.home-product-card__add {
  min-width: 5.6rem;
  height: 2.25rem;
  border: 1px solid var(--ds-color-product-accent);
  border-radius: 999px;
  background: transparent;
  color: var(--ds-color-product-accent);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  padding: 0 0.7rem;
  font: inherit;
  font-size: 0.78rem;
  line-height: 1;
  font-weight: 800;
  box-shadow: none;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
}

.home-product-card__add:hover,
.home-product-card__add:focus-visible,
.home-product-card__add.added {
  background: var(--home-card-accent);
  border-color: var(--home-card-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse));
  transform: translateY(-1px);
  outline: none;
}

.home-product-card__add:focus-visible {
  box-shadow: 0 0 0 3px var(--ds-color-product-accent-soft);
}

.home-product-card__add-icon {
  font-size: 1rem;
}

.home-product-card__add-label {
  white-space: nowrap;
}

@media (max-width: 760px) {
  .home-product-card {
    border-radius: 1.3rem;
  }

  .home-product-card__media {
    min-height: 168px;
    max-height: 220px;
    aspect-ratio: 1.25 / 1;
    border-radius: 0.95rem 0.95rem 1.2rem 1.2rem;
  }

  .home-product-card__body {
    grid-template-columns: 1fr;
    gap: 0.55rem;
    align-items: start;
  }

  .home-product-card__divider {
    display: none;
  }

  .home-product-card__action {
    width: 100%;
    min-width: 0;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-product-card,
  .home-product-card__image,
  .home-product-card__shine,
  .home-product-card__add {
    transition: none;
  }

  .home-product-card:hover,
  .home-product-card:hover .home-product-card__image,
  .home-product-card:hover .home-product-card__shine {
    transform: none;
  }
}
</style>
