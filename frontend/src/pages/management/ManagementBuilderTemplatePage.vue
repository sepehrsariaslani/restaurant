<template>
  <ManagementPageScaffold :title="pageTitle" :subtitle="pageSubtitle">
    <template #actions>
      <span v-if="hasUnsavedChanges" class="unsaved-chip">تغییرات ذخیره نشده</span>
      <a class="secondary-btn" href="/management/builder-templates">بازگشت</a>
      <button class="primary-btn" type="button" @click="saveTemplate" :disabled="!canSave">
        {{ saving ? 'در حال ذخیره...' : 'ذخیره قالب' }}
      </button>
    </template>

    <p class="muted" v-if="loading">
      <ManagementBearLoader :size="40" /> در حال بارگذاری قالب سفارشی‌سازی...
    </p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="error" v-if="validationErrors.length">
      لطفاً خطاهای زیر را اصلاح کنید.
      <ul>
        <li v-for="(err, i) in validationErrors" :key="i">{{ err }}</li>
      </ul>
    </p>

    <template v-if="!loading">
      <!-- Template Settings -->
      <ManagementSurfaceCard title="تنظیمات قالب" subtitle="اطلاعات عمومی قالب سفارشی‌سازی" class="settings-card">
        <div class="settings-grid">
          <label>
            عنوان قالب <span class="required">*</span>
            <input class="input" v-model="form.title" placeholder="مثلاً: سفارشی‌سازی پیتزا" :class="{ 'is-invalid': !form.title.trim() }" />
            <small v-if="!form.title.trim()" class="error-text">نام قالب نمی‌تواند خالی باشد.</small>
          </label>
          <label>
            اسلاگ <span class="required">*</span>
            <input class="input" v-model="form.slug" placeholder="pizza-customization" dir="ltr" :class="{ 'is-invalid': !form.slug.trim() }" />
          </label>
          <label>
            توضیحات
            <textarea class="textarea" v-model="form.description" placeholder="توضیح اختیاری درباره این قالب" rows="2" />
          </label>
          <ManagementToggleSwitch v-model="form.is_active" label="قالب فعال" hint="در سایت مشتری نمایش داده شود" />
        </div>
      </ManagementSurfaceCard>

      <!-- Display Settings -->
      <ManagementSurfaceCard title="تنظیمات نمایش" subtitle="ظاهر و رفتار قالب در سایت مشتری">
        <div class="settings-grid">
          <label>
            حالت چیدمان
            <select class="input" v-model="form.layout_mode">
              <option value="vertical_steps">مرحله‌ای عمودی</option>
              <option value="horizontal_tabs">تب‌های افقی</option>
              <option value="accordion">آکاردئون</option>
              <option value="wizard">مرحله‌ای (ویزارد)</option>
            </select>
          </label>
          <label>
            رنگ اصلی
            <input class="input" v-model="form.primary_color" type="color" dir="ltr" />
          </label>
          <ManagementToggleSwitch v-model="form.show_summary_panel" label="نمایش خلاصه" hint="خلاصه انتخاب‌ها را نشان بده" />
          <ManagementToggleSwitch v-model="form.show_price_live" label="قیمت زنده" hint="قیمت نهایی به‌صورت زنده محاسبه شود" />
        </div>
        <div class="settings-grid" style="margin-top: 1rem;">
          <ManagementToggleSwitch v-model="form.allow_skip_steps" label="اجازه رد شدن" hint="مشتری بتواند مراحل اختیاری را رد کند" />
          <ManagementToggleSwitch v-model="form.allow_go_back" label="اجازه بازگشت" hint="مشتری بتواند به مرحله قبل برگردد" />
          <ManagementToggleSwitch v-model="form.require_all_required" label="اجبار همه مراحل" hint="همه مراحل اجباری باید تکمیل شوند" />
          <label>
            حداکثر انتخاب کل
            <PersianNumberInput v-model="form.max_total_selections" :min="0" />
            <small class="hint">0 یعنی بدون محدودیت</small>
          </label>
        </div>
      </ManagementSurfaceCard>

      <!-- Steps Configuration -->
      <ManagementSurfaceCard title="مراحل سفارشی‌سازی" subtitle="مراحل و گزینه‌ها را اضافه و تنظیم کنید">
        <div class="steps-toolbar">
          <button class="primary-btn" type="button" @click="addStep">+ افزودن مرحله</button>
        </div>

        <div v-if="!form.steps.length" class="empty-steps">
          <p class="muted">هنوز مرحله‌ای اضافه نشده است.</p>
          <button class="secondary-btn" type="button" @click="addStep">افزودن اولین مرحله</button>
        </div>

        <div class="steps-list">
          <BuilderStepCard
            v-for="(step, index) in form.steps"
            :key="step.step_key || step.name || index"
            :step="step"
            :step-index="index"
            :steps-length="form.steps.length"
            :item-options="itemOptions"
            @update:step="updateStep(index, $event)"
            @move-up="moveStep(index, -1)"
            @move-down="moveStep(index, 1)"
            @delete="deleteStep(index)"
          />
        </div>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import ManagementBearLoader from '@/components/management/ManagementBearLoader.vue'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import BuilderStepCard from '@/components/management/builder/BuilderStepCard.vue'
import { callMethodByPath, callMethodByPathGET } from '@/utils/api'

const props = defineProps({
  templateId: { type: String, default: '' },
})

const isEditMode = computed(() => Boolean(props.templateId))
const pageTitle = computed(() => (isEditMode.value ? `ویرایش قالب: ${form.title}` : 'سفارشی‌سازی جدید'))
const pageSubtitle = computed(() => (isEditMode.value ? 'تغییرات قالب را ویرایش و ذخیره کنید' : 'قالب جدیدی برای سفارشی‌سازی محصول ایجاد کنید'))

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const validationErrors = ref([])
const hasUnsavedChanges = ref(false)
const originalSnapshot = ref('')

const form = reactive({
  name: '',
  title: '',
  slug: '',
  description: '',
  is_active: true,
  layout_mode: 'vertical_steps',
  show_summary_panel: true,
  show_price_live: true,
  primary_color: '#1a73e8',
  background_image: '',
  allow_skip_steps: false,
  allow_go_back: true,
  require_all_required: true,
  max_total_selections: 0,
  steps: [],
})

const itemOptions = ref([])

const canSave = computed(() => {
  return !saving.value && !loading.value && hasUnsavedChanges.value && form.title.trim() && form.steps.length > 0
})

function createEmptyStep(index) {
  return {
    step_title: `مرحله ${index + 1}`,
    step_key: `step-${Date.now()}-${index}`,
    step_description: '',
    sort_order: index,
    selection_mode: 'single',
    min_select: 1,
    max_select: 1,
    is_required: true,
    show_step_price: true,
    step_icon: '',
    options: [],
    conditional_logic: {},
  }
}

function addStep() {
  form.steps.push(createEmptyStep(form.steps.length))
  hasUnsavedChanges.value = true
}

function updateStep(index, updatedStep) {
  form.steps[index] = { ...updatedStep }
  hasUnsavedChanges.value = true
}

function moveStep(index, direction) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= form.steps.length) return
  const temp = form.steps[index]
  form.steps.splice(index, 1)
  form.steps.splice(newIndex, 0, temp)
  form.steps.forEach((s, i) => {
    s.sort_order = i
  })
  hasUnsavedChanges.value = true
}

function deleteStep(index) {
  const step = form.steps[index]
  if (step.options?.length && !confirm(`مرحله "${step.step_title}" با ${step.options.length} گزینه حذف شود؟`)) return
  form.steps.splice(index, 1)
  form.steps.forEach((s, i) => {
    s.sort_order = i
  })
  hasUnsavedChanges.value = true
}

function validate() {
  const errors = []
  if (!form.title.trim()) errors.push('نام قالب سفارشی‌سازی نمی‌تواند خالی باشد.')
  if (!form.slug.trim()) errors.push('اسلاگ نمی‌تواند خالی باشد.')
  if (form.steps.length === 0) errors.push('حداقل یک مرحله باید اضافه شود.')

  const stepNames = new Set()
  form.steps.forEach((step, i) => {
    if (!step.step_title.trim()) {
      errors.push(`نام مرحله ${i + 1} نمی‌تواند خالی باشد.`)
    } else {
      const nameLower = step.step_title.trim().toLowerCase()
      if (stepNames.has(nameLower)) {
        errors.push(`نام مراحل نباید تکراری باشد: ${step.step_title}`)
      }
      stepNames.add(nameLower)
    }
    if (Number(step.min_select) > Number(step.max_select)) {
      errors.push(`حداقل انتخاب نمی‌تواند بیشتر از حداکثر باشد (مرحله ${i + 1}).`)
    }
    if (Number(step.min_select) < 0) {
      errors.push(`حداقل انتخاب نمی‌تواند منفی باشد (مرحله ${i + 1}).`)
    }
    if (Number(step.max_select) < 1) {
      errors.push(`حداکثر انتخاب باید بیشتر از صفر باشد (مرحله ${i + 1}).`)
    }
    if (step.is_required && Number(step.min_select) < 1) {
      errors.push(`مراحل اجباری حداقل باید یک انتخاب داشته باشند (مرحله ${i + 1}).`)
    }
    if (step.options.length === 0) {
      errors.push(`هر مرحله باید حداقل یک گزینه داشته باشد (مرحله ${i + 1}).`)
    }
  })

  return errors
}

async function saveTemplate() {
  validationErrors.value = validate()
  if (validationErrors.value.length) return

  saving.value = true
  error.value = ''
  try {
    const payload = {
      name: form.name || undefined,
      title: form.title,
      slug: form.slug,
      description: form.description,
      is_active: form.is_active,
      layout_mode: form.layout_mode,
      show_summary_panel: form.show_summary_panel,
      show_price_live: form.show_price_live,
      primary_color: form.primary_color,
      background_image: form.background_image,
      allow_skip_steps: form.allow_skip_steps,
      allow_go_back: form.allow_go_back,
      require_all_required: form.require_all_required,
      max_total_selections: form.max_total_selections,
      steps: form.steps.map((s, i) => ({
        ...s,
        sort_order: i,
      })),
    }
    const result = await callMethodByPath('restaurant.api.save_builder_template', {
      template_data: JSON.stringify(payload),
    })
    const data = result?.data || result
    hasUnsavedChanges.value = false
    originalSnapshot.value = JSON.stringify(form)
    if (data?.name) {
      form.name = data.name
    }
    if (!isEditMode.value && data?.name) {
      window.history.replaceState({}, '', `/management/builder-template/edit/${data.name}`)
    }
  } catch (e) {
    error.value = e.message || 'خطا در ذخیره‌سازی'
  } finally {
    saving.value = false
  }
}

async function loadTemplate() {
  if (!props.templateId) {
    loading.value = false
    originalSnapshot.value = JSON.stringify(form)
    return
  }
  try {
    const result = await callMethodByPathGET('restaurant.api.get_builder_template_detail', {
      name: props.templateId,
    })
    const data = result?.data || result
    const template = data?.template || data
    if (template) {
      form.name = template.name || ''
      form.title = template.title || ''
      form.slug = template.slug || ''
      form.description = template.description || ''
      form.is_active = template.is_active !== false
      form.layout_mode = template.layout_mode || 'vertical_steps'
      form.show_summary_panel = template.show_summary_panel !== false
      form.show_price_live = template.show_price_live !== false
      form.primary_color = template.primary_color || '#1a73e8'
      form.background_image = template.background_image || ''
      form.allow_skip_steps = Boolean(template.allow_skip_steps)
      form.allow_go_back = template.allow_go_back !== false
      form.require_all_required = template.require_all_required !== false
      form.max_total_selections = template.max_total_selections || 0
      form.steps = Array.isArray(template.steps) ? template.steps : []
    }
    originalSnapshot.value = JSON.stringify(form)
    hasUnsavedChanges.value = false
  } catch (e) {
    error.value = e.message || 'خطا در بارگذاری قالب'
  } finally {
    loading.value = false
  }
}

async function loadItemOptions() {
  try {
    const result = await callMethodByPathGET('restaurant.api.list_builder_option_items', {
      limit: 500,
    })
    const data = result?.data || result
    const rows = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
    itemOptions.value = rows.map((r) => ({
      value: r.value || r.name,
      label: r.label || r.item_name || r.name,
      item_name: r.item_name || r.label || r.name,
      item_code: r.item_code || r.name,
      image: r.image || '',
      standard_rate: Number(r.standard_rate) || 0,
      stock_uom: r.stock_uom || '',
      item_group: r.item_group || '',
    }))
  } catch {
    itemOptions.value = []
  }
}

// Track changes
let stopWatch
onMounted(async () => {
  await Promise.all([loadTemplate(), loadItemOptions()])
  stopWatch = watch(
    () => JSON.stringify(form),
    (val) => {
      hasUnsavedChanges.value = val !== originalSnapshot.value
    },
  )
})
</script>

<style scoped>
.settings-card {
  margin-bottom: 1rem;
}
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.required {
  color: #dc2626;
}
.error-text {
  color: #dc2626;
  font-size: 0.8rem;
}
.is-invalid {
  border-color: #fca5a5 !important;
}
.steps-toolbar {
  margin-bottom: 1rem;
}
.empty-steps {
  text-align: center;
  padding: 2rem;
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
}
.unsaved-chip {
  display: inline-block;
  padding: 4px 12px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}
.steps-list {
  margin-top: 1rem;
}
</style>
