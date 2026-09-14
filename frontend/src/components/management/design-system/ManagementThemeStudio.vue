<template>
  <div class="theme-studio">
    <ManagementSurfaceCard tone="accent">
      <div class="toolbar">
        <button class="primary-btn" type="button" @click="saveSettings">{{ saveButtonLabel || (saveMode === 'draft' ? 'ذخیره پیش‌نویس تم' : 'ذخیره تنظیمات') }}</button>
        <button class="secondary-btn" type="button" @click="resetToDefaults">بازگشت به پیش‌فرض</button>
        <span class="muted">{{ saveState }}</span>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="تم‌های آماده ایرانی" subtitle="یک تم آماده را انتخاب کنید یا روی آن شخصی‌سازی انجام دهید.">
      <div class="preset-grid">
        <article
          v-for="preset in presets"
          :key="preset.id"
          class="preset-card"
          :class="{ active: activePresetId === preset.id }"
        >
          <header>
            <strong>{{ preset.name }}</strong>
            <span v-if="activePresetId === preset.id" class="badge">فعال</span>
          </header>
          <p class="muted preset-desc">{{ preset.description }}</p>
          <div class="preset-swatches">
            <i :style="{ backgroundColor: preset.colors.primary }" title="Primary"></i>
            <i :style="{ backgroundColor: preset.colors.accent }" title="Accent"></i>
            <i :style="{ backgroundColor: preset.colors.surface }" title="Surface"></i>
            <i :style="{ backgroundColor: preset.colors.text }" title="Text"></i>
          </div>
          <div class="preset-actions">
            <button class="secondary-btn" type="button" @click="applyPreset(preset)">
              پیش‌نمایش
            </button>
            <button class="primary-btn" type="button" @click="applyPresetAndSave(preset)">
              انتخاب و ذخیره
            </button>
          </div>
        </article>
      </div>
    </ManagementSurfaceCard>

    <section class="grid-2">
      <ManagementSurfaceCard title="رنگ‌های عمومی" subtitle="پالت اصلی وب‌سایت و پنل مدیریت">
        <div class="field-grid">
          <label v-for="item in generalFields" :key="item.key">
            <span>{{ item.label }}</span>
            <div class="color-input">
              <input v-model="form[item.key]" type="color" />
              <input class="input" v-model="form[item.key]" type="text" />
            </div>
          </label>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="رنگ وضعیت‌ها" subtitle="موفقیت، خطا و هشدار در کل پنل">
        <div class="field-grid">
          <label v-for="item in statusFields" :key="item.key">
            <span>{{ item.label }}</span>
            <div class="color-input">
              <input v-model="form[item.key]" type="color" />
              <input class="input" v-model="form[item.key]" type="text" />
            </div>
          </label>
        </div>
      </ManagementSurfaceCard>
    </section>

    <ManagementSurfaceCard title="رنگ‌های POS" subtitle="ظاهر صفحه POS و حالت میزها">
      <div class="field-grid pos-grid">
        <label v-for="item in posFields" :key="item.key">
          <span>{{ item.label }}</span>
          <div class="color-input">
            <input v-model="form[item.key]" type="color" />
            <input class="input" v-model="form[item.key]" type="text" />
          </div>
        </label>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="پیش‌نمایش سریع">
      <div class="preview-grid">
        <article>
          <small>Primary</small>
          <strong>دکمه اصلی</strong>
          <button class="preview-btn preview-btn-primary" type="button">اقدام اصلی</button>
        </article>
        <article>
          <small>Accent</small>
          <strong>اکسنت ثانویه</strong>
          <button class="preview-btn preview-btn-accent" type="button">اقدام ثانویه</button>
        </article>
        <article>
          <small>Success</small>
          <strong>پیام موفقیت</strong>
          <p class="preview-chip preview-chip-success">عملیات با موفقیت انجام شد.</p>
        </article>
        <article>
          <small>Danger</small>
          <strong>پیام خطا</strong>
          <p class="preview-chip preview-chip-danger">خطا در ذخیره‌سازی اطلاعات.</p>
        </article>
        <article>
          <small>POS Success</small>
          <strong>میز خالی</strong>
          <p class="preview-chip preview-chip-pos-success">status-empty</p>
        </article>
        <article>
          <small>POS Danger</small>
          <strong>میز اشغال</strong>
          <p class="preview-chip preview-chip-pos-danger">status-occupied</p>
        </article>
      </div>
    </ManagementSurfaceCard>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  applyThemeSettings,
  defaultThemeSettings,
  hydrateThemeSettingsFromServer,
  loadThemeSettings,
  resetThemeSettings,
  sanitizeThemeSettings,
  saveThemeSettingsToServer,
  themePresets,
} from '@/utils/themeSettings'

const props = defineProps({
  initialSettings: {
    type: Object,
    default: null,
  },
  saveMode: {
    type: String,
    default: 'live',
  },
  saveButtonLabel: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['save-draft', 'reset-draft'])

const generalFields = [
  { key: 'primary', label: 'رنگ اصلی برند' },
  { key: 'accent', label: 'رنگ اکسنت' },
  { key: 'surface', label: 'پس‌زمینه کارت‌ها' },
  { key: 'surfaceAlt', label: 'سطح ثانویه (جعبه‌ها)' },
  { key: 'background', label: 'پس‌زمینه اصلی صفحه' },
  { key: 'border', label: 'رنگ مرزها' },
  { key: 'text', label: 'رنگ متن اصلی' },
  { key: 'textSecondary', label: 'رنگ متن ثانویه' },
  { key: 'muted', label: 'رنگ متن کم‌رنگ' },
]

const statusFields = [
  { key: 'success', label: 'موفقیت' },
  { key: 'danger', label: 'شکست/خطا' },
  { key: 'warning', label: 'هشدار' },
]

const posFields = [
  { key: 'posPrimary', label: 'POS Primary' },
  { key: 'posAccent', label: 'POS Accent' },
  { key: 'posSuccess', label: 'POS وضعیت موفقیت (میز خالی)' },
  { key: 'posDanger', label: 'POS وضعیت شکست (میز اشغال)' },
  { key: 'posWarning', label: 'POS وضعیت انتظار' },
]

const form = reactive({
  ...defaultThemeSettings,
  ...(props.initialSettings || loadThemeSettings()),
})
const themeKeys = Object.keys(defaultThemeSettings)
const presets = themePresets.map((preset) => ({
  ...preset,
  colors: sanitizeThemeSettings(preset.colors),
}))

const saveState = ref('هنوز ذخیره نشده است.')

const normalizedForm = computed(() => sanitizeThemeSettings(form))
const activePresetId = computed(() => {
  const current = normalizedForm.value
  const matchedPreset = presets.find((preset) => isSameTheme(current, preset.colors))
  return matchedPreset?.id || 'custom'
})

watch(
  normalizedForm,
  (next) => {
    applyThemeSettings(next)
    saveState.value = 'در حال پیش‌نمایش لحظه‌ای'
  },
  { deep: true },
)

function isSameTheme(left, right) {
  return themeKeys.every((key) => String(left?.[key] || '').toUpperCase() === String(right?.[key] || '').toUpperCase())
}

function applyPreset(preset) {
  const payload = sanitizeThemeSettings(preset?.colors || {})
  Object.assign(form, payload)
  applyThemeSettings(payload)
  saveState.value = `تم «${preset?.name || 'انتخابی'}» اعمال شد. برای ثبت نهایی ذخیره کنید.`
}

async function applyPresetAndSave(preset) {
  applyPreset(preset)
  await saveSettings()
}

async function saveSettings() {
  const payload = normalizedForm.value
  if (props.saveMode === 'draft') {
    emit('save-draft', payload)
    saveState.value = 'پیش‌نویس تم ذخیره شد.'
    return
  }

  saveState.value = 'در حال ذخیره سراسری...'
  try {
    const saved = await saveThemeSettingsToServer(payload)
    Object.assign(form, saved)
    applyThemeSettings(saved)
    saveState.value = 'تنظیمات برای همه کاربران ذخیره شد.'
  } catch (error) {
    saveState.value = error.message || 'ذخیره تنظیمات ناموفق بود.'
  }
}

async function resetToDefaults() {
  if (props.saveMode === 'draft') {
    Object.assign(form, defaultThemeSettings)
    applyThemeSettings(defaultThemeSettings)
    emit('reset-draft', sanitizeThemeSettings(defaultThemeSettings))
    saveState.value = 'پیش‌نویس تم به پیش‌فرض برگشت.'
    return
  }

  saveState.value = 'در حال بازگشت به پیش‌فرض سراسری...'
  try {
    const saved = await saveThemeSettingsToServer(defaultThemeSettings)
    Object.assign(form, saved)
    applyThemeSettings(saved)
    saveState.value = 'تنظیمات پیش‌فرض برای همه کاربران اعمال شد.'
  } catch (error) {
    saveState.value = error.message || 'بازگشت به پیش‌فرض ناموفق بود.'
  }
}

onMounted(async () => {
  if (props.saveMode === 'draft') {
    const payload = sanitizeThemeSettings(props.initialSettings || defaultThemeSettings)
    Object.assign(form, payload)
    applyThemeSettings(payload)
    saveState.value = 'پیش‌نویس تم بارگذاری شد.'
    return
  }

  try {
    const remote = await hydrateThemeSettingsFromServer()
    Object.assign(form, remote)
    applyThemeSettings(remote)
    saveState.value = 'تنظیمات سراسری بارگذاری شد.'
  } catch (_) {
    const fallback = resetThemeSettings()
    Object.assign(form, fallback)
    saveState.value = 'تنظیمات محلی بارگذاری شد.'
  }
})

watch(
  () => props.initialSettings,
  (next) => {
    if (props.saveMode !== 'draft' || !next || typeof next !== 'object') {
      return
    }
    Object.assign(form, sanitizeThemeSettings(next))
  },
  { deep: true },
)
</script>

<style scoped>
.theme-studio {
  display: grid;
  gap: 1rem;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.preset-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  padding: 0.65rem;
  display: grid;
  gap: 0.42rem;
}

.preset-card.active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.44);
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.preset-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
}

.preset-card strong {
  font-size: 0.84rem;
}

.preset-desc {
  margin: 0;
  font-size: 0.75rem;
}

.preset-swatches {
  display: flex;
  align-items: center;
  gap: 0.32rem;
}

.preset-swatches i {
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  display: inline-block;
}

.preset-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.toolbar {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.field-grid label {
  display: grid;
  gap: 0.24rem;
  font-size: 0.78rem;
}

.color-input {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 0.35rem;
  align-items: center;
}

.color-input input[type='color'] {
  width: 44px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: #fff;
  padding: 0.14rem;
}

.pos-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
}

.preview-grid article {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 14px;
  padding: 0.55rem;
  display: grid;
  gap: 0.25rem;
}

.preview-grid small {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.preview-grid strong {
  font-size: 0.84rem;
}

.preview-btn {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 0.42rem 0.7rem;
  color: #fff;
  font-family: inherit;
  font-size: 0.78rem;
}

.preview-btn-primary {
  background: var(--accent-green);
}

.preview-btn-accent {
  background: var(--accent-gold);
}

.preview-chip {
  margin: 0;
  border-radius: 999px;
  padding: 0.3rem 0.62rem;
  color: #fff;
  font-size: 0.74rem;
  width: fit-content;
}

.preview-chip-success {
  background: var(--success);
}

.preview-chip-danger {
  background: var(--danger);
}

.preview-chip-pos-success {
  background: var(--pos-success-color);
}

.preview-chip-pos-danger {
  background: var(--pos-danger-color);
}

@media (max-width: 980px) {
  .preset-grid,
  .field-grid,
  .pos-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }

  .preset-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
