<template>
  <section class="blk faq" dir="rtl" v-if="normalizedFaqs.length">
    <div class="blk__head blk__head--between">
      <div>
        <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
        <h2 class="blk__title">{{ title }}</h2>
        <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
      </div>
      <a v-if="moreLabel" class="blk__more" :href="moreHref">{{ moreLabel }}</a>
    </div>

    <!-- ACCORDION -->
    <div v-if="variant === 'accordion'" class="faq-acc">
      <article
        v-for="(row, idx) in normalizedFaqs"
        :key="row.name || idx"
        class="faq-acc__item"
        :class="{ open: openIndex === idx }"
      >
        <button class="faq-acc__trigger" type="button" @click="toggle(idx)" :aria-expanded="openIndex === idx">
          <span>{{ row.question }}</span>
          <ChevronDown class="faq-acc__icon" :size="18" stroke-width="2.2" />
        </button>
        <div v-show="openIndex === idx" class="faq-acc__answer">{{ row.answer }}</div>
      </article>
    </div>

    <!-- GRID -->
    <div v-else class="faq-grid">
      <article v-for="(row, idx) in normalizedFaqs" :key="row.name || idx" class="faq-grid__item">
        <h3>{{ row.question }}</h3>
        <p>{{ row.answer }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { normalizeFaqPublicRow } from '@/utils/faqMeta'
import '@/components/blocks/blocks.css'

const props = defineProps({
  variant: { type: String, default: 'accordion' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  moreLabel: { type: String, default: '' },
  moreHref: { type: String, default: '/faq' },
  faqs: { type: Array, default: () => [] },
})

const openIndex = ref(0)

const normalizedFaqs = computed(() =>
  (props.faqs || [])
    .filter((row) => Number(row?.is_active ?? 1) !== 0)
    .map((row) => normalizeFaqPublicRow(row)),
)

function toggle(index) {
  openIndex.value = openIndex.value === index ? -1 : index
}
</script>

<style scoped>
.faq-acc {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.faq-acc__item {
  border: 1px solid var(--blk-border);
  border-radius: var(--blk-radius-sm);
  background: var(--blk-surface);
  overflow: hidden;
  transition: border-color 0.15s ease;
}

.faq-acc__item.open {
  border-color: color-mix(in srgb, var(--blk-accent) 40%, transparent);
}

.faq-acc__trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem 1.1rem;
  border: 0;
  background: transparent;
  font: inherit;
  font-weight: 700;
  text-align: right;
  color: var(--blk-ink);
  cursor: pointer;
}

.faq-acc__icon {
  flex: 0 0 auto;
  color: var(--blk-accent);
  transition: transform 0.18s ease;
}

.faq-acc__item.open .faq-acc__icon {
  transform: rotate(180deg);
}

.faq-acc__answer {
  padding: 0 1.1rem 1.1rem;
  font-size: 0.9rem;
  line-height: 1.9;
  color: var(--blk-ink-soft);
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--blk-gap);
}

.faq-grid__item {
  padding: 1.25rem;
  border-radius: var(--blk-radius-sm);
  background: var(--blk-surface-soft);
}

.faq-grid__item h3 {
  margin: 0 0 0.5rem;
  font-size: 0.98rem;
  font-weight: 800;
}

.faq-grid__item p {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.85;
  color: var(--blk-ink-soft);
}
</style>
