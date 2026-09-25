<template>
  <nav class="mobile-bottom-nav" dir="rtl" aria-label="ناوبری اصلی">
    <a href="/" class="nav-item" :class="{ active: page === 'landing' || page === 'homev2' }" :aria-current="page === 'landing' || page === 'homev2' ? 'page' : undefined">
      <Home class="nav-icon" :size="20" />
      <small>خانه</small>
    </a>

    <a href="/menu" class="nav-item" :class="{ active: page === 'menu' || page === 'item' || page === 'search' || page === 'product-groups' }" :aria-current="page === 'menu' || page === 'item' || page === 'search' || page === 'product-groups' ? 'page' : undefined">
      <List class="nav-icon" :size="20" />
      <small>منو</small>
    </a>

    <a href="/cart" class="nav-item" :class="{ active: page === 'cart' }" :aria-current="page === 'cart' ? 'page' : undefined" :aria-label="cartCount > 0 ? `سبد سفارش، ${cartCount.toLocaleString('fa-IR')} آیتم` : 'سبد سفارش'">
      <ShoppingCart class="nav-icon" :size="20" />
      <small>سبد</small>
      <i v-if="cartCount > 0" aria-hidden="true">{{ cartCount.toLocaleString('fa-IR') }}</i>
    </a>

    <a :href="accountHref" class="nav-item" :class="{ active: isCustomerAccountActive }" :aria-current="isCustomerAccountActive ? 'page' : undefined">
      <UserRound class="nav-icon" :size="20" />
      <small>حساب</small>
    </a>

    <button
      type="button"
      class="nav-item nav-more"
      :class="{ active: moreOpen }"
      ref="moreTriggerRef"
      :aria-expanded="moreOpen"
      aria-controls="mobile-more-sheet"
      @click="toggleMore"
    >
      <MoreHorizontal class="nav-icon" :size="20" />
      <small>بیشتر</small>
    </button>
  </nav>

  <Teleport to="body">
    <Transition name="mobile-more">
      <div v-if="moreOpen" class="mobile-more-layer" @click.self="closeMore">
        <div class="mobile-more-backdrop" aria-hidden="true" @click="closeMore"></div>
        <section id="mobile-more-sheet" ref="moreDialogRef" class="mobile-more-sheet" dir="rtl" role="dialog" aria-modal="true" aria-labelledby="mobile-more-title">
          <div class="mobile-more-grabber" aria-hidden="true"></div>
          <header class="mobile-more-head">
            <div>
              <small>دسترسی سریع</small>
              <h2 id="mobile-more-title">بیشتر</h2>
            </div>
            <button ref="moreCloseRef" class="mobile-more-close" type="button" aria-label="بستن" @click="closeMore"><X :size="20" /></button>
          </header>
          <nav class="mobile-more-links" aria-label="صفحه‌های بیشتر">
            <a v-for="link in moreLinks" :key="link.href" :href="link.href" class="mobile-more-link" @click="closeMore">
              <span class="mobile-more-icon"><component :is="link.icon" :size="19" aria-hidden="true" /></span>
              <span><strong>{{ link.label }}</strong><small>{{ link.hint }}</small></span>
              <ChevronLeft class="mobile-more-chevron" :size="17" aria-hidden="true" />
            </a>
            <ShareWebsiteButton
              class="mobile-more-link mobile-more-link--share"
              appearance="menu"
              label="اشتراک‌گذاری سایت"
              title="ویدرخت"
              :url="siteShareUrl"
              @shared="closeMore"
              @copied="closeMore"
              @error="closeMore"
            >
              <template #default>
                <span class="mobile-more-icon"><Share2 :size="19" aria-hidden="true" /></span>
                <span><strong>اشتراک‌گذاری سایت</strong><small>معرفی سایت به دوستان</small></span>
                <ChevronLeft class="mobile-more-chevron" :size="17" aria-hidden="true" />
              </template>
            </ShareWebsiteButton>
          </nav>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Bike, ChevronLeft, CircleHelp, Clock3, Home, List, MapPin, MoreHorizontal, Search, Share2, ShoppingCart, Store, UserRound, X } from 'lucide-vue-next'
import { customerAccountHref, hasCustomerSession } from '@/utils/customerAuth'
import ShareWebsiteButton from '@/components/customer/ShareWebsiteButton.vue'

const props = defineProps({
  page: { type: String, default: 'landing' },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
})

const customerAccountPages = new Set([
  'customer-dashboard',
  'customer-profile',
  'customer-addresses',
  'customer-vehicles',
  'customer-branches',
  'customer-orders',
  'customer-order-detail',
  'customer-delivery',
  'customer-table-reservation',
  'customer-table-select',
  'customer-login',
])

const isCustomerAccountActive = computed(() => customerAccountPages.has(props.page))
const siteShareUrl = window.location.origin
const moreOpen = ref(false)
const isSignedIn = ref(hasCustomerSession())
const moreTriggerRef = ref(null)
const moreCloseRef = ref(null)
const moreDialogRef = ref(null)
let bodyOverflowBeforeSheet = ''
const accountHref = computed(() => isSignedIn.value ? '/customer/dashboard' : customerAccountHref('/customer/dashboard'))
const moreLinks = computed(() => [
  { href: '/search', label: 'جستجو', hint: 'پیدا کردن غذا در منو', icon: Search },
  { href: '/order/type', label: 'شروع سفارش', hint: 'نوع سفارش و مقصد را انتخاب کنید', icon: Bike },
  { href: customerAccountHref('/customer/orders'), label: 'سفارش‌های من', hint: 'پیگیری و خریدهای قبلی', icon: Clock3 },
  { href: '/customer/branches', label: 'شعبه‌ها', hint: 'نشانی و ساعت کار', icon: Store },
  { href: '/table-reservation', label: 'رزرو میز', hint: 'انتخاب زمان و میز', icon: MapPin },
  { href: customerAccountHref('/customer/profile'), label: isSignedIn.value ? 'پروفایل' : 'ورود / ثبت‌نام', hint: isSignedIn.value ? 'اطلاعات حساب کاربری' : 'ورود با شماره موبایل', icon: UserRound },
  { href: '/faq', label: 'راهنما', hint: 'پاسخ به پرسش‌های پرتکرار', icon: CircleHelp },
])

function toggleMore() {
  moreOpen.value = !moreOpen.value
}

function closeMore() {
  moreOpen.value = false
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    closeMore()
    return
  }
  if (event.key !== 'Tab' || !moreDialogRef.value) return
  const focusable = [...moreDialogRef.value.querySelectorAll('a[href], button:not([disabled])')]
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function onStorage(event) {
  if (!event.key || event.key === 'restaurant-customer-auth-v1' || event.key === 'customer_phone') {
    isSignedIn.value = hasCustomerSession()
  }
}

watch(moreOpen, async (isOpen) => {
  if (isOpen) {
    bodyOverflowBeforeSheet = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeydown)
    await nextTick()
    moreCloseRef.value?.focus()
  } else {
    window.removeEventListener('keydown', onKeydown)
    document.body.style.overflow = bodyOverflowBeforeSheet
    await nextTick()
    moreTriggerRef.value?.focus()
  }
})

window.addEventListener('storage', onStorage)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('storage', onStorage)
  document.body.style.overflow = bodyOverflowBeforeSheet
})
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: calc(0.62rem + env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 0.8rem));
  border-radius: 24px;
  background: var(--ds-color-surface-raised, #fff);
  background: color-mix(in srgb, var(--ds-color-surface-raised, #fff) 96%, transparent);
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.12));
  box-shadow: 0 10px 24px rgba(15,23,42,0.1);
  padding: 0.34rem;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.12rem;
  z-index: 115;
  backdrop-filter: blur(16px);
}

.nav-item {
  min-height: 52px;
  border: 0;
  border-radius: 16px;
  color: var(--ds-color-text-muted, var(--text-muted, #846b58));
  background: transparent;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.3rem;
  position: relative;
  text-decoration: none;
  transition: background 0.2s, color 0.2s, transform 0.15s;
  font-family: inherit;
  cursor: pointer;
}

.nav-icon {
  width: 19px;
  height: 19px;
}

.nav-item small {
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.1;
}

.nav-item.active {
  background: var(--ds-color-action-primary-soft, var(--accent-green20, rgba(111,74,49,0.09)));
  color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
}

.nav-more {
  font-family: inherit;
}

.nav-item:active {
  transform: scale(0.96);
}

.nav-search {
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse, #fff));
  transform: translateY(-0.36rem);
}

.search-orb {
  width: 44px;
  height: 44px;
  border-radius: 18px;
  background: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse, #fff));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--ds-shadow-md, 0 10px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.20));
}

.nav-search small {
  color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  margin-top: -0.1rem;
}

.nav-search.active .search-orb {
  background: var(--ds-color-action-primary, var(--accent-green));
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse, #fff));
}

.nav-item i {
  position: absolute;
  top: 0;
  left: 30%;
  transform: translateX(-50%);
  min-width: 0.95rem;
  height: 0.95rem;
  padding: 0 0.2rem;
  border-radius: 999px;
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground);
  font-style: normal;
  font-size: 0.72rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.mobile-bottom-nav a:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
  position: relative;
  z-index: 1;
}

.mobile-bottom-nav button:focus-visible,
.mobile-more-sheet :is(a, button):focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
}

.mobile-more-layer {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.mobile-more-backdrop {
  position: absolute;
  inset: 0;
  border: 0;
  padding: 0;
  background: rgb(20 19 17 / 0.42);
  backdrop-filter: blur(3px);
}

.mobile-more-sheet {
  position: relative;
  width: min(560px, 100%);
  max-height: min(78dvh, 680px);
  overflow: auto;
  padding: 0.55rem 1rem calc(1.1rem + env(safe-area-inset-bottom));
  border: 1px solid var(--ds-color-border);
  border-bottom: 0;
  border-radius: 26px 26px 0 0;
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-text-primary);
  box-shadow: 0 -18px 50px rgb(29 22 13 / 0.22);
}

.mobile-more-grabber {
  width: 38px;
  height: 4px;
  margin: 0 auto 0.8rem;
  border-radius: 99px;
  background: var(--ds-color-border);
}

.mobile-more-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.8rem;
}

.mobile-more-head small,
.mobile-more-link small {
  display: block;
  color: var(--ds-color-text-muted);
  font-size: 0.72rem;
}

.mobile-more-head h2 {
  margin: 0.1rem 0 0;
  font-size: 1.12rem;
}

.mobile-more-close {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ds-color-border);
  border-radius: 14px;
  background: var(--ds-color-surface);
  color: var(--ds-color-text-primary);
}

.mobile-more-links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.mobile-more-link {
  min-height: 72px;
  min-width: 0;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem;
  border: 1px solid var(--ds-color-border);
  border-radius: 17px;
  background: var(--ds-color-surface);
  color: var(--ds-color-text-primary);
  text-decoration: none;
}

.mobile-more-link--share { grid-column: 1 / -1; }

.mobile-more-link strong {
  display: block;
  overflow: hidden;
  font-size: 0.79rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-more-link small {
  margin-top: 0.15rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-more-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
}

.mobile-more-chevron {
  color: var(--ds-color-text-muted);
}

.mobile-more-enter-active,
.mobile-more-leave-active {
  transition: opacity 0.2s ease;
}

.mobile-more-enter-active .mobile-more-sheet,
.mobile-more-leave-active .mobile-more-sheet {
  transition: transform 0.22s ease;
}

.mobile-more-enter-from,
.mobile-more-leave-to {
  opacity: 0;
}

.mobile-more-enter-from .mobile-more-sheet,
.mobile-more-leave-to .mobile-more-sheet {
  transform: translateY(100%);
}

@media (max-width: 370px) {
  .mobile-bottom-nav { width: calc(100% - 0.5rem); padding: 0.28rem; }
  .nav-item small { font-size: 0.68rem; }
  .mobile-more-links { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-more-enter-active,
  .mobile-more-leave-active,
  .mobile-more-enter-active .mobile-more-sheet,
  .mobile-more-leave-active .mobile-more-sheet { transition: none; }
}

@media (min-width: 920px) {
  .mobile-bottom-nav {
    display: none;
  }
}
</style>
