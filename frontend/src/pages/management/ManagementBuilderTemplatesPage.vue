<template>
  <ManagementPageScaffold title="قالب‌های سفارشی‌سازی" subtitle="مدیریت قالب‌های سفارشی‌سازی محصولات">
    <template #actions>
      <button class="primary-btn" type="button" @click="goToCreate">+ قالب جدید</button>
    </template>

    <ManagementSurfaceCard tone="accent" class="filter-card">
      <div class="toolbar">
        <input class="input" v-model="search" placeholder="جستجوی قالب..." @keydown.enter.prevent="loadTemplates" />
        <button class="primary-btn" type="button" @click="loadTemplates" :disabled="loading">
          {{ loading ? 'در حال جستجو...' : 'جستجو' }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری قالب‌ها...</p>
    <p class="error" v-if="error">{{ error }}</p>

    <ManagementSurfaceCard v-if="!loading && !templates.length" title="قالبی وجود ندارد">
      <div class="empty-state">
        <LayersIcon class="icon-lg" />
        <p>هنوز قالب سفارشی‌سازی ایجاد نشده است.</p>
        <button class="primary-btn" type="button" @click="goToCreate">ایجاد اولین قالب</button>
      </div>
    </ManagementSurfaceCard>

    <ManagementDataTable
      v-else-if="!loading"
      :columns="columns"
      :rows="templates"
      @row-click="goToEdit"
    >
      <template #cell.is_active="{ row }">
        <span class="status-badge" :class="row.is_active ? 'active' : 'inactive'">
          {{ row.is_active ? 'فعال' : 'غیرفعال' }}
        </span>
      </template>
      <template #cell.steps_count="{ row }">
        {{ row.steps_count || 0 }}
      </template>
      <template #cell.modified="{ row }">
        {{ formatDate(row.modified) }}
      </template>
      <template #cell.actions="{ row }">
        <div class="row-actions">
          <button class="icon-btn" title="ویرایش" @click.stop="goToEdit(row)">
            <PencilIcon class="icon-sm" />
          </button>
          <button class="icon-btn" title="تکرار" @click.stop="duplicateTemplate(row)">
            <CopyIcon class="icon-sm" />
          </button>
          <button class="icon-btn danger" title="غیرفعال کردن" @click.stop="toggleActive(row)">
            <ToggleIcon class="icon-sm" />
          </button>
        </div>
      </template>
    </ManagementDataTable>
  </ManagementPageScaffold>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import { callMethodByPathGET, callMethodByPath } from '@/utils/api'
import {
  Layers as LayersIcon,
  Pencil as PencilIcon,
  Copy as CopyIcon,
  ToggleLeft as ToggleIcon,
} from 'lucide-vue-next'

const templates = ref([])
const loading = ref(false)
const error = ref('')
const search = ref('')

const columns = [
  { key: 'title', label: 'عنوان قالب' },
  { key: 'slug', label: 'اسلاگ' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'steps_count', label: 'تعداد مراحل' },
  { key: 'modified', label: 'آخرین تغییر' },
  { key: 'actions', label: 'عملیات' },
]

async function loadTemplates() {
  loading.value = true
  error.value = ''
  try {
    const result = await callMethodByPathGET('restaurant.api.list_builder_templates', {
      search: search.value || undefined,
    })
    const data = result?.data || result
    templates.value = Array.isArray(data?.templates) ? data.templates : []
  } catch (e) {
    error.value = e.message || 'خطا در بارگذاری قالب‌ها'
    templates.value = []
  } finally {
    loading.value = false
  }
}

function goToCreate() {
  window.location.href = '/management/builder-template/new'
}

function goToEdit(row) {
  window.location.href = `/management/builder-template/edit/${row.name}`
}

async function duplicateTemplate(row) {
  if (!confirm(`قالب "${row.title}" تکرار شود؟`)) return
  try {
    loading.value = true
    const result = await callMethodByPath('restaurant.api.duplicate_builder_template', { name: row.name })
    const data = result?.data || result
    error.value = ''
    await loadTemplates()
    if (data?.name) {
      window.location.href = `/management/builder-template/edit/${data.name}`
    }
  } catch (e) {
    error.value = e.message || 'خطا در تکرار قالب'
  } finally {
    loading.value = false
  }
}

async function toggleActive(row) {
  try {
    loading.value = true
    await callMethodByPath('restaurant.api.save_builder_template', {
      template_data: JSON.stringify({ name: row.name, is_active: !row.is_active }),
    })
    row.is_active = !row.is_active
  } catch (e) {
    error.value = e.message || 'خطا در تغییر وضعیت'
  } finally {
    loading.value = false
  }
}

function formatDate(d) {
  if (!d) return '-'
  try {
    return new Date(d).toLocaleDateString('fa-IR')
  } catch {
    return d
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 1rem;
}
.toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: #6b7280;
}
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}
.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}
.status-badge.inactive {
  background: #f3f4f6;
  color: #6b7280;
}
.row-actions {
  display: flex;
  gap: 0.25rem;
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: #4b5563;
}
.icon-btn:hover {
  background: #f3f4f6;
}
.icon-btn.danger {
  color: #dc2626;
  border-color: #fca5a5;
}
.icon-btn.danger:hover {
  background: #fef2f2;
}
</style>
