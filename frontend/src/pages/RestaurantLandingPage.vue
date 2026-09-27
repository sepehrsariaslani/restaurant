<template>
  <div class="home-page" :class="{ 'home-page--v2': page === 'homev2' }" dir="rtl">
    <div v-if="!previewMode" class="desktop-public-header">
      <PublicHeader
        :branding="branding"
        :page="'landing'"
        :cart-count="cartCount"
        :header-variant="siteComponents.header_variant"
      />
    </div>
    <div v-else class="home-preview-chrome">
      <div class="home-preview-chrome__inner">
        <div class="home-preview-brand">
          <span class="home-preview-brand__mark">{{ previewBrandInitial }}</span>
          <div class="home-preview-brand__copy">
            <strong>{{ branding.name }}</strong>
            <small>{{ branding.tagline || 'پیش‌نمایش صفحه اصلی' }}</small>
          </div>
        </div>
        <span class="home-preview-badge">پیش‌نمایش صفحه اصلی</span>
      </div>
    </div>

    <div id="content" class="home-content" :class="{ 'needs-header-offset': !previewMode }">
      <div v-if="!previewMode" class="home-shortcuts" aria-label="دسترسی سریع سفارش">
        <button type="button" class="home-shortcuts__search" @click="openSearch"><Search :size="20" aria-hidden="true" /><span>چی میل دارید؟ جستجو در منو</span></button>
        <a class="home-shortcuts__method" href="/order/type"><Bike :size="19" aria-hidden="true" /><span>روش دریافت</span></a>
        <a v-if="cartCount" class="home-shortcuts__cart" href="/cart">سبد من <span>{{ cartCount.toLocaleString('fa-IR') }}</span></a>
      </div>
      <HomePageRenderer :boot="boot" :page="page" @quick-add="quickAdd" />
      <BlogHighlights v-if="!previewMode" />
    </div>

    <CartActionFeedback :message="toastMessage" />
    <MenuQuickAddSheet
      :open="Boolean(previewItem)"
      :item="previewItem"
      :currency="boot.currency || 'IRR'"
      :branch="cartState.orderContext.branch || ''"
      @close="previewItem = null"
      @confirm="confirmQuickAdd"
    />

    <SiteFooter
      v-if="!previewMode && siteComponents.footer_variant === 'full'"
      :brand-name="branding.name"
      :description="branding.footer_description || branding.hero_subtitle || '\u062a\u062c\u0631\u0628\u0647 \u0633\u0641\u0627\u0631\u0634 \u0622\u0646\u0644\u0627\u06cc\u0646 \u0633\u0631\u06cc\u0639\u060c \u062a\u0627\u0632\u0647 \u0648 \u062e\u0648\u0634\u200c\u0637\u0639\u0645.'"
      :phone="branding.footer_phone"
      :email="branding.footer_email"
      :address="branding.footer_address"
      :instagram="branding.footer_instagram"
      :telegram="branding.footer_telegram"
      :copyright="branding.footer_copyright"
    />
    <SiteFooterMinimal
      v-else-if="!previewMode && siteComponents.footer_variant === 'minimal'"
      :brand-name="branding.name"
      :copyright="branding.footer_copyright"
    />
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { Bike, Search } from 'lucide-vue-next'
import { upsertLine, cartState } from '@/stores/cartStore'
import PublicHeader from '@/components/PublicHeader.vue'
import CartActionFeedback from '@/components/customer/CartActionFeedback.vue'
import MenuQuickAddSheet from '@/components/MenuQuickAddSheet.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import HomePageRenderer from '@/components/blocks/HomePageRenderer.vue'
import BlogHighlights from '@/components/blog/BlogHighlights.vue'
import { resolveBranding, resolveSiteComponents } from '@/utils/siteComponents'
import { useSearchModal } from '@/composables/useSearchModal'
const { openSearch } = useSearchModal()

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
  previewMode: {
    type: Boolean,
    default: false,
  },
  page: {
    type: String,
    default: 'home',
  },
})

const toastMessage = ref('')
const previewItem = ref(null)
let toastTimer = null

const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))

const branding = computed(() => resolveBranding(props.boot))
const siteComponents = computed(() => resolveSiteComponents(props.boot))
const previewBrandInitial = computed(() => String(branding.value?.name || 'V').trim().charAt(0) || 'V')

function quickAdd(item) {
  if (props.previewMode) return
  if (!item) return
  previewItem.value = item
}

function confirmQuickAdd(payload) {
  upsertLine(payload)
  showToast(`${payload.item_title || 'آیتم'} به سبد اضافه شد.`)
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

.desktop-public-header { display: contents; }

.home-preview-chrome {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgb(247 245 242 / 0.94);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgb(0 0 0 / 0.06);
}

.home-preview-chrome__inner {
  width: min(1160px, calc(100% - 2rem));
  margin: 0 auto;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.home-preview-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
}

.home-preview-brand__mark {
  width: 2rem;
  height: 2rem;
  border-radius: 12px;
  background: var(--ds-color-action-primary);
  color: var(--ds-color-action-primary-foreground, #fff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 900;
  flex-shrink: 0;
}

.home-preview-brand__copy {
  min-width: 0;
}

.home-preview-brand__copy strong,
.home-preview-brand__copy small {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.home-preview-brand__copy strong {
  font-size: 0.9rem;
  color: var(--ink-900, #1c1411);
}

.home-preview-brand__copy small {
  font-size: 0.74rem;
  color: var(--ink-700, #5b5248);
}

.home-preview-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0 0.85rem;
  border-radius: 999px;
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
  font-size: 0.76rem;
  font-weight: 800;
}

.home-content {
  padding-block: clamp(1.25rem, 3vw, 2.5rem);
  background: var(--ds-color-bg-page, var(--bg-soft));
}

.home-shortcuts {
  width: min(1160px, calc(100% - 2rem));
  margin: 0 auto 1rem;
  display: flex;
  gap: .6rem;
  align-items: center;
}
.home-shortcuts :is(button, a) {
  min-height: 48px;
  border: 1px solid var(--ds-color-border);
  border-radius: 15px;
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: .55rem;
  padding: .6rem .9rem;
  font: inherit;
  font-size: .84rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}
.home-shortcuts__search { flex: 1; justify-content: flex-start !important; color: var(--ds-color-text-muted) !important; }
.home-shortcuts__method { white-space: nowrap; }
.home-shortcuts__cart { white-space: nowrap; background: var(--ds-color-action-accent-soft, #fff1e5) !important; }
.home-shortcuts__cart span { color: var(--ds-color-action-accent); }
.home-shortcuts :is(button, a):focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
@media (min-width: 921px) { .home-shortcuts { display: none; } }
@media (max-width: 420px) {
  .home-shortcuts { width: calc(100% - 2rem); gap: .45rem; }
  .home-shortcuts :is(button, a) { padding-inline: .65rem; }
  .home-shortcuts__cart { display: none !important; }
}

.home-page--v2 {
  color: var(--ds-color-text-primary);
  background: var(--ds-color-bg-page);
}

:global(.home-page--v2 .home-content) {
  padding-block: clamp(1rem, 3vw, 2.4rem) clamp(2.5rem, 5vw, 4.5rem);
  background: var(--ds-color-bg-page);
}

.needs-header-offset {
  padding-top: 5.4rem;
}

@media (max-width: 920px) {
  .needs-header-offset { padding-top: 0; }
  .desktop-public-header { display: none; }
}

@media (max-width: 640px) {
  .home-preview-chrome__inner {
    min-height: 54px;
  }

  .home-preview-badge {
    padding: 0 0.7rem;
    font-size: 0.71rem;
  }
}
</style>
