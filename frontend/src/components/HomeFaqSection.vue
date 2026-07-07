<template>
  <section class="home-faq glass-card" dir="rtl" v-if="faqs.length">
    <div class="section-head">
      <h3 class="section-title">سوالات متداول</h3>
      <a href="/faq" class="more-link">همه سوالات</a>
    </div>

    <div class="faq-list">
      <article class="faq-item" v-for="(row, idx) in visibleFaqs" :key="row.name || idx">
        <button
          class="faq-trigger"
          type="button"
          :aria-expanded="openIndex === idx"
          :aria-controls="`home-faq-${idx}`"
          @click="toggle(idx)"
        >
          <strong>{{ row.question }}</strong>
          <ChevronDown class="faq-icon" :class="{ open: openIndex === idx }" :size="18" stroke-width="2.2" />
        </button>
        <p
          class="faq-answer muted"
          v-if="openIndex === idx"
          :id="`home-faq-${idx}`"
        >
          {{ row.answer }}
        </p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { normalizeFaqPublicRow } from '@/utils/faqMeta'

const props = defineProps({
  faqs: {
    type: Array,
    default: () => [],
  },
})

const openIndex = ref(0)
const visibleFaqs = computed(() => {
  const rows = (props.faqs || []).map((row) => normalizeFaqPublicRow(row))
  return rows.slice(0, 4)
})

function toggle(index) {
  openIndex.value = openIndex.value === index ? -1 : index
}
</script>

<style scoped>
.home-faq {
  margin-top: 0.8rem;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.more-link {
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
  font-size: 0.78rem;
  background: var(--accent-green20);
  color: var(--ink-800);
}

.faq-list {
  margin-top: 0.7rem;
  display: grid;
  gap: 0.52rem;
  grid-template-columns: 1fr 1fr;
}

.faq-item {
  border-radius: 14px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
}

.faq-trigger {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0.65rem 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  text-align: right;
  font-family: inherit;
  color: var(--text-primary);
  cursor: pointer;
}

.faq-trigger strong {
  font-size: 0.88rem;
}

.faq-icon {
  flex: 0 0 auto;
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 999px;
  padding: 0.28rem;
  background: var(--accent-green20);
  color: var(--accent-green);
  transition: transform 0.18s ease, background 0.18s ease;
}

.faq-icon.open {
  transform: rotate(180deg);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.faq-answer {
  margin: 0 0.75rem 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: rgb(255 255 255 / 0.52);
  border-right: 3px solid var(--accent-gold, #f4b24d);
  font-size: 0.82rem;
  line-height: 1.8;
}

@media (max-width: 980px) {
  .faq-list {
    grid-template-columns: 1fr;
  }
}
</style>
