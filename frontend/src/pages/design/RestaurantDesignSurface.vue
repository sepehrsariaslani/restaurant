<template>
  <div ref="surface" class="design-surface" dir="rtl" @click.capture="guardAction" @submit.capture.prevent.stop @input.capture="guardInput" @change.capture="guardInput" @keydown.capture="guardKey">
    <p v-if="error" class="design-surface__message" role="alert">{{ error }}</p>
    <RestaurantApp v-else-if="preview && nativePreviewReady" :key="nativePage" />
    <template v-else-if="ready">
      <div @click="selectChrome('visual')">
        <PublicHeader :branding="branding" :header-variant="components.header_variant" :preview="preview" page="landing" />
      </div>
      <main class="design-surface__content">
        <BlockRenderer v-for="block in blocks" :key="block.id" :block="block" :boot="boot" />
        <p v-if="preview && !blocks.length" class="design-surface__message">برای شروع طراحی، یک کامپوننت به صفحه اضافه کنید.</p>
        <div v-if="preview && isWorkflow" class="design-surface__workflow" @click="selectChrome('visual')">
          <strong>{{ pageTitle }}</strong>
          <p>این قسمت، جریان اصلی {{ pageTitle }} است. محتوا و سکشن‌های بالا و ظاهر مشترک سایت از محیط طراحی تنظیم می‌شوند.</p>
          <p>برای دیدن داده‌ها و فرم عملیاتی، از «نمایش صفحهٔ مشتری» در تنظیمات صفحه استفاده کنید.</p>
        </div>
      </main>
      <div @click="selectChrome('content')">
        <SiteFooter v-if="components.footer_variant === 'full'" :brand-name="branding.name" :description="branding.footer_description || branding.hero_subtitle" :phone="branding.footer_phone" :email="branding.footer_email" :address="branding.footer_address" :instagram="branding.footer_instagram" :telegram="branding.footer_telegram" :copyright="branding.footer_copyright" />
        <SiteFooterMinimal v-else-if="components.footer_variant === 'minimal'" :brand-name="branding.name" :copyright="branding.footer_copyright" />
      </div>
      <MobileBottomNav page="landing" :cart-count="0" />
    </template>
  </div>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, onUnmounted, provide, reactive, ref } from 'vue'
import RestaurantApp from '@/App.vue'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import MobileBottomNav from '@/components/MobileBottomNav.vue'
import BlockRenderer from '@/components/blocks/BlockRenderer.vue'
import { BLOCK_TYPE_LIST, normalizePageBuilderKey } from '@/utils/blockRegistry'
import { applyThemeSettings } from '@/utils/themeSettings'
import { resolveBranding, resolveSiteComponents } from '@/utils/siteComponents'
import { callMethodByPath, getMenuBoot } from '@/utils/api'
const props = defineProps({ preview: Boolean })
const surface = ref(null)
const ready = ref(false)
const error = ref('')
const boot = ref(window._BOOT || {})
const blocks = ref([])
const selectedId = ref('')
const editing = ref(true)
const page = ref('home')
const pageTitle = ref('')
const publicUrl = ref('')
const nativePage = ref('')
const nativePreviewReady = ref(false)
const appBoot = reactive({})
let originalStorageDescriptor
let originalPageDescriptor
let originalBootDescriptor
let originalPreviewDescriptor
let previewStorage
const branding = computed(() => resolveBranding(boot.value))
const components = computed(() => resolveSiteComponents(boot.value))
const isWorkflow = computed(() => !['home', 'homev2', 'about', 'faq', 'product_groups'].includes(page.value) && !page.value.startsWith('custom:'))
const channel = new URLSearchParams(location.search).get('channel') || ''
let parentOrigin = ''
try { const referrer = new URL(document.referrer); if (referrer.hostname === location.hostname) parentOrigin = referrer.origin } catch (_) {}
let observer
let heightFrame
function send(type, detail = {}) {
  if (props.preview && parentOrigin && window.parent !== window) window.parent.postMessage({ source: 'restaurant-design-preview', channel, type, ...detail }, parentOrigin)
}
provide('restaurant-design-session', props.preview ? {
  selectedId, editing, isLocked: id => isBlockLocked(id),
  select: id => { selectedId.value = id; send('select', { id }) },
  update: (id, key, value) => send('update', { id, key, value }),
  siteUpdate: (collection, index, key, value, id) => send('site-update', { collection, index, key, value, id }),
} : null)
function isBlockLocked(id, rows = blocks.value, inherited = false) {
  for (const block of rows || []) {
    const locked = inherited || Boolean(block.locked)
    if (block.id === id) return locked
    const nested = isBlockLocked(id, block.children, locked)
    if (nested) return true
  }
  return false
}
function selectChrome(panel) { if (props.preview && editing.value) send('panel', { panel }) }
function guardInput(event) {
  if (!props.preview || event.target.isContentEditable) return
  event.preventDefault()
  event.stopPropagation()
}
function guardKey(event) {
  if (!props.preview || event.target.isContentEditable || event.target.closest('input,textarea,select,button,[role="button"]')) return
  if (event.target.closest('a')) {
    event.preventDefault()
    event.stopPropagation()
  }
}
function guardAction(event) {
  if (!props.preview) return
  const block = event.target.closest('[data-design-id]')
  if (block && editing.value) send('select', { id: block.dataset.designId })
  if (event.target.isContentEditable) {
    event.stopPropagation()
    return
  }
  if (block || event.target.closest('a,button,input,select,textarea,[role="button"]')) {
    event.preventDefault()
    event.stopPropagation()
  }
  if (!block && event.target.closest('.app-header, header.site-header, .app-footer, footer.site-footer')) {
    send('panel', { panel: event.target.closest('footer, .app-footer, footer.site-footer') ? 'content' : 'visual' })
  }
}
function receive(event) {
  if (!props.preview || event.origin !== parentOrigin || event.source !== window.parent) return
  const message = event.data
  if (message?.source !== 'accounts-design-studio' || message.channel !== channel) return
  if (message.type === 'focus') {
    const target = Array.from(surface.value?.querySelectorAll('[data-design-id]') || []).find(node => node.dataset.designId === message.id)
    if (target) send('position', { top: target.getBoundingClientRect().top + window.scrollY })
    return
  }
  if (message.type !== 'render' || !message.payload) return
  const data = message.payload
  page.value = data.page || 'home'
  pageTitle.value = data.pageTitle || ''
  publicUrl.value = data.publicUrl || ''
  selectedId.value = data.selectedId || ''
  editing.value = data.editing !== false
  const site = data.site || {}
  const web = { ...(site.web_settings || {}), ...(data.visuals || {}) }
  boot.value = { ...(data.boot || {}), web_settings: web, branding: { ...(data.boot?.branding || {}), ...web, name: web.brand_name || data.boot?.branding?.name, tagline: web.brand_tagline || data.boot?.branding?.tagline }, about_us_sections: site.about_sections || data.boot?.about_us_sections || [], faq_items: site.faq_items || data.boot?.faq_items || [], hero_slides: site.hero_slides || data.boot?.hero_slides || [] }
  blocks.value = (data.blocks || []).filter(block => block.enabled !== false && block.enabled !== 0)
  const pageAliases = { home: 'landing', about: 'about-us', product_groups: 'product-groups', 'order-start': 'order-type', 'customer-table-select': 'customer-table-reservation' }
  nativePage.value = page.value.startsWith('custom:') ? '' : pageAliases[page.value] || page.value
  for (const key of Object.keys(appBoot)) delete appBoot[key]
  const pageLayouts = { ...(boot.value.page_layout || {}) }
  const currentLayout = { blocks: blocks.value }
  const editorPageKey = normalizePageBuilderKey(page.value)
  const nativePageKey = normalizePageBuilderKey(nativePage.value)
  pageLayouts[editorPageKey] = currentLayout
  if (nativePage.value && (nativePageKey !== 'home' || nativePageKey === editorPageKey)) pageLayouts[nativePageKey] = currentLayout
  Object.assign(appBoot, boot.value, { page_layout: pageLayouts })
  window._PAGE = nativePage.value
  window._BOOT = appBoot
  window.__RESTAURANT_DESIGN_STUDIO_PREVIEW = true
  nativePreviewReady.value = Boolean(props.preview && nativePage.value)
  applyThemeSettings(data.theme || boot.value.theme_settings || {})
  ready.value = true
  nextTick(reportHeight)
}
function reportHeight() {
  cancelAnimationFrame(heightFrame)
  heightFrame = requestAnimationFrame(() => send('height', { height: Math.ceil(surface.value?.scrollHeight || 800) }))
}
function keyboard(event) {
  if (event.target.isContentEditable || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return
  if ((event.ctrlKey || event.metaKey) && ['s', 'z', 'y', 'd'].includes(event.key.toLowerCase())) {
    event.preventDefault(); send('shortcut', { key: event.key.toLowerCase(), shift: event.shiftKey })
  } else if (event.key === 'Delete' || event.key === 'Backspace') {
    event.preventDefault(); send('shortcut', { key: 'delete' })
  }
}
function installPreviewStorage() {
  originalStorageDescriptor = Object.getOwnPropertyDescriptor(window, 'localStorage')
  originalPageDescriptor = Object.getOwnPropertyDescriptor(window, '_PAGE')
  originalBootDescriptor = Object.getOwnPropertyDescriptor(window, '_BOOT')
  originalPreviewDescriptor = Object.getOwnPropertyDescriptor(window, '__RESTAURANT_DESIGN_STUDIO_PREVIEW')
  const values = new Map([
    ['restaurant-customer-auth-v1', JSON.stringify({ mobile: '00000000000', customer_token: 'design-preview-invalid-session', customer_name: 'پیش‌نمایش', name: 'پیش‌نمایش' })],
    ['customer_name', 'پیش‌نمایش'],
    ['customer_phone', '00000000000'],
    ['customer_email', 'preview@example.invalid'],
  ])
  const keys = [...values.keys()]
  previewStorage = {
    get length() { return keys.length },
    key(index) { return keys[Number(index)] ?? null },
    getItem(key) { return values.get(String(key)) ?? null },
    setItem() {},
    removeItem() {},
    clear() {},
  }
  if (!originalStorageDescriptor || originalStorageDescriptor.configurable) {
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      enumerable: originalStorageDescriptor?.enumerable ?? true,
      get: () => previewStorage,
    })
  }
}
function restoreWindowProperty(name, descriptor) {
  try {
    if (descriptor) Object.defineProperty(window, name, descriptor)
    else delete window[name]
  } catch (_) {}
}
onMounted(async () => {
  if (props.preview) {
    installPreviewStorage()
    window.addEventListener('message', receive)
    window.addEventListener('keydown', keyboard)
    observer = new ResizeObserver(reportHeight)
    observer.observe(surface.value)
    send('ready', { registry: BLOCK_TYPE_LIST.map(({ type, label, variants, defaultVariant, props: fields, single }) => ({ type, label, variants, defaultVariant, fields, single: Boolean(single) })) })
    return
  }
  try {
    const result = window._DESIGN_PAGE?.page ? window._DESIGN_PAGE : await callMethodByPath('restaurant.page_layout.get_public_design_page', { slug: location.pathname.split('/').filter(Boolean).pop() })
    if (!Object.keys(boot.value).length) boot.value = await getMenuBoot()
    page.value = result.page
    blocks.value = (result.blocks || []).filter(block => block.enabled !== false && block.enabled !== 0)
    document.title = result.metadata?.title || 'صفحهٔ سایت'
    applyThemeSettings(boot.value.theme_settings || {})
    ready.value = true
  } catch (_) { error.value = 'این صفحه منتشر نشده یا در دسترس نیست.' }
})
onBeforeUnmount(() => {
  window.removeEventListener('message', receive)
  window.removeEventListener('keydown', keyboard)
  observer?.disconnect()
  cancelAnimationFrame(heightFrame)
})
onUnmounted(() => {
  if (!props.preview) return
  restoreWindowProperty('localStorage', originalStorageDescriptor)
  restoreWindowProperty('_PAGE', originalPageDescriptor)
  restoreWindowProperty('_BOOT', originalBootDescriptor)
  restoreWindowProperty('__RESTAURANT_DESIGN_STUDIO_PREVIEW', originalPreviewDescriptor)
})
</script>
<style scoped>
.design-surface { min-height: 100vh; background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.design-surface__content { width: 100%; max-width: 1440px; margin-inline: auto; padding: 100px 24px 32px; display: flex; flex-direction: column; gap: 32px; }
.design-surface__message { padding: 3rem 1rem; text-align: center; color: var(--ds-color-text-secondary); }
.design-surface__workflow { padding: 2rem; border: 1px dashed var(--ds-color-border); color: var(--ds-color-text-secondary); background: var(--ds-color-surface); }
.design-surface__workflow p { line-height: 1.9; }
@media (max-width: 767px) { .design-surface__content { padding: 24px 16px 96px; gap: 24px; } }
</style>
