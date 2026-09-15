<template>
  <ManagementPageScaffold
    title="دیزاین سیستم رستوران"
    subtitle="مرجع زنده‌ی توکن‌ها، کامپوننت‌ها، پترن‌ها و صفحه‌های محصول برای یکدست‌سازی کل برنامه"
  >
    <template #actions>
      <a class="secondary-btn ds-page-link" href="/management/products">
        <Package :size="16" aria-hidden="true" />
        بازگشت به محصولات
      </a>
    </template>

    <section class="ds-intro" aria-labelledby="ds-intro-title">
      <div class="ds-intro-copy">
        <span class="ds-eyebrow"><Sparkles :size="15" aria-hidden="true" /> منبع مرجع رابط</span>
        <h2 id="ds-intro-title">از محصول شروع می‌کنیم، برای همه‌جا یک زبان می‌سازیم.</h2>
        <p>کارت محصول، جزئیات محصول و وضعیت‌های عملیاتی اینجا به‌صورت واقعی نمایش داده می‌شوند تا هر صفحه‌ی جدید همان قرارداد بصری را ادامه دهد.</p>
      </div>
      <div class="ds-intro-stats" aria-label="خلاصه دیزاین سیستم">
        <div><strong>{{ designSystemCatalog.components.length.toLocaleString('fa-IR') }}</strong><span>کامپوننت مرجع</span></div>
        <div><strong>{{ designSystemCatalog.patterns.length.toLocaleString('fa-IR') }}</strong><span>پترن عملیاتی</span></div>
        <div><strong>{{ designSystemCatalog.templates.length.toLocaleString('fa-IR') }}</strong><span>تمپلیت محصول</span></div>
      </div>
    </section>

    <div class="ds-workbench">
      <nav class="ds-tabs" role="tablist" aria-label="بخش‌های دیزاین سیستم">
        <button
          v-for="tab in designSystemTabs"
          :key="tab.id"
          class="ds-tab"
          :class="{ active: activeTab === tab.id }"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.id"
          :aria-controls="`ds-panel-${tab.id}`"
          @click="activeTab = tab.id"
        >
          <strong>{{ tab.label }}</strong>
          <small>{{ tab.caption }}</small>
        </button>
      </nav>

      <main :id="`ds-panel-${activeTab}`" class="ds-content" role="tabpanel" tabindex="-1">
        <template v-if="activeTab === 'theme'">
          <ManagementSurfaceCard title="تم‌های آماده" subtitle="پیش‌نمایش تم‌ها با همان palette ذخیره‌شده‌ی برنامه">
            <div class="ds-preset-grid">
              <button
                v-for="preset in themePresets"
                :key="preset.id"
                type="button"
                class="ds-preset"
                :class="{ active: selectedPresetId === preset.id }"
                @click="selectPreset(preset)"
              >
                <span class="ds-preset-swatches" aria-hidden="true">
                  <i :style="{ background: preset.colors.primary }"></i>
                  <i :style="{ background: preset.colors.accent }"></i>
                  <i :style="{ background: preset.colors.surface }"></i>
                </span>
                <strong>{{ preset.name }}</strong>
                <small>{{ preset.description }}</small>
              </button>
            </div>
          </ManagementSurfaceCard>

          <section class="ds-grid-2">
            <ManagementSurfaceCard title="توکن‌های معنایی" subtitle="کامپوننت‌ها این نام‌ها را مصرف می‌کنند، نه رنگ خام">
              <div class="ds-token-list">
                <div v-for="token in tokenRows" :key="token.token" class="ds-token-row">
                  <span class="ds-token-swatch" :style="{ background: token.swatch }" aria-hidden="true"></span>
                  <span class="ds-token-copy"><strong>{{ token.label }}</strong><code>{{ token.token }}</code></span>
                  <code class="ds-token-value">{{ token.value }}</code>
                </div>
              </div>
            </ManagementSurfaceCard>

            <ManagementSurfaceCard title="تایپوگرافی و ریتم" subtitle="مبنای فاصله‌گذاری و خوانایی RTL">
              <div class="ds-type-specimen">
                <span class="ds-type-kicker">Peyda / ۴۰۰ تا ۹۰۰</span>
                <strong>غذای خوب، تجربه‌ی ساده</strong>
                <p>متن بدنه با فاصله‌ی خطی باز و اندازه‌ی مناسب برای خواندن اطلاعات عملیاتی.</p>
              </div>
              <div class="ds-scale-row">
                <div v-for="(value, key) in designTokens.spacing" :key="key" class="ds-scale-item">
                  <i :style="{ width: value, height: value }"></i><span>{{ key }}</span>
                </div>
              </div>
              <div class="ds-radius-row">
                <span v-for="(value, key) in designTokens.radius" :key="key" :style="{ borderRadius: value }">{{ key }}</span>
              </div>
            </ManagementSurfaceCard>
          </section>

          <ManagementSurfaceCard title="پیش‌نمایش روشن و تیره" subtitle="هر تغییر تم باید در هر دو حالت خوانا و قابل استفاده بماند.">
            <div class="ds-preview-toolbar" role="group" aria-label="حالت پیش‌نمایش">
              <DsButton size="sm" :variant="previewMode === 'light' ? 'primary' : 'secondary'" @click="previewMode = 'light'">حالت روشن</DsButton>
              <DsButton size="sm" :variant="previewMode === 'dark' ? 'primary' : 'secondary'" @click="previewMode = 'dark'">حالت تیره</DsButton>
            </div>
            <div class="ds-theme-preview" :class="`ds-theme-preview--${previewMode}`" :style="previewStyle">
              <div><span class="ds-preview-label">{{ selectedPreset?.name || 'تم سفارشی' }}</span><strong>نمای محصول مرجع</strong><small>سطح، متن، اکسنت و وضعیت‌ها</small></div>
              <div class="ds-preview-actions"><DsButton variant="primary">افزودن به سبد</DsButton><DsBadge tone="success">فعال در منو</DsBadge></div>
            </div>
          </ManagementSurfaceCard>
        </template>

        <template v-else-if="activeTab === 'icons'">
          <ManagementSurfaceCard title="خانواده آیکون‌ها" subtitle="Lucide با اندازه‌ی توکن‌شده و برچسب فارسی">
            <div class="ds-icon-rules">
              <DsBadge tone="primary">stroke یکسان</DsBadge>
              <DsBadge tone="neutral">بدون emoji</DsBadge>
              <DsBadge tone="info">هدف تعاملی حداقل ۴۴px</DsBadge>
            </div>
            <div class="ds-icon-grid">
              <article v-for="icon in iconCatalog" :key="icon.name" class="ds-icon-card">
                <span class="ds-icon-box"><component :is="icon.component" :size="icon.token === 'icon-lg' ? 24 : icon.token === 'icon-sm' ? 16 : 20" :stroke-width="2" aria-hidden="true" /></span>
                <strong>{{ icon.label }}</strong>
                <code>{{ icon.name }} · {{ icon.token }}</code>
              </article>
            </div>
          </ManagementSurfaceCard>
        </template>

        <template v-else-if="activeTab === 'components'">
          <section class="ds-grid-2">
            <ManagementSurfaceCard title="Primitiveها" subtitle="حالت‌های پایه برای هر صفحه">
              <div class="ds-component-stack">
                <div class="ds-sample-row"><DsButton variant="primary">عمل اصلی</DsButton><DsButton variant="secondary">ثانویه</DsButton><DsButton variant="quiet">کم‌اهمیت</DsButton></div>
                <div class="ds-sample-row"><DsButton variant="danger">عمل خطرناک</DsButton><DsButton loading>در حال ثبت</DsButton></div>
                <div class="ds-sample-row"><DsBadge tone="success">فعال</DsBadge><DsBadge tone="warning">به‌زودی</DsBadge><DsBadge tone="danger">ناموجود</DsBadge><DsBadge tone="neutral">پیش‌نویس</DsBadge></div>
                <label class="ds-field-sample">جستجوی نمونه<input class="input" value="برگر مخصوص" aria-label="جستجوی نمونه" /></label>
              </div>
            </ManagementSurfaceCard>

            <ManagementSurfaceCard title="قرارداد محصول" subtitle="کامپوننت‌های اصلی از همین صفحه شروع می‌شوند">
              <div class="ds-reference-list">
                <div v-for="item in designSystemCatalog.components.filter((entry) => entry.kind === 'reference' || entry.kind === 'domain')" :key="item.id"><span class="ds-reference-dot"></span><div><strong>{{ item.title }}</strong><p>{{ item.description }}</p><code>{{ item.source }}</code></div></div>
              </div>
            </ManagementSurfaceCard>
          </section>

          <ManagementSurfaceCard title="کارت محصول مشتری" subtitle="نمونه‌ی واقعی MenuProductCard با hierarchy تصویر، قیمت و اقدام">
            <div class="ds-product-card-stage"><MenuProductCard :item="referenceProduct" layout="featured" :cart-qty="1" /></div>
          </ManagementSurfaceCard>

          <section class="ds-grid-2">
            <ManagementSurfaceCard title="SmartDataTable" subtitle="جستجو، فیلتر ستونی، مرتب‌سازی، فریز و تغییر عرض ستون">
              <ManagementSmartDataTable
                :columns="dataTablePreviewColumns"
                :rows="editableTablePreviewRows"
                row-key="name"
                filterable
                sticky-header
                max-height="260px"
                frozen-storage-key="restaurant-design-system-smart-table"
              >
                <template #cell-amount="{ value }">{{ Number(value).toLocaleString('fa-IR') }} ریال</template>
                <template #cell-status="{ value }"><DsBadge :tone="value === 'فعال' ? 'success' : 'neutral'">{{ value }}</DsBadge></template>
              </ManagementSmartDataTable>
            </ManagementSurfaceCard>

            <ManagementSurfaceCard title="EditableTable" subtitle="افزودن، ویرایش، حذف، اعتبارسنجی و تنظیمات ستون با تم Restaurant">
              <ManagementEditableTable
                v-model="editableTablePreviewRows"
                :columns="editableTablePreviewColumns"
                row-key="name"
                title="آیتم‌های نمونه"
                storage-key="restaurant-design-system-editable-table"
                :create-empty-row="() => ({ name: '', amount: 0, status: 'پیش‌نویس' })"
                :normalize-row="(row) => ({ ...row, amount: Number(row.amount || 0) })"
              >
                <template #editor="{ draft }">
                  <div class="ds-editor-grid">
                    <label>نام محصول<input v-model.trim="draft.name" class="input" /></label>
                    <label>مبلغ پایه<input v-model.number="draft.amount" class="input" type="number" min="0" /></label>
                    <label>وضعیت<input v-model.trim="draft.status" class="input" /></label>
                  </div>
                </template>
              </ManagementEditableTable>
            </ManagementSurfaceCard>
          </section>

          <section class="ds-grid-2">
            <ManagementProductSummaryCard title="خلاصه محصول در مدیریت" subtitle="کارت خلاصه‌ی مرجع برای detail و پنل‌ها" :chips="referenceSummaryChips" />
            <ManagementProductReadinessPanel :checks="referenceChecks" :score="4" />
          </section>

          <ManagementSurfaceCard title="قالب‌های قابل استفاده مجدد محصول" subtitle="همان قاب‌های صفحه‌ی واقعی محصولات؛ محتوا با slot و داده‌ی دامنه‌ای جایگزین می‌شود.">
            <section class="ds-grid-2 ds-product-shell-grid">
              <ManagementProductCollectionShell
                title="مجموعه محصولات"
                subtitle="قاب مشترک برای لیست، گالری و کانبان"
              >
                <template #toolbar>
                  <div class="ds-shell-toolbar">
                    <label class="ds-field-sample">جستجو<input class="input" value="کاسه نودل" aria-label="جستجوی مجموعه محصول" /></label>
                    <DsButton size="sm" variant="primary">کالای جدید</DsButton>
                  </div>
                </template>
                <template #status><DsBadge tone="success">۲۴ کالا آماده نمایش</DsBadge></template>
                <ManagementSmartDataTable
                  :columns="dataTablePreviewColumns"
                  :rows="editableTablePreviewRows"
                  row-key="name"
                  :show-search="false"
                  :filterable="false"
                  :freezable="false"
                  :resizable="false"
                >
                  <template #cell-amount="{ value }">{{ Number(value).toLocaleString('fa-IR') }} ریال</template>
                  <template #cell-status="{ value }"><DsBadge :tone="value === 'فعال' ? 'success' : 'neutral'">{{ value }}</DsBadge></template>
                </ManagementSmartDataTable>
              </ManagementProductCollectionShell>

              <ManagementProductDetailShell
                title="کاسه نودل بیف"
                subtitle="قاب مشترک برای صفحات جزئیات و ویرایش"
              >
                <template #breadcrumb><span class="ds-shell-breadcrumb">محصولات / کاسه نودل بیف</span></template>
                <template #hero>
                  <ManagementProductSummaryCard title="کاسه نودل بیف" subtitle="غذای اصلی / نمایش مدیریت" :chips="referenceSummaryChips" />
                </template>
                <template #navigation>
                  <div class="ds-shell-tabs" role="tablist" aria-label="نمونه تب‌های جزئیات محصول">
                    <button type="button" class="active">اطلاعات کلی</button>
                    <button type="button">قیمت‌گذاری</button>
                    <button type="button">فرمول و Variant</button>
                  </div>
                </template>
                <template #status><DsBadge tone="success">فعال در منو</DsBadge></template>
                <ManagementProductReadinessPanel :checks="referenceChecks" :score="4" />
              </ManagementProductDetailShell>
            </section>
          </ManagementSurfaceCard>
        </template>

        <template v-else-if="activeTab === 'patterns'">
          <ManagementSurfaceCard title="پترن‌های عملیاتی" subtitle="الگوهای پرتکرار را از اینجا به صفحات جدید منتقل کن.">
            <div class="ds-pattern-grid">
              <article v-for="pattern in designSystemCatalog.patterns" :key="pattern.id" class="ds-pattern-card">
                <span class="ds-pattern-number">{{ (designSystemCatalog.patterns.indexOf(pattern) + 1).toLocaleString('fa-IR') }}</span>
                <div><strong>{{ pattern.title }}</strong><p>{{ pattern.description }}</p></div>
              </article>
            </div>
          </ManagementSurfaceCard>

          <section class="ds-grid-2">
            <ManagementSurfaceCard title="جستجو و نتیجه" subtitle="پترن جستجوی محصول با بازخورد فوری">
              <label class="ds-field-sample">عبارت جستجو<div class="ds-search-control"><Search :size="18" aria-hidden="true" /><input v-model="patternSearch" class="input" placeholder="نام محصول را بنویسید" /></div></label>
              <div class="ds-mini-results"><div v-for="row in filteredPatternProducts" :key="row.title"><Package :size="17" aria-hidden="true" /><span>{{ row.title }}</span><strong>{{ row.price }}</strong></div></div>
              <p v-if="!filteredPatternProducts.length" class="ds-empty-inline"><CircleHelp :size="18" aria-hidden="true" />محصولی با این عبارت پیدا نشد.</p>
            </ManagementSurfaceCard>

            <ManagementSurfaceCard title="وضعیت‌های قابل اعتماد" subtitle="رنگ همیشه با متن و icon همراه است.">
              <div class="ds-state-grid"><div><DsBadge tone="success">فعال</DsBadge><span>قابل سفارش و نمایش در منو</span></div><div><DsBadge tone="warning">به‌زودی</DsBadge><span>نمایش داده می‌شود، خرید بسته است</span></div><div><DsBadge tone="danger">ناموجود</DsBadge><span>نیازمند اصلاح موجودی یا تاریخ</span></div><div><DsBadge tone="neutral">در حال بارگذاری</DsBadge><span>اقدام اصلی تا دریافت نتیجه قفل است</span></div></div>
            </ManagementSurfaceCard>
          </section>
        </template>

        <template v-else>
          <ManagementSurfaceCard title="تمپلیت‌های مرجع" subtitle="هر صفحه‌ی جدید باید از نزدیک‌ترین تمپلیت شروع شود.">
            <div class="ds-template-list">
              <article v-for="template in designSystemCatalog.templates" :key="template.id" class="ds-template-card">
                <div class="ds-template-icon"><Package :size="20" aria-hidden="true" /></div>
                <div class="ds-template-copy"><strong>{{ template.title }}</strong><p>{{ template.description }}</p><code>{{ template.source }}</code></div>
                <a class="secondary-btn" :href="template.href">مشاهده</a>
              </article>
            </div>
          </ManagementSurfaceCard>
          <ManagementSurfaceCard title="نمونه‌ی تمپلیت محصول" subtitle="ترکیب کارت مشتری و خلاصه‌ی مدیریت در یک مرجع دیداری">
            <div class="ds-template-preview"><div class="ds-product-card-stage"><MenuProductCard :item="referenceProduct" layout="compact" /></div><ManagementProductSummaryCard title="کاسه نودل بیف" subtitle="نمایش داده‌ی مرجع در مدیریت" :chips="referenceSummaryChips" /></div>
          </ManagementSurfaceCard>
        </template>
      </main>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CircleHelp, Package, Search, Sparkles } from 'lucide-vue-next'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementProductReadinessPanel from '@/components/management/catalog/ManagementProductReadinessPanel.vue'
import ManagementProductSummaryCard from '@/components/management/catalog/ManagementProductSummaryCard.vue'
import ManagementProductCollectionShell from '@/components/management/catalog/ManagementProductCollectionShell.vue'
import ManagementProductDetailShell from '@/components/management/catalog/ManagementProductDetailShell.vue'
import MenuProductCard from '@/components/MenuProductCard.vue'
import DsBadge from '@/components/design/DsBadge.vue'
import DsButton from '@/components/design/DsButton.vue'
import { designTokens, tokenRows } from '@/design-system/tokens'
import { designSystemCatalog, designSystemTabs, iconCatalog } from '@/design-system/catalog'
import { defaultThemeSettings, themePresets } from '@/utils/themeSettings'

const activeTab = ref('theme')
const previewMode = ref('light')
const selectedPresetId = ref(themePresets[0]?.id || 'nooshyar-brown')
const previewSettings = ref({ ...defaultThemeSettings })
const patternSearch = ref('')
const editableTablePreviewRows = ref([
  { name: 'کاسه نودل بیف', amount: 285000, status: 'فعال' },
  { name: 'برگر مخصوص', amount: 320000, status: 'پیش‌نویس' },
])

const dataTablePreviewColumns = [
  { key: 'name', label: 'نام', width: '12rem' },
  { key: 'amount', label: 'مبلغ', type: 'currency', align: 'left' },
  { key: 'status', label: 'وضعیت', sortable: false },
]

const editableTablePreviewColumns = [
  { key: 'name', label: 'نام محصول', width: '12rem' },
  { key: 'amount', label: 'مبلغ پایه', type: 'currency', align: 'left' },
  { key: 'status', label: 'وضعیت' },
]

const selectedPreset = computed(() => themePresets.find((preset) => preset.id === selectedPresetId.value) || themePresets[0])
const previewStyle = computed(() => ({
  '--ds-preview-primary': previewSettings.value.primary,
  '--ds-preview-accent': previewSettings.value.accent,
  '--ds-preview-surface': previewSettings.value.surface,
  '--ds-preview-text': previewSettings.value.text,
}))

const referenceProduct = {
  slug: 'reference-product',
  title: 'کاسه نودل بیف تریاکی',
  short_desc: 'نودل تازه، سبزیجات فصل و سس تریاکی مخصوص نوش‌یار',
  image: '/NooshYar%20Image.png',
  base_price: 285000,
  prep_time_mins: 18,
  tags: ['پرفروش'],
  nutrition: { kcal: 640, protein_g: 28 },
  restaurant_is_customizable: 1,
  restaurant_builder_active: 1,
}

const referenceSummaryChips = [
  { key: 'status', label: 'وضعیت منو', value: 'فعال', tone: 'success' },
  { key: 'price', label: 'قیمت پایه', value: '۲۸۵٬۰۰۰ ریال', tone: 'info' },
  { key: 'category', label: 'دسته', value: 'غذاهای اصلی', tone: 'neutral' },
  { key: 'bom', label: 'فرمول ساخت', value: 'متصل', tone: 'success' },
]

const referenceChecks = [
  { key: 'image', label: 'تصویر محصول', detail: 'تصویر اصلی ثبت شده است.', ok: true },
  { key: 'slug', label: 'اسلاگ', detail: 'لینک مشتری آماده است.', ok: true },
  { key: 'description', label: 'توضیح کوتاه', detail: 'متن کارت تکمیل است.', ok: true },
  { key: 'price', label: 'قیمت', detail: 'قیمت فروش مشخص است.', ok: true },
  { key: 'category', label: 'دسته‌بندی', detail: 'دسته انتخاب شده است.', ok: true },
]

const patternProducts = [
  { title: 'کاسه نودل بیف تریاکی', price: '۲۸۵٬۰۰۰ ریال' },
  { title: 'برگر مخصوص نوش‌یار', price: '۳۲۰٬۰۰۰ ریال' },
  { title: 'سالاد سزار', price: '۱۸۵٬۰۰۰ ریال' },
]

const filteredPatternProducts = computed(() => {
  const query = String(patternSearch.value || '').trim().toLocaleLowerCase('fa')
  if (!query) return patternProducts
  return patternProducts.filter((row) => row.title.toLocaleLowerCase('fa').includes(query))
})

function selectPreset(preset) {
  selectedPresetId.value = preset.id
  previewSettings.value = { ...preset.colors }
}
</script>

<style scoped>
.ds-page-link { display: inline-flex; align-items: center; gap: var(--ds-space-2); }
.ds-intro { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--ds-space-6); padding: clamp(1rem, 3vw, 2rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-xl); background: linear-gradient(135deg, var(--ds-color-surface), var(--ds-color-surface-muted)); box-shadow: var(--ds-shadow-sm); }
.ds-intro-copy { max-width: 48rem; }
.ds-eyebrow { display: inline-flex; align-items: center; gap: var(--ds-space-2); color: var(--ds-color-action-accent); font-size: .78rem; font-weight: 800; }
.ds-intro h2 { margin: .45rem 0 .35rem; color: var(--ds-color-text-primary); font-size: clamp(1.35rem, 2vw, 2rem); line-height: 1.35; }
.ds-intro p { max-width: 44rem; margin: 0; color: var(--ds-color-text-secondary); line-height: 1.9; }
.ds-intro-stats { display: grid; grid-template-columns: repeat(3, minmax(90px, 1fr)); gap: var(--ds-space-3); min-width: min(100%, 330px); }
.ds-intro-stats div { display: grid; gap: .2rem; padding: .8rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 18%, var(--ds-color-border)); border-radius: var(--ds-radius-md); background: color-mix(in srgb, var(--ds-color-surface-raised) 72%, transparent); }
.ds-intro-stats strong { color: var(--ds-color-action-primary); font-size: 1.25rem; }
.ds-intro-stats span { color: var(--ds-color-text-muted); font-size: .72rem; }
.ds-workbench { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: var(--ds-space-4); align-items: start; }
.ds-tabs { position: sticky; top: 1rem; display: grid; gap: var(--ds-space-2); padding: var(--ds-space-2); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface); box-shadow: var(--ds-shadow-sm); }
.ds-tab { min-height: 58px; padding: .65rem .8rem; border: 1px solid transparent; border-radius: var(--ds-radius-md); display: grid; gap: .18rem; text-align: start; color: var(--ds-color-text-secondary); background: transparent; font: inherit; cursor: pointer; transition: background-color var(--ds-motion-fast) ease, color var(--ds-motion-fast) ease, border-color var(--ds-motion-fast) ease; }
.ds-tab strong { font-size: .84rem; }
.ds-tab small { color: var(--ds-color-text-muted); font-size: .7rem; }
.ds-tab:hover { background: var(--ds-color-action-primary-soft); }
.ds-tab.active { border-color: color-mix(in srgb, var(--ds-color-action-primary) 28%, var(--ds-color-border)); color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.ds-tab.active small { color: var(--ds-color-text-secondary); }
.ds-content { min-width: 0; display: grid; gap: var(--ds-space-4); }
.ds-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ds-space-4); align-items: start; }
.ds-preset-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ds-space-3); }
.ds-preset { min-height: 126px; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); display: grid; gap: .35rem; text-align: start; background: var(--ds-color-surface-raised); color: var(--ds-color-text-primary); font: inherit; cursor: pointer; transition: transform var(--ds-motion-fast) var(--ds-motion-ease), border-color var(--ds-motion-fast) ease, box-shadow var(--ds-motion-fast) ease; }
.ds-preset:hover { transform: translateY(-2px); box-shadow: var(--ds-shadow-sm); }
.ds-preset.active { border-color: var(--ds-color-action-primary); box-shadow: 0 0 0 3px var(--ds-color-action-primary-soft); }
.ds-preset strong { font-size: .88rem; }
.ds-preset small { color: var(--ds-color-text-muted); font-size: .72rem; line-height: 1.7; }
.ds-preset-swatches { display: flex; gap: .3rem; }
.ds-preset-swatches i { width: 28px; height: 28px; border: 1px solid var(--ds-color-border); border-radius: 9px; }
.ds-token-list { display: grid; gap: .35rem; }
.ds-token-row { display: flex; align-items: center; gap: .5rem; min-width: 0; padding: .48rem .55rem; border-bottom: 1px solid color-mix(in srgb, var(--ds-color-border) 60%, transparent); }
.ds-token-swatch { width: 24px; height: 24px; flex: 0 0 auto; border: 1px solid color-mix(in srgb, var(--ds-color-text-primary) 18%, transparent); border-radius: 8px; }
.ds-token-copy { min-width: 0; flex: 1; display: grid; gap: .08rem; }
.ds-token-copy strong { font-size: .78rem; }
.ds-token-copy code, .ds-token-value, .ds-reference-list code, .ds-template-copy code, .ds-icon-card code { color: var(--ds-color-text-muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .65rem; direction: ltr; text-align: start; }
.ds-token-value { white-space: nowrap; }
.ds-type-specimen { display: grid; gap: .35rem; padding: 1rem; border-radius: var(--ds-radius-md); background: var(--ds-color-surface-muted); }
.ds-type-kicker { color: var(--ds-color-action-accent); font-size: .72rem; font-weight: 800; }
.ds-type-specimen strong { color: var(--ds-color-text-primary); font-size: 1.55rem; line-height: 1.4; }
.ds-type-specimen p { margin: 0; color: var(--ds-color-text-secondary); line-height: 1.8; }
.ds-scale-row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: .8rem; margin-top: 1rem; }
.ds-scale-item { display: grid; justify-items: center; gap: .25rem; color: var(--ds-color-text-muted); font-size: .67rem; }
.ds-scale-item i { display: block; max-width: 48px; max-height: 48px; border-radius: 4px; background: var(--ds-color-action-primary); }
.ds-radius-row { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: 1rem; }
.ds-radius-row span { padding: .5rem .7rem; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); color: var(--ds-color-text-secondary); font-size: .72rem; }
.ds-preview-toolbar { display: flex; gap: .5rem; margin-bottom: .75rem; }
.ds-theme-preview { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1.1rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-preview-surface); color: var(--ds-preview-text); transition: background-color var(--ds-motion-normal) ease, color var(--ds-motion-normal) ease; }
.ds-theme-preview--dark { --ds-preview-surface: #25221f; --ds-preview-text: #eae5df; border-color: #423c38; }
.ds-theme-preview > div:first-child { display: grid; gap: .25rem; }
.ds-theme-preview strong { font-size: 1.2rem; }
.ds-theme-preview small { opacity: .74; }
.ds-preview-label { width: fit-content; padding: .2rem .55rem; border-radius: var(--ds-radius-pill); color: var(--ds-preview-primary); background: color-mix(in srgb, var(--ds-preview-primary) 14%, transparent); font-size: .7rem; font-weight: 800; }
.ds-preview-actions { display: flex; align-items: center; flex-wrap: wrap; gap: .5rem; }
.ds-preview-actions :deep(.ds-button--primary) { background: var(--ds-preview-primary); }
.ds-preview-actions :deep(.ds-badge--success) { color: var(--ds-preview-primary); }
.ds-icon-rules, .ds-sample-row { display: flex; align-items: center; flex-wrap: wrap; gap: .5rem; }
.ds-icon-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .55rem; margin-top: 1rem; }
.ds-icon-card { min-height: 100px; padding: .65rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); display: grid; justify-items: center; align-content: center; gap: .3rem; text-align: center; background: var(--ds-color-surface-raised); }
.ds-icon-box { width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; border-radius: 14px; color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.ds-icon-card strong { font-size: .76rem; }
.ds-component-stack { display: grid; gap: .8rem; }
.ds-editor-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }
.ds-editor-grid label { display: grid; gap: .3rem; color: var(--ds-color-text-secondary); font-size: .76rem; font-weight: 700; }
.ds-editor-grid label:last-child { grid-column: 1 / -1; }
.ds-field-sample { display: grid; gap: .35rem; color: var(--ds-color-text-secondary); font-size: .78rem; font-weight: 700; }
.ds-reference-list { display: grid; gap: .8rem; }
.ds-reference-list > div { display: flex; gap: .55rem; }
.ds-reference-dot { width: 9px; height: 9px; margin-top: .35rem; flex: 0 0 auto; border-radius: 50%; background: var(--ds-color-action-accent); box-shadow: 0 0 0 4px var(--ds-color-action-accent-soft); }
.ds-reference-list div > div { display: grid; gap: .12rem; }
.ds-reference-list p, .ds-template-copy p, .ds-pattern-card p { margin: 0; color: var(--ds-color-text-muted); font-size: .76rem; line-height: 1.7; }
.ds-product-card-stage { max-width: 760px; margin: 0 auto; padding: .85rem; border: 1px dashed var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-bg-page); }
.ds-product-card-stage :deep(.product-card) { box-shadow: var(--ds-shadow-sm); }
.ds-product-shell-grid { align-items: start; }
.ds-shell-toolbar { display: flex; align-items: end; justify-content: space-between; gap: var(--ds-space-3); margin-bottom: var(--ds-space-3); }
.ds-shell-toolbar .ds-field-sample { flex: 1; }
.ds-shell-breadcrumb { display: inline-flex; padding: .45rem .65rem; border-radius: var(--ds-radius-sm); color: var(--ds-color-text-muted); background: var(--ds-color-surface-muted); font-size: .75rem; }
.ds-shell-tabs { display: flex; flex-wrap: wrap; gap: .35rem; padding: .35rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-muted); }
.ds-shell-tabs button { border: 1px solid transparent; border-radius: var(--ds-radius-sm); padding: .5rem .7rem; color: var(--ds-color-text-secondary); background: transparent; font: inherit; cursor: pointer; }
.ds-shell-tabs button.active { border-color: var(--ds-color-action-primary); color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.ds-pattern-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
.ds-pattern-card { display: flex; gap: .7rem; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); }
.ds-pattern-number { width: 30px; height: 30px; flex: 0 0 auto; display: grid; place-items: center; border-radius: 10px; color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); font-weight: 900; }
.ds-pattern-card strong { font-size: .84rem; }
.ds-search-control { position: relative; display: flex; align-items: center; }
.ds-search-control > svg { position: absolute; right: .75rem; color: var(--ds-color-text-muted); z-index: 1; }
.ds-search-control input { padding-right: 2.4rem; }
.ds-mini-results { display: grid; gap: .35rem; margin-top: .75rem; }
.ds-mini-results > div { display: flex; align-items: center; gap: .5rem; padding: .55rem .6rem; border: 1px solid var(--ds-color-border); border-radius: 10px; background: var(--ds-color-surface-raised); }
.ds-mini-results span { flex: 1; font-size: .78rem; }
.ds-mini-results strong { color: var(--ds-color-action-primary); font-size: .72rem; }
.ds-empty-inline { display: flex; align-items: center; gap: .45rem; margin: .75rem 0 0; color: var(--ds-color-text-muted); font-size: .78rem; }
.ds-state-grid { display: grid; gap: .55rem; }
.ds-state-grid > div { display: flex; align-items: center; gap: .55rem; padding: .55rem; border-bottom: 1px solid color-mix(in srgb, var(--ds-color-border) 60%, transparent); }
.ds-state-grid span { color: var(--ds-color-text-secondary); font-size: .76rem; }
.ds-template-list { display: grid; gap: .55rem; }
.ds-template-card { display: flex; align-items: center; gap: .7rem; padding: .7rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); }
.ds-template-icon { width: 42px; height: 42px; flex: 0 0 auto; display: grid; place-items: center; border-radius: 13px; color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.ds-template-copy { min-width: 0; flex: 1; display: grid; gap: .1rem; }
.ds-template-copy strong { font-size: .84rem; }
.ds-template-card .secondary-btn { white-space: nowrap; }
.ds-template-preview { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 980px) { .ds-intro { align-items: stretch; flex-direction: column; } .ds-workbench { grid-template-columns: 1fr; } .ds-tabs { position: static; grid-template-columns: repeat(5, minmax(0, 1fr)); overflow-x: auto; } .ds-tab { min-width: 140px; } }
@media (max-width: 720px) { .ds-grid-2, .ds-template-preview, .ds-pattern-grid, .ds-editor-grid { grid-template-columns: 1fr; } .ds-preset-grid { grid-template-columns: 1fr; } .ds-icon-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .ds-intro-stats { min-width: 0; } .ds-theme-preview, .ds-template-card { align-items: flex-start; flex-direction: column; } .ds-preview-actions { width: 100%; } }
@media (prefers-reduced-motion: reduce) { .ds-tab, .ds-preset, .ds-theme-preview { transition: none; } }
</style>
