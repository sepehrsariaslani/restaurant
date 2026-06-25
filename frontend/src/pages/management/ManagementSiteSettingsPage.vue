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

    <template v-else-if="activeTab === 'components'">
      <ManagementSurfaceCard title="هدر سایت" subtitle="یک سبک هدر انتخاب کنید — این تنها هدری است که روی سایت نمایش داده می‌شود.">
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
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="کامپوننت سرچ منو" subtitle="این کارت جدا از هدر است و در صفحه خانه/منو برای جستجوی سریع نمایش داده می‌شود.">
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
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="هیرو سکشن" subtitle="نحوه نمایش بنر اصلی صفحه خانه را مشخص کنید — فقط یک گزینه فعال می‌ماند.">
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
        <div class="variant-action-row" v-if="webSettings.hero_section_variant !== 'off'">
          <button type="button" class="secondary-btn mini" @click="activeTab = 'content'">ویرایش محتوای هیرو ←</button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="فوتر سایت" subtitle="سبک پاورقی سایت را انتخاب کنید — فقط یک گزینه فعال می‌ماند.">
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
        <div class="variant-action-row" v-if="webSettings.footer_variant !== 'off'">
          <button type="button" class="secondary-btn mini" @click="activeTab = 'content'">ویرایش محتوای فوتر ←</button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="دسته‌بندی‌های منو" subtitle="نحوه نمایش دسته‌بندی‌ها را انتخاب کنید — تصویری یا متنی.">
        <div class="variant-row">
          <button
            type="button"
            class="variant-card"
            :class="{ selected: webSettings.category_rail_variant === 'pill' }"
            @click="webSettings.category_rail_variant = 'pill'"
          >
            <div class="variant-preview" style="background: #f5f0eb; padding: 8px;">
              <div style="display: flex; gap: 6px; margin-top: 8px;">
                <div style="background: #fff; border: 1px solid #ddd; border-radius: 10px; width: 56px; height: 38px;"></div>
                <div style="background: rgba(111,74,49,0.12); border: 1px solid rgba(111,74,49,0.4); border-radius: 10px; width: 56px; height: 38px;"></div>
                <div style="background: #fff; border: 1px solid #ddd; border-radius: 10px; width: 56px; height: 38px;"></div>
              </div>
            </div>
            <div class="variant-meta">
              <strong>دسته‌بندی متنی (Pill)</strong>
              <small>دکمه‌های متنی با نام و تعداد آیتم — کلاسیک و خوانا</small>
            </div>
            <span class="variant-check" v-if="webSettings.category_rail_variant === 'pill'">✓</span>
          </button>
          <button
            type="button"
            class="variant-card"
            :class="{ selected: webSettings.category_rail_variant === 'image' }"
            @click="webSettings.category_rail_variant = 'image'"
          >
            <div class="variant-preview" style="background: #f5f0eb; padding: 8px;">
              <div style="display: flex; gap: 8px; margin-top: 6px; justify-content: center;">
                <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                  <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--accent-green, #6f4a31);"></div>
                  <div style="width: 34px; height: 6px; background: #ccc; border-radius: 3px;"></div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                  <div style="width: 40px; height: 40px; border-radius: 50%; background: #e0d8cf;"></div>
                  <div style="width: 34px; height: 6px; background: #ccc; border-radius: 3px;"></div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                  <div style="width: 40px; height: 40px; border-radius: 50%; background: #e0d8cf;"></div>
                  <div style="width: 34px; height: 6px; background: #ccc; border-radius: 3px;"></div>
                </div>
              </div>
            </div>
            <div class="variant-meta">
              <strong>دسته‌بندی تصویری (Image)</strong>
              <small>دایره‌های تصویر/ایموجی با برچسب — بصری و مدرن</small>
            </div>
            <span class="variant-check" v-if="webSettings.category_rail_variant === 'image'">✓</span>
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="کارت محصولات" subtitle="نمایش کارت‌های منو — یک استایل را انتخاب کنید.">
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
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="پیش‌نمایش کارت محصول" subtitle="نمایش زنده کارت با استایل انتخابی">
        <div class="card-preview-row">
          <div class="card-preview-item">
            <MenuItemCard
              :key="`card-preview-${webSettings.card_variant}`"
              :item="previewCardItem"
              :card-variant="webSettings.card_variant"
              :currency="'TOMAN'"
            />
          </div>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="پیش‌نمایش زنده" subtitle="با تغییر هر گزینه، همین‌جا کامپوننت واقعی را می‌بینی.">
        <div class="site-preview-shell">
          <PublicHeader
            :key="`preview-${webSettings.header_variant}`"
            :branding="previewBranding"
            :page="'preview'"
            :cart-count="3"
            :has-last-order="false"
            :last-order-url="'/menu'"
            :header-variant="webSettings.header_variant"
            :preview="true"
          />

          <MenuHeroHeader
            v-if="webSettings.menu_search_variant === 'search-card'"
            :key="`menu-search-${webSettings.menu_search_variant}`"
            :branding="previewBranding"
            :search="'جستجو در منو...'"
            :cart-count="3"
          />

          <component
            :is="heroPreviewComponent"
            v-if="heroPreviewComponent"
            :key="`hero-${webSettings.hero_section_variant}`"
            v-bind="heroPreviewProps"
            class="site-preview-hero"
          />

          <div v-else class="site-preview-empty">
            <strong>هیرو سکشن خاموش است</strong>
            <p>برای دیدن پیش‌نمایش هیرو، یک حالت دیگر را از تب کامپوننت‌ها انتخاب کن.</p>
          </div>

          <component
            :is="footerPreviewComponent"
            v-if="footerPreviewComponent"
            :key="`footer-${webSettings.footer_variant}`"
            v-bind="footerPreviewProps"
            class="site-preview-footer"
          />

          <div v-else class="site-preview-empty site-preview-empty--footer">
            <strong>فوتر خاموش است</strong>
            <p>با انتخاب فوتر کامل یا مینیمال، پاورقی سایت روی همه صفحات عمومی نمایش داده می‌شود.</p>
          </div>
        </div>
      </ManagementSurfaceCard>
    </template>

    <template v-else-if="activeTab === 'content'">
      <ManagementSurfaceCard title="اطلاعات هیرو سکشن" subtitle="محتوای بنر انتخابی صفحه خانه را تنظیم کنید." v-if="webSettings.hero_section_variant !== 'off'">
        <div class="form-grid">
          <label class="span-2">
            عنوان هیرو سکشن
            <input class="input" v-model.trim="webSettings.hero_section_title" placeholder="مثال: بهترین غذا را سفارش دهید" />
          </label>
          <label class="span-2">
            توضیحات هیرو سکشن
            <textarea class="textarea" v-model.trim="webSettings.hero_section_description" placeholder="متن توضیحی که زیر عنوان نمایش داده می‌شود..." />
          </label>
          <label>
            متن دکمه CTA
            <input class="input" v-model.trim="webSettings.hero_section_cta" placeholder="مثال: مشاهده منو" />
          </label>
          <label>
            تصویر پس‌زمینه
            <input class="input" v-model.trim="webSettings.hero_image" placeholder="/files/hero.jpg یا URL عکس" />
            <div class="image-upload-row">
              <button type="button" class="secondary-btn mini" @click="heroImageInput.click()">📁 انتخاب عکس از دستگاه</button>
              <button type="button" class="secondary-btn mini danger" v-if="webSettings.hero_image" @click="webSettings.hero_image = ''">حذف عکس</button>
            </div>
            <input
              ref="heroImageInput"
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
              style="display:none"
              @change="handleHeroImageUpload"
            />
            <img
              v-if="String(webSettings.hero_image || '').trim()"
              class="image-preview"
              :src="webSettings.hero_image"
              alt="Hero bg"
            />
          </label>
          <label>
            موقعیت تصویر
            <SearchableDropdown
              v-model="webSettings.hero_image_position"
              :options="imagePositionOptions"
              placeholder="انتخاب موقعیت"
            />
          </label>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="اطلاعات فوتر" subtitle="محتوایی که در پاورقی سایت نمایش داده می‌شود." v-if="webSettings.footer_variant !== 'off'">
        <div class="form-grid">
          <label class="span-2">
            توضیحات برند (زیر لوگو)
            <textarea class="textarea" v-model.trim="webSettings.footer_description" placeholder="جمله معرفی کسب‌وکار..." />
          </label>
          <label>
            شماره تماس
            <input class="input" v-model.trim="webSettings.footer_phone" placeholder="مثال: 021-12345678" />
          </label>
          <label>
            ایمیل
            <input class="input" type="email" v-model.trim="webSettings.footer_email" placeholder="info@example.com" />
          </label>
          <label class="span-2">
            آدرس
            <input class="input" v-model.trim="webSettings.footer_address" placeholder="آدرس کامل..." />
          </label>
          <label>
            لینک اینستاگرام
            <input class="input" v-model.trim="webSettings.footer_instagram" placeholder="https://instagram.com/..." />
          </label>
          <label>
            لینک تلگرام
            <input class="input" v-model.trim="webSettings.footer_telegram" placeholder="https://t.me/..." />
          </label>
          <label class="span-2">
            متن کپی‌رایت
            <input class="input" v-model.trim="webSettings.footer_copyright" placeholder="مثال: تمامی حقوق محفوظ است." />
          </label>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard v-if="webSettings.hero_section_variant === 'off' && webSettings.footer_variant === 'off'">
        <p class="muted">هیچ کامپوننتی فعال نیست. ابتدا از تب <strong>کامپوننت‌ها</strong> یک بخش را فعال کنید.</p>
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
import MenuHeroHeader from '@/components/MenuHeroHeader.vue'
import PublicHeader from '@/components/PublicHeader.vue'
import SiteLoaderRenderer from '@/components/SiteLoaderRenderer.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import SiteFooterMinimal from '@/components/SiteFooterMinimal.vue'
import SiteHeroBanner from '@/components/SiteHeroBanner.vue'
import SiteHeroSection from '@/components/SiteHeroSection.vue'
import ManagementEditableTable from '@/components/management/ManagementEditableTable.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import MenuItemCard from '@/components/MenuItemCard.vue'
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
  { value: 'components', label: 'کامپوننت‌ها' },
  { value: 'content', label: 'محتوای سایت' },
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
  hero_section_enabled: 0,
  footer_enabled: 1,
  header_variant: 'classic',
  menu_search_variant: 'search-card',
  hero_section_variant: 'off',
  footer_variant: 'full',
  hero_section_title: '',
  hero_section_description: '',
  hero_section_cta: '',
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
    label: 'هیرو پوشش‌دهنده',
    desc: 'هدر و هیرو در یک کامپوننت تمام‌صفحه با تصویر پس‌زمینه و ناوبری شفاف روی آن',
    previewStyle: { background: 'linear-gradient(135deg, #1c1411, #3d2510)' },
    heroStyle: { background: 'linear-gradient(145deg, rgba(28,20,17,0.95), rgba(61,37,16,0.9))', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
  {
    value: 'foodbar',
    label: 'فودبار (محصول محور)',
    desc: 'هیرو با نمایش محصولات پرفروش، تصویر بزرگ محصول، چرخش خودکار و کارت‌های مینیاتوری',
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
  footer_description: String(webSettings.footer_description || '').trim(),
  footer_phone: String(webSettings.footer_phone || '').trim(),
  footer_email: String(webSettings.footer_email || '').trim(),
  footer_address: String(webSettings.footer_address || '').trim(),
  footer_instagram: String(webSettings.footer_instagram || '').trim(),
  footer_telegram: String(webSettings.footer_telegram || '').trim(),
  footer_copyright: String(webSettings.footer_copyright || '').trim(),
}))

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

const previewHeroTitle = computed(() => String(webSettings.hero_section_title || previewBranding.value.hero_title || '').trim())
const previewHeroDescription = computed(() => String(webSettings.hero_section_description || previewBranding.value.hero_subtitle || '').trim())
const previewHeroCta = computed(() => String(webSettings.hero_section_cta || previewBranding.value.primary_cta_label || 'مشاهده منو').trim() || 'مشاهده منو')
const previewHeroImage = computed(() => String(webSettings.hero_image || previewBranding.value.hero_image || '').trim())

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
    const footerEnabled = Number(nextWeb.footer_enabled ?? 1)
    webSettings.footer_variant = String(nextWeb.footer_variant || (footerEnabled ? 'full' : 'off')).trim() || 'full'
    webSettings.hero_section_title = String(nextWeb.hero_section_title || '').trim()
    webSettings.hero_section_description = String(nextWeb.hero_section_description || '').trim()
    webSettings.hero_section_cta = String(nextWeb.hero_section_cta || '').trim()
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
    })

    heroSlides.value = (payload?.hero_slides || []).map((row) => normalizeHeroSlide(row))
    aboutSections.value = (payload?.about_sections || []).map((row) => normalizeAboutSection(row))
    faqItems.value = (payload?.faq_items || []).map((row) => normalizeFaqItem(row))
    assignLoaderSettingsToForm(payload?.web_settings || {})
    syncBootFromWebSettings(payload)
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
