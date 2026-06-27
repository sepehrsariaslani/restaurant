<template>
  <div class="home-page" dir="rtl">
    <PublicHeader
      v-if="siteComponents.hero_section_variant !== 'cover'"
      :branding="branding"
      :page="'landing'"
      :cart-count="cartCount"
      :header-variant="siteComponents.header_variant"
    />

    <SiteHeaderHero
      v-if="siteComponents.hero_section_variant === 'cover'"
      :branding="branding"
      :cart-count="cartCount"
      :page="'landing'"
      :preview="false"
    />
    <section v-else-if="siteComponents.hero_section_variant === 'slider'" class="home-container section-hero hero-grid hero-grid--top">
      <ScrollReveal>
        <div class="hero-main glass-card">
          <span class="hero-chip">{{ branding.hero_section_cta || 'پیشنهاد ویژه' }}</span>
          <h1>{{ branding.hero_section_title || branding.hero_title }}</h1>
          <p class="muted">{{ branding.hero_section_description || shortHeroSubtitle }}</p>
          <div class="hero-actions">
            <a class="primary-btn" href="/menu">{{ branding.primary_cta_label || 'مشاهده منو' }}</a>
            <a class="secondary-btn" :href="secondaryCta.href">{{ secondaryCta.label }}</a>
          </div>
        </div>
      </ScrollReveal>
      <ScrollReveal :delay="120">
        <HomeHeroSlider :slides="heroSlides" :fallback-items="featured" />
      </ScrollReveal>
    </section>
    <SiteHeroFoodbar
      v-else-if="siteComponents.hero_section_variant === 'foodbar'"
      :items="featured"
      :currency="currency"
      @quick-add="quickAdd"
    />
    <SiteHeroSection
      v-else-if="siteComponents.hero_section_variant === 'fullscreen'"
      :branding="branding"
      :title="branding.hero_section_title"
      :description="branding.hero_section_description"
      :cta="branding.hero_section_cta"
      :hero-image="branding.hero_image"
      :categories="categories"
    />
    <SiteHeroBanner
      v-else-if="siteComponents.hero_section_variant === 'banner'"
      :branding="branding"
      :title="branding.hero_section_title"
      :description="branding.hero_section_description"
      :cta="branding.hero_section_cta"
      :hero-image="branding.hero_image"
    />

    <div id="content" :class="{ 'needs-header-offset': siteComponents.hero_section_variant !== 'fullscreen' && siteComponents.header_variant !== 'hero' }">
      <GlassShell class="home-shell" :title="branding.name" :subtitle="'ارگانیک، تازه، قابل شخصی سازی'">
        <FloatingFoodIcons />

        <section v-if="showInlineHero" class="home-container section-hero hero-grid">
          <ScrollReveal>
            <div class="hero-main glass-card">
              <span class="hero-chip">سفارش تازه‌ترین غذاها</span>
              <h1>{{ branding.hero_title }}</h1>
              <p class="muted">
                {{ shortHeroSubtitle }}
              </p>
              <div class="hero-actions">
                <a class="primary-btn" href="/menu">{{ branding.primary_cta_label || 'مشاهده منو' }}</a>
                <a class="secondary-btn" :href="secondaryCta.href">{{ secondaryCta.label }}</a>
              </div>
              <div class="hero-stats">
                <div class="stat-item">
                  <strong><AnimatedCounter :target="25" suffix=" دقیقه" /></strong>
                  <small>میانگین آماده‌سازی</small>
                </div>
                <div class="stat-item">
                  <strong><AnimatedCounter :target="100" suffix="٪" /></strong>
                  <small>مواد اولیه تازه</small>
                </div>
                <div class="stat-item">
                  <strong><AnimatedCounter :target="5" suffix="/5" /></strong>
                  <small>امکان شخصی‌سازی</small>
                </div>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal :delay="120">
            <HomeHeroSlider :slides="heroSlides" :fallback-items="featured" />
          </ScrollReveal>
        </section>

        <section class="home-container section-categories">
          <ScrollReveal :delay="100">
            <SectionHeader
              eyebrow="دسته‌بندی"
              title="از کدام دسته شروع می‌کنید؟"
              subtitle="یک دسته را باز کنید، چند آیتم محبوب را ببینید یا مستقیم وارد منوی کامل شوید."
              variant="compact"
            />
          </ScrollReveal>
          <ScrollReveal :delay="160">
            <CategoryExpandableGrid :categories="categories" :currency="currency" @quick-add="quickAdd" />
          </ScrollReveal>
        </section>

        <section class="home-container section-featured featured-wrap" v-if="featured.length">
          <ScrollReveal :delay="100">
            <SectionHeader
              eyebrow="پرفروش‌ترین‌ها"
              title="محبوب‌ترین انتخاب‌های امروز"
              subtitle="آیتم‌هایی که مشتری‌ها بیشتر انتخاب کرده‌اند؛ آماده برای سفارش سریع."
              variant="compact"
            />
          </ScrollReveal>
          <div class="featured-grid">
            <ScrollReveal
              v-for="(item, idx) in featured"
              :key="item.slug"
              :delay="Math.min(idx, 7) * 70"
            >
              <HomeFeaturedProductCard
                :item="item"
                :currency="currency"
                @quick-add="quickAdd"
              />
            </ScrollReveal>
          </div>
        </section>

        <section class="home-container section-features">
          <ScrollReveal :delay="80">
            <SectionHeader
              eyebrow="چرا ما؟"
              title="سه دلیل برای سفارش راحت‌تر"
              subtitle="تمرکز ما روی سرعت، تازگی و کنترل کامل انتخاب شماست."
              variant="feature"
            />
          </ScrollReveal>
          <div class="features-grid">
            <ScrollReveal v-for="(feature, idx) in featureCards" :key="feature.title" :delay="idx * 80">
              <FeatureCard :icon="feature.icon" :title="feature.title" :description="feature.description" :bg-image="feature.bgImage" />
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

    <Transition name="home-toast">
      <div v-if="toastMessage" class="home-toast" role="status" aria-live="polite">
        {{ toastMessage }}
      </div>
    </Transition>

    <Transition name="cart-pop">
      <a v-if="cartCount > 0" class="home-sticky-cart" href="/cart" aria-label="مشاهده سبد سفارش">
        <span>سبد سفارش</span>
        <strong>{{ cartCount }} آیتم</strong>
      </a>
    </Transition>

    <SiteFooter
      v-if="siteComponents.footer_variant === 'full'"
      :brand-name="branding.name"
      :description="branding.footer_description || branding.hero_subtitle || 'تجربه سفارش آنلاین سریع، تازه و خوش‌طعم با امکان انتخاب از محبوب‌ترین آیتم‌های امروز.'"
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
import { computed, onUnmounted, ref } from 'vue'
import GlassShell from '@/components/GlassShell.vue'
import HomeFeaturedProductCard from '@/components/HomeFeaturedProductCard.vue'
import HomeHeroSlider from '@/components/HomeHeroSlider.vue'
import HomeAboutSection from '@/components/HomeAboutSection.vue'
import HomeFaqSection from '@/components/HomeFaqSection.vue'
import { upsertLine, cartState } from '@/stores/cartStore'
import CategoryExpandableGrid from '@/components/CategoryExpandableGrid.vue'
import FloatingFoodIcons from '@/components/FloatingFoodIcons.vue'
import ScrollReveal from '@/components/ScrollReveal.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import FeatureCard from '@/components/FeatureCard.vue'
import AnimatedCounter from '@/components/AnimatedCounter.vue'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteHeaderHero from '@/components/SiteHeaderHero.vue'
import SiteHeroSection from '@/components/SiteHeroSection.vue'
import SiteHeroBanner from '@/components/SiteHeroBanner.vue'
import SiteHeroFoodbar from '@/components/SiteHeroFoodbar.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import { resolveBranding, resolveSiteComponents } from '@/utils/siteComponents'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const toastMessage = ref('')
let toastTimer = null

const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))

const categories = computed(() => props.boot.categories || [])
const featured = computed(() => props.boot.featured_items || [])
const heroSlides = computed(() => props.boot.hero_slides || [])
const aboutSections = computed(() => props.boot.about_us_sections || [])
const faqItems = computed(() => props.boot.faq_items || [])
const currency = computed(() => props.boot.currency || 'IRR')
const branding = computed(() => resolveBranding(props.boot))
const siteComponents = computed(() => resolveSiteComponents(props.boot))
const showInlineHero = computed(() => !['cover', 'slider', 'banner', 'fullscreen', 'foodbar'].includes(siteComponents.value.hero_section_variant))

const shortHeroSubtitle = computed(() => {
  const text = String(branding.value.hero_subtitle || '').trim()
  if (!text) {
    return 'غذاهای تازه، امکان شخصی‌سازی مواد و سفارش سریع بدون نیاز به ثبت‌نام.'
  }
  return text.length <= 115 ? text : `${text.slice(0, 112).trim()}…`
})

const secondaryCta = computed(() => (
  cartCount.value > 0
    ? { label: `ادامه سفارش (${cartCount.value})`, href: '/cart' }
    : { label: 'مشاهده منو', href: '/menu' }
))

const featureCards = computed(() => [
  {
    icon: 'zap',
    title: 'تحویل سریع',
    description: 'از انتخاب آیتم تا تکمیل سفارش، مسیر خرید کوتاه و روشن طراحی شده است.',
    bgImage: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=60',
  },
  {
    icon: 'sliders',
    title: 'شخصی‌سازی مواد',
    description: 'مواد اولیه و افزودنی‌ها را قبل از افزودن به سبد مطابق سلیقه تنظیم کنید.',
    bgImage: 'https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=600&auto=format&fit=crop&q=60',
  },
  {
    icon: 'leaf',
    title: 'مواد تازه',
    description: 'آیتم‌ها با تمرکز روی تازگی، کیفیت و ترکیب قابل اعتماد آماده می‌شوند.',
    bgImage: 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=600&auto=format&fit=crop&q=60',
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
  showToast(`${item.title || 'آیتم'} به سبد اضافه شد.`)
}

function showToast(message) {
  toastMessage.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 2200)
}

onUnmounted(() => {
  clearTimeout(toastTimer)
})
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

.needs-header-offset {
  padding-top: 5.4rem;
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
  margin-top: 1.25rem;
  margin-bottom: 1.2rem;
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
  grid-template-columns: repeat(3, 1fr);
  gap: 0.7rem;
  margin-top: 1rem;
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.9rem;
  margin-top: 1rem;
  align-items: stretch;
}

.home-toast {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 80;
  max-width: min(340px, calc(100vw - 2rem));
  border-radius: 999px;
  padding: 0.7rem 1rem;
  background: var(--palette-deep-sapphire, #6F4A31);
  color: #fff;
  box-shadow: 0 16px 38px rgb(0 0 0 / 0.18);
  font-size: 0.86rem;
  font-weight: 800;
}

.home-sticky-cart {
  position: fixed;
  left: 1rem;
  bottom: 1rem;
  z-index: 79;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 999px;
  padding: 0.65rem 0.9rem;
  background: var(--accent-gold);
  color: var(--ink-900);
  text-decoration: none;
  box-shadow: 0 16px 38px rgb(0 0 0 / 0.16);
}

.home-sticky-cart span {
  font-size: 0.78rem;
}

.home-sticky-cart strong {
  font-size: 0.84rem;
}

.home-toast-enter-active,
.home-toast-leave-active,
.cart-pop-enter-active,
.cart-pop-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.home-toast-enter-from,
.home-toast-leave-to,
.cart-pop-enter-from,
.cart-pop-leave-to {
  opacity: 0;
  transform: translateY(10px);
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
