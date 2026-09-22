<template>
  <div class="live-site-preview" dir="rtl">
    <PublicHeader
      :branding="branding"
      page="preview"
      :cart-count="3"
      :header-variant="siteComponents.header_variant"
      :preview="true"
    />

    <main class="live-site-preview__content">
      <HomePageRenderer v-if="page === 'home'" :boot="boot" />
      <AboutUsPage v-else-if="page === 'about'" :boot="boot" />
      <FaqPage v-else-if="page === 'faq'" :boot="boot" />
      <ProductGroupsPage v-else-if="page === 'product_groups'" :boot="boot" />
      <section v-else-if="page === 'product'" class="live-site-preview__product-page">
        <div class="live-site-preview__product-card">
          <MenuItemCard :item="previewItem" :card-variant="siteComponents.card_variant" currency="TOMAN" />
        </div>
      </section>
      <HomePageRenderer v-else :boot="boot" />
    </main>

    <SiteFooter
      v-if="siteComponents.footer_variant === 'full'"
      v-bind="footerProps"
    />
    <SiteFooterMinimal
      v-else-if="siteComponents.footer_variant === 'minimal'"
      :brand-name="branding.name"
      :copyright="branding.footer_copyright"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AboutUsPage from '@/pages/AboutUsPage.vue'
import FaqPage from '@/pages/FaqPage.vue'
import ProductGroupsPage from '@/pages/ProductGroupsPage.vue'
import HomePageRenderer from '@/components/blocks/HomePageRenderer.vue'
import MenuItemCard from '@/components/MenuItemCard.vue'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import { resolveBranding, resolveSiteComponents } from '@/utils/siteComponents'

const props = defineProps({
  page: { type: String, default: 'home' },
  boot: { type: Object, default: () => ({}) },
})

const branding = computed(() => resolveBranding(props.boot))
const siteComponents = computed(() => resolveSiteComponents(props.boot))
const previewItem = computed(() => {
  const item = props.boot?.preview_item || props.boot?.featured_items?.[0] || props.boot?.best_seller_items?.[0] || {}
  return {
    title: item.title || 'پیتزا پپرونی',
    short_desc: item.short_desc || 'پیتزا با پپرونی تازه و پنیر موزارلا',
    category_title: item.category_title || 'غذای اصلی',
    base_price: Number(item.base_price || 280000),
    image: item.image || 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=60',
    slug: item.slug || 'sample-item',
    tags: item.tags || ['پرفروش'],
  }
})

const footerProps = computed(() => ({
  brandName: branding.value.name,
  description: branding.value.footer_description || branding.value.hero_subtitle,
  phone: branding.value.footer_phone,
  email: branding.value.footer_email,
  address: branding.value.footer_address,
  instagram: branding.value.footer_instagram,
  telegram: branding.value.footer_telegram,
  copyright: branding.value.footer_copyright,
}))
</script>

<style scoped>
.live-site-preview {
  min-height: 100%;
  overflow: hidden;
  background: var(--bg-soft, #f7f5f2);
}

.live-site-preview__content {
  min-width: 0;
}

.live-site-preview__product-page {
  display: grid;
  place-items: center;
  padding: 1rem;
  min-height: 420px;
}

.live-site-preview__product-card {
  width: min(100%, 360px);
}

.live-site-preview :deep(.site-footer),
.live-site-preview :deep(.site-footer-minimal) {
  margin-top: 1rem;
}
</style>
