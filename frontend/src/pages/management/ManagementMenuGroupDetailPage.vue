<template>
  <ManagementPageScaffold :title="pageTitle" subtitle="جزئیات دسته‌بندی را به‌صورت کامل و بدون پاپ‌آپ مدیریت کنید.">
    <template #actions>
      <a class="secondary-btn" href="/management/menu-groups">بازگشت به دسته‌بندی‌ها</a>
    </template>

    <ManagementSurfaceCard tone="accent">
      <p class="hint">
        از این صفحه می‌توانید دسته یا زیردسته جدید بسازید یا اطلاعات یک دسته موجود را کامل ویرایش کنید.
      </p>
      <p v-if="isEditMode" class="hint">شناسه: {{ groupName }}</p>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری اطلاعات...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="success">{{ success }}</p>

    <ManagementSurfaceCard title="اطلاعات پایه" subtitle="مشخصات اصلی گروه محصول">
      <div class="form-grid">
        <label>
          عنوان
          <input class="input" v-model.trim="form.item_group_name" placeholder="مثال: نوشیدنی‌ها" />
        </label>

        <label>
          اسلاگ
          <input class="input" v-model.trim="form.restaurant_slug" placeholder="مثال: drinks" />
        </label>

        <label>
          گروه والد
          <SearchableDropdown
            v-model="form.parent_item_group"
            :options="parentOptions"
            placeholder="انتخاب گروه والد"
            search-placeholder="جستجوی گروه والد..."
          />
        </label>

        <label>
          ترتیب نمایش
          <input class="input" v-model.number="form.restaurant_sort_order" type="number" min="0" />
        </label>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="ساختار و وضعیت" subtitle="کنترل نوع دسته و حالت فعال بودن">
      <div class="checks-grid">
        <label class="check">
          <input type="checkbox" :checked="Number(form.restaurant_is_subcategory || 0) === 1" @change="onChangeSubcategory" />
          زیرگروه باشد
        </label>

        <label class="check">
          <input type="checkbox" :checked="Number(form.restaurant_is_menu_category || 0) === 1" @change="onChangeMenuCategory" />
          دسته منوی رستوران
        </label>

        <label class="check">
          <input type="checkbox" :checked="Number(form.is_group || 0) === 1" @change="onChangeIsGroup" />
          is_group
        </label>

        <label class="check">
          <input type="checkbox" :checked="Number(form.restaurant_active || 0) === 1" @change="onChangeActive" />
          فعال در سایت
        </label>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="توضیحات">
      <label class="full">
        توضیح
        <textarea class="textarea" v-model.trim="form.restaurant_description" placeholder="توضیح داخلی برای تیم" />
      </label>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard>
      <div class="actions">
        <a class="secondary-btn" href="/management/menu-groups">انصراف</a>
        <button class="primary-btn" type="button" :disabled="saving || loading" @click="saveGroup">
          {{ saving ? 'در حال ذخیره...' : isEditMode ? 'ذخیره تغییرات' : 'ایجاد دسته' }}
        </button>
      </div>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  createManagementMenuGroup,
  getManagementMenuGroup,
  listManagementItemGroupParents,
  updateManagementMenuGroup,
} from '@/utils/api'
import { parseQuery } from '@/utils/format'

const query = parseQuery()
const groupName = ref(String(query.name || '').trim())

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const parentRows = ref([])

const form = reactive(createEmptyForm())

const isEditMode = computed(() => Boolean(groupName.value))
const pageTitle = computed(() => (isEditMode.value ? 'ویرایش دسته‌بندی محصول' : 'ایجاد دسته‌بندی محصول'))

const parentOptions = computed(() =>
  (parentRows.value || []).map((row) => ({
    value: String(row?.name || '').trim(),
    label: String(row?.item_group_name || row?.name || '').trim(),
  })),
)

watch(
  () => form.restaurant_is_subcategory,
  (value) => {
    const isSub = Number(value || 0) === 1
    if (isSub) {
      form.restaurant_is_menu_category = 1
      form.is_group = 0
      return
    }
    if (Number(form.restaurant_is_menu_category || 0) === 1) {
      form.is_group = 1
    }
  },
)

watch(
  () => form.restaurant_is_menu_category,
  (value) => {
    const isMenuCategory = Number(value || 0) === 1
    if (isMenuCategory && Number(form.restaurant_is_subcategory || 0) !== 1) {
      form.is_group = 1
    }
  },
)

function createEmptyForm() {
  return {
    item_group_name: '',
    parent_item_group: '',
    is_group: 1,
    restaurant_is_menu_category: 1,
    restaurant_is_subcategory: 0,
    restaurant_active: 1,
    restaurant_slug: '',
    restaurant_sort_order: 0,
    restaurant_description: '',
  }
}

function writeForm(payload = {}) {
  const next = {
    ...createEmptyForm(),
    ...(payload || {}),
  }

  form.item_group_name = String(next.item_group_name || '').trim()
  form.parent_item_group = String(next.parent_item_group || '').trim()
  form.is_group = Number(next.is_group || 0) ? 1 : 0
  form.restaurant_is_menu_category = Number(next.restaurant_is_menu_category || 0) ? 1 : 0
  form.restaurant_is_subcategory = Number(next.restaurant_is_subcategory || 0) ? 1 : 0
  form.restaurant_active = Number(next.restaurant_active || 0) ? 1 : 0
  form.restaurant_slug = String(next.restaurant_slug || '').trim()
  form.restaurant_sort_order = Number(next.restaurant_sort_order || 0) || 0
  form.restaurant_description = String(next.restaurant_description || '').trim()
}

async function loadParentGroups() {
  const parents = await listManagementItemGroupParents({})
  parentRows.value = Array.isArray(parents) ? parents : []
}

async function loadCurrentGroup() {
  if (!isEditMode.value) {
    return
  }

  const payload = await getManagementMenuGroup(groupName.value)
  writeForm(payload)
}

function applyDefaultParentIfNeeded() {
  if (form.parent_item_group) {
    return
  }
  const firstParent = parentOptions.value[0]?.value || ''
  form.parent_item_group = firstParent
}

async function bootstrap() {
  loading.value = true
  error.value = ''
  try {
    await loadParentGroups()
    if (isEditMode.value) {
      await loadCurrentGroup()
    }
    applyDefaultParentIfNeeded()
  } catch (bootError) {
    error.value = bootError.message || 'بارگذاری اطلاعات صفحه ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function onChangeSubcategory(event) {
  const checked = Number(event?.target?.checked ? 1 : 0)
  form.restaurant_is_subcategory = checked
  if (checked === 1) {
    form.restaurant_is_menu_category = 1
    form.is_group = 0
  } else if (Number(form.restaurant_is_menu_category || 0) === 1) {
    form.is_group = 1
  }
}

function onChangeMenuCategory(event) {
  const checked = Number(event?.target?.checked ? 1 : 0)
  form.restaurant_is_menu_category = checked
  if (checked === 1 && Number(form.restaurant_is_subcategory || 0) !== 1) {
    form.is_group = 1
  }
}

function onChangeIsGroup(event) {
  form.is_group = Number(event?.target?.checked ? 1 : 0)
}

function onChangeActive(event) {
  form.restaurant_active = Number(event?.target?.checked ? 1 : 0)
}

function normalizePayload() {
  return {
    name: groupName.value,
    item_group_name: form.item_group_name,
    parent_item_group: form.parent_item_group,
    is_group: Number(form.is_group || 0) ? 1 : 0,
    restaurant_is_menu_category: Number(form.restaurant_is_menu_category || 0) ? 1 : 0,
    restaurant_is_subcategory: Number(form.restaurant_is_subcategory || 0) ? 1 : 0,
    restaurant_active: Number(form.restaurant_active || 0) ? 1 : 0,
    restaurant_slug: form.restaurant_slug,
    restaurant_sort_order: Number(form.restaurant_sort_order || 0) || 0,
    restaurant_description: form.restaurant_description,
  }
}

async function saveGroup() {
  error.value = ''
  success.value = ''

  if (!form.item_group_name) {
    error.value = 'عنوان گروه الزامی است.'
    return
  }
  if (!form.parent_item_group) {
    error.value = 'گروه والد را انتخاب کنید.'
    return
  }

  saving.value = true
  try {
    const payload = normalizePayload()
    if (isEditMode.value) {
      await updateManagementMenuGroup(payload)
      success.value = 'تغییرات با موفقیت ذخیره شد.'
    } else {
      const created = await createManagementMenuGroup(payload)
      const createdName = String(created?.name || '').trim()
      if (createdName) {
        window.location.replace(`/management/menu-group?name=${encodeURIComponent(createdName)}`)
        return
      }
      success.value = 'گروه جدید با موفقیت ایجاد شد.'
      window.location.replace('/management/menu-groups')
      return
    }
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره دسته‌بندی ناموفق بود.'
  } finally {
    saving.value = false
  }
}

bootstrap()
</script>

<style scoped>
.hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.form-grid label,
.full {
  display: grid;
  gap: 0.24rem;
  font-size: 0.8rem;
}

.checks-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.error {
  margin: 0;
  color: var(--danger);
}

.success {
  margin: 0;
  color: var(--accent-green);
}

@media (max-width: 860px) {
  .form-grid,
  .checks-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
