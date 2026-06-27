<template>
  <section class="menu-groups-settings">
    <ManagementSurfaceCard tone="accent">
      <div class="toolbar">
        <input class="input" v-model="search" placeholder="جستجو گروه/زیرگروه..." />
        <ManagementFilterControl
          v-model="typeFilter"
          :options="typeOptions"
          label="نوع"
          placeholder="نوع گروه"
          :include-empty-option="true"
          empty-label="همه"
        />
        <ManagementFilterControl
          v-model="statusFilter"
          :options="statusOptions"
          label="وضعیت"
          placeholder="وضعیت"
          :include-empty-option="true"
          empty-label="همه"
        />
        <button class="secondary-btn" type="button" @click="openCreatePage">گروه جدید</button>
        <button class="primary-btn" type="button" @click="loadGroups">بروزرسانی</button>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری گروه‌ها...</p>
    <p class="error" v-if="error">{{ error }}</p>

    <section class="summary-strip" v-if="!loading">
      <article>
        <small>کل گروه‌ها</small>
        <strong>{{ summary.total.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>دسته اصلی</small>
        <strong>{{ summary.categories.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>زیردسته</small>
        <strong>{{ summary.subcategories.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>فعال در سایت</small>
        <strong>{{ summary.active.toLocaleString('fa-IR') }}</strong>
      </article>
      <article>
        <small>دارای تصویر</small>
        <strong>{{ summary.withImage.toLocaleString('fa-IR') }}</strong>
      </article>
    </section>

    <ManagementSurfaceCard title="گروه‌ها و زیرگروه‌های منو" subtitle="برای ویرایش کامل، روی هر سطر یا کارت کلیک کنید.">
      <ManagementCollectionView v-model="viewMode" :modes="viewModes" class="groups-collection">
        <template #list>
          <ManagementListView
            :columns="columns"
            :rows="visibleRows"
            row-key="name"
            :row-clickable="true"
            @row-click="openEditPage"
          >
            <template #cell-item_group_name="{ row }">
              <div class="group-title-cell">
                <span class="group-thumb" :class="{ empty: !row.image }">
                  <img v-if="row.image" :src="row.image" :alt="row.item_group_name" loading="lazy" />
                  <span v-else>{{ initials(row.item_group_name || row.name) }}</span>
                </span>
                <div>
                  <strong>{{ row.item_group_name || row.name }}</strong>
                  <small>{{ row.name }}</small>
                </div>
              </div>
            </template>

            <template #cell-type="{ row }">
              <span :class="['pill', row.restaurant_is_subcategory ? 'sub' : 'cat']">
                {{ row.restaurant_is_subcategory ? 'زیردسته' : 'دسته اصلی' }}
              </span>
            </template>

            <template #cell-parent_item_group="{ value }">{{ value || '—' }}</template>

            <template #cell-is_group="{ value }">
              <span :class="['pill', Number(value) ? 'ok' : 'warn']">{{ Number(value) ? 'Group' : 'Leaf' }}</span>
            </template>

            <template #cell-restaurant_active="{ value }">
              <span :class="['state-pill', Number(value) ? 'on' : 'off']">
                {{ Number(value) ? 'فعال' : 'غیرفعال' }}
              </span>
            </template>

            <template #cell-show_on_homepage="{ row }">
              <ManagementToggleSwitch
                compact
                :model-value="Number(row?.show_on_homepage || 1) === 1"
                label="نمایش صفحه اصلی"
                @update:model-value="toggleHomepage(row)"
              />
            </template>

            <template #cell-actions="{ row }">
              <div class="actions">
                <button class="secondary-btn mini" type="button" @click="toggleActive(row)">
                  {{ Number(row?.restaurant_active || 0) ? 'غیرفعال' : 'فعال' }}
                </button>
              </div>
            </template>
          </ManagementListView>
        </template>

        <template #gallery>
          <ManagementGalleryView
            :rows="visibleRows"
            row-key="name"
            title-field="item_group_name"
            subtitle-field="parent_item_group"
            fallback-text="GRP"
            image-field="image"
            :clickable="true"
            @click-item="openEditPage"
          >
            <template #caption="{ row }">
              {{ row.restaurant_is_subcategory ? 'زیردسته' : 'دسته اصلی' }} • {{ row.restaurant_slug || 'بدون اسلاگ' }}
            </template>
            <template #overlay="{ row }">
              <span class="gallery-status" :class="Number(row.restaurant_active) ? 'on' : 'off'">
                {{ Number(row.restaurant_active) ? 'فعال' : 'غیرفعال' }}
              </span>
            </template>
            <template #actions="{ row }">
              <div class="actions" @click.stop>
                <button class="secondary-btn mini" type="button" @click="toggleActive(row)">
                  {{ Number(row?.restaurant_active || 0) ? 'غیرفعال' : 'فعال' }}
                </button>
              </div>
            </template>
          </ManagementGalleryView>
        </template>

        <template #tree>
          <ManagementTreeView
            :nodes="treeNodes"
            empty-text="گروهی برای نمایش وجود ندارد."
            :node-clickable="canOpenGroupNode"
            @node-click="openEditPage"
          >
            <template #actions="{ node }">
              <div class="actions">
                <button class="secondary-btn mini" type="button" @click="toggleActive(node)">
                  {{ Number(node?.restaurant_active || 0) ? 'غیرفعال' : 'فعال' }}
                </button>
              </div>
            </template>
          </ManagementTreeView>
        </template>

        <template #sort>
          <div class="sort-list-wrap">
            <p class="sort-hint">با دکمه‌های بالا/پایین ترتیب دسته‌های اصلی را تغییر دهید، سپس ذخیره کنید.</p>
            <p class="error" v-if="sortError">{{ sortError }}</p>
            <div class="sort-list">
              <div
                v-for="(row, idx) in topLevelSortRows"
                :key="row.name"
                class="sort-row"
              >
                <span class="sort-index">{{ idx + 1 }}</span>
                <div class="sort-row-img" v-if="row.image">
                  <img :src="row.image" :alt="row.item_group_name" />
                </div>
                <div class="sort-row-img sort-row-no-img" v-else>
                  <span>{{ (row.item_group_name || '؟').slice(0, 2) }}</span>
                </div>
                <div class="sort-row-info">
                  <strong>{{ row.item_group_name }}</strong>
                  <span class="sort-row-slug">{{ row.restaurant_slug || 'بدون اسلاگ' }}</span>
                </div>
                <div class="sort-row-btns">
                  <button
                    type="button"
                    class="sort-btn"
                    :disabled="idx === 0"
                    @click="moveSortUp(idx)"
                    title="بالاتر"
                  >↑</button>
                  <button
                    type="button"
                    class="sort-btn"
                    :disabled="idx === topLevelSortRows.length - 1"
                    @click="moveSortDown(idx)"
                    title="پایین‌تر"
                  >↓</button>
                </div>
                <span class="sort-row-status" :class="Number(row.restaurant_active) ? 'on' : 'off'">
                  {{ Number(row.restaurant_active) ? 'فعال' : 'غیرفعال' }}
                </span>
              </div>
            </div>
            <div class="sort-actions">
              <button class="primary-btn" type="button" :disabled="sortSaving" @click="saveSortOrder">
                {{ sortSaving ? 'در حال ذخیره...' : 'ذخیره ترتیب' }}
              </button>
              <button class="secondary-btn" type="button" @click="resetSortRows">بازنشانی</button>
            </div>
          </div>
        </template>
      </ManagementCollectionView>
    </ManagementSurfaceCard>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import ManagementCollectionView from '@/components/management/ManagementCollectionView.vue'
import ManagementFilterControl from '@/components/management/ManagementFilterControl.vue'
import ManagementGalleryView from '@/components/management/ManagementGalleryView.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import ManagementTreeView from '@/components/management/ManagementTreeView.vue'
import {
  listManagementMenuGroups,
  reorderManagementMenuGroups,
  updateManagementMenuGroup,
} from '@/utils/api'

const loading = ref(false)
const error = ref('')
const rows = ref([])
const search = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const viewMode = ref(readStoredViewMode())

const columns = [
  { key: 'item_group_name', label: 'عنوان' },
  { key: 'restaurant_slug', label: 'اسلاگ' },
  { key: 'type', label: 'نوع' },
  { key: 'parent_item_group', label: 'گروه والد' },
  { key: 'is_group', label: 'is_group' },
  { key: 'restaurant_sort_order', label: 'ترتیب' },
  { key: 'restaurant_active', label: 'وضعیت' },
  { key: 'show_on_homepage', label: 'صفحه اصلی' },
  { key: 'actions', label: 'عملیات سریع' },
]

const typeOptions = [
  { value: 'category', label: 'دسته اصلی' },
  { value: 'subcategory', label: 'زیردسته' },
]

const statusOptions = [
  { value: 'active', label: 'فقط فعال' },
  { value: 'inactive', label: 'فقط غیرفعال' },
]

const viewModes = [
  { value: 'list', label: 'لیست', icon: '≡' },
  { value: 'gallery', label: 'گالری', icon: '▦' },
  { value: 'tree', label: 'درخت', icon: '⋰' },
  { value: 'sort', label: 'ترتیب‌بندی', icon: '↕' },
]

const sortError = ref('')
const sortSaving = ref(false)
const sortRows = ref([])

const topLevelSortRows = computed(() =>
  (sortRows.value || []).filter((row) => Number(row?.restaurant_is_subcategory || 0) !== 1),
)

const summary = computed(() => {
  const list = rows.value || []
  return {
    total: list.length,
    categories: list.filter((row) => Number(row?.restaurant_is_subcategory || 0) !== 1).length,
    subcategories: list.filter((row) => Number(row?.restaurant_is_subcategory || 0) === 1).length,
    active: list.filter((row) => Number(row?.restaurant_active || 0) === 1).length,
    withImage: list.filter((row) => String(row?.image || '').trim()).length,
  }
})

const visibleRows = computed(() => {
  let output = [...rows.value]
  const query = String(search.value || '').trim().toLowerCase()
  if (query) {
    output = output.filter((row) => {
      const title = String(row?.item_group_name || '').toLowerCase()
      const slug = String(row?.restaurant_slug || '').toLowerCase()
      const name = String(row?.name || '').toLowerCase()
      return title.includes(query) || slug.includes(query) || name.includes(query)
    })
  }

  if (typeFilter.value === 'category') {
    output = output.filter((row) => Number(row?.restaurant_is_subcategory || 0) !== 1)
  } else if (typeFilter.value === 'subcategory') {
    output = output.filter((row) => Number(row?.restaurant_is_subcategory || 0) === 1)
  }

  if (statusFilter.value === 'active') {
    output = output.filter((row) => Number(row?.restaurant_active || 0) === 1)
  } else if (statusFilter.value === 'inactive') {
    output = output.filter((row) => Number(row?.restaurant_active || 0) !== 1)
  }

  return output
})

const groupTree = computed(() => {
  const categories = (visibleRows.value || [])
    .filter((row) => Number(row?.restaurant_is_subcategory || 0) !== 1)
    .map((row) => ({
      ...row,
      children: [],
    }))
    .sort((left, right) => String(left?.item_group_name || '').localeCompare(String(right?.item_group_name || ''), 'fa'))

  const categoryMap = new Map(categories.map((row) => [String(row?.name || '').trim(), row]))
  const subcategories = (visibleRows.value || [])
    .filter((row) => Number(row?.restaurant_is_subcategory || 0) === 1)
    .sort((left, right) => String(left?.item_group_name || '').localeCompare(String(right?.item_group_name || ''), 'fa'))

  for (const sub of subcategories) {
    const parentKey = String(sub?.parent_item_group || '').trim()
    const parent = categoryMap.get(parentKey)
    if (!parent) {
      continue
    }
    parent.children.push(sub)
  }

  return categories
})

const treeNodes = computed(() =>
  (groupTree.value || []).map((category) => ({
    ...category,
    key: String(category?.name || ''),
    label: String(category?.item_group_name || category?.name || '').trim(),
    caption: String(category?.restaurant_slug || '').trim() || 'بدون اسلاگ',
    badge: 'دسته',
    status: {
      label: Number(category?.restaurant_active || 0) ? 'فعال' : 'غیرفعال',
      tone: Number(category?.restaurant_active || 0) ? 'success' : 'warning',
    },
    children: (category.children || []).map((child) => ({
      ...child,
      key: String(child?.name || ''),
      label: String(child?.item_group_name || child?.name || '').trim(),
      caption: String(child?.restaurant_slug || '').trim() || 'بدون اسلاگ',
      badge: 'زیرگروه',
      status: {
        label: Number(child?.restaurant_active || 0) ? 'فعال' : 'غیرفعال',
        tone: Number(child?.restaurant_active || 0) ? 'success' : 'warning',
      },
      children: [],
    })),
  })),
)

async function loadGroups() {
  loading.value = true
  error.value = ''
  try {
    const groups = await listManagementMenuGroups({})
    rows.value = Array.isArray(groups) ? groups : []
    resetSortRows()
  } catch (err) {
    error.value = err.message || 'بارگذاری گروه‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function resetSortRows() {
  const categories = (rows.value || [])
    .filter((row) => Number(row?.restaurant_is_subcategory || 0) !== 1)
    .slice()
    .sort((a, b) => Number(a?.restaurant_sort_order || 0) - Number(b?.restaurant_sort_order || 0))
  sortRows.value = categories.map((row, idx) => ({ ...row, restaurant_sort_order: idx }))
}

function moveSortUp(idx) {
  if (idx <= 0) return
  const cats = [...topLevelSortRows.value]
  const fullRows = [...sortRows.value]

  const catIdx = fullRows.findIndex((r) => r.name === cats[idx].name)
  const prevCatIdx = fullRows.findIndex((r) => r.name === cats[idx - 1].name)

  if (catIdx === -1 || prevCatIdx === -1) return

  const temp = fullRows[catIdx]
  fullRows[catIdx] = { ...fullRows[prevCatIdx], restaurant_sort_order: idx }
  fullRows[prevCatIdx] = { ...temp, restaurant_sort_order: idx - 1 }
  sortRows.value = fullRows
}

function moveSortDown(idx) {
  const cats = topLevelSortRows.value
  if (idx >= cats.length - 1) return
  moveSortUp(idx + 1)
}

async function saveSortOrder() {
  sortError.value = ''
  sortSaving.value = true
  try {
    const items = topLevelSortRows.value.map((row, idx) => ({
      name: row.name,
      sort_order: idx,
    }))
    await reorderManagementMenuGroups(items)
    await loadGroups()
  } catch (err) {
    sortError.value = err.message || 'ذخیره ترتیب ناموفق بود.'
  } finally {
    sortSaving.value = false
  }
}

function openCreatePage() {
  window.location.href = '/management/menu-group'
}

function openEditPage(row) {
  const name = String(row?.name || '').trim()
  if (!name) {
    return
  }
  window.location.href = `/management/menu-group?name=${encodeURIComponent(name)}`
}

function canOpenGroupNode(node) {
  return Boolean(String(node?.name || '').trim())
}

function initials(value = '') {
  return (
    String(value || 'گروه')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('') || 'گ'
  )
}

async function toggleActive(row) {
  error.value = ''
  const rowName = String(row?.name || '').trim()
  if (!rowName) {
    return
  }

  const nextActive = Number(row?.restaurant_active || 0) ? 0 : 1

  try {
    await updateManagementMenuGroup({
      name: rowName,
      restaurant_active: nextActive,
    })
    const idx = rows.value.findIndex(r => String(r?.name || '').trim() === rowName)
    if (idx !== -1) {
      rows.value[idx] = { ...rows.value[idx], restaurant_active: nextActive }
    }
  } catch (err) {
    error.value = err.message || 'تغییر وضعیت گروه ناموفق بود.'
  }
}

async function toggleHomepage(row) {
  error.value = ''
  const rowName = String(row?.name || '').trim()
  if (!rowName) {
    return
  }

  const nextValue = Number(row?.show_on_homepage || 1) ? 0 : 1

  try {
    await updateManagementMenuGroup({
      name: rowName,
      show_on_homepage: nextValue,
    })
    const idx = rows.value.findIndex(r => String(r?.name || '').trim() === rowName)
    if (idx !== -1) {
      rows.value[idx] = { ...rows.value[idx], show_on_homepage: nextValue }
    }
  } catch (err) {
    error.value = err.message || 'تغییر وضعیت نمایش صفحه اصلی ناموفق بود.'
  }
}

function readStoredViewMode() {
  try {
    const raw = localStorage.getItem('management-menu-groups-view-mode')
    if (['list', 'gallery', 'tree'].includes(raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return 'list'
}

watch(
  () => viewMode.value,
  (nextMode) => {
    try {
      localStorage.setItem('management-menu-groups-view-mode', nextMode)
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

loadGroups()
</script>

<style scoped>
.menu-groups-settings {
  display: grid;
  gap: 0.7rem;
}

.toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: end;
  flex-wrap: wrap;
}

.toolbar .input {
  width: min(340px, 100%);
}

.groups-collection {
  display: grid;
  gap: 0.6rem;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.55rem;
}

.summary-strip article {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 16px;
  background: color-mix(in srgb, var(--bg-card, #fff) 82%, var(--bg-soft, #f8fafc));
  padding: 0.75rem 0.85rem;
  display: grid;
  gap: 0.18rem;
  box-shadow: 0 10px 26px rgb(15 23 42 / 0.04);
}

.summary-strip small {
  color: var(--text-muted, #64748b);
  font-size: 0.72rem;
}

.summary-strip strong {
  color: var(--text-primary, #0f172a);
  font-size: 1.2rem;
}

.pill {
  border-radius: 999px;
  padding: 0.16rem 0.52rem;
  font-size: 0.68rem;
}

.pill.cat {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  color: var(--ink-800);
}

.pill.sub {
  background: rgb(var(--palette-june-bud-rgb) / 0.25);
  color: var(--ink-800);
}

.pill.ok {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.pill.warn {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.18);
}

.state-pill {
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-size: 0.71rem;
}

.state-pill.on {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.36);
  color: #fff;
}

.state-pill.off {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.2);
  color: var(--ink-800);
}

.group-title-cell {
  min-width: 220px;
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  align-items: center;
  gap: 0.65rem;
}

.group-thumb {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  background: linear-gradient(135deg, rgb(var(--palette-eggshell-rgb) / 0.92), rgb(var(--palette-june-bud-rgb) / 0.2));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-700, #7a6a60);
  font-weight: 800;
  flex-shrink: 0;
}

.group-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.group-title-cell strong,
.group-title-cell small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-title-cell small {
  margin-top: 0.12rem;
  color: var(--ink-500, #9a8a80);
  font-size: 0.68rem;
}

.actions {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
}

.mini {
  padding: 0.32rem 0.56rem;
  font-size: 0.7rem;
}

.gallery-status {
  position: absolute;
  top: 0.45rem;
  inset-inline-start: 0.45rem;
  border-radius: 999px;
  padding: 0.14rem 0.48rem;
  font-size: 0.68rem;
  font-weight: 700;
}

.gallery-status.on {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.74);
  color: #fff;
}

.gallery-status.off {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.22);
  color: var(--ink-800);
}

.error {
  margin: 0;
  color: var(--danger);
}

.sort-list-wrap {
  display: grid;
  gap: 0.7rem;
}

.sort-hint {
  font-size: 0.78rem;
  color: var(--ink-600, #9a8a80);
  margin: 0;
}

.sort-list {
  display: grid;
  gap: 0.35rem;
}

.sort-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.8rem;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  background: #fff;
  transition: box-shadow 0.15s;
}

.sort-row:hover {
  box-shadow: 0 2px 10px rgb(0 0 0 / 0.06);
}

.sort-index {
  font-size: 0.72rem;
  color: var(--ink-500, #b0a098);
  font-weight: 700;
  width: 1.4rem;
  text-align: center;
}

.sort-row-img {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 7px;
  overflow: hidden;
  flex-shrink: 0;
}

.sort-row-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sort-row-no-img {
  background: linear-gradient(135deg, #f5f0eb, #e8e0d6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--ink-700, #7a6a60);
}

.sort-row-info {
  flex: 1;
  display: grid;
  gap: 0.1rem;
}

.sort-row-info strong {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--ink-800, #3d2e26);
}

.sort-row-slug {
  font-size: 0.68rem;
  color: var(--ink-500, #b0a098);
  direction: ltr;
  text-align: right;
}

.sort-row-btns {
  display: flex;
  gap: 0.25rem;
}

.sort-btn {
  width: 1.8rem;
  height: 1.8rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 7px;
  background: none;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-700, #7a6a60);
  transition: background 0.15s;
}

.sort-btn:hover:not(:disabled) {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--ink-900, #1c1411);
}

.sort-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.sort-row-status {
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  white-space: nowrap;
}

.sort-row-status.on {
  background: rgb(72 199 142 / 0.12);
  color: #1a7a47;
}

.sort-row-status.off {
  background: rgb(229 57 53 / 0.1);
  color: #c62828;
}

.sort-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.3rem;
}

@media (max-width: 960px) {
  .toolbar .input {
    width: 100%;
  }

  .summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .summary-strip {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
