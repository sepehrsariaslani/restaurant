<template>
  <section class="home-faq glass-card" dir="rtl" v-if="faqs.length">
    <div class="section-head">
      <h3 class="section-title">سوالات متداول</h3>
      <a href="/faq" class="more-link">همه سوالات</a>
    </div>

    <div class="faq-list">
      <article class="faq-item" v-for="(row, idx) in visibleFaqs" :key="row.name || idx">
        <button class="faq-trigger" type="button" @click="toggle(idx)">
          <strong>{{ row.question }}</strong>
          <span>{{ openIndex === idx ? '−' : '+' }}</span>
        </button>
        <p class="faq-answer muted" v-if="openIndex === idx">{{ row.answer }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
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

.faq-trigger span {
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-green20);
  color: var(--accent-green);
  font-size: 0.95rem;
}

.faq-answer {
  margin: 0;
  padding: 0 0.75rem 0.7rem;
  font-size: 0.82rem;
  line-height: 1.7;
}

@media (max-width: 980px) {
  .faq-list {
    grid-template-columns: 1fr;
  }
}
</style>
