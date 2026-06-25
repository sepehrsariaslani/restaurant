<template>
  <ManagementPageScaffold title="طراحی منو" subtitle="چیدمان دسته‌ها و محصولات را ببینید، جابه‌جا کنید و همان‌جا ویرایش کنید.">
    <template #actions>
      <span v-if="dirtyCount" class="dirty-chip">{{ dirtyCountLabel }}</span>
      <button class="secondary-btn" type="button" @click="loadDesigner" :disabled="loading || saving">
        {{ loading ? 'در حال بروزرسانی...' : 'تازه‌سازی' }}
      </button>
      <button class="primary-btn" type="button" @click="saveDesigner" :disabled="!dirtyCount || loading || saving">
        {{ saving ? 'در حال ذخیره...' : 'ذخیره چیدمان' }}
      </button>
    </template>

    <section class="designer-shell">
      <aside class="designer-panel structure-panel">
        <header class="panel-head">
          <div>
            <span class="eyebrow">ساختار</span>
            <h3>دسته‌ها</h3>
          </div>
          <span class="count-chip">{{ activeCategories.length.toLocaleString('fa-IR') }}</span>
        </header>

        <p v-if="loading" class="muted">در حال بارگذاری منو...</p>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>

        <div class="category-stack" v-if="!loading">
          <button
            v-for="category in activeCategories"
            :key="category.name"
            class="category-row"
            :class="{ active: selectedCategoryName === category.name, dragging: dragState.id === category.name }"
            type="button"
            :data-reorder-kind="'category'"
            :data-reorder-id="category.name"
            @click="selectCategory(category.name)"
            @dragover.prevent
            @drop.prevent="dropReorder('category', category.name)"
          >
            <span
              class="drag-handle"
              role="button"
              tabindex="0"
              aria-label="جابجایی دسته"
              draggable="true"
              @dragstart.stop="startHtmlDrag('category', category.name)"
              @dragend="clearDrag"
              @pointerdown.stop.prevent="startPointerDrag('category', category.name, $event)"
              @keydown.up.prevent="moveCategory(category.name, -1)"
              @keydown.down.prevent="moveCategory(category.name, 1)"
            >
              <GripVerticalIcon :size="17" />
            </span>
            <span class="category-copy">
              <strong>{{ category.item_group_name || category.name }}</strong>
              <small>{{ productCountByCategory(category.name).toLocaleString('fa-IR') }} محصول</small>
            </span>
            <span class="order-badge">{{ resolveCategoryIndex(category.name).toLocaleString('fa-IR') }}</span>
          </button>
        </div>
      </aside>

      <main class="designer-preview">
        <div class="preview-toolbar">
          <div>
            <span class="eyebrow">Preview</span>
            <h3>{{ selectedCategoryTitle }}</h3>
          </div>
          <div class="preview-actions">
            <button class="icon-btn" type="button" title="دسته قبل" @click="selectAdjacentCategory(-1)">
              <ChevronRightIcon :size="18" />
            </button>
            <button class="icon-btn" type="button" title="دسته بعد" @click="selectAdjacentCategory(1)">
              <ChevronLeftIcon :size="18" />
            </button>
          </div>
        </div>

        <div class="menu-preview-frame">
          <nav class="preview-tabs" aria-label="دسته‌های منو">
            <button
              v-for="category in activeCategories"
              :key="`tab-${category.name}`"
              class="preview-tab"
              :class="{ active: selectedCategoryName === category.name }"
              type="button"
              @click="selectCategory(category.name)"
            >
              {{ category.item_group_name || category.name }}
            </button>
          </nav>

          <section class="preview-category-card" v-if="selectedCategory">
            <div class="preview-category-copy">
              <span>{{ selectedCategory.restaurant_slug || 'menu' }}</span>
              <h2>{{ selectedCategory.item_group_name || selectedCategory.name }}</h2>
              <p>{{ selectedCategory.restaurant_description || 'زیردسته‌ها و محصولات این دسته را با drag handle مرتب کنید.' }}</p>
            </div>
          </section>

          <section class="subcategory-sort-list" v-if="selectedSubcategories.length">
            <header class="subsection-head">
              <strong>زیردسته‌ها</strong>
              <small>ترتیب نمایش بخش‌های داخل این دسته</small>
            </header>
            <article
              v-for="subcategory in selectedSubcategories"
              :key="subcategory.name || '__misc__'"
              class="subcategory-row"
              :class="{ active: selectedSubcategoryName === subcategory.name, dragging: dragState.id === subcategory.name }"
              :data-reorder-kind="'subcategory'"
              :data-reorder-id="subcategory.name"
              @dragover.prevent
              @drop.prevent="!subcategory.is_misc && dropReorder('subcategory', subcategory.name)"
              @click="selectSubcategory(subcategory.name)"
            >
              <button
                v-if="!subcategory.is_misc"
                class="drag-handle product-handle"
                type="button"
                aria-label="جابجایی زیردسته"
                draggable="true"
                @dragstart.stop="startHtmlDrag('subcategory', subcategory.name)"
                @dragend="clearDrag"
                @pointerdown.stop.prevent="startPointerDrag('subcategory', subcategory.name, $event)"
              >
                <GripVerticalIcon :size="16" />
              </button>
              <span v-else class="drag-placeholder" aria-hidden="true"></span>
              <div>
                <strong>{{ subcategory.title }}</strong>
                <small>{{ productCountBySubcategory(subcategory.name).toLocaleString('fa-IR') }} محصول</small>
              </div>
              <div v-if="!subcategory.is_misc" class="quick-order-actions">
                <button class="mini-icon" type="button" title="بالا" @click.stop="moveSubcategory(subcategory.name, -1)">
                  <ChevronUpIcon :size="15" />
                </button>
                <button class="mini-icon" type="button" title="پایین" @click.stop="moveSubcategory(subcategory.name, 1)">
                  <ChevronDownIcon :size="15" />
                </button>
              </div>
              <span v-else class="order-badge">آخر</span>
            </article>
          </section>

          <div v-if="selectedProducts.length" class="product-sort-list">
            <article
              v-for="product in selectedProducts"
              :key="product.name"
              class="preview-product"
              :class="{ selected: selectedProductName === product.name, disabled: !isProductActive(product), dragging: dragState.id === product.name }"
              :data-reorder-kind="'product'"
              :data-reorder-id="product.name"
              @dragover.prevent
              @drop.prevent="dropReorder('product', product.name)"
              @click="selectProduct(product.name)"
            >
              <button
                class="drag-handle product-handle"
                type="button"
                aria-label="جابجایی محصول"
                draggable="true"
                @dragstart.stop="startHtmlDrag('product', product.name)"
                @dragend="clearDrag"
                @pointerdown.stop.prevent="startPointerDrag('product', product.name, $event)"
              >
                <GripVerticalIcon :size="17" />
              </button>
              <div class="product-media">
                <img v-if="product.image" :src="product.image" :alt="product.title || product.item_name || 'تصویر محصول'" loading="lazy" />
                <span v-else>{{ initials(product.title || product.item_name || product.item_code) }}</span>
              </div>
              <div class="product-copy">
                <strong>{{ product.title || product.item_name || product.item_code }}</strong>
                <small>{{ product.short_desc || 'بدون توضیح کوتاه' }}</small>
                <span class="price-line">{{ formatMoney(product.base_price, currency) }}</span>
              </div>
              <div class="quick-order-actions">
                <button class="mini-icon" type="button" title="بالا" @click.stop="moveProduct(product.name, -1)">
                  <ChevronUpIcon :size="16" />
                </button>
                <button class="mini-icon" type="button" title="پایین" @click.stop="moveProduct(product.name, 1)">
                  <ChevronDownIcon :size="16" />
                </button>
              </div>
            </article>
          </div>

          <p v-else class="empty-state">در این دسته محصولی برای نمایش نیست.</p>
        </div>
      </main>

      <aside class="designer-panel inspector-panel">
        <header class="panel-head">
          <div>
            <span class="eyebrow">ویرایش سریع</span>
            <h3>{{ inspectorTitle }}</h3>
          </div>
        </header>

        <template v-if="selectedProduct">
          <div class="inspector-media">
            <img v-if="selectedProduct.image" :src="selectedProduct.image" :alt="selectedProduct.title || 'تصویر محصول'" loading="lazy" />
            <span v-else>{{ initials(selectedProduct.title || selectedProduct.item_code) }}</span>
          </div>

          <label class="field">
            نام محصول
            <input class="input" v-model="selectedProduct.title" @input="markProductDirty(selectedProduct.name)" />
          </label>
          <label class="field">
            توضیح کوتاه
            <textarea class="textarea" v-model="selectedProduct.short_desc" rows="3" @input="markProductDirty(selectedProduct.name)" />
          </label>
          <label class="field">
            دسته
            <select class="select" v-model="selectedProduct.category" @change="changeProductCategory(selectedProduct)">
              <option v-for="category in activeCategories" :key="`select-${category.name}`" :value="category.name">
                {{ category.item_group_name || category.name }}
              </option>
            </select>
          </label>
          <label class="field" v-if="selectedSubcategories.length">
            زیردسته
            <select class="select" v-model="selectedProduct.subcategory" @change="changeProductSubcategory(selectedProduct)">
              <option value="">سایر موارد</option>
              <option v-for="subcategory in selectedSubcategoriesWithoutMisc" :key="`sub-select-${subcategory.name}`" :value="subcategory.name">
                {{ subcategory.title }}
              </option>
            </select>
          </label>
          <ManagementToggleSwitch
            :model-value="isProductActive(selectedProduct)"
            label="نمایش در منو"
            hint="خاموش شود، مشتری این محصول را در سایت نمی‌بیند."
            @update:modelValue="setSelectedProductActive"
          />
          <div class="inspector-actions">
            <a class="secondary-btn" :href="`/management/product?item_name=${encodeURIComponent(selectedProduct.name)}`">جزئیات کامل</a>
          </div>
        </template>

        <template v-else-if="selectedCategory">
          <label class="field">
            عنوان دسته
            <input class="input" v-model="selectedCategory.item_group_name" @input="markCategoryDirty" />
          </label>
          <label class="field">
            توضیح دسته
            <textarea class="textarea" v-model="selectedCategory.restaurant_description" rows="4" @input="markCategoryDirty" />
          </label>
          <ManagementToggleSwitch
            :model-value="Number(selectedCategory.restaurant_active ?? 1) === 1"
            label="دسته فعال"
            hint="دسته در منوی مشتری نمایش داده شود."
            @update:modelValue="setSelectedCategoryActive"
          />
          <div class="inspector-actions">
            <a class="secondary-btn" :href="`/management/menu-group?name=${encodeURIComponent(selectedCategory.name)}`">جزئیات دسته</a>
          </div>
        </template>

        <p v-else class="muted">یک دسته یا محصول را انتخاب کنید.</p>
      </aside>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  ChevronDown as ChevronDownIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  ChevronUp as ChevronUpIcon,
  GripVertical as GripVerticalIcon,
} from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import {
  getMenuBoot,
  getMenuItems,
  listManagementMenuGroups,
  saveManagementMenuDesign,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const categories = ref([])
const products = ref([])
const currency = ref('IRR')
const selectedCategoryName = ref('')
const selectedSubcategoryName = ref('')
const selectedProductName = ref('')
const dirtyGroups = ref(false)
const dirtyProductNames = ref([])
const dragState = ref({ kind: '', id: '' })

const activeCategories = computed(() =>
  [...categories.value]
    .filter((row) => Number(row?.restaurant_is_menu_category ?? 1) === 1 && Number(row?.restaurant_is_subcategory || 0) !== 1)
    .sort((a, b) => Number(a?.restaurant_sort_order || 0) - Number(b?.restaurant_sort_order || 0)),
)

const selectedCategory = computed(() =>
  activeCategories.value.find((row) => row.name === selectedCategoryName.value) || activeCategories.value[0] || null,
)

const selectedSubcategoriesWithoutMisc = computed(() =>
  (selectedCategory.value?.subcategories || [])
    .map(normalizeSubcategory)
    .filter((row) => row.name && productCountBySubcategory(row.name) > 0)
    .sort((a, b) => Number(a?.sort_order || 0) - Number(b?.sort_order || 0)),
)

const selectedSubcategories = computed(() => {
  const rows = [...selectedSubcategoriesWithoutMisc.value]
  const miscCount = productCountBySubcategory('')
  if (miscCount > 0) {
    rows.push({
      name: '',
      title: 'سایر موارد',
      slug: 'misc',
      sort_order: 9999,
      item_count: miscCount,
      is_misc: true,
    })
  }
  return rows
})

const selectedSubcategory = computed(() => {
  if (!selectedSubcategories.value.length) {
    return null
  }
  return selectedSubcategories.value.find((row) => row.name === selectedSubcategoryName.value) || selectedSubcategories.value[0] || null
})

const selectedProducts = computed(() => {
  const categoryName = selectedCategory.value?.name || ''
  const hasSubcategories = selectedSubcategories.value.length > 0
  const subcategoryName = hasSubcategories ? String(selectedSubcategory.value?.name || '').trim() : ''
  return products.value
    .filter((row) => String(row?.category || '').trim() === categoryName)
    .filter((row) => !hasSubcategories || String(row?.subcategory || '').trim() === subcategoryName)
    .sort((a, b) => Number(a?.restaurant_sort_order || 0) - Number(b?.restaurant_sort_order || 0))
})

const selectedProduct = computed(() =>
  products.value.find((row) => row.name === selectedProductName.value) || null,
)

const selectedCategoryTitle = computed(() => selectedCategory.value?.item_group_name || selectedCategory.value?.name || 'منو')
const inspectorTitle = computed(() => selectedProduct.value ? 'محصول' : selectedCategory.value ? 'دسته' : 'انتخاب نشده')
const dirtyCount = computed(() => (dirtyGroups.value ? 1 : 0) + dirtyProductNames.value.length)
const dirtyCountLabel = computed(() => `${dirtyCount.value.toLocaleString('fa-IR')} تغییر ذخیره نشده`)

function resolveBranchFromBoot() {
  const boot = window._BOOT || {}
  const fromBoot = String(boot.active_branch || '').trim()
  if (fromBoot) return fromBoot
  const fromTable = String(boot?.table_context?.table?.branch || '').trim()
  if (fromTable) return fromTable
  return String(new URLSearchParams(window.location.search || '').get('branch') || '').trim()
}

function normalizePublicCategory(row, managementMap = new Map()) {
  const name = String(row?.name || '').trim()
  const managementRow = managementMap.get(name) || {}
  const subcategories = Array.isArray(row?.subcategories) ? row.subcategories.map(normalizeSubcategory) : []
  return {
    ...managementRow,
    ...row,
    name,
    item_group_name: String(row?.title || managementRow?.item_group_name || name).trim(),
    restaurant_slug: String(row?.slug || managementRow?.restaurant_slug || '').trim(),
    restaurant_sort_order: Number(row?.sort_order ?? managementRow?.restaurant_sort_order ?? 0),
    restaurant_is_menu_category: 1,
    restaurant_is_subcategory: 0,
    restaurant_active: Number(managementRow?.restaurant_active ?? 1) ? 1 : 0,
    item_count: Number(row?.item_count || 0),
    subcategories,
  }
}

function normalizeSubcategory(row) {
  const name = String(row?.name || '').trim()
  const title = String(row?.title || row?.label || name || 'زیردسته').trim()
  return {
    ...row,
    name,
    title,
    slug: String(row?.slug || '').trim(),
    sort_order: Number(row?.sort_order ?? row?.restaurant_sort_order ?? 0),
    item_count: Number(row?.item_count || 0),
  }
}

function normalizeProduct(row) {
  return {
    ...row,
    name: String(row?.name || row?.item_code || row?.slug || '').trim(),
    item_code: String(row?.item_code || row?.name || '').trim(),
    title: String(row?.title || row?.item_name || row?.item_code || row?.name || '').trim(),
    short_desc: String(row?.short_desc || row?.restaurant_short_desc || '').trim(),
    category: String(row?.category || row?.restaurant_category || '').trim(),
    category_slug: String(row?.category_slug || '').trim(),
    subcategory: String(row?.subcategory || row?.restaurant_subcategory || '').trim(),
    subcategory_title: String(row?.subcategory_title || '').trim(),
    subcategory_slug: String(row?.subcategory_slug || '').trim(),
    restaurant_sort_order: Number(row?.restaurant_sort_order ?? row?.sort_order ?? 0),
    is_active: 1,
  }
}

async function loadVisibleMenuProducts(publicCategories, branch = '') {
  const loaded = []
  const seen = new Set()

  async function fetchCategory(category) {
    const categorySlug = String(category?.slug || '').trim()
    if (!categorySlug) return
    let page = 1
    let totalPages = 1
    while (page <= totalPages && page <= 200) {
      const orderOffset = loaded.filter((item) => String(item?.category || '').trim() === String(category?.name || '').trim()).length
      const payload = await getMenuItems({
        category_slug: categorySlug,
        subcategory_slug: '',
        search: '',
        page,
        page_size: 100,
        branch,
      })
      const rows = Array.isArray(payload?.items) ? payload.items : []
      for (const row of rows) {
        const normalized = normalizeProduct(row)
        const key = String(normalized?.slug || normalized?.name || '').trim()
        if (!key || seen.has(key)) continue
        seen.add(key)
        if (!Number(normalized.restaurant_sort_order || 0)) {
          normalized.restaurant_sort_order = (orderOffset + rows.indexOf(row) + 1) * 10
        }
        loaded.push(normalized)
      }
      const paginationPayload = payload?.pagination || {}
      const nextTotalPages = Number(paginationPayload.total_pages || 1)
      totalPages = Number.isFinite(nextTotalPages) && nextTotalPages > 0 ? nextTotalPages : 1
      page += 1
    }
  }

  for (const category of publicCategories || []) {
    await fetchCategory(category)
  }

  return loaded
}

async function loadDesigner() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const branch = resolveBranchFromBoot()
    const [groupRows, menuBoot] = await Promise.all([
      listManagementMenuGroups(),
      getMenuBoot(branch),
    ])
    const managementMap = new Map((Array.isArray(groupRows) ? groupRows : []).map((row) => [String(row?.name || '').trim(), row]))
    const publicCategories = (Array.isArray(menuBoot?.categories) ? menuBoot.categories : [])
      .filter((row) => Number(row?.item_count || 0) > 0)
      .map((row) => normalizePublicCategory(row, managementMap))

    categories.value = publicCategories
    products.value = await loadVisibleMenuProducts(publicCategories, branch)
    currency.value = menuBoot?.currency || currency.value || 'TOMAN'
    selectedCategoryName.value = activeCategories.value[0]?.name || ''
    selectedSubcategoryName.value = selectedSubcategories.value[0]?.name || ''
    selectedProductName.value = selectedProducts.value[0]?.name || ''
    dirtyGroups.value = false
    dirtyProductNames.value = []
  } catch (loadError) {
    error.value = loadError.message || 'بارگذاری طراحی منو ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function selectCategory(name) {
  selectedCategoryName.value = String(name || '').trim()
  selectedSubcategoryName.value = selectedSubcategories.value[0]?.name || ''
  selectedProductName.value = selectedProducts.value[0]?.name || ''
}

function selectSubcategory(name) {
  selectedSubcategoryName.value = String(name || '').trim()
  selectedProductName.value = selectedProducts.value[0]?.name || ''
}

function selectProduct(name) {
  selectedProductName.value = String(name || '').trim()
}

function productCountByCategory(categoryName) {
  return products.value.filter((row) => String(row?.category || '').trim() === String(categoryName || '').trim()).length
}

function productCountBySubcategory(subcategoryName) {
  const categoryName = String(selectedCategory.value?.name || '').trim()
  const normalizedSubcategory = String(subcategoryName || '').trim()
  return products.value.filter((row) =>
    String(row?.category || '').trim() === categoryName &&
    String(row?.subcategory || '').trim() === normalizedSubcategory,
  ).length
}

function resolveCategoryIndex(categoryName) {
  return activeCategories.value.findIndex((row) => row.name === categoryName) + 1
}

function isProductActive(product) {
  return Number(product?.is_active || 0) === 1
}

function initials(value) {
  return String(value || 'م')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
}

function markProductDirty(name) {
  const normalized = String(name || '').trim()
  if (normalized && !dirtyProductNames.value.includes(normalized)) {
    dirtyProductNames.value = [...dirtyProductNames.value, normalized]
  }
}

function markCategoryDirty() {
  dirtyGroups.value = true
}

function arrayMove(rows, fromIndex, toIndex) {
  if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex || fromIndex >= rows.length || toIndex >= rows.length) {
    return rows
  }
  const next = [...rows]
  const [item] = next.splice(fromIndex, 1)
  next.splice(toIndex, 0, item)
  return next
}

function moveCategory(name, direction) {
  const ordered = activeCategories.value
  const from = ordered.findIndex((row) => row.name === name)
  const nextOrdered = arrayMove(ordered, from, from + direction)
  if (nextOrdered === ordered) return
  nextOrdered.forEach((row, index) => {
    row.restaurant_sort_order = (index + 1) * 10
  })
  categories.value = categories.value.map((row) => nextOrdered.find((item) => item.name === row.name) || row)
  dirtyGroups.value = true
}

function moveSubcategory(name, direction) {
  const ordered = selectedSubcategoriesWithoutMisc.value
  const from = ordered.findIndex((row) => row.name === name)
  const nextOrdered = arrayMove(ordered, from, from + direction)
  if (nextOrdered === ordered) return
  applySubcategoryOrder(nextOrdered)
}

function moveProduct(name, direction) {
  const ordered = selectedProducts.value
  const from = ordered.findIndex((row) => row.name === name)
  const nextOrdered = arrayMove(ordered, from, from + direction)
  if (nextOrdered === ordered) return
  nextOrdered.forEach((row, index) => {
    row.restaurant_sort_order = (index + 1) * 10
    markProductDirty(row.name)
  })
  products.value = products.value.map((row) => nextOrdered.find((item) => item.name === row.name) || row)
}

function startHtmlDrag(kind, id) {
  dragState.value = { kind, id }
}

function clearDrag() {
  dragState.value = { kind: '', id: '' }
}

function dropReorder(kind, targetId) {
  if (dragState.value.kind !== kind || !dragState.value.id || dragState.value.id === targetId) {
    clearDrag()
    return
  }
  if (kind === 'category') {
    reorderCategories(dragState.value.id, targetId)
  } else if (kind === 'subcategory') {
    reorderSubcategories(dragState.value.id, targetId)
  } else {
    reorderProducts(dragState.value.id, targetId)
  }
  clearDrag()
}

function startPointerDrag(kind, id, event) {
  dragState.value = { kind, id }
  const pointerId = event.pointerId
  const target = event.currentTarget
  target?.setPointerCapture?.(pointerId)

  const onPointerUp = (upEvent) => {
    const element = document.elementFromPoint(upEvent.clientX, upEvent.clientY)
    const dropTarget = element?.closest?.(`[data-reorder-kind="${kind}"]`)
    const targetId = dropTarget?.dataset?.reorderId || ''
    if (targetId && targetId !== id) {
      dropReorder(kind, targetId)
    } else {
      clearDrag()
    }
    window.removeEventListener('pointerup', onPointerUp)
    window.removeEventListener('pointercancel', onPointerCancel)
  }
  const onPointerCancel = () => {
    clearDrag()
    window.removeEventListener('pointerup', onPointerUp)
    window.removeEventListener('pointercancel', onPointerCancel)
  }
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerCancel)
}

function reorderCategories(sourceId, targetId) {
  const ordered = activeCategories.value
  const from = ordered.findIndex((row) => row.name === sourceId)
  const to = ordered.findIndex((row) => row.name === targetId)
  const nextOrdered = arrayMove(ordered, from, to)
  nextOrdered.forEach((row, index) => {
    row.restaurant_sort_order = (index + 1) * 10
  })
  categories.value = categories.value.map((row) => nextOrdered.find((item) => item.name === row.name) || row)
  dirtyGroups.value = true
}

function applySubcategoryOrder(nextOrdered) {
  const category = selectedCategory.value
  if (!category) return
  nextOrdered.forEach((row, index) => {
    row.sort_order = (index + 1) * 10
    row.restaurant_sort_order = row.sort_order
  })
  const byName = new Map(nextOrdered.map((row) => [row.name, row]))
  const updatedCategory = {
    ...category,
    subcategories: (category.subcategories || []).map((row) => byName.get(String(row?.name || '').trim()) || row),
  }
  categories.value = categories.value.map((row) => row.name === updatedCategory.name ? updatedCategory : row)
  selectedSubcategoryName.value = nextOrdered.find((row) => row.name === selectedSubcategoryName.value)?.name || nextOrdered[0]?.name || ''
  dirtyGroups.value = true
}

function reorderSubcategories(sourceId, targetId) {
  if (!sourceId || !targetId) return
  const ordered = selectedSubcategoriesWithoutMisc.value
  const from = ordered.findIndex((row) => row.name === sourceId)
  const to = ordered.findIndex((row) => row.name === targetId)
  const nextOrdered = arrayMove(ordered, from, to)
  if (nextOrdered === ordered) return
  applySubcategoryOrder(nextOrdered)
}

function reorderProducts(sourceId, targetId) {
  const ordered = selectedProducts.value
  const from = ordered.findIndex((row) => row.name === sourceId)
  const to = ordered.findIndex((row) => row.name === targetId)
  const nextOrdered = arrayMove(ordered, from, to)
  nextOrdered.forEach((row, index) => {
    row.restaurant_sort_order = (index + 1) * 10
    markProductDirty(row.name)
  })
  products.value = products.value.map((row) => nextOrdered.find((item) => item.name === row.name) || row)
}

function selectAdjacentCategory(direction) {
  const index = activeCategories.value.findIndex((row) => row.name === selectedCategoryName.value)
  const nextIndex = Math.min(Math.max(index + direction, 0), activeCategories.value.length - 1)
  const next = activeCategories.value[nextIndex]
  if (next) selectCategory(next.name)
}

function changeProductCategory(product) {
  product.category = String(product.category || '').trim()
  selectedCategoryName.value = product.category
  product.subcategory = selectedSubcategoriesWithoutMisc.value[0]?.name || ''
  selectedSubcategoryName.value = product.subcategory
  product.restaurant_sort_order = (selectedProducts.value.length + 1) * 10
  markProductDirty(product.name)
}

function changeProductSubcategory(product) {
  product.subcategory = String(product.subcategory || '').trim()
  selectedSubcategoryName.value = product.subcategory
  product.restaurant_sort_order = (selectedProducts.value.length + 1) * 10
  markProductDirty(product.name)
}

function setSelectedProductActive(value) {
  if (!selectedProduct.value) return
  selectedProduct.value.is_active = value ? 1 : 0
  markProductDirty(selectedProduct.value.name)
}

function setSelectedCategoryActive(value) {
  if (!selectedCategory.value) return
  selectedCategory.value.restaurant_active = value ? 1 : 0
  markCategoryDirty()
}

function normalizeDesignerSortOrders() {
  activeCategories.value.forEach((category, categoryIndex) => {
    category.restaurant_sort_order = (categoryIndex + 1) * 10
    ;(category.subcategories || [])
      .map(normalizeSubcategory)
      .filter((subcategory) => subcategory.name)
      .sort((a, b) => Number(a?.sort_order || 0) - Number(b?.sort_order || 0))
      .forEach((subcategory, subcategoryIndex) => {
        const source = category.subcategories.find((row) => String(row?.name || '').trim() === subcategory.name)
        if (source) {
          source.sort_order = (subcategoryIndex + 1) * 10
          source.restaurant_sort_order = source.sort_order
        }
      })
  })

  const buckets = new Map()
  products.value.forEach((product) => {
    const key = `${String(product?.category || '').trim()}::${String(product?.subcategory || '').trim()}`
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key).push(product)
  })
  buckets.forEach((rows) => {
    rows
      .sort((a, b) => Number(a?.restaurant_sort_order || 0) - Number(b?.restaurant_sort_order || 0))
      .forEach((product, productIndex) => {
        product.restaurant_sort_order = (productIndex + 1) * 10
        markProductDirty(product.name)
      })
  })
  dirtyGroups.value = true
}

function buildGroupOrderPayload() {
  const items = []
  activeCategories.value.forEach((category) => {
    items.push({
      name: category.name,
      sort_order: Number(category.restaurant_sort_order || 0),
      item_group_name: category.item_group_name || category.name,
      restaurant_description: category.restaurant_description || '',
      restaurant_active: Number(category.restaurant_active ?? 1) ? 1 : 0,
    })
    ;(category.subcategories || [])
      .map(normalizeSubcategory)
      .filter((subcategory) => subcategory.name)
      .sort((a, b) => Number(a?.sort_order || 0) - Number(b?.sort_order || 0))
      .forEach((subcategory) => {
        items.push({
          name: subcategory.name,
          sort_order: Number(subcategory.sort_order || subcategory.restaurant_sort_order || 0),
        })
      })
  })
  return items
}

async function saveDesigner() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    normalizeDesignerSortOrders()
    const dirtyProducts = products.value.filter((row) => dirtyProductNames.value.includes(row.name))
    const result = await saveManagementMenuDesign({
      groups: dirtyGroups.value ? buildGroupOrderPayload() : [],
      products: dirtyProducts.map((row) => ({
        name: row.name,
        item_name: row.title,
        restaurant_short_desc: row.short_desc,
        restaurant_category: row.category,
        restaurant_subcategory: row.subcategory,
        restaurant_sort_order: Number(row.restaurant_sort_order || 0),
        restaurant_enabled: Number(row.is_active || 0) ? 1 : 0,
      })),
    })

    const savedGroupsCount = Number(result?.groups_count || 0)
    const savedProductsCount = Number(result?.products_count || 0)
    if (dirtyGroups.value && savedGroupsCount < 1) {
      throw new Error('هیچ گروهی در سرور ذخیره نشد. لطفا دوباره تلاش کنید.')
    }
    if (dirtyProducts.length && savedProductsCount < 1) {
      throw new Error('هیچ محصولی در سرور ذخیره نشد. لطفا دوباره تلاش کنید.')
    }

    success.value = 'چیدمان منو ذخیره شد.'
    await loadDesigner()
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره طراحی منو ناموفق بود.'
  } finally {
    saving.value = false
  }
}

onBeforeUnmount(() => clearDrag())

loadDesigner()
</script>

<style scoped>
.designer-shell {
  display: grid;
  grid-template-columns: minmax(220px, 0.8fr) minmax(360px, 1.45fr) minmax(260px, 0.95fr);
  gap: 0.85rem;
  align-items: start;
}

.designer-panel,
.designer-preview {
  border: 1px solid #e4ded6;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 30px rgb(43 33 26 / 0.06);
}

.designer-panel {
  padding: 0.85rem;
  display: grid;
  gap: 0.75rem;
}

.structure-panel,
.inspector-panel {
  position: sticky;
  top: 5.5rem;
}

.panel-head,
.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.panel-head h3,
.preview-toolbar h3 {
  margin: 0;
  color: #2b211a;
  font-size: 1rem;
  font-weight: 900;
}

.eyebrow {
  color: #7c5a42;
  font-size: 0.72rem;
  font-weight: 900;
}

.count-chip,
.dirty-chip,
.order-badge {
  border: 1px solid rgb(124 90 66 / 0.18);
  border-radius: 999px;
  background: #f7f1ea;
  color: #5f402d;
  padding: 0.22rem 0.55rem;
  font-size: 0.74rem;
  font-weight: 900;
}

.category-stack,
.product-sort-list {
  display: grid;
  gap: 0.45rem;
}

.category-row,
.preview-product,
.subcategory-row {
  width: 100%;
  border: 1px solid #ece6de;
  border-radius: 8px;
  background: #fff;
  color: #2b211a;
  display: grid;
  align-items: center;
  gap: 0.55rem;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
  touch-action: manipulation;
}

.category-row {
  grid-template-columns: auto minmax(0, 1fr) auto;
  padding: 0.45rem;
  text-align: right;
}

.category-row:hover,
.category-row.active,
.preview-product:hover,
.preview-product.selected,
.subcategory-row:hover,
.subcategory-row.active {
  border-color: rgb(124 90 66 / 0.34);
  background: #fbfaf8;
  box-shadow: 0 10px 22px rgb(43 33 26 / 0.07);
}

.category-row.dragging,
.preview-product.dragging,
.subcategory-row.dragging {
  opacity: 0.62;
  transform: scale(0.99);
}

.drag-handle,
.icon-btn,
.mini-icon {
  min-width: 2.35rem;
  min-height: 2.35rem;
  border: 1px solid #e4ded6;
  border-radius: 8px;
  background: #fbfaf8;
  color: #7c5a42;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  touch-action: none;
}

.drag-placeholder {
  width: 2.35rem;
  height: 2.35rem;
}

.category-copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.category-copy strong,
.product-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-copy small,
.product-copy small {
  color: #74685f;
  font-size: 0.76rem;
  line-height: 1.6;
}

.designer-preview {
  min-width: 0;
  padding: 0.85rem;
}

.preview-actions {
  display: inline-flex;
  gap: 0.35rem;
}

.icon-btn,
.mini-icon {
  cursor: pointer;
  touch-action: manipulation;
}

.menu-preview-frame {
  margin-top: 0.75rem;
  border: 1px solid #e4ded6;
  border-radius: 8px;
  background: #f7f6f4;
  padding: 0.75rem;
  min-height: 65vh;
}

.preview-tabs {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  padding-bottom: 0.45rem;
}

.preview-tab {
  border: 1px solid #e4ded6;
  border-radius: 999px;
  background: #fff;
  color: #74685f;
  padding: 0.45rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 850;
  white-space: nowrap;
  cursor: pointer;
}

.preview-tab.active {
  color: #2b211a;
  background: #f7f1ea;
  border-color: rgb(124 90 66 / 0.24);
}

.preview-category-card {
  margin: 0.35rem 0 0.7rem;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e4ded6;
  padding: 0.9rem;
}

.preview-category-copy span {
  color: #7c5a42;
  font-size: 0.72rem;
  font-weight: 900;
}

.preview-category-copy h2 {
  margin: 0.15rem 0;
  color: #2b211a;
  font-size: clamp(1.35rem, 2.4vw, 2.1rem);
  line-height: 1.35;
}

.preview-category-copy p {
  margin: 0;
  color: #74685f;
  line-height: 1.75;
}

.subcategory-sort-list {
  display: grid;
  gap: 0.4rem;
  margin: 0.35rem 0 0.7rem;
}

.subsection-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  color: #4a3b31;
  font-size: 0.8rem;
}

.subsection-head strong {
  font-weight: 900;
}

.subsection-head small,
.subcategory-row small {
  color: #74685f;
  font-size: 0.74rem;
}

.subcategory-row {
  grid-template-columns: auto minmax(0, 1fr) auto;
  padding: 0.48rem;
}

.subcategory-row > div:not(.quick-order-actions) {
  min-width: 0;
  display: grid;
  gap: 0.08rem;
}

.subcategory-row strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-product {
  grid-template-columns: auto 72px minmax(0, 1fr) auto;
  padding: 0.55rem;
}

.preview-product.disabled {
  opacity: 0.62;
}

.product-media,
.inspector-media {
  border: 1px solid #e4ded6;
  border-radius: 8px;
  background: #fbfaf8;
  display: grid;
  place-items: center;
  color: #7c5a42;
  font-weight: 900;
  overflow: hidden;
}

.product-media {
  width: 72px;
  aspect-ratio: 1;
}

.product-media img,
.inspector-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-copy {
  min-width: 0;
  display: grid;
  gap: 0.12rem;
}

.price-line {
  color: #5f402d;
  font-size: 0.82rem;
  font-weight: 900;
}

.quick-order-actions {
  display: grid;
  gap: 0.25rem;
}

.empty-state,
.muted {
  margin: 0;
  color: #74685f;
  line-height: 1.75;
}

.error {
  margin: 0;
  color: var(--danger);
}

.success {
  margin: 0;
  color: var(--success);
}

.inspector-media {
  aspect-ratio: 16 / 10;
  min-height: 150px;
}

.field {
  display: grid;
  gap: 0.28rem;
  color: #4a3b31;
  font-size: 0.82rem;
  font-weight: 800;
}

.textarea {
  min-height: 5.5rem;
  resize: vertical;
}

.inspector-actions {
  display: grid;
  gap: 0.45rem;
}

@media (max-width: 1180px) {
  .designer-shell {
    grid-template-columns: minmax(220px, 0.85fr) minmax(0, 1.2fr);
  }

  .inspector-panel {
    grid-column: 1 / -1;
    position: static;
  }
}

@media (max-width: 760px) {
  .designer-shell {
    grid-template-columns: 1fr;
    gap: 0.65rem;
  }

  .structure-panel,
  .inspector-panel {
    position: static;
  }

  .designer-panel,
  .designer-preview {
    padding: 0.65rem;
  }

  .menu-preview-frame {
    min-height: auto;
    padding: 0.55rem;
  }

  .preview-product {
    grid-template-columns: auto 58px minmax(0, 1fr);
  }

  .quick-order-actions {
    grid-column: 1 / -1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mini-icon {
    width: 100%;
  }
}
</style>
