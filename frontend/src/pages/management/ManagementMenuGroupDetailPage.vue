<template>
  <ManagementPageScaffold :title="pageTitle" subtitle="جزئیات دسته‌بندی را به‌صورت کامل و بدون پاپ‌آپ مدیریت کنید.">
    <template #actions>
      <a class="secondary-btn" href="/management/menu-groups">بازگشت به دسته‌بندی‌ها</a>
    </template>

    <ManagementSurfaceCard tone="accent" class="group-hero-card">
      <section class="group-hero">
        <div class="hero-image" :class="{ empty: !form.image }">
          <img v-if="form.image" :src="form.image" :alt="form.item_group_name || 'تصویر دسته‌بندی'" loading="lazy" />
          <span v-else>{{ groupInitials }}</span>
        </div>
        <div class="hero-copy">
          <span class="eyebrow">{{ isEditMode ? 'ویرایش گروه محصول' : 'ساخت گروه محصول' }}</span>
          <h3>{{ form.item_group_name || 'عنوان گروه محصول' }}</h3>
          <p>
            {{ form.restaurant_description || 'عکس، وضعیت نمایش و ساختار دسته را از همین صفحه کامل کنید.' }}
          </p>
          <div class="hero-meta">
            <span :class="['state-pill', Number(form.restaurant_active || 0) ? 'on' : 'off']">
              {{ Number(form.restaurant_active || 0) ? 'فعال در سایت' : 'غیرفعال' }}
            </span>
            <span class="soft-pill">{{ Number(form.restaurant_is_subcategory || 0) ? 'زیردسته' : 'دسته اصلی' }}</span>
            <span v-if="isEditMode" class="soft-pill ltr">{{ groupName }}</span>
          </div>
        </div>
      </section>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری اطلاعات...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="success">{{ success }}</p>

    <div class="detail-layout">
      <div class="detail-main">
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

        <ManagementSurfaceCard title="توضیحات">
          <label class="full">
            توضیح
            <textarea class="textarea" v-model.trim="form.restaurant_description" placeholder="توضیح داخلی برای تیم" />
          </label>
        </ManagementSurfaceCard>
      </div>

      <aside class="detail-side">
        <ManagementSurfaceCard title="تصویر دسته‌بندی" subtitle="آپلود یا انتخاب تصویر گروه محصول">
          <ManagementImageDropzone
            v-model="form.image"
            :alt-text="form.item_group_name"
            doctype="Item Group"
            :docname="groupName"
            fieldname="image"
            @error="showUploadError"
          />
          <p class="hint image-hint">بعد از ذخیره، تصویر برای صفحه اصلی و نمایش‌های تصویری استفاده می‌شود.</p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="آیکون منو" subtitle="انتخاب آیکون دسته در صفحه منوی مشتری">
          <ManagementMenuIconSelector v-model="form.restaurant_menu_icon" />
          <p class="hint image-hint">این آیکون فقط برای دسته‌بندی‌های بالای صفحه /menu استفاده می‌شود.</p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="ساختار و وضعیت" subtitle="کنترل نوع دسته و حالت فعال بودن">
          <div class="checks-grid">
            <ManagementToggleSwitch
              :model-value="Number(form.restaurant_is_subcategory || 0) === 1"
              label="زیرگروه باشد"
              hint="برای ساخت زیردسته زیر یک گروه اصلی"
              @update:model-value="setSubcategory"
            />
            <ManagementToggleSwitch
              :model-value="Number(form.restaurant_is_menu_category || 0) === 1"
              label="دسته منوی رستوران"
              hint="در ساختار منوی مشتری استفاده شود"
              @update:model-value="setMenuCategory"
            />
            <ManagementToggleSwitch
              :model-value="Number(form.is_group || 0) === 1"
              label="گروه والدپذیر"
              hint="امکان داشتن زیرگروه در ERPNext"
              @update:model-value="setIsGroup"
            />
            <ManagementToggleSwitch
              :model-value="Number(form.restaurant_active || 0) === 1"
              label="فعال در سایت"
              hint="خاموش شود، این دسته به مشتری نمایش داده نمی‌شود"
              @update:model-value="setActive"
            />
            <ManagementToggleSwitch
              :model-value="Number(form.show_on_homepage || 0) === 1"
              label="نمایش در صفحه اصلی"
              hint="برای دسته‌های مهم و پرفروش روشن کنید"
              @update:model-value="setHomepage"
            />
          </div>
        </ManagementSurfaceCard>
      </aside>
    </div>

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
import ManagementImageDropzone from '@/components/management/ManagementImageDropzone.vue'
import ManagementMenuIconSelector from '@/components/management/ManagementMenuIconSelector.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
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
const groupInitials = computed(() => initials(form.item_group_name || groupName.value || 'گروه'))

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
    show_on_homepage: 1,
    restaurant_menu_icon: '',
    image: '',
  }
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

function showUploadError(message) {
  error.value = message || 'آپلود تصویر ناموفق بود.'
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
  form.show_on_homepage = Number(next.show_on_homepage ?? 1) ? 1 : 0
  form.restaurant_menu_icon = String(next.restaurant_menu_icon || '').trim()
  form.image = String(next.image || '').trim()
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

function setSubcategory(value) {
  const checked = value ? 1 : 0
  form.restaurant_is_subcategory = checked
  if (checked === 1) {
    form.restaurant_is_menu_category = 1
    form.is_group = 0
  } else if (Number(form.restaurant_is_menu_category || 0) === 1) {
    form.is_group = 1
  }
}

function setMenuCategory(value) {
  const checked = value ? 1 : 0
  form.restaurant_is_menu_category = checked
  if (checked === 1 && Number(form.restaurant_is_subcategory || 0) !== 1) {
    form.is_group = 1
  }
}

function setIsGroup(value) {
  form.is_group = value ? 1 : 0
}

function setActive(value) {
  form.restaurant_active = value ? 1 : 0
}

function setHomepage(value) {
  form.show_on_homepage = value ? 1 : 0
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
    show_on_homepage: Number(form.show_on_homepage || 0) ? 1 : 0,
    restaurant_menu_icon: form.restaurant_menu_icon,
    image: form.image,
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

.group-hero-card {
  overflow: hidden;
}

.group-hero {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
}

.hero-image {
  width: 112px;
  height: 112px;
  border-radius: 26px;
  overflow: hidden;
  background: linear-gradient(135deg, rgb(var(--palette-eggshell-rgb) / 0.92), rgb(var(--palette-june-bud-rgb) / 0.24));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  display: grid;
  place-items: center;
  color: var(--ink-700, #7a6a60);
  font-weight: 900;
  font-size: 1.7rem;
  box-shadow: 0 18px 38px rgb(15 23 42 / 0.08);
}

.hero-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-copy {
  min-width: 0;
  display: grid;
  gap: 0.45rem;
}

.eyebrow {
  color: var(--text-muted);
  font-size: 0.76rem;
  font-weight: 800;
}

.hero-copy h3,
.hero-copy p {
  margin: 0;
}

.hero-copy h3 {
  color: var(--text-primary);
  font-size: clamp(1.1rem, 2vw, 1.55rem);
}

.hero-copy p {
  color: var(--text-muted);
  line-height: 1.8;
  max-width: 68ch;
}

.hero-meta {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  align-items: center;
}

.state-pill,
.soft-pill {
  border-radius: 999px;
  padding: 0.18rem 0.62rem;
  font-size: 0.74rem;
  font-weight: 800;
}

.state-pill.on {
  background: rgb(72 199 142 / 0.15);
  color: #167544;
}

.state-pill.off {
  background: rgb(229 57 53 / 0.1);
  color: #c62828;
}

.soft-pill {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: var(--ink-700, #7a6a60);
}

.ltr {
  direction: ltr;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.72fr);
  gap: 0.85rem;
  align-items: start;
}

.detail-main,
.detail-side {
  display: grid;
  gap: 0.85rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.form-grid label,
.full {
  display: grid;
  gap: 0.32rem;
  font-size: 0.82rem;
}

.checks-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.55rem;
}

.image-hint {
  margin-top: 0.7rem;
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

@media (max-width: 980px) {
  .detail-layout {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 860px) {
  .group-hero {
    grid-template-columns: minmax(0, 1fr);
  }

  .hero-image {
    width: 100%;
    height: 180px;
  }

  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
