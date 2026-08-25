<template>
  <a class="group-card" :href="groupUrl">
    <div class="group-card__media" :class="{ 'group-card__media--empty': !group.image }">
      <img
        v-if="group.image"
        :src="group.image"
        :alt="group.title"
        class="group-card__image"
        loading="lazy"
      />
      <div v-else class="group-card__placeholder">{{ initials }}</div>
      <div class="group-card__overlay"></div>
    </div>

    <div class="group-card__body">
      <div class="group-card__copy">
        <small class="group-card__eyebrow">گروه محصول</small>
        <h3 class="group-card__title">{{ group.title }}</h3>
        <p v-if="group.description" class="group-card__desc">{{ group.description }}</p>
      </div>

      <div class="group-card__meta">
        <span class="group-card__count">{{ itemCountLabel }}</span>
        <span class="group-card__cta">مشاهده منو ←</span>
      </div>
    </div>
  </a>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  group: {
    type: Object,
    required: true,
  },
})

const groupUrl = computed(() => `/menu?category=${encodeURIComponent(props.group.slug || '')}`)

const initials = computed(() => {
  const value = String(props.group.title || 'گروه').trim()
  return (
    value
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('') || 'گ'
  )
})

const itemCountLabel = computed(() => {
  const count = Number(props.group.item_count || 0)
  if (!count) return 'بدون آیتم'
  return `${count.toLocaleString('fa-IR')} آیتم`
})
</script>

<style scoped>
.group-card {
  display: grid;
  gap: 0.9rem;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  border-radius: 22px;
  padding: 0.85rem;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 16px 34px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.group-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 42px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.group-card__media {
  position: relative;
  min-height: 180px;
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--accent-green20, #eefaf0), rgba(255, 255, 255, 0.88));
}

.group-card__media--empty {
  display: grid;
  place-items: center;
}

.group-card__image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.group-card__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 0%, rgb(15 23 42 / 0.18) 100%);
  pointer-events: none;
}

.group-card__placeholder {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--accent-green, #2f855a);
  font-size: 1.35rem;
  font-weight: 900;
}

.group-card__body {
  display: grid;
  gap: 0.8rem;
}

.group-card__copy {
  display: grid;
  gap: 0.3rem;
}

.group-card__eyebrow {
  color: var(--text-muted, #64748b);
  font-size: 0.72rem;
  font-weight: 700;
}

.group-card__title {
  margin: 0;
  color: var(--text-primary, #0f172a);
  font-size: 1.05rem;
  font-weight: 900;
}

.group-card__desc {
  margin: 0;
  color: var(--text-secondary, #475569);
  font-size: 0.88rem;
  line-height: 1.8;
}

.group-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.group-card__count {
  color: var(--text-muted, #64748b);
  font-size: 0.8rem;
  font-weight: 700;
}

.group-card__cta {
  color: var(--accent-green, #2f855a);
  font-size: 0.84rem;
  font-weight: 800;
}
</style>
