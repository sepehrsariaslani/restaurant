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
import ManagementTreeView from '@/components/management/ManagementTreeView.vue'
import {
  listManagementMenuGroups,
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
]

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
  } catch (err) {
    error.value = err.message || 'بارگذاری گروه‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function openCreatePage() {
  window.location.href = '/desk/menu-group'
}

function openEditPage(row) {
  const name = String(row?.name || '').trim()
  if (!name) {
    return
  }
  window.location.href = `/desk/menu-group?name=${encodeURIComponent(name)}`
}

function canOpenGroupNode(node) {
  return Boolean(String(node?.name || '').trim())
}

async function toggleActive(row) {
  error.value = ''
  const rowName = String(row?.name || '').trim()
  if (!rowName) {
    return
  }

  try {
    await updateManagementMenuGroup({
      name: rowName,
      restaurant_active: Number(row?.restaurant_active || 0) ? 0 : 1,
    })
    await loadGroups()
  } catch (err) {
    error.value = err.message || 'تغییر وضعیت گروه ناموفق بود.'
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

@media (max-width: 960px) {
  .toolbar .input {
    width: 100%;
  }
}
</style>
