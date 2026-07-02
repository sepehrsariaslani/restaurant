<template>
  <section class="blk features" dir="rtl">
    <div class="blk__head">
      <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
      <h2 class="blk__title">{{ title }}</h2>
      <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
    </div>

    <div :class="variant === 'inline' ? 'feat-inline' : 'feat-cards'">
      <div
        v-for="(f, idx) in items"
        :key="idx"
        :class="variant === 'inline' ? 'feat-inline__item' : 'feat-card'"
      >
        <span class="feat-icon">
          <component :is="iconFor(f.icon)" :size="22" stroke-width="2" />
        </span>
        <div class="feat-body">
          <h3>{{ f.title }}</h3>
          <p v-if="f.description">{{ f.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Zap, Sliders, Leaf, Clock, Truck, Star, Heart, ShieldCheck, Sparkles } from 'lucide-vue-next'
import '@/components/blocks/blocks.css'

defineProps({
  variant: { type: String, default: 'cards' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  items: { type: Array, default: () => [] },
})

const iconMap = {
  zap: Zap,
  sliders: Sliders,
  leaf: Leaf,
  clock: Clock,
  truck: Truck,
  star: Star,
  heart: Heart,
  shield: ShieldCheck,
  sparkles: Sparkles,
}

function iconFor(name) {
  return iconMap[String(name || '').trim().toLowerCase()] || Sparkles
}
</script>

<style scoped>
.feat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--blk-gap);
}

.feat-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem 1.35rem;
  border-radius: var(--blk-radius);
  background: var(--blk-surface);
  border: 1px solid var(--blk-border);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.feat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 40px rgb(0 0 0 / 0.07);
}

.feat-inline {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--blk-gap);
  padding: 1.25rem;
  border-radius: var(--blk-radius);
  background: var(--blk-surface-soft);
}

.feat-inline__item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.feat-icon {
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--blk-accent);
  background: color-mix(in srgb, var(--blk-accent) 12%, transparent);
}

.feat-body h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 800;
}

.feat-body p {
  margin: 0.3rem 0 0;
  font-size: 0.88rem;
  line-height: 1.8;
  color: var(--blk-ink-soft);
}
</style>
