<template>
  <div v-if="hasCustomLayout" class="product-groups-builder" dir="rtl">
    <PageBlocksRenderer page="product_groups" :boot="boot" />
  </div>
  <div v-else class="product-groups-page" dir="rtl">
    <GlassShell class="groups-shell" :title="branding.name" subtitle="انتخاب گروه محصول">
      <section class="groups-hero glass-card">
        <div class="groups-hero__copy">
          <span class="groups-hero__eyebrow">منوی دسته‌بندی‌شده</span>
          <h1>{{ titleText }}</h1>
          <p class="muted">{{ subtitleText }}</p>
        </div>
        <a class="primary-btn" href="/menu">مشاهده همه منو</a>
      </section>

      <section v-if="groups.length" class="groups-grid">
        <ProductGroupCard
          v-for="group in groups"
          :key="group.slug || group.name"
          :group="group"
        />
      </section>

      <section v-else class="groups-empty glass-card">
        <p class="groups-empty__title">هنوز گروه محصولی برای نمایش ثبت نشده است.</p>
        <p class="muted">بعد از ساخت دسته‌ها در مدیریت، اینجا به‌صورت خودکار نمایش داده می‌شوند.</p>
        <a class="secondary-btn" href="/menu">رفتن به منوی کامل</a>
      </section>
    </GlassShell>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PageBlocksRenderer from '@/components/blocks/PageBlocksRenderer.vue'
import GlassShell from '@/components/GlassShell.vue'
import ProductGroupCard from '@/components/ProductGroupCard.vue'
import { hasStoredPageLayout } from '@/utils/pageLayout'
import { resolveBranding } from '@/utils/siteComponents'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const branding = computed(() => resolveBranding(props.boot))
const hasCustomLayout = computed(() => hasStoredPageLayout(props.boot, 'product_groups'))

const groups = computed(() => {
  const rows = Array.isArray(props.boot?.categories) ? props.boot.categories : []
  return rows
    .filter((row) => String(row?.slug || '').trim())
    .map((row) => ({
      name: row.name,
      slug: row.slug,
      title: row.title || row.name || 'گروه محصول',
      image: row.image || '',
      item_count: Number(row.item_count || 0),
      description: String(row.restaurant_description || row.description || '').trim(),
    }))
})

const titleText = computed(() => branding.value?.hero_title || 'گروه محصولات را انتخاب کنید')
const subtitleText = computed(() => branding.value?.hero_subtitle || 'مشتری روی هر گروه بزند و مستقیم وارد منوی همان گروه شود.')
</script>

<style scoped>
.product-groups-builder {
  padding-block: clamp(1.5rem, 4vw, 3rem);
  background: var(--bg-soft, #f7f5f2);
}

.product-groups-page {
  padding: 0 0 2rem;
}

.groups-shell {
  display: grid;
  gap: 1rem;
}

.groups-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.2rem;
  border-radius: 24px;
}

.groups-hero__copy {
  display: grid;
  gap: 0.45rem;
}

.groups-hero__eyebrow {
  color: var(--accent-green, #2f855a);
  font-size: 0.78rem;
  font-weight: 800;
}

.groups-hero h1 {
  margin: 0;
  font-size: clamp(1.35rem, 2vw, 2rem);
  color: var(--text-primary, #0f172a);
}

.groups-hero p {
  margin: 0;
  max-width: 56ch;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.groups-empty {
  display: grid;
  gap: 0.75rem;
  justify-items: start;
  padding: 1.3rem;
  border-radius: 22px;
}

.groups-empty__title {
  margin: 0;
  color: var(--text-primary, #0f172a);
  font-size: 1rem;
  font-weight: 900;
}

@media (max-width: 720px) {
  .groups-hero {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
