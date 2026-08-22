<template>
  <div class="menu-page-root">
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

    <div class="menu-toolbar">
      <button class="sort-toggle" type="button" @click="toggleSortMenu" :aria-expanded="sortMenuOpen ? 'true' : 'false'">
        <ChevronDown :size="16" />
        <span>{{ activeSortLabel }}</span>
      </button>
      <div class="sort-menu" v-if="sortMenuOpen">
        <button
          v-for="option in sortOptions"
          :key="option.value"
          type="button"
          :class="{ active: sortMode === option.value }"
          @click="setSortMode(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <!-- فیلتر تگ‌ها -->
    <div class="tag-filter-row" v-if="availableTags.length">
      <button
        class="tag-filter-btn"
        :class="{ active: !selectedTag }"
        @click="selectedTag = ''"
      >همه</button>
      <button
        v-for="tag in availableTags"
        :key="tag"
        class="tag-filter-btn"
        :class="{ active: selectedTag === tag }"
        @click="selectedTag = selectedTag === tag ? '' : tag"
      >{{ tag }}</button>
    </div>

    <LiquidGlassBackdrop>
    <section class="page-shell menu-shell">
      <OrderContextStrip :currency="currency" />

      <section class="item-section-list" v-if="highlightedItems.length">
        <article class="subcategory-block">
          <header class="subcategory-head">
            <h3>{{ highlightedTitle }}</h3>
            <small>{{ highlightedItems.length }} آیتم</small>
          </header>

          <div class="item-list">
            <MenuProductCard
              v-for="(item, idx) in highlightedItems"
              :key="`highlight-${item.slug || idx}`"
              :item="resolveDisplayItem(item)"
              :currency="currency"
              :theme="menuCardTheme"
              :cart-qty="getItemCartQty(item)"
              :can-view-bom="canViewBom"
              class="product-card-anim"
              :style="{ animationDelay: `${Math.min(idx, 8) * 40}ms` }"
              @quick-add="quickAdd"
              @quick-increase="quickIncrease"
              @quick-decrease="quickDecrease"
              @bom-preview="openBomModal"
            />
          </div>
        </article>
      </section>

      <!-- سربرگ نتایج -->
      <section class="result-head" ref="resultHeadRef">
        <transition name="fade" mode="out-in">
          <p class="muted result-count" v-if="!loading" key="count">
            <span class="count-badge">{{ pagination.total }}</span>
            محصول آماده سفارش
          </p>
          <p class="muted" v-else key="loading-text">در حال بارگذاری...</p>
        </transition>
        <p class="muted error-text" v-if="error">
          {{ error }}
          <button class="retry-btn" @click="reloadItems(1)" :disabled="loading">تلاش مجدد</button>
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

      <!-- لیست محصولات (دسته‌بندی بر اساس زیردسته) -->
      <section class="item-section-list" v-if="showSubcategorySections && groupedSections.length">
        <article
          v-for="section in groupedSections"
          :key="section.anchorKey"
          class="subcategory-block"
          :ref="(el) => setSubcategorySectionRef(section.anchorKey, el)"
        >
          <header class="subcategory-head">
            <h3>{{ section.title }}</h3>
            <small>{{ section.items.length }} آیتم</small>
          </header>

          <div class="item-list">
            <MenuProductCard
              v-for="(item, idx) in section.items"
              :key="item.slug"
              :item="item"
              :currency="currency"
              :theme="menuCardTheme"
              :cart-qty="getItemCartQty(item)"
              :can-view-bom="canViewBom"
              class="product-card-anim"
              :style="{ animationDelay: `${Math.min(idx, 8) * 55}ms` }"
              @quick-add="quickAdd"
              @quick-increase="quickIncrease"
              @quick-decrease="quickDecrease"
              @bom-preview="openBomModal"
            />
          </div>
        </article>

        <!-- اسکلتون برای لود بیشتر (infinite scroll) -->
        <template v-if="loadingMore">
          <div class="item-list">
            <div class="skeleton-card" v-for="n in 4" :key="`group-more-${n}`">
              <div class="skeleton-img shimmer"></div>
              <div class="skeleton-body">
                <div class="skeleton-line shimmer" style="width: 60%"></div>
                <div class="skeleton-line shimmer" style="width: 40%; height: 0.65rem; margin-top: 0.3rem"></div>
                <div class="skeleton-footer">
                  <div class="skeleton-line shimmer" style="width: 30%"></div>
                  <div class="skeleton-btn shimmer"></div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </section>

      <!-- لیست محصولات (حالت ساده) -->
      <section class="item-list" v-else-if="displayItems.length">
        <MenuProductCard
          v-for="(item, idx) in displayItems"
          :key="item.slug"
          :item="item"
          :currency="currency"
          :theme="menuCardTheme"
          :cart-qty="getItemCartQty(item)"
          :can-view-bom="canViewBom"
          class="product-card-anim"
          :style="{ animationDelay: `${Math.min(idx, 8) * 55}ms` }"
          @quick-add="quickAdd"
          @quick-increase="quickIncrease"
          @quick-decrease="quickDecrease"
          @bom-preview="openBomModal"
        />

        <!-- اسکلتون برای لود بیشتر (infinite scroll) -->
        <template v-if="loadingMore">
          <div class="skeleton-card" v-for="n in 4" :key="`more-${n}`">
            <div class="skeleton-img shimmer"></div>
            <div class="skeleton-body">
              <div class="skeleton-line shimmer" style="width: 60%"></div>
              <div class="skeleton-line shimmer" style="width: 40%; height: 0.65rem; margin-top: 0.3rem"></div>
              <div class="skeleton-footer">
                <div class="skeleton-line shimmer" style="width: 30%"></div>
                <div class="skeleton-btn shimmer"></div>
              </div>
            </div>
          </div>
        </template>
      </section>

      <button
        v-if="displayItems.length && nextCategoryMeta"
        type="button"
        class="next-category-card"
        :class="{ 'next-category-card--image': nextCategoryMeta.image }"
        @click="goToNextCategory"
      >
        <template v-if="nextCategoryMeta.image">
          <span class="next-category-card__media-full">
            <img :src="nextCategoryMeta.image" :alt="nextCategoryMeta.title" />
          </span>
          <span class="next-category-card__overlay"></span>
          <span class="next-category-card__copy next-category-card__copy--overlay">
            <strong>{{ nextCategoryMeta.title }}</strong>
            <small>{{ nextCategoryMeta.subtitle }}</small>
          </span>
          <span class="next-category-card__cta next-category-card__cta--overlay">{{ nextCategoryMeta.actionLabel }}</span>
        </template>
        <template v-else>
          <span class="next-category-card__media next-category-card__media--icon">
            <component :is="nextCategoryMeta.icon" :size="20" stroke-width="2.1" />
          </span>
          <span class="next-category-card__copy">
            <strong>{{ nextCategoryMeta.title }}</strong>
            <small>{{ nextCategoryMeta.subtitle }}</small>
          </span>
          <span class="next-category-card__cta">{{ nextCategoryMeta.actionLabel }}</span>
        </template>
      </button>

      <!-- نقطه تشخیص برای infinite scroll -->
      <div ref="infiniteAnchor" class="infinite-anchor"></div>

      <!-- حالت خالی -->
      <transition name="fade">
        <LiquidGlassCard class="empty-box" v-if="!loading && !displayItems.length && !error">
          <Utensils class="empty-icon" :size="34" stroke-width="1.8" />
          <p class="empty-title">{{ emptyStateTitle }}</p>
          <p class="muted">{{ emptyStateMessage }}</p>
          <button class="reset-btn" @click="resetFilters">{{ emptyStateAction }}</button>
        </LiquidGlassCard>
      </transition>

      <!-- سبد سفارش شناور -->
      <transition name="cart-pop">
        <a class="sticky-cart" href="/cart" v-if="cartCount > 0">
          <div class="cart-info">
            <span class="cart-icon"><ShoppingCart :size="20" stroke-width="2" /></span>
            <div>
              <small>سبد سفارش</small>
              <strong>{{ cartCount }} آیتم</strong>
            </div>
          </div>
          <div class="cart-price">
            <strong>{{ formatMoney(cartTotal, currency) }}</strong>
            <span class="cart-arrow">←</span>
          </div>
        </a>
      </transition>

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
import { ChevronDown, ChevronsUp, ShoppingCart, Utensils } from 'lucide-vue-next'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import LiquidGlassCard from '@/components/LiquidGlassCard.vue'
import CategoryImageRail from '@/components/CategoryImageRail.vue'
import MenuProductCard from '@/components/MenuProductCard.vue'
import MenuQuickAddSheet from '@/components/MenuQuickAddSheet.vue'
import BomPreviewModal from '@/components/BomPreviewModal.vue'
import ProductBuilderWizard from '@/components/ProductBuilderWizard.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { getMenuItems, getManagementSessionProfile, getBuilderTemplate, computeBuilderPrice } from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { getMenuIconComponent } from '@/utils/menuIcons'
import { cartState, cartSubtotal, upsertLine, removeLine } from '@/stores/cartStore'

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
const menuHighlight = ref(
  props.boot.menu_highlight || {
    enabled: 0,
    title: 'ویژه و پرفروش',
    per_category_limit: 3,
    category_items: {},
    items: [],
  },
)
const items = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
const selectedTag = ref('')
const sortMode = ref('default')
const sortMenuOpen = ref(false)
const selectedCategorySlug = ref(categories.value[0]?.slug || '')
const selectedSubcategorySlug = ref('')

// Flag to track if URL category was applied
let urlCategoryApplied = false
const allLoaded = ref(false)
const infiniteAnchor = ref(null)
const resultHeadRef = ref(null)
const subcategorySectionRefs = ref({})
let intersectionObserver = null
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
      scrollTicking = false
    })
    scrollTicking = true
  }
}

function handleResize() {
  railOffsetTop = railRef.value?.offsetTop || 0
  syncHeaderOffset()
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

const pagination = ref({
  page: 1,
  page_size: 12,
  total: 0,
  total_pages: 0,
})

// ─── computed ───────────────────────────────────────────────────────
const menuCardTheme = computed(() => {
  const theme = props.boot?.theme && typeof props.boot.theme === 'object' ? props.boot.theme : {}
  return {
    primary_color: theme.primary_color || props.boot?.primary_color || 'var(--accent-gold)',
    primary_color_dark: theme.primary_color_dark || props.boot?.primary_color_dark || 'var(--accent-gold80)',
    accent_color: theme.accent_color || props.boot?.accent_color || 'var(--accent-green)',
    surface: theme.surface || 'var(--pos-surface-color, #ffffff)',
    surface_alt: theme.surface_alt || 'var(--theme-surface-alt)',
    border: theme.border || 'var(--glass-border)',
    text_primary: theme.text_primary || 'var(--text-primary)',
    text_secondary: theme.text_secondary || 'var(--text-secondary)',
    text_muted: theme.text_muted || 'var(--text-muted)',
    add_btn_bg: theme.add_btn_bg || theme.accent_color || props.boot?.accent_color || 'var(--accent-gold)',
  }
})
const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))
const cartTotal = computed(() => cartSubtotal())
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
const activeCategoryIndex = computed(() => categories.value.findIndex((row) => row.slug === selectedCategorySlug.value))

function resolveCategoryIcon(category = null) {
  if (!category) {
    return Utensils
  }
  return getMenuIconComponent(category.menu_icon || '', Utensils) || Utensils
}

const nextCategoryMeta = computed(() => {
  const rows = Array.isArray(categories.value) ? categories.value : []
  const currentIndex = activeCategoryIndex.value
  if (!rows.length || currentIndex < 0) {
    return null
  }

  if (rows.length === 1) {
    return {
      kind: 'top',
      slug: rows[0]?.slug || '',
      title: 'بازگشت به ابتدای منو',
      subtitle: 'برای مرور دوباره همین گروه به بالا برگردید.',
      actionLabel: 'رفتن به بالا',
      icon: ChevronsUp,
      image: '',
    }
  }

  const isLast = currentIndex >= rows.length - 1
  if (isLast) {
    const firstCategory = rows[0]
    return {
      kind: 'restart',
      slug: String(firstCategory?.slug || '').trim(),
      title: `بعدی: ${String(firstCategory?.title || 'اولین گروه').trim()}`,
      subtitle: 'به ابتدای مسیر گروه‌ها برگردید و منو را ادامه دهید.',
      actionLabel: 'شروع دوباره',
      icon: resolveCategoryIcon(firstCategory),
      image: String(firstCategory?.image || '').trim(),
    }
  }

  const nextCategory = rows[currentIndex + 1]
  return {
    kind: 'next',
    slug: String(nextCategory?.slug || '').trim(),
    title: `گروه بعدی: ${String(nextCategory?.title || 'گروه بعدی').trim()}`,
    subtitle: `${Number(nextCategory?.item_count || 0).toLocaleString('fa-IR')} آیتم دیگر برای دیدن دارید.`,
    actionLabel: 'نمایش گروه',
    icon: resolveCategoryIcon(nextCategory),
    image: String(nextCategory?.image || '').trim(),
  }
})

const highlightedItems = computed(() => {
  const payload = menuHighlight.value || {}
  if (Number(payload.enabled || 0) !== 1) {
    return []
  }
  const activeSlug = String(selectedCategorySlug.value || '').trim()
  const categoryMap = payload?.category_items && typeof payload.category_items === 'object' ? payload.category_items : {}
  const rows = Array.isArray(categoryMap[activeSlug]) ? categoryMap[activeSlug] : []
  const seen = new Set()
  return rows.filter((row) => {
    const slug = String(row?.slug || '').trim()
    const key = slug || String(row?.name || '').trim()
    if (!key || seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
})
const highlightedTitle = computed(() => String(menuHighlight.value?.title || 'ویژه و پرفروش').trim() || 'ویژه و پرفروش')
const currentSubcategories = computed(() => {
  const rows = []
  const bySlug = new Map()
  const byTitle = new Map()

  function registerSubcategory(row, fallbackSortOrder = 9999) {
    const title = String(row?.title || '').trim()
    const rawSlug = String(row?.slug || '').trim()
    const normalizedTitle = normalizeSubcategoryToken(title)
    const slug = rawSlug || buildSyntheticSubcategorySlug(normalizedTitle)
    if (!slug) {
      return null
    }

    const existing = bySlug.get(slug)
    if (existing) {
      if (!existing.title && title) {
        existing.title = title
      }
      return existing
    }

    const sortOrder = Number(row?.sort_order)
    const next = {
      slug,
      title: title || 'زیردسته',
      sort_order: Number.isFinite(sortOrder) ? sortOrder : fallbackSortOrder,
      item_count: Number(row?.item_count || 0),
    }

    rows.push(next)
    bySlug.set(slug, next)
    if (normalizedTitle && !byTitle.has(normalizedTitle)) {
      byTitle.set(normalizedTitle, next)
    }
    return next
  }

  for (const sub of activeCategory.value?.subcategories || []) {
    registerSubcategory(sub, Number(sub?.sort_order || 0))
  }

  for (const item of displayItems.value) {
    const itemSlug = String(item?.subcategory_slug || '').trim()
    const itemTitle = String(item?.subcategory_title || item?.subcategory || '').trim()
    const itemTitleToken = normalizeSubcategoryToken(itemTitle)
    if (!itemSlug && !itemTitleToken) {
      continue
    }
    if (itemSlug && bySlug.has(itemSlug)) {
      continue
    }

    const matchedByTitle = itemTitleToken ? byTitle.get(itemTitleToken) : null
    if (matchedByTitle) {
      if (itemSlug && !bySlug.has(itemSlug)) {
        bySlug.set(itemSlug, matchedByTitle)
      }
      continue
    }

    const added = registerSubcategory(
      {
        slug: itemSlug,
        title: itemTitle,
      },
      9999,
    )

    if (added && itemSlug && !bySlug.has(itemSlug)) {
      bySlug.set(itemSlug, added)
    }
  }

  return rows.sort((left, right) => {
    const leftSort = Number(left?.sort_order || 0)
    const rightSort = Number(right?.sort_order || 0)
    if (leftSort !== rightSort) {
      return leftSort - rightSort
    }
    return String(left?.title || '').localeCompare(String(right?.title || ''), 'fa')
  })
})
const showSubcategorySections = computed(() => currentSubcategories.value.length > 0)
const groupedSections = computed(() => {
  if (!showSubcategorySections.value) {
    return []
  }

  const sectionMap = new Map()
  const sectionByTitle = new Map()
  for (const sub of currentSubcategories.value) {
    const slug = String(sub.slug || '').trim()
    if (!slug) {
      continue
    }
    const normalizedTitle = normalizeSubcategoryToken(sub.title)
    const section = {
      slug,
      title: sub.title || 'زیردسته',
      anchorKey: getSubcategoryAnchorKey(slug),
      items: [],
    }
    sectionMap.set(slug, section)
    if (normalizedTitle && !sectionByTitle.has(normalizedTitle)) {
      sectionByTitle.set(normalizedTitle, section)
    }
  }

  const miscSection = {
    slug: '',
    title: 'سایر موارد',
    anchorKey: getSubcategoryAnchorKey('misc'),
    items: [],
  }

  for (const item of displayItems.value) {
    const slug = String(item.subcategory_slug || '').trim()
    const titleToken = normalizeSubcategoryToken(item.subcategory_title || item.subcategory)
    const section = (slug ? sectionMap.get(slug) : null) || (titleToken ? sectionByTitle.get(titleToken) : null)
    if (section) {
      section.items.push(item)
      continue
    }
    miscSection.items.push(item)
  }

  const ordered = Array.from(sectionMap.values()).filter((row) => row.items.length > 0)
  if (miscSection.items.length) {
    ordered.push(miscSection)
  }
  return ordered.map((section) => ({
    ...section,
    items: sortItems(section.items),
  }))
})

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

function normalizeSubcategoryToken(value) {
  return String(value || '').trim().toLowerCase()
}

function buildSyntheticSubcategorySlug(normalizedTitle) {
  const token = String(normalizedTitle || '').trim()
  return token ? `name:${token}` : ''
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

watch(selectedTag, () => {
  // Scroll to top of results when tag filter changes
  scrollElementIntoMenuView(resultHeadRef.value)
})

// ─── بارگذاری آیتم‌ها ──────────────────────────────────────────────
async function fetchMenuPage(page = 1, pageSize = 12) {
  return getMenuItems({
    category_slug: selectedCategorySlug.value,
    subcategory_slug: '',
    search: '',
    page,
    page_size: pageSize,
    branch: activeBranch.value,
  })
}

async function loadCategoryCatalog() {
  const pageSize = 100
  let page = 1
  let totalPages = 1
  const collected = []
  const seen = new Set()
  let lastPagination = {
    page: 1,
    page_size: pageSize,
    total: 0,
    total_pages: 1,
  }

  while (page <= totalPages && page <= 200) {
    const data = await fetchMenuPage(page, pageSize)
    const rows = Array.isArray(data?.items) ? data.items : []
    for (const row of rows) {
      const key = String(row?.slug || row?.name || '').trim()
      if (!key || seen.has(key)) {
        continue
      }
      seen.add(key)
      collected.push(row)
    }

    const paginationPayload = data?.pagination || {}
    const nextTotalPages = Number(paginationPayload.total_pages || 1)
    totalPages = Number.isFinite(nextTotalPages) && nextTotalPages > 0 ? nextTotalPages : 1
    lastPagination = {
      page,
      page_size: pageSize,
      total: Number(paginationPayload.total || collected.length) || collected.length,
      total_pages: totalPages,
    }
    page += 1
  }

  return {
    items: collected,
    pagination: lastPagination,
  }
}

async function reloadItems(page = 1) {
  if (page === 1) {
    loading.value = true
    items.value = []
    subcategorySectionRefs.value = {}
    allLoaded.value = false
  } else {
    loadingMore.value = true
  }
  error.value = ''

  try {
    const data = page === 1 ? await loadCategoryCatalog() : await fetchMenuPage(page, 12)

    const newItems = data.items || []
    if (page === 1) {
      items.value = newItems
      allLoaded.value = true
    } else {
      items.value = [...items.value, ...newItems]
      allLoaded.value = pagination.value.page >= pagination.value.total_pages
    }

    pagination.value = data.pagination || pagination.value
    if (page !== 1) {
      allLoaded.value = pagination.value.page >= pagination.value.total_pages
    }
  } catch (err) {
    error.value = err.message || 'دریافت منو ناموفق بود.'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// ─── infinite scroll ────────────────────────────────────────────────
let scrollLoadLock = false

function setupIntersectionObserver() {
  if (!infiniteAnchor.value) return

  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }

  scrollLoadLock = false

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (
        entry.isIntersecting &&
        !loading.value &&
        !loadingMore.value &&
        !allLoaded.value &&
        !scrollLoadLock
      ) {
        scrollLoadLock = true
        reloadItems(pagination.value.page + 1).finally(() => {
          scrollLoadLock = false
        })
      }
    },
    { rootMargin: '300px' },
  )
  intersectionObserver.observe(infiniteAnchor.value)
}

// ─── دسته‌بندی ──────────────────────────────────────────────────────
async function goToCategory(slug, { scrollTarget = 'top' } = {}) {
  const cleanSlug = String(slug || '').trim()
  if (!cleanSlug) {
    return
  }

  if (selectedCategorySlug.value === cleanSlug) {
    if (scrollTarget === 'results') {
      await nextTick()
      scrollElementIntoMenuView(resultHeadRef.value)
    } else {
      scrollToTop()
    }
    return
  }

  selectedCategorySlug.value = cleanSlug
  selectedSubcategorySlug.value = ''
  selectedTag.value = ''
  sortMenuOpen.value = false
  await reloadItems(1)
  await nextTick()

  if (scrollTarget === 'results') {
    scrollElementIntoMenuView(resultHeadRef.value)
    return
  }

  if (window.scrollY > 0) {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function selectCategory(slug) {
  if (selectedCategorySlug.value === slug) return
  void goToCategory(slug, { scrollTarget: 'top' })
}

function goToNextCategory() {
  const next = nextCategoryMeta.value
  if (!next) {
    return
  }
  if (next.kind === 'top') {
    scrollToTop()
    return
  }
  void goToCategory(next.slug, { scrollTarget: 'results' })
}

function getSubcategoryAnchorKey(slug) {
  const cleanSlug = String(slug || '').trim()
  return cleanSlug ? `subcategory-${cleanSlug}` : 'subcategory-misc'
}

function setSubcategorySectionRef(anchorKey, element) {
  if (!anchorKey) return
  if (element) {
    subcategorySectionRefs.value[anchorKey] = element
    return
  }
  delete subcategorySectionRefs.value[anchorKey]
}

async function scrollToSubcategory(slug) {
  const anchorKey = getSubcategoryAnchorKey(slug)
  await nextTick()

  let guard = 0
  while (!subcategorySectionRefs.value[anchorKey] && !allLoaded.value && guard < 12) {
    guard += 1
    await reloadItems(pagination.value.page + 1)
    await nextTick()
  }

  const target = subcategorySectionRefs.value[anchorKey]
  if (target) {
    scrollElementIntoMenuView(target)
  }
}

async function selectSubcategory(slug) {
  const cleanSlug = String(slug || '').trim()
  selectedSubcategorySlug.value = cleanSlug

  if (!cleanSlug) {
    scrollElementIntoMenuView(resultHeadRef.value)
    return
  }

  await scrollToSubcategory(cleanSlug)
}

function resetFilters() {
  selectedTag.value = ''
  selectedCategorySlug.value = categories.value[0]?.slug || ''
  selectedSubcategorySlug.value = ''
  reloadItems(1)
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

function resolveDisplayItem(item = {}) {
  const slug = String(item?.slug || '').trim()
  const fromList = slug ? itemsBySlug.value.get(slug) : null
  if (fromList) {
    return fromList
  }
  return item || {}
}

function isComingSoonItem(item = {}) {
  return Number(item?.coming_soon ?? item?.restaurant_coming_soon ?? 0) === 1
}

function isStockOutItem(item = {}) {
  return Number(item?.stock_out || 0) === 1
}

// ─── افزودن سریع به سبد ────────────────────────────────────────────
function quickAdd(item) {
  if (isComingSoonItem(item) || isStockOutItem(item)) {
    return
  }
  if (itemHasBuilder(item)) {
    openBuilderWizard(item)
    return
  }
  if (!itemHasCustomization(item)) {
    addSimpleLine(item, 1)
    return
  }
  quickSheetItem.value = item
  quickSheetOpen.value = true
}

function quickIncrease(item) {
  if (isComingSoonItem(item) || isStockOutItem(item)) {
    return
  }
  if (itemHasBuilder(item) || itemHasCustomization(item)) {
    quickAdd(item)
    return
  }
  addSimpleLine(item, 1)
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
  closeQuickSheet()
}

// ─── lifecycle ──────────────────────────────────────────────────────
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  try {
    const profile = await getManagementSessionProfile()
    canViewBom.value = Boolean(profile?.is_staff || profile?.is_admin)
  } catch (_) {
    canViewBom.value = false
  }

  // Apply category from URL query parameter
  const urlCategory = new URLSearchParams(window.location.search).get('category')
  if (urlCategory && !urlCategoryApplied) {
    const matched = categories.value.find((c) => c.slug === urlCategory)
    if (matched && selectedCategorySlug.value !== matched.slug) {
      selectedCategorySlug.value = matched.slug
      selectedSubcategorySlug.value = ''
      urlCategoryApplied = true
    }
  }

  const highlightPayload = props.boot.menu_highlight || {}
  menuHighlight.value = {
    enabled: Number(highlightPayload.enabled || 0) ? 1 : 0,
    title: String(highlightPayload.title || 'ویژه و پرفروش').trim() || 'ویژه و پرفروش',
    per_category_limit: Number(highlightPayload.per_category_limit || 3) || 3,
    category_items:
      highlightPayload.category_items && typeof highlightPayload.category_items === 'object'
        ? highlightPayload.category_items
        : {},
    items: Array.isArray(highlightPayload.items) ? highlightPayload.items : [],
  }
  await reloadItems(1)
  printCards.value = items.value.filter((row) => isPrintableItem(row))
  setupIntersectionObserver()
  window.addEventListener('keydown', handlePrintShortcut)
  window.addEventListener('scroll', onScroll)
  window.addEventListener('resize', handleResize)
  // Capture rail offset after DOM is ready
  nextTick(() => {
    railOffsetTop = railRef.value?.offsetTop || 0
    syncHeaderOffset()
  })
})

onUnmounted(() => {
  intersectionObserver?.disconnect()
  window.removeEventListener('keydown', handlePrintShortcut)
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', handleResize)
  document.documentElement.style.setProperty('--menu-header-offset', '0px')
})
</script>

<style scoped>
.menu-shell {
  width: min(540px, calc(100% - 1rem));
  margin: 0 auto;
  padding: 0 0.5rem max(6.5rem, calc(6.5rem + env(safe-area-inset-bottom)));
}

/* ─── Sticky Rail (JS-based because overflow:hidden ancestors break CSS sticky) ─── */
.category-rail-sticky {
  position: relative;
  z-index: 100;
  background: var(--theme-background, #f6f1ea);
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
    top: 3.3rem;
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
  min-height: 32px;
  padding: 0 0.62rem;
  border-radius: 12px;
  border: 1px solid var(--glass-border);
  background: #fff;
  color: var(--text-secondary);
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
  border: 1px solid var(--glass-border);
  background: #fff;
  box-shadow: 0 12px 24px rgb(15 23 42 / 0.10);
}

.sort-menu button {
  border: 0;
  background: transparent;
  border-radius: 9px;
  padding: 0.4rem 0.52rem;
  text-align: right;
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
}

.sort-menu button.active,
.sort-menu button:hover {
  background: var(--accent-green20);
  color: var(--accent-green);
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
  background: var(--glass-bg, #fdf8f1);
  border: 1px solid var(--glass-border, #d5c3af);
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.78rem;
  color: var(--text-secondary, #654a38);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tag-filter-btn:hover {
  border-color: var(--accent-green, #6f4a31);
  color: var(--accent-green, #6f4a31);
}

.tag-filter-btn.active {
  background: var(--accent-green, #6f4a31);
  border-color: var(--accent-green, #6f4a31);
  color: #fff;
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
  background: var(--accent-green20);
  color: var(--ink-800);
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
  color: #fff;
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

.item-section-list {
  display: grid;
  gap: 0.72rem;
}

.subcategory-block {
  display: grid;
  gap: 0.48rem;
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

.product-card-anim {
  animation: cardReveal 0.4s ease both;
}

.next-category-card {
  width: 100%;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.28rem;
  padding: 0.88rem 0.9rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--text-primary, #172521);
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  text-align: right;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.next-category-card--image {
  position: relative;
  grid-template-columns: 1fr;
  min-height: 168px;
  padding: 0;
  overflow: hidden;
  border-radius: 22px;
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.next-category-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
}

.next-category-card__media-full {
  position: absolute;
  inset: 0;
}

.next-category-card__media-full img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.next-category-card__overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgb(15 23 42 / 0.72) 0%, rgb(15 23 42 / 0.38) 45%, rgb(15 23 42 / 0.14) 100%),
    linear-gradient(180deg, rgb(15 23 42 / 0.04) 0%, rgb(15 23 42 / 0.45) 100%);
}

.next-category-card__media {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.next-category-card__media--icon {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.92);
}

.next-category-card__media--image {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.next-category-card__media--image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.next-category-card__copy {
  display: grid;
  gap: 0.16rem;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.next-category-card__copy strong {
  font-size: 0.88rem;
  line-height: 1.45;
}

.next-category-card__copy small {
  color: var(--text-muted, #7a6e64);
  font-size: 0.72rem;
  line-height: 1.5;
}

.next-category-card__copy--overlay {
  align-self: end;
  padding: 1rem 1rem 1.15rem;
  max-width: min(72%, 420px);
}

.next-category-card__copy--overlay strong {
  color: #fff;
  font-size: 1rem;
}

.next-category-card__copy--overlay small {
  color: rgb(255 255 255 / 0.82);
  font-size: 0.76rem;
}

.next-category-card__cta {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 0.82rem;
  border-radius: 999px;
  background: var(--accent-green20);
  color: var(--accent-green, #2f6f5c);
  font-size: 0.75rem;
  font-weight: 800;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.next-category-card__cta--overlay {
  position: absolute;
  left: 1rem;
  bottom: 1rem;
  background: rgba(255, 255, 255, 0.92);
  color: var(--text-primary, #172521);
  box-shadow: 0 8px 20px rgb(15 23 42 / 0.14);
}

@keyframes cardReveal {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  border: 1px solid var(--accent-green40);
  background: var(--accent-green20);
  color: var(--ink-800);
  padding: 0.46rem 1rem;
  font-family: inherit;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.18s ease;
}

.reset-btn:hover {
  background: var(--accent-green40);
}

/* ─── anchor برای infinite scroll ─── */
.infinite-anchor {
  height: 1px;
  margin-top: 0.5rem;
}

/* ─── سبد شناور ─── */
.sticky-cart {
  position: fixed;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  width: min(500px, calc(100% - 1rem));
  border-radius: 20px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow: 0 14px 34px rgb(15 23 42 / 0.12);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.72rem 1rem;
  z-index: 80;
  text-decoration: none;
  color: var(--text-primary);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sticky-cart:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 20px 44px rgb(15 23 42 / 0.16);
}

.cart-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.cart-icon {
  font-size: 1.2rem;
}

.cart-info small {
  display: block;
  color: var(--text-muted);
  font-size: 0.72rem;
}

.cart-info strong,
.cart-price strong {
  font-size: 0.9rem;
  color: var(--text-primary);
  display: block;
}

.cart-price {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cart-arrow {
  font-size: 1rem;
  color: var(--accent-green);
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

.cart-pop-enter-active {
  animation: cartPopIn 0.38s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.cart-pop-leave-active {
  animation: cartPopOut 0.25s ease forwards;
}

@keyframes cartPopIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes cartPopOut {
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(16px) scale(0.94);
  }
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
  :global(.sticky-cart),
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
    width: min(980px, 100%);
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

  .next-category-card {
    grid-template-columns: 38px minmax(0, 1fr);
    padding: 0.82rem 0.82rem 0.86rem;
  }

  .next-category-card--image {
    grid-template-columns: 1fr;
    min-height: 154px;
    padding: 0;
  }

  .next-category-card__cta {
    grid-column: 1 / -1;
    justify-content: center;
    margin-top: 0.15rem;
  }

  .next-category-card__copy--overlay {
    max-width: calc(100% - 1.6rem);
    padding: 0.95rem 0.9rem 1rem;
  }

  .next-category-card__cta--overlay {
    left: 0.75rem;
    bottom: 0.75rem;
    min-height: 34px;
    padding-inline: 0.72rem;
    margin-top: 0;
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
  bottom: 5rem;
  right: 1.2rem;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 0;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.35);
  opacity: 0;
  transform: translateY(12px) scale(0.85);
  transition: opacity 0.3s ease, transform 0.3s ease, background 0.2s ease;
  z-index: 9999;
  pointer-events: none;
}
.scroll-top-btn.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.scroll-top-btn:hover {
  background: var(--accent-green80, #6f4a31);
  transform: translateY(-2px) scale(1.08);
  box-shadow: 0 12px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.45);
}
.scroll-top-btn:active {
  transform: scale(0.95);
}
</style>
