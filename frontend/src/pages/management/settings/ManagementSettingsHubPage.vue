<template>
  <section class="settings-hub" dir="rtl" aria-label="مرکز تنظیمات مدیریت">
    <nav class="settings-hub__tabs" aria-label="دسته‌های تنظیمات">
      <a
        v-for="tab in tabs"
        :key="tab.key"
        class="settings-hub__tab"
        :class="{ 'is-active': routeState.tab === tab.key }"
        :href="tab.href"
        :aria-current="routeState.tab === tab.key ? 'page' : undefined"
      >
        <component :is="tab.icon" :size="17" aria-hidden="true" />
        <span>{{ tab.label }}</span>
      </a>
    </nav>

    <nav v-if="subviews.length" class="settings-hub__subtabs" :aria-label="subviewLabel">
      <a
        v-for="view in subviews"
        :key="view.key"
        class="settings-hub__subtab"
        :class="{ 'is-active': routeState.view === view.key }"
        :href="view.href"
        :aria-current="routeState.view === view.key ? 'page' : undefined"
      >
        {{ view.label }}
      </a>
    </nav>

    <component
      :is="activeComponent"
      :key="routeState.componentKey"
      v-bind="activeComponentProps"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  Globe2,
  Palette,
  FileText,
  MonitorCog,
  PlugZap,
  UsersRound,
  Printer,
} from 'lucide-vue-next'
import ManagementSiteSettingsPage from './ManagementSiteSettingsPage.vue'
import ManagementPosDefaultsPage from '../sales/ManagementPosDefaultsPage.vue'
import ManagementPosProfilePage from '../sales/ManagementPosProfilePage.vue'
import ManagementPosShiftSettingsPage from './ManagementPosShiftSettingsPage.vue'
import ManagementSnappfoodPage from './ManagementSnappfoodPage.vue'
import ManagementZarinpalSettingsPage from './ManagementZarinpalSettingsPage.vue'
import ManagementUsersPage from './ManagementUsersPage.vue'
import ManagementUserDetailPage from './ManagementUserDetailPage.vue'
import ManagementPrintFormatsPage from './ManagementPrintFormatsPage.vue'

const tabs = [
  { key: 'site', label: 'سایت', href: '/management/settings?tab=site', icon: Globe2 },
  { key: 'appearance', label: 'ظاهر و چیدمان', href: '/management/settings?tab=appearance', icon: Palette },
  { key: 'content', label: 'محتوا و انتشار', href: '/management/settings?tab=content', icon: FileText },
  { key: 'sales', label: 'فروش و صندوق', href: '/management/settings?tab=sales&view=defaults', icon: MonitorCog },
  { key: 'connections', label: 'اتصال‌ها و پرداخت', href: '/management/settings?tab=connections&view=snappfood', icon: PlugZap },
  { key: 'access', label: 'کاربران و دسترسی', href: '/management/settings?tab=access', icon: UsersRound },
  { key: 'print', label: 'چاپ', href: '/management/settings?tab=print', icon: Printer },
]

const salesViews = [
  { key: 'defaults', label: 'پیش‌فرض‌های POS', href: '/management/settings?tab=sales&view=defaults' },
  { key: 'profile', label: 'پروفایل POS', href: '/management/settings?tab=sales&view=profile' },
  { key: 'shift', label: 'تنظیم شیفت', href: '/management/settings?tab=sales&view=shift' },
]

const connectionViews = [
  { key: 'snappfood', label: 'Food Partner', href: '/management/settings?tab=connections&view=snappfood' },
  { key: 'zarinpal', label: 'زرین‌پال', href: '/management/settings?tab=connections&view=zarinpal' },
]

function normalizeRoute() {
  if (typeof window === 'undefined') return { tab: 'site', view: '', entryMode: '', componentKey: 'site' }
  const pathname = window.location.pathname || '/management/settings'
  const params = new URLSearchParams(window.location.search || '')
  const requestedTab = params.get('tab') || ''
  const requestedView = params.get('view') || ''
  const legacyStage = params.get('stage') || ''

  if (/\/management\/(pos-profile|pos_profile)(\/|$)/.test(pathname)) {
    return { tab: 'sales', view: 'profile', entryMode: '', componentKey: 'pos-profile' }
  }
  if (/\/management\/(pos-defaults|pos_defaults)(\/|$)/.test(pathname)) {
    return { tab: 'sales', view: 'defaults', entryMode: '', componentKey: 'pos-defaults' }
  }
  if (/\/management\/(snappfood|snapp-food)(\/|$)/.test(pathname)) {
    return { tab: 'connections', view: 'snappfood', entryMode: '', componentKey: 'snappfood' }
  }
  if (/\/management\/(zarinpal-settings|zarinpal_settings)(\/|$)/.test(pathname)) {
    return { tab: 'connections', view: 'zarinpal', entryMode: '', componentKey: 'zarinpal' }
  }
  if (/\/management\/print[-_]formats(\/|$)/.test(pathname)) {
    return { tab: 'print', view: '', entryMode: '', componentKey: 'print' }
  }
  if (/\/management\/user(\/|$)/.test(pathname) && !/\/management\/users/.test(pathname)) {
    return { tab: 'access', view: '', entryMode: '', componentKey: 'user-detail' }
  }
  if (/\/management\/(users|user-access|user_access)(\/|$)/.test(pathname)) {
    return { tab: 'access', view: '', entryMode: '', componentKey: 'users' }
  }
  if (/\/management\/(home-builder|home_builder)(\/|$)/.test(pathname)) {
    return { tab: 'appearance', view: '', entryMode: 'home-builder', componentKey: 'site' }
  }
  if (/\/management\/(site-settings|site_settings)(\/|$)/.test(pathname)) {
    const legacyTabStage = {
      theme: 'theme',
      'page-builder': 'layout',
      content: 'content',
      review: 'review',
      general: 'identity',
      loader: 'identity',
    }[params.get('tab') || '']
    const stage = legacyStage || legacyTabStage || 'identity'
    const tab = stage === 'theme' || stage === 'layout' ? 'appearance' : ['content', 'review'].includes(stage) ? 'content' : 'site'
    return { tab, view: '', entryMode: '', componentKey: 'site' }
  }

  let tab = ['site', 'appearance', 'content', 'sales', 'connections', 'access', 'print'].includes(requestedTab)
    ? requestedTab
    : 'site'
  if (!requestedTab && legacyStage === 'theme') tab = 'appearance'
  else if (!requestedTab && ['content', 'review'].includes(legacyStage)) tab = 'content'
  else if (!requestedTab && legacyStage === 'layout') tab = 'appearance'

  if (tab === 'sales') {
    const view = ['profile', 'shift'].includes(requestedView) ? requestedView : 'defaults'
    const componentKey = view === 'profile' ? 'pos-profile' : view === 'shift' ? 'pos-shift' : 'pos-defaults'
    return { tab, view, entryMode: '', componentKey }
  }
  if (tab === 'connections') {
    const view = requestedView === 'zarinpal' ? 'zarinpal' : 'snappfood'
    return { tab, view, entryMode: '', componentKey: view }
  }
  if (tab === 'access') return { tab, view: '', entryMode: '', componentKey: 'users' }
  if (tab === 'print') return { tab, view: '', entryMode: '', componentKey: 'print' }
  return {
    tab,
    view: '',
    entryMode: tab === 'appearance' ? 'theme-settings' : '',
    componentKey: 'site',
  }
}

const routeState = ref(normalizeRoute())
const activeComponent = computed(() => ({
  site: ManagementSiteSettingsPage,
  'pos-defaults': ManagementPosDefaultsPage,
  'pos-profile': ManagementPosProfilePage,
  'pos-shift': ManagementPosShiftSettingsPage,
  snappfood: ManagementSnappfoodPage,
  zarinpal: ManagementZarinpalSettingsPage,
  users: ManagementUsersPage,
  'user-detail': ManagementUserDetailPage,
  print: ManagementPrintFormatsPage,
})[routeState.value.componentKey] || ManagementSiteSettingsPage)
const activeComponentProps = computed(() => routeState.value.componentKey === 'site'
  ? { entryMode: routeState.value.entryMode, hubMode: true }
  : {})
const subviews = computed(() => routeState.value.tab === 'sales' ? salesViews : routeState.value.tab === 'connections' ? connectionViews : [])
const subviewLabel = computed(() => routeState.value.tab === 'sales' ? 'تنظیمات فروش' : 'اتصال‌ها و پرداخت')

function syncRouteState() {
  routeState.value = normalizeRoute()
}

onMounted(() => {
  window.addEventListener('popstate', syncRouteState)
  window.addEventListener('restaurant:management-settings-route-change', syncRouteState)
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', syncRouteState)
  window.removeEventListener('restaurant:management-settings-route-change', syncRouteState)
})
</script>

<style scoped>
.settings-hub {
  display: grid;
  gap: var(--ds-space-3, .75rem);
  width: 100%;
  min-width: 0;
}

.settings-hub__tabs,
.settings-hub__subtabs {
  display: flex;
  align-items: center;
  gap: var(--ds-space-2, .5rem);
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}

.settings-hub__tabs {
  padding: var(--ds-space-2, .5rem);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-surface);
}

.settings-hub__tab,
.settings-hub__subtab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2, .5rem);
  min-height: 44px;
  flex: 0 0 auto;
  padding: 0 var(--ds-space-3, .75rem);
  border: 1px solid transparent;
  border-radius: var(--ds-radius-sm, 10px);
  color: var(--ds-color-text-secondary);
  text-decoration: none;
  white-space: nowrap;
  font-size: .85rem;
  font-weight: 700;
  transition: color var(--ds-motion-fast, 160ms) ease, background var(--ds-motion-fast, 160ms) ease;
}

.settings-hub__tab:hover,
.settings-hub__subtab:hover { color: var(--ds-color-action-primary); background: var(--ds-color-surface-muted); }
.settings-hub__tab.is-active,
.settings-hub__subtab.is-active {
  color: var(--ds-color-action-primary);
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 26%, var(--ds-color-border));
  background: var(--ds-color-action-primary-soft);
}

.settings-hub__subtabs { padding-inline: var(--ds-space-1, .25rem); }

.settings-hub :deep(.management-page) { gap: var(--ds-space-3, .75rem); }
.settings-hub :deep(.management-page__header) { box-shadow: none; }

@media (max-width: 640px) {
  .settings-hub__tabs { margin-inline: calc(var(--ds-space-2, .5rem) * -1); border-radius: 0; }
  .settings-hub__tab { min-height: 42px; padding-inline: var(--ds-space-2, .5rem); font-size: .8rem; }
}

@media (prefers-reduced-motion: reduce) {
  .settings-hub__tab, .settings-hub__subtab { transition: none; }
}
</style>
