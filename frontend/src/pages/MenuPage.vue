<template>
  <div class="menu-page-root">
    <div class="menu-intro">
      <div><p>تازه آماده می‌کنیم</p><h1>امروز چی میل دارید؟</h1></div>
      <button type="button" class="menu-search-link" aria-label="جستجو در منو" @click="openSearch"><Search :size="20" /> <span>جستجو</span></button>
    </div>
    <!-- ─── Sticky Category Rail (first on mobile, after hero on desktop) ─── -->
    <div
      class="category-rail-sticky"
      :class="{ 'is-sticky': railSticky }"
      ref="railRef"
    >
      <CategoryImageRail
        :categories="categories"
        :selected-category="selectedCategorySlug"
        :subcategories="currentSubcategories"
        :selected-subcategory="selectedSubcategorySlug"
        :active-category-title="activeCategoryTitle"
        @select-category="selectCategory"
        @select-subcategory="selectSubcategory"
      />
    </div>

    <div class="menu-toolbar" role="group" aria-label="مرتب‌سازی منو">
      <button
        class="sort-toggle"
        type="button"
        @click="toggleSortMenu"
        :aria-expanded="sortMenuOpen ? 'true' : 'false'"
        aria-controls="menu-sort-options"
      >
        <ChevronDown :size="16" />
        <span>{{ activeSortLabel }}</span>
      </button>
      <div class="sort-menu" id="menu-sort-options" role="group" aria-label="گزینه‌های مرتب‌سازی" v-show="sortMenuOpen">
        <button
          v-for="option in sortOptions"
          :key="option.value"
          type="button"
          :class="{ active: sortMode === option.value }"
          :aria-pressed="sortMode === option.value"
          @click="setSortMode(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <!-- فیلتر تگ‌ها -->
    <div class="tag-filter-row" role="group" aria-label="فیلتر بر اساس برچسب" v-if="availableTags.length">
      <button
        class="tag-filter-btn"
        type="button"
        :class="{ active: !selectedTag }"
        :aria-pressed="!selectedTag"
        @click="selectedTag = ''"
      >همه</button>
      <button
        v-for="tag in availableTags"
        :key="tag"
        class="tag-filter-btn"
        type="button"
        :class="{ active: selectedTag === tag }"
        :aria-pressed="selectedTag === tag"
        @click="selectedTag = selectedTag === tag ? '' : tag"
      >{{ tag }}</button>
    </div>

    <LiquidGlassBackdrop>
    <section class="page-shell menu-shell">
      <OrderContextStrip :currency="currency" />

      <!-- سربرگ نتایج -->
      <section class="result-head" ref="resultHeadRef">
        <transition name="fade" mode="out-in">
          <p class="muted result-count" role="status" aria-live="polite" aria-atomic="true" v-if="!loading" key="count">
            <span class="count-badge">{{ displayItems.length }}</span>
            محصول آماده سفارش
          </p>
          <p class="muted" role="status" aria-live="polite" v-else key="loading-text">در حال بارگذاری...</p>
        </transition>
        <p class="muted error-text" role="alert" v-if="error">
          {{ error }}
          <button class="retry-btn" type="button" @click="reloadItems" :disabled="loading">تلاش مجدد</button>
        </p>
      </section>

      <!-- اسکلتون هنگام لودینگ اولیه -->
      <section class="item-list" v-if="loading && !items.length">
        <div class="skeleton-card" v-for="n in 6" :key="n">
          <div class="skeleton-img shimmer"></div>
          <div class="skeleton-body">
            <div class="skeleton-line shimmer" style="width: 65%"></div>
            <div class="skeleton-line shimmer" style="width: 45%; height: 0.65rem; margin-top: 0.3rem"></div>
            <div class="skeleton-footer">
              <div class="skeleton-line shimmer" style="width: 35%"></div>
              <div class="skeleton-btn shimmer"></div>
            </div>
          </div>
        </div>
      </section>

      <div class="menu-groups" v-if="menuGroups.length">
        <section
          v-for="group in menuGroups"
          :key="group.slug"
          class="menu-category-section"
          :ref="(el) => setCategorySectionRef(group.slug, el)"
          :aria-label="group.title"
        >
          <header class="menu-category-head">
            <div><small>دسته‌بندی منو</small><h2>{{ group.title }}</h2></div>
            <span>{{ group.items.length.toLocaleString('fa-IR') }} آیتم</span>
          </header>
          <article
            v-for="section in group.sections"
            :key="section.anchorKey"
            class="subcategory-block"
            :ref="(el) => setSubcategorySectionRef(section.anchorKey, el)"
          >
            <header v-if="section.title" class="subcategory-head">
              <h3>{{ section.title }}</h3>
              <small>{{ section.items.length.toLocaleString('fa-IR') }} آیتم</small>
            </header>
            <div class="item-list">
              <MenuProductCard
                v-for="item in section.items"
                :key="item.slug"
                :item="item"
                :currency="currency"
                :theme="menuCardTheme"
                :cart-qty="getItemCartQty(item)"
                :can-view-bom="canViewBom"
                @quick-add="quickAdd"
                @quick-increase="quickIncrease"
                @quick-decrease="quickDecrease"
                @bom-preview="openBomModal"
              />
            </div>
          </article>
        </section>
      </div>

      <!-- حالت خالی -->
      <transition name="fade">
        <LiquidGlassCard class="empty-box" v-if="!loading && !displayItems.length && !error">
          <Utensils class="empty-icon" :size="34" stroke-width="1.8" />
          <p class="empty-title">{{ emptyStateTitle }}</p>
          <p class="muted">{{ emptyStateMessage }}</p>
          <button class="reset-btn" type="button" @click="resetFilters">{{ emptyStateAction }}</button>
        </LiquidGlassCard>
      </transition>

      <CartActionFeedback :message="cartFeedback" />

      <MenuQuickAddSheet
        :open="quickSheetOpen"
        :item="quickSheetItem"
        :currency="currency"
        :branch="activeBranch"
        @close="closeQuickSheet"
        @confirm="confirmQuickAdd"
      />

      <Teleport to="body">
        <ProductBuilderWizard
          v-if="builderOpen && builderTemplate && builderItem"
          :product="builderProductPayload"
          :template="builderTemplate"
          :base-price="Number(builderItem.base_price || 0)"
          :currency="currency"
          :loading-price="builderPriceLoading"
          @close="closeBuilderWizard"
          @selection-change="handleBuilderSelectionChange"
          @add-to-cart="handleBuilderAddToCart"
        />
      </Teleport>

      <section class="print-catalog">
        <section class="print-grid" v-if="printCards.length">
          <article class="print-card" v-for="item in printCards" :key="`print-item-${item.slug || item.name || item.title}`">
            <h3>{{ item.title || item.name || '-' }}</h3>
            <p v-if="item.short_desc">{{ item.short_desc }}</p>
            <strong>{{ formatMoney(item.base_price, currency) }}</strong>
          </article>
        </section>
        <p class="print-empty" v-else>آیتمی برای چاپ پیدا نشد.</p>
      </section>

      <!-- دکمه فلش رو به بالا -->
      <button
        class="scroll-top-btn"
        :class="{ visible: showScrollTop }"
        @click="scrollToTop"
        aria-label="بازگشت به بالا"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"/></svg>
      </button>

    </section>
    </LiquidGlassBackdrop>

    <!-- BOM Preview Modal -->
    <BomPreviewModal
      :open="bomModalOpen"
      :item="bomModalItem"
      :currency="currency"
      :branch="activeBranch"
      :is-staff-only="bomModalItem?.is_staff_only || false"
      @close="closeBomModal"
      @confirm="confirmQuickAdd"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch, Teleport } from 'vue'
import { useSearchModal } from '@/composables/useSearchModal'
import { Search, ChevronDown, Utensils } from 'lucide-vue-next'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import LiquidGlassCard from '@/components/LiquidGlassCard.vue'
import CategoryImageRail from '@/components/CategoryImageRail.vue'
import MenuProductCard from '@/components/MenuProductCard.vue'
import MenuQuickAddSheet from '@/components/MenuQuickAddSheet.vue'
import BomPreviewModal from '@/components/BomPreviewModal.vue'
import ProductBuilderWizard from '@/components/ProductBuilderWizard.vue'
import CartActionFeedback from '@/components/customer/CartActionFeedback.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { getMenuItems, getManagementSessionProfile, getBuilderTemplate, computeBuilderPrice } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { buildMenuSections } from '@/utils/menuSections'
import { cartState, upsertLine, removeLine } from '@/stores/cartStore'
const { openSearch } = useSearchModal()

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

function resolveBranchFromBoot() {
  const fromBoot = String(props.boot.active_branch || '').trim()
  if (fromBoot) {
    return fromBoot
  }

  const fromTable = String(props.boot?.table_context?.table?.branch || '').trim()
  if (fromTable) {
    return fromTable
  }

  const branchParam = new URLSearchParams(window.location.search).get('branch')
  return String(branchParam || '').trim()
}

// ─── state ─────────────────────────────────────────────────────────
const categories = ref((props.boot.categories || []).filter((row) => (row.item_count || 0) > 0))
const currency = ref(props.boot.currency || 'IRR')
const activeBranch = ref(resolveBranchFromBoot())
const items = ref([])
const loading = ref(true)
const error = ref('')
const cartFeedback = ref('')
let cartFeedbackTimer = null
const selectedTag = ref('')
const sortMode = ref('default')
const sortMenuOpen = ref(false)
const selectedCategorySlug = ref(categories.value[0]?.slug || '')
const selectedSubcategorySlug = ref('')

const resultHeadRef = ref(null)
const categorySectionRefs = ref({})
const subcategorySectionRefs = ref({})
const quickSheetOpen = ref(false)
const quickSheetItem = ref(null)
const builderOpen = ref(false)
const builderItem = ref(null)
const builderTemplate = ref(null)
const builderPriceLoading = ref(false)
const builderPriceData = ref(null)
const bomModalOpen = ref(false)
const bomModalItem = ref(null)
const canViewBom = ref(false)
const printPreparing = ref(false)
const printCards = ref([])
const showScrollTop = ref(false)
const railSticky = ref(false)
const railRef = ref(null)
let railOffsetTop = 0

function syncHeaderOffset() {
  const header = document.querySelector('.app-header')
  const desktopHeader = header?.querySelector?.('.header-inner')
  const desktopVisible = Boolean(desktopHeader && window.innerWidth >= 920)
  const offset = desktopVisible ? Math.ceil(header?.getBoundingClientRect?.().height || header?.offsetHeight || 0) : 0
  document.documentElement.style.setProperty('--menu-header-offset', `${offset}px`)
}

function handleScroll() {
  if (!railOffsetTop) {
    railOffsetTop = railRef.value?.offsetTop || 0
  }
  const scrolled = window.scrollY || document.documentElement.scrollTop
  const shouldSticky = scrolled > railOffsetTop
  if (shouldSticky !== railSticky.value) {
    railSticky.value = shouldSticky
    // Set CSS variable for padding compensation
    if (shouldSticky && railRef.value) {
      document.documentElement.style.setProperty('--rail-height', `${railRef.value.offsetHeight}px`)
    } else {
      document.documentElement.style.setProperty('--rail-height', '0px')
    }
  }
}

let scrollTicking = false
function onScroll() {
  showScrollTop.value = window.scrollY > 300
  if (!scrollTicking) {
    requestAnimationFrame(() => {
      handleScroll()
      syncActiveSectionFromScroll()
      scrollTicking = false
    })
    scrollTicking = true
  }
}

function handleResize() {
  railOffsetTop = railRef.value?.offsetTop || 0
  syncHeaderOffset()
  syncActiveSectionFromScroll()
}

function getMenuStickyOffset() {
  const rootStyles = window.getComputedStyle(document.documentElement)
  const headerOffset = Number.parseFloat(rootStyles.getPropertyValue('--menu-header-offset')) || 0
  const railHeight = Number(railRef.value?.offsetHeight || 0)
  return Math.max(0, Math.ceil(headerOffset + railHeight + 10))
}

function scrollElementIntoMenuView(element, { behavior = 'smooth' } = {}) {
  if (!element) {
    return
  }
  const targetTop = window.scrollY + element.getBoundingClientRect().top - getMenuStickyOffset()
  window.scrollTo({
    top: Math.max(0, targetTop),
    behavior,
  })
}

// ─── computed ───────────────────────────────────────────────────────
const menuCardTheme = computed(() => {
  return {
    primary_color: 'var(--ds-color-action-primary)',
    primary_color_dark: 'color-mix(in srgb, var(--ds-color-action-primary) 88%, var(--ds-color-text-primary))',
    accent_color: 'var(--ds-color-status-success)',
    success: 'var(--ds-color-status-success)',
    success_bg: 'var(--ds-color-status-success-soft)',
    surface: 'var(--ds-color-surface-raised)',
    surface_alt: 'var(--ds-color-surface-muted)',
    border: 'var(--ds-color-border)',
    text_primary: 'var(--ds-color-text-primary)',
    text_secondary: 'var(--ds-color-text-secondary)',
    text_muted: 'var(--ds-color-text-muted)',
    add_btn_bg: 'var(--ds-color-action-accent)',
  }
})
const availableTags = computed(() => {
  const tagSet = new Set()
  const allItems = items.value || []
  for (const item of allItems) {
    const tags = Array.isArray(item.tags) ? item.tags : []
    for (const tag of tags) {
      const t = String(tag || '').trim()
      if (t) tagSet.add(t)
    }
  }
  return Array.from(tagSet).sort((a, b) => a.localeCompare(b, 'fa'))
})
const builderProductPayload = computed(() => {
  const target = builderItem.value || {}
  return {
    ...target,
    item_name: target.title || target.item_name || '',
    item_code: target.name || target.item_code || '',
    image: target.image || '',
  }
})

const sortOptions = [
  { value: 'default', label: 'مرتب‌سازی' },
  { value: 'price_asc', label: 'ارزان‌ترین' },
  { value: 'price_desc', label: 'گران‌ترین' },
  { value: 'name_asc', label: 'نام محصول' },
]
const activeSortLabel = computed(() => sortOptions.find((row) => row.value === sortMode.value)?.label || 'مرتب‌سازی')
const tagFilteredItems = computed(() => {
  const tag = selectedTag.value
  if (!tag) return items.value
  return (items.value || []).filter((item) => {
    const tags = Array.isArray(item.tags) ? item.tags : []
    return tags.some((t) => String(t).trim() === tag)
  })
})

const displayItems = computed(() => sortItems(tagFilteredItems.value))

// ─── empty state context ────────────────────────────────────────────
const emptyStateTitle = computed(() => {
  if (selectedTag.value) return 'محصولی با این فیلتر پیدا نشد'
  return 'محصولی پیدا نشد'
})
const emptyStateMessage = computed(() => {
  if (selectedTag.value) return 'فیلترها را تغییر دهید'
  return 'در این دسته‌بندی محصولی وجود ندارد'
})
const emptyStateAction = computed(() => {
  if (selectedTag.value) return 'حذف فیلتر'
  return 'نمایش همه محصولات'
})

const activeCategory = computed(() => categories.value.find((row) => row.slug === selectedCategorySlug.value) || null)
const activeCategoryTitle = computed(() => activeCategory.value?.title || 'دسته')
const menuGroups = computed(() => buildMenuSections(categories.value, displayItems.value, sortMode.value))
const currentSubcategories = computed(() =>
  menuGroups.value.find((group) => group.slug === selectedCategorySlug.value)?.subcategories || [],
)

const itemsBySlug = computed(() => {
  const map = new Map()
  for (const row of items.value || []) {
    const slug = String(row?.slug || '').trim()
    if (slug) {
      map.set(slug, row)
    }
  }
  return map
})

function sortItems(rows = []) {
  const next = [...(rows || [])]
  if (sortMode.value === 'price_asc') {
    return next.sort((left, right) => Number(left?.base_price || 0) - Number(right?.base_price || 0))
  }
  if (sortMode.value === 'price_desc') {
    return next.sort((left, right) => Number(right?.base_price || 0) - Number(left?.base_price || 0))
  }
  if (sortMode.value === 'name_asc') {
    return next.sort((left, right) => String(left?.title || '').localeCompare(String(right?.title || ''), 'fa'))
  }
  return next
}

function toggleSortMenu() {
  sortMenuOpen.value = !sortMenuOpen.value
}

function setSortMode(value) {
  sortMode.value = value
  sortMenuOpen.value = false
}

function isPrintableItem(item = {}) {
  if (item?.show_in_print !== undefined && item?.show_in_print !== null && item?.show_in_print !== '') {
    return Number(item.show_in_print || 0) === 1
  }
  if (item?.show_in_website !== undefined && item?.show_in_website !== null && item?.show_in_website !== '') {
    return Number(item.show_in_website || 0) === 1
  }
  return true
}

async function buildPrintCards() {
  const loaded = []
  const seen = new Set()

  async function fetchCategoryPages(categorySlug = '') {
    const slug = String(categorySlug || '').trim()
    let page = 1
    let totalPages = 1
    while (page <= totalPages && page <= 200) {
      const data = await getMenuItems({
        category_slug: slug,
        subcategory_slug: '',
        search: '',
        page,
        page_size: 100,
        branch: activeBranch.value,
      })
      const rows = Array.isArray(data?.items) ? data.items : []
      for (const row of rows) {
        if (!isPrintableItem(row)) {
          continue
        }
        const key = String(row?.slug || row?.name || '').trim()
        if (!key || seen.has(key)) {
          continue
        }
        seen.add(key)
        loaded.push(row)
      }
      const paginationPayload = data?.pagination || {}
      const nextTotalPages = Number(paginationPayload.total_pages || 1)
      totalPages = Number.isFinite(nextTotalPages) && nextTotalPages > 0 ? nextTotalPages : 1
      page += 1
    }
  }

  const categoryRows = Array.isArray(categories.value) ? categories.value : []
  for (const category of categoryRows) {
    const slug = String(category?.slug || '').trim()
    if (!slug) {
      continue
    }
    await fetchCategoryPages(slug)
  }

  await fetchCategoryPages('')

  loaded.sort((left, right) => {
    const byCategory = String(left?.category_title || left?.category || '').localeCompare(
      String(right?.category_title || right?.category || ''),
      'fa',
    )
    if (byCategory !== 0) {
      return byCategory
    }
    const bySubcategory = String(left?.subcategory_title || left?.subcategory || '').localeCompare(
      String(right?.subcategory_title || right?.subcategory || ''),
      'fa',
    )
    if (bySubcategory !== 0) {
      return bySubcategory
    }
    return String(left?.title || left?.name || '').localeCompare(String(right?.title || right?.name || ''), 'fa')
  })

  printCards.value = loaded
}

async function triggerCatalogPrint() {
  if (printPreparing.value) {
    return
  }
  printPreparing.value = true
  try {
    await buildPrintCards()
    await nextTick()
    window.print()
  } finally {
    printPreparing.value = false
  }
}

function handlePrintShortcut(event) {
  const key = String(event?.key || '').toLowerCase()
  if ((event?.ctrlKey || event?.metaKey) && key === 'p') {
    event.preventDefault()
    void triggerCatalogPrint()
  }
}

watch(selectedTag, async () => {
  await nextTick()
  scrollElementIntoMenuView(resultHeadRef.value)
  syncActiveSectionFromScroll()
})

// Keep every category in one continuous catalog; the rail only navigates within it.
async function fetchCategoryCatalog(categorySlug) {
  const collected = []
  const seen = new Set()
  let page = 1
  let totalPages = 1
  while (page <= totalPages && page <= 200) {
    const data = await getMenuItems({
      category_slug: categorySlug,
      subcategory_slug: '',
      search: '',
      page,
      page_size: 100,
      branch: activeBranch.value,
    })
    for (const item of Array.isArray(data?.items) ? data.items : []) {
      const key = String(item?.slug || item?.name || '').trim()
      if (!key || seen.has(key)) continue
      seen.add(key)
      collected.push(item)
    }
    totalPages = Math.max(1, Number(data?.pagination?.total_pages || 1))
    page += 1
  }
  return collected
}

async function reloadItems() {
  loading.value = true
  error.value = ''
  items.value = []
  categorySectionRefs.value = {}
  subcategorySectionRefs.value = {}
  try {
    const requests = categories.value.length
      ? categories.value.map((category) => fetchCategoryCatalog(category.slug))
      : [fetchCategoryCatalog('')]
    const responses = await Promise.allSettled(requests)
    const seen = new Set()
    items.value = responses.flatMap((response) => response.status === 'fulfilled' ? response.value : [])
      .filter((item) => {
        const key = String(item?.slug || item?.name || '').trim()
        if (!key || seen.has(key)) return false
        seen.add(key)
        return true
      })
    if (responses.some((response) => response.status === 'rejected')) {
      error.value = items.value.length
        ? 'بخشی از منو بارگذاری نشد. برای دیدن همهٔ محصولات دوباره تلاش کنید.'
        : 'دریافت منو ناموفق بود. دوباره تلاش کنید.'
    }
  } finally {
    loading.value = false
  }
}

function setCategorySectionRef(slug, element) {
  if (!slug) return
  if (element) categorySectionRefs.value[slug] = element
  else delete categorySectionRefs.value[slug]
}

function setSubcategorySectionRef(anchorKey, element) {
  if (!anchorKey) return
  if (element) subcategorySectionRefs.value[anchorKey] = element
  else delete subcategorySectionRefs.value[anchorKey]
}

function syncActiveSectionFromScroll() {
  const threshold = getMenuStickyOffset() + 40
  let activeGroup = menuGroups.value[0]
  for (const group of menuGroups.value) {
    const element = categorySectionRefs.value[group.slug]
    if (element && element.getBoundingClientRect().top <= threshold) activeGroup = group
    else if (element) break
  }
  if (!activeGroup) return
  if (selectedCategorySlug.value !== activeGroup.slug) selectedCategorySlug.value = activeGroup.slug

  let subcategory = ''
  for (const section of activeGroup.sections) {
    const element = subcategorySectionRefs.value[section.anchorKey]
    if (element && element.getBoundingClientRect().top <= threshold) subcategory = section.slug
    else if (element) break
  }
  if (selectedSubcategorySlug.value !== subcategory) selectedSubcategorySlug.value = subcategory
}

function selectCategory(slug) {
  const target = categorySectionRefs.value[String(slug || '').trim()]
  if (target) scrollElementIntoMenuView(target)
}

function selectSubcategory(slug) {
  const cleanSlug = String(slug || '').trim()
  if (!cleanSlug) {
    scrollElementIntoMenuView(categorySectionRefs.value[selectedCategorySlug.value])
    return
  }
  const target = subcategorySectionRefs.value[selectedCategorySlug.value + ':' + cleanSlug]
  if (target) scrollElementIntoMenuView(target)
}

function resetFilters() {
  selectedTag.value = ''
  scrollToTop()
}

function itemHasCustomization(item = {}) {
  const slug = String(item?.slug || '').trim()
  const itemFromList = slug ? itemsBySlug.value.get(slug) : null
  const target = itemFromList || item
  return Number(target?.has_customization || 0) === 1
}

function itemHasBuilder(item = {}) {
  const slug = String(item?.slug || '').trim()
  const itemFromList = slug ? itemsBySlug.value.get(slug) : null
  const target = itemFromList || item
  return Boolean(
    target &&
      Number(target.restaurant_is_customizable || 0) === 1 &&
      Number(target.restaurant_builder_active || 0) === 1,
  )
}

function getItemCartQty(item = {}) {
  const slug = String(item?.slug || '').trim()
  if (!slug) {
    return 0
  }
  return cartState.lines
    .filter((line) => String(line?.item_slug || '').trim() === slug)
    .reduce((sum, line) => sum + Number(line?.qty || 0), 0)
}

function findSimpleLineBySlug(slug = '') {
  const normalized = String(slug || '').trim()
  if (!normalized) {
    return null
  }
  return (
    cartState.lines.find((line) => {
      if (String(line?.item_slug || '').trim() !== normalized) {
        return false
      }
      const hasIngredients = Array.isArray(line?.ingredient_catalog) && line.ingredient_catalog.length > 0
      const hasModifiers = Array.isArray(line?.modifier_groups_catalog) && line.modifier_groups_catalog.length > 0
      return !hasIngredients && !hasModifiers
    }) || null
  )
}

function addSimpleLine(item = {}, qtyDelta = 1) {
  const slug = String(item?.slug || '').trim()
  if (!slug || qtyDelta <= 0) {
    return
  }

  const basePrice = Number(item?.base_price || 0)
  const existing = findSimpleLineBySlug(slug)
  if (existing) {
    const nextQty = Math.max(Number(existing.qty || 0) + Number(qtyDelta || 0), 1)
    upsertLine({
      ...existing,
      id: existing.id,
      qty: nextQty,
      unit_price_preview: Number(existing.unit_price_preview || basePrice),
      line_total_preview: Number(existing.unit_price_preview || basePrice) * nextQty,
    })
    return
  }

  upsertLine({
    item_slug: slug,
    item_title: item?.title,
    item_image: item?.image || '',
    base_price: basePrice,
    qty: Math.max(Number(qtyDelta || 1), 1),
    unit_price_preview: basePrice,
    line_total_preview: basePrice * Math.max(Number(qtyDelta || 1), 1),
    customization: {
      ingredient_adjustments: [],
      selected_modifiers: [],
    },
    ingredient_catalog: [],
    modifier_groups_catalog: [],
  })
}

function removeSimpleLineQty(item = {}, qtyDelta = 1) {
  const slug = String(item?.slug || '').trim()
  if (!slug || qtyDelta <= 0) {
    return
  }
  const line = findSimpleLineBySlug(slug)
  if (!line) {
    return
  }
  const nextQty = Number(line.qty || 0) - Number(qtyDelta || 0)
  if (nextQty <= 0) {
    removeLine(line.id)
    return
  }
  upsertLine({
    ...line,
    id: line.id,
    qty: nextQty,
    unit_price_preview: Number(line.unit_price_preview || line.base_price || 0),
    line_total_preview: Number(line.unit_price_preview || line.base_price || 0) * nextQty,
  })
}

function isComingSoonItem(item = {}) {
  return Number(item?.coming_soon ?? item?.restaurant_coming_soon ?? 0) === 1
}

function isStockOutItem(item = {}) {
  return Number(item?.stock_out || 0) === 1
}

function isOutOfStockItem(item = {}) {
  return Number(item?.out_of_stock ?? item?.restaurant_out_of_stock ?? 0) === 1
}

// ─── افزودن سریع به سبد ────────────────────────────────────────────
function quickAdd(item) {
  if (isComingSoonItem(item) || isStockOutItem(item) || isOutOfStockItem(item)) {
    return
  }
  if (itemHasBuilder(item)) {
    openBuilderWizard(item)
    return
  }
  if (!itemHasCustomization(item)) {
    addSimpleLine(item, 1)
    showCartFeedback(`${item.title || 'محصول'} به سبد سفارش اضافه شد.`)
    return
  }
  quickSheetItem.value = item
  quickSheetOpen.value = true
}

function quickIncrease(item) {
  if (isComingSoonItem(item) || isStockOutItem(item) || isOutOfStockItem(item)) {
    return
  }
  if (itemHasBuilder(item) || itemHasCustomization(item)) {
    quickAdd(item)
    return
  }
  addSimpleLine(item, 1)
  showCartFeedback(`${item.title || 'محصول'} به سبد سفارش اضافه شد.`)
}

function showCartFeedback(message) {
  cartFeedback.value = message
  clearTimeout(cartFeedbackTimer)
  cartFeedbackTimer = setTimeout(() => { cartFeedback.value = '' }, 2200)
}

function quickDecrease(item) {
  if (itemHasBuilder(item) || itemHasCustomization(item)) {
    return
  }
  removeSimpleLineQty(item, 1)
}

async function openBuilderWizard(item) {
  const slug = String(item?.slug || '').trim()
  const target = slug ? (itemsBySlug.value.get(slug) || item) : item
  if (!target) return
  closeQuickSheet()
  builderItem.value = target
  builderTemplate.value = null
  builderPriceData.value = null
  builderPriceLoading.value = false
  builderOpen.value = true
  try {
    const itemCode = target.name || target.item_code || target.title || target.slug
    const data = await getBuilderTemplate(itemCode)
    builderTemplate.value = data?.data?.template || data?.template || data || null
  } catch (err) {
    builderOpen.value = false
    builderItem.value = null
    window.location.href = `/item/${target.slug}`
  }
}

function closeBuilderWizard() {
  builderOpen.value = false
  builderItem.value = null
  builderTemplate.value = null
  builderPriceData.value = null
  builderPriceLoading.value = false
}

async function handleBuilderSelectionChange(selections) {
  if (!builderItem.value) return
  builderPriceLoading.value = true
  try {
    const itemCode = builderItem.value.name || builderItem.value.item_code || builderItem.value.title || builderItem.value.slug
    const response = await computeBuilderPrice(itemCode, selections || [])
    builderPriceData.value = response?.data || response || null
  } catch (_) {
    builderPriceData.value = null
  } finally {
    builderPriceLoading.value = false
  }
}

function handleBuilderAddToCart(payload) {
  if (!builderItem.value) return
  const builderRows = Array.isArray(payload?.builder_portion_rows)
    ? payload.builder_portion_rows
    : Array.isArray(payload?.selections)
      ? payload.selections
      : []
  const builderSelection = {
    selection_id: String(payload?.selection_id || '').trim(),
    template: payload?.template || builderTemplate.value?.name || '',
    selections: builderRows.map((row) => ({
      step_key: row.step_key,
      option_key: row.option_key,
      qty: Number(row.portion_count ?? row.qty ?? 0),
    })),
    summary: payload?.builder_summary || '',
  }
  const builderPricingBreakdown = payload?.builder_pricing_breakdown || builderPriceData.value || {}
  const finalPrice = Number(
    builderPricingBreakdown?.final_price ??
    builderPriceData.value?.final_price ??
    payload?.final_price ??
    builderItem.value.base_price ??
    0,
  )
  upsertLine({
    item_slug: builderItem.value.slug,
    item_title: builderItem.value.title || builderItem.value.item_name,
    item_image: builderItem.value.image,
    base_price: Number(builderItem.value.base_price || 0),
    qty: 1,
    unit_price_preview: finalPrice,
    line_total_preview: finalPrice,
    customization: {
      ingredient_adjustments: [],
      selected_modifiers: [],
      selected_alternatives: [],
      builder_selection: builderSelection,
      builder_summary: payload?.builder_summary || builderSelection.summary || '',
      builder_pricing_breakdown: {
        ...builderPricingBreakdown,
        final_price: finalPrice,
      },
      builder_portion_rows: builderRows,
      builder_template: builderTemplate.value?.name || payload?.template || '',
    },
  })
  showCartFeedback(`${builderItem.value.title || 'محصول'} به سبد سفارش اضافه شد.`)
  setTimeout(() => {
    closeBuilderWizard()
  }, 650)
}

function closeQuickSheet() {
  quickSheetOpen.value = false
  quickSheetItem.value = null
}

function openBomModal(item) {
  bomModalItem.value = item
  bomModalOpen.value = true
}

function closeBomModal() {
  bomModalOpen.value = false
  bomModalItem.value = null
}

function confirmQuickAdd(linePayload) {
  upsertLine({
    ...linePayload,
  })
  showCartFeedback(`${linePayload?.item_title || linePayload?.item_name || quickSheetItem.value?.title || 'محصول'} به سبد سفارش اضافه شد.`)
  closeQuickSheet()
}

// ─── lifecycle ──────────────────────────────────────────────────────
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  getManagementSessionProfile()
    .then((profile) => {
      canViewBom.value = Boolean(profile?.is_staff || profile?.is_admin)
    })
    .catch(() => {
      canViewBom.value = false
    })

  const urlCategory = new URLSearchParams(window.location.search).get('category')
  await reloadItems()
  printCards.value = items.value.filter((row) => isPrintableItem(row))
  await nextTick()
  railOffsetTop = railRef.value?.offsetTop || 0
  syncHeaderOffset()
  if (urlCategory && categorySectionRefs.value[urlCategory]) {
    scrollElementIntoMenuView(categorySectionRefs.value[urlCategory], { behavior: 'auto' })
  }
  syncActiveSectionFromScroll()
  showScrollTop.value = window.scrollY > 300
  window.addEventListener('keydown', handlePrintShortcut)
  window.addEventListener('scroll', onScroll)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearTimeout(cartFeedbackTimer)
  window.removeEventListener('keydown', handlePrintShortcut)
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', handleResize)
  document.documentElement.style.setProperty('--menu-header-offset', '0px')
})
</script>

<style scoped>
.menu-intro { width: min(1120px, calc(100% - 2rem)); margin: 1.1rem auto; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.menu-intro p { color: var(--ds-color-action-primary); font-size: .8rem; margin: 0 0 .3rem; }
.menu-intro h1 { font-size: clamp(1.35rem, 3vw, 1.9rem); margin: 0; }
.menu-search-link { display: inline-flex; align-items: center; gap: .4rem; min-height: 44px; padding: .5rem .7rem; border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); border: 1px solid var(--ds-color-border); color: var(--ds-color-action-primary); text-decoration: none; }

.menu-shell {
  width: min(540px, calc(100% - 1rem));
  margin: 0 auto;
  padding: 0 0.5rem max(6.5rem, calc(6.5rem + env(safe-area-inset-bottom)));
}

/* ─── Sticky Rail (JS-based because overflow:hidden ancestors break CSS sticky) ─── */
.category-rail-sticky {
  position: relative;
  z-index: 100;
  background: var(--ds-color-bg-page, var(--theme-background, #f6f1ea));
  padding: 0;
  border-bottom: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.1);
  transition: box-shadow 0.2s ease;
}

/* On mobile, rail is at the very top — add some breathing room */
@media (max-width: 919px) {
  .category-rail-sticky {
    padding-top: 0;
  }
}

.category-rail-sticky.is-sticky {
  position: fixed;
  top: var(--menu-header-offset, 0px);
  left: 0;
  right: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* On mobile (no header), rail sits at top: 0 when sticky */
@media (max-width: 919px) {
  .category-rail-sticky.is-sticky {
    top: 0;
  }
}

.menu-page-root {
  min-height: 100dvh;
}

.menu-toolbar {
  width: min(540px, calc(100% - 1rem));
  margin: 0.42rem auto 0.34rem;
  position: relative;
  display: flex;
  justify-content: flex-start;
  z-index: 20;
}

.sort-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  min-height: 44px;
  padding: 0 0.62rem;
  border-radius: 12px;
  border: 1px solid var(--ds-color-border, var(--glass-border));
  background: var(--ds-color-surface-raised, #fff);
  color: var(--ds-color-text-secondary, var(--text-secondary));
  box-shadow: 0 6px 14px rgb(15 23 42 / 0.045);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  cursor: pointer;
}

.sort-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 132px;
  display: grid;
  gap: 0.18rem;
  padding: 0.28rem;
  border-radius: 13px;
  border: 1px solid var(--ds-color-border, var(--glass-border));
  background: var(--ds-color-surface-raised, #fff);
  box-shadow: 0 12px 24px rgb(15 23 42 / 0.10);
}

.sort-menu button {
  border: 0;
  background: transparent;
  border-radius: 9px;
  min-height: 44px;
  padding: 0.5rem 0.65rem;
  text-align: right;
  color: var(--ds-color-text-secondary, var(--text-secondary));
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
}

.sort-menu button.active,
.sort-menu button:hover {
  background: var(--ds-color-action-primary-soft, var(--accent-green20));
  color: var(--ds-color-action-primary, var(--accent-green));
}

/* Reserve space when rail is fixed so content doesn't jump */
.category-rail-sticky.is-sticky ~ .liquid-backdrop {
  padding-top: var(--rail-height, 0px);
}

/* ─── فیلتر تگ‌ها ─── */
.tag-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  width: min(540px, calc(100% - 1rem));
  margin: 0 auto 0.25rem;
  padding: 0.5rem 0.5rem 0;
  margin-bottom: 0.25rem;
}

.tag-filter-btn {
  min-height: 44px;
  background: var(--ds-color-surface, var(--glass-bg, #fdf8f1));
  border: 1px solid var(--ds-color-border, var(--glass-border, #d5c3af));
  border-radius: 999px;
  padding: 0.45rem 0.85rem;
  font-size: 0.78rem;
  color: var(--ds-color-text-secondary, var(--text-secondary, #654a38));
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tag-filter-btn:hover {
  border-color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
}

.tag-filter-btn.active {
  background: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  border-color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse, #fff));
  font-weight: 600;
}

/* ─── سربرگ نتایج ─── */
.result-head {
  padding: 0 0.15rem;
  margin-bottom: 0.52rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.result-head p {
  margin: 0;
  font-size: 0.8rem;
}

.result-count {
  display: flex;
  align-items: center;
  gap: 0.38rem;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.6rem;
  padding: 0.1rem 0.38rem;
  border-radius: 999px;
  background: var(--ds-color-action-primary-soft, var(--accent-green20));
  color: var(--ds-color-text-primary, var(--ink-800));
  font-weight: 700;
  font-size: 0.78rem;
}

.error-text {
  color: var(--danger, #c0392b);
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.retry-btn {
  border-radius: 999px;
  border: 1px solid var(--danger, #c0392b);
  background: transparent;
  color: var(--danger, #c0392b);
  padding: 0.3rem 0.75rem;
  font-family: inherit;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.retry-btn:hover {
  background: var(--danger, #c0392b);
  color: var(--ds-color-status-danger-foreground, #fff);
}
.retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── لیست آیتم‌ها ─── */
.item-list {
  display: grid;
  gap: 0.56rem;
}

.menu-groups { display: grid; gap: clamp(2rem, 4vw, 3rem); }
.menu-category-section { display: grid; gap: 1rem; min-width: 0; }
.menu-category-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: .75rem;
  padding: .9rem 1rem;
  border: 1px solid var(--ds-color-border);
  border-radius: 18px;
  background: var(--ds-color-surface-raised);
}
.menu-category-head small { color: var(--ds-color-text-muted); font-size: .73rem; }
.menu-category-head h2 { margin: .15rem 0 0; font-size: clamp(1.1rem, 2.5vw, 1.45rem); line-height: 1.4; }
.menu-category-head > span { color: var(--ds-color-text-secondary); font-size: .75rem; white-space: nowrap; }

.subcategory-block {
  display: grid;
  gap: 0.65rem;
}

.subcategory-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0 0.15rem;
}

.subcategory-head h3 {
  margin: 0;
  font-size: 0.96rem;
  color: var(--text-primary, #172521);
}

.subcategory-head small {
  color: var(--text-muted, #7a6e64);
  font-size: 0.72rem;
}

/* ─── اسکلتون ─── */
.skeleton-card {
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.7);
  display: flex;
  gap: 0.7rem;
  padding: 0.7rem;
}

.skeleton-img {
  width: 82px;
  height: 82px;
  border-radius: 14px;
  flex-shrink: 0;
}

.skeleton-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.3rem;
}

.skeleton-line {
  height: 0.9rem;
  border-radius: 6px;
}

.skeleton-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.skeleton-btn {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 999px;
}

.shimmer {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  background-size: 200% 100%;
  animation: shimmerAnim 1.5s infinite;
}

@keyframes shimmerAnim {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* ─── حالت خالی ─── */
.empty-box {
  text-align: center;
  padding: 2rem 1rem;
  display: grid;
  gap: 0.4rem;
  justify-items: center;
}

.empty-icon {
  font-size: 2.2rem;
  margin-bottom: 0.2rem;
}

.empty-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #172521);
}

.reset-btn {
  margin-top: 0.5rem;
  border-radius: 999px;
  min-height: 44px;
  border: 1px solid var(--ds-color-border, var(--accent-green40));
  background: var(--ds-color-action-primary-soft, var(--accent-green20));
  color: var(--ds-color-action-primary, var(--ink-800));
  padding: 0.46rem 1rem;
  font-family: inherit;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.18s ease;
}

.reset-btn:hover {
  background: var(--ds-color-action-accent-soft, var(--accent-green40));
}

.print-catalog {
  display: none;
}

/* ─── انیمیشن‌های transition ─── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media print {
  @page {
    size: A4;
    margin: 12mm;
  }

  :global(html),
  :global(body) {
    margin: 0 !important;
    padding: 0 !important;
    background: #fff !important;
  }

  :global(.app-header),
  :global(.app-footer),
  :global(.mobile-bottom-nav),
  :global(.liquid-backdrop > .blob),
  :global(.header-surface),
  :global(.header-inner),
  :global(.mobile-overlay),
  :global(.mobile-sheet) {
    display: none !important;
  }

  :global(.app-main) {
    padding-top: 0 !important;
  }

  .menu-shell {
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  .menu-shell > :not(.print-catalog) {
    display: none !important;
  }

  .print-catalog {
    display: block !important;
    color: #111;
    direction: rtl;
  }

  .print-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.45rem;
  }

  .print-card {
    border: 1px solid #d8d8d8;
    border-radius: 8px;
    padding: 0.4rem;
    min-height: 115px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .print-card h3 {
    margin: 0;
    font-size: 0.8rem;
    color: #111;
    line-height: 1.45;
  }

  .print-card p {
    margin: 0.2rem 0 0.35rem;
    font-size: 0.68rem;
    color: #555;
    line-height: 1.5;
    flex: 1;
    overflow: hidden;
  }

  .print-card strong {
    display: block;
    margin-top: auto;
    font-size: 0.78rem;
    color: #111;
  }

  .print-empty {
    margin: 1rem 0;
    font-size: 0.82rem;
  }

  @media (max-width: 1000px) {
    .print-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
}

/* ─── ریسپانسیو ─── */
@media (min-width: 760px) {
.menu-shell {
    width: min(1180px, calc(100% - 1rem));
  }

  .menu-toolbar,
  .tag-filter-row {
    width: min(1180px, calc(100% - 1rem));
  }

  .item-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .skeleton-card {
    flex-direction: column;
    padding: 0;
  }

  .skeleton-img {
    width: 100%;
    height: 160px;
    border-radius: 0;
  }

  .skeleton-body {
    padding: 0.7rem;
  }
}

@media (max-width: 640px) {
  .menu-shell {
    width: calc(100% - 0.8rem);
    padding-inline: 0.4rem;
  }

  .menu-toolbar,
  .tag-filter-row {
    width: calc(100% - 0.8rem);
  }


}

@media (min-width: 1100px) {
  .item-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

/* دکمه فلش رو به بالا */
.scroll-top-btn {
  position: fixed;
  bottom: 1.25rem;
  right: 1.2rem;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 0;
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--ds-shadow-sm);
  opacity: 0;
  transform: translateY(12px) scale(0.85);
  transition: opacity 0.3s ease, transform 0.3s ease, background 0.2s ease;
  z-index: 120;
  pointer-events: none;
}
.scroll-top-btn.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.scroll-top-btn:hover {
  background: var(--ds-color-action-primary-soft);
  transform: translateY(-2px) scale(1.08);
  box-shadow: var(--ds-shadow-sm);
}
.scroll-top-btn:active {
  transform: scale(0.95);
}

@media (max-width: 919px) {
  .menu-shell {
    padding-bottom: max(7rem, calc(7rem + env(safe-area-inset-bottom)));
  }

  .scroll-top-btn {
    bottom: calc(5.5rem + env(safe-area-inset-bottom));
  }
}

.menu-page-root :deep(a:focus-visible),
.menu-page-root :deep(button:focus-visible) {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  .menu-page-root :deep(*) {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
