<template>
  <ManagementPageScaffold :title="pageTitle" :subtitle="pageSubtitle">
    <template #actions>
      <span v-if="hasUnsavedChanges" class="unsaved-chip">تغییرات ذخیره نشده</span>
      <a class="secondary-btn" href="/management/products">بازگشت</a>
      <button class="primary-btn" type="button" @click="saveSettings" :disabled="!canSaveSettings">
        {{ savingSettings ? 'در حال ذخیره...' : hasUnsavedChanges ? 'ذخیره تغییرات' : 'بدون تغییر' }}
      </button>
      <button class="secondary-btn" type="button" @click="loadDetail" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی اطلاعات' }}
      </button>
      <button class="secondary-btn delete-btn" type="button" :disabled="deletingProduct || loading" @click="deleteProduct">
        {{ deletingProduct ? 'در حال حذف...' : 'حذف / غیرفعال' }}
      </button>
    </template>

    <ManagementSurfaceCard tone="soft" class="tabs-shell">
      <div class="tab-list" role="tablist" aria-label="مدیریت جزئیات محصول">
        <button
          v-for="tab in tabOptions"
          :key="tab.value"
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === tab.value }"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <p class="muted tab-hint">{{ activeTabHint }}</p>
      <p class="unsaved-note" v-if="hasUnsavedChanges">تغییرات ذخیره نشده است؛ برای ثبت، روی «ذخیره تغییرات» در بالای صفحه بزنید.</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="accent" v-if="activeTab === 'reports'">
      <div class="filters">
        <label>
          از تاریخ
          <PersianDateInput v-model="filters.date_from" />
        </label>
        <label>
          تا تاریخ
          <PersianDateInput v-model="filters.date_to" />
        </label>
        <button class="primary-btn" type="button" @click="loadDetail">اجرای تحلیل</button>
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری اطلاعات محصول...</p>
    <p class="error" v-if="error">{{ error }}</p>

    <template v-if="detail && !loading">
      <section class="product-top-grid" v-if="activeTab === 'overview'">
        <ManagementSurfaceCard title="مشخصات محصول" subtitle="فیلدهای اصلی سایت و منو">
          <div class="identity-grid">
            <label>
              کد محصول
              <input class="input" v-model="settingsForm.item_code" />
              <small class="hint">کد یکتای محصول در سیستم</small>
            </label>
            <label>
              کد اسنپ (custom_snapp_code)
              <input class="input" v-model="settingsForm.custom_snapp_code" placeholder="مثال: SNP-F3FEECEF86" />
              <small class="hint">کد محصول در سیستم اسنپ‌فود</small>
            </label>
            <label>
              نام محصول
              <input class="input" v-model="settingsForm.item_name" />
              <small class="hint">نام نمایشی محصول برای مشتریان</small>
            </label>
            <label>
              گروه کالا
              <SearchableDropdown
                v-model="settingsForm.item_group"
                :options="fieldOptions.item_groups || []"
                placeholder="انتخاب گروه"
                search-placeholder="جستجوی گروه..."
                include-empty-option
                empty-label="انتخاب گروه"
              />
            </label>
            <label>
              واحد
              <SearchableDropdown
                v-model="settingsForm.stock_uom"
                :options="fieldOptions.uoms || []"
                placeholder="انتخاب واحد"
                search-placeholder="جستجوی واحد..."
                include-empty-option
                empty-label="انتخاب واحد"
              />
            </label>
          </div>

          <label>
            <span class="field-label">توضیح کوتاه</span>
            <textarea class="textarea" v-model="settingsForm.restaurant_short_desc"></textarea>
            <small class="field-help">این متن در کارت محصول داخل صفحه منو و لیست محصولات نمایش داده می‌شود.</small>
          </label>
          <label>
            <span class="field-label">توضیح کامل</span>
            <textarea class="textarea" v-model="settingsForm.restaurant_long_desc"></textarea>
            <small class="field-help">این بخش در صفحه جزئیات محصول سایت (کنار اطلاعات اصلی) نشان داده می‌شود.</small>
          </label>
          <label>
            <span class="field-label">توضیحات داخلی</span>
            <textarea class="textarea" v-model="settingsForm.description"></textarea>
            <small class="field-help">
              توضیح داخلی تیم است؛ اگر توضیح کامل خالی باشد، این متن می‌تواند به‌عنوان متن جایگزین در سایت استفاده شود.
            </small>
          </label>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="تصاویر محصول" subtitle="تصویر اصلی + گالری پیوست‌ها">
          <div class="image-shell">
            <img v-if="mainImage" :src="mainImage" alt="product image" class="main-image" />
            <p v-else class="muted">تصویری ثبت نشده است.</p>
          </div>
          <section class="menu-preview-inline">
            <header class="menu-preview-inline-head">
              <div class="menu-preview-inline-meta">
                <strong>نمایش منو (Preview)</strong>
                <small>خروجی واقعی کارت‌های منو با تنظیمات فعلی این محصول</small>
              </div>
              <span class="muted menu-preview-inline-note">برای بازبینی کامل، روی کارت بزنید.</span>
            </header>
            <div v-if="previewMenuCardRows.length" class="menu-preview-list menu-preview-list--inline">
              <div
                v-for="row in previewMenuCardRows"
                :key="`${row.slug}-${row.name}`"
                class="menu-preview-row"
                role="button"
                tabindex="0"
                @click="openPreviewCard(row)"
                @keydown.enter.prevent="openPreviewCard(row)"
                @keydown.space.prevent="openPreviewCard(row)"
              >
                <MenuProductCard
                  :item="row"
                  currency="TOMAN"
                  :cart-qty="0"
                  class="product-card-anim preview-static-card"
                />
              </div>
            </div>
            <p v-else class="muted">در حال حاضر خروجی منوی قابل نمایش وجود ندارد.</p>
          </section>
          <p class="error" v-if="mediaError">{{ mediaError }}</p>
          <p class="success" v-if="mediaSuccess">{{ mediaSuccess }}</p>
          <ManagementImageUploaderView
            :items="mediaItems"
            :uploading="mediaUploading"
            :busy="mediaSaving"
            @select="selectImage"
            @upload="uploadImages"
            @set-cover="setCoverImage"
            @set-secondary="setSecondaryImage"
            @remove="removeImage"
          />
        </ManagementSurfaceCard>
      </section>

      <section class="product-settings-grid" v-if="activeTab === 'settings'">
        <ManagementSurfaceCard title="تنظیمات رستورانی و وب">
          <div class="identity-grid">
            <label>
              اسلاگ
              <input class="input" v-model="settingsForm.restaurant_slug" />
            </label>
            <label>
              دسته
              <SearchableDropdown
                v-model="settingsForm.restaurant_category"
                :options="fieldOptions.categories || []"
                placeholder="بدون دسته"
                search-placeholder="جستجوی دسته..."
                include-empty-option
                empty-label="بدون دسته"
              />
            </label>
            <label>
              زیردسته
              <SearchableDropdown
                v-model="settingsForm.restaurant_subcategory"
                :options="filteredSubcategoryOptions"
                placeholder="بدون زیردسته"
                search-placeholder="جستجوی زیردسته..."
                include-empty-option
                empty-label="بدون زیردسته"
              />
            </label>
            <label>
              شعبه
              <SearchableDropdown
                v-model="settingsForm.restaurant_branch"
                :options="fieldOptions.branches || []"
                placeholder="همه شعب"
                search-placeholder="جستجوی شعبه..."
                include-empty-option
                empty-label="همه شعب"
              />
            </label>
            <label>
              زمان آماده‌سازی (دقیقه)
              <PersianNumberInput v-model="settingsForm.restaurant_prep_time_mins" suffix="دقیقه" :min="0" />
            </label>
            <label>
              ترتیب نمایش
              <PersianNumberInput v-model="settingsForm.restaurant_sort_order" :min="0" />
            </label>
            <label>
              کالری
              <PersianNumberInput v-model="settingsForm.restaurant_nutrition_kcal" :allow-float="true" :min="0" />
            </label>
            <label>
              پروتئین (g)
              <PersianNumberInput v-model="settingsForm.restaurant_nutrition_protein_g" :allow-float="true" :min="0" />
            </label>
            <label>
              کربوهیدرات (g)
              <PersianNumberInput v-model="settingsForm.restaurant_nutrition_carb_g" :allow-float="true" :min="0" />
            </label>
            <label>
              قند (g)
              <PersianNumberInput v-model="settingsForm.restaurant_nutrition_sugar_g" :allow-float="true" :min="0" />
            </label>
            <label>
              چربی (g)
              <PersianNumberInput v-model="settingsForm.restaurant_nutrition_fat_g" :allow-float="true" :min="0" />
            </label>
            <label>
              تصویر اصلی
              <input class="input" v-model="settingsForm.image" placeholder="/files/item.jpg" />
            </label>
            <label>
              تصویر وب
              <input class="input" v-model="settingsForm.website_image" placeholder="/files/item-web.jpg" />
            </label>
            <label>
              مقدار افزودن خودکار
              <PersianNumberInput v-model="settingsForm.restaurant_auto_add_qty" :allow-float="true" :min="0" />
            </label>
          </div>

          <div class="checks-grid">
            <label class="check"><input type="checkbox" v-model="settingsForm.show_in_print" /> نمایش در پرینت</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.restaurant_enabled" /> فعال در منوی رستوران</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.restaurant_is_featured" /> محصول ویژه</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.restaurant_is_best_seller" /> محصول پرفروش</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.restaurant_requires_bom" /> نیازمند BOM</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.restaurant_auto_add_to_order" /> افزودن خودکار به سفارش</label>
            <label class="check"><input type="checkbox" v-model="settingsForm.disabled" /> غیرفعال در ERPNext</label>
          </div>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="قیمت‌گذاری" subtitle="پیروی از Price List پیش‌فرض">
          <div class="identity-grid">
            <label>
              لیست قیمت پیش‌فرض
              <SearchableDropdown
                v-model="selectedDefaultPriceList"
                :options="priceListOptions"
                placeholder="انتخاب لیست قیمت"
                search-placeholder="جستجوی لیست قیمت..."
              />
            </label>
            <label>
              قیمت فعلی (لیست پیش‌فرض)
              <input class="input" :value="formatMoney(currentPriceRate, activeCurrency)" readonly />
            </label>
            <label>
              آخرین قیمت ثبت‌شده
              <input class="input" :value="formatMoney(latestPriceRate, activeCurrency)" readonly />
            </label>
            <label>
              تاریخ آخرین قیمت
              <input class="input" :value="formatPersianDate(latestPriceDate, true)" readonly />
            </label>
          </div>

          <div class="inline-actions">
            <button class="secondary-btn" type="button" @click="saveDefaultPriceList" :disabled="savingDefaultPriceList">
              {{ savingDefaultPriceList ? 'در حال اعمال...' : 'اعمال لیست قیمت پیش‌فرض' }}
            </button>
          </div>

          <div class="identity-grid">
            <label>
              لیست قیمت برای ثبت
              <SearchableDropdown
                v-model="priceForm.price_list"
                :options="priceListOptions"
                placeholder="انتخاب لیست قیمت"
                search-placeholder="جستجوی لیست قیمت..."
              />
            </label>
            <label>
              قیمت جدید
              <PersianNumberInput v-model="priceForm.price_list_rate" :min="0" suffix="ریال" />
            </label>
            <label>
              تاریخ اعتبار
              <PersianDateInput v-model="priceForm.valid_from" />
            </label>
          </div>

          <button class="primary-btn" type="button" @click="savePrice" :disabled="savingPrice">
            {{ savingPrice ? 'در حال ثبت قیمت...' : 'ثبت قیمت محصول' }}
          </button>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard
          class="bom-card"
          title="لیست BOMهای این محصول"
          subtitle="ویرایش BOM فقط از صفحه اختصاصی BOM انجام می‌شود."
        >
          <div class="bom-meta">
            <a class="primary-btn mini-link-btn" :href="productBomPageUrl">مدیریت BOM در صفحه اختصاصی</a>
            <a
              v-if="defaultBomName"
              class="secondary-btn mini-link-btn"
              :href="`/app/bom/${encodeURIComponent(defaultBomName)}`"
              target="_blank"
              rel="noreferrer"
            >
              BOM پیش‌فرض: {{ defaultBomName }}
            </a>
            <a
              v-if="activeBomName && activeBomName !== defaultBomName"
              class="secondary-btn mini-link-btn"
              :href="`/app/bom/${encodeURIComponent(activeBomName)}`"
              target="_blank"
              rel="noreferrer"
            >
              BOM فعال: {{ activeBomName }}
            </a>
            <p v-if="!defaultBomName && !activeBomName" class="hint-line">
              هنوز BOM پیش‌فرض/فعال برای این محصول تعیین نشده است.
            </p>
          </div>

          <p class="muted" v-if="bomLoading">در حال دریافت لیست BOM...</p>
          <p class="error" v-if="bomError">{{ bomError }}</p>

          <ManagementDataTable v-if="productBoms.length" :columns="bomColumns" :rows="productBoms" row-key="name">
            <template #cell-status="{ row }">
              <div class="status-pills">
                <span :class="['pill', Number(row.is_active) ? 'active' : 'inactive']">
                  {{ Number(row.is_active) ? 'فعال' : 'غیرفعال' }}
                </span>
                <span class="pill default" v-if="Number(row.is_default)">پیش فرض</span>
                <span class="pill docstatus" v-if="Number(row.docstatus) === 0">پیش نویس</span>
                <span class="pill docstatus submitted" v-else-if="Number(row.docstatus) === 1">ثبت شده</span>
              </div>
            </template>
            <template #cell-quantity="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-modified="{ value }">{{ formatPersianDate(value, true) }}</template>
            <template #cell-actions="{ row }">
              <div class="row-actions">
                <a class="secondary-btn mini-link-btn" :href="bomManagerUrl(row)">ویرایش در صفحه BOM</a>
                <a class="secondary-btn mini-link-btn" :href="`/app/bom/${encodeURIComponent(row.name)}`" target="_blank" rel="noreferrer">
                  ERP
                </a>
              </div>
            </template>
          </ManagementDataTable>

          <p v-else-if="!bomLoading" class="hint-line">برای این محصول BOM ثبت نشده است.</p>
        </ManagementSurfaceCard>
      </section>

      <section v-if="activeTab === 'variants'" class="variants-grid">
        <ManagementSurfaceCard
          v-if="isVariantContext"
          title="ویژگی‌های همین Variant"
          subtitle="این کالا از قالب ساخته شده و در این تب فقط ویژگی‌های فعلی نمایش داده می‌شود"
        >
          <p class="hint-line">
            این کالا از تمپلیت {{ detail?.item?.variant_of_item_name || detail?.item?.variant_of || resolvedTemplateLabel || resolvedTemplateName || '-' }} ساخته شده است.
          </p>
          <p class="muted">
            تمپلیت: {{ resolvedTemplateLabel || '-' }} ({{ resolvedTemplateName || '-' }})
          </p>
          <div class="variant-editor-table-wrap" v-if="currentVariantAttributeRows.length">
            <table class="variant-values-table">
              <thead>
                <tr>
                  <th>شماره</th>
                  <th>ویژگی</th>
                  <th>مقدار</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in currentVariantAttributeRows" :key="`current-variant-attr-${row.index}-${row.attribute}-${row.value}`">
                  <td>{{ row.index.toLocaleString('fa-IR') }}</td>
                  <td>{{ row.attribute || '-' }}</td>
                  <td>{{ row.value || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="variant-value-mobile-list" v-if="currentVariantAttributeRows.length">
            <article v-for="row in currentVariantAttributeRows" :key="`current-variant-mobile-${row.index}-${row.attribute}-${row.value}`" class="variant-value-mobile-card">
              <strong>{{ row.attribute || '-' }}</strong>
              <small class="muted">ردیف {{ row.index.toLocaleString('fa-IR') }}</small>
              <p class="muted">مقدار: {{ row.value || '-' }}</p>
            </article>
          </div>
          <p v-else class="muted">برای این Variant هنوز ویژگی ثبت نشده است.</p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard
          v-else-if="hasVariantFeatureEnabled"
          title="مدیریت Item Attribute و Variant"
          subtitle="ویژگی‌های موثر در منو و ویژگی‌های انتخابی مشتری"
        >
          <p class="muted">
            تمپلیت فعال: {{ resolvedTemplateLabel || '-' }} ({{ resolvedTemplateName || '-' }})
          </p>

          <div class="inline-actions">
            <button class="primary-btn" type="button" @click="openVariantCreationDialog" :disabled="variantBuilderLoading || selectedTemplateAttributeCount === 0">
              ساخت متغیر از محصول
            </button>
          </div>

          <p class="error" v-if="variantBuilderError">{{ variantBuilderError }}</p>
          <p class="success" v-if="variantBuilderSuccess">{{ variantBuilderSuccess }}</p>
          <p class="muted" v-if="variantBuilderLoading">در حال دریافت اطلاعات ویژگی‌ها...</p>

          <template v-if="!variantBuilderLoading && variantAttributesDraft.length">
            <div class="variant-config-shell">
              <div class="variant-config-head">
                <strong>جدول ویژگی‌های تمپلیت</strong>
                <small class="muted">ویژگی‌های فعال: {{ selectedTemplateAttributeCount.toLocaleString('fa-IR') }}</small>
                <button v-if="inactiveTemplateAttributes.length > 0" class="secondary-btn mini-link-btn" type="button" @click="showAddAttributeDialog = true">
                  افزودن ویژگی
                </button>
              </div>

              <div class="variant-editor-table-wrap">
                <table class="variant-editor-table">
                  <thead>
                    <tr>
                      <th>ویژگی</th>
                      <th>نمایش در سایت</th>
                      <th>انتخابی مشتری</th>
                      <th>مقادیر فعال</th>
                      <th>عملیات</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="row in activeTemplateAttributes"
                      :key="`table-${row.name}`"
                      class="variant-clickable-row"
                      :class="{ active: activeVariantAttributeName === row.name }"
                      @click="openAttributeEditor(row.name)"
                    >
                      <td>
                        <div class="variant-attr-meta">
                          <strong>{{ row.label }}</strong>
                          <small>{{ row.name }}</small>
                        </div>
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          :checked="Number(row.show_in_website || 0) === 1"
                          @click.stop
                          @change.stop="updateAttributeToggle(row.name, 'show_in_website', $event.target.checked)"
                        />
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          :checked="Number(row.selection_only || 0) === 1"
                          @click.stop
                          @change.stop="updateAttributeToggle(row.name, 'selection_only', $event.target.checked)"
                        />
                      </td>
                      <td>
                        {{ countSelectedValues(row.name).toLocaleString('fa-IR') }} / {{ (row.values || []).length.toLocaleString('fa-IR') }}
                      </td>
                      <td>
                        <div class="row-actions" @click.stop>
                          <button class="secondary-btn mini-link-btn" type="button" @click.stop="openAttributeEditor(row.name)">ویرایش</button>
                          <button class="secondary-btn mini-link-btn delete-mini-btn" type="button" @click.stop="removeAttributeFromTemplate(row.name)">حذف</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="variant-attribute-mobile-list">
                <article
                  v-for="row in activeTemplateAttributes"
                  :key="`mobile-attr-${row.name}`"
                  class="variant-attribute-mobile-card"
                  :class="{ active: activeVariantAttributeName === row.name }"
                  role="button"
                  tabindex="0"
                  @click="openAttributeEditor(row.name)"
                  @keydown.enter.prevent="openAttributeEditor(row.name)"
                  @keydown.space.prevent="openAttributeEditor(row.name)"
                >
                  <header>
                    <strong>{{ row.label }}</strong>
                    <small>{{ row.name }}</small>
                  </header>
                  <div class="checks-grid compact-checks">
                    <label class="check">
                      <input
                        type="checkbox"
                        :checked="Number(row.show_in_website || 0) === 1"
                        @click.stop
                        @change.stop="updateAttributeToggle(row.name, 'show_in_website', $event.target.checked)"
                      />
                      نمایش در سایت
                    </label>
                    <label class="check">
                      <input
                        type="checkbox"
                        :checked="Number(row.selection_only || 0) === 1"
                        @click.stop
                        @change.stop="updateAttributeToggle(row.name, 'selection_only', $event.target.checked)"
                      />
                      انتخابی مشتری
                    </label>
                  </div>
                  <footer>
                    <span>مقادیر فعال: {{ countSelectedValues(row.name).toLocaleString('fa-IR') }} / {{ (row.values || []).length.toLocaleString('fa-IR') }}</span>
                    <div class="row-actions" @click.stop>
                      <button class="secondary-btn mini-link-btn" type="button" @click.stop="openAttributeEditor(row.name)">ویرایش مقادیر</button>
                      <button class="secondary-btn mini-link-btn delete-mini-btn" type="button" @click.stop="removeAttributeFromTemplate(row.name)">حذف</button>
                    </div>
                  </footer>
                </article>
              </div>
            </div>
          </template>
          <p v-else-if="!variantBuilderLoading" class="muted">ویژگی فعالی برای این تمپلیت ثبت نشده است.</p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard v-else title="Variant برای این کالا فعال نیست" subtitle="این بخش فقط برای کالا/قالبی نمایش داده می‌شود که has_variants روشن باشد">
          <p class="muted">برای مدیریت و ساخت Variant، ابتدا گزینه has_variants را روی قالب کالا فعال کنید.</p>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard v-if="!isVariantContext && hasVariantFeatureEnabled" title="Variantهای ساخته‌شده" subtitle="لیست خروجی Variantهای این تمپلیت">
          <ManagementDataTable
            class="variant-desktop-table"
            v-if="variantRows.length"
            :columns="[
              { key: 'item_code', label: 'کد' },
              { key: 'item_name', label: 'نام' },
              { key: 'attributes', label: 'ویژگی‌ها' },
              { key: 'slug', label: 'اسلاگ' },
              { key: 'is_active', label: 'وضعیت' },
              { key: 'actions', label: 'عملیات' },
            ]"
            :rows="variantRows"
            row-key="name"
          >
            <template #cell-attributes="{ row }">
              <span>{{ formatVariantAttributes(row) }}</span>
            </template>
            <template #cell-is_active="{ value }">
              <span :class="['state-pill', Number(value || 0) ? 'on' : 'off']">
                {{ Number(value || 0) ? 'فعال' : 'غیرفعال' }}
              </span>
            </template>
            <template #cell-actions="{ row }">
              <a class="secondary-btn mini-link-btn" :href="`/management/product?item_name=${encodeURIComponent(row.name)}`">جزئیات</a>
            </template>
          </ManagementDataTable>
          <div v-if="variantRows.length" class="variant-mobile-list">
            <article v-for="row in variantRows" :key="`variant-mobile-${row.name}`" class="variant-mobile-card">
              <header>
                <strong>{{ row.item_name || row.item_code || row.name }}</strong>
                <span :class="['state-pill', Number(row.is_active || 0) ? 'on' : 'off']">
                  {{ Number(row.is_active || 0) ? 'فعال' : 'غیرفعال' }}
                </span>
              </header>
              <p class="muted">کد: {{ row.item_code || '-' }}</p>
              <p class="muted">ویژگی‌ها: {{ formatVariantAttributes(row) }}</p>
              <p class="muted">اسلاگ: {{ row.slug || '-' }}</p>
              <a class="secondary-btn mini-link-btn" :href="`/management/product?item_name=${encodeURIComponent(row.name)}`">جزئیات</a>
            </article>
          </div>
          <p v-else class="muted">هنوز وریانتی برای این تمپلیت ثبت نشده است. از بخش بالا ویژگی‌ها را انتخاب کنید و روی «ساخت Variantها» بزنید.</p>
        </ManagementSurfaceCard>

      </section>

      <section v-if="activeTab === 'reports'" class="reports-content">
        <p class="muted" v-if="!hasReportData">برای این محصول گزارشی در بازه انتخابی ثبت نشده است.</p>

        <ReportKpiGrid :kpis="localizedReport.kpis" :currency="activeCurrency" />

        <section class="charts-grid" v-if="localizedReport.charts.length">
          <ReportChartRenderer
            v-for="chart in localizedReport.charts"
            :key="chart.key || chart.title"
            :chart="chart"
            :currency="activeCurrency"
          />
        </section>

        <section class="tables-grid" v-if="localizedReport.tables.length">
          <ManagementSurfaceCard
            v-for="table in localizedReport.tables"
            :key="table.key || table.title"
            :title="table.title || 'جدول'"
          >
            <ManagementDataTable :columns="table.columns || []" :rows="table.rows || []" row-key="name">
              <template v-for="column in table.columns || []" #[`cell-${column.key}`]="{ value }" :key="column.key">
                {{ formatTableCell(column, value) }}
              </template>
            </ManagementDataTable>
          </ManagementSurfaceCard>
        </section>

        <ReportInsightCards :insights="localizedReport.insights" />
      </section>

      <ManagementPopup
        v-model:open="previewModalOpen"
        title="پیش‌نمایش کامل محصول در منو"
        subtitle="نمایش کارت + نمای واقعی صفحه مشتری برای بازبینی نهایی"
        :size="isCompactViewport ? 'md' : 'xl'"
      >
        <section v-if="previewModalItem" class="menu-preview-modal-body">
          <MenuProductCard
            :item="previewModalItem"
            currency="TOMAN"
            :cart-qty="0"
            class="product-card-anim preview-static-card"
          />
          <section class="menu-preview-modal-details">
            <article>
              <strong>نام محصول</strong>
              <p>{{ previewModalItem.title || '-' }}</p>
            </article>
            <article>
              <strong>اسلاگ</strong>
              <p>{{ previewModalItem.slug || '-' }}</p>
            </article>
            <article>
              <strong>دسته / زیردسته</strong>
              <p>{{ previewModalItem.category_title || '-' }} / {{ previewModalItem.subcategory_title || '-' }}</p>
            </article>
            <article>
              <strong>توضیح کوتاه</strong>
              <p>{{ previewModalItem.short_desc || '-' }}</p>
            </article>
            <article>
              <strong>توضیح کامل</strong>
              <p>{{ previewModalItem.long_desc || '-' }}</p>
            </article>
            <article>
              <strong>قیمت</strong>
              <p>{{ formatMoney(previewModalItem.base_price || 0, 'TOMAN') }}</p>
            </article>
          </section>
          <section class="menu-preview-customer-view">
            <header class="menu-preview-customer-head">
              <strong>نمای واقعی صفحه مشتری</strong>
            </header>
            <iframe
              v-if="customerPreviewUrl && !isCompactViewport"
              :src="customerPreviewUrl"
              class="menu-preview-customer-iframe"
              title="Customer Product Preview"
              loading="lazy"
            ></iframe>
            <a
              v-else-if="customerPreviewUrl"
              class="secondary-btn menu-preview-customer-link"
              :href="customerPreviewUrl"
              target="_blank"
              rel="noreferrer"
            >
              باز کردن پیش‌نمایش صفحه مشتری
            </a>
            <p class="muted" v-else>برای نمایش دقیق صفحه مشتری، ابتدا اسلاگ محصول را تنظیم کنید.</p>
          </section>
        </section>
        <template #footer="{ close }">
          <button class="secondary-btn" type="button" @click="close">بستن</button>
        </template>
      </ManagementPopup>
    </template>
  </ManagementPageScaffold>

  <ManagementPopup
    v-model:open="attributeValuesDialogOpen"
    :title="activeVariantAttributeRow ? `جدول مقادیر ویژگی: ${activeVariantAttributeRow.label}` : 'جدول مقادیر ویژگی'"
    subtitle="مقادیر قابل تولید برای این ویژگی"
  >
    <template v-if="activeVariantAttributeRow">
      <div class="variant-values-head">
        <small class="muted">{{ activeVariantAttributeRow.name }}</small>
        <a class="secondary-btn mini-link-btn" :href="activeAttributeDocUrl" target="_blank" rel="noreferrer">مشاهده در ERP</a>
      </div>

      <div class="variant-editor-table-wrap">
        <table class="variant-values-table">
          <thead>
            <tr>
              <th>تولید Variant</th>
              <th>مقدار</th>
              <th>abbr</th>
              <th>پیش‌فرض</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="valueRow in activeVariantAttributeRow.values" :key="`value-table-${activeVariantAttributeRow.name}-${valueRow.value}`">
              <td>
                <input
                  type="checkbox"
                  :checked="activeAttributeSelectedValues.includes(valueRow.value)"
                  @change="toggleGeneratedValue(activeVariantAttributeRow.name, valueRow.value)"
                />
              </td>
              <td>{{ valueRow.value }}</td>
              <td>
                <input
                  class="input mini-abbr"
                  :value="valueRow.abbr"
                  @input="valueRow.abbr = String($event.target.value || '').trim()"
                  placeholder="abbr"
                />
              </td>
              <td>
                <input
                  type="radio"
                  :name="`default-${activeVariantAttributeRow.name}`"
                  :checked="Number(valueRow.is_default || 0) === 1"
                  @change="updateAttributeDefault(activeVariantAttributeRow.name, valueRow.value)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="variant-value-mobile-list">
        <article
          v-for="valueRow in activeVariantAttributeRow.values"
          :key="`value-mobile-${activeVariantAttributeRow.name}-${valueRow.value}`"
          class="variant-value-mobile-card"
        >
          <strong>{{ valueRow.value }}</strong>
          <label class="check">
            <input
              type="checkbox"
              :checked="activeAttributeSelectedValues.includes(valueRow.value)"
              @change="toggleGeneratedValue(activeVariantAttributeRow.name, valueRow.value)"
            />
            تولید Variant
          </label>
          <label>
            abbr
            <input
              class="input mini-abbr"
              :value="valueRow.abbr"
              @input="valueRow.abbr = String($event.target.value || '').trim()"
              placeholder="abbr"
            />
          </label>
          <label class="check">
            <input
              type="radio"
              :name="`default-mobile-${activeVariantAttributeRow.name}`"
              :checked="Number(valueRow.is_default || 0) === 1"
              @change="updateAttributeDefault(activeVariantAttributeRow.name, valueRow.value)"
            />
            مقدار پیش‌فرض
          </label>
        </article>
      </div>
    </template>
    <p v-else class="muted">ویژگی معتبری انتخاب نشده است.</p>

    <template #footer>
      <div class="popup-actions">
        <button class="secondary-btn" type="button" @click="attributeValuesDialogOpen = false">بستن</button>
      </div>
    </template>
  </ManagementPopup>

  <ManagementPopup
    v-model:open="variantCreationDialogOpen"
    title="ساخت متغیر از محصول"
    subtitle="برای هر ویژگی می‌توانید یک مقدار مشخص کنید یا خالی بگذارید"
    :close-on-backdrop="!variantBuilderGenerating"
    :close-on-escape="!variantBuilderGenerating"
  >
    <div class="variant-creation-form">
      <p class="info-box">
        💡 در حالت «ساخت گروهی»، اگر مقداری برای یک ویژگی انتخاب نکنید، همه مقادیر آن ویژگی در نظر گرفته می‌شود.
      </p>

      <label class="check">
        <input type="checkbox" v-model="variantCreationForm.create_multiple" />
        ساخت گروهی Variant
      </label>

      <template v-if="!variantCreationForm.create_multiple">
        <div class="variant-attributes-grid">
          <label v-for="attr in variantCreationAttributes" :key="`single-create-${attr.name}`">
            {{ attr.label }}
            <SearchableDropdown
              v-model="variantCreationForm.attributes[attr.name]"
              :options="(attr.values || []).map(v => ({ value: v.value, label: v.value }))"
              :placeholder="`انتخاب ${attr.label}`"
              search-placeholder="جستجو..."
              :include-empty-option="!variantCreationForm.create_multiple"
              empty-label="انتخاب مقدار"
              :multiple="variantCreationForm.create_multiple"
              allow-create
              @create-option="addVariantCreationOption(attr.name, $event)"
            />
            <small class="hint">برای ساخت تکی، مقدار {{ attr.label }} را انتخاب کنید.</small>
          </label>
        </div>
      </template>

      <template v-else>
        <p class="muted">برای محدود کردن خروجی، می‌توانید فقط بعضی ویژگی‌ها را مقداردهی کنید.</p>
        <div class="variant-attributes-grid">
          <label v-for="attr in variantCreationAttributes" :key="`batch-create-${attr.name}`">
            {{ attr.label }}
            <SearchableDropdown
              v-model="variantCreationForm.attributes[attr.name]"
              :options="(attr.values || []).map(v => ({ value: v.value, label: v.value }))"
              :placeholder="`فیلتر ${attr.label}`"
              search-placeholder="جستجو..."
              :include-empty-option="!variantCreationForm.create_multiple"
              empty-label="همه مقادیر"
              :multiple="variantCreationForm.create_multiple"
              allow-create
              @create-option="addVariantCreationOption(attr.name, $event)"
            />
            <small class="hint">خالی = همه مقادیر {{ attr.label }}</small>
          </label>
        </div>
        <p class="muted">
          مثال: اگر فقط «نوع شیر = نارگیل» بزنید و «چربی» را خالی بگذارید، همه Variantهای نارگیل ساخته می‌شود.
        </p>
      </template>
    </div>

    <p class="error" v-if="variantBuilderError">{{ variantBuilderError }}</p>
    <p class="success" v-if="variantBuilderSuccess">{{ variantBuilderSuccess }}</p>

    <template #footer>
      <div class="popup-actions">
        <button class="secondary-btn" type="button" :disabled="variantBuilderGenerating" @click="closeVariantCreationDialog">انصراف</button>
        <button class="primary-btn" type="button" :disabled="variantBuilderGenerating" @click="createVariantsFromDialog">
          {{ variantBuilderGenerating ? 'در حال ساخت...' : variantCreationForm.create_multiple ? 'ساخت گروهی' : 'ساخت محصول' }}
        </button>
      </div>
    </template>
  </ManagementPopup>

  <ManagementPopup
    v-model:open="showAddAttributeDialog"
    title="افزودن ویژگی به محصول"
    subtitle="انتخاب ویژگی از لیست موجود"
    size="lg"
  >
    <div class="add-attribute-form">
      <p class="muted">ویژگی‌های زیر هنوز به این محصول اضافه نشده‌اند:</p>
      <label>
        انتخاب ویژگی
        <SearchableDropdown
          v-model="selectedNewAttribute"
          :options="inactiveTemplateAttributes.map(a => ({ value: a.name, label: a.label }))"
          placeholder="انتخاب ویژگی"
          search-placeholder="جستجوی ویژگی..."
        />
        <small class="hint">ویژگی مورد نظر را انتخاب کنید</small>
      </label>
    </div>

    <template #footer>
      <div class="popup-actions">
        <button class="secondary-btn" type="button" @click="showAddAttributeDialog = false">انصراف</button>
        <button class="primary-btn" type="button" :disabled="!selectedNewAttribute" @click="addAttributeToTemplate">
          افزودن ویژگی
        </button>
      </div>
    </template>
  </ManagementPopup>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import MenuProductCard from '@/components/MenuProductCard.vue'
import ManagementImageUploaderView from '@/components/management/ManagementImageUploaderView.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ReportChartRenderer from '@/components/management/bi/ReportChartRenderer.vue'
import ReportInsightCards from '@/components/management/bi/ReportInsightCards.vue'
import ReportKpiGrid from '@/components/management/bi/ReportKpiGrid.vue'
import {
  deleteManagementProduct,
  deleteManagementItemImageByUrl,
  generateManagementProductVariants,
  getManagementProductVariantBuilder,
  getManagementProductDetail,
  listManagementBoms,
  saveManagementProductVariantBuilder,
  setManagementDefaultPriceList,
  setManagementProductPrice,
  uploadManagementItemImage,
  updateManagementProductSettings,
} from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const query = parseQuery()
const PREVIEW_COMPACT_QUERY = '(max-width: 980px)'
const itemName = ref(String(query.item_name || query.item || props.boot?.item_name || '').trim())
const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 29)

const filters = reactive({
  date_from: start.toISOString().slice(0, 10),
  date_to: today.toISOString().slice(0, 10),
})

const loading = ref(false)
const error = ref('')
const detail = ref(null)
const selectedImage = ref('')
const selectedDefaultPriceList = ref('')
const activeTab = ref(readStoredDetailTab())
const savingSettings = ref(false)
const savingDefaultPriceList = ref(false)
const savingPrice = ref(false)
const mediaUploading = ref(false)
const mediaSaving = ref(false)
const mediaError = ref('')
const mediaSuccess = ref('')
const bomLoading = ref(false)
const bomError = ref('')
const productBoms = ref([])
const settingsSnapshot = ref('')
const variantBuilderLoading = ref(false)
const variantBuilderSaving = ref(false)
const variantBuilderGenerating = ref(false)
const variantBuilderError = ref('')
const variantBuilderSuccess = ref('')
const deletingProduct = ref(false)
const variantBuilder = ref(null)
const variantAttributesDraft = ref([])
const selectedTemplateAttributes = ref([])
const selectedValuesByAttribute = ref({})
const activeVariantAttributeName = ref('')
const variantBuilderLoadedKey = ref('')
const previewModalOpen = ref(false)
const previewModalItem = ref(null)
const isCompactViewport = ref(false)
let compactPreviewMedia = null
let compactPreviewMediaListener = null
const attributeValuesDialogOpen = ref(false)
const variantCreationDialogOpen = ref(false)
const variantCreationForm = ref({
  attributes: {},
  create_multiple: false,
})
const showAddAttributeDialog = ref(false)
const selectedNewAttribute = ref('')

const settingsForm = reactive({
  item_code: '',
  item_name: '',
  custom_snapp_code: '',
  item_group: '',
  stock_uom: '',
  description: '',
  restaurant_slug: '',
  restaurant_short_desc: '',
  restaurant_long_desc: '',
  restaurant_category: '',
  restaurant_subcategory: '',
  restaurant_branch: '',
  image: '',
  website_image: '',
  restaurant_prep_time_mins: 0,
  restaurant_sort_order: 0,
  restaurant_auto_add_qty: 0,
  restaurant_nutrition_kcal: 0,
  restaurant_nutrition_protein_g: 0,
  restaurant_nutrition_carb_g: 0,
  restaurant_nutrition_sugar_g: 0,
  restaurant_nutrition_fat_g: 0,
  show_in_print: false,
  restaurant_enabled: false,
  restaurant_is_featured: false,
  restaurant_is_best_seller: false,
  restaurant_requires_bom: false,
  restaurant_auto_add_to_order: false,
  disabled: false,
})

const priceForm = reactive({
  price_list: '',
  price_list_rate: 0,
  valid_from: '',
})

const tabOptions = [
  { value: 'overview', label: 'اطلاعات اولیه' },
  { value: 'settings', label: 'تنظیمات و قیمت' },
  { value: 'variants', label: 'ویژگی و وریانت' },
  { value: 'reports', label: 'گزارش‌ها' },
]

const bomColumns = [
  { key: 'name', label: 'BOM' },
  { key: 'quantity', label: 'تعداد' },
  { key: 'status', label: 'وضعیت' },
  { key: 'modified', label: 'آخرین بروزرسانی' },
  { key: 'actions', label: 'عملیات' },
]

const pageTitle = computed(() => detail.value?.item?.item_name || 'جزئیات محصول')
const pageSubtitle = computed(() => detail.value?.item?.item_name || '')
const productBomItemCode = computed(() => {
  const item = detail.value?.item || {}
  return String(item.name || item.item_code || '').trim()
})
const productBomPageUrl = computed(() => {
  const itemCode = encodeURIComponent(String(productBomItemCode.value || '').trim())
  if (!itemCode) {
    return '/management/boms'
  }
  return `/management/boms?item=${itemCode}`
})
const defaultBomName = computed(() => {
  const fromItem = String(detail.value?.item?.default_bom || '').trim()
  if (fromItem) {
    return fromItem
  }
  const fromList = (productBoms.value || []).find((row) => Number(row?.is_default || 0))
  return String(fromList?.name || '').trim()
})
const activeBomName = computed(() => {
  const fromItem = String(detail.value?.item?.bom_no || '').trim()
  if (fromItem) {
    return fromItem
  }
  const fromList = (productBoms.value || []).find((row) => Number(row?.is_active || 0))
  return String(fromList?.name || '').trim()
})
const priceLists = computed(() => detail.value?.pricing?.price_lists || [])
const activeCurrency = computed(() => detail.value?.report?.currency || 'IRR')
const priceListOptions = computed(() =>
  priceLists.value.map((row) => ({
    value: row.name,
    label: `${row.title} (${row.currency || activeCurrency.value})`,
  })),
)
const currentPriceRate = computed(() => Number(detail.value?.pricing?.current_price?.price_list_rate || 0))
const latestPriceRate = computed(() => Number(detail.value?.pricing?.latest_price?.price_list_rate || 0))
const latestPriceDate = computed(() => detail.value?.pricing?.latest_price?.effective_at || '')
const activeTabHint = computed(() => {
  if (activeTab.value === 'reports') {
    return 'نمودارها، KPI و جدول تحلیل فروش این محصول در این تب نمایش داده می‌شود.'
  }
  if (activeTab.value === 'variants') {
    return 'مدیریت Item Attribute، تعیین ویژگی‌های انتخابی مشتری و ساخت خودکار Variantها.'
  }
  if (activeTab.value === 'settings') {
    return 'تنظیمات رستورانی، وب‌سایت و قیمت‌گذاری را از این بخش مدیریت کنید.'
  }
  return 'مشخصات پایه محصول و تصاویر را در این بخش ویرایش کنید.'
})
const canSaveSettings = computed(() => !savingSettings.value && !loading.value && hasUnsavedChanges.value && !!detail.value?.item?.name)
const hasReportData = computed(() => {
  const report = detail.value?.report || {}
  return (
    Number(report?.kpis?.length || 0) > 0 ||
    Number(report?.charts?.length || 0) > 0 ||
    Number(report?.tables?.length || 0) > 0 ||
    Number(report?.insights?.length || 0) > 0
  )
})
const localizedReport = computed(() => {
  const report = detail.value?.report || {}
  return {
    kpis: (report.kpis || []).map((kpi) => ({
      ...kpi,
      label: localizeText(kpi.label || kpi.key),
      change_label: localizeText(kpi.change_label),
    })),
    charts: (report.charts || []).map((chart) => ({
      ...chart,
      title: localizeText(chart.title || chart.key || 'نمودار'),
      subtitle: localizeText(chart.subtitle),
      labels: Array.isArray(chart.labels) ? chart.labels.map((label) => localizeAxisLabel(label)) : [],
      series: Array.isArray(chart.series)
        ? chart.series.map((row) => ({
            ...row,
            label: localizeText(row.label || row.key),
          }))
        : [],
    })),
    tables: (report.tables || []).map((table) => ({
      ...table,
      title: localizeText(table.title || table.key || 'جدول'),
      subtitle: localizeText(table.subtitle),
      columns: (table.columns || []).map((column) => ({
        ...column,
        label: localizeText(column.label || column.key),
      })),
    })),
    insights: (report.insights || []).map((item) => ({
      ...item,
      text: localizeText(item.text),
    })),
  }
})
const galleryImages = computed(() => detail.value?.media?.gallery || [])
const mainImage = computed(() => selectedImage.value || detail.value?.media?.main_image || '')
const mediaItems = computed(() => {
  const urls = []
  const pushUrl = (value) => {
    const normalized = String(value || '').trim()
    if (normalized) {
      urls.push(normalized)
    }
  }

  pushUrl(settingsForm.image)
  pushUrl(settingsForm.website_image)
  for (const row of galleryImages.value) {
    pushUrl(row)
  }

  const seen = new Set()
  const deduplicated = []
  for (const url of urls) {
    if (seen.has(url)) {
      continue
    }
    seen.add(url)
    deduplicated.push(url)
  }

  return deduplicated.map((url) => ({
    url,
    isCover: url === String(settingsForm.image || '').trim(),
    isSecondary: url === String(settingsForm.website_image || '').trim(),
  }))
})
const fieldOptions = computed(() => {
  const payload = detail.value?.field_options || {}
  return {
    uoms: payload.uoms || [],
    item_groups: payload.item_groups || [],
    categories: payload.categories || [],
    subcategories: payload.subcategories || [],
    branches: payload.branches || [],
  }
})
const filteredSubcategoryOptions = computed(() => {
  const rows = fieldOptions.value?.subcategories || []
  const category = String(settingsForm.restaurant_category || '').trim()
  if (!category) {
    return rows
  }
  return rows.filter((row) => String(row.category || '').trim() === category)
})

const variantTemplate = computed(() => variantBuilder.value?.template || {})
const resolvedTemplateName = computed(() => {
  const fromBuilder = String(variantTemplate.value?.name || '').trim()
  if (fromBuilder) {
    return fromBuilder
  }
  return String(detail.value?.item?.variant_of || detail.value?.item?.name || '').trim()
})
const resolvedTemplateLabel = computed(() => {
  const fromBuilder = String(variantTemplate.value?.item_name || '').trim()
  if (fromBuilder) {
    return fromBuilder
  }
  return String(detail.value?.item?.variant_of_item_name || detail.value?.item?.variant_of || detail.value?.item?.item_name || '').trim()
})
const isVariantContext = computed(() => {
  const currentItem = String(detail.value?.item?.name || '').trim()
  const templateItem = String(resolvedTemplateName.value || '').trim()
  return Boolean(currentItem && templateItem && currentItem !== templateItem)
})
const hasVariantFeatureEnabled = computed(() => {
  const fromBuilder = Number(variantTemplate.value?.has_variants || 0)
  if (fromBuilder === 1) {
    return true
  }
  return Number(detail.value?.item?.has_variants || 0) === 1
})
const selectedTemplateAttributeCount = computed(() => selectedTemplateAttributes.value.length)
const variantRows = computed(() => (Array.isArray(variantBuilder.value?.variants) ? variantBuilder.value.variants : []))
const activeTemplateAttributes = computed(() => {
  return variantAttributesDraft.value.filter(attr => selectedTemplateAttributes.value.includes(attr.name))
})
const inactiveTemplateAttributes = computed(() => {
  return variantAttributesDraft.value.filter(attr => !selectedTemplateAttributes.value.includes(attr.name))
})
const variantCreationAttributes = computed(() => activeTemplateAttributes.value)
const currentVariantRow = computed(() => {
  const currentName = String(detail.value?.item?.name || '').trim()
  if (!currentName) {
    return null
  }
  return variantRows.value.find((row) => String(row?.name || '').trim() === currentName) || null
})
const currentVariantAttributeRows = computed(() => {
  const rows = Array.isArray(currentVariantRow.value?.attributes) ? currentVariantRow.value.attributes : []
  return rows.map((row, index) => ({
    index: index + 1,
    attribute: String(row?.attribute || '').trim(),
    value: String(row?.value || '').trim(),
  }))
})
const activeVariantAttributeRow = computed(() => {
  const activeName = String(activeVariantAttributeName.value || '').trim()
  if (!activeName) {
    return null
  }
  return variantAttributesDraft.value.find((row) => row.name === activeName) || null
})
const activeAttributeSelectedValues = computed(() => {
  const activeName = String(activeVariantAttributeName.value || '').trim()
  if (!activeName) {
    return []
  }
  return Array.isArray(selectedValuesByAttribute.value[activeName]) ? selectedValuesByAttribute.value[activeName] : []
})
const activeAttributeDocUrl = computed(() => itemAttributeDocUrl(activeVariantAttributeName.value))
const menuDisplayRows = computed(() => {
  const rows = Array.isArray(variantBuilder.value?.menu_display) ? variantBuilder.value.menu_display : []
  if (rows.length) {
    return rows
  }
  if (!detail.value?.item?.name) {
    return []
  }
  return [
    {
      name: detail.value.item.name,
      title: detail.value.item.item_name || detail.value.item.name,
      slug: detail.value.item.restaurant_slug || '',
      fixed_attributes: {},
    },
  ]
})
const previewMenuCardRows = computed(() => {
  const item = detail.value?.item || {}
  const categoryLabel =
    (fieldOptions.value?.categories || []).find((row) => String(row?.value || '').trim() === String(settingsForm.restaurant_category || '').trim())?.label ||
    settingsForm.restaurant_category ||
    'منو'
  const shortDesc = String(settingsForm.restaurant_short_desc || item.restaurant_short_desc || '').trim()
  const image = String(settingsForm.website_image || settingsForm.image || item.website_image || item.image || '').trim()
  const basePrice = Number(item.restaurant_base_price || item.standard_rate || 0)

  return menuDisplayRows.value.map((row, index) => ({
    ...row,
    name: String(row?.name || item.name || `preview-${index + 1}`).trim(),
    title: String(row?.title || item.item_name || item.name || '-').trim(),
    slug: String(row?.slug || settingsForm.restaurant_slug || item.restaurant_slug || '').trim(),
    short_desc: shortDesc,
    long_desc: String(settingsForm.restaurant_long_desc || settingsForm.description || item.restaurant_long_desc || '').trim(),
    image,
    base_price: basePrice,
    category_title: String(categoryLabel || 'منو').trim(),
    subcategory_title:
      (fieldOptions.value?.subcategories || []).find((sub) => String(sub?.value || '').trim() === String(settingsForm.restaurant_subcategory || '').trim())?.label ||
      settingsForm.restaurant_subcategory ||
      '',
    prep_time_mins: Number(settingsForm.restaurant_prep_time_mins || item.restaurant_prep_time_mins || 0),
    nutrition_kcal: Number(settingsForm.restaurant_nutrition_kcal || item.restaurant_nutrition_kcal || 0),
    nutrition_protein_g: Number(settingsForm.restaurant_nutrition_protein_g || item.restaurant_nutrition_protein_g || 0),
    nutrition_carb_g: Number(settingsForm.restaurant_nutrition_carb_g || item.restaurant_nutrition_carb_g || 0),
    nutrition_sugar_g: Number(settingsForm.restaurant_nutrition_sugar_g || item.restaurant_nutrition_sugar_g || 0),
  }))
})
const customerPreviewUrl = computed(() => {
  const slug = String(previewModalItem.value?.slug || '').trim()
  if (!slug) {
    return ''
  }
  const params = new URLSearchParams()
  const branch = String(settingsForm.restaurant_branch || '').trim()
  if (branch) {
    params.set('branch', branch)
  }
  const query = params.toString()
  return `/item/${encodeURIComponent(slug)}${query ? `?${query}` : ''}`
})

function openPreviewCard(row) {
  previewModalItem.value = row ? { ...row } : null
  previewModalOpen.value = Boolean(previewModalItem.value)
}

const hasUnsavedChanges = computed(() => {
  if (!detail.value?.item?.name || !settingsSnapshot.value) {
    return false
  }
  return serializeSettingsState() !== settingsSnapshot.value
})

watch(
  () => settingsForm.restaurant_category,
  () => {
    const currentSubcategory = String(settingsForm.restaurant_subcategory || '').trim()
    if (!currentSubcategory) {
      return
    }
    const valid = filteredSubcategoryOptions.value.some((row) => row.value === currentSubcategory)
    if (!valid) {
      settingsForm.restaurant_subcategory = ''
    }
  },
)

watch(
  () => activeTab.value,
  async (nextTab) => {
    try {
      localStorage.setItem('management-product-detail-tab', nextTab)
    } catch (storageError) {
      // Ignore storage failures.
    }
    if (nextTab === 'variants') {
      await loadVariantBuilder()
    }
  },
)

watch(
  () => variantAttributesDraft.value,
  (rows) => {
    const activeName = String(activeVariantAttributeName.value || '').trim()
    if (rows.some((row) => row.name === activeName)) {
      return
    }
    const preferred = selectedTemplateAttributes.value[0] || ''
    activeVariantAttributeName.value = String(preferred || '').trim()
  },
  { deep: true },
)

watch(
  () => activeVariantAttributeRow.value,
  (row) => {
    if (row) {
      return
    }
    attributeValuesDialogOpen.value = false
  },
)

watch(
  () => variantCreationForm.value.create_multiple,
  (isMultiple) => {
    if (!variantCreationDialogOpen.value) {
      return
    }
    const nextAttributes = { ...(variantCreationForm.value.attributes || {}) }
    for (const attr of variantCreationAttributes.value) {
      const key = String(attr?.name || '').trim()
      if (!key) {
        continue
      }
      nextAttributes[key] = normalizeVariantCreationAttributeValue(nextAttributes[key], isMultiple)
    }
    variantCreationForm.value = {
      ...variantCreationForm.value,
      attributes: nextAttributes,
    }
  },
)

function syncForms(payload) {
  const item = payload?.item || {}
  settingsForm.item_code = item.item_code || ''
  settingsForm.item_name = item.item_name || ''
  settingsForm.custom_snapp_code = item.custom_snapp_code || ''
  settingsForm.item_group = item.item_group || ''
  settingsForm.stock_uom = item.stock_uom || ''
  settingsForm.description = item.description || ''
  settingsForm.restaurant_slug = item.restaurant_slug || ''
  settingsForm.restaurant_short_desc = item.short_description || ''
  settingsForm.restaurant_long_desc = item.long_description || ''
  settingsForm.restaurant_category = item.restaurant_category || ''
  settingsForm.restaurant_subcategory = item.restaurant_subcategory || ''
  settingsForm.restaurant_branch = item.restaurant_branch || ''
  settingsForm.image = item.image || ''
  settingsForm.website_image = item.website_image || ''
  settingsForm.restaurant_prep_time_mins = Number(item.restaurant_prep_time_mins || 0)
  settingsForm.restaurant_sort_order = Number(item.restaurant_sort_order || 0)
  settingsForm.restaurant_auto_add_qty = Number(item.restaurant_auto_add_qty || 0)
  settingsForm.restaurant_nutrition_kcal = Number(item.restaurant_nutrition_kcal || item.nutrition?.kcal || 0)
  settingsForm.restaurant_nutrition_protein_g = Number(item.restaurant_nutrition_protein_g || item.nutrition?.protein_g || 0)
  settingsForm.restaurant_nutrition_carb_g = Number(item.restaurant_nutrition_carb_g || item.nutrition?.carb_g || 0)
  settingsForm.restaurant_nutrition_sugar_g = Number(item.restaurant_nutrition_sugar_g || item.nutrition?.sugar_g || 0)
  settingsForm.restaurant_nutrition_fat_g = Number(item.restaurant_nutrition_fat_g || item.nutrition?.fat_g || 0)
  settingsForm.show_in_print = Number(item.show_in_print ?? item.show_in_website ?? 0) === 1
  settingsForm.restaurant_enabled = Number(item.restaurant_enabled || 0) === 1
  settingsForm.restaurant_is_featured = Number(item.restaurant_is_featured || 0) === 1
  settingsForm.restaurant_is_best_seller = Number(item.restaurant_is_best_seller || 0) === 1
  settingsForm.restaurant_requires_bom = Number(item.restaurant_requires_bom || 0) === 1
  settingsForm.restaurant_auto_add_to_order = Number(item.restaurant_auto_add_to_order || 0) === 1
  settingsForm.disabled = Number(item.disabled || 0) === 1

  selectedDefaultPriceList.value = payload?.pricing?.default_price_list || ''
  priceForm.price_list = payload?.pricing?.default_price_list || priceLists.value?.[0]?.name || ''
  priceForm.price_list_rate = Number(payload?.pricing?.current_price?.price_list_rate || item.base_price || 0)
  priceForm.valid_from = ''
  selectedImage.value = payload?.media?.main_image || ''
  settingsSnapshot.value = serializeSettingsState()
}

function normalizeVariantAttributesDraft(attributes = []) {
  const rows = []
  for (const row of attributes || []) {
    const name = String(row?.name || '').trim()
    if (!name) {
      continue
    }
    const values = Array.isArray(row?.values)
      ? row.values.map((valueRow) => ({
          value: String(valueRow?.value || '').trim(),
          abbr: String(valueRow?.abbr || '').trim(),
          sort_order: Number(valueRow?.sort_order || 0),
          is_default: Number(valueRow?.is_default || 0) ? 1 : 0,
        }))
      : []
    rows.push({
      name,
      label: String(row?.label || name).trim(),
      selected_on_template: Number(row?.selected_on_template || 0) ? 1 : 0,
      show_in_website: row?.show_in_website === undefined ? 1 : Number(row?.show_in_website || 0),
      selection_only: Number(row?.selection_only || 0),
      disabled: Number(row?.disabled || 0),
      values,
    })
  }
  return rows
}

function resolveTemplateAttributeSelection(attributes = [], templateAttributes = []) {
  const availableNames = new Set(attributes.map((row) => row.name))
  const fromPayload = Array.isArray(templateAttributes)
    ? templateAttributes
        .map((value) => String(value || '').trim())
        .filter((value) => value && availableNames.has(value))
    : []
  const fromRows = attributes
    .filter((row) => Number(row?.selected_on_template || 0) === 1)
    .map((row) => row.name)

  return Array.from(new Set((fromPayload.length ? fromPayload : fromRows).filter(Boolean)))
}

function resetVariantBuilderState(payload) {
  const attributes = normalizeVariantAttributesDraft(payload?.attributes || [])
  const selectedAttributes = resolveTemplateAttributeSelection(attributes, payload?.template_attributes)
  variantBuilder.value = payload || null
  variantAttributesDraft.value = attributes
  selectedTemplateAttributes.value = selectedAttributes

  const byAttribute = {}
  for (const row of attributes) {
    if (!selectedAttributes.includes(row.name)) {
      continue
    }
    byAttribute[row.name] = (row.values || []).map((valueRow) => valueRow.value).filter(Boolean)
  }
  selectedValuesByAttribute.value = byAttribute
  const preferredActive = selectedAttributes[0] || ''
  activeVariantAttributeName.value = String(preferredActive || '').trim()
}

async function loadVariantBuilder({ force = false } = {}) {
  const targetItem = String(detail.value?.item?.name || itemName.value || '').trim()
  if (!targetItem) {
    variantBuilder.value = null
    variantAttributesDraft.value = []
    selectedTemplateAttributes.value = []
    selectedValuesByAttribute.value = {}
    activeVariantAttributeName.value = ''
    variantBuilderLoadedKey.value = ''
    return
  }
  if (!force && variantBuilderLoadedKey.value === targetItem && variantBuilder.value) {
    return
  }
  variantBuilderLoading.value = true
  variantBuilderError.value = ''
  try {
    const payload = await getManagementProductVariantBuilder({ item_name: targetItem })
    resetVariantBuilderState(payload)
    variantBuilderLoadedKey.value = targetItem
  } catch (builderErr) {
    variantBuilder.value = null
    variantAttributesDraft.value = []
    selectedTemplateAttributes.value = []
    selectedValuesByAttribute.value = {}
    activeVariantAttributeName.value = ''
    variantBuilderLoadedKey.value = ''
    variantBuilderError.value = builderErr.message || 'دریافت تنظیمات وریانت ناموفق بود.'
  } finally {
    variantBuilderLoading.value = false
  }
}

async function loadDetail() {
  if (!itemName.value) {
    error.value = 'شناسه محصول ارسال نشده است.'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const payload = await getManagementProductDetail({
      item_name: itemName.value,
      date_from: filters.date_from,
      date_to: filters.date_to,
    })
    detail.value = payload
    variantBuilderLoadedKey.value = ''
    syncForms(payload)
    await loadProductBoms(payload?.item?.name || payload?.item?.item_code || '')
    if (activeTab.value === 'variants') {
      await loadVariantBuilder({ force: true })
    }
  } catch (errObj) {
    error.value = errObj.message || 'بارگذاری جزئیات محصول ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function loadProductBoms(itemCode = '') {
  const normalizedItem = String(itemCode || '').trim()
  if (!normalizedItem) {
    productBoms.value = []
    bomError.value = ''
    return
  }

  bomLoading.value = true
  bomError.value = ''
  try {
    const rows = await listManagementBoms({
      item_code: normalizedItem,
      limit: 80,
    })
    productBoms.value = Array.isArray(rows) ? rows : []
  } catch (bomErr) {
    bomError.value = bomErr.message || 'دریافت لیست BOM ناموفق بود.'
    productBoms.value = []
  } finally {
    bomLoading.value = false
  }
}

async function saveSettings() {
  if (!detail.value?.item?.name || !hasUnsavedChanges.value) {
    return
  }
  savingSettings.value = true
  error.value = ''
  try {
    const payload = await updateManagementProductSettings(buildSettingsPayload())
    detail.value = payload
    itemName.value = String(payload?.item?.name || payload?.item?.item_code || itemName.value || '').trim()
    syncItemQueryInUrl(itemName.value)
    variantBuilderLoadedKey.value = ''
    syncForms(payload)
    await loadProductBoms(payload?.item?.name || payload?.item?.item_code || '')
    if (activeTab.value === 'variants') {
      await loadVariantBuilder({ force: true })
    }
  } catch (errObj) {
    error.value = errObj.message || 'ذخیره تنظیمات محصول ناموفق بود.'
  } finally {
    savingSettings.value = false
  }
}

async function saveDefaultPriceList() {
  if (!selectedDefaultPriceList.value) {
    return
  }
  savingDefaultPriceList.value = true
  error.value = ''
  try {
    await setManagementDefaultPriceList(selectedDefaultPriceList.value)
    await loadDetail()
  } catch (errObj) {
    error.value = errObj.message || 'تنظیم لیست قیمت پیش‌فرض ناموفق بود.'
  } finally {
    savingDefaultPriceList.value = false
  }
}

async function savePrice() {
  if (!detail.value?.item?.name) {
    return
  }
  savingPrice.value = true
  error.value = ''
  try {
    await setManagementProductPrice({
      item_name: detail.value.item.name,
      price_list: priceForm.price_list,
      price_list_rate: Number(priceForm.price_list_rate || 0),
      valid_from: priceForm.valid_from || '',
    })
    await loadDetail()
  } catch (errObj) {
    error.value = errObj.message || 'ثبت قیمت محصول ناموفق بود.'
  } finally {
    savingPrice.value = false
  }
}

async function deleteProduct() {
  const itemDocName = String(detail.value?.item?.name || '').trim()
  if (!itemDocName || deletingProduct.value) {
    return
  }

  const itemLabel =
    String(settingsForm.item_name || '').trim() ||
    String(settingsForm.item_code || '').trim() ||
    itemDocName
  const confirmed = window.confirm(
    `آیا مطمئن هستید که می‌خواهید کالای «${itemLabel}» را حذف کنید؟`,
  )
  if (!confirmed) {
    return
  }

  deletingProduct.value = true
  error.value = ''
  try {
    await deleteManagementProduct(itemDocName, { allow_archive_on_link: 0, force_delete: 0 })
    window.alert(`✅ کالای «${itemLabel}» با موفقیت حذف شد.`)
    window.location.href = '/management/products'
  } catch (errObj) {
    if (isLinkedDeleteError(errObj)) {
      const disableConfirmed = window.confirm(
        `❌ این کالا به اسناد فروش یا انبار متصل است و قابل حذف نیست.\n\n✅ پیشنهاد: می‌توانید آن را غیرفعال کنید تا در منو نمایش داده نشود.\n\nآیا می‌خواهید کالای «${itemLabel}» را غیرفعال کنید؟`,
      )
      if (!disableConfirmed) {
        return
      }
      try {
        await deleteManagementProduct(itemDocName, { allow_archive_on_link: 1, force_delete: 0 })
        window.alert(`✅ کالای «${itemLabel}» غیرفعال شد و دیگر در منو نمایش داده نمی‌شود.`)
        window.location.href = '/management/products'
      } catch (archiveErr) {
        error.value = archiveErr.message || `❌ متأسفانه غیرفعال‌سازی کالای «${itemLabel}» ناموفق بود. لطفاً دوباره تلاش کنید.`
      }
      return
    }
    error.value = errObj.message || `❌ متأسفانه حذف کالای «${itemLabel}» ناموفق بود. لطفاً دوباره تلاش کنید.`
  } finally {
    deletingProduct.value = false
  }
}

function isLinkedDeleteError(errorObj) {
  const message = String(errorObj?.message || '')
  return /(disable this item|linked|link exists|cannot delete|وابسته|مرتبط|reference|dependent)/i.test(message)
}

function openAttributeEditor(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return
  }
  activeVariantAttributeName.value = normalized
  attributeValuesDialogOpen.value = true
}

function itemAttributeDocUrl(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return '/app/item-attribute'
  }
  return `/app/item-attribute/${encodeURIComponent(normalized)}`
}

function countSelectedValues(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return 0
  }
  const rows = selectedValuesByAttribute.value[normalized]
  return Array.isArray(rows) ? rows.length : 0
}

function updateAttributeDefault(attributeName, valueName) {
  const normalizedAttr = String(attributeName || '').trim()
  const normalizedValue = String(valueName || '').trim()
  if (!normalizedAttr || !normalizedValue) {
    return
  }
  variantAttributesDraft.value = variantAttributesDraft.value.map((row) => {
    if (row.name !== normalizedAttr) {
      return row
    }
    return {
      ...row,
      values: (row.values || []).map((valueRow) => ({
        ...valueRow,
        is_default: valueRow.value === normalizedValue ? 1 : 0,
      })),
    }
  })
}

function updateAttributeToggle(attributeName, fieldname, checked) {
  const normalizedAttr = String(attributeName || '').trim()
  variantAttributesDraft.value = variantAttributesDraft.value.map((row) =>
    row.name === normalizedAttr ? { ...row, [fieldname]: checked ? 1 : 0 } : row,
  )
}

function toggleGeneratedValue(attributeName, valueName) {
  const attrName = String(attributeName || '').trim()
  const normalizedValue = String(valueName || '').trim()
  if (!attrName || !normalizedValue) {
    return
  }
  const current = Array.isArray(selectedValuesByAttribute.value[attrName]) ? selectedValuesByAttribute.value[attrName] : []
  if (current.includes(normalizedValue)) {
    selectedValuesByAttribute.value = {
      ...selectedValuesByAttribute.value,
      [attrName]: current.filter((value) => value !== normalizedValue),
    }
    return
  }
  selectedValuesByAttribute.value = {
    ...selectedValuesByAttribute.value,
    [attrName]: [...current, normalizedValue],
  }
}

function buildVariantBuilderSavePayload() {
  const selectedSet = new Set(selectedTemplateAttributes.value.map((value) => String(value || '').trim()).filter(Boolean))
  const attributeSettings = variantAttributesDraft.value
    .filter((row) => selectedSet.has(row.name))
    .map((row) => ({
      name: row.name,
      show_in_website: Number(row.show_in_website || 0) ? 1 : 0,
      selection_only: Number(row.selection_only || 0) ? 1 : 0,
      values: (row.values || []).map((valueRow) => ({
        value: String(valueRow.value || '').trim(),
        abbr: String(valueRow.abbr || '').trim(),
        is_default: Number(valueRow.is_default || 0) ? 1 : 0,
      })),
    }))

  return {
    item_name: String(detail.value?.item?.name || itemName.value || '').trim(),
    selected_attributes: Array.from(selectedSet),
    attribute_settings: attributeSettings,
  }
}

async function saveVariantBuilder() {
  variantBuilderSaving.value = true
  variantBuilderError.value = ''
  variantBuilderSuccess.value = ''
  try {
    const payload = await saveManagementProductVariantBuilder(buildVariantBuilderSavePayload())
    resetVariantBuilderState(payload)
    variantBuilderSuccess.value = 'تنظیمات ویژگی‌ها ذخیره شد.'
  } catch (saveErr) {
    variantBuilderError.value = saveErr.message || 'ذخیره تنظیمات ویژگی‌ها ناموفق بود.'
  } finally {
    variantBuilderSaving.value = false
  }
}

async function generateVariantsFromBuilder() {
  variantBuilderGenerating.value = true
  variantBuilderError.value = ''
  variantBuilderSuccess.value = ''
  try {
    const payload = await generateManagementProductVariants({
      item_name: String(detail.value?.item?.name || itemName.value || '').trim(),
      selected_attributes: selectedTemplateAttributes.value,
      selected_values_by_attribute: selectedValuesByAttribute.value,
    })
    if (payload?.builder) {
      resetVariantBuilderState(payload.builder)
    }
    const createdCount = Number(payload?.created_count || 0)
    const existingCount = Number(payload?.existing_count || 0)
    variantBuilderSuccess.value = `ایجاد شد: ${createdCount.toLocaleString('fa-IR')} | موجود بود: ${existingCount.toLocaleString('fa-IR')}`
    await loadDetail()
  } catch (generateErr) {
    variantBuilderError.value = generateErr.message || 'ساخت وریانت‌ها ناموفق بود.'
  } finally {
    variantBuilderGenerating.value = false
  }
}

function openVariantCreationDialog() {
  variantCreationForm.value = {
    attributes: {},
    create_multiple: false,
  }

  for (const attr of variantCreationAttributes.value) {
    variantCreationForm.value.attributes[attr.name] = ''
  }

  variantCreationDialogOpen.value = true
}

function closeVariantCreationDialog() {
  variantCreationDialogOpen.value = false
}

function removeAttributeFromTemplate(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return
  }
  const attrLabel = variantAttributesDraft.value.find((row) => row.name === normalized)?.label || normalized
  const confirmed = window.confirm(`آیا مطمئن هستید که می‌خواهید ویژگی «${attrLabel}» را از این محصول حذف کنید؟`)
  if (!confirmed) {
    return
  }

  selectedTemplateAttributes.value = selectedTemplateAttributes.value.filter((name) => name !== normalized)
  const byAttribute = { ...selectedValuesByAttribute.value }
  delete byAttribute[normalized]
  selectedValuesByAttribute.value = byAttribute

  if (activeVariantAttributeName.value === normalized) {
    activeVariantAttributeName.value = selectedTemplateAttributes.value[0] || ''
  }
}

function addAttributeToTemplate() {
  const normalized = String(selectedNewAttribute.value || '').trim()
  if (!normalized) {
    return
  }

  if (!selectedTemplateAttributes.value.includes(normalized)) {
    selectedTemplateAttributes.value = [...selectedTemplateAttributes.value, normalized]

    const attr = variantAttributesDraft.value.find((row) => row.name === normalized)
    if (attr) {
      selectedValuesByAttribute.value = {
        ...selectedValuesByAttribute.value,
        [normalized]: (attr.values || []).map((row) => row.value),
      }
      activeVariantAttributeName.value = normalized
    }
  }

  showAddAttributeDialog.value = false
  selectedNewAttribute.value = ''
}

function normalizeVariantCreationAttributeValue(value, isMultiple) {
  if (isMultiple) {
    const source = Array.isArray(value) ? value : String(value || '').trim() ? [value] : []
    return source
      .map((entry) => String(entry || '').trim())
      .filter(Boolean)
      .filter((entry, index, rows) => rows.indexOf(entry) === index)
  }
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

function addVariantCreationOption(attributeName, createdValue) {
  const normalizedAttribute = String(attributeName || '').trim()
  const normalizedValue = String(createdValue || '').trim()
  if (!normalizedAttribute || !normalizedValue) {
    return
  }

  variantAttributesDraft.value = variantAttributesDraft.value.map((row) => {
    if (row.name !== normalizedAttribute) {
      return row
    }
    const hasValue = (row.values || []).some((valueRow) => String(valueRow?.value || '').trim() === normalizedValue)
    if (hasValue) {
      return row
    }
    return {
      ...row,
      values: [
        ...(row.values || []),
        {
          value: normalizedValue,
          abbr: normalizedValue,
          sort_order: Number((row.values || []).length + 1),
          is_default: 0,
        },
      ],
    }
  })

  const currentRaw = variantCreationForm.value.attributes?.[normalizedAttribute]
  const nextValue = normalizeVariantCreationAttributeValue(currentRaw, variantCreationForm.value.create_multiple)
  if (variantCreationForm.value.create_multiple) {
    const nextRows = Array.isArray(nextValue) ? nextValue : []
    if (!nextRows.includes(normalizedValue)) {
      nextRows.push(normalizedValue)
    }
    variantCreationForm.value = {
      ...variantCreationForm.value,
      attributes: {
        ...(variantCreationForm.value.attributes || {}),
        [normalizedAttribute]: nextRows,
      },
    }
    return
  }

  variantCreationForm.value = {
    ...variantCreationForm.value,
    attributes: {
      ...(variantCreationForm.value.attributes || {}),
      [normalizedAttribute]: normalizedValue,
    },
  }
}

async function createVariantsFromDialog() {
  const selectedAttrs = variantCreationAttributes.value.map((row) => row.name).filter(Boolean)
  if (!selectedAttrs.length) {
    variantBuilderError.value = 'ابتدا حداقل یک ویژگی را روی تمپلیت فعال کنید.'
    return
  }

  variantBuilderGenerating.value = true
  variantBuilderError.value = ''
  variantBuilderSuccess.value = ''

  try {
    const selectedVals = {}
    for (const attrName of selectedAttrs) {
      const normalized = normalizeVariantCreationAttributeValue(
        variantCreationForm.value.attributes?.[attrName],
        variantCreationForm.value.create_multiple,
      )
      if (variantCreationForm.value.create_multiple) {
        if (Array.isArray(normalized) && normalized.length) {
          selectedVals[attrName] = normalized
        }
        continue
      }
      if (normalized) {
        selectedVals[attrName] = [normalized]
      }
    }

    if (!variantCreationForm.value.create_multiple) {
      const missingAttributes = selectedAttrs.filter((attrName) => !selectedVals[attrName]?.length)
      if (missingAttributes.length) {
        const missingLabels = variantCreationAttributes.value
          .filter((row) => missingAttributes.includes(row.name))
          .map((row) => row.label || row.name)
        variantBuilderError.value = `برای ساخت تکی، مقدار این ویژگی‌ها الزامی است: ${missingLabels.join('، ')}`
        return
      }
    }

    const payload = await generateManagementProductVariants({
      item_name: String(detail.value?.item?.name || itemName.value || '').trim(),
      selected_attributes: selectedAttrs,
      selected_values_by_attribute: selectedVals,
    })

    if (payload?.builder) {
      resetVariantBuilderState(payload.builder)
    }

    const createdCount = Number(payload?.created_count || 0)
    const existingCount = Number(payload?.existing_count || 0)
    variantBuilderSuccess.value = `ایجاد شد: ${createdCount.toLocaleString('fa-IR')} | موجود بود: ${existingCount.toLocaleString('fa-IR')}`
    await loadDetail()
    closeVariantCreationDialog()
  } catch (generateErr) {
    variantBuilderError.value = generateErr.message || 'ساخت وریانت‌ها ناموفق بود.'
  } finally {
    variantBuilderGenerating.value = false
  }
}

function formatVariantAttributes(row = {}) {
  const rows = Array.isArray(row?.attributes) ? row.attributes : []
  if (!rows.length) {
    return '-'
  }
  return rows
    .map((attr) => {
      const attribute = String(attr?.attribute || '').trim()
      const value = String(attr?.value || '').trim()
      if (!attribute && !value) {
        return ''
      }
      if (!attribute) {
        return value
      }
      if (!value) {
        return attribute
      }
      return `${attribute}: ${value}`
    })
    .filter(Boolean)
    .join(' | ')
}

function selectImage(url) {
  selectedImage.value = String(url || '')
}

function clearMediaMessages() {
  mediaError.value = ''
  mediaSuccess.value = ''
}

async function uploadImages(files = []) {
  const itemDocName = detail.value?.item?.name
  if (!itemDocName) {
    mediaError.value = 'شناسه محصول نامعتبر است.'
    return
  }

  const imageFiles = Array.from(files || []).filter((file) => String(file?.type || '').startsWith('image/'))
  if (!imageFiles.length) {
    mediaError.value = 'فایل انتخابی باید تصویر باشد.'
    return
  }

  mediaUploading.value = true
  clearMediaMessages()
  try {
    for (const file of imageFiles) {
      await uploadManagementItemImage({
        item_name: itemDocName,
        file,
        is_private: 0,
      })
    }
    await loadDetail()
    mediaSuccess.value = `${imageFiles.length.toLocaleString('fa-IR')} تصویر با موفقیت آپلود شد.`
  } catch (uploadErr) {
    mediaError.value = uploadErr.message || 'آپلود تصویر ناموفق بود.'
  } finally {
    mediaUploading.value = false
  }
}

async function setCoverImage(url) {
  const itemDocName = detail.value?.item?.name
  if (!itemDocName) {
    return
  }
  mediaSaving.value = true
  clearMediaMessages()
  try {
    await updateManagementProductSettings({
      name: itemDocName,
      image: String(url || '').trim(),
    })
    await loadDetail()
    selectedImage.value = String(url || '').trim()
    mediaSuccess.value = 'تصویر کاور بروزرسانی شد.'
  } catch (saveErr) {
    mediaError.value = saveErr.message || 'تنظیم تصویر کاور ناموفق بود.'
  } finally {
    mediaSaving.value = false
  }
}

async function setSecondaryImage(url) {
  const itemDocName = detail.value?.item?.name
  if (!itemDocName) {
    return
  }
  mediaSaving.value = true
  clearMediaMessages()
  try {
    await updateManagementProductSettings({
      name: itemDocName,
      website_image: String(url || '').trim(),
    })
    await loadDetail()
    mediaSuccess.value = 'تصویر دوم بروزرسانی شد.'
  } catch (saveErr) {
    mediaError.value = saveErr.message || 'تنظیم تصویر دوم ناموفق بود.'
  } finally {
    mediaSaving.value = false
  }
}

async function removeImage(url) {
  const itemDocName = detail.value?.item?.name
  const normalizedUrl = String(url || '').trim()
  if (!itemDocName || !normalizedUrl) {
    return
  }

  mediaSaving.value = true
  clearMediaMessages()
  try {
    const nextPayload = { name: itemDocName }
    let shouldUpdateItem = false

    if (String(settingsForm.image || '').trim() === normalizedUrl) {
      nextPayload.image = ''
      shouldUpdateItem = true
    }
    if (String(settingsForm.website_image || '').trim() === normalizedUrl) {
      nextPayload.website_image = ''
      shouldUpdateItem = true
    }

    if (shouldUpdateItem) {
      await updateManagementProductSettings(nextPayload)
    }

    const removed = await deleteManagementItemImageByUrl({
      item_name: itemDocName,
      file_url: normalizedUrl,
    })

    if (!removed?.deleted && !shouldUpdateItem) {
      throw new Error('این تصویر قابل حذف نیست یا به محصول متصل نشده است.')
    }

    await loadDetail()
    if (selectedImage.value === normalizedUrl) {
      selectedImage.value = String(detail.value?.media?.main_image || '')
    }
    mediaSuccess.value = 'تصویر حذف شد.'
  } catch (removeErr) {
    mediaError.value = removeErr.message || 'حذف تصویر ناموفق بود.'
  } finally {
    mediaSaving.value = false
  }
}

function formatTableCell(column, value) {
  const key = String(column?.key || '')
  const valueType = String(column?.type || '').toLowerCase()
  if (valueType === 'money' || /(sales|amount|total|spent|line_total|price|rate)/i.test(key)) {
    return formatMoney(value || 0, activeCurrency.value)
  }
  if (valueType === 'percent' || /percent/i.test(key)) {
    return `${Number(value || 0).toLocaleString('fa-IR')}%`
  }
  if (valueType === 'date' || /(date|created_at|time|valid_from|effective_at)/i.test(key)) {
    return formatPersianDate(value, true)
  }
  if (/status/i.test(key)) {
    return localizeText(value)
  }
  if (/(channel|source)/i.test(key)) {
    return localizeText(value)
  }
  return localizeText(value)
}

function serializeSettingsState() {
  return JSON.stringify({
    item_code: String(settingsForm.item_code || '').trim(),
    item_name: String(settingsForm.item_name || '').trim(),
    custom_snapp_code: String(settingsForm.custom_snapp_code || '').trim(),
    item_group: String(settingsForm.item_group || '').trim(),
    stock_uom: String(settingsForm.stock_uom || '').trim(),
    description: String(settingsForm.description || '').trim(),
    restaurant_slug: String(settingsForm.restaurant_slug || '').trim(),
    restaurant_short_desc: String(settingsForm.restaurant_short_desc || '').trim(),
    restaurant_long_desc: String(settingsForm.restaurant_long_desc || '').trim(),
    restaurant_category: String(settingsForm.restaurant_category || '').trim(),
    restaurant_subcategory: String(settingsForm.restaurant_subcategory || '').trim(),
    restaurant_branch: String(settingsForm.restaurant_branch || '').trim(),
    image: String(settingsForm.image || '').trim(),
    website_image: String(settingsForm.website_image || '').trim(),
    restaurant_prep_time_mins: Number(settingsForm.restaurant_prep_time_mins || 0),
    restaurant_sort_order: Number(settingsForm.restaurant_sort_order || 0),
    restaurant_auto_add_qty: Number(settingsForm.restaurant_auto_add_qty || 0),
    restaurant_nutrition_kcal: Number(settingsForm.restaurant_nutrition_kcal || 0),
    restaurant_nutrition_protein_g: Number(settingsForm.restaurant_nutrition_protein_g || 0),
    restaurant_nutrition_carb_g: Number(settingsForm.restaurant_nutrition_carb_g || 0),
    restaurant_nutrition_sugar_g: Number(settingsForm.restaurant_nutrition_sugar_g || 0),
    restaurant_nutrition_fat_g: Number(settingsForm.restaurant_nutrition_fat_g || 0),
    show_in_print: settingsForm.show_in_print ? 1 : 0,
    restaurant_enabled: settingsForm.restaurant_enabled ? 1 : 0,
    restaurant_is_featured: settingsForm.restaurant_is_featured ? 1 : 0,
    restaurant_is_best_seller: settingsForm.restaurant_is_best_seller ? 1 : 0,
    restaurant_requires_bom: settingsForm.restaurant_requires_bom ? 1 : 0,
    restaurant_auto_add_to_order: settingsForm.restaurant_auto_add_to_order ? 1 : 0,
    disabled: settingsForm.disabled ? 1 : 0,
  })
}

function buildSettingsPayload() {
  const serialized = serializeSettingsState()
  const parsed = JSON.parse(serialized)
  return {
    name: detail.value?.item?.name,
    ...parsed,
    show_in_website: Number(parsed.show_in_print || 0) ? 1 : 0,
  }
}

function handleBeforeUnload(event) {
  if (!hasUnsavedChanges.value) {
    return
  }
  event.preventDefault()
  event.returnValue = ''
}

function syncItemQueryInUrl(nextItemName) {
  if (typeof window === 'undefined') {
    return
  }
  const normalizedItemName = String(nextItemName || '').trim()
  if (!normalizedItemName) {
    return
  }
  try {
    const nextUrl = new URL(window.location.href)
    nextUrl.searchParams.set('item_name', normalizedItemName)
    nextUrl.searchParams.delete('item')
    const query = nextUrl.searchParams.toString()
    const targetUrl = `${nextUrl.pathname}${query ? `?${query}` : ''}${nextUrl.hash || ''}`
    window.history.replaceState(window.history.state, '', targetUrl)
  } catch (urlError) {
    // Ignore URL sync failures.
  }
}

function onWindowKeydown(event) {
  const key = String(event?.key || '').toLowerCase()
  const hasModifier = Boolean(event.ctrlKey || event.metaKey)
  if (!hasModifier || key !== 's') {
    return
  }
  event.preventDefault()

  if (activeTab.value === 'variants') {
    if (!variantBuilderSaving.value && !variantBuilderLoading.value) {
      saveVariantBuilder()
    }
    return
  }

  if (canSaveSettings.value) {
    saveSettings()
  }
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 4 })
}

function bomManagerUrl(row) {
  const itemCode = encodeURIComponent(String(productBomItemCode.value || '').trim())
  const bomName = encodeURIComponent(String(row?.name || '').trim())
  if (!itemCode) {
    return '/management/bom'
  }
  if (!bomName) {
    return `/management/bom?item=${itemCode}`
  }
  return `/management/bom?item=${itemCode}&bom=${bomName}`
}

function formatPersianDate(value, withTime = false) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  const normalizedRaw = normalizeDateRaw(raw)
  try {
    const parsedDate = new Date(normalizedRaw)
    if (Number.isNaN(parsedDate.getTime())) {
      return raw
    }
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
    }).format(parsedDate)
  } catch (dateErr) {
    return raw
  }
}

function localizeAxisLabel(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return raw
  }

  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
    return formatPersianDate(raw, false)
  }
  if (/^\d{1,2}:\d{2}/.test(raw)) {
    return raw
  }
  if (/^\d+(\.\d+)?$/.test(raw)) {
    return Number(raw).toLocaleString('fa-IR')
  }
  return localizeText(raw)
}

function localizeText(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return ''
  }

  if (/^peak day for this item:/i.test(raw)) {
    const datePart = raw.split(':').slice(1).join(':').trim().replace(/\.$/, '')
    const formattedDate = localizeAxisLabel(datePart)
    return `روز اوج فروش این محصول: ${formattedDate}.`
  }

  if (/^cancelled amount in window:/i.test(raw)) {
    const amountPart = raw.split(':').slice(1).join(':').trim().replace(/\.$/, '')
    return `مبلغ لغو شده در این بازه: ${amountPart}.`
  }

  const regexReplacements = [
    [/\bCompared to previous window\b/gi, 'نسبت به بازه قبلی'],
    [/\bProduct sales\b/gi, 'فروش محصول'],
    [/\bSold Quantity\b/gi, 'مقدار فروش'],
    [/\bUnique Customers\b/gi, 'مشتریان یکتا'],
    [/\bAverage Order Value\b/gi, 'میانگین مبلغ سفارش'],
    [/\bSales Contribution\b/gi, 'سهم از فروش'],
    [/\bDaily Sales\b/gi, 'فروش روزانه'],
    [/\bDaily Quantity\b/gi, 'تعداد روزانه'],
    [/\bHourly Sales Trend\b/gi, 'روند فروش ساعتی'],
    [/\bRecent Orders\b/gi, 'سفارش‌های اخیر'],
    [/\bTop Customers\b/gi, 'برترین مشتریان'],
    [/\bOrder Code\b/gi, 'کد سفارش'],
    [/\bCustomer Name\b/gi, 'نام مشتری'],
    [/\bPrice List Rate\b/gi, 'نرخ لیست قیمت'],
    [/\bLine Total\b/gi, 'جمع ردیف'],
    [/\bIn window\b/gi, 'در این بازه'],
    [/\bWith\b/gi, 'با'],
    [/\bSnapp Guest\b/gi, 'مهمان اسنپ'],
    [/\bdine_in\b/gi, 'سالن'],
  ]

  let replaced = raw
  for (const [pattern, replacement] of regexReplacements) {
    replaced = replaced.replace(pattern, replacement)
  }

  if (replaced !== raw) {
    return replaced
  }

  const normalized = raw
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  const phraseMap = {
    'price history': 'تاریخچه قیمت',
    'sales summary': 'خلاصه فروش',
    'sales trend': 'روند فروش',
    'sales hourly': 'فروش ساعتی',
    'top products': 'محصولات پرفروش',
    'product mix': 'ترکیب محصولات',
    'order status': 'وضعیت سفارش',
    'channel split': 'تفکیک کانال فروش',
    'cashier performance': 'عملکرد صندوقدار',
    cancellations: 'لغو سفارش‌ها',
    'modifier usage': 'استفاده از افزودنی‌ها',
    'average ticket': 'میانگین سبد خرید',
    'line total': 'جمع ردیف',
    'order code': 'کد سفارش',
    'customer name': 'نام مشتری',
    'price list rate': 'نرخ لیست قیمت',
    'daily sales': 'فروش روزانه',
    'daily quantity': 'تعداد روزانه',
    'hourly sales trend': 'روند فروش ساعتی',
    'recent orders': 'سفارش‌های اخیر',
    'top customers': 'برترین مشتریان',
    'product sales': 'فروش محصول',
    'sold quantity': 'مقدار فروش',
    'unique customers': 'مشتریان یکتا',
    'average order value': 'میانگین مبلغ سفارش',
    'sales contribution': 'سهم از فروش',
    'compared to previous window': 'نسبت به بازه قبلی',
    'valid from': 'تاریخ اعتبار',
    'effective at': 'زمان اثرگذاری',
    'created at': 'زمان ایجاد',
    'updated at': 'زمان بروزرسانی',
    'price list': 'لیست قیمت',
    amount: 'مبلغ',
    sales: 'فروش',
    revenue: 'درآمد',
    total: 'جمع کل',
    orders: 'تعداد سفارش',
    order: 'سفارش',
    customer: 'مشتری',
    customers: 'مشتریان',
    name: 'نام',
    product: 'محصول',
    products: 'محصولات',
    item: 'آیتم',
    items: 'آیتم‌ها',
    category: 'دسته',
    subcategory: 'زیردسته',
    date: 'تاریخ',
    hour: 'ساعت',
    status: 'وضعیت',
    channel: 'کانال',
    code: 'کد',
    count: 'تعداد',
    value: 'مقدار',
    price: 'قیمت',
    rate: 'نرخ',
    qty: 'تعداد',
    quantity: 'تعداد',
    currency: 'ارز',
    uom: 'واحد',
    modified: 'آخرین بروزرسانی',
    cost: 'هزینه',
    profit: 'سود',
    margin: 'حاشیه سود',
    discount: 'تخفیف',
    tax: 'مالیات',
    tip: 'انعام',
    service: 'حق سرویس',
    wallet: 'کیف پول',
    pending: 'در انتظار',
    confirmed: 'تایید شده',
    preparing: 'در حال آماده‌سازی',
    ready: 'آماده تحویل',
    delivered: 'تحویل شده',
    cancelled: 'لغو شده',
  }

  if (phraseMap[normalized]) {
    return phraseMap[normalized]
  }

  const words = normalized.split(' ')
  const translatedWords = words.map((word) => phraseMap[word] || word)
  const translated = translatedWords.join(' ')

  if (translated !== normalized) {
    return translated
  }

  return raw
}

function normalizeDateRaw(raw) {
  let value = String(raw || '').trim()
  if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(value)) {
    value = value.replace(' ', 'T')
  }
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{4,}$/.test(value)) {
    value = value.replace(/^(.+\.\d{3})\d+$/, '$1')
  }
  return value
}

function readStoredDetailTab() {
  try {
    const raw = localStorage.getItem('management-product-detail-tab')
    if (tabOptions.some((tab) => tab.value === raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return 'overview'
}

function updatePreviewViewportFromMedia(media) {
  isCompactViewport.value = Boolean(media?.matches)
}

function setupPreviewViewportListener() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return
  }
  compactPreviewMedia = window.matchMedia(PREVIEW_COMPACT_QUERY)
  updatePreviewViewportFromMedia(compactPreviewMedia)
  compactPreviewMediaListener = (event) => updatePreviewViewportFromMedia(event)
  if (compactPreviewMedia.addEventListener) {
    compactPreviewMedia.addEventListener('change', compactPreviewMediaListener)
  } else if (compactPreviewMedia.addListener) {
    compactPreviewMedia.addListener(compactPreviewMediaListener)
  }
}

function cleanupPreviewViewportListener() {
  if (!compactPreviewMedia || !compactPreviewMediaListener) {
    compactPreviewMedia = null
    compactPreviewMediaListener = null
    return
  }
  if (compactPreviewMedia.removeEventListener) {
    compactPreviewMedia.removeEventListener('change', compactPreviewMediaListener)
  } else if (compactPreviewMedia.removeListener) {
    compactPreviewMedia.removeListener(compactPreviewMediaListener)
  }
  compactPreviewMedia = null
  compactPreviewMediaListener = null
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('keydown', onWindowKeydown)
  setupPreviewViewportListener()
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('keydown', onWindowKeydown)
  cleanupPreviewViewportListener()
})

loadDetail()
</script>

<style scoped>
.tabs-shell {
  padding-bottom: 0.4rem;
}

.tab-list {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.tab-btn {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  border-radius: 999px;
  background: rgb(var(--palette-eggshell-rgb) / 0.9);
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.42rem 0.74rem;
  white-space: nowrap;
  cursor: pointer;
}

.tab-btn.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  border-color: transparent;
}

.tab-hint {
  margin: 0.45rem 0 0;
  font-size: 0.8rem;
}

.unsaved-note {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
  color: var(--danger);
}

.unsaved-chip {
  border-radius: 999px;
  border: 1px solid rgb(var(--danger-rgb) / 0.3);
  background: rgb(var(--danger-rgb) / 0.1);
  color: var(--danger);
  padding: 0.28rem 0.6rem;
  font-size: 0.72rem;
}

.filters {
  display: flex;
  align-items: end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filters label {
  min-width: 160px;
  display: grid;
  gap: 0.2rem;
  font-size: 0.82rem;
}

.reports-content {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
}

.reports-content > * {
  min-width: 0;
}

.product-top-grid,
.product-settings-grid,
.charts-grid,
.tables-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
  min-width: 0;
}

.charts-grid > *,
.tables-grid > * {
  min-width: 0;
}

.identity-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
  margin-bottom: 0.55rem;
}

.identity-grid label {
  display: grid;
  gap: 0.18rem;
  font-size: 0.82rem;
  min-width: 0;
}

.field-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.field-help {
  font-size: 0.76rem;
  line-height: 1.75;
  color: var(--text-muted);
}

.checks-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  margin: 0.45rem 0 0.7rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.82rem;
}

.image-shell {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 12px;
  background: rgb(var(--palette-eggshell-rgb) / 0.56);
  min-height: 200px;
  display: grid;
  place-items: center;
  margin-bottom: 0.55rem;
}

.main-image {
  width: 100%;
  height: min(52vh, 360px);
  max-height: 360px;
  object-fit: contain;
  object-position: center;
  background: #fff;
  border-radius: 12px;
}

.gallery {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
}

.gallery-item {
  padding: 0;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 10px;
  background: rgb(var(--palette-eggshell-rgb) / 0.5);
  overflow: hidden;
  min-width: 70px;
  width: 70px;
  height: 70px;
  cursor: pointer;
}

.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.inline-actions {
  margin: 0.25rem 0 0.6rem;
  display: flex;
  justify-content: flex-start;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.variants-grid {
  display: grid;
  gap: 0.65rem;
}

.variant-config-shell {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.5);
  padding: 0.6rem;
  display: grid;
  gap: 0.6rem;
}

.variant-config-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

.variant-config-head strong {
  font-size: 0.82rem;
}

.variant-editor-table-wrap {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 12px;
  background: #fff;
  overflow-x: auto;
}

.variant-editor-table,
.variant-values-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

.variant-editor-table th,
.variant-editor-table td,
.variant-values-table th,
.variant-values-table td {
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  padding: 0.45rem 0.5rem;
  text-align: right;
  font-size: 0.77rem;
  vertical-align: middle;
}

.variant-editor-table th,
.variant-values-table th {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--text-muted);
  font-size: 0.74rem;
}

.variant-editor-table tbody tr.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.variant-clickable-row {
  cursor: pointer;
}

.variant-clickable-row:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.variant-attr-meta {
  display: grid;
  gap: 0.08rem;
}

.variant-attr-meta strong {
  font-size: 0.78rem;
}

.variant-attr-meta small {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.variant-values-shell {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 12px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.5rem;
}

.variant-values-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.variant-values-head strong {
  font-size: 0.8rem;
}

.variant-values-head-meta {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.mini-abbr {
  min-width: 70px;
  max-width: 110px;
  padding: 0.25rem 0.35rem;
  font-size: 0.72rem;
}

.variant-attribute-mobile-list,
.variant-value-mobile-list,
.variant-mobile-list {
  display: none;
}

.compact-checks {
  margin: 0;
}

.variant-attribute-mobile-card,
.variant-value-mobile-card,
.variant-mobile-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 12px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.45rem;
}

.variant-attribute-mobile-card.active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.38);
  box-shadow: 0 10px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.variant-attribute-mobile-card header,
.variant-mobile-card header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.45rem;
}

.variant-attribute-mobile-card footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
  font-size: 0.74rem;
  color: var(--text-muted);
}

.variant-desktop-table {
  display: block;
}

.menu-preview-inline {
  margin-top: 0.6rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.56);
  padding: 0.55rem;
  display: grid;
  gap: 0.5rem;
}

.menu-preview-inline-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.55rem;
}

.menu-preview-inline-meta {
  display: grid;
  gap: 0.12rem;
}

.menu-preview-inline-meta strong {
  font-size: 0.84rem;
  color: var(--text-primary);
}

.menu-preview-inline-meta small {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.menu-preview-inline-note {
  font-size: 0.72rem;
  white-space: nowrap;
}

.menu-preview-list {
  display: grid;
  gap: 0.4rem;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.menu-preview-list--inline {
  gap: 0.5rem;
}

.menu-preview-row {
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 12px;
  padding: 0.52rem;
  display: grid;
  gap: 0.35rem;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.menu-preview-row:hover,
.menu-preview-row:focus-visible {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
  box-shadow: 0 12px 30px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  transform: translateY(-2px);
  outline: none;
}

.menu-preview-modal-body {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(240px, 1fr) minmax(340px, 1.2fr);
  gap: 0.75rem;
  align-items: start;
}

.menu-preview-modal-details {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 14px;
  padding: 0.6rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.6);
  display: grid;
  gap: 0.45rem;
}

.menu-preview-modal-details article {
  display: grid;
  gap: 0.15rem;
}

.menu-preview-modal-details strong {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.menu-preview-modal-details p {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.7;
  color: var(--text-primary);
}

.menu-preview-customer-view {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.6);
  padding: 0.6rem;
  display: grid;
  gap: 0.45rem;
}

.menu-preview-customer-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.4rem;
}

.menu-preview-customer-head strong {
  font-size: 0.8rem;
}

.menu-preview-customer-iframe {
  width: 100%;
  min-height: 520px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 12px;
  background: #fff;
}

.menu-preview-customer-link {
  width: 100%;
  text-align: center;
}

.preview-static-card :deep(a),
.preview-static-card :deep(button) {
  pointer-events: none !important;
  cursor: default !important;
}

.preview-static-card :deep(.add-btn),
.preview-static-card :deep(.like-btn),
.preview-static-card :deep(.detail-link),
.preview-static-card :deep(.qty-step) {
  opacity: 0.72;
}

.bom-card {
  grid-column: 1 / -1;
}

.bom-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.55rem;
}

.mini-link-btn {
  font-size: 0.75rem;
  padding: 0.3rem 0.6rem;
}

.hint-line {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.status-pills {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.pill {
  border-radius: 999px;
  padding: 0.12rem 0.46rem;
  font-size: 0.69rem;
}

.pill.active {
  background: rgb(var(--palette-june-bud-rgb) / 0.44);
  color: var(--accent-green);
}

.pill.inactive {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.17);
  color: var(--accent-gold);
}

.pill.default {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

.pill.docstatus {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--text-muted);
}

.pill.docstatus.submitted {
  background: rgb(var(--palette-june-bud-rgb) / 0.24);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
}

:deep(.table-shell) {
  max-width: 100%;
  overflow-x: auto;
}

:deep(.kpi-grid) {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
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
  .filters {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-items: stretch;
  }

  .filters .primary-btn {
    width: 100%;
  }

  .product-top-grid,
  .product-settings-grid,
  .charts-grid,
  .tables-grid,
  .identity-grid,
  .checks-grid {
    grid-template-columns: 1fr;
  }

  .checks-grid {
    gap: 0.3rem;
  }

  .variant-config-head,
  .variant-values-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .variant-editor-table-wrap,
  .variant-desktop-table {
    display: none;
  }

  .variant-attribute-mobile-list,
  .variant-value-mobile-list,
  .variant-mobile-list {
    display: grid;
    gap: 0.5rem;
  }

  .variant-values-shell {
    padding: 0.5rem;
  }

  .variant-values-head-meta {
    width: 100%;
    justify-content: space-between;
  }

  .variant-attribute-mobile-card footer {
    flex-direction: column;
    align-items: stretch;
  }

  .variant-mobile-card .mini-link-btn {
    width: 100%;
    text-align: center;
  }

  .menu-preview-inline-head {
    flex-direction: column;
    align-items: stretch;
  }

  .menu-preview-inline-note {
    white-space: normal;
  }

  .menu-preview-list {
    grid-template-columns: 1fr;
  }

  .menu-preview-row {
    padding: 0.42rem;
  }

  .menu-preview-modal-body {
    grid-template-columns: 1fr;
  }

  .menu-preview-modal-body > :deep(.product-card) {
    max-width: 100%;
  }

  .menu-preview-customer-iframe {
    min-height: 420px;
  }

  .check {
    border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
    border-radius: 10px;
    padding: 0.35rem 0.45rem;
    background: rgb(var(--palette-eggshell-rgb) / 0.62);
  }

  .main-image {
    height: min(62vw, 300px);
  }
}

@media (max-width: 640px) {
  .tab-btn {
    font-size: 0.78rem;
    padding: 0.38rem 0.66rem;
  }

  .tab-hint {
    font-size: 0.78rem;
    line-height: 1.7;
  }
}
</style>

<style scoped>
.variant-creation-form {
  display: grid;
  gap: 1.25rem;
}

.add-attribute-form {
  display: grid;
  gap: 1rem;
}

.add-attribute-form label {
  display: grid;
  gap: 0.5rem;
}

.variant-attributes-grid {
  display: grid;
  gap: 1rem;
}

.variant-attributes-grid label {
  display: grid;
  gap: 0.5rem;
}

.hint {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.info-box {
  padding: 0.75rem 1rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  border-radius: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.delete-btn {
  border-color: rgb(220, 38, 38) !important;
  color: rgb(220, 38, 38) !important;
}

.delete-btn:hover:not(:disabled) {
  background: rgb(220, 38, 38, 0.1) !important;
  border-color: rgb(220, 38, 38) !important;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-mini-btn {
  border-color: rgb(220, 38, 38) !important;
  color: rgb(220, 38, 38) !important;
}

.delete-mini-btn:hover:not(:disabled) {
  background: rgb(220, 38, 38, 0.1) !important;
}
</style>
