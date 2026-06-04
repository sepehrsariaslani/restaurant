<template>
  <GlassShell class="faq-shell" :title="'سوالات متداول'" :subtitle="branding.name || 'پشتیبانی سفارش'">
    <section class="faq-container">
      <ScrollReveal>
        <div class="faq-hero glass-card">
          <div>
            <span class="faq-chip">پاسخ‌گویی سریع</span>
            <h1>هر سوالی درباره سفارش، آماده پاسخ هستیم</h1>
            <p class="muted">
              سوالات پرتکرار کاربران را اینجا جمع‌آوری کرده‌ایم تا سریع‌تر پاسخ موردنظر خود را پیدا کنید.
            </p>
            <a class="primary-btn" href="/menu">شروع سفارش</a>
          </div>
          <div class="faq-meta">
            <article>
              <strong>{{ faqs.length.toLocaleString('fa-IR') }}</strong>
              <small>سوال ثبت‌شده</small>
            </article>
            <article>
              <strong>{{ groupedFaqs.length.toLocaleString('fa-IR') }}</strong>
              <small>دسته سوال</small>
            </article>
          </div>
        </div>
      </ScrollReveal>

      <section class="faq-groups" v-if="groupedFaqs.length">
        <article class="faq-category glass-card" v-for="(group, groupIndex) in groupedFaqs" :key="group.category">
          <header class="category-head">
            <h2>{{ group.category }}</h2>
            <small>{{ group.rows.length.toLocaleString('fa-IR') }} سوال</small>
          </header>

          <div class="faq-grid">
            <ScrollReveal
              v-for="(faq, idx) in group.rows"
              :key="faq.name || `${group.category}-${idx}`"
              :delay="Math.min(idx + groupIndex, 10) * 45"
            >
              <article class="faq-row">
                <button class="faq-trigger" type="button" @click="toggle(`${group.category}-${idx}`)">
                  <div class="faq-title-wrap">
                    <span class="faq-icon" v-if="faq.icon">{{ faq.icon }}</span>
                    <strong>{{ faq.question }}</strong>
                  </div>
                  <span :class="{ open: openIndex === `${group.category}-${idx}` }">+</span>
                </button>

                <transition name="faq-drop">
                  <div class="faq-answer-wrap" v-if="openIndex === `${group.category}-${idx}`">
                    <img class="faq-image" v-if="faq.image" :src="faq.image" :alt="faq.question" />
                    <p class="muted faq-summary" v-if="faq.summary">{{ faq.summary }}</p>
                    <p class="muted faq-answer">{{ faq.answer }}</p>
                  </div>
                </transition>
              </article>
            </ScrollReveal>
          </div>
        </article>
      </section>

      <ScrollReveal v-else>
        <section class="glass-card empty-state">
          <p class="muted">سوالات متداول هنوز ثبت نشده است.</p>
        </section>
      </ScrollReveal>
    </section>
  </GlassShell>
</template>

<script setup>
import { computed, ref } from 'vue'
import GlassShell from '@/components/GlassShell.vue'
import ScrollReveal from '@/components/ScrollReveal.vue'
import { normalizeFaqPublicRow } from '@/utils/faqMeta'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const openIndex = ref('')
const branding = computed(() => props.boot.branding || {})
const faqs = computed(() => {
  const rows = Array.isArray(props.boot.faq_items) ? props.boot.faq_items : []
  return rows.map((row) => normalizeFaqPublicRow(row)).filter((row) => row.is_active !== 0)
})

const groupedFaqs = computed(() => {
  const map = new Map()
  for (const row of faqs.value) {
    const category = String(row.category || 'عمومی').trim() || 'عمومی'
    if (!map.has(category)) {
      map.set(category, [])
    }
    map.get(category).push(row)
  }
  return Array.from(map.entries()).map(([category, rows]) => ({
    category,
    rows: rows.sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0)),
  }))
})

function toggle(index) {
  openIndex.value = openIndex.value === index ? '' : index
}
</script>

<style scoped>
.faq-shell {
  background: #fff;
}

.faq-container {
  width: min(1120px, calc(100% - 2rem));
  margin: 0 auto 1.4rem;
}

.faq-hero {
  margin-bottom: 1rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 1rem;
  align-items: stretch;
}

.faq-chip {
  display: inline-flex;
  border-radius: 999px;
  padding: 0.25rem 0.8rem;
  background: var(--accent-green20);
  color: var(--accent-green);
  font-size: 0.78rem;
  font-weight: 700;
}

.faq-hero h1 {
  margin: 0.6rem 0 0;
  font-size: 1.95rem;
  color: var(--ink-900);
  line-height: 1.3;
}

.faq-hero p {
  margin: 0.65rem 0 0.95rem;
  line-height: 1.85;
  max-width: 52ch;
}

.faq-meta {
  display: grid;
  gap: 0.55rem;
}

.faq-meta article {
  border-radius: 16px;
  padding: 0.9rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.07);
}

.faq-meta strong {
  display: block;
  font-size: 1.25rem;
  color: var(--ink-900);
}

.faq-meta small {
  color: var(--text-muted);
}

.faq-groups {
  display: grid;
  gap: 0.8rem;
}

.faq-category {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
}

.category-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.7rem;
}

.category-head h2 {
  margin: 0;
  font-size: 1.1rem;
}

.category-head small {
  color: var(--text-muted);
}

.faq-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.55rem;
}

.faq-row {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.25);
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.88);
  overflow: hidden;
}

.faq-trigger {
  width: 100%;
  border: 0;
  background: transparent;
  font-family: inherit;
  text-align: right;
  color: var(--text-primary);
  padding: 0.85rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.faq-title-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.faq-icon {
  font-size: 1rem;
  line-height: 1;
}

.faq-trigger strong {
  font-size: 0.9rem;
  line-height: 1.7;
}

.faq-trigger span {
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  color: var(--accent-green);
  font-size: 1rem;
  transition: transform 0.25s ease;
}

.faq-trigger span.open {
  transform: rotate(45deg);
}

.faq-answer-wrap {
  padding: 0 0.85rem 0.85rem;
}

.faq-image {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 10px;
  margin-bottom: 0.55rem;
}

.faq-summary {
  margin: 0 0 0.45rem;
  font-size: 0.82rem;
  line-height: 1.8;
}

.faq-answer {
  margin: 0;
  line-height: 1.85;
}

.empty-state {
  text-align: center;
}

.faq-drop-enter-active,
.faq-drop-leave-active {
  transition: all 0.24s ease;
}

.faq-drop-enter-from,
.faq-drop-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 980px) {
  .faq-container {
    width: min(760px, calc(100% - 1rem));
  }

  .faq-hero {
    grid-template-columns: 1fr;
  }

  .faq-hero h1 {
    font-size: 1.45rem;
  }

  .faq-meta {
    grid-template-columns: 1fr 1fr;
  }

  .faq-grid {
    grid-template-columns: 1fr;
  }
}
</style>
