<template>
  <ManagementPageScaffold title="تنظیمات سایت" subtitle="مدیریت محتوای صفحات عمومی مثل FAQ، درباره ما و اسلایدهای هدر">
    <ManagementSurfaceCard tone="accent">
      <div class="toolbar">
        <button class="secondary-btn" type="button" :disabled="loading || saving" @click="loadSettings">
          {{ loading ? 'در حال بارگذاری...' : 'بروزرسانی' }}
        </button>
        <button class="primary-btn" type="button" :disabled="loading || saving" @click="saveSettings">
          {{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات سایت' }}
        </button>
        <span class="muted">{{ statusText }}</span>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft">
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="error" v-if="error">{{ error }}</p>

    <template v-if="activeTab === 'general'">
      <ManagementSurfaceCard title="اطلاعات عمومی سایت" subtitle="برند، عنوان هدر و CTA اصلی منوی آنلاین">
        <div class="form-grid">
          <label>
            نام برند
            <input class="input" v-model.trim="webSettings.brand_name" />
          </label>
          <label>
            شعار برند
            <input class="input" v-model.trim="webSettings.brand_tagline" />
          </label>
          <label>
            ارز پیش فرض
            <SearchableDropdown
              v-model="webSettings.default_currency"
              :options="currencyOptions"
              placeholder="انتخاب ارز"
              search-placeholder="جستجوی ارز..."
            />
          </label>
          <label>
            متن دکمه اصلی
            <input class="input" v-model.trim="webSettings.primary_cta_label" />
          </label>
          <label class="span-2">
            تیتر هدر سایت
            <input class="input" v-model.trim="webSettings.hero_title" />
          </label>
          <label class="span-2">
            زیرتیتر هدر سایت
            <textarea class="textarea" v-model.trim="webSettings.hero_subtitle" />
          </label>
          <label class="span-2">
            تصویر هدر سایت
            <input class="input" v-model.trim="webSettings.hero_image" placeholder="/files/hero.jpg" />
            <img
              v-if="String(webSettings.hero_image || '').trim()"
              class="image-preview image-preview-wide"
              :src="webSettings.hero_image"
              alt="Hero preview"
            />
          </label>
          <label class="check span-2">
            <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_enabled" :true-value="1" :false-value="0" />
            نمایش بلاک ویژه/پرفروش در ابتدای منو
          </label>
          <label class="span-2" v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            عنوان بلاک ویژه
            <input class="input" v-model.trim="webSettings.restaurant_menu_highlight_title" />
          </label>
          <label class="check" v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_featured" :true-value="1" :false-value="0" />
            نمایش آیتم های ویژه
          </label>
          <label v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            تعداد آیتم ویژه
            <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_featured_limit" />
          </label>
          <label class="check" v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_best_seller" :true-value="1" :false-value="0" />
            نمایش آیتم های پرفروش
          </label>
          <label v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            تعداد آیتم پرفروش
            <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_best_seller_limit" />
          </label>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeTab === 'hero'">
      <ManagementEditableTable
        v-model="heroSlides"
        title="اسلایدهای هدر"
        subtitle="این بخش در صفحه اصلی سایت نمایش داده می‌شود."
        tone="accent"
        :columns="heroColumns"
        popup-title-add="افزودن اسلاید"
        popup-title-edit="ویرایش اسلاید"
        popup-subtitle="محتوای اسلاید را تکمیل کنید."
        :create-empty-row="createEmptyHeroSlide"
        :normalize-row="normalizeHeroSlide"
        :validate-row="validateHeroSlide"
      >
        <template #cell-is_active="{ value }">
          <span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span>
        </template>

        <template #editor="{ draft }">
          <div class="editor-grid">
            <label>
              عنوان
              <input class="input" v-model.trim="draft.title" />
            </label>
            <label>
              ترتیب
              <input class="input" type="number" min="0" v-model.number="draft.sort_order" />
            </label>
            <label class="span-2">
              زیرعنوان
              <textarea class="textarea" v-model.trim="draft.subtitle" />
            </label>
            <label>
              تصویر
              <input class="input" v-model.trim="draft.image" placeholder="/files/slide.jpg" />
              <img
                v-if="String(draft.image || '').trim()"
                class="image-preview"
                :src="draft.image"
                alt="Slide preview"
              />
            </label>
            <label>
              لینک محصول (Item)
              <input class="input" v-model.trim="draft.linked_item" placeholder="مثال: ITEM-0001" />
            </label>
            <label>
              متن دکمه
              <input class="input" v-model.trim="draft.cta_label" />
            </label>
            <label>
              لینک دکمه
              <input class="input" v-model.trim="draft.cta_url" placeholder="/menu" />
            </label>
            <label>
              شعبه (اختیاری)
              <input class="input" v-model.trim="draft.branch" />
            </label>
            <label class="check">
              <input type="checkbox" v-model="draft.is_active" :true-value="1" :false-value="0" />
              فعال
            </label>
          </div>
        </template>
      </ManagementEditableTable>
    </template>

    <template v-else-if="activeTab === 'about'">
      <ManagementSurfaceCard title="بخش درباره ما" subtitle="برای ویرایش، روی ردیف کلیک کنید.">
        <div class="section-toolbar">
          <button class="secondary-btn" type="button" @click="openAboutAdd">افزودن بخش</button>
        </div>
        <ManagementListView
          :columns="aboutColumns"
          :rows="aboutSections"
          row-key="name"
          :row-clickable="true"
          @row-click="openAboutEdit"
        >
          <template #cell-is_active="{ value }">
            <span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span>
          </template>
          <template #cell-actions="{ row, rowIndex }">
            <div class="row-actions">
              <button class="secondary-btn mini" type="button" @click.stop="openAboutEdit(row)">ویرایش</button>
              <button class="secondary-btn mini danger" type="button" @click.stop="removeAboutRow(rowIndex)">حذف</button>
            </div>
          </template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="aboutEditorOpen"
        :title="aboutEditorIndex >= 0 ? 'ویرایش بخش درباره ما' : 'افزودن بخش درباره ما'"
      >
        <div class="editor-grid">
          <label>
            نوع بخش
            <SearchableDropdown
              v-model="aboutDraft.section_type"
              :options="aboutSectionTypeOptions"
              placeholder="نوع بخش"
              search-placeholder="جستجو..."
            />
          </label>
          <label>
            عنوان
            <input class="input" v-model.trim="aboutDraft.title" />
          </label>
          <label>
            ترتیب
            <input class="input" type="number" min="0" v-model.number="aboutDraft.sort_order" />
          </label>
          <label class="span-2">
            زیرعنوان
            <textarea class="textarea" v-model.trim="aboutDraft.subtitle" />
          </label>
          <label class="span-2">
            متن اصلی
            <textarea class="textarea" v-model.trim="aboutDraft.body_text" />
          </label>
          <label>
            آیکون
            <input class="input" v-model.trim="aboutDraft.icon" placeholder="مثال: ✦" />
          </label>
          <label>
            سال/برچسب زمانی
            <input class="input" v-model.trim="aboutDraft.year_label" placeholder="مثال: ۱۴۰۲" />
          </label>
          <label>
            Badge هیرو
            <input class="input" v-model.trim="aboutDraft.badge" placeholder="مثال: ABOUT US" />
          </label>
          <label>
            سال تاسیس
            <input class="input" v-model.trim="aboutDraft.founded_year" placeholder="مثال: ۱۳۹۶" />
          </label>
          <label class="check">
            <input type="checkbox" v-model="aboutDraft.highlight" :true-value="1" :false-value="0" />
            هایلایت شود
          </label>
          <label>
            تصویر
            <input class="input" v-model.trim="aboutDraft.image" placeholder="/files/about.jpg" />
            <img
              v-if="String(aboutDraft.image || '').trim()"
              class="image-preview"
              :src="aboutDraft.image"
              alt="About preview"
            />
          </label>
          <label>
            برچسب آمار
            <input class="input" v-model.trim="aboutDraft.stat_label" />
          </label>
          <label>
            مقدار آمار
            <input class="input" v-model.trim="aboutDraft.stat_value" />
          </label>
          <label class="check">
            <input type="checkbox" v-model="aboutDraft.is_active" :true-value="1" :false-value="0" />
            فعال
          </label>
        </div>
        <div class="editor-actions">
          <button class="secondary-btn" type="button" @click="closeAboutEditor">انصراف</button>
          <button class="primary-btn" type="button" @click="saveAboutDraft">ثبت بخش</button>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeTab === 'loader'">
      <ManagementSurfaceCard
        title="تنظیمات Loader داینامیک"
        subtitle="یک لودر پیش‌فرض انتخاب کنید یا کد اختصاصی خودتان را قرار دهید."
      >
        <div class="loader-guide">
          <p class="muted">
            این لودر برای صفحات عمومی سایت نمایش داده می‌شود. می‌توانید بین پریست‌های آماده انتخاب کنید یا HTML/CSS/JS اختصاصی خودتان را وارد کنید.
          </p>
          <p class="muted">
            پیشنهاد: برای UX بهتر، زمان نمایش را بین 700 تا 1800 میلی‌ثانیه نگه دارید.
          </p>
        </div>
        <div class="form-grid">
          <label class="check span-2">
            <input type="checkbox" v-model="webSettings.loader_enabled" :true-value="1" :false-value="0" />
            فعال بودن Loader در سایت عمومی
          </label>
          <label>
            نوع Loader
            <SearchableDropdown
              v-model="webSettings.loader_mode"
              :options="loaderModeOptions"
              placeholder="انتخاب نوع"
              search-placeholder="جستجو..."
            />
          </label>
          <label v-if="webSettings.loader_mode === 'preset'">
            پریست آماده
            <SearchableDropdown
              v-model="webSettings.loader_preset"
              :options="loaderPresetOptions"
              placeholder="انتخاب پریست"
              search-placeholder="جستجو..."
            />
          </label>
          <label>
            حداقل زمان نمایش (ms)
            <input class="input" type="number" min="0" max="8000" v-model.number="webSettings.loader_min_duration_ms" />
          </label>
          <label>
            عنوان
            <input class="input" v-model.trim="webSettings.loader_title" />
          </label>
          <label class="span-2">
            زیرعنوان
            <input class="input" v-model.trim="webSettings.loader_subtitle" />
          </label>
          <label>
            رنگ پس‌زمینه Overlay
            <div class="color-field">
              <input class="color-picker" type="color" v-model="webSettings.loader_overlay_color" />
              <input class="input" v-model.trim="webSettings.loader_overlay_color" placeholder="#F6F4ED" />
            </div>
          </label>
          <label>
            رنگ اصلی انیمیشن
            <div class="color-field">
              <input class="color-picker" type="color" v-model="webSettings.loader_accent_color" />
              <input class="input" v-model.trim="webSettings.loader_accent_color" placeholder="#6A9A6B" />
            </div>
          </label>
          <label class="span-2" v-if="webSettings.loader_mode === 'custom'">
            کد اختصاصی Loader (HTML/CSS/JS)
            <textarea
              class="textarea code-textarea"
              v-model="webSettings.loader_custom_code"
              placeholder="<style>.dot{width:18px;height:18px;border-radius:50%;background:#3B7A57;animation:pulse 1.2s infinite}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.6)}}</style><div class='dot'></div>"
            />
          </label>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="پیش‌نمایش Loader">
        <div class="loader-preview">
          <SiteLoaderRenderer :settings="loaderPreviewSettings" />
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeTab === 'faq'">
      <ManagementSurfaceCard title="سوالات متداول" subtitle="برای ویرایش، روی ردیف کلیک کنید.">
        <div class="section-toolbar">
          <button class="secondary-btn" type="button" @click="openFaqAdd">افزودن سوال</button>
        </div>
        <ManagementListView
          :columns="faqColumns"
          :rows="faqItems"
          row-key="name"
          :row-clickable="true"
          @row-click="openFaqEdit"
        >
          <template #cell-is_active="{ value }">
            <span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span>
          </template>
          <template #cell-actions="{ row, rowIndex }">
            <div class="row-actions">
              <button class="secondary-btn mini" type="button" @click.stop="openFaqEdit(row)">ویرایش</button>
              <button class="secondary-btn mini danger" type="button" @click.stop="removeFaqRow(rowIndex)">حذف</button>
            </div>
          </template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="faqEditorOpen"
        :title="faqEditorIndex >= 0 ? 'ویرایش سوال متداول' : 'افزودن سوال متداول'"
      >
        <div class="editor-grid">
          <label class="span-2">
            سوال
            <input class="input" v-model.trim="faqDraft.question" />
          </label>
          <label>
            دسته‌بندی
            <input class="input" v-model.trim="faqDraft.category" placeholder="مثال: سفارش و پرداخت" />
          </label>
          <label>
            آیکون
            <input class="input" v-model.trim="faqDraft.icon" placeholder="مثال: 💳 یا ❓" />
          </label>
          <label class="span-2">
            تصویر
            <input class="input" v-model.trim="faqDraft.image" placeholder="/files/faq.jpg" />
            <img
              v-if="String(faqDraft.image || '').trim()"
              class="image-preview image-preview-wide"
              :src="faqDraft.image"
              alt="FAQ preview"
            />
          </label>
          <label class="span-2">
            توضیح کوتاه
            <input class="input" v-model.trim="faqDraft.summary" placeholder="متن کوتاه اختیاری" />
          </label>
          <label>
            ترتیب
            <input class="input" type="number" min="0" v-model.number="faqDraft.sort_order" />
          </label>
          <label class="check">
            <input type="checkbox" v-model="faqDraft.is_active" :true-value="1" :false-value="0" />
            فعال
          </label>
          <label class="span-2">
            پاسخ
            <textarea class="textarea" v-model.trim="faqDraft.answer" />
          </label>
        </div>
        <div class="editor-actions">
          <button class="secondary-btn" type="button" @click="closeFaqEditor">انصراف</button>
          <button class="primary-btn" type="button" @click="saveFaqDraft">ثبت سوال</button>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else>
      <ManagementSurfaceCard title="تنظیمات سایت">
        <p class="muted">یک تب را برای ویرایش انتخاب کنید.</p>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import SiteLoaderRenderer from '@/components/SiteLoaderRenderer.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementSiteSettings, setManagementSiteSettings } from '@/utils/api'
import { composeFaqAnswer, parseFaqAnswer } from '@/utils/faqMeta'
import {
  defaultLoaderSettings,
  normalizeLoaderSettings,
  toLoaderWebSettingsPayload,
} from '@/utils/loaderSettings'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const statusText = ref('')
const activeTab = ref('general')

const tabs = [
  { value: 'general', label: 'عمومی' },
  { value: 'hero', label: 'اسلایدر هدر' },
  { value: 'about', label: 'درباره ما' },
  { value: 'loader', label: 'Loader' },
  { value: 'faq', label: 'FAQ' },
]

const webSettings = reactive({
  brand_name: '',
  brand_tagline: '',
  default_currency: 'IRR',
  hero_title: '',
  hero_subtitle: '',
  hero_image: '',
  primary_cta_label: '',
  restaurant_menu_highlight_enabled: 1,
  restaurant_menu_highlight_title: 'ویژه و پرفروش',
  restaurant_menu_highlight_show_featured: 1,
  restaurant_menu_highlight_featured_limit: 10,
  restaurant_menu_highlight_show_best_seller: 1,
  restaurant_menu_highlight_best_seller_limit: 10,
  loader_enabled: defaultLoaderSettings.enabled,
  loader_mode: defaultLoaderSettings.mode,
  loader_preset: defaultLoaderSettings.preset,
  loader_title: defaultLoaderSettings.title,
  loader_subtitle: defaultLoaderSettings.subtitle,
  loader_min_duration_ms: defaultLoaderSettings.minDurationMs,
  loader_overlay_color: defaultLoaderSettings.overlayColor,
  loader_accent_color: defaultLoaderSettings.accentColor,
  loader_custom_code: defaultLoaderSettings.customCode,
})

const heroSlides = ref([])
const aboutSections = ref([])
const faqItems = ref([])

const aboutEditorOpen = ref(false)
const aboutEditorIndex = ref(-1)
const aboutDraft = reactive(createEmptyAboutSection())

const faqEditorOpen = ref(false)
const faqEditorIndex = ref(-1)
const faqDraft = reactive(createEmptyFaqItem())

const currencyOptions = [
  { value: 'IRR', label: 'IRR' },
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
]

const loaderModeOptions = [
  { value: 'preset', label: 'پریست آماده' },
  { value: 'custom', label: 'کد اختصاصی' },
]

const loaderPresetOptions = [
  { value: 'steaming-bowl', label: 'کاسه داغ و بخار' },
  { value: 'noodle-bowl', label: 'نودل بخارپز' },
  { value: 'burger-stack', label: 'برگر لایه‌ای' },
  { value: 'club-sandwich', label: 'کلاب ساندویچ' },
  { value: 'coffee-cup', label: 'فنجان قهوه' },
  { value: 'pizza-slice', label: 'اسلایس پیتزا' },
  { value: 'donut-bite', label: 'دونات شکلاتی' },
]

const aboutSectionTypeOptions = [
  { value: 'hero', label: 'هیرو' },
  { value: 'mission', label: 'ماموریت' },
  { value: 'vision', label: 'چشم‌انداز' },
  { value: 'value', label: 'ارزش' },
  { value: 'history', label: 'تاریخچه' },
  { value: 'timeline', label: 'تایم‌لاین' },
  { value: 'story', label: 'عمومی/داستان' },
]

const heroColumns = [
  { key: 'title', label: 'عنوان' },
  { key: 'linked_item', label: 'محصول' },
  { key: 'sort_order', label: 'ترتیب' },
  { key: 'is_active', label: 'وضعیت' },
]

const aboutColumns = [
  { key: 'section_type', label: 'نوع بخش' },
  { key: 'title', label: 'عنوان' },
  { key: 'stat_label', label: 'آمار' },
  { key: 'sort_order', label: 'ترتیب' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

const faqColumns = [
  { key: 'category', label: 'دسته' },
  { key: 'question', label: 'سوال' },
  { key: 'sort_order', label: 'ترتیب' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

const loaderPreviewSettings = computed(() =>
  normalizeLoaderSettings({
    loader_enabled: webSettings.loader_enabled,
    loader_mode: webSettings.loader_mode,
    loader_preset: webSettings.loader_preset,
    loader_title: webSettings.loader_title,
    loader_subtitle: webSettings.loader_subtitle,
    loader_min_duration_ms: webSettings.loader_min_duration_ms,
    loader_overlay_color: webSettings.loader_overlay_color,
    loader_accent_color: webSettings.loader_accent_color,
    loader_custom_code: webSettings.loader_custom_code,
  }),
)

function deepCopy(value) {
  try {
    return JSON.parse(JSON.stringify(value || {}))
  } catch (copyError) {
    return {}
  }
}

function writeReactive(target, payload) {
  for (const key of Object.keys(target)) {
    delete target[key]
  }
  Object.assign(target, deepCopy(payload))
}

function assignLoaderSettingsToForm(source = {}) {
  const normalized = normalizeLoaderSettings(source)
  webSettings.loader_enabled = normalized.enabled ? 1 : 0
  webSettings.loader_mode = normalized.mode
  webSettings.loader_preset = normalized.preset
  webSettings.loader_title = normalized.title
  webSettings.loader_subtitle = normalized.subtitle
  webSettings.loader_min_duration_ms = normalized.minDurationMs
  webSettings.loader_overlay_color = normalized.overlayColor
  webSettings.loader_accent_color = normalized.accentColor
  webSettings.loader_custom_code = String(normalized.customCode || '')
}

function createEmptyHeroSlide() {
  return {
    title: '',
    subtitle: '',
    image: '',
    linked_item: '',
    cta_label: 'مشاهده محصول',
    cta_url: '',
    branch: '',
    sort_order: heroSlides.value.length,
    is_active: 1,
  }
}

function createEmptyAboutSection() {
  return {
    name: '',
    section_type: 'story',
    icon: '',
    year_label: '',
    highlight: 0,
    badge: '',
    founded_year: '',
    title: '',
    subtitle: '',
    body_text: '',
    image: '',
    stat_label: '',
    stat_value: '',
    sort_order: aboutSections.value.length,
    is_active: 1,
  }
}

function createEmptyFaqItem() {
  return {
    name: '',
    category: '',
    icon: '',
    image: '',
    summary: '',
    question: '',
    answer: '',
    sort_order: faqItems.value.length,
    is_active: 1,
  }
}

function normalizeHeroSlide(row) {
  return {
    name: String(row?.name || '').trim(),
    title: String(row?.title || '').trim(),
    subtitle: String(row?.subtitle || '').trim(),
    image: String(row?.image || '').trim(),
    linked_item: String(row?.linked_item || '').trim(),
    cta_label: String(row?.cta_label || 'مشاهده محصول').trim() || 'مشاهده محصول',
    cta_url: String(row?.cta_url || '').trim(),
    branch: String(row?.branch || '').trim(),
    sort_order: Number(row?.sort_order || 0) || 0,
    is_active: Number(row?.is_active || 0) ? 1 : 0,
  }
}

function normalizeAboutSection(row) {
  const sourceSectionType = String(row?.section_type || '').trim()
  const sourceIcon = String(row?.icon || '').trim()
  const sourceYearLabel = String(row?.year_label || '').trim()
  const sourceBadge = String(row?.badge || '').trim()
  const sourceFoundedYear = String(row?.founded_year || '').trim()
  const sourceHighlight = Number(row?.highlight || 0) ? 1 : 0

  return {
    name: String(row?.name || '').trim(),
    section_type: String(sourceSectionType || 'story').trim(),
    icon: String(sourceIcon || '').trim(),
    year_label: String(sourceYearLabel || '').trim(),
    highlight: sourceHighlight ? 1 : 0,
    badge: String(sourceBadge || '').trim(),
    founded_year: String(sourceFoundedYear || '').trim(),
    title: String(row?.title || '').trim(),
    subtitle: String(row?.subtitle || '').trim(),
    body_text: String(row?.body_text || '').trim(),
    image: String(row?.image || '').trim(),
    stat_label: String(row?.stat_label || '').trim(),
    stat_value: String(row?.stat_value || '').trim(),
    sort_order: Number(row?.sort_order || 0) || 0,
    is_active: Number(row?.is_active || 0) ? 1 : 0,
  }
}

function normalizeFaqItem(row) {
  const parsed = parseFaqAnswer(row?.answer || '')
  const sourceCategory = String(row?.category || '').trim()
  const sourceIcon = String(row?.icon || '').trim()
  const sourceImage = String(row?.image || '').trim()
  const sourceSummary = String(row?.summary || '').trim()

  return {
    name: String(row?.name || '').trim(),
    category: String(sourceCategory || parsed.meta.category || '').trim(),
    icon: String(sourceIcon || parsed.meta.icon || '').trim(),
    image: String(sourceImage || parsed.meta.image || '').trim(),
    summary: String(sourceSummary || parsed.meta.summary || '').trim(),
    question: String(row?.question || '').trim(),
    answer: parsed.answer || String(row?.answer || '').trim(),
    sort_order: Number(row?.sort_order || 0) || 0,
    is_active: Number(row?.is_active || 0) ? 1 : 0,
  }
}

function validateHeroSlide(row) {
  if (!String(row?.title || '').trim()) {
    return 'عنوان اسلاید الزامی است.'
  }
  return ''
}

function validateAboutSection(row) {
  if (!String(row?.title || '').trim()) {
    return 'عنوان بخش الزامی است.'
  }
  if (!String(row?.body_text || '').trim()) {
    return 'متن اصلی بخش الزامی است.'
  }
  return ''
}

function validateFaqItem(row) {
  if (!String(row?.question || '').trim()) {
    return 'سوال الزامی است.'
  }
  if (!String(row?.answer || '').trim()) {
    return 'پاسخ الزامی است.'
  }
  return ''
}

function findRowIndex(rows, row) {
  const byRef = rows.indexOf(row)
  if (byRef >= 0) {
    return byRef
  }
  const name = String(row?.name || '').trim()
  if (name) {
    return rows.findIndex((entry) => String(entry?.name || '').trim() === name)
  }
  return -1
}

function openAboutAdd() {
  aboutEditorIndex.value = -1
  writeReactive(aboutDraft, createEmptyAboutSection())
  aboutEditorOpen.value = true
}

function openAboutEdit(row) {
  aboutEditorIndex.value = findRowIndex(aboutSections.value, row)
  writeReactive(aboutDraft, normalizeAboutSection(row))
  aboutEditorOpen.value = true
}

function closeAboutEditor() {
  aboutEditorOpen.value = false
}

function saveAboutDraft() {
  const message = validateAboutSection(aboutDraft)
  if (message) {
    error.value = message
    return
  }
  error.value = ''
  const normalized = normalizeAboutSection(aboutDraft)
  const next = [...aboutSections.value]
  if (aboutEditorIndex.value >= 0) {
    next.splice(aboutEditorIndex.value, 1, normalized)
  } else {
    next.push(normalized)
  }
  aboutSections.value = next
  closeAboutEditor()
}

function removeAboutRow(index) {
  const next = [...aboutSections.value]
  next.splice(index, 1)
  aboutSections.value = next
}

function openFaqAdd() {
  faqEditorIndex.value = -1
  writeReactive(faqDraft, createEmptyFaqItem())
  faqEditorOpen.value = true
}

function openFaqEdit(row) {
  faqEditorIndex.value = findRowIndex(faqItems.value, row)
  writeReactive(faqDraft, normalizeFaqItem(row))
  faqEditorOpen.value = true
}

function closeFaqEditor() {
  faqEditorOpen.value = false
}

function saveFaqDraft() {
  const message = validateFaqItem(faqDraft)
  if (message) {
    error.value = message
    return
  }
  error.value = ''
  const normalized = normalizeFaqItem(faqDraft)
  const next = [...faqItems.value]
  if (faqEditorIndex.value >= 0) {
    next.splice(faqEditorIndex.value, 1, normalized)
  } else {
    next.push(normalized)
  }
  faqItems.value = next
  closeFaqEditor()
}

function removeFaqRow(index) {
  const next = [...faqItems.value]
  next.splice(index, 1)
  faqItems.value = next
}

async function loadSettings() {
  loading.value = true
  error.value = ''
  statusText.value = ''

  try {
    const payload = await getManagementSiteSettings()
    const nextWeb = payload?.web_settings || {}
    webSettings.brand_name = String(nextWeb.brand_name || '').trim()
    webSettings.brand_tagline = String(nextWeb.brand_tagline || '').trim()
    webSettings.default_currency = String(nextWeb.default_currency || 'IRR').trim() || 'IRR'
    webSettings.hero_title = String(nextWeb.hero_title || '').trim()
    webSettings.hero_subtitle = String(nextWeb.hero_subtitle || '').trim()
    webSettings.hero_image = String(nextWeb.hero_image || '').trim()
    webSettings.primary_cta_label = String(nextWeb.primary_cta_label || '').trim()
    webSettings.restaurant_menu_highlight_enabled = Number(nextWeb.restaurant_menu_highlight_enabled || 0) ? 1 : 0
    webSettings.restaurant_menu_highlight_title = String(nextWeb.restaurant_menu_highlight_title || 'ویژه و پرفروش').trim() || 'ویژه و پرفروش'
    webSettings.restaurant_menu_highlight_show_featured = Number(nextWeb.restaurant_menu_highlight_show_featured || 0) ? 1 : 0
    webSettings.restaurant_menu_highlight_featured_limit = Number(nextWeb.restaurant_menu_highlight_featured_limit || 10) || 10
    webSettings.restaurant_menu_highlight_show_best_seller = Number(nextWeb.restaurant_menu_highlight_show_best_seller || 0) ? 1 : 0
    webSettings.restaurant_menu_highlight_best_seller_limit = Number(nextWeb.restaurant_menu_highlight_best_seller_limit || 10) || 10
    assignLoaderSettingsToForm(nextWeb)

    heroSlides.value = (payload?.hero_slides || []).map((row) => normalizeHeroSlide(row))
    aboutSections.value = (payload?.about_sections || []).map((row) => normalizeAboutSection(row))
    faqItems.value = (payload?.faq_items || []).map((row) => normalizeFaqItem(row))
    aboutEditorOpen.value = false
    faqEditorOpen.value = false
    statusText.value = 'تنظیمات سایت بارگذاری شد.'
  } catch (loadError) {
    error.value = loadError.message || 'بارگذاری تنظیمات سایت ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  error.value = ''
  statusText.value = ''

  try {
    const loaderPayload = toLoaderWebSettingsPayload(webSettings)
    if (loaderPayload.loader_enabled && loaderPayload.loader_mode === 'custom' && !String(loaderPayload.loader_custom_code || '').trim()) {
      throw new Error('برای حالت کد اختصاصی، لطفا کد Loader را وارد کنید.')
    }

    const normalizedBrandName = String(webSettings.brand_name || '').trim() || 'Veederakht Restaurant'
    const payload = await setManagementSiteSettings({
      web_settings: {
        brand_name: normalizedBrandName,
        brand_tagline: String(webSettings.brand_tagline || '').trim(),
        default_currency: String(webSettings.default_currency || 'IRR').trim() || 'IRR',
        hero_title: String(webSettings.hero_title || '').trim(),
        hero_subtitle: String(webSettings.hero_subtitle || '').trim(),
        hero_image: String(webSettings.hero_image || '').trim(),
        primary_cta_label: String(webSettings.primary_cta_label || '').trim(),
        restaurant_menu_highlight_enabled: Number(webSettings.restaurant_menu_highlight_enabled || 0) ? 1 : 0,
        restaurant_menu_highlight_title: String(webSettings.restaurant_menu_highlight_title || 'ویژه و پرفروش').trim() || 'ویژه و پرفروش',
        restaurant_menu_highlight_show_featured: Number(webSettings.restaurant_menu_highlight_show_featured || 0) ? 1 : 0,
        restaurant_menu_highlight_featured_limit: Math.max(0, Math.min(Number(webSettings.restaurant_menu_highlight_featured_limit || 10) || 10, 50)),
        restaurant_menu_highlight_show_best_seller: Number(webSettings.restaurant_menu_highlight_show_best_seller || 0) ? 1 : 0,
        restaurant_menu_highlight_best_seller_limit: Math.max(0, Math.min(Number(webSettings.restaurant_menu_highlight_best_seller_limit || 10) || 10, 50)),
        ...loaderPayload,
      },
      hero_slides: heroSlides.value.map((row, index) => ({ ...normalizeHeroSlide(row), sort_order: index })),
      about_sections: aboutSections.value.map((row, index) => ({ ...normalizeAboutSection(row), sort_order: index })),
      faq_items: faqItems.value.map((row, index) => {
        const normalized = normalizeFaqItem(row)
        return {
          ...normalized,
          answer: composeFaqAnswer(normalized.answer, {
            category: normalized.category,
            icon: normalized.icon,
            image: normalized.image,
            summary: normalized.summary,
          }),
          sort_order: index,
        }
      }),
    })

    heroSlides.value = (payload?.hero_slides || []).map((row) => normalizeHeroSlide(row))
    aboutSections.value = (payload?.about_sections || []).map((row) => normalizeAboutSection(row))
    faqItems.value = (payload?.faq_items || []).map((row) => normalizeFaqItem(row))
    assignLoaderSettingsToForm(payload?.web_settings || {})
    statusText.value = 'تنظیمات سایت با موفقیت ذخیره شد.'
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره تنظیمات سایت ناموفق بود.'
  } finally {
    saving.value = false
  }
}

loadSettings()
</script>

<style scoped>
.toolbar {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tabs {
  display: inline-flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.tab-btn {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: #fff;
  color: var(--ink-800);
  border-radius: 999px;
  padding: 0.34rem 0.8rem;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.78rem;
}

.tab-btn.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
}

.form-grid,
.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.form-grid label,
.editor-grid label {
  display: grid;
  gap: 0.22rem;
  font-size: 0.8rem;
}

.loader-guide {
  display: grid;
  gap: 0.2rem;
  margin-bottom: 0.55rem;
}

.color-field {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.4rem;
  align-items: center;
}

.color-picker {
  width: 2.2rem;
  height: 2rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.25);
  border-radius: 0.5rem;
  background: #fff;
  padding: 0.12rem;
}

.code-textarea {
  min-height: 200px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace;
  direction: ltr;
  text-align: left;
}

.loader-preview {
  min-height: 280px;
  border-radius: 16px;
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.32);
  background: linear-gradient(145deg, rgb(255 255 255 / 0.84), rgb(var(--palette-eggshell-rgb) / 0.75));
  display: grid;
  place-items: center;
  padding: 0.7rem;
}

.image-preview {
  width: 100%;
  max-width: 180px;
  height: 120px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: #fff;
}

.image-preview-wide {
  max-width: min(100%, 360px);
}

.section-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.45rem;
}

.row-actions {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.45rem;
  margin-top: 0.55rem;
}

.mini {
  padding: 0.32rem 0.56rem;
  font-size: 0.7rem;
}

.danger {
  color: var(--danger);
}

.span-2 {
  grid-column: span 2;
}

.check {
  display: inline-flex !important;
  align-items: center;
  gap: 0.35rem;
  align-self: center;
}

.state-pill {
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  font-size: 0.7rem;
}

.state-pill.on {
  background: rgb(var(--palette-june-bud-rgb) / 0.35);
  color: var(--accent-green);
}

.state-pill.off {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.2);
  color: var(--accent-gold);
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 900px) {
  .form-grid,
  .editor-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .span-2 {
    grid-column: span 1;
  }
}
</style>
