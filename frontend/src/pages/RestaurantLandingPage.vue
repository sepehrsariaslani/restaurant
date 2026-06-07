<template>
  <div class="home-page" dir="rtl">
    <SiteHeaderMinimal
      v-if="siteComponents.header_variant === 'minimal'"
      :branding="branding"
      :cart-count="0"
    />
    <SiteHeader
      v-else
      :branding="branding"
      :cart-count="0"
      :has-hero="siteComponents.hero_section_variant === 'fullscreen'"
      :hero-visible="heroVisible"
    />

    <SiteHeroSection
      v-if="siteComponents.hero_section_variant === 'fullscreen'"
      :branding="branding"
      :title="branding.hero_section_title"
      :description="branding.hero_section_description"
      :cta="branding.hero_section_cta"
      :hero-image="branding.hero_image"
      @visibility-change="heroVisible = $event"
    />
    <SiteHeroBanner
      v-else-if="siteComponents.hero_section_variant === 'banner'"
      :branding="branding"
      :title="branding.hero_section_title"
      :description="branding.hero_section_description"
      :cta="branding.hero_section_cta"
      :hero-image="branding.hero_image"
    />

    <div id="content">
      <GlassShell class="home-shell" :title="branding.name" :subtitle="'ارگانیک، تازه، قابل شخصی سازی'">
        <FloatingFoodIcons />

        <section class="home-container section-hero hero-grid">
          <ScrollReveal>
            <div class="hero-main glass-card">
              <span class="hero-chip">رستوران آنلاین مدرن</span>
              <h1>{{ branding.hero_title }}</h1>
              <p class="muted">
                {{ branding.hero_subtitle }}
              </p>
              <div class="hero-actions">
                <a class="primary-btn" href="/menu">{{ branding.primary_cta_label || 'ورود به منو' }}</a>
                <a class="secondary-btn" href="/cart">مشاهده سبد سفارش</a>
              </div>
              <div class="hero-stats">
                <div class="stat-item">
                  <strong><AnimatedCounter :target="categories.length || 8" suffix="+" /></strong>
                  <small>دسته غذایی</small>
                </div>
                <div class="stat-item">
                  <strong><AnimatedCounter :target="featured.length || 24" suffix="+" /></strong>
                  <small>غذای پرطرفدار</small>
                </div>
                <div class="stat-item">
                  <strong><AnimatedCounter :target="faqItems.length || 12" suffix="+" /></strong>
                  <small>پاسخ سریع</small>
                </div>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal :delay="120">
            <HomeHeroSlider :slides="heroSlides" :fallback-items="featured" />
          </ScrollReveal>
        </section>

        <section class="home-container section-features">
          <ScrollReveal :delay="80">
            <SectionHeader
              eyebrow="چرا ما؟"
              title="تجربه سفارش سریع، جذاب و قابل شخصی‌سازی"
              subtitle="از انتخاب غذا تا پرداخت نهایی، همه چیز برای راحتی کاربر روی موبایل و دسکتاپ بهینه شده است."
            />
          </ScrollReveal>
          <div class="features-grid">
            <ScrollReveal v-for="(feature, idx) in featureCards" :key="feature.title" :delay="idx * 80">
              <FeatureCard :icon="feature.icon" :title="feature.title" :description="feature.description" />
            </ScrollReveal>
          </div>
        </section>

        <section class="home-container section-categories">
          <ScrollReveal :delay="100">
            <SectionHeader eyebrow="دسته‌بندی" title="منوی هوشمند بر اساس سلیقه شما" />
          </ScrollReveal>
          <ScrollReveal :delay="160">
            <CategoryMasonry :categories="categories" />
          </ScrollReveal>
        </section>

        <section class="home-container section-featured featured-wrap" v-if="featured.length">
          <ScrollReveal :delay="100">
            <SectionHeader eyebrow="پرفروش‌ترین‌ها" title="محبوب‌های امروز" subtitle="انتخاب‌های ویژه که بیشترین سفارش را داشته‌اند." />
          </ScrollReveal>
          <div class="featured-grid">
            <ScrollReveal
              v-for="(item, idx) in featured"
              :key="item.slug"
              :delay="Math.min(idx, 7) * 70"
            >
              <MenuItemCard
                :item="item"
                :currency="currency"
                @quick-add="quickAdd"
              />
            </ScrollReveal>
          </div>
        </section>

        <section class="home-container section-about">
          <ScrollReveal :delay="90">
            <HomeAboutSection :sections="aboutSections" />
          </ScrollReveal>
        </section>

        <section class="home-container section-faq">
          <ScrollReveal :delay="90">
            <HomeFaqSection :faqs="faqItems" />
          </ScrollReveal>
        </section>
      </GlassShell>
    </div>

    <SiteFooter
      v-if="siteComponents.footer_variant === 'full'"
      :brand-name="branding.name"
      :description="branding.footer_description"
      :phone="branding.footer_phone"
      :email="branding.footer_email"
      :address="branding.footer_address"
      :instagram="branding.footer_instagram"
      :telegram="branding.footer_telegram"
      :copyright="branding.footer_copyright"
    />
    <SiteFooterMinimal
      v-else-if="siteComponents.footer_variant === 'minimal'"
      :brand-name="branding.name"
      :copyright="branding.footer_copyright"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import GlassShell from '@/components/GlassShell.vue'
import MenuItemCard from '@/components/MenuItemCard.vue'
import HomeHeroSlider from '@/components/HomeHeroSlider.vue'
import HomeAboutSection from '@/components/HomeAboutSection.vue'
import HomeFaqSection from '@/components/HomeFaqSection.vue'
import { upsertLine } from '@/stores/cartStore'
import CategoryMasonry from '@/components/CategoryMasonry.vue'
import FloatingFoodIcons from '@/components/FloatingFoodIcons.vue'
import ScrollReveal from '@/components/ScrollReveal.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import FeatureCard from '@/components/FeatureCard.vue'
import AnimatedCounter from '@/components/AnimatedCounter.vue'
import SiteHeader from '@/components/SiteHeader.vue'
import SiteHeaderMinimal from '@/components/SiteHeaderMinimal.vue'
import SiteHeroSection from '@/components/SiteHeroSection.vue'
import SiteHeroBanner from '@/components/SiteHeroBanner.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const heroVisible = ref(true)

const categories = computed(() => props.boot.categories || [])
const featured = computed(() => props.boot.featured_items || [])
const heroSlides = computed(() => props.boot.hero_slides || [])
const aboutSections = computed(() => props.boot.about_us_sections || [])
const faqItems = computed(() => props.boot.faq_items || [])
const currency = computed(() => props.boot.currency || 'IRR')
const branding = computed(
  () =>
    props.boot.branding || {
      name: 'Veederakht Restaurant',
      hero_title: 'منوی آنلاین با انتخاب کامل مواد داخل هر غذا',
      hero_subtitle:
        'مشتری می‌تواند آیتم‌ها را ببیند، ترکیبات را کم و زیاد کند، و سفارش مهمان را بدون ثبت نام نهایی کند.',
      primary_cta_label: 'ورود به منو',
    },
)

const siteComponents = computed(() => {
  const ws = props.boot.web_settings || props.boot.branding || {}
  const heroEnabled = Number(ws.hero_section_enabled || 0) === 1
  const footerEnabled = Number(ws.footer_enabled ?? 1) !== 0
  return {
    header_variant: String(ws.header_variant || 'classic').trim() || 'classic',
    hero_section_variant: String(ws.hero_section_variant || (heroEnabled ? 'fullscreen' : 'off')).trim() || 'off',
    footer_variant: String(ws.footer_variant || (footerEnabled ? 'full' : 'off')).trim() || 'full',
  }
})

const featureCards = computed(() => [
  {
    icon: '⚡',
    title: 'سفارش سریع',
    description: 'فرآیند سفارش با کمترین کلیک و بیشترین سرعت طراحی شده است.',
  },
  {
    icon: '🧩',
    title: 'شخصی‌سازی کامل',
    description: 'مواد اولیه هر غذا را متناسب با سلیقه خودتان تنظیم کنید.',
  },
  {
    icon: '🍃',
    title: 'مواد تازه',
    description: 'تمرکز اصلی روی کیفیت، تازگی و ترکیب سالم مواد اولیه است.',
  },
  {
    icon: '💬',
    title: 'پشتیبانی شفاف',
    description: 'پاسخ سوالات متداول و مسیر ارتباطی روشن برای مشتریان.',
  },
])

function quickAdd(item) {
  upsertLine({
    item_slug: item.slug,
    item_title: item.title,
    item_image: item.image,
    base_price: Number(item.base_price || 0),
    qty: 1,
    unit_price_preview: Number(item.base_price || 0),
    line_total_preview: Number(item.base_price || 0),
    customization: {
      ingredient_adjustments: [],
      selected_modifiers: [],
    },
  })
  window.location.href = '/cart'
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-height: 100svh;
}

.home-shell {
  --home-surface-rgb: var(--palette-eggshell-rgb);
  --home-soft-rgb: var(--palette-june-bud-rgb);
  --home-primary-rgb: var(--palette-deep-sapphire-rgb);
  --home-accent-rgb: var(--palette-deep-saffron-rgb);
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background: var(--bg-soft);
}

.home-container {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.section-hero {
  margin-bottom: 1.35rem;
}

.section-features {
  margin-bottom: 0;
}

.section-categories {
  margin-top: 0.95rem;
  margin-bottom: 1.3rem;
}

.section-featured {
  margin-bottom: 1.2rem;
}

.section-about {
  margin-bottom: 1.05rem;
}

.section-faq {
  margin-bottom: 1.5rem;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 1rem;
  align-items: stretch;
}

.hero-main {
  border-color: rgb(var(--home-primary-rgb) / 0.2);
  background: rgb(var(--home-surface-rgb) / 0.95);
  box-shadow: 0 16px 34px rgb(var(--home-primary-rgb) / 0.14);
  display: grid;
  align-content: start;
  gap: 0.85rem;
}

.hero-chip {
  display: inline-flex;
  width: max-content;
  border-radius: 999px;
  padding: 0.28rem 0.8rem;
  background: rgb(var(--home-soft-rgb) / 0.32);
  border: 1px solid rgb(var(--home-accent-rgb) / 0.28);
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--ink-900);
}

.hero-main h1 {
  margin: 0;
  font-size: clamp(1.5rem, 3.5vw, 2.4rem);
  line-height: 1.25;
  color: var(--ink-900);
}

.hero-main .muted {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.65;
}

.hero-actions {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.hero-stats {
  display: flex;
  gap: 1.4rem;
  padding-top: 0.5rem;
  border-top: 1px dashed rgb(var(--home-primary-rgb) / 0.16);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.stat-item strong {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--accent-green);
}

.stat-item small {
  font-size: 0.7rem;
  color: var(--ink-700);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.7rem;
  margin-top: 1rem;
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.9rem;
  margin-top: 1rem;
}

@media (max-width: 900px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 580px) {
  .features-grid {
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
}
</style>
