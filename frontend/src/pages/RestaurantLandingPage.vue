<template>
  <div class="home-page" dir="rtl">
    <PublicHeader
      :branding="branding"
      :page="'landing'"
      :cart-count="cartCount"
      :header-variant="siteComponents.header_variant"
    />

    <div id="content" class="home-content needs-header-offset">
      <HomePageRenderer :boot="boot" @quick-add="quickAdd" />
    </div>

    <Transition name="home-toast">
      <div v-if="toastMessage" class="home-toast" role="status" aria-live="polite">
        {{ toastMessage }}
      </div>
    </Transition>

    <Transition name="cart-pop">
      <a v-if="cartCount > 0" class="home-sticky-cart" href="/cart" aria-label="\u0645\u0634\u0627\u0647\u062f\u0647 \u0633\u0628\u062f \u0633\u0641\u0627\u0631\u0634">
        <span>\u0633\u0628\u062f \u0633\u0641\u0627\u0631\u0634</span>
        <strong>{{ cartCount }} \u0622\u06cc\u062a\u0645</strong>
      </a>
    </Transition>

    <SiteFooter
      v-if="siteComponents.footer_variant === 'full'"
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
      v-else-if="siteComponents.footer_variant === 'minimal'"
      :brand-name="branding.name"
      :copyright="branding.footer_copyright"
    />
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { upsertLine, cartState } from '@/stores/cartStore'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import HomePageRenderer from '@/components/blocks/HomePageRenderer.vue'
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

const branding = computed(() => resolveBranding(props.boot))
const siteComponents = computed(() => resolveSiteComponents(props.boot))

function quickAdd(item) {
  if (!item) return
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
  showToast(`${item.title || '\u0622\u06cc\u062a\u0645'} \u0628\u0647 \u0633\u0628\u062f \u0627\u0636\u0627\u0641\u0647 \u0634\u062f.`)
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

.home-content {
  padding-block: clamp(2rem, 6vw, 4rem);
  background: var(--bg-soft, #f7f5f2);
}

.needs-header-offset {
  padding-top: 5.4rem;
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
</style>
