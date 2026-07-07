<template>
  <ManagementPageScaffold title="تنظیمات سایت" subtitle="مدیریت محتوای صفحات عمومی مثل FAQ، درباره ما و اسلایدهای هدر">
    <ManagementSurfaceCard tone="accent">
      <div class="toolbar">
        <template v-if="!['theme', 'layout'].includes(activeStage)">
          <button class="secondary-btn" type="button" :disabled="secondaryActionDisabled" @click="handleSecondaryAction">
            {{ secondaryActionLabel }}
          </button>
          <button class="primary-btn" type="button" :disabled="primaryActionDisabled" @click="saveSettings">
            {{ primaryActionLabel }}
          </button>
        </template>
        <span class="muted">{{ statusText }}</span>
        <span class="muted" v-if="stageSaveHint">{{ stageSaveHint }}</span>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft" title="فرآیند ویرایش سایت" subtitle="تم را انتخاب کن، ظاهر هر صفحه را مشخص کن، بعد چیدمان و محتوا را نهایی کن.">
      <div class="workflow-stages">
        <button
          v-for="stage in workflowStages"
          :key="stage.value"
          type="button"
          class="workflow-stage"
          :class="{ active: activeStage === stage.value }"
          @click="activeStage = stage.value"
        >
          <strong>{{ stage.label }}</strong>
          <small>{{ stage.caption }}</small>
        </button>
      </div>
    </ManagementSurfaceCard>

    <p class="error" v-if="error">{{ error }}</p>

    <template v-if="activeStage === 'identity' && activeTab === 'general'">
      <ManagementSurfaceCard title="ابزارهای پایه" subtitle="اطلاعات اصلی سایت و Loader را از این مرحله مدیریت کن.">
        <div class="tabs">
          <button type="button" class="tab-btn" :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">
            اطلاعات سایت
          </button>
          <button type="button" class="tab-btn" :class="{ active: activeTab === 'loader' }" @click="activeTab = 'loader'">
            Loader
          </button>
        </div>
      </ManagementSurfaceCard>

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

    <template v-else-if="activeStage === 'theme'">
      <ManagementThemeStudio
        :initial-settings="themeDraft"
        save-mode="draft"
        save-button-label="ذخیره پیش‌نویس تم"
        @save-draft="saveThemeDraft"
        @reset-draft="resetThemeDraft"
      />
    </template>

    <template v-else-if="activeStage === 'layout' && activeLayoutPanel === 'visual'">
      <ManagementSurfaceCard title="چیدمان و کامپوننت‌ها" subtitle="کنترل بصری هر صفحه را در همان context واقعی آن ویرایش کن.">
        <div class="page-switcher">
          <button
            v-for="pageItem in builderPageOptions"
            :key="pageItem.value"
            type="button"
            class="page-chip"
            :class="{ active: activeBuilderPage === pageItem.value }"
            @click="activeBuilderPage = pageItem.value"
          >
            <strong>{{ pageItem.label }}</strong>
            <small>{{ pageItem.subtitle }}</small>
          </button>
        </div>
        <div class="page-switcher page-switcher--subtle">
          <button
            v-for="panel in layoutPanelOptions"
            :key="panel.value"
            type="button"
            class="page-chip"
            :class="{ active: activeLayoutPanel === panel.value }"
            @click="activeLayoutPanel = panel.value"
          >
            <strong>{{ panel.label }}</strong>
            <small>{{ panel.caption }}</small>
          </button>
        </div>
      </ManagementSurfaceCard>

      <div class="designer-shell">
        <aside class="designer-preview" aria-label="پیش‌نمایش طراحی صفحه">
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
              <div class="preview-viewport" :class="`preview-viewport--${previewDevice}`">
                <div class="site-preview-shell compact-preview">
              <PublicHeader
                v-if="activeDesignPage !== 'product' || activeDesignComponent !== 'productCard'"
                :key="`preview-header-${webSettings.header_variant}-${activeDesignPage}`"
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
                  :key="`menu-search-${webSettings.menu_search_variant}`"
                  :branding="previewBranding"
                  :search="'جستجو در منو...'"
                  :cart-count="3"
                />

                <div v-if="webSettings.hero_section_variant === 'slider'" class="slider-hero-preview site-preview-hero">
                  <div class="slider-hero-copy">
                    <span>اسلایدر هیرو</span>
                    <h2>{{ previewHeroTitle || 'اسلایدر پیشنهادهای ویژه' }}</h2>
                    <p>{{ previewHeroDescription || 'اسلایدهای تصویری برای معرفی محصولات و کمپین‌های روزانه.' }}</p>
                  </div>
                  <div class="slider-hero-card">
                    <img :src="heroSlidesPreviewImage" alt="Hero slide preview" />
                    <strong>{{ heroSlidesPreviewTitle }}</strong>
                  </div>
                </div>
                <SiteHeaderHero
                  v-else-if="webSettings.hero_section_variant === 'cover'"
                  :key="`cover-${previewDevice}-${webSettings.hero_image}`"
                  :branding="previewBranding"
                  :cart-count="3"
                  :page="'landing'"
                  :preview="true"
                  class="site-preview-hero"
                />
                <div
                  v-else-if="webSettings.hero_section_variant === 'foodbar'"
                  class="healthy-cover-preview site-preview-hero"
                  :style="previewHeroImage ? { '--hero-img': `url('${previewHeroImage}')` } : {}"
                >
                  <div class="hcp-media"></div>
                  <div class="hcp-content">
                    <span class="hcp-badge">تازه، سالم، روزانه</span>
                    <h2>{{ previewHeroTitle || 'سبک زندگی سالم، انتخاب هر روز ما' }}</h2>
                    <p>{{ previewHeroDescription || 'غذاهای سالم و متنوع با بهترین مواد اولیه تازه برای یک زندگی پرانرژی و متعادل.' }}</p>
                    <div class="hcp-actions">
                      <span>{{ previewHeroCta || 'سفارش آنلاین' }}</span>
                      <span class="ghost">مشاهده منو</span>
                    </div>
                    <div class="hcp-features">
                      <span>مواد اولیه تازه</span>
                      <span>ارسال سریع</span>
                    </div>
                  </div>
                </div>
                <component
                  :is="heroPreviewComponent"
                  v-else-if="heroPreviewComponent"
                  :key="`hero-${webSettings.hero_section_variant}`"
                  v-bind="heroPreviewProps"
                  class="site-preview-hero"
                />
                <div v-else class="site-preview-empty">
                  <strong>هیرو خاموش است</strong>
                </div>

                <div class="mini-section" v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
                  <strong>{{ webSettings.restaurant_menu_highlight_title || 'ویژه و پرفروش' }}</strong>
                  <div class="mini-products">
                    <span></span><span></span><span></span>
                  </div>
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

              <template v-else-if="activeDesignPage === 'faq'">
                <div class="faq-preview-card">
                  <strong>سوالات متداول</strong>
                  <span>{{ faqItems.length }} سوال در منبع داده فعلی</span>
                </div>
              </template>

              <template v-else-if="activeDesignPage === 'product_groups'">
                <div class="about-preview-card">
                  <small>گروه‌های محصول</small>
                  <strong>{{ builderGroupsCount }} گروه آماده نمایش</strong>
                  <p>چیدمان و نحوه ارائه این گروه‌ها از theme و layout همین صفحه تبعیت می‌کند.</p>
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

        <section class="designer-panel">
          <ManagementSurfaceCard title="کنترل‌های بصری" subtitle="هدر و فوتر همیشه در دسترس‌اند و کنترل‌های اختصاصی صفحه از همین‌جا می‌آیند.">
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
                <button
                  v-for="opt in headerVariantOptions"
                  :key="opt.value"
                  type="button"
                  class="variant-card"
                  :class="{ selected: webSettings.header_variant === opt.value }"
                  @click="webSettings.header_variant = opt.value"
                >
                  <div class="variant-preview" :style="opt.previewStyle">
                    <div class="vp-bar" :style="opt.barStyle">
                      <span class="vp-brand"></span>
                      <span class="vp-links"></span>
                    </div>
                  </div>
                  <div class="variant-meta">
                    <strong>{{ opt.label }}</strong>
                    <small>{{ opt.desc }}</small>
                  </div>
                  <span class="variant-check" v-if="webSettings.header_variant === opt.value">✓</span>
                </button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'footer'">
              <div class="variant-row">
                <button
                  v-for="opt in footerVariantOptions"
                  :key="opt.value"
                  type="button"
                  class="variant-card"
                  :class="{ selected: webSettings.footer_variant === opt.value }"
                  @click="webSettings.footer_variant = opt.value"
                >
                  <div class="variant-preview" :style="opt.previewStyle">
                    <div class="vp-footer" :style="opt.footerStyle">
                      <span class="vp-footer-brand"></span>
                      <span class="vp-footer-links"></span>
                    </div>
                  </div>
                  <div class="variant-meta">
                    <strong>{{ opt.label }}</strong>
                    <small>{{ opt.desc }}</small>
                  </div>
                  <span class="variant-check" v-if="webSettings.footer_variant === opt.value">✓</span>
                </button>
              </div>

              <div class="inline-editor" v-if="webSettings.footer_variant !== 'off'">
                <div class="form-grid">
                  <label class="span-2">
                    توضیحات برند
                    <textarea class="textarea" v-model.trim="webSettings.footer_description" />
                  </label>
                  <label>
                    شماره تماس
                    <input class="input" v-model.trim="webSettings.footer_phone" />
                  </label>
                  <label>
                    ایمیل
                    <input class="input" type="email" v-model.trim="webSettings.footer_email" />
                  </label>
                  <label class="span-2">
                    آدرس
                    <input class="input" v-model.trim="webSettings.footer_address" />
                  </label>
                  <label>
                    اینستاگرام
                    <input class="input" v-model.trim="webSettings.footer_instagram" />
                  </label>
                  <label>
                    تلگرام
                    <input class="input" v-model.trim="webSettings.footer_telegram" />
                  </label>
                  <label class="span-2">
                    کپی‌رایت
                    <input class="input" v-model.trim="webSettings.footer_copyright" />
                  </label>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'homeHero'">
              <div class="variant-row">
                <button
                  v-for="opt in heroVariantOptions"
                  :key="opt.value"
                  type="button"
                  class="variant-card"
                  :class="{ selected: webSettings.hero_section_variant === opt.value }"
                  @click="webSettings.hero_section_variant = opt.value"
                >
                  <div class="variant-preview" :style="opt.previewStyle">
                    <div class="vp-hero" :style="opt.heroStyle">
                      <span class="vp-title"></span>
                      <span class="vp-sub"></span>
                    </div>
                  </div>
                  <div class="variant-meta">
                    <strong>{{ opt.label }}</strong>
                    <small>{{ opt.desc }}</small>
                  </div>
                  <span class="variant-check" v-if="webSettings.hero_section_variant === opt.value">✓</span>
                </button>
              </div>

              <div class="inline-editor" v-if="webSettings.hero_section_variant !== 'off'">
                <div class="hero-editor-head">
                  <strong>{{ activeHeroContentMeta.title }}</strong>
                  <small>{{ activeHeroContentMeta.hint }}</small>
                </div>

                <div class="form-grid">
                  <label class="span-2" v-if="activeHeroContentMeta.fields.includes('title')">
                    {{ activeHeroContentMeta.titleLabel }}
                    <input class="input" v-model.trim="webSettings.hero_section_title" :placeholder="activeHeroContentMeta.titlePlaceholder" />
                  </label>
                  <label class="span-2" v-if="activeHeroContentMeta.fields.includes('description')">
                    {{ activeHeroContentMeta.descriptionLabel }}
                    <textarea class="textarea" v-model.trim="webSettings.hero_section_description" :placeholder="activeHeroContentMeta.descriptionPlaceholder" />
                  </label>
                  <label v-if="activeHeroContentMeta.fields.includes('cta')">
                    متن دکمه اصلی
                    <input class="input" v-model.trim="webSettings.hero_section_cta" :placeholder="activeHeroContentMeta.ctaPlaceholder" />
                  </label>
                  <label v-if="activeHeroContentMeta.fields.includes('image')">
                    {{ activeHeroContentMeta.imageLabel }}
                    <input class="input" v-model.trim="webSettings.hero_image" placeholder="/files/hero.jpg" />
                    <div class="image-upload-row">
                      <button type="button" class="secondary-btn mini" @click="heroImageInput.click()">انتخاب عکس</button>
                      <button type="button" class="secondary-btn mini danger" v-if="webSettings.hero_image" @click="webSettings.hero_image = ''">حذف</button>
                    </div>
                    <input
                      ref="heroImageInput"
                      type="file"
                      accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                      style="display:none"
                      @change="handleHeroImageUpload"
                    />
                    <img v-if="String(webSettings.hero_image || '').trim()" class="image-preview" :src="webSettings.hero_image" alt="Hero bg" />
                  </label>
                  <label v-if="activeHeroContentMeta.fields.includes('imagePosition')">
                    موقعیت تصویر
                    <SearchableDropdown v-model="webSettings.hero_image_position" :options="imagePositionOptions" placeholder="انتخاب موقعیت" />
                  </label>
                </div>
              </div>

              <div class="inline-editor hero-slider-editor" v-if="activeHeroContentMeta.usesSlides">
                <ManagementEditableTable
                  v-model="heroSlides"
                  title="اسلایدر همین هیرو"
                  subtitle=""
                  tone="accent"
                  :columns="heroColumns"
                  popup-title-add="افزودن اسلاید"
                  popup-title-edit="ویرایش اسلاید"
                  popup-subtitle=""
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
                        <img v-if="String(draft.image || '').trim()" class="image-preview" :src="draft.image" alt="Slide preview" />
                      </label>
                      <label>
                        لینک محصول
                        <input class="input" v-model.trim="draft.linked_item" />
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
                        شعبه
                        <input class="input" v-model.trim="draft.branch" />
                      </label>
                      <label class="check">
                        <input type="checkbox" v-model="draft.is_active" :true-value="1" :false-value="0" />
                        فعال
                      </label>
                    </div>
                  </template>
                </ManagementEditableTable>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'menuSearch'">
              <div class="variant-row">
                <button
                  v-for="opt in menuSearchVariantOptions"
                  :key="opt.value"
                  type="button"
                  class="variant-card"
                  :class="{ selected: webSettings.menu_search_variant === opt.value }"
                  @click="webSettings.menu_search_variant = opt.value"
                >
                  <div class="variant-preview" :style="opt.previewStyle">
                    <div class="vp-search-card" :style="opt.searchStyle">
                      <span class="vp-search-title"></span>
                      <span class="vp-search-input"></span>
                    </div>
                  </div>
                  <div class="variant-meta">
                    <strong>{{ opt.label }}</strong>
                    <small>{{ opt.desc }}</small>
                  </div>
                  <span class="variant-check" v-if="webSettings.menu_search_variant === opt.value">✓</span>
                </button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'featuredBlock'">
              <div class="form-grid">
                <label class="check span-2">
                  <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_enabled" :true-value="1" :false-value="0" />
                  نمایش بخش ویژه و پرفروش
                </label>
                <template v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
                  <label class="span-2">
                    عنوان
                    <input class="input" v-model.trim="webSettings.restaurant_menu_highlight_title" />
                  </label>
                  <label class="check">
                    <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_featured" :true-value="1" :false-value="0" />
                    آیتم‌های ویژه
                  </label>
                  <label>
                    تعداد ویژه
                    <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_featured_limit" />
                  </label>
                  <label class="check">
                    <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_best_seller" :true-value="1" :false-value="0" />
                    پرفروش‌ها
                  </label>
                  <label>
                    تعداد پرفروش
                    <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_best_seller_limit" />
                  </label>
                </template>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'categoryRail'">
              <div class="variant-row">
                <button type="button" class="variant-card" :class="{ selected: webSettings.category_rail_variant === 'pill' }" @click="webSettings.category_rail_variant = 'pill'">
                  <div class="variant-preview" style="background: #f5f0eb; padding: 8px;">
                    <div style="display: flex; gap: 6px; margin-top: 8px;">
                      <div style="background: #fff; border: 1px solid #ddd; border-radius: 10px; width: 56px; height: 38px;"></div>
                      <div style="background: rgba(111,74,49,0.12); border: 1px solid rgba(111,74,49,0.4); border-radius: 10px; width: 56px; height: 38px;"></div>
                      <div style="background: #fff; border: 1px solid #ddd; border-radius: 10px; width: 56px; height: 38px;"></div>
                    </div>
                  </div>
                  <div class="variant-meta"><strong>متنی</strong><small>دکمه‌های ساده و خوانا</small></div>
                  <span class="variant-check" v-if="webSettings.category_rail_variant === 'pill'">✓</span>
                </button>
                <button type="button" class="variant-card" :class="{ selected: webSettings.category_rail_variant === 'image' }" @click="webSettings.category_rail_variant = 'image'">
                  <div class="variant-preview" style="background: #f5f0eb; padding: 8px;">
                    <div style="display: flex; gap: 8px; margin-top: 6px; justify-content: center;">
                      <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--accent-green, #6f4a31);"></div>
                      <div style="width: 40px; height: 40px; border-radius: 50%; background: #e0d8cf;"></div>
                      <div style="width: 40px; height: 40px; border-radius: 50%; background: #e0d8cf;"></div>
                    </div>
                  </div>
                  <div class="variant-meta"><strong>تصویری</strong><small>دایره‌های تصویر با برچسب</small></div>
                  <span class="variant-check" v-if="webSettings.category_rail_variant === 'image'">✓</span>
                </button>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'productCard'">
              <div class="variant-row">
                <button
                  v-for="opt in cardVariantOptions"
                  :key="opt.value"
                  type="button"
                  class="variant-card"
                  :class="{ selected: webSettings.card_variant === opt.value }"
                  @click="webSettings.card_variant = opt.value"
                >
                  <div class="variant-preview" :style="opt.previewStyle">
                    <div class="vp-card-preview" :style="opt.cardStyle"></div>
                  </div>
                  <div class="variant-meta">
                    <strong>{{ opt.label }}</strong>
                    <small>{{ opt.desc }}</small>
                  </div>
                  <span class="variant-check" v-if="webSettings.card_variant === opt.value">✓</span>
                </button>
              </div>
              <div class="card-preview-row">
                <div class="card-preview-item">
                  <MenuItemCard :key="`card-preview-${webSettings.card_variant}`" :item="previewCardItem" :card-variant="webSettings.card_variant" :currency="'TOMAN'" />
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'aboutSections'">
              <div class="section-toolbar">
                <button class="secondary-btn" type="button" @click="openAboutAdd">افزودن بخش</button>
              </div>
              <ManagementListView :columns="aboutColumns" :rows="aboutSections" row-key="name" :row-clickable="true" @row-click="openAboutEdit">
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

              <div v-if="aboutEditorOpen" class="inline-editor">
                <div class="editor-grid">
                  <label>
                    نوع بخش
                    <SearchableDropdown v-model="aboutDraft.section_type" :options="aboutSectionTypeOptions" placeholder="نوع بخش" search-placeholder="جستجو..." />
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
                    <input class="input" v-model.trim="aboutDraft.icon" />
                  </label>
                  <label>
                    سال/برچسب
                    <input class="input" v-model.trim="aboutDraft.year_label" />
                  </label>
                  <label>
                    Badge
                    <input class="input" v-model.trim="aboutDraft.badge" />
                  </label>
                  <label>
                    سال تاسیس
                    <input class="input" v-model.trim="aboutDraft.founded_year" />
                  </label>
                  <label class="check">
                    <input type="checkbox" v-model="aboutDraft.highlight" :true-value="1" :false-value="0" />
                    هایلایت
                  </label>
                  <label>
                    تصویر
                    <input class="input" v-model.trim="aboutDraft.image" />
                    <img v-if="String(aboutDraft.image || '').trim()" class="image-preview" :src="aboutDraft.image" alt="About preview" />
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
                  <button class="primary-btn" type="button" @click="saveAboutDraft">ثبت</button>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'faqItems'">
              <div class="section-toolbar">
                <button class="secondary-btn" type="button" @click="openFaqAdd">افزودن سوال</button>
              </div>
              <ManagementListView :columns="faqColumns" :rows="faqItems" row-key="name" :row-clickable="true" @row-click="openFaqEdit">
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

              <div v-if="faqEditorOpen" class="inline-editor">
                <div class="editor-grid">
                  <label class="span-2">
                    سوال
                    <input class="input" v-model.trim="faqDraft.question" />
                  </label>
                  <label>
                    دسته‌بندی
                    <input class="input" v-model.trim="faqDraft.category" />
                  </label>
                  <label>
                    آیکون
                    <input class="input" v-model.trim="faqDraft.icon" />
                  </label>
                  <label class="span-2">
                    تصویر
                    <input class="input" v-model.trim="faqDraft.image" />
                    <img v-if="String(faqDraft.image || '').trim()" class="image-preview image-preview-wide" :src="faqDraft.image" alt="FAQ preview" />
                  </label>
                  <label class="span-2">
                    توضیح کوتاه
                    <input class="input" v-model.trim="faqDraft.summary" />
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
                  <button class="primary-btn" type="button" @click="saveFaqDraft">ثبت</button>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'aboutShell'">
              <div class="inline-editor">
                <p class="muted">ظاهر صفحه درباره ما بیشتر از تم و چیدمان همین صفحه می‌آید.</p>
                <div class="context-actions">
                  <button class="secondary-btn" type="button" @click="activeStage = 'layout'; activeBuilderPage = 'about'; activeLayoutPanel = 'builder'">
                    رفتن به چیدمان درباره ما
                  </button>
                  <button class="secondary-btn" type="button" @click="activeStage = 'content'; activeBuilderPage = 'about'">
                    ویرایش محتوای درباره ما
                  </button>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'faqShell'">
              <div class="inline-editor">
                <p class="muted">در FAQ، تم و page builder ظاهر کلی را مشخص می‌کنند و سوال‌ها در مرحله محتوا مدیریت می‌شوند.</p>
                <div class="context-actions">
                  <button class="secondary-btn" type="button" @click="activeStage = 'layout'; activeBuilderPage = 'faq'; activeLayoutPanel = 'builder'">
                    رفتن به چیدمان FAQ
                  </button>
                  <button class="secondary-btn" type="button" @click="activeStage = 'content'; activeBuilderPage = 'faq'">
                    ویرایش سوالات و پاسخ‌ها
                  </button>
                </div>
              </div>
            </template>

            <template v-else-if="activeDesignComponent === 'groupsShell'">
              <div class="inline-editor">
                <p class="muted">صفحه گروه‌های محصول از تم، category rail و layout همین صفحه تبعیت می‌کند.</p>
                <div class="context-actions">
                  <button class="secondary-btn" type="button" @click="activeStage = 'layout'; activeBuilderPage = 'product_groups'; activeLayoutPanel = 'builder'">
                    رفتن به چیدمان گروه‌ها
                  </button>
                  <button class="secondary-btn" type="button" @click="activeStage = 'content'; activeBuilderPage = 'product_groups'">
                    منبع داده گروه‌ها
                  </button>
                </div>
              </div>
            </template>

            <template v-else>
              <p class="muted">یک کامپوننت را انتخاب کن.</p>
            </template>
          </ManagementSurfaceCard>
        </section>
      </div>
    </template>

    <template v-else-if="activeStage === 'layout' && activeLayoutPanel === 'builder'">
      <ManagementSurfaceCard title="چیدمان و کامپوننت‌ها" subtitle="انتخاب بلاک، ترتیب، فعال بودن و variantها در همین workspace انجام می‌شود.">
        <div class="page-switcher">
          <button
            v-for="pageItem in builderPageOptions"
            :key="pageItem.value"
            type="button"
            class="page-chip"
            :class="{ active: activeBuilderPage === pageItem.value }"
            @click="activeBuilderPage = pageItem.value"
          >
            <strong>{{ pageItem.label }}</strong>
            <small>{{ pageItem.subtitle }}</small>
          </button>
        </div>
        <div class="page-switcher page-switcher--subtle">
          <button
            v-for="panel in layoutPanelOptions"
            :key="panel.value"
            type="button"
            class="page-chip"
            :class="{ active: activeLayoutPanel === panel.value }"
            @click="activeLayoutPanel = panel.value"
          >
            <strong>{{ panel.label }}</strong>
            <small>{{ panel.caption }}</small>
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard>
        <KeepAlive>
          <ManagementPageBuilderWorkspace
            v-if="activeStage === 'layout'"
            :page="activeBuilderPage"
            :boot="builderBoot"
            :load-layout-fn="loadDraftPageLayout"
            :save-layout-fn="saveDraftPageLayout"
            :refresh-key="builderWorkspaceRevision"
          />
        </KeepAlive>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="activeBuilderPage === 'home'"
        title="منابع محتوای صفحه اصلی"
        subtitle="اسلایدر هیرو و تنظیمات هدر/فوتر هنوز از تنظیمات سراسری مدیریت می‌شوند."
      >
        <div class="context-actions">
          <button class="secondary-btn" type="button" @click="activeLayoutPanel = 'visual'; activeDesignPage = 'home'; activeDesignComponent = 'homeHero'">
            ویرایش هیرو و اسلایدر
          </button>
          <button class="secondary-btn" type="button" @click="activeLayoutPanel = 'visual'; activeDesignPage = 'home'; activeDesignComponent = 'header'">
            ویرایش هدر و فوتر
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else-if="activeBuilderPage === 'about'"
        title="محتوای درباره ما"
        subtitle="در این مرحله فقط چیدمان را تعیین کن؛ ویرایش متن‌ها و آیتم‌ها در مرحله محتوا انجام می‌شود."
      >
        <div class="context-actions">
          <span class="muted">{{ aboutSections.length }} بخش محتوایی برای این صفحه ثبت شده است.</span>
          <button class="secondary-btn" type="button" @click="activeStage = 'content'; activeBuilderPage = 'about'">
            ویرایش محتوای درباره ما
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else-if="activeBuilderPage === 'faq'"
        title="سوالات متداول"
        subtitle="در این مرحله فقط ترتیب و نمایش سکشن‌ها را بچین؛ سوال‌ها و جواب‌ها در مرحله محتوا مدیریت می‌شوند."
      >
        <div class="context-actions">
          <span class="muted">{{ faqItems.length }} سوال در منبع داده فعلی ثبت شده است.</span>
          <button class="secondary-btn" type="button" @click="activeStage = 'content'; activeBuilderPage = 'faq'">
            ویرایش سوالات و پاسخ‌ها
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else
        title="منبع داده‌ی گروه‌های محصول"
        subtitle="چیدمان این صفحه از builder می‌آید، اما خود گروه‌ها از تنظیمات منو خوانده می‌شوند."
      >
        <div class="context-actions">
          <span class="muted">{{ builderGroupsCount }} گروه در داده‌های فعلی منو در دسترس است.</span>
          <a class="secondary-btn" href="/management/menu-groups">رفتن به مدیریت گروه‌های منو</a>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeStage === 'content'">
      <ManagementSurfaceCard title="محتوای صفحه" subtitle="صفحه موردنظر را انتخاب کن و متن‌ها، آیتم‌ها و داده‌های همان صفحه را ویرایش کن.">
        <div class="page-switcher">
          <button
            v-for="pageItem in builderPageOptions"
            :key="pageItem.value"
            type="button"
            class="page-chip"
            :class="{ active: activeBuilderPage === pageItem.value }"
            @click="activeBuilderPage = pageItem.value"
          >
            <strong>{{ pageItem.label }}</strong>
            <small>{{ pageItem.subtitle }}</small>
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="activeBuilderPage === 'home'"
        title="متن‌ها و CTAهای صفحه اصلی"
        subtitle="نام برند، تیترها و متن‌های اصلی از اینجا کنترل می‌شوند."
      >
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
            متن دکمه اصلی
            <input class="input" v-model.trim="webSettings.primary_cta_label" />
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
          <label class="span-2">
            تیتر هدر سایت
            <input class="input" v-model.trim="webSettings.hero_title" />
          </label>
          <label class="span-2">
            زیرتیتر هدر سایت
            <textarea class="textarea" v-model.trim="webSettings.hero_subtitle" />
          </label>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="activeBuilderPage === 'home'"
        :title="activeHeroContentMeta.title"
        :subtitle="activeHeroContentMeta.hint"
      >
        <div class="form-grid">
          <label class="span-2" v-if="activeHeroContentMeta.fields.includes('title')">
            {{ activeHeroContentMeta.titleLabel }}
            <input class="input" v-model.trim="webSettings.hero_section_title" :placeholder="activeHeroContentMeta.titlePlaceholder" />
          </label>
          <label class="span-2" v-if="activeHeroContentMeta.fields.includes('description')">
            {{ activeHeroContentMeta.descriptionLabel }}
            <textarea class="textarea" v-model.trim="webSettings.hero_section_description" :placeholder="activeHeroContentMeta.descriptionPlaceholder" />
          </label>
          <label v-if="activeHeroContentMeta.fields.includes('cta')">
            متن دکمه اصلی
            <input class="input" v-model.trim="webSettings.hero_section_cta" :placeholder="activeHeroContentMeta.ctaPlaceholder" />
          </label>
          <label v-if="activeHeroContentMeta.fields.includes('image')">
            {{ activeHeroContentMeta.imageLabel }}
            <input class="input" v-model.trim="webSettings.hero_image" placeholder="/files/hero.jpg" />
            <div class="image-upload-row">
              <button type="button" class="secondary-btn mini" @click="heroImageInput.click()">انتخاب عکس</button>
              <button type="button" class="secondary-btn mini danger" v-if="webSettings.hero_image" @click="webSettings.hero_image = ''">حذف</button>
            </div>
            <input
              ref="heroImageInput"
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
              style="display:none"
              @change="handleHeroImageUpload"
            />
            <img v-if="String(webSettings.hero_image || '').trim()" class="image-preview" :src="webSettings.hero_image" alt="Hero bg" />
          </label>
          <label v-if="activeHeroContentMeta.fields.includes('imagePosition')">
            موقعیت تصویر
            <SearchableDropdown v-model="webSettings.hero_image_position" :options="imagePositionOptions" placeholder="انتخاب موقعیت" />
          </label>
        </div>

        <div class="inline-editor hero-slider-editor" v-if="activeHeroContentMeta.usesSlides">
          <ManagementEditableTable
            v-model="heroSlides"
            title="اسلایدر هیرو"
            subtitle=""
            tone="accent"
            :columns="heroColumns"
            popup-title-add="افزودن اسلاید"
            popup-title-edit="ویرایش اسلاید"
            popup-subtitle=""
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
                  <img v-if="String(draft.image || '').trim()" class="image-preview" :src="draft.image" alt="Slide preview" />
                </label>
                <label>
                  لینک محصول
                  <input class="input" v-model.trim="draft.linked_item" />
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
                  شعبه
                  <input class="input" v-model.trim="draft.branch" />
                </label>
                <label class="check">
                  <input type="checkbox" v-model="draft.is_active" :true-value="1" :false-value="0" />
                  فعال
                </label>
              </div>
            </template>
          </ManagementEditableTable>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-if="activeBuilderPage === 'home'"
        title="بخش ویژه و پرفروش"
        subtitle="تیتر و آیتم‌های این بخش را از اینجا تنظیم کن."
      >
        <div class="form-grid">
          <label class="check span-2">
            <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_enabled" :true-value="1" :false-value="0" />
            نمایش بخش ویژه و پرفروش
          </label>
          <template v-if="Number(webSettings.restaurant_menu_highlight_enabled || 0) === 1">
            <label class="span-2">
              عنوان
              <input class="input" v-model.trim="webSettings.restaurant_menu_highlight_title" />
            </label>
            <label class="check">
              <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_featured" :true-value="1" :false-value="0" />
              آیتم‌های ویژه
            </label>
            <label>
              تعداد ویژه
              <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_featured_limit" />
            </label>
            <label class="check">
              <input type="checkbox" v-model="webSettings.restaurant_menu_highlight_show_best_seller" :true-value="1" :false-value="0" />
              پرفروش‌ها
            </label>
            <label>
              تعداد پرفروش
              <input class="input" type="number" min="0" max="50" v-model.number="webSettings.restaurant_menu_highlight_best_seller_limit" />
            </label>
          </template>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else-if="activeBuilderPage === 'about'"
        title="محتوای درباره ما"
        subtitle="بخش‌های این صفحه از همین لیست به بلاک‌های صفحه تزریق می‌شوند."
      >
        <div class="section-toolbar">
          <button class="secondary-btn" type="button" @click="openAboutAdd">افزودن بخش</button>
        </div>
        <ManagementListView :columns="aboutColumns" :rows="aboutSections" row-key="name" :row-clickable="true" @row-click="openAboutEdit">
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

        <div v-if="aboutEditorOpen" class="inline-editor">
          <div class="editor-grid">
            <label>
              نوع بخش
              <SearchableDropdown v-model="aboutDraft.section_type" :options="aboutSectionTypeOptions" placeholder="نوع بخش" search-placeholder="جستجو..." />
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
              <input class="input" v-model.trim="aboutDraft.icon" />
            </label>
            <label>
              سال/برچسب
              <input class="input" v-model.trim="aboutDraft.year_label" />
            </label>
            <label>
              Badge
              <input class="input" v-model.trim="aboutDraft.badge" />
            </label>
            <label>
              سال تاسیس
              <input class="input" v-model.trim="aboutDraft.founded_year" />
            </label>
            <label class="check">
              <input type="checkbox" v-model="aboutDraft.highlight" :true-value="1" :false-value="0" />
              هایلایت
            </label>
            <label>
              تصویر
              <input class="input" v-model.trim="aboutDraft.image" />
              <img v-if="String(aboutDraft.image || '').trim()" class="image-preview" :src="aboutDraft.image" alt="About preview" />
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
            <button class="primary-btn" type="button" @click="saveAboutDraft">ثبت</button>
          </div>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else-if="activeBuilderPage === 'faq'"
        title="سوالات متداول"
        subtitle="سوال‌ها و پاسخ‌هایی که در صفحه FAQ نمایش داده می‌شوند از همین لیست می‌آیند."
      >
        <div class="section-toolbar">
          <button class="secondary-btn" type="button" @click="openFaqAdd">افزودن سوال</button>
        </div>
        <ManagementListView :columns="faqColumns" :rows="faqItems" row-key="name" :row-clickable="true" @row-click="openFaqEdit">
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

        <div v-if="faqEditorOpen" class="inline-editor">
          <div class="editor-grid">
            <label class="span-2">
              سوال
              <input class="input" v-model.trim="faqDraft.question" />
            </label>
            <label>
              دسته‌بندی
              <input class="input" v-model.trim="faqDraft.category" />
            </label>
            <label>
              آیکون
              <input class="input" v-model.trim="faqDraft.icon" />
            </label>
            <label class="span-2">
              تصویر
              <input class="input" v-model.trim="faqDraft.image" />
              <img v-if="String(faqDraft.image || '').trim()" class="image-preview image-preview-wide" :src="faqDraft.image" alt="FAQ preview" />
            </label>
            <label class="span-2">
              توضیح کوتاه
              <input class="input" v-model.trim="faqDraft.summary" />
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
            <button class="primary-btn" type="button" @click="saveFaqDraft">ثبت</button>
          </div>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        v-else
        title="منبع داده‌ی گروه‌های محصول"
        subtitle="این صفحه از گروه‌های واقعی منو تغذیه می‌شود و این مرحله فقط همان منبع را مدیریت می‌کند."
      >
        <div class="context-actions">
          <span class="muted">{{ builderGroupsCount }} گروه در داده‌های فعلی منو در دسترس است.</span>
          <a class="secondary-btn" href="/management/menu-groups">رفتن به مدیریت گروه‌های منو</a>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeStage === 'identity' && activeTab === 'loader'">
      <ManagementSurfaceCard title="ابزارهای پایه" subtitle="اطلاعات اصلی سایت و Loader را از این مرحله مدیریت کن.">
        <div class="tabs">
          <button type="button" class="tab-btn" :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">
            اطلاعات سایت
          </button>
          <button type="button" class="tab-btn" :class="{ active: activeTab === 'loader' }" @click="activeTab = 'loader'">
            Loader
          </button>
        </div>
      </ManagementSurfaceCard>

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

    <template v-else-if="activeStage === 'review'">
      <ManagementSurfaceCard title="بازبینی و انتشار" subtitle="پیش‌نویس‌های ذخیره‌شده را بررسی کن و فقط وقتی همه‌چیز آماده بود روی سایت منتشر کن.">
        <div class="review-summary-grid">
          <article class="review-summary-card" :class="{ changed: hasThemeDraftChanges }">
            <strong>تم</strong>
            <small>{{ hasThemeDraftChanges ? 'دارای تغییر draft' : 'بدون تغییر نسبت به نسخه live' }}</small>
          </article>
          <article class="review-summary-card" :class="{ changed: hasSiteDraftChanges }">
            <strong>هویت و محتوا</strong>
            <small>{{ hasSiteDraftChanges ? 'متن‌ها، loader یا داده‌ها تغییر کرده‌اند' : 'بدون تغییر نسبت به نسخه live' }}</small>
          </article>
          <article class="review-summary-card" :class="{ changed: hasLayoutDraftChanges }">
            <strong>چیدمان صفحات</strong>
            <small>{{ hasLayoutDraftChanges ? `${changedLayoutPages.length} صفحه دارای draft است` : 'هیچ layout draftی ندارید' }}</small>
          </article>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="صفحات دارای تغییر" subtitle="این لیست مشخص می‌کند draft کدام صفحه‌ها هنوز منتشر نشده است.">
        <div class="review-page-list">
          <article
            v-for="pageItem in builderPageOptions"
            :key="pageItem.value"
            class="review-page-item"
            :class="{ changed: changedLayoutPages.includes(pageItem.value) }"
          >
            <div>
              <strong>{{ pageItem.label }}</strong>
              <small>{{ pageItem.subtitle }}</small>
            </div>
            <span class="state-pill" :class="changedLayoutPages.includes(pageItem.value) ? 'on' : 'off'">
              {{ changedLayoutPages.includes(pageItem.value) ? 'دارای draft' : 'بدون draft چیدمان' }}
            </span>
          </article>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="انتشار نهایی" subtitle="انتشار، draft تم، محتوای صفحات و layoutهای ذخیره‌شده را به نسخه live تبدیل می‌کند.">
        <div class="context-actions">
          <button class="secondary-btn danger" type="button" :disabled="saving || !hasAnyDraftChanges" @click="discardAllDrafts">
            حذف همه پیش‌نویس‌ها
          </button>
          <button class="primary-btn" type="button" :disabled="saving || !hasAnyDraftChanges" @click="publishAllDrafts">
            {{ saving ? 'در حال انتشار...' : 'انتشار روی سایت' }}
          </button>
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
import { computed, reactive, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import MenuHeroHeader from '@/components/MenuHeroHeader.vue'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteLoaderRenderer from '@/components/SiteLoaderRenderer.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import SiteHeroBanner from '@/components/SiteHeroBanner.vue'
import SiteHeroSection from '@/components/SiteHeroSection.vue'
import SiteHeaderHero from '@/components/SiteHeaderHero.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageBuilderWorkspace from '@/components/management/ManagementPageBuilderWorkspace.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementThemeStudio from '@/components/management/ManagementThemeStudio.vue'
import MenuItemCard from '@/components/MenuItemCard.vue'
import {
  getManagementSiteSettings,
  getManagementThemeSettings,
  setManagementSiteSettings,
} from '@/utils/api'
import { composeFaqAnswer, parseFaqAnswer } from '@/utils/faqMeta'
import {
  defaultLoaderSettings,
  normalizeLoaderSettings,
  toLoaderWebSettingsPayload,
} from '@/utils/loaderSettings'
import { getManagementPageLayout, setManagementPageLayout } from '@/utils/pageLayoutApi'
import {
  clearSiteAuthoringDraft,
  loadSiteAuthoringDraft,
  readDraftPageLayout,
  writeDraftPageLayout,
  writeDraftSiteSettings,
  writeDraftThemeSettings,
} from '@/utils/siteAuthoringDraft'
import {
  applyThemeSettings,
  defaultThemeSettings,
  sanitizeThemeSettings,
  saveThemeSettingsToServer,
} from '@/utils/themeSettings'

const props = defineProps({
  entryMode: {
    type: String,
    default: '',
  },
})

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const statusText = ref('')
const activeStage = ref('identity')
const activeTab = ref('general')
const activeBuilderPage = ref('home')
const activeLayoutPanel = ref('builder')

const workflowStages = [
  { value: 'identity', label: 'هویت سایت', caption: 'برند، متن‌های پایه و Loader' },
  { value: 'theme', label: 'تم', caption: 'رنگ، هویت و ظاهر کلی' },
  { value: 'layout', label: 'چیدمان و کامپوننت‌ها', caption: 'ساختار صفحه و کنترل‌های بصری' },
  { value: 'content', label: 'محتوا', caption: 'متن، سوالات، اسلایدها و داده‌ها' },
  { value: 'review', label: 'بازبینی و انتشار', caption: 'بررسی draft و اعمال روی سایت' },
]

const tabStageMap = {
  general: 'identity',
  loader: 'identity',
  theme: 'theme',
  'page-builder': 'layout',
  content: 'content',
  review: 'review',
}

const stageTabMap = {
  identity: 'general',
  theme: 'theme',
  layout: 'page-builder',
  content: 'content',
  review: 'review',
}

const layoutPanelOptions = [
  { value: 'builder', label: 'ساختار صفحه', caption: 'بلاک‌ها، ترتیب و variantها' },
  { value: 'visual', label: 'کنترل‌های بصری', caption: 'ظاهر سکشن‌ها و کامپوننت‌های صفحه' },
]

const liveThemeSettings = ref({ ...defaultThemeSettings })
const themeDraft = ref({ ...defaultThemeSettings })
const liveSiteSettingsPayload = ref(null)
const livePageLayouts = ref({})
const draftRevision = ref(0)
const builderWorkspaceRevision = ref(0)

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
  hero_section_enabled: 0,
  footer_enabled: 1,
  header_variant: 'classic',
  menu_search_variant: 'search-card',
  hero_section_variant: 'off',
  footer_variant: 'full',
  hero_section_title: '',
  hero_section_description: '',
  hero_section_cta: '',
  hero_variant_contents: {},
  footer_description: '',
  footer_phone: '',
  footer_email: '',
  footer_address: '',
  footer_instagram: '',
  footer_telegram: '',
  footer_copyright: '',
  loader_enabled: defaultLoaderSettings.enabled,
  loader_mode: defaultLoaderSettings.mode,
  loader_preset: defaultLoaderSettings.preset,
  loader_title: defaultLoaderSettings.title,
  loader_subtitle: defaultLoaderSettings.subtitle,
  loader_min_duration_ms: defaultLoaderSettings.minDurationMs,
  loader_overlay_color: defaultLoaderSettings.overlayColor,
  loader_accent_color: defaultLoaderSettings.accentColor,
  loader_custom_code: defaultLoaderSettings.customCode,
  card_variant: 'classic',
  hero_image_position: 'center',
  category_rail_variant: 'pill',
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

const heroImageInput = ref(null)

const activeDesignPage = ref('global')
const activeDesignComponent = ref('header')
const previewDevice = ref('desktop')

const builderPageOptions = [
  { value: 'home', label: 'صفحه اصلی', subtitle: 'خانه و لندینگ اصلی' },
  { value: 'about', label: 'درباره ما', subtitle: 'داستان و معرفی برند' },
  { value: 'faq', label: 'سوالات متداول', subtitle: 'پرسش و پاسخ عمومی' },
  { value: 'product_groups', label: 'گروه‌های محصول', subtitle: 'ورودی منوی دسته‌بندی‌شده' },
]

const previewDeviceOptions = [
  { value: 'desktop', label: 'دسکتاپ' },
  { value: 'mobile', label: 'گوشی' },
]

const authoringPages = ['home', 'about', 'faq', 'product_groups']

function currentSiteSettingsPayload() {
  persistActiveHeroContent()
  const loaderPayload = toLoaderWebSettingsPayload(webSettings)

  return {
    web_settings: {
      brand_name: String(webSettings.brand_name || '').trim() || 'Veederakht Restaurant',
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
      header_variant: normalizeHeaderSetting(webSettings.header_variant),
      menu_search_variant: normalizeMenuSearchSetting(webSettings.menu_search_variant),
      hero_section_variant: String(webSettings.hero_section_variant || 'off').trim() || 'off',
      card_variant: String(webSettings.card_variant || 'classic').trim() || 'classic',
      hero_image_position: String(webSettings.hero_image_position || 'center').trim() || 'center',
      category_rail_variant: webSettings.category_rail_variant === 'image' ? 'image' : 'pill',
      footer_variant: String(webSettings.footer_variant || 'full').trim() || 'full',
      hero_section_enabled: webSettings.hero_section_variant !== 'off' ? 1 : 0,
      footer_enabled: webSettings.footer_variant !== 'off' ? 1 : 0,
      hero_section_title: String(webSettings.hero_section_title || '').trim(),
      hero_section_description: String(webSettings.hero_section_description || '').trim(),
      hero_section_cta: String(webSettings.hero_section_cta || '').trim(),
      hero_variant_contents: ensureHeroVariantContents(webSettings.hero_variant_contents),
      footer_description: String(webSettings.footer_description || '').trim(),
      footer_phone: String(webSettings.footer_phone || '').trim(),
      footer_email: String(webSettings.footer_email || '').trim(),
      footer_address: String(webSettings.footer_address || '').trim(),
      footer_instagram: String(webSettings.footer_instagram || '').trim(),
      footer_telegram: String(webSettings.footer_telegram || '').trim(),
      footer_copyright: String(webSettings.footer_copyright || '').trim(),
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
  }
}

function isEqual(left, right) {
  try {
    return JSON.stringify(left) === JSON.stringify(right)
  } catch (_) {
    return false
  }
}

function bumpDraftRevision() {
  draftRevision.value += 1
}

function bumpBuilderWorkspaceRevision() {
  builderWorkspaceRevision.value += 1
}

const currentThemeDraft = computed(() => sanitizeThemeSettings(themeDraft.value))
const currentSiteDraft = computed(() => currentSiteSettingsPayload())
const hasThemeDraftChanges = computed(() => !isEqual(currentThemeDraft.value, sanitizeThemeSettings(liveThemeSettings.value)))
const hasSiteDraftChanges = computed(() => !isEqual(currentSiteDraft.value, liveSiteSettingsPayload.value || {}))
const draftPageLayouts = computed(() =>
  {
    draftRevision.value
    return authoringPages.reduce((acc, page) => {
      const draft = readDraftPageLayout(page)
      if (draft?.blocks) {
        acc[page] = draft
      }
      return acc
    }, {})
  },
)
const changedLayoutPages = computed(() =>
  authoringPages.filter((page) => !isEqual(draftPageLayouts.value?.[page] || livePageLayouts.value?.[page] || { page, blocks: [] }, livePageLayouts.value?.[page] || { page, blocks: [] })),
)
const hasLayoutDraftChanges = computed(() => changedLayoutPages.value.length > 0)
const hasAnyDraftChanges = computed(() => hasThemeDraftChanges.value || hasSiteDraftChanges.value || hasLayoutDraftChanges.value)
const primaryActionLabel = computed(() => {
  if (saving.value) {
    return activeStage.value === 'review' ? 'در حال انتشار...' : 'در حال ذخیره...'
  }
  if (activeStage.value === 'review') {
    return 'انتشار روی سایت'
  }
  return 'ذخیره پیش‌نویس'
})
const secondaryActionLabel = computed(() => {
  if (activeStage.value === 'review') {
    return 'حذف پیش‌نویس‌ها'
  }
  return loading.value ? 'در حال بارگذاری...' : 'بازخوانی از سرور'
})
const primaryActionDisabled = computed(() => {
  if (loading.value || saving.value) {
    return true
  }
  if (activeStage.value === 'review') {
    return !hasAnyDraftChanges.value
  }
  return false
})
const secondaryActionDisabled = computed(() => {
  if (loading.value || saving.value) {
    return true
  }
  if (activeStage.value === 'review') {
    return !hasAnyDraftChanges.value
  }
  return false
})

const stageSaveHint = computed(() => {
  if (activeStage.value === 'theme') {
    return 'ذخیره این مرحله به‌صورت draft تم انجام می‌شود.'
  }
  if (activeStage.value === 'layout') {
    return 'ذخیره ساختار صفحه از داخل workspace انجام می‌شود.'
  }
  if (activeStage.value === 'review') {
    return 'در این مرحله draftهای ذخیره‌شده را منتشر می‌کنی.'
  }
  return ''
})

function normalizeStage(value = '') {
  const normalized = String(value || '').trim()
  return workflowStages.some((item) => item.value === normalized) ? normalized : 'identity'
}

function normalizeBuilderPage(value = '') {
  const normalized = String(value || '').trim()
  if (normalized === 'product-groups') {
    return 'product_groups'
  }
  return builderPageOptions.some((item) => item.value === normalized) ? normalized : 'home'
}

function syncSiteSettingsRoute() {
  if (typeof window === 'undefined' || !window.history?.replaceState) {
    return
  }

  const url = new URL(window.location.href)
  url.pathname = '/management/site-settings'

  url.searchParams.set('stage', activeStage.value)

  if (activeTab.value === 'loader') {
    url.searchParams.set('panel', 'loader')
  } else {
    url.searchParams.delete('panel')
  }

  if (['layout', 'content'].includes(activeStage.value)) {
    url.searchParams.set('page', activeBuilderPage.value === 'product_groups' ? 'product-groups' : activeBuilderPage.value)
  } else {
    url.searchParams.delete('page')
  }

  if (activeStage.value === 'layout') {
    url.searchParams.set('layout_panel', activeLayoutPanel.value)
  } else {
    url.searchParams.delete('layout_panel')
  }

  url.searchParams.delete('tab')

  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`)
}

function applyRouteState() {
  if (typeof window === 'undefined') {
    return
  }

  const params = new URLSearchParams(window.location.search || '')
  const legacyTab = String(params.get('tab') || '').trim()
  const requestedStage =
    props.entryMode === 'home-builder'
      ? 'layout'
      : props.entryMode === 'theme-settings'
        ? 'theme'
        : normalizeStage(params.get('stage') || tabStageMap[legacyTab] || '')
  const requestedPage = props.entryMode === 'home-builder' ? 'home' : String(params.get('page') || '').trim()
  const requestedPanel = String(params.get('panel') || '').trim()
  const requestedLayoutPanel = String(params.get('layout_panel') || '').trim()

  activeStage.value = requestedStage
  activeTab.value = stageTabMap[requestedStage] || 'general'
  if (requestedStage === 'identity' && (requestedPanel === 'loader' || legacyTab === 'loader')) {
    activeTab.value = 'loader'
  }
  activeLayoutPanel.value = requestedLayoutPanel === 'visual' ? 'visual' : 'builder'

  activeBuilderPage.value = normalizeBuilderPage(requestedPage)

  if (props.entryMode === 'home-builder' || props.entryMode === 'theme-settings') {
    syncSiteSettingsRoute()
  }
}

const heroContentDefaults = {
  off: {
    title: '',
    description: '',
    cta: '',
    image: '',
    imagePosition: 'center',
  },
  slider: {
    title: 'اسلایدر پیشنهادهای ویژه',
    description: 'اسلایدهای تصویری برای معرفی محصولات، کمپین‌ها یا پیشنهادهای روزانه.',
    cta: 'مشاهده پیشنهادها',
    image: '',
    imagePosition: 'center',
  },
  fullscreen: {
    title: 'غذای تازه با سفارش سریع',
    description: 'تجربه سفارش آنلاین با تصویر بزرگ، متن کوتاه و مسیر سریع ورود به منو.',
    cta: 'مشاهده منو',
    image: '',
    imagePosition: 'center',
  },
  banner: {
    title: 'پیشنهاد امروز رستوران',
    description: 'یک بنر کوتاه برای معرفی سریع پیشنهادها یا کمپین‌های روزانه.',
    cta: 'شروع سفارش',
    image: '',
    imagePosition: 'center',
  },
  cover: {
    title: 'سبک زندگی سالم، انتخاب هر روز ما',
    description: 'غذاهای سالم و متنوع با بهترین مواد اولیه تازه برای یک زندگی پرانرژی و متعادل.',
    cta: 'سفارش آنلاین',
    image: '',
    imagePosition: 'center',
  },
  foodbar: {
    title: 'محبوب‌ترین انتخاب‌های امروز',
    description: 'نمایش محصول‌محور برای غذاهای پرفروش همراه با تصویر بزرگ و کارت‌های انتخاب سریع.',
    cta: 'سفارش الان',
    image: '',
    imagePosition: 'center',
  },
}

const heroContentMeta = {
  slider: {
    title: 'محتوای اسلایدر هیرو',
    hint: 'برای هیرویی که محتوای اصلی‌اش از اسلایدهای تصویری می‌آید.',
    fields: ['title', 'description', 'cta'],
    usesSlides: true,
    titleLabel: 'عنوان کلی اسلایدر',
    titlePlaceholder: 'اسلایدر پیشنهادهای ویژه',
    descriptionLabel: 'توضیح کلی',
    descriptionPlaceholder: 'توضیح کوتاه قبل یا کنار اسلایدر...',
    ctaPlaceholder: 'مشاهده پیشنهادها',
    imageLabel: 'تصویر',
  },
  fullscreen: {
    title: 'محتوای هیرو تمام‌صفحه',
    hint: 'برای بنر بزرگ با پس‌زمینه تصویری.',
    fields: ['title', 'description', 'cta', 'image', 'imagePosition'],
    usesSlides: false,
    titleLabel: 'عنوان اصلی',
    titlePlaceholder: 'مثال: غذای تازه با سفارش سریع',
    descriptionLabel: 'توضیح کوتاه',
    descriptionPlaceholder: 'توضیحی که روی هیرو نمایش داده می‌شود...',
    ctaPlaceholder: 'مشاهده منو',
    imageLabel: 'تصویر پس‌زمینه',
  },
  banner: {
    title: 'محتوای بنر کوتاه',
    hint: 'برای پیام کوتاه، کمپین یا پیشنهاد روز.',
    fields: ['title', 'description', 'cta', 'image', 'imagePosition'],
    usesSlides: false,
    titleLabel: 'عنوان بنر',
    titlePlaceholder: 'مثال: پیشنهاد امروز رستوران',
    descriptionLabel: 'متن بنر',
    descriptionPlaceholder: 'متن کوتاه و مستقیم...',
    ctaPlaceholder: 'شروع سفارش',
    imageLabel: 'تصویر بنر',
  },
  cover: {
    title: 'محتوای کاور سالم',
    hint: 'برای هیروی روشن شبیه نمونه با عکس غذا و متن بزرگ.',
    fields: ['title', 'description', 'cta', 'image', 'imagePosition'],
    usesSlides: false,
    titleLabel: 'تیتر بزرگ کاور',
    titlePlaceholder: 'سبک زندگی سالم، انتخاب هر روز ما',
    descriptionLabel: 'متن زیر تیتر',
    descriptionPlaceholder: 'غذاهای سالم و متنوع با بهترین مواد اولیه...',
    ctaPlaceholder: 'سفارش آنلاین',
    imageLabel: 'عکس اصلی غذا',
  },
  foodbar: {
    title: 'محتوای فودبار محصولی',
    hint: 'متن کلی فودبار و آیتم‌های نمایشی از محصولات پرفروش می‌آیند.',
    fields: ['title', 'description', 'cta'],
    usesSlides: false,
    titleLabel: 'عنوان فودبار',
    titlePlaceholder: 'محبوب‌ترین انتخاب‌های امروز',
    descriptionLabel: 'توضیح فودبار',
    descriptionPlaceholder: 'معرفی کوتاه بخش محصول‌محور...',
    ctaPlaceholder: 'سفارش الان',
    imageLabel: 'تصویر محصول از لیست محصولات می‌آید',
  },
  off: {
    title: 'هیرو خاموش است',
    hint: 'برای ویرایش محتوا یک هیرو انتخاب کن.',
    fields: [],
    usesSlides: false,
    titleLabel: 'عنوان',
    titlePlaceholder: '',
    descriptionLabel: 'توضیحات',
    descriptionPlaceholder: '',
    ctaPlaceholder: '',
    imageLabel: 'تصویر',
  },
}

const activeHeroContentMeta = computed(() => {
  const variant = String(webSettings.hero_section_variant || 'off').trim() || 'off'
  return heroContentMeta[variant] || heroContentMeta.fullscreen
})

function normalizeHeroVariantContent(value = {}) {
  return {
    title: String(value?.title || '').trim(),
    description: String(value?.description || '').trim(),
    cta: String(value?.cta || '').trim(),
    image: String(value?.image || '').trim(),
    imagePosition: String(value?.imagePosition || 'center').trim() || 'center',
  }
}

function ensureHeroVariantContents(source = {}) {
  const next = {}
  for (const [variant, defaults] of Object.entries(heroContentDefaults)) {
    next[variant] = normalizeHeroVariantContent({ ...defaults, ...(source?.[variant] || {}) })
  }
  return next
}

function currentHeroVariant() {
  return String(webSettings.hero_section_variant || 'off').trim() || 'off'
}

function applyHeroContentToForm(variant = currentHeroVariant()) {
  const contents = ensureHeroVariantContents(webSettings.hero_variant_contents)
  webSettings.hero_variant_contents = contents
  const content = contents[variant] || contents.off
  webSettings.hero_section_title = content.title
  webSettings.hero_section_description = content.description
  webSettings.hero_section_cta = content.cta
  webSettings.hero_image = content.image
  webSettings.hero_image_position = content.imagePosition || 'center'
}

function persistActiveHeroContent(variant = currentHeroVariant()) {
  const contents = ensureHeroVariantContents(webSettings.hero_variant_contents)
  contents[variant] = normalizeHeroVariantContent({
    title: webSettings.hero_section_title,
    description: webSettings.hero_section_description,
    cta: webSettings.hero_section_cta,
    image: webSettings.hero_image,
    imagePosition: webSettings.hero_image_position,
  })
  webSettings.hero_variant_contents = contents
}


const componentRegistry = {
  header: { value: 'header', label: 'هدر', status: 'عمومی' },
  footer: { value: 'footer', label: 'فوتر', status: 'عمومی' },
  loader: { value: 'loader', label: 'Loader', status: 'تب جدا' },
  homeHero: { value: 'homeHero', label: 'هیرو و اسلایدر', status: 'صفحه اصلی' },
  menuSearch: { value: 'menuSearch', label: 'سرچ منو', status: 'صفحه اصلی' },
  featuredBlock: { value: 'featuredBlock', label: 'ویژه و پرفروش', status: 'صفحه اصلی' },
  categoryRail: { value: 'categoryRail', label: 'دسته‌بندی‌ها', status: 'صفحه اصلی' },
  productCard: { value: 'productCard', label: 'کارت محصول', status: 'مشترک' },
  aboutShell: { value: 'aboutShell', label: 'پوسته درباره ما', status: 'درباره ما' },
  faqShell: { value: 'faqShell', label: 'پوسته FAQ', status: 'سوالات متداول' },
  groupsShell: { value: 'groupsShell', label: 'پوسته گروه‌ها', status: 'گروه‌های محصول' },
  aboutSections: { value: 'aboutSections', label: 'محتوای درباره ما', status: 'درباره ما' },
  faqItems: { value: 'faqItems', label: 'سوالات متداول', status: 'FAQ' },
}

const designPages = [
  { value: 'global', label: 'عمومی', components: ['header', 'footer'] },
  { value: 'home', label: 'صفحه اصلی', components: ['homeHero', 'menuSearch', 'featuredBlock', 'categoryRail', 'productCard'] },
  { value: 'about', label: 'درباره ما', components: ['aboutShell'] },
  { value: 'faq', label: 'سوالات متداول', components: ['faqShell'] },
  { value: 'product_groups', label: 'گروه‌های محصول', components: ['groupsShell'] },
  { value: 'product', label: 'جزئیات محصول', components: ['productCard'] },
].map((pageItem) => ({ ...pageItem, count: pageItem.components.length }))

const currentDesignPage = computed(() => designPages.find((pageItem) => pageItem.value === activeDesignPage.value) || designPages[0])
const currentDesignComponents = computed(() => {
  const globalComponents = designPages.find((pageItem) => pageItem.value === 'global')?.components || []
  const pageComponents = currentDesignPage.value.value === 'global' ? [] : currentDesignPage.value.components
  const keys = [...globalComponents, ...pageComponents]
  return keys.map((key) => componentRegistry[key]).filter(Boolean)
})
const currentDesignComponent = computed(() => componentRegistry[activeDesignComponent.value] || currentDesignComponents.value[0])

function selectDesignPage(value) {
  const nextPage = designPages.find((pageItem) => pageItem.value === value) || designPages[0]
  activeDesignPage.value = nextPage.value
  if (!nextPage.components.includes(activeDesignComponent.value)) {
    activeDesignComponent.value = nextPage.components[0]
  }
}

function selectDesignComponent(value) {
  activeDesignComponent.value = value
}

watch(
  () => webSettings.hero_section_variant,
  (nextVariant, previousVariant) => {
    if (previousVariant) {
      persistActiveHeroContent(previousVariant)
    }
    applyHeroContentToForm(nextVariant)
  },
)

watch(
  () => [
    webSettings.hero_section_title,
    webSettings.hero_section_description,
    webSettings.hero_section_cta,
    webSettings.hero_image,
    webSettings.hero_image_position,
  ],
  () => {
    persistActiveHeroContent()
  },
)

watch(
  () => activeStage.value,
  (nextStage) => {
    const mappedTab = stageTabMap[nextStage] || 'general'
    if (nextStage === 'identity') {
      if (!['general', 'loader'].includes(activeTab.value)) {
        activeTab.value = 'general'
      }
      return
    }
    if (activeTab.value !== mappedTab) {
      activeTab.value = mappedTab
    }
  },
)

watch(
  () => activeTab.value,
  (nextTab) => {
    const mappedStage = tabStageMap[nextTab] || 'identity'
    if (activeStage.value !== mappedStage) {
      activeStage.value = mappedStage
    }
  },
)

watch(
  () => [activeStage.value, activeTab.value, activeBuilderPage.value, activeLayoutPanel.value],
  () => {
    syncSiteSettingsRoute()
  },
)

watch(
  () => activeBuilderPage.value,
  (page) => {
    selectDesignPage(page)
  },
  { immediate: true },
)

function handleHeroImageUpload(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    webSettings.hero_image = String(e.target?.result || '').trim()
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

const currencyOptions = [
  { value: 'IRR', label: 'IRR' },
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
]

const imagePositionOptions = [
  { value: 'top', label: 'بالا' },
  { value: 'center', label: 'وسط' },
  { value: 'bottom', label: 'پایین' },
]

const cardVariantOptions = [
  {
    value: 'classic',
    label: 'کارت کلاسیک',
    desc: 'کارت سفید با تصویر بالا، بج قیمت، دسته‌بندی، توضیح و دکمه مشاهده',
    previewStyle: { background: '#f5f0eb' },
    cardStyle: { background: '#fff', border: '1px solid #e0d8cf', borderRadius: '14px', height: '80%' },
  },
  {
    value: 'dark',
    label: 'کارت تاریک',
    desc: 'کارت با تصویر پوشش‌دهنده، افکت تاریک و متن سفید روی آن',
    previewStyle: { background: '#1c1411' },
    cardStyle: { background: 'linear-gradient(135deg, #2d1a10, #1c1411)', borderRadius: '14px', height: '80%' },
  },
  {
    value: 'navy',
    label: 'کارت نیوی',
    desc: 'کارت تیره با تصویر مرکزی، ستاره‌بندی، قیمت بزرگ و دکمه فلش',
    previewStyle: { background: '#1e2035' },
    cardStyle: { background: 'linear-gradient(145deg, rgba(111,74,49,0.7), rgba(30,32,53,0.9))', borderRadius: '14px', height: '80%' },
  },
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

const headerVariantOptions = [
  {
    value: 'classic',
    label: 'هدر کارتی',
    desc: 'هدر اصلی سایت با برند، ناوبری، سبد و ورود مدیریت؛ همان نوار بالای سایت',
    previewStyle: { background: '#f5f0eb' },
    barStyle: { background: '#fff', border: '1px solid #e0d8cf', borderRadius: '12px', boxShadow: '0 8px 18px rgba(76,33,45,0.08)' },
  },
  {
    value: 'minimal',
    label: 'مینیمال تاریک',
    desc: 'هدر تاریک و مدرن با پس‌زمینه یکدست قهوه‌ای تیره',
    previewStyle: { background: '#1c1411' },
    barStyle: { background: '#1c1411', borderBottom: '1px solid rgba(255,255,255,0.08)' },
  },
  {
    value: 'glass',
    label: 'شیشه‌ای (Glass)',
    desc: 'هدر شفاف با افکت شیشه‌ای و بلور مدرن؛ روی هر پس‌زمینه‌ای زیبا به نظر می‌رسد',
    previewStyle: { background: 'linear-gradient(135deg, #f0ece7, #e8e0d8)' },
    barStyle: { background: 'rgba(255,255,255,0.72)', borderBottom: '1px solid rgba(111,74,49,0.12)', backdropFilter: 'blur(18px)' },
  },
]

const menuSearchVariantOptions = [
  {
    value: 'search-card',
    label: 'کارت سرچ کامل',
    desc: 'کامپوننت جداگانه برای جستجو در منو، با عنوان برند، input جستجو و دکمه سبد',
    previewStyle: { background: '#f0ece7', padding: '8px' },
    searchStyle: { background: '#fff', border: '1px solid #e0d8cf', borderRadius: '14px', padding: '12px' },
  },
  {
    value: 'off',
    label: 'خاموش',
    desc: 'کارت سرچ نمایش داده نمی‌شود و فقط دسته‌بندی‌ها/محتوا باقی می‌ماند',
    previewStyle: { background: '#f0ece7' },
    searchStyle: { background: 'repeating-linear-gradient(45deg, #e0d8cf 0, #e0d8cf 1px, transparent 0, transparent 50%) 0 0 / 8px 8px', height: '100%' },
  },
]

const heroVariantOptions = [
  {
    value: 'off',
    label: 'بدون هیرو',
    desc: 'هیرو سکشن نمایش داده نمی‌شود',
    previewStyle: { background: '#f0ece7' },
    heroStyle: { background: 'repeating-linear-gradient(45deg, #e0d8cf 0, #e0d8cf 1px, transparent 0, transparent 50%) 0 0 / 8px 8px', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
  {
    value: 'slider',
    label: 'اسلایدر هیرو',
    desc: 'هیرو مخصوص اسلایدها؛ هر اسلاید تصویر، عنوان، لینک و CTA خودش را دارد',
    previewStyle: { background: '#f0ece7' },
    heroStyle: { background: 'linear-gradient(135deg, #fff, #e7d8c8)', height: '100%' },
  },
  {
    value: 'fullscreen',
    label: 'تمام‌صفحه',
    desc: 'بنر بزرگ تمام صفحه با تصویر پس‌زمینه و هدر شفاف روی آن',
    previewStyle: { background: '#2a1a10' },
    heroStyle: { background: 'linear-gradient(135deg, #1c1411, #3d2510)', height: '100%' },
  },
  {
    value: 'banner',
    label: 'بنر کوتاه',
    desc: 'بنر افقی جمع‌وجور با ارتفاع کمتر، مناسب برای صفحات مینیمال',
    previewStyle: { background: '#1c1411' },
    heroStyle: { background: 'linear-gradient(135deg, #1c1411 60%, #3d2510)', height: '60%', marginTop: '20%' },
  },
  {
    value: 'cover',
    label: 'کاور سالم',
    desc: 'هیرو روشن شبیه تصویر نمونه؛ عکس غذا، متن بزرگ، دکمه‌ها و مزیت‌ها',
    previewStyle: { background: '#f7efe4' },
    heroStyle: { background: 'linear-gradient(135deg, #fff7ed 45%, #f0dfca)', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
  {
    value: 'foodbar',
    label: 'فودبار محصولی',
    desc: 'هیرو محصول‌محور با تصویر بزرگ و تمرکز روی آیتم‌های پرفروش',
    previewStyle: { background: '#1c1411' },
    heroStyle: { background: 'linear-gradient(180deg, #1c1411 40%, #fff 40%)', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
]

const footerVariantOptions = [
  {
    value: 'off',
    label: 'بدون فوتر',
    desc: 'فوتر نمایش داده نمی‌شود',
    previewStyle: { background: '#f0ece7' },
    footerStyle: { background: 'repeating-linear-gradient(45deg, #e0d8cf 0, #e0d8cf 1px, transparent 0, transparent 50%) 0 0 / 8px 8px', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
  {
    value: 'full',
    label: 'فوتر کامل',
    desc: 'فوتر کامل با نام برند، اطلاعات تماس، لینک‌های اجتماعی و کپی‌رایت',
    previewStyle: { background: '#1c1411' },
    footerStyle: { background: '#1c1411', height: '100%' },
  },
  {
    value: 'minimal',
    label: 'فوتر مینیمال',
    desc: 'فوتر ساده و کوچک فقط با نام برند و کپی‌رایت',
    previewStyle: { background: '#f5f0eb' },
    footerStyle: { background: '#f5f0eb', borderTop: '1px solid #e0d8cf', height: '45%', marginTop: '55%' },
  },
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

function normalizeHeaderSetting(value = '') {
  const v = String(value || '').trim()
  const valid = ['classic', 'minimal', 'hero', 'glass']
  return valid.includes(v) ? v : 'classic'
}

function normalizeMenuSearchSetting(value = '') {
  return String(value || '').trim() === 'off' ? 'off' : 'search-card'
}

function syncBootFromWebSettings(payload = {}) {
  if (typeof window === 'undefined') {
    return
  }

  const target = window._BOOT || {}
  const nextWeb = deepCopy(payload?.web_settings || {})
  const currentBranding = deepCopy(target.branding || {})
  const nextBranding = {
    ...currentBranding,
    name: String(nextWeb.brand_name || currentBranding.name || 'Veederakht Restaurant').trim() || 'Veederakht Restaurant',
    tagline: String(nextWeb.brand_tagline || currentBranding.tagline || '').trim(),
    hero_title: String(nextWeb.hero_title || currentBranding.hero_title || '').trim(),
    hero_subtitle: String(nextWeb.hero_subtitle || currentBranding.hero_subtitle || '').trim(),
    primary_cta_label: String(nextWeb.primary_cta_label || currentBranding.primary_cta_label || '').trim(),
    hero_image: String(nextWeb.hero_image || currentBranding.hero_image || '').trim(),
    header_variant: normalizeHeaderSetting(nextWeb.header_variant || currentBranding.header_variant),
    menu_search_variant: normalizeMenuSearchSetting(nextWeb.menu_search_variant || currentBranding.menu_search_variant),
    hero_section_variant: String(nextWeb.hero_section_variant || currentBranding.hero_section_variant || 'off').trim() || 'off',
    footer_variant: String(nextWeb.footer_variant || currentBranding.footer_variant || 'full').trim() || 'full',
    card_variant: String(nextWeb.card_variant || currentBranding.card_variant || 'classic').trim() || 'classic',
    hero_section_title: String(nextWeb.hero_section_title || currentBranding.hero_section_title || '').trim(),
    hero_section_description: String(nextWeb.hero_section_description || currentBranding.hero_section_description || '').trim(),
    hero_section_cta: String(nextWeb.hero_section_cta || currentBranding.hero_section_cta || '').trim(),
    hero_variant_contents: ensureHeroVariantContents(nextWeb.hero_variant_contents || currentBranding.hero_variant_contents || {}),
    footer_description: String(nextWeb.footer_description || currentBranding.footer_description || '').trim(),
    footer_phone: String(nextWeb.footer_phone || currentBranding.footer_phone || '').trim(),
    footer_email: String(nextWeb.footer_email || currentBranding.footer_email || '').trim(),
    footer_address: String(nextWeb.footer_address || currentBranding.footer_address || '').trim(),
    footer_instagram: String(nextWeb.footer_instagram || currentBranding.footer_instagram || '').trim(),
    footer_telegram: String(nextWeb.footer_telegram || currentBranding.footer_telegram || '').trim(),
    footer_copyright: String(nextWeb.footer_copyright || currentBranding.footer_copyright || '').trim(),
  }

  target.web_settings = {
    ...(target.web_settings || {}),
    ...nextWeb,
  }
  target.branding = nextBranding
  target.currency = String(nextWeb.default_currency || target.currency || 'IRR').trim() || 'IRR'

  if (Array.isArray(payload?.hero_slides)) {
    target.hero_slides = deepCopy(payload.hero_slides)
  }
  if (Array.isArray(payload?.about_sections)) {
    target.about_us_sections = deepCopy(payload.about_sections)
  }
  if (Array.isArray(payload?.faq_items)) {
    target.faq_items = deepCopy(payload.faq_items)
  }

  // Sync loader_settings from payload or web_settings
  if (payload?.loader_settings && typeof payload.loader_settings === 'object') {
    target.loader_settings = {
      ...(target.loader_settings || {}),
      ...payload.loader_settings,
    }
  } else {
    // Fallback: extract loader fields from web_settings
    const loaderKeys = [
      'loader_enabled', 'loader_mode', 'loader_preset', 'loader_title',
      'loader_subtitle', 'loader_min_duration_ms', 'loader_overlay_color',
      'loader_accent_color', 'loader_custom_code',
    ]
    const nextLoader = {}
    for (const key of loaderKeys) {
      if (key in nextWeb) {
        nextLoader[key] = nextWeb[key]
      }
    }
    if (Object.keys(nextLoader).length > 0) {
      target.loader_settings = {
        ...(target.loader_settings || {}),
        ...nextLoader,
      }
    }
  }

  window._BOOT = target

  if (typeof window.dispatchEvent === 'function') {
    window.dispatchEvent(
      new CustomEvent('restaurant-site-settings-updated', {
        detail: deepCopy(payload),
      }),
    )
  }
}

async function loadLiveThemeSettings() {
  try {
    const remote = await getManagementThemeSettings()
    liveThemeSettings.value = sanitizeThemeSettings(remote)
  } catch (_) {
    liveThemeSettings.value = sanitizeThemeSettings(defaultThemeSettings)
  }
}

async function loadLivePageLayouts() {
  const entries = await Promise.all(
    authoringPages.map(async (page) => {
      try {
        const result = await getManagementPageLayout(page)
        return [page, result || { page, blocks: [] }]
      } catch (_) {
        return [page, { page, blocks: [] }]
      }
    }),
  )
  livePageLayouts.value = Object.fromEntries(entries)
}

function applyDraftOverlay() {
  const draft = loadSiteAuthoringDraft()

  themeDraft.value = sanitizeThemeSettings(draft.theme_settings || liveThemeSettings.value || defaultThemeSettings)

  if (draft.site_settings && typeof draft.site_settings === 'object') {
    const payload = deepCopy(draft.site_settings)
    const nextWeb = payload.web_settings || {}
    Object.assign(webSettings, {
      ...webSettings,
      ...nextWeb,
    })
    webSettings.header_variant = normalizeHeaderSetting(nextWeb.header_variant)
    webSettings.menu_search_variant = normalizeMenuSearchSetting(nextWeb.menu_search_variant)
    webSettings.hero_variant_contents = ensureHeroVariantContents(nextWeb.hero_variant_contents || {})
    webSettings.hero_section_variant = String(nextWeb.hero_section_variant || webSettings.hero_section_variant || 'off').trim() || 'off'
    webSettings.footer_variant = String(nextWeb.footer_variant || webSettings.footer_variant || 'full').trim() || 'full'
    webSettings.card_variant = String(nextWeb.card_variant || webSettings.card_variant || 'classic').trim() || 'classic'
    webSettings.category_rail_variant = nextWeb.category_rail_variant === 'image' ? 'image' : 'pill'
    applyHeroContentToForm()
    assignLoaderSettingsToForm(nextWeb)
    heroSlides.value = (payload.hero_slides || []).map((row) => normalizeHeroSlide(row))
    aboutSections.value = (payload.about_sections || []).map((row) => normalizeAboutSection(row))
    faqItems.value = (payload.faq_items || []).map((row) => normalizeFaqItem(row))
    syncBootFromWebSettings(payload)
  }

  applyThemeSettings(themeDraft.value)
}

function saveThemeDraft(settings) {
  themeDraft.value = sanitizeThemeSettings(settings)
  writeDraftThemeSettings(themeDraft.value)
  bumpDraftRevision()
  applyThemeSettings(themeDraft.value)
  statusText.value = 'پیش‌نویس تم ذخیره شد.'
}

function resetThemeDraft(settings) {
  themeDraft.value = sanitizeThemeSettings(settings)
  writeDraftThemeSettings(themeDraft.value)
  bumpDraftRevision()
  applyThemeSettings(themeDraft.value)
  statusText.value = 'پیش‌نویس تم به پیش‌فرض برگشت.'
}

function saveSiteDraft() {
  const payload = currentSiteDraft.value
  writeDraftSiteSettings(payload)
  bumpDraftRevision()
  statusText.value = 'پیش‌نویس این مرحله ذخیره شد.'
  syncBootFromWebSettings(payload)
}

async function loadDraftPageLayout(page, { forceServer = false } = {}) {
  const pageKey = String(page || 'home').trim() || 'home'
  if (!forceServer) {
    const draft = readDraftPageLayout(pageKey)
    if (draft?.blocks) {
      return draft
    }
  }
  const live = livePageLayouts.value?.[pageKey]
  if (live?.blocks) {
    return live
  }
  return getManagementPageLayout(pageKey)
}

async function saveDraftPageLayout(page, blocks) {
  const pageKey = String(page || 'home').trim() || 'home'
  const result = {
    page: pageKey,
    blocks,
    company: String(livePageLayouts.value?.[pageKey]?.company || '').trim(),
  }
  writeDraftPageLayout(pageKey, result)
  bumpDraftRevision()
  statusText.value = 'پیش‌نویس چیدمان ذخیره شد.'
  return result
}

async function discardAllDrafts() {
  clearSiteAuthoringDraft()
  bumpDraftRevision()
  bumpBuilderWorkspaceRevision()
  await loadSettings()
  statusText.value = 'همه پیش‌نویس‌ها حذف شدند.'
}

async function publishAllDrafts() {
  saving.value = true
  error.value = ''
  statusText.value = ''

  try {
    await saveThemeSettingsToServer(currentThemeDraft.value)
    const sitePayload = await setManagementSiteSettings(currentSiteDraft.value)
    for (const page of authoringPages) {
      const draft = draftPageLayouts.value?.[page]
      if (draft?.blocks) {
        await setManagementPageLayout({ page, blocks: draft.blocks })
      }
    }
    clearSiteAuthoringDraft()
    bumpDraftRevision()
    bumpBuilderWorkspaceRevision()
    liveSiteSettingsPayload.value = deepCopy(sitePayload)
    syncBootFromWebSettings(sitePayload)
    await loadLiveThemeSettings()
    await loadLivePageLayouts()
    applyDraftOverlay()
    statusText.value = 'تغییرات سایت منتشر شد.'
  } catch (publishError) {
    error.value = publishError.message || 'انتشار تغییرات ناموفق بود.'
  } finally {
    saving.value = false
  }
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

const previewBranding = computed(() => ({
  name: String(webSettings.brand_name || 'Veederakht Restaurant').trim() || 'Veederakht Restaurant',
  tagline: String(webSettings.brand_tagline || '').trim(),
  hero_title: String(webSettings.hero_title || '').trim(),
  hero_subtitle: String(webSettings.hero_subtitle || '').trim(),
  primary_cta_label: String(webSettings.primary_cta_label || 'ورود به منو').trim() || 'ورود به منو',
  hero_image: String(webSettings.hero_image || '').trim(),
  hero_section_title: String(webSettings.hero_section_title || '').trim(),
  hero_section_description: String(webSettings.hero_section_description || '').trim(),
  hero_section_cta: String(webSettings.hero_section_cta || '').trim(),
  hero_variant_contents: ensureHeroVariantContents(webSettings.hero_variant_contents),
  footer_description: String(webSettings.footer_description || '').trim(),
  footer_phone: String(webSettings.footer_phone || '').trim(),
  footer_email: String(webSettings.footer_email || '').trim(),
  footer_address: String(webSettings.footer_address || '').trim(),
  footer_instagram: String(webSettings.footer_instagram || '').trim(),
  footer_telegram: String(webSettings.footer_telegram || '').trim(),
  footer_copyright: String(webSettings.footer_copyright || '').trim(),
}))

const builderBoot = computed(() => {
  const baseBoot = typeof window !== 'undefined' && window._BOOT ? window._BOOT : {}
  return {
    ...baseBoot,
    web_settings: {
      ...(baseBoot.web_settings || {}),
      ...deepCopy(webSettings),
    },
    branding: previewBranding.value,
    hero_slides: deepCopy(heroSlides.value),
    about_us_sections: deepCopy(aboutSections.value),
    faq_items: deepCopy(faqItems.value),
    currency: String(webSettings.default_currency || baseBoot.currency || 'IRR').trim() || 'IRR',
    page_layout: {
      ...(baseBoot.page_layout || {}),
    },
  }
})

const builderGroupsCount = computed(() => {
  const rows = Array.isArray(builderBoot.value?.categories) ? builderBoot.value.categories : []
  return rows.length
})

const previewCardItem = computed(() => ({
  title: 'پیتزا پپرونی',
  short_desc: 'پیتزا با پپرونی تازه و پنیر موزارلا خوشمزه',
  category_title: 'غذای اصلی',
  base_price: 280000,
  image: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=60',
  slug: 'sample-item',
  item_code: 'SAMPLE-001',
  tags: ['پرفروش', 'پپرونی'],
  restaurant_enabled: 1,
}))


const aboutPreviewSection = computed(() => aboutSections.value.find((row) => Number(row?.is_active || 0) === 1) || aboutSections.value[0] || {})
const aboutPreviewTitle = computed(() => String(aboutPreviewSection.value.title || 'داستان ما').trim())
const aboutPreviewText = computed(() => String(aboutPreviewSection.value.body_text || aboutPreviewSection.value.subtitle || 'محتوای صفحه درباره ما اینجا نمایش داده می‌شود.').trim())

const previewHeroTitle = computed(() => String(webSettings.hero_section_title || previewBranding.value.hero_title || '').trim())
const previewHeroDescription = computed(() => String(webSettings.hero_section_description || previewBranding.value.hero_subtitle || '').trim())
const previewHeroCta = computed(() => String(webSettings.hero_section_cta || previewBranding.value.primary_cta_label || 'مشاهده منو').trim() || 'مشاهده منو')
const previewHeroImage = computed(() => String(webSettings.hero_image || previewBranding.value.hero_image || '').trim())
const heroSlidesPreviewItem = computed(() => heroSlides.value.find((row) => Number(row?.is_active || 0) === 1) || heroSlides.value[0] || {})
const heroSlidesPreviewTitle = computed(() => String(heroSlidesPreviewItem.value.title || 'اسلاید ویژه').trim())
const heroSlidesPreviewImage = computed(() => String(heroSlidesPreviewItem.value.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=70').trim())

const heroPreviewComponent = computed(() => {
  if (String(webSettings.hero_section_variant || 'off').trim() === 'fullscreen') {
    return SiteHeroSection
  }
  if (String(webSettings.hero_section_variant || 'off').trim() === 'banner') {
    return SiteHeroBanner
  }
  return null
})

const heroPreviewProps = computed(() => {
  const base = {
    branding: previewBranding.value,
    title: previewHeroTitle.value,
    description: previewHeroDescription.value,
    cta: previewHeroCta.value,
    heroImage: previewHeroImage.value,
  }
  if (heroPreviewComponent.value === SiteHeroSection) {
    return {
      ...base,
      categories: [],
    }
  }
  return base
})

const footerPreviewComponent = computed(() => {
  if (String(webSettings.footer_variant || 'off').trim() === 'full') {
    return SiteFooter
  }
  if (String(webSettings.footer_variant || 'off').trim() === 'minimal') {
    return SiteFooterMinimal
  }
  return null
})

const footerPreviewProps = computed(() => {
  if (footerPreviewComponent.value === SiteFooter) {
    return {
      brandName: previewBranding.value.name,
      description: previewBranding.value.footer_description || previewBranding.value.hero_subtitle,
      phone: previewBranding.value.footer_phone,
      email: previewBranding.value.footer_email,
      address: previewBranding.value.footer_address,
      instagram: previewBranding.value.footer_instagram,
      telegram: previewBranding.value.footer_telegram,
      copyright: previewBranding.value.footer_copyright,
    }
  }

  return {
    brandName: previewBranding.value.name,
    copyright: previewBranding.value.footer_copyright,
  }
})

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
    liveSiteSettingsPayload.value = deepCopy(payload)
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
    webSettings.hero_section_enabled = Number(nextWeb.hero_section_enabled || 0) ? 1 : 0
    webSettings.footer_enabled = Number(nextWeb.footer_enabled ?? 1) ? 1 : 0
    webSettings.header_variant = normalizeHeaderSetting(nextWeb.header_variant)
    webSettings.menu_search_variant = normalizeMenuSearchSetting(nextWeb.menu_search_variant)
    const heroEnabled = Number(nextWeb.hero_section_enabled || 0)
    webSettings.hero_section_variant = String(nextWeb.hero_section_variant || (heroEnabled ? 'fullscreen' : 'off')).trim() || 'off'
    webSettings.hero_variant_contents = ensureHeroVariantContents(nextWeb.hero_variant_contents || {})
    const footerEnabled = Number(nextWeb.footer_enabled ?? 1)
    webSettings.footer_variant = String(nextWeb.footer_variant || (footerEnabled ? 'full' : 'off')).trim() || 'full'
    if (nextWeb.hero_section_title || nextWeb.hero_section_description || nextWeb.hero_section_cta || nextWeb.hero_image) {
      const variant = currentHeroVariant()
      const contents = ensureHeroVariantContents(webSettings.hero_variant_contents)
      contents[variant] = normalizeHeroVariantContent({
        ...contents[variant],
        title: nextWeb.hero_section_title,
        description: nextWeb.hero_section_description,
        cta: nextWeb.hero_section_cta,
        image: nextWeb.hero_image,
        imagePosition: nextWeb.hero_image_position,
      })
      webSettings.hero_variant_contents = contents
    }
    applyHeroContentToForm()
    webSettings.footer_description = String(nextWeb.footer_description || '').trim()
    webSettings.footer_phone = String(nextWeb.footer_phone || '').trim()
    webSettings.footer_email = String(nextWeb.footer_email || '').trim()
    webSettings.footer_address = String(nextWeb.footer_address || '').trim()
    webSettings.footer_instagram = String(nextWeb.footer_instagram || '').trim()
    webSettings.footer_telegram = String(nextWeb.footer_telegram || '').trim()
    webSettings.footer_copyright = String(nextWeb.footer_copyright || '').trim()
    webSettings.card_variant = String(nextWeb.card_variant || 'classic').trim() || 'classic'
    webSettings.hero_image_position = String(nextWeb.hero_image_position || 'center').trim() || 'center'
    webSettings.category_rail_variant = nextWeb.category_rail_variant === 'image' ? 'image' : 'pill'
    assignLoaderSettingsToForm(nextWeb)

    heroSlides.value = (payload?.hero_slides || []).map((row) => normalizeHeroSlide(row))
    aboutSections.value = (payload?.about_sections || []).map((row) => normalizeAboutSection(row))
    faqItems.value = (payload?.faq_items || []).map((row) => normalizeFaqItem(row))
    aboutEditorOpen.value = false
    faqEditorOpen.value = false
    syncBootFromWebSettings(payload)
    await loadLiveThemeSettings()
    await loadLivePageLayouts()
    applyDraftOverlay()
    bumpBuilderWorkspaceRevision()
    statusText.value = 'تنظیمات سایت بارگذاری شد.'
  } catch (loadError) {
    error.value = loadError.message || 'بارگذاری تنظیمات سایت ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function validateSiteDraft() {
  persistActiveHeroContent()
  const loaderPayload = toLoaderWebSettingsPayload(webSettings)
  if (loaderPayload.loader_enabled && loaderPayload.loader_mode === 'custom' && !String(loaderPayload.loader_custom_code || '').trim()) {
    throw new Error('برای حالت کد اختصاصی، لطفا کد Loader را وارد کنید.')
  }
}

async function handleSecondaryAction() {
  if (activeStage.value === 'review') {
    await discardAllDrafts()
    return
  }
  await loadSettings()
}

async function saveSettings() {
  error.value = ''
  statusText.value = ''

  try {
    if (activeStage.value === 'review') {
      await publishAllDrafts()
      return
    }
    saving.value = true
    validateSiteDraft()
    saveSiteDraft()
  } catch (saveError) {
    error.value = saveError.message || 'ذخیره تنظیمات سایت ناموفق بود.'
  } finally {
    if (activeStage.value !== 'review') {
      saving.value = false
    }
  }
}

applyRouteState()
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

.workflow-stages {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.6rem;
}

.workflow-stage {
  display: grid;
  gap: 0.22rem;
  text-align: right;
  padding: 0.8rem 0.9rem;
  border-radius: 16px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  background: #fff;
  cursor: pointer;
  font: inherit;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.workflow-stage strong {
  font-size: 0.88rem;
}

.workflow-stage small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.workflow-stage.active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.42);
  box-shadow: 0 14px 30px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  transform: translateY(-1px);
}

.context-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
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

.designer-shell {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.35fr);
  gap: 0.9rem;
  align-items: start;
}

.designer-preview {
  position: sticky;
  top: 0.8rem;
}

.preview-frame {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 24px;
  background: rgb(255 255 255 / 0.86);
  box-shadow: 0 18px 45px rgb(15 23 42 / 0.08);
  overflow: hidden;
}

.preview-topbar {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  background: rgb(var(--palette-eggshell-rgb) / 0.55);
}

.preview-topbar span {
  font-weight: 900;
  color: var(--ink-900, #1c1411);
}

.preview-topbar small {
  color: var(--text-muted, #786b61);
}

.preview-topbar > div:first-child {
  display: grid;
  gap: 0.1rem;
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
  height: 620px;
  overflow: auto;
  background: linear-gradient(145deg, rgb(var(--palette-eggshell-rgb) / 0.65), #fff);
}

.preview-stage--mobile {
  height: 720px;
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
  transform: scale(0.31);
}

.preview-viewport--mobile {
  width: 390px;
  min-height: 900px;
  transform: scale(0.88);
  transform-origin: top center;
  border-radius: 34px;
  overflow: hidden;
  box-shadow: 0 18px 45px rgb(15 23 42 / 0.16);
  margin-top: 0.8rem;
}

.compact-preview {
  padding: 0;
  max-height: none;
  overflow: visible;
}

.designer-panel {
  display: grid;
  gap: 0.75rem;
}

.page-switcher,
.component-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.page-switcher--subtle {
  margin-top: 0.75rem;
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
  transition: border-color 0.18s, background 0.18s, box-shadow 0.18s;
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

.review-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.review-summary-card,
.review-page-item {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 16px;
  background: #fff;
  padding: 0.9rem;
  display: grid;
  gap: 0.3rem;
}

.review-summary-card.changed,
.review-page-item.changed {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.38);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.review-summary-card strong,
.review-page-item strong {
  font-size: 0.9rem;
}

.review-summary-card small,
.review-page-item small {
  color: var(--text-muted, #786b61);
}

.review-page-list {
  display: grid;
  gap: 0.65rem;
}

.review-page-item {
  grid-template-columns: 1fr auto;
  align-items: center;
}

.inline-editor {
  margin-top: 0.85rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.hero-editor-head {
  display: grid;
  gap: 0.18rem;
  margin-bottom: 0.75rem;
}

.hero-editor-head strong {
  color: var(--ink-900, #1c1411);
  font-size: 0.92rem;
}

.hero-editor-head small {
  color: var(--text-muted, #786b61);
  line-height: 1.7;
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

.about-preview-card small,
.faq-preview-card span {
  color: var(--text-muted, #786b61);
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

.compact-card-preview {
  padding: 0;
}

.slider-hero-preview {
  min-height: 560px;
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #fffaf2, #efe0cf);
  color: #174d32;
}

.slider-hero-copy {
  display: grid;
  gap: 0.8rem;
}

.slider-hero-copy span {
  width: max-content;
  border-radius: 999px;
  padding: 0.36rem 0.78rem;
  background: rgb(23 77 50 / 0.08);
  font-weight: 900;
}

.slider-hero-copy h2 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 4rem);
  line-height: 1.15;
}

.slider-hero-copy p {
  margin: 0;
  color: rgb(28 20 17 / 0.65);
  line-height: 1.9;
}

.slider-hero-card {
  position: relative;
  min-height: 360px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 22px 64px rgb(72 44 18 / 0.18);
}

.slider-hero-card img {
  width: 100%;
  height: 100%;
  min-height: 360px;
  object-fit: cover;
  display: block;
}

.slider-hero-card strong {
  position: absolute;
  right: 1rem;
  bottom: 1rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.82);
  padding: 0.55rem 0.9rem;
}

.preview-viewport--mobile .slider-hero-preview {
  min-height: 620px;
  grid-template-columns: 1fr;
  padding: 1.1rem;
  border-radius: 0;
}

.preview-viewport--mobile .slider-hero-card,
.preview-viewport--mobile .slider-hero-card img {
  min-height: 260px;
}

.healthy-cover-preview {
  min-height: 620px;
  border-radius: 28px;
  background: radial-gradient(circle at 16% 15%, rgb(255 255 255 / 0.9), transparent 28%), linear-gradient(135deg, #fffaf2, #f1ddc3);
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 1.2rem;
  align-items: center;
  padding: 3rem;
  direction: ltr;
  border: 1px solid rgb(255 255 255 / 0.8);
}

.hcp-media {
  min-height: 470px;
  border-radius: 999px;
  background: var(--hero-img, url('https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=70')) center / cover;
  box-shadow: 0 24px 70px rgb(72 44 18 / 0.22);
}

.hcp-content {
  direction: rtl;
  display: grid;
  gap: 1rem;
  color: #174d32;
}

.hcp-badge {
  width: max-content;
  border-radius: 999px;
  border: 1px solid rgb(23 77 50 / 0.16);
  background: rgb(255 255 255 / 0.68);
  padding: 0.42rem 0.8rem;
  font-weight: 900;
  font-size: 0.84rem;
}

.hcp-content h2 {
  margin: 0;
  font-size: clamp(2rem, 4.8vw, 4.3rem);
  line-height: 1.14;
  font-weight: 950;
}

.hcp-content p {
  margin: 0;
  max-width: 520px;
  color: rgb(28 20 17 / 0.68);
  font-size: 1.05rem;
  line-height: 1.9;
}

.hcp-actions,
.hcp-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.hcp-actions span {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  padding: 0 1.3rem;
  background: #175333;
  color: #fff;
  font-weight: 900;
}

.hcp-actions .ghost {
  background: rgb(255 255 255 / 0.66);
  color: #174d32;
  border: 1px solid rgb(23 77 50 / 0.18);
}

.hcp-features {
  margin-top: 0.8rem;
  padding: 1rem;
  border-radius: 20px;
  background: rgb(255 255 255 / 0.62);
}

.hcp-features span {
  color: #174d32;
  font-weight: 900;
}

.preview-viewport--mobile .slider-hero-preview {
  min-height: 560px;
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #fffaf2, #efe0cf);
  color: #174d32;
}

.slider-hero-copy {
  display: grid;
  gap: 0.8rem;
}

.slider-hero-copy span {
  width: max-content;
  border-radius: 999px;
  padding: 0.36rem 0.78rem;
  background: rgb(23 77 50 / 0.08);
  font-weight: 900;
}

.slider-hero-copy h2 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 4rem);
  line-height: 1.15;
}

.slider-hero-copy p {
  margin: 0;
  color: rgb(28 20 17 / 0.65);
  line-height: 1.9;
}

.slider-hero-card {
  position: relative;
  min-height: 360px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 22px 64px rgb(72 44 18 / 0.18);
}

.slider-hero-card img {
  width: 100%;
  height: 100%;
  min-height: 360px;
  object-fit: cover;
  display: block;
}

.slider-hero-card strong {
  position: absolute;
  right: 1rem;
  bottom: 1rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.82);
  padding: 0.55rem 0.9rem;
}

.preview-viewport--mobile .slider-hero-preview {
  min-height: 620px;
  grid-template-columns: 1fr;
  padding: 1.1rem;
  border-radius: 0;
}

.preview-viewport--mobile .slider-hero-card,
.preview-viewport--mobile .slider-hero-card img {
  min-height: 260px;
}

.healthy-cover-preview {
  min-height: 620px;
  grid-template-columns: 1fr;
  padding: 1.2rem;
  border-radius: 0;
}

.preview-viewport--mobile .hcp-media {
  min-height: 260px;
}

.preview-viewport--mobile .hcp-content h2 {
  font-size: 2.2rem;
}


@media (max-width: 900px) {
  .workflow-stages {
    grid-template-columns: minmax(0, 1fr);
  }

  .review-summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .designer-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .designer-preview {
    position: static;
    order: 2;
  }

  .preview-viewport--desktop {
    transform: scale(0.28);
  }

  .form-grid,
  .editor-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .span-2 {
    grid-column: span 1;
  }
}

/* Variant selector */
.variant-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.variant-card {
  position: relative;
  flex: 1 1 160px;
  max-width: 220px;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border: 2px solid rgb(var(--palette-deep-sapphire-rgb) / 0.15);
  border-radius: 14px;
  padding: 0;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.15s;
  text-align: right;
  overflow: hidden;
  font-family: inherit;
}

.variant-card:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgb(0 0 0 / 0.08);
}

.variant-card.selected {
  border-color: var(--palette-deep-sapphire, #6F4A31);
  box-shadow: 0 4px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-june-bud-rgb) / 0.04);
}

.variant-preview {
  width: 100%;
  height: 80px;
  position: relative;
  overflow: hidden;
  border-radius: 0;
}

.vp-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  gap: 6px;
}

.vp-brand {
  width: 36px;
  height: 7px;
  border-radius: 4px;
  background: rgb(111 74 49 / 0.3);
}

.vp-links {
  width: 48px;
  height: 5px;
  border-radius: 4px;
  background: rgb(111 74 49 / 0.15);
}

.vp-hero {
  position: absolute;
  inset: 0;
  border-radius: 0;
}

.vp-title {
  display: block;
  width: 60%;
  height: 7px;
  border-radius: 4px;
  background: rgb(255 255 255 / 0.55);
  position: absolute;
  top: 38%;
  right: 14px;
}

.vp-sub {
  display: block;
  width: 40%;
  height: 4px;
  border-radius: 3px;
  background: rgb(255 255 255 / 0.3);
  position: absolute;
  top: 58%;
  right: 14px;
}

.vp-footer {
  position: absolute;
  inset: 0;
}

.vp-footer-brand {
  display: block;
  width: 50px;
  height: 6px;
  border-radius: 3px;
  background: rgb(201 141 66 / 0.5);
  position: absolute;
  bottom: 28px;
  right: 14px;
}

.vp-footer-links {
  display: block;
  width: 70px;
  height: 4px;
  border-radius: 3px;
  background: rgb(255 255 255 / 0.18);
  position: absolute;
  bottom: 14px;
  right: 14px;
}

.vp-search-card {
  position: absolute;
  inset: 10px;
  display: grid;
  align-content: center;
  gap: 9px;
}

.vp-search-title {
  display: block;
  width: 46%;
  height: 9px;
  border-radius: 999px;
  background: #4c212d;
  margin-right: auto;
}

.vp-search-input {
  display: block;
  width: 100%;
  height: 18px;
  border-radius: 999px;
  border: 1px solid #e4cfd3;
  background: #fff;
}

.variant-meta {
  padding: 0 0.8rem 0.7rem;
  display: grid;
  gap: 0.18rem;
  text-align: right;
}

.variant-meta strong {
  font-size: 0.82rem;
  color: var(--ink-900, #1c1411);
}

.variant-meta small {
  font-size: 0.7rem;
  color: var(--ink-700, #7a6a60);
  line-height: 1.45;
}

.variant-check {
  position: absolute;
  top: 0.45rem;
  left: 0.45rem;
  width: 1.3rem;
  height: 1.3rem;
  border-radius: 50%;
  background: var(--palette-deep-sapphire, #6F4A31);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vp-card-preview {
  width: 48%;
  margin: auto;
  border-radius: 10px;
}

.image-upload-row {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}

.secondary-btn.mini {
  font-size: 0.76rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--glass-border, #d5c3af);
  background: transparent;
  color: var(--text-primary, #3f2a1d);
  cursor: pointer;
}

.secondary-btn.mini.danger {
  border-color: var(--danger, #dc2626);
  color: var(--danger, #dc2626);
}

.variant-action-row {
  margin-top: 0.65rem;
  display: flex;
}

.site-preview-shell {
  display: grid;
  gap: 0.85rem;
}

.card-preview-row {
  display: flex;
  justify-content: center;
  padding: 1rem 0;
}

.card-preview-item {
  width: 100%;
  max-width: 360px;
}

.site-preview-hero {
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 14px 26px rgb(15 23 42 / 0.1);
}

.site-preview-hero.site-hero {
  min-height: 360px;
}

.site-preview-hero.site-hero .hero-content {
  padding: 2rem 1rem 2.4rem;
}

.site-preview-hero.site-hero .hero-title {
  font-size: clamp(1.8rem, 4vw, 3rem);
}

.site-preview-hero.site-hero .hero-description {
  font-size: 0.98rem;
}

.site-preview-hero.site-hero .hero-food-icons,
.site-preview-hero.site-hero .hero-scroll-hint {
  display: none;
}

.site-preview-footer {
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 14px 26px rgb(15 23 42 / 0.08);
}

.site-preview-footer.site-footer :deep(.footer-inner) {
  width: 100%;
  padding: 1.4rem 1rem 0.8rem;
}

.site-preview-footer.site-footer :deep(.footer-grid) {
  grid-template-columns: 1fr;
  gap: 1rem;
}

.site-preview-footer.site-footer-minimal :deep(.sfm-inner) {
  width: 100%;
  padding: 0.9rem 1rem;
}

.site-preview-empty {
  border-radius: 18px;
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.25);
  background: rgb(var(--palette-eggshell-rgb) / 0.75);
  padding: 1rem;
  color: var(--text-muted);
  display: grid;
  gap: 0.25rem;
}

.site-preview-empty strong {
  color: var(--ink-900, #1c1411);
}

.site-preview-empty--footer {
  min-height: 92px;
}

@media (max-width: 640px) {
  .variant-row {
    gap: 0.55rem;
  }

  .variant-card {
    flex: 1 1 130px;
    max-width: 180px;
  }
}
</style>
