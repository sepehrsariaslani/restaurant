from pathlib import Path

p = Path("frontend/src/pages/management/ManagementSiteSettingsPage.vue")
s = p.read_text()

# Tabs: keep only general, components, loader
s = s.replace(
	"const tabs = [\n  { value: 'general', label: 'عمومی' },\n  { value: 'components', label: 'کامپوننت‌ها' },\n  { value: 'content', label: 'محتوای سایت' },\n  { value: 'hero', label: 'اسلایدر هدر' },\n  { value: 'about', label: 'درباره ما' },\n  { value: 'loader', label: 'Loader' },\n  { value: 'faq', label: 'FAQ' },\n]\n",
	"const tabs = [\n  { value: 'general', label: 'عمومی' },\n  { value: 'components', label: 'طراحی صفحات' },\n  { value: 'loader', label: 'Loader' },\n]\n",
)

# Imports for richer preview
s = s.replace(
	"import SiteHeroBanner from '@/components/SiteHeroBanner.vue'\nimport SiteHeroSection from '@/components/SiteHeroSection.vue'\n",
	"import SiteHeaderHero from '@/components/SiteHeaderHero.vue'\nimport SiteHeroBanner from '@/components/SiteHeroBanner.vue'\nimport SiteHeroFoodbar from '@/components/SiteHeroFoodbar.vue'\nimport SiteHeroSection from '@/components/SiteHeroSection.vue'\n",
)

# Add builder state after activeTab
s = s.replace(
	"const activeTab = ref('general')\n\nconst tabs = [",
	"const activeTab = ref('general')\nconst activeDesignPage = ref('home')\nconst activeDesignComponent = ref('homeHero')\nconst previewDevice = ref('desktop')\n\nconst previewDeviceOptions = [\n  { value: 'desktop', label: 'دسکتاپ' },\n  { value: 'mobile', label: 'گوشی' },\n]\n\nconst tabs = [",
)

# Add builder registry before loaderPreviewSettings
registry = r"""
const designPageRegistry = [
  {
    value: 'global',
    label: 'عمومی',
    components: [
      { value: 'header', label: 'هدر سایت', status: 'عمومی' },
      { value: 'footer', label: 'فوتر سایت', status: 'عمومی' },
    ],
  },
  {
    value: 'home',
    label: 'صفحه اصلی',
    components: [
      { value: 'homeHero', label: 'هیرو صفحه اصلی', status: 'محتوا و اسلایدر' },
      { value: 'menuSearch', label: 'سرچ منو', status: 'اختیاری' },
      { value: 'featuredBlock', label: 'ویژه و پرفروش', status: 'اختیاری' },
      { value: 'categoryRail', label: 'دسته‌بندی‌ها', status: 'نمایش منو' },
    ],
  },
  {
    value: 'about',
    label: 'درباره ما',
    components: [
      { value: 'aboutSections', label: 'درباره ما', status: 'بخش‌ها' },
      { value: 'faqItems', label: 'FAQ', status: 'سوالات' },
    ],
  },
  {
    value: 'product',
    label: 'جزئیات محصول',
    components: [
      { value: 'productCard', label: 'کارت محصول', status: 'استایل' },
    ],
  },
]

const designPages = computed(() =>
  designPageRegistry.map((page) => ({
    value: page.value,
    label: page.label,
    count: page.components.length,
  })),
)

const currentDesignPage = computed(() => designPageRegistry.find((page) => page.value === activeDesignPage.value) || designPageRegistry[0])
const currentDesignComponents = computed(() => currentDesignPage.value?.components || [])
const currentDesignComponent = computed(() => currentDesignComponents.value.find((item) => item.value === activeDesignComponent.value) || currentDesignComponents.value[0] || null)

function selectDesignPage(page) {
  activeDesignPage.value = page
  const nextPage = designPageRegistry.find((item) => item.value === page) || designPageRegistry[0]
  activeDesignComponent.value = nextPage.components[0]?.value || ''
}

function selectDesignComponent(component) {
  activeDesignComponent.value = component
}

const aboutPreviewTitle = computed(() => aboutSections.value.find((row) => Number(row.is_active || 0))?.title || 'داستان برند ما')
const aboutPreviewText = computed(() => aboutSections.value.find((row) => Number(row.is_active || 0))?.body_text || 'بخش درباره ما از همین صفحه مدیریت می‌شود.')

const previewFoodbarItems = computed(() => [
  {
    slug: 'preview-salad',
    title: previewHeroTitle.value || 'سالاد سالم روز',
    short_desc: previewHeroDescription.value || 'غذای سالم و تازه با مواد اولیه روزانه',
    category_title: 'پیشنهادی',
    base_price: 240000,
    image: previewHeroImage.value || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=700&auto=format&fit=crop&q=70',
    rating: '5.0',
  },
  {
    slug: 'preview-bowl',
    title: 'بول انرژی',
    short_desc: 'ترکیب سبزیجات، پروتئین و سس مخصوص',
    category_title: 'سالم',
    base_price: 210000,
    image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700&auto=format&fit=crop&q=70',
    rating: '4.9',
  },
])

"""
s = s.replace(
	"const loaderPreviewSettings = computed(() =>", registry + "const loaderPreviewSettings = computed(() =>"
)

# Expand hero preview component
s = s.replace(
	"const heroPreviewComponent = computed(() => {\n  if (String(webSettings.hero_section_variant || 'off').trim() === 'fullscreen') {\n    return SiteHeroSection\n  }\n  if (String(webSettings.hero_section_variant || 'off').trim() === 'banner') {\n    return SiteHeroBanner\n  }\n  return null\n})\n",
	"const heroPreviewComponent = computed(() => {\n  const variant = String(webSettings.hero_section_variant || 'off').trim()\n  if (variant === 'fullscreen') return SiteHeroSection\n  if (variant === 'banner') return SiteHeroBanner\n  if (variant === 'cover') return SiteHeaderHero\n  if (variant === 'foodbar') return SiteHeroFoodbar\n  return null\n})\n",
)

s = s.replace(
	"  if (heroPreviewComponent.value === SiteHeroSection) {\n    return {\n      ...base,\n      categories: [],\n    }\n  }\n  return base\n})\n",
	"  if (heroPreviewComponent.value === SiteHeroSection) {\n    return {\n      ...base,\n      categories: [],\n    }\n  }\n  if (heroPreviewComponent.value === SiteHeaderHero) {\n    return {\n      branding: previewBranding.value,\n      cartCount: 3,\n      page: 'landing',\n      preview: true,\n      previewDevice: previewDevice.value,\n    }\n  }\n  if (heroPreviewComponent.value === SiteHeroFoodbar) {\n    return {\n      items: previewFoodbarItems.value,\n      currency: 'TOMAN',\n    }\n  }\n  return base\n})\n",
)

start = s.index("    <template v-else-if=\"activeTab === 'components'\">")
end = s.index("    <template v-else-if=\"activeTab === 'loader'\">")
new_block = r"""    <template v-else-if="activeTab === 'components'">
      <div class="designer-shell site-designer-shell">
        <aside class="designer-preview site-designer-preview" aria-label="پیش‌نمایش طراحی صفحه">
          <div class="preview-frame">
            <div class="preview-topbar">
              <div>
                <span>{{ currentDesignPage?.label || 'پیش‌نمایش' }}</span>
                <small>{{ currentDesignComponent?.label || '' }}</small>
              </div>
              <div class="preview-device-toggle" role="group" aria-label="انتخاب نمای پیش‌نمایش">
                <button
                  v-for="device in previewDeviceOptions"
                  :key="device.value"
                  type="button"
                  :class="{ active: previewDevice === device.value }"
                  @click="previewDevice = device.value"
                >
                  {{ device.label }}
                </button>
              </div>
            </div>

            <div class="preview-stage" :class="`preview-stage--${previewDevice}`">
              <div class="preview-viewport" :class="[`preview-viewport--${previewDevice}`, `preview-context--${previewDevice}`]">
                <div class="site-preview-shell compact-preview">
                  <PublicHeader
                    v-if="activeDesignPage !== 'product' || activeDesignComponent !== 'productCard'"
                    :key="`preview-header-${webSettings.header_variant}-${activeDesignPage}-${previewDevice}`"
                    :branding="previewBranding"
                    :page="'preview'"
                    :cart-count="3"
                    :has-last-order="false"
                    :last-order-url="'/menu'"
                    :header-variant="webSettings.header_variant"
                    :preview="true"
                  />

                  <template v-if="activeDesignPage === 'home'">
                    <MenuHeroHeader
                      v-if="webSettings.menu_search_variant === 'search-card'"
                      :key="`menu-search-${webSettings.menu_search_variant}-${previewDevice}`"
                      :branding="previewBranding"
                      :search="'جستجو در منو...'"
                      :cart-count="3"
                      :preview-device="previewDevice"
                    />

                    <component
                      :is="heroPreviewComponent"
                      v-if="heroPreviewComponent"
                      :key="`hero-${webSettings.hero_section_variant}-${previewDevice}`"
                      v-bind="heroPreviewProps"
                      class="site-preview-hero"
                    />

                    <div v-else class="site-preview-empty">
                      <strong>هیرو خاموش است</strong>
                    </div>

                    <div class="mini-section" v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
                      <strong>{{ webSettings.restaurant_menu_highlight_title || 'ویژه و پرفروش' }}</strong>
                      <div class="mini-products"><span></span><span></span><span></span></div>
                    </div>
                  </template>

                  <template v-else-if="activeDesignPage === 'about'">
                    <div class="about-preview-card">
                      <small>درباره ما</small>
                      <strong>{{ aboutPreviewTitle }}</strong>
                      <p>{{ aboutPreviewText }}</p>
                    </div>
                    <div class="faq-preview-card" v-if="faqItems.length">
                      <span>{{ faqItems.length }} سوال متداول</span>
                    </div>
                  </template>

                  <template v-else-if="activeDesignPage === 'product'">
                    <div class="card-preview-row compact-card-preview">
                      <div class="card-preview-item">
                        <MenuItemCard
                          :key="`product-preview-${webSettings.card_variant}`"
                          :item="previewCardItem"
                          :card-variant="webSettings.card_variant"
                          :currency="'TOMAN'"
                        />
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <div class="mini-section">
                      <strong>محتوای نمونه</strong>
                      <p>کامپوننت‌های عمومی روی صفحات سایت اعمال می‌شوند.</p>
                    </div>
                  </template>

                  <component
                    :is="footerPreviewComponent"
                    v-if="footerPreviewComponent && activeDesignPage !== 'product'"
                    :key="`footer-${webSettings.footer_variant}`"
                    v-bind="footerPreviewProps"
                    class="site-preview-footer"
                  />
                  <div v-else-if="activeDesignPage !== 'product'" class="site-preview-empty site-preview-empty--footer">
                    <strong>فوتر خاموش است</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <section class="designer-panel site-designer-panel">
          <ManagementSurfaceCard title="طراحی صفحات" subtitle="صفحه و کامپوننت را انتخاب کن.">
            <div class="page-switcher">
              <button
                v-for="pageItem in designPages"
                :key="pageItem.value"
                type="button"
                class="page-chip"
                :class="{ active: activeDesignPage === pageItem.value }"
                @click="selectDesignPage(pageItem.value)"
              >
                <strong>{{ pageItem.label }}</strong>
                <small>{{ pageItem.count }} بخش</small>
              </button>
            </div>
          </ManagementSurfaceCard>

          <ManagementSurfaceCard>
            <div class="component-list">
              <button
                v-for="componentItem in currentDesignComponents"
                :key="componentItem.value"
                type="button"
                class="component-chip"
                :class="{ active: activeDesignComponent === componentItem.value }"
                @click="selectDesignComponent(componentItem.value)"
              >
                <span>{{ componentItem.label }}</span>
                <small>{{ componentItem.status }}</small>
              </button>
            </div>
          </ManagementSurfaceCard>

          <ManagementSurfaceCard :title="currentDesignComponent?.label || 'کامپوننت'">
            <template v-if="activeDesignComponent === 'header'">
              <div class="variant-row">
                <button v-for="opt in headerVariantOptions" :key="opt.value" type="button" class="variant-card" :class="{ selected: webSettings.header_variant === opt.value }" @click="webSettings.header_variant = opt.value">
                  <div class="variant-preview" :style="opt.previewStyle"><div class="vp-bar" :style="opt.barStyle"><span class="vp-brand"></span><span class="vp-links"></span></div></div>
                  <div class="variant-meta"><strong>{{ opt.label }}</strong><small>{{ opt.desc }}</small></div>
                  <span class="variant-check" v-if="webSettings.header_variant === opt.value">✓</span>
                </button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'footer'">
              <div class="variant-row">
                <button v-for="opt in footerVariantOptions" :key="opt.value" type="button" class="variant-card" :class="{ selected: webSettings.footer_variant === opt.value }" @click="webSettings.footer_variant = opt.value">
                  <div class="variant-preview" :style="opt.previewStyle"><div class="vp-footer" :style="opt.footerStyle"><span class="vp-footer-brand"></span><span class="vp-footer-links"></span></div></div>
                  <div class="variant-meta"><strong>{{ opt.label }}</strong><small>{{ opt.desc }}</small></div>
                  <span class="variant-check" v-if="webSettings.footer_variant === opt.value">✓</span>
                </button>
              </div>
              <div class="inline-editor" v-if="webSettings.footer_variant !== 'off'">
                <div class="form-grid">
                  <label class="span-2">توضیحات برند<textarea class="textarea" v-model.trim="webSettings.footer_description" /></label>
                  <label>شماره تماس<input class="input" v-model.trim="webSettings.footer_phone" /></label>
                  <label>ایمیل<input class="input" type="email" v-model.trim="webSettings.footer_email" /></label>
                  <label class="span-2">آدرس<input class="input" v-model.trim="webSettings.footer_address" /></label>
                  <label>اینستاگرام<input class="input" v-model.trim="webSettings.footer_instagram" /></label>
                  <label>تلگرام<input class="input" v-model.trim="webSettings.footer_telegram" /></label>
                  <label class="span-2">کپی‌رایت<input class="input" v-model.trim="webSettings.footer_copyright" /></label>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'homeHero'">
              <div class="variant-row">
                <button v-for="opt in heroVariantOptions" :key="opt.value" type="button" class="variant-card" :class="{ selected: webSettings.hero_section_variant === opt.value }" @click="webSettings.hero_section_variant = opt.value">
                  <div class="variant-preview" :style="opt.previewStyle"><div class="vp-hero" :style="opt.heroStyle"><span class="vp-title"></span><span class="vp-sub"></span></div></div>
                  <div class="variant-meta"><strong>{{ opt.label }}</strong><small>{{ opt.desc }}</small></div>
                  <span class="variant-check" v-if="webSettings.hero_section_variant === opt.value">✓</span>
                </button>
              </div>

              <div class="inline-editor" v-if="webSettings.hero_section_variant !== 'off'">
                <div class="form-grid">
                  <label class="span-2">عنوان هیرو<input class="input" v-model.trim="webSettings.hero_section_title" /></label>
                  <label class="span-2">توضیحات<textarea class="textarea" v-model.trim="webSettings.hero_section_description" /></label>
                  <label>متن CTA<input class="input" v-model.trim="webSettings.hero_section_cta" /></label>
                  <label>
                    تصویر
                    <input class="input" v-model.trim="webSettings.hero_image" placeholder="/files/hero.jpg" />
                    <div class="image-upload-row">
                      <button type="button" class="secondary-btn mini" @click="heroImageInput.click()">انتخاب عکس</button>
                      <button type="button" class="secondary-btn mini danger" v-if="webSettings.hero_image" @click="webSettings.hero_image = ''">حذف</button>
                    </div>
                    <input ref="heroImageInput" type="file" accept="image/png,image/jpeg,image/jpg,image/webp,image/gif" style="display:none" @change="handleHeroImageUpload" />
                    <img v-if="String(webSettings.hero_image || '').trim()" class="image-preview" :src="webSettings.hero_image" alt="Hero bg" />
                  </label>
                  <label>موقعیت تصویر<SearchableDropdown v-model="webSettings.hero_image_position" :options="imagePositionOptions" placeholder="انتخاب موقعیت" /></label>
                </div>
              </div>

              <div class="inline-editor hero-slider-editor">
                <ManagementEditableTable v-model="heroSlides" title="اسلایدر همین هیرو" subtitle="" tone="accent" :columns="heroColumns" popup-title-add="افزودن اسلاید" popup-title-edit="ویرایش اسلاید" popup-subtitle="" :create-empty-row="createEmptyHeroSlide" :normalize-row="normalizeHeroSlide" :validate-row="validateHeroSlide">
                  <template #cell-is_active="{ value }"><span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span></template>
                  <template #editor="{ draft }">
                    <div class="editor-grid">
                      <label>عنوان<input class="input" v-model.trim="draft.title" /></label>
                      <label>ترتیب<input class="input" type="number" min="0" v-model.number="draft.sort_order" /></label>
                      <label class="span-2">زیرعنوان<textarea class="textarea" v-model.trim="draft.subtitle" /></label>
                      <label>تصویر<input class="input" v-model.trim="draft.image" placeholder="/files/slide.jpg" /><img v-if="String(draft.image || '').trim()" class="image-preview" :src="draft.image" alt="Slide preview" /></label>
                      <label>لینک محصول<input class="input" v-model.trim="draft.linked_item" /></label>
                      <label>متن دکمه<input class="input" v-model.trim="draft.cta_label" /></label>
                      <label>لینک دکمه<input class="input" v-model.trim="draft.cta_url" placeholder="/menu" /></label>
                      <label>شعبه<input class="input" v-model.trim="draft.branch" /></label>
                      <label class="check"><input type="checkbox" v-model="draft.is_active" :true-value="1" :false-value="0" />فعال</label>
                    </div>
                  </template>
                </ManagementEditableTable>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'menuSearch'">
              <div class="variant-row">
                <button v-for="opt in menuSearchVariantOptions" :key="opt.value" type="button" class="variant-card" :class="{ selected: webSettings.menu_search_variant === opt.value }" @click="webSettings.menu_search_variant = opt.value">
                  <div class="variant-preview" :style="opt.previewStyle"><div class="vp-search-card" :style="opt.searchStyle"><span class="vp-search-title"></span><span class="vp-search-input"></span></div></div>
                  <div class="variant-meta"><strong>{{ opt.label }}</strong><small>{{ opt.desc }}</small></div>
                  <span class="variant-check" v-if="webSettings.menu_search_variant === opt.value">✓</span>
                </button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'featuredBlock'">
              <div class="form-grid">
                <label class="check span-2"><input type="checkbox" v-model="webSettings.restaurant_menu_highlight_enabled" :true-value="1" :false-value="0" />نمایش بخش ویژه و پرفروش</label>
                <template v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
                  <label class="span-2">عنوان<input class="input" v-model.trim="webSettings.restaurant_menu_highlight_title" /></label>
                  <label class="check"><input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_featured" :true-value="1" :false-value="0" />آیتم‌های ویژه</label>
                  <label>تعداد ویژه<input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_featured_limit" /></label>
                  <label class="check"><input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_best_seller" :true-value="1" :false-value="0" />پرفروش‌ها</label>
                  <label>تعداد پرفروش<input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_best_seller_limit" /></label>
                </template>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'categoryRail'">
              <div class="variant-row">
                <button type="button" class="variant-card" :class="{ selected: webSettings.category_rail_variant === 'pill' }" @click="webSettings.category_rail_variant = 'pill'"><div class="variant-preview" style="background:#f5f0eb;padding:8px"><div style="display:flex;gap:6px;margin-top:8px"><div style="background:#fff;border:1px solid #ddd;border-radius:10px;width:56px;height:38px"></div><div style="background:rgba(111,74,49,.12);border:1px solid rgba(111,74,49,.4);border-radius:10px;width:56px;height:38px"></div><div style="background:#fff;border:1px solid #ddd;border-radius:10px;width:56px;height:38px"></div></div></div><div class="variant-meta"><strong>متنی</strong><small>دکمه‌های ساده و خوانا</small></div><span class="variant-check" v-if="webSettings.category_rail_variant === 'pill'">✓</span></button>
                <button type="button" class="variant-card" :class="{ selected: webSettings.category_rail_variant === 'image' }" @click="webSettings.category_rail_variant = 'image'"><div class="variant-preview" style="background:#f5f0eb;padding:8px"><div style="display:flex;gap:8px;margin-top:6px;justify-content:center"><div style="width:40px;height:40px;border-radius:50%;background:var(--accent-green,#6f4a31)"></div><div style="width:40px;height:40px;border-radius:50%;background:#e0d8cf"></div><div style="width:40px;height:40px;border-radius:50%;background:#e0d8cf"></div></div></div><div class="variant-meta"><strong>تصویری</strong><small>دایره‌های تصویر با برچسب</small></div><span class="variant-check" v-if="webSettings.category_rail_variant === 'image'">✓</span></button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'productCard'">
              <div class="variant-row">
                <button v-for="opt in cardVariantOptions" :key="opt.value" type="button" class="variant-card" :class="{ selected: webSettings.card_variant === opt.value }" @click="webSettings.card_variant = opt.value">
                  <div class="variant-preview" :style="opt.previewStyle"><div class="vp-card-preview" :style="opt.cardStyle"></div></div>
                  <div class="variant-meta"><strong>{{ opt.label }}</strong><small>{{ opt.desc }}</small></div>
                  <span class="variant-check" v-if="webSettings.card_variant === opt.value">✓</span>
                </button>
              </div>
              <div class="card-preview-row"><div class="card-preview-item"><MenuItemCard :key="`card-preview-${webSettings.card_variant}`" :item="previewCardItem" :card-variant="webSettings.card_variant" :currency="'TOMAN'" /></div></div>
            </template>

            <template v-else-if="activeDesignComponent === 'aboutSections'">
              <div class="section-toolbar"><button class="secondary-btn" type="button" @click="openAboutAdd">افزودن بخش</button></div>
              <ManagementListView :columns="aboutColumns" :rows="aboutSections" row-key="name" :row-clickable="true" @row-click="openAboutEdit">
                <template #cell-is_active="{ value }"><span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span></template>
                <template #cell-actions="{ row, rowIndex }"><div class="row-actions"><button class="secondary-btn mini" type="button" @click.stop="openAboutEdit(row)">ویرایش</button><button class="secondary-btn mini danger" type="button" @click.stop="removeAboutRow(rowIndex)">حذف</button></div></template>
              </ManagementListView>
              <div v-if="aboutEditorOpen" class="inline-editor">
                <div class="editor-grid">
                  <label>نوع بخش<SearchableDropdown v-model="aboutDraft.section_type" :options="aboutSectionTypeOptions" placeholder="نوع بخش" search-placeholder="جستجو..." /></label>
                  <label>عنوان<input class="input" v-model.trim="aboutDraft.title" /></label>
                  <label>ترتیب<input class="input" type="number" min="0" v-model.number="aboutDraft.sort_order" /></label>
                  <label class="span-2">زیرعنوان<textarea class="textarea" v-model.trim="aboutDraft.subtitle" /></label>
                  <label class="span-2">متن اصلی<textarea class="textarea" v-model.trim="aboutDraft.body_text" /></label>
                  <label>آیکون<input class="input" v-model.trim="aboutDraft.icon" /></label>
                  <label>سال/برچسب<input class="input" v-model.trim="aboutDraft.year_label" /></label>
                  <label>Badge<input class="input" v-model.trim="aboutDraft.badge" /></label>
                  <label>سال تاسیس<input class="input" v-model.trim="aboutDraft.founded_year" /></label>
                  <label class="check"><input type="checkbox" v-model="aboutDraft.highlight" :true-value="1" :false-value="0" />هایلایت</label>
                  <label>تصویر<input class="input" v-model.trim="aboutDraft.image" /><img v-if="String(aboutDraft.image || '').trim()" class="image-preview" :src="aboutDraft.image" alt="About preview" /></label>
                  <label>برچسب آمار<input class="input" v-model.trim="aboutDraft.stat_label" /></label>
                  <label>مقدار آمار<input class="input" v-model.trim="aboutDraft.stat_value" /></label>
                  <label class="check"><input type="checkbox" v-model="aboutDraft.is_active" :true-value="1" :false-value="0" />فعال</label>
                </div>
                <div class="editor-actions"><button class="secondary-btn" type="button" @click="closeAboutEditor">انصراف</button><button class="primary-btn" type="button" @click="saveAboutDraft">ثبت</button></div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'faqItems'">
              <div class="section-toolbar"><button class="secondary-btn" type="button" @click="openFaqAdd">افزودن سوال</button></div>
              <ManagementListView :columns="faqColumns" :rows="faqItems" row-key="name" :row-clickable="true" @row-click="openFaqEdit">
                <template #cell-is_active="{ value }"><span :class="['state-pill', Number(value) ? 'on' : 'off']">{{ Number(value) ? 'فعال' : 'غیرفعال' }}</span></template>
                <template #cell-actions="{ row, rowIndex }"><div class="row-actions"><button class="secondary-btn mini" type="button" @click.stop="openFaqEdit(row)">ویرایش</button><button class="secondary-btn mini danger" type="button" @click.stop="removeFaqRow(rowIndex)">حذف</button></div></template>
              </ManagementListView>
              <div v-if="faqEditorOpen" class="inline-editor">
                <div class="editor-grid">
                  <label class="span-2">سوال<input class="input" v-model.trim="faqDraft.question" /></label>
                  <label>دسته‌بندی<input class="input" v-model.trim="faqDraft.category" /></label>
                  <label>آیکون<input class="input" v-model.trim="faqDraft.icon" /></label>
                  <label class="span-2">تصویر<input class="input" v-model.trim="faqDraft.image" /><img v-if="String(faqDraft.image || '').trim()" class="image-preview image-preview-wide" :src="faqDraft.image" alt="FAQ preview" /></label>
                  <label class="span-2">توضیح کوتاه<input class="input" v-model.trim="faqDraft.summary" /></label>
                  <label>ترتیب<input class="input" type="number" min="0" v-model.number="faqDraft.sort_order" /></label>
                  <label class="check"><input type="checkbox" v-model="faqDraft.is_active" :true-value="1" :false-value="0" />فعال</label>
                  <label class="span-2">پاسخ<textarea class="textarea" v-model.trim="faqDraft.answer" /></label>
                </div>
                <div class="editor-actions"><button class="secondary-btn" type="button" @click="closeFaqEditor">انصراف</button><button class="primary-btn" type="button" @click="saveFaqDraft">ثبت</button></div>
              </div>
            </template>

            <template v-else>
              <p class="muted">یک کامپوننت را انتخاب کن.</p>
            </template>
          </ManagementSurfaceCard>
        </section>
      </div>
    </template>

"""
s = s[:start] + new_block + s[end:]

# Add CSS before @media max 900 or end style
css = r"""
.site-designer-shell {
  display: grid;
  grid-template-columns: minmax(360px, 0.95fr) minmax(0, 1.25fr);
  gap: 0.85rem;
  align-items: start;
}

.site-designer-preview {
  position: sticky;
  top: 1rem;
  min-width: 0;
}

.preview-frame {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 20px;
  background: #fff;
  overflow: hidden;
}

.preview-topbar {
  min-height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.preview-topbar > div:first-child {
  display: grid;
  gap: 0.1rem;
}

.preview-topbar span {
  font-weight: 900;
}

.preview-topbar small {
  color: var(--text-muted, #786b61);
}

.preview-device-toggle {
  display: inline-flex;
  padding: 0.16rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 999px;
  background: #fff;
}

.preview-device-toggle button {
  min-height: 32px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-muted, #786b61);
  font-family: inherit;
  font-size: 0.72rem;
  padding: 0.22rem 0.58rem;
  cursor: pointer;
}

.preview-device-toggle button.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  color: var(--ink-900, #1c1411);
  font-weight: 800;
}

.preview-stage {
  position: relative;
  height: 720px;
  overflow: auto;
  background: linear-gradient(145deg, rgb(var(--palette-eggshell-rgb) / 0.65), #fff);
  padding: 1rem;
}

.preview-stage--mobile {
  display: flex;
  justify-content: center;
}

.preview-viewport {
  transform-origin: top right;
  background: #fff;
}

.preview-viewport--desktop {
  width: 1280px;
  min-height: 1600px;
  transform: scale(0.5);
  margin-bottom: -800px;
}

.preview-viewport--mobile {
  width: 390px;
  min-height: 900px;
  transform: scale(0.92);
  transform-origin: top center;
  border-radius: 34px;
  overflow: hidden;
  box-shadow: 0 18px 45px rgb(15 23 42 / 0.16);
  margin-bottom: -72px;
}

.compact-preview {
  padding: 0;
  max-height: none;
  overflow: visible;
}

.page-switcher,
.component-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.page-chip,
.component-chip {
  min-height: 44px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 16px;
  background: #fff;
  color: var(--ink-900, #1c1411);
  font-family: inherit;
  cursor: pointer;
}

.page-chip {
  display: grid;
  gap: 0.1rem;
  padding: 0.65rem 0.85rem;
  text-align: right;
}

.component-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 0.75rem;
}

.page-chip small,
.component-chip small {
  color: var(--text-muted, #786b61);
  font-size: 0.68rem;
}

.page-chip.active,
.component-chip.active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.inline-editor {
  margin-top: 0.85rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.hero-slider-editor {
  display: grid;
  gap: 0.65rem;
}

.mini-section,
.about-preview-card,
.faq-preview-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 18px;
  background: #fff;
  padding: 0.85rem;
  display: grid;
  gap: 0.35rem;
}

.mini-section p,
.about-preview-card p {
  margin: 0;
  color: var(--text-muted, #786b61);
  line-height: 1.7;
}

.mini-products {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.45rem;
}

.mini-products span {
  height: 58px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgb(var(--palette-eggshell-rgb) / 0.9), rgb(var(--palette-deep-sapphire-rgb) / 0.08));
}

.preview-context--mobile :deep(.app-header) {
  padding: max(0.35rem, env(safe-area-inset-top)) 0.5rem 0 !important;
}

.preview-context--mobile :deep(.header-surface),
.preview-context--mobile :deep(.desktop-nav),
.preview-context--mobile :deep(.search-pill--desktop),
.preview-context--mobile :deep(.management-login-pill),
.preview-context--mobile :deep(.action-icon-pill),
.preview-context--mobile :deep(.center-search-btn),
.preview-context--mobile :deep(.hero-desktop-nav),
.preview-context--mobile :deep(.hero-mgmt-pill) {
  display: none !important;
}

.preview-context--mobile :deep(.webapp-header),
.preview-context--mobile :deep(.hero-hamburger) {
  display: grid !important;
}

.preview-context--mobile :deep(.hero-header),
.preview-context--mobile :deep(.foodbar-hero) {
  min-height: 700px !important;
}

.preview-context--mobile :deep(.foodbar-hero) {
  grid-template-columns: 1fr !important;
  grid-template-rows: auto auto auto auto !important;
}

.preview-context--mobile :deep(.fb-left),
.preview-context--mobile :deep(.fb-right),
.preview-context--mobile :deep(.fb-thumbs-area),
.preview-context--mobile :deep(.fb-dots),
.preview-context--mobile :deep(.fb-social) {
  grid-column: auto !important;
  grid-row: auto !important;
}

.preview-context--mobile :deep(.fb-left),
.preview-context--mobile :deep(.fb-right) {
  padding: 1.2rem !important;
}

.preview-context--mobile :deep(.fb-product-name) {
  font-size: 1.9rem !important;
}

.preview-context--mobile :deep(.fb-thumbs-area) {
  display: grid !important;
  grid-template-columns: 1fr !important;
  padding: 0 1rem 1rem !important;
}

.preview-context--mobile :deep(.site-footer .footer-grid) {
  grid-template-columns: 1fr !important;
}

"""
s = s.replace("@media (max-width: 900px) {\n", css + "@media (max-width: 900px) {\n")
s = s.replace(
	"  .form-grid,\n  .editor-grid {\n    grid-template-columns: minmax(0, 1fr);\n  }\n",
	"  .site-designer-shell {\n    grid-template-columns: minmax(0, 1fr);\n  }\n\n  .site-designer-preview {\n    position: static;\n  }\n\n  .preview-viewport--desktop {\n    transform: scale(0.36);\n    margin-bottom: -1024px;\n  }\n\n  .form-grid,\n  .editor-grid {\n    grid-template-columns: minmax(0, 1fr);\n  }\n",
)

p.write_text(s)
print("rebuilt site settings page builder")
