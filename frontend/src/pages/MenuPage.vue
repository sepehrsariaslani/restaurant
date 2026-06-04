<template>
  <LiquidGlassBackdrop>
    <section class="page-shell menu-shell">

      <!-- هدر جستجو و برندینگ -->
      <MenuHeroHeader
        :branding="branding"
        :search="search"
        :cart-count="cartCount"
        @update:search="search = $event"
        @search="onSearchSubmit"
      />

      <!-- دسته‌بندی‌ها -->
      <CategoryPillRail
        :categories="categories"
        :selected-category="selectedCategorySlug"
        :subcategories="currentSubcategories"
        :selected-subcategory="selectedSubcategorySlug"
        :active-category-title="activeCategoryTitle"
        @select-category="selectCategory"
        @select-subcategory="selectSubcategory"
      />

      <section class="item-section-list" v-if="highlightedItems.length && !isSearchMode">
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
              :cart-qty="getItemCartQty(item)"
              class="product-card-anim"
              :style="{ animationDelay: `${Math.min(idx, 8) * 40}ms` }"
              @quick-add="quickAdd"
              @quick-increase="quickIncrease"
              @quick-decrease="quickDecrease"
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
        <p class="muted error-text" v-if="error">{{ error }}</p>
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
              :cart-qty="getItemCartQty(item)"
              class="product-card-anim"
              :style="{ animationDelay: `${Math.min(idx, 8) * 55}ms` }"
              @quick-add="quickAdd"
              @quick-increase="quickIncrease"
              @quick-decrease="quickDecrease"
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
      <section class="item-list" v-else-if="items.length">
        <MenuProductCard
          v-for="(item, idx) in items"
          :key="item.slug"
          :item="item"
          :currency="currency"
          :cart-qty="getItemCartQty(item)"
          class="product-card-anim"
          :style="{ animationDelay: `${Math.min(idx, 8) * 55}ms` }"
          @quick-add="quickAdd"
          @quick-increase="quickIncrease"
          @quick-decrease="quickDecrease"
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

      <!-- نقطه تشخیص برای infinite scroll -->
      <div ref="infiniteAnchor" class="infinite-anchor"></div>

      <!-- حالت خالی -->
      <transition name="fade">
        <LiquidGlassCard class="empty-box" v-if="!loading && !items.length && !error">
          <span class="empty-icon">🍽️</span>
          <p class="empty-title">محصولی پیدا نشد</p>
          <p class="muted">فیلترها یا جستجو را تغییر دهید</p>
          <button class="reset-btn" @click="resetFilters">پاک کردن فیلترها</button>
        </LiquidGlassCard>
      </transition>

      <!-- پیام پایان لیست -->
      <transition name="fade">
        <p class="end-label muted" v-if="!loading && !loadingMore && allLoaded && items.length">
          ✓ همه محصولات نمایش داده شدند
        </p>
      </transition>

      <!-- سبد سفارش شناور -->
      <transition name="cart-pop">
        <a class="sticky-cart" href="/cart" v-if="cartCount > 0">
          <div class="cart-info">
            <span class="cart-icon">🛒</span>
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

    </section>
  </LiquidGlassBackdrop>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import LiquidGlassBackdrop from '@/components/LiquidGlassBackdrop.vue'
import LiquidGlassCard from '@/components/LiquidGlassCard.vue'
import MenuHeroHeader from '@/components/MenuHeroHeader.vue'
import CategoryPillRail from '@/components/CategoryPillRail.vue'
import MenuProductCard from '@/components/MenuProductCard.vue'
import MenuQuickAddSheet from '@/components/MenuQuickAddSheet.vue'
import { getMenuItems } from '@/utils/api'
import { formatMoney } from '@/utils/format'
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
const currency = ref('TOMAN')
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
const search = ref('')
const searchDebounceTimer = ref(null)
const selectedCategorySlug = ref(categories.value[0]?.slug || '')
const selectedSubcategorySlug = ref('')
const allLoaded = ref(false)
const infiniteAnchor = ref(null)
const resultHeadRef = ref(null)
const subcategorySectionRefs = ref({})
let intersectionObserver = null
const quickSheetOpen = ref(false)
const quickSheetItem = ref(null)
const printPreparing = ref(false)
const printCards = ref([])

const pagination = ref({
  page: 1,
  page_size: 12,
  total: 0,
  total_pages: 0,
})

// ─── computed ───────────────────────────────────────────────────────
const branding = computed(
  () =>
    props.boot.branding || {
      name: 'رستوران',
      tagline: 'منوی آنلاین',
      hero_subtitle: 'روی هر آیتم بزن، مواد را تنظیم کن، سفارش ثبت کن.',
    },
)
const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))
const cartTotal = computed(() => cartSubtotal())
const isSearchMode = computed(() => Boolean(search.value.trim()))
const activeCategory = computed(() => categories.value.find((row) => row.slug === selectedCategorySlug.value) || null)
const activeCategoryTitle = computed(() => activeCategory.value?.title || 'دسته')
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
  if (isSearchMode.value) {
    return []
  }

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

  for (const item of items.value) {
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
const showSubcategorySections = computed(() => !isSearchMode.value && currentSubcategories.value.length > 0)
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

  for (const item of items.value) {
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
  return ordered
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

// ─── جستجو با debounce ─────────────────────────────────────────────
watch(search, (newVal) => {
  if (String(newVal || '').trim()) {
    selectedSubcategorySlug.value = ''
  }
  clearTimeout(searchDebounceTimer.value)
  searchDebounceTimer.value = setTimeout(() => {
    reloadItems(1)
  }, 420)
})

function onSearchSubmit() {
  clearTimeout(searchDebounceTimer.value)
  reloadItems(1)
}

// ─── بارگذاری آیتم‌ها ──────────────────────────────────────────────
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
    const query = search.value.trim()
    const searchMode = Boolean(query)
    const data = await getMenuItems({
      category_slug: searchMode ? '' : selectedCategorySlug.value,
      subcategory_slug: '',
      search: query,
      page,
      page_size: 12,
      branch: activeBranch.value,
    })

    const newItems = data.items || []
    if (page === 1) {
      items.value = newItems
    } else {
      items.value = [...items.value, ...newItems]
    }

    pagination.value = data.pagination || pagination.value
    allLoaded.value = pagination.value.page >= pagination.value.total_pages
  } catch (err) {
    error.value = err.message || 'دریافت منو ناموفق بود.'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// ─── infinite scroll ────────────────────────────────────────────────
function setupIntersectionObserver() {
  if (!infiniteAnchor.value) return

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry.isIntersecting && !loading.value && !loadingMore.value && !allLoaded.value) {
        reloadItems(pagination.value.page + 1)
      }
    },
    { rootMargin: '200px' },
  )
  intersectionObserver.observe(infiniteAnchor.value)
}

// ─── دسته‌بندی ──────────────────────────────────────────────────────
function selectCategory(slug) {
  if (selectedCategorySlug.value === slug && !isSearchMode.value) return
  selectedCategorySlug.value = slug
  selectedSubcategorySlug.value = ''
  reloadItems(1)
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
  if (target?.scrollIntoView) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

async function selectSubcategory(slug) {
  if (isSearchMode.value) return

  const cleanSlug = String(slug || '').trim()
  selectedSubcategorySlug.value = cleanSlug

  if (!cleanSlug) {
    resultHeadRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
    return
  }

  await scrollToSubcategory(cleanSlug)
}

function resetFilters() {
  search.value = ''
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

// ─── افزودن سریع به سبد ────────────────────────────────────────────
function quickAdd(item) {
  if (!itemHasCustomization(item)) {
    addSimpleLine(item, 1)
    return
  }
  quickSheetItem.value = item
  quickSheetOpen.value = true
}

function quickIncrease(item) {
  if (itemHasCustomization(item)) {
    quickAdd(item)
    return
  }
  addSimpleLine(item, 1)
}

function quickDecrease(item) {
  if (itemHasCustomization(item)) {
    return
  }
  removeSimpleLineQty(item, 1)
}

function closeQuickSheet() {
  quickSheetOpen.value = false
  quickSheetItem.value = null
}

function confirmQuickAdd(linePayload) {
  upsertLine({
    ...linePayload,
  })
  closeQuickSheet()
}

// ─── lifecycle ──────────────────────────────────────────────────────
onMounted(async () => {
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
})

onUnmounted(() => {
  intersectionObserver?.disconnect()
  clearTimeout(searchDebounceTimer.value)
  window.removeEventListener('keydown', handlePrintShortcut)
})
</script>

<style scoped>
.menu-shell {
  width: min(540px, calc(100% - 1rem));
  padding: 0.6rem 0.2rem 7rem;
}

/* ─── سربرگ نتایج ─── */
.result-head {
  padding: 0 0.2rem;
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
  padding: 0 0.2rem;
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

/* ─── پیام پایان لیست ─── */
.end-label {
  text-align: center;
  padding: 0.7rem;
  font-size: 0.78rem;
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
    width: min(980px, calc(100% - 2rem));
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

@media (min-width: 1100px) {
  .item-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
