<template>
  <ManagementBreadcrumbs class="page-breadcrumbs" :items="breadcrumbItems" />
  <ManagementPageScaffold>

    <ManagementSurfaceCard v-if="detail" class="product-general-card product-general-card--compact" title="اطلاعات کلی" subtitle="تصویر و تنظیمات سریع محصول">
      <div class="product-general-layout">
        <aside class="product-general-media" aria-label="عکس محصول">
          <div class="general-image-shell is-clickable" @click="openMediaDialog">
            <img v-if="mainImage" :src="mainImage" :alt="settingsForm.item_name || 'عکس محصول'" class="general-product-image" />
            <div v-else class="general-image-empty">
              <span aria-hidden="true">+</span>
            </div>
            <button
              type="button"
              class="pg-image-edit-btn"
              title="مدیریت تصاویر"
              aria-label="مدیریت تصاویر"
              @click.stop="openMediaDialog"
            >
              <Camera :size="13" />
            </button>
          </div>
        </aside>

        <div class="product-general-main">
          <div class="product-general-fields">
            <label class="pg-name-field">
              نام کالا
              <input class="input" v-model="settingsForm.item_name" placeholder="نام نمایشی محصول" />
            </label>

            <div class="pg-status-row">
              <span class="pg-status-pill" :class="settingsForm.restaurant_enabled ? 'is-on' : 'is-off'">
                {{ settingsForm.restaurant_enabled ? 'فعال در منو' : 'غیرفعال در منو' }}
              </span>
              <span v-if="settingsForm.restaurant_coming_soon" class="pg-status-pill is-soon">به‌زودی</span>
              <span v-if="Number(detail?.item?.restaurant_out_of_stock || 0)" class="pg-status-pill is-warn">ناموجود</span>
              <span v-if="settingsForm.disabled" class="pg-status-pill is-off">غیرفعال در ERPNext</span>
              <button
                type="button"
                class="pg-status-pill pg-status-pill--btn"
                :class="settingsForm.restaurant_kitchen_ticket ? 'is-kitchen-on' : 'is-kitchen-off'"
                title="فیش آشپزخانه — با کلیک روشن/خاموش می‌شود"
                @click="settingsForm.restaurant_kitchen_ticket = !settingsForm.restaurant_kitchen_ticket"
              >
                فیش آشپزخانه
              </button>
              <span class="pg-status-pill is-code" :title="settingsForm.item_code">{{ settingsForm.item_code }}</span>
            </div>

            <div class="pg-meta-row">
              <span v-if="selectedCategoryLabel || selectedSubcategoryLabel" class="pg-meta-chip">
                <strong>دسته‌بندی</strong>
                {{ [selectedCategoryLabel, selectedSubcategoryLabel].filter(Boolean).join(' / ') || '-' }}
              </span>
              <span v-if="productReadinessChecks.length" class="pg-readiness" :class="readinessScore === productReadinessChecks.length ? 'is-ready' : ''">
                آمادگی: {{ readinessScore.toLocaleString('fa-IR') }} / {{ productReadinessChecks.length.toLocaleString('fa-IR') }}
              </span>
            </div>
          </div>

          <label class="price-inline-field">
            قیمت کالا
            <span class="price-inline-control">
              <PersianNumberInput v-model="priceForm.price_list_rate" :min="0" suffix="ریال" />
              <button class="secondary-btn quick-price-save" type="button" @click="savePrice" :disabled="savingPrice">
                {{ savingPrice ? 'در حال ثبت...' : 'ثبت قیمت' }}
              </button>
            </span>
          </label>

          <div class="pg-quick-toggles">
            <ManagementToggleSwitch v-model="settingsForm.restaurant_enabled" label="فعال در منو" />
            <ManagementToggleSwitch v-model="settingsForm.restaurant_coming_soon" label="به‌زودی" />
          </div>
        </div>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard tone="soft" class="section-picker-shell">
      <div class="section-picker">
        <div class="simple-tabs" role="tablist" aria-label="بخش‌های جزئیات محصول">
          <button
            v-for="tab in tabOptions"
            :key="tab.value"
            class="simple-tab"
            :class="{ active: activeTab === tab.value }"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.value"
            @click="activeTab = tab.value"
          >
            <span>{{ tab.label }}</span>
            <span v-if="getTabBadge(tab.value)" class="tab-badge">{{ getTabBadge(tab.value) }}</span>
          </button>
        </div>
        <button class="secondary-btn" type="button" @click="loadDetail" :disabled="loading">
          {{ loading ? 'در حال بروزرسانی...' : 'تازه‌سازی' }}
        </button>
      </div>
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
        <ManagementSurfaceCard title="کارت محصول" subtitle="توضیحات و خروجی قابل نمایش در منوی مشتری">
          <div class="identity-grid">
            <label>
              کد محصول
              <input class="input" v-model="settingsForm.item_code" />
              <small class="hint">کد یکتای محصول در سیستم</small>
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
            <label>
              گروه کالا
              <SearchableDropdown
                v-model="settingsForm.item_group"
                :options="fieldOptions.item_groups || []"
                placeholder="انتخاب گروه کالا"
                search-placeholder="جستجوی گروه کالا..."
                include-empty-option
                empty-label="انتخاب گروه کالا"
              />
            </label>

            <label>
              زیرگروه کالا
              <SearchableDropdown
                v-model="settingsForm.restaurant_subcategory"
                :options="filteredSubcategoryOptions"
                placeholder="بدون زیرگروه"
                search-placeholder="جستجوی زیرگروه..."
                include-empty-option
                empty-label="بدون زیرگروه"
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
            <small class="field-help">این بخش در صفحه جزئیات محصول سایت کنار اطلاعات اصلی نشان داده می‌شود.</small>
          </label>

          <section class="nutrition-box " aria-label="ارزش غذایی">
            <header class="nutrition-head">
              <strong>ارزش غذایی</strong>
              <small>اعداد اختیاری هستند و در صفحه محصول مشتری نمایش داده می‌شوند.</small>
            </header>
            <div class="nutrition-grid">
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
            </div>
          </section>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="وضعیت‌ها" subtitle="نمایش در منو، برجسته‌سازی و حالت‌های فروش">
          <div class="product-general-toggles">
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_enabled"
              label="نمایش در منوی سایت"
              hint="مشتری محصول را در منو می‌بیند."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.show_in_print"
              label="نمایش در پرینت"
              hint="در رسیدها و چاپ‌ها نمایش داده شود."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_is_featured"
              label="محصول ویژه"
              hint="در بخش‌های برجسته سایت استفاده می‌شود."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_is_best_seller"
              label="پرفروش"
              hint="برای برچسب و مرتب‌سازی محصولات پرفروش."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_requires_bom"
              label="نیازمند BOM"
              hint="اگر مواد اولیه و فرمول ساخت دارد روشن باشد."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_coming_soon"
              label="به‌زودی"
              hint="محصول دیده می‌شود ولی برای فروش آماده نیست."
            />
            <div class="restock-field">
              <span class="field-label">موجودی</span>
              <div class="oos-toggle-row">
                <button
                  type="button"
                  class="stock-toggle-btn"
                  :class="{ active: settingsForm.restaurant_out_of_stock }"
                  @click="settingsForm.restaurant_out_of_stock = !settingsForm.restaurant_out_of_stock"
                >
                  {{ settingsForm.restaurant_out_of_stock ? 'ناموجود' : 'موجود' }}
                </button>
                <small class="field-help" v-if="!settingsForm.restaurant_out_of_stock">
                  محصول در سایت قابل سفارش است.
                </small>
              </div>
              <PersianDateInput
                v-if="settingsForm.restaurant_out_of_stock"
                v-model="settingsForm.out_of_stock_until"
                placeholder="کی دوباره موجود می‌شود؟"
              />
              <small class="field-help" v-if="settingsForm.restaurant_out_of_stock">
                تا این تاریخ در سایت «ناموجود» نمایش داده می‌شود.
              </small>
            </div>
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_auto_add_to_order"
              label="افزودن خودکار"
              hint="برای آیتم‌های مکمل یا اجباری سفارش."
            />
            <ManagementToggleSwitch
              v-model="settingsForm.disabled"
              label="غیرفعال در ERPNext"
              hint="در کل سیستم ERP غیرفعال می‌شود."
            />
          </div>
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
            <label class="tag-select-field">
              تگ‌های محصول
              <SearchableDropdown
                v-model="tagList"
                :options="allTagOptions"
                placeholder="انتخاب یا ساخت تگ"
                search-placeholder="جستجو یا ساخت تگ..."
                no-results-text="تگی پیدا نشد"
                :multiple="true"
                clearable
                allow-create
                create-option-label="ساخت تگ"
                @create-option="handleCreateTagOption"
              />
              <small class="hint">چند تگ انتخاب کنید یا همانجا تگ جدید بسازید.</small>
            </label>
            <label>
              مقدار افزودن خودکار
              <PersianNumberInput v-model="settingsForm.restaurant_auto_add_qty" :allow-float="true" :min="0" />
            </label>
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

      </section>

      <section v-else-if="activeTab === 'changes'" class="product-changes-grid">
        <ManagementSurfaceCard title="تاریخچه تغییرات" subtitle="نسخه‌های ثبت‌شده این محصول در ERPNext">
          <p v-if="activityLoading" class="muted">در حال بارگذاری تاریخچه...</p>
          <p v-else-if="!activityVersions.length" class="muted">تغییری روی این محصول ثبت نشده است.</p>
          <ol v-else class="changes-timeline">
            <li v-for="ver in activityVersions" :key="ver.name" class="change-item">
              <div class="change-item-head">
                <strong>{{ ver.owner }}</strong>
                <span class="change-item-date">{{ formatPersianDate(ver.creation, true) }}</span>
              </div>
              <ul v-if="parseVersionChanges(ver).length" class="change-fields">
                <li v-for="(ch, idx) in parseVersionChanges(ver).slice(0, 8)" :key="idx">
                  <span class="change-field">{{ fieldLabel(ch.field) }}</span>
                  <span class="change-old">{{ ch.old }}</span>
                  <span class="change-arrow" aria-hidden="true">←</span>
                  <span class="change-new">{{ ch.new }}</span>
                </li>
                <li v-if="parseVersionChanges(ver).length > 8" class="change-more">
                  +{{ parseVersionChanges(ver).length - 8 }} تغییر دیگر
                </li>
              </ul>
              <p v-else class="muted change-empty">جزئیات این نسخه ثبت نشده است.</p>
            </li>
          </ol>
        </ManagementSurfaceCard>

        <ManagementSurfaceCard title="نظرات" subtitle="یادداشت‌های شما و تیم روی این محصول">
          <div class="comments-list">
            <div v-for="cm in activityComments" :key="cm.name" class="comment-item">
              <div class="comment-item-head">
                <strong>{{ cm.owner }}</strong>
                <span class="comment-item-date">{{ formatPersianDate(cm.creation, true) }}</span>
              </div>
              <p class="comment-content">{{ cm.content }}</p>
            </div>
            <p v-if="!activityComments.length" class="muted">هنوز نظری ثبت نشده است.</p>
          </div>
          <div class="comment-form">
            <textarea v-model="commentDraft" class="textarea" rows="2" placeholder="نظر خود را بنویسید..."></textarea>
            <div class="comment-form-actions">
              <button class="primary-btn" type="button" :disabled="!String(commentDraft || '').trim() || commentSaving" @click="submitComment">
                {{ commentSaving ? 'در حال ثبت...' : 'ثبت نظر' }}
              </button>
            </div>
          </div>
        </ManagementSurfaceCard>
      </section>

            <section v-if="activeTab === 'formula'" class="variants-grid">
              <ManagementSurfaceCard title="فرمول و رسپی" subtitle="ثبت BOM و دستور پخت همین محصول از همین صفحه">
                <div class="identity-grid">
                  <label>
                    تعداد خروجی فرمول
                    <PersianNumberInput v-model="bomForm.quantity" :min="1" :allow-float="true" />
                  </label>
                  <label>
                    شرکت
                    <SearchableDropdown
                      v-model="bomForm.company"
                      :options="bomCompanyOptions"
                      placeholder="انتخاب شرکت"
                      search-placeholder="جستجوی شرکت..."
                      include-empty-option
                      empty-label="انتخاب شرکت"
                    />
                  </label>
                  <label>
                    ارز
                    <SearchableDropdown
                      v-model="bomForm.currency"
                      :options="bomCurrencyOptions"
                      placeholder="انتخاب ارز"
                      search-placeholder="جستجوی ارز..."
                      include-empty-option
                      empty-label="انتخاب ارز"
                    />
                  </label>
                  <label>
                    نام BOM فعال
                    <input class="input" :value="bomForm.name || 'BOM جدید'" readonly />
                  </label>
                </div>

                <label>
                  <span class="field-label">دستور پخت</span>
                  <textarea class="textarea" v-model="bomForm.restaurant_recipe_instruction" placeholder="مراحل آماده‌سازی و رسپی محصول را اینجا وارد کنید."></textarea>
                </label>

                <section class="bom-status-section">
                  <header class="bom-status-section__head">
                    <strong>وضعیت این فرمول</strong>
                    <small>مشخص کنید این BOM فقط ثبت باشد یا فرمول فعال و پیش‌فرض محصول هم باشد.</small>
                  </header>

                  <div class="checks-grid compact-checks">
                    <ManagementCheckboxField
                      v-model="bomForm.is_active"
                      label="BOM فعال"
                      hint="در فرمول‌های قابل استفاده محصول قرار بگیرد."
                    />
                    <ManagementCheckboxField
                      v-model="bomForm.is_default"
                      label="BOM پیش‌فرض"
                      hint="به عنوان فرمول اصلی همین محصول استفاده شود."
                    />
                  </div>
                </section>

                <div class="inline-actions">
                  <button class="secondary-btn" type="button" @click="addBomItemRow">افزودن ماده اولیه</button>
                  <button class="primary-btn" type="button" @click="saveBomFromProduct" :disabled="bomSaving">
                    {{ bomSaving ? 'در حال ذخیره فرمول...' : 'ذخیره فرمول و رسپی' }}
                  </button>
                </div>

                <p class="error" v-if="bomError">{{ bomError }}</p>
                <p class="success" v-if="bomSaveSuccess">{{ bomSaveSuccess }}</p>

                <div class="formula-workspace">
                  <section class="formula-block">
                    <header class="formula-block__head">
                      <div>
                        <strong>جدول مواد BOM</strong>
                        <small>مواد اولیه، جایگزینی ماده، چاپ و تنظیمات فرمول را یک‌جا ببینید.</small>
                      </div>
                      <span class="formula-block__meta">
                        {{ formatNumber(bomItemsSummary.length) }} ردیف
                      </span>
                    </header>

                    <ManagementBomItemsTable
                      v-model="bomForm.items"
                      :item-options="bomItemOptions"
                      :item-catalog="bomItemCatalog"
                      :disabled="bomLoading || bomSaving"
                    />
                  </section>

                  <section class="formula-block">
                    <header class="formula-block__head">
                      <div>
                        <strong>Modifierهای متصل به همین BOM</strong>
                        <small>گروه‌های انتخاب مشتری که روی همین فرمول اثر می‌گذارند.</small>
                      </div>
                      <span class="formula-block__meta">
                        {{ formatNumber(activeBomModifierGroupsCount) }} گروه
                      </span>
                    </header>

                    <ManagementBomModifiersTable
                      v-model="bomForm.restaurant_modifier_rows"
                      :modifier-group-options="bomModifierGroupOptions"
                      :item-options="bomItemOptions"
                      :bom-options="bomReferenceOptions"
                      :disabled="bomLoading || bomSaving"
                    />
                  </section>
                </div>

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
                      <button class="secondary-btn mini-link-btn" type="button" @click="loadBomDocIntoForm(row.name)">بارگذاری</button>
                      <a class="secondary-btn mini-link-btn" :href="`/app/bom/${encodeURIComponent(row.name)}`" target="_blank" rel="noreferrer">ERP</a>
                    </div>
                  </template>
                </ManagementDataTable>
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
                        <ManagementToggleSwitch
                          :model-value="Number(row.show_in_website || 0) === 1"
                          label="نمایش در سایت"
                          compact
                          @click.stop
                          @update:modelValue="updateAttributeToggle(row.name, 'show_in_website', $event)"
                        />
                      </td>
                      <td>
                        <ManagementToggleSwitch
                          :model-value="Number(row.selection_only || 0) === 1"
                          label="انتخابی مشتری"
                          compact
                          @click.stop
                          @update:modelValue="updateAttributeToggle(row.name, 'selection_only', $event)"
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
                    <ManagementToggleSwitch
                      :model-value="Number(row.show_in_website || 0) === 1"
                      label="نمایش در سایت"
                      @click.stop
                      @update:modelValue="updateAttributeToggle(row.name, 'show_in_website', $event)"
                    />
                    <ManagementToggleSwitch
                      :model-value="Number(row.selection_only || 0) === 1"
                      label="انتخابی مشتری"
                      @click.stop
                      @update:modelValue="updateAttributeToggle(row.name, 'selection_only', $event)"
                    />
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

      <section v-if="activeTab === 'builder'" class="builder-section">
        <ManagementSurfaceCard title="سفارشی‌سازی محصول" subtitle="تنظیم ساختار سفارشی‌سازی برای مشتری" tone="accent">
          <div class="builder-grid">
            <ManagementToggleSwitch
              v-model="settingsForm.restaurant_is_customizable"
              label="قابل سفارشی‌سازی"
              hint="با فعال‌سازی، مشتری می‌تواند این محصول را سفارشی کند."
            />
          </div>

          <div v-if="settingsForm.restaurant_is_customizable" class="builder-fields">
            <div class="builder-grid">
              <label>
                متن دکمه سفارشی‌سازی
                <input class="input" v-model="settingsForm.restaurant_customize_button_label" />
                <small class="hint">پیش‌فرض: سفارشی‌سازی</small>
              </label>
              <label>
                نوع محصول سفارشی
                <select class="input" v-model="settingsForm.restaurant_custom_product_type">
                  <option value="">انتخاب کنید</option>
                  <option value="configured">پیکربندی‌شده</option>
                  <option value="made_to_order">سفارشی/سفارش‌ساز</option>
                  <option value="assembled">مونتاژ‌شده</option>
                </select>
              </label>
              <label>
                قالب سفارشی‌سازی
                <SearchableDropdown
                  v-model="settingsForm.restaurant_builder_template"
                  :options="builderTemplateOptions"
                  placeholder="انتخاب قالب"
                  search-placeholder="جستجوی قالب..."
                  include-empty-option
                  empty-label="بدون قالب"
                />
              </label>
              <ManagementToggleSwitch
                v-model="settingsForm.restaurant_builder_active"
                label="سفارشی‌سازی فعال"
                hint="سفارشی‌سازی در سایت مشتری فعال باشد"
              />
            </div>

            <div class="builder-grid">
              <ManagementToggleSwitch
                v-model="settingsForm.restaurant_allow_direct_add"
                label="اجازه افزودن مستقیم"
                :disabled="settingsForm.restaurant_is_customizable && settingsForm.restaurant_builder_active"
                :hint="settingsForm.restaurant_is_customizable && settingsForm.restaurant_builder_active ? 'در محصول‌های builder-driven این گزینه اعمال نمی‌شود و کاربر همیشه اول وارد سازنده می‌شود.' : 'مشتری می‌تواند محصول پایه را بدون سفارشی‌سازی سفارش دهد'"
              />
              <ManagementToggleSwitch
                v-model="settingsForm.restaurant_show_nutrition_summary"
                label="نمایش ارزش غذایی"
                hint="اطلاعات تغذیه‌ای در بخش سفارشی‌سازی نمایش داده شود"
              />
              <ManagementToggleSwitch
                v-model="settingsForm.restaurant_show_allergen_warnings"
                label="نمایش هشدار آلرژی"
                hint="آلرژی‌های هر گزینه نشان داده شود"
              />
              <label>
                حالت چاپ آشپزخانه
                <select class="input" v-model="settingsForm.restaurant_kitchen_print_mode">
                  <option
                    v-for="option in fieldOptions.kitchen_print_modes"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </label>
              <label>
                حالت مصرف موجودی
                <select class="input" v-model="settingsForm.restaurant_stock_consumption_mode">
                  <option
                    v-for="option in fieldOptions.stock_consumption_modes"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>

            <ManagementSurfaceCard
              title="پیکربندی اختصاصی این محصول"
              subtitle="می‌توانید یک قالب عمومی را روی این محصول اعمال کنید و سپس مرحله‌ها و گزینه‌های همین محصول را جداگانه ویرایش کنید."
              tone="accent"
              class="builder-editor-card"
            >
              <div class="builder-actions-row">
                <button
                  class="secondary-btn"
                  type="button"
                  :disabled="!settingsForm.restaurant_builder_template"
                  @click="applyBuilderTemplateToProduct"
                >
                  آوردن داده‌های قالب داخل این محصول
                </button>
                <button
                  class="secondary-btn"
                  type="button"
                  :disabled="!settingsForm.restaurant_builder_template || !hasBuilderConfig"
                  @click="resetBuilderToTemplate"
                >
                  بازنشانی از روی قالب انتخاب‌شده
                </button>
                <a
                  v-if="settingsForm.restaurant_builder_template"
                  class="primary-pill-link"
                  :href="`/management/builder-template/edit/${settingsForm.restaurant_builder_template}`"
                >
                  مشاهده/ویرایش قالب مرجع ←
                </a>
                <a
                  v-else
                  class="secondary-btn"
                  href="/management/builder-template/new"
                >
                  ایجاد قالب سفارشی‌سازی جدید
                </a>
              </div>

              <p v-if="builderSourceTemplateName" class="muted builder-source-note">
                قالب مرجع این محصول: <strong>{{ builderSourceTemplateName }}</strong>
              </p>

              <div v-if="builderConfig" class="builder-editor-stack">
                <div class="builder-grid">
                  <label>
                    عنوان پیکربندی
                    <input class="input" v-model="builderConfig.title" placeholder="مثلاً سالاد سفارشی" />
                  </label>
                  <label>
                    اسلاگ پیکربندی
                    <input class="input" v-model="builderConfig.slug" placeholder="custom-salad-builder" dir="ltr" />
                  </label>
                  <label>
                    حالت چیدمان
                    <select class="input" v-model="builderConfig.layout_mode">
                      <option value="vertical_steps">مرحله‌ای عمودی</option>
                      <option value="horizontal_tabs">تب‌های افقی</option>
                      <option value="accordion">آکاردئون</option>
                      <option value="wizard">مرحله‌ای (ویزارد)</option>
                    </select>
                  </label>
                  <label>
                    رنگ اصلی
                    <input class="input" v-model="builderConfig.primary_color" type="color" dir="ltr" />
                  </label>
                </div>

                <div class="builder-grid">
                  <ManagementToggleSwitch v-model="builderConfig.show_summary_panel" label="نمایش خلاصه" hint="خلاصه انتخاب‌ها را نشان بده" />
                  <ManagementToggleSwitch v-model="builderConfig.show_price_live" label="قیمت زنده" hint="قیمت نهایی به‌صورت زنده محاسبه شود" />
                  <ManagementToggleSwitch v-model="builderConfig.allow_skip_steps" label="اجازه رد شدن" hint="مشتری بتواند مراحل اختیاری را رد کند" />
                  <ManagementToggleSwitch v-model="builderConfig.allow_go_back" label="اجازه بازگشت" hint="مشتری بتواند به مرحله قبل برگردد" />
                  <ManagementToggleSwitch v-model="builderConfig.require_all_required" label="اجبار همه مراحل" hint="همه مراحل اجباری باید تکمیل شوند" />
                  <label>
                    حداکثر انتخاب کل
                    <PersianNumberInput v-model="builderConfig.max_total_selections" :min="0" />
                    <small class="hint">0 یعنی بدون محدودیت</small>
                  </label>
                </div>

                <ManagementSurfaceCard title="مراحل سفارشی‌سازی" subtitle="مراحل و گزینه‌ها را برای همین محصول تنظیم کنید">
                  <div class="steps-toolbar">
                    <button class="primary-btn" type="button" @click="addBuilderStep">+ افزودن مرحله</button>
                  </div>

                  <div v-if="!builderConfig.steps?.length" class="empty-steps">
                    <p class="muted">هنوز مرحله‌ای برای این محصول اضافه نشده است.</p>
                    <button class="secondary-btn" type="button" @click="addBuilderStep">افزودن اولین مرحله</button>
                  </div>

                  <div v-else class="steps-list">
                    <BuilderStepCard
                      v-for="(step, index) in builderConfig.steps"
                      :key="step.step_key || step.name || index"
                      :step="step"
                      :step-index="index"
                      :steps-length="builderConfig.steps.length"
                      :item-options="builderItemOptions"
                      @update:step="updateBuilderStep(index, $event)"
                      @move-up="moveBuilderStep(index, -1)"
                      @move-down="moveBuilderStep(index, 1)"
                      @delete="deleteBuilderStep(index)"
                    />
                  </div>
                </ManagementSurfaceCard>
              </div>

              <div v-else class="empty-steps">
                <p class="muted">هنوز پیکربندی اختصاصی برای این محصول ساخته نشده است.</p>
                <div class="builder-actions-row">
                  <button class="primary-btn" type="button" @click="applyBuilderTemplateToProduct" :disabled="!settingsForm.restaurant_builder_template">
                    استفاده از قالب انتخاب‌شده
                  </button>
                  <button class="secondary-btn" type="button" @click="addBuilderStep">
                    ساخت دستی از صفر
                  </button>
                </div>
              </div>
            </ManagementSurfaceCard>
          </div>

          <p v-else class="muted builder-hint">
            با فعال‌سازی سفارشی‌سازی، مشتری می‌تواند این محصول را مطابق سلیقه خود تنظیم کند.
          </p>
        </ManagementSurfaceCard>
      </section>

      <div v-if="detail" class="sticky-save-bar" :class="{ 'is-dirty': hasUnsavedChanges }" role="status" aria-live="polite">
        <div v-if="hasUnsavedChanges">
          <strong>تغییرات ذخیره نشده دارید</strong>
          <small>با Ctrl/⌘ + S هم می‌توانید ذخیره کنید.</small>
        </div>
        <button class="primary-btn save-spark-btn" type="button" @click="saveSettings" :disabled="!canSaveSettings">
          {{ savingSettings ? 'در حال ذخیره...' : 'ذخیره' }}
        </button>
      </div>
    </template>
  </ManagementPageScaffold>

  <ManagementPopup
    v-model:open="mediaDialogOpen"
    title="تصاویر محصول"
    subtitle="انتخاب عکس اصلی، حذف یا افزودن تصویر"
    :close-on-backdrop="!mediaSaving && !mediaUploading"
  >
    <div class="media-dialog-body">
      <div class="media-preview-box">
        <div class="media-preview-head">
          <strong>پیش‌نمایش کارت محصول</strong>
          <small>نمایش کارت منو با تصویر اصلی فعلی</small>
        </div>
        <div class="media-preview-card-wrap">
          <MenuProductCard
            :item="mediaPreviewItem"
            currency="TOMAN"
            :cart-qty="0"
            class="preview-static-card"
          />
        </div>
      </div>

      <div class="media-divider"></div>

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
      <p class="error" v-if="mediaError">{{ mediaError }}</p>
      <p class="success" v-if="mediaSuccess">{{ mediaSuccess }}</p>
    </div>
  </ManagementPopup>

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
                <ManagementToggleSwitch
                  :model-value="activeAttributeSelectedValues.includes(valueRow.value)"
                  label="تولید Variant"
                  compact
                  @update:modelValue="toggleGeneratedValue(activeVariantAttributeRow.name, valueRow.value)"
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
          <ManagementToggleSwitch
            :model-value="activeAttributeSelectedValues.includes(valueRow.value)"
            label="تولید Variant"
            @update:modelValue="toggleGeneratedValue(activeVariantAttributeRow.name, valueRow.value)"
          />
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

      <ManagementToggleSwitch
        v-model="variantCreationForm.create_multiple"
        label="ساخت گروهی Variant"
        hint="اگر روشن باشد چند مدل با هم ساخته می‌شود."
      />

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
import BuilderStepCard from '@/components/management/builder/BuilderStepCard.vue'
import ManagementBomItemsTable from '@/components/management/ManagementBomItemsTable.vue'
import ManagementBomModifiersTable from '@/components/management/ManagementBomModifiersTable.vue'
import ManagementCheckboxField from '@/components/management/ManagementCheckboxField.vue'
import ManagementImageUploaderView from '@/components/management/ManagementImageUploaderView.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementBreadcrumbs from '@/components/management/ManagementBreadcrumbs.vue'
import { clearNavbarTitle, setNavbarTitle } from '@/utils/navbarTitle'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import { Camera } from 'lucide-vue-next'
import MenuProductCard from '@/components/MenuProductCard.vue'
import ReportChartRenderer from '@/components/management/bi/ReportChartRenderer.vue'
import ReportInsightCards from '@/components/management/bi/ReportInsightCards.vue'
import ReportKpiGrid from '@/components/management/bi/ReportKpiGrid.vue'
import {
  callMethodByPathGET,
  createManagementBom,
  deleteManagementItemImageByUrl,
  generateManagementProductVariants,
  getManagementBomContext,
  getManagementBomDoc,
  getManagementProductVariantBuilder,
  getManagementProductDetail,
  getManagementProductActivity,
  addManagementProductComment,
  listManagementModifierGroups,
  listManagementBomItems,
  listManagementBoms,
  listRestaurantItemTags,
  saveManagementProductVariantBuilder,
  setManagementDefaultPriceList,
  setManagementProductPrice,
  updateManagementBom,
  uploadManagementItemImage,
  updateManagementProductSettings
} from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import {
  PRODUCT_DETAIL_TABS,
  buildProductSettingsPayload,
  clonePlainObject,
  createEmptyBuilderStep,
  createInitialProductSettingsForm,
  formatPersianDate,
  hydrateProductSettingsForm,
  KITCHEN_PRINT_MODE_OPTIONS,
  localizeAxisLabel,
  localizeText,
  normalizeVariantAttributesDraft,
  resolveTemplateAttributeSelection,
  serializeProductSettingsState,
  STOCK_CONSUMPTION_MODE_OPTIONS
} from '@/utils/managementProductDetail'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({})
}
})

const query = parseQuery()
const PREVIEW_COMPACT_QUERY = '(max-width: 980px)'
const itemName = ref(String(query.item_name || query.item || props.boot?.item_name || '').trim())
const today = new Date()
const start = new Date(today)
start.setDate(today.getDate() - 29)

const filters = reactive({
  date_from: start.toISOString().slice(0, 10),
  date_to: today.toISOString().slice(0, 10)
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
const mediaDialogOpen = ref(false)
const mediaUploading = ref(false)
const mediaSaving = ref(false)
const mediaError = ref('')
const mediaSuccess = ref('')
const bomLoading = ref(false)
const bomError = ref('')
const productBoms = ref([])
const bomSaving = ref(false)
const bomSaveSuccess = ref('')
const bomContext = ref({ companies: [], currencies: [], default_company: '', default_currency: '' })
const bomItemOptions = ref([])
const settingsSnapshot = ref('')
const builderItemOptions = ref([])
const builderConfig = ref(null)
const builderSourceTemplateName = ref('')
const variantBuilderLoading = ref(false)
const variantBuilderSaving = ref(false)
const variantBuilderGenerating = ref(false)
const variantBuilderError = ref('')
const variantBuilderSuccess = ref('')
const variantBuilder = ref(null)
const variantAttributesDraft = ref([])
const selectedTemplateAttributes = ref([])
const selectedValuesByAttribute = ref({})
const activeVariantAttributeName = ref('')
const variantBuilderLoadedKey = ref('')
const isCompactViewport = ref(false)
let compactPreviewMedia = null
let compactPreviewMediaListener = null
const attributeValuesDialogOpen = ref(false)
const variantCreationDialogOpen = ref(false)
const variantCreationForm = ref({
  attributes: {},
  create_multiple: false
})
const showAddAttributeDialog = ref(false)
const selectedNewAttribute = ref('')

const settingsForm = reactive(createInitialProductSettingsForm())

const priceForm = reactive({
  price_list: '',
  price_list_rate: 0,
  valid_from: ''
})

const bomForm = reactive({
  name: '',
  quantity: 1,
  company: '',
  currency: '',
  is_active: true,
  is_default: true,
  restaurant_recipe_instruction: '',
  items: [],
  restaurant_modifier_rows: []
})

const tabOptions = PRODUCT_DETAIL_TABS

const bomColumns = [
  { key: 'name', label: 'BOM' },
  { key: 'quantity', label: 'تعداد' },
  { key: 'status', label: 'وضعیت' },
  { key: 'modified', label: 'آخرین بروزرسانی' },
  { key: 'actions', label: 'عملیات' },
]

const bomModifierGroupOptions = ref([])
const bomItemCatalog = ref([])



const pageTitle = computed(() => detail.value?.item?.item_name || 'جزئیات محصول')
const breadcrumbItems = computed(() => [
  { label: 'مدیریت', href: '/management' },
  { label: 'محصولات', href: '/management/products' },
  { label: pageTitle.value, href: '' },
])

watch(pageTitle, (title) => {
  setNavbarTitle(title)
})
const pageSubtitle = computed(() => {
  const item = detail.value?.item || {}
  const parts = [item.item_code || item.name, selectedCategoryLabel.value, settingsForm.restaurant_enabled ? 'فعال در منو' : 'غیرفعال در منو']
    .map((value) => String(value || '').trim())
    .filter(Boolean)
  return parts.join(' • ')
})
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
const activeBomRow = computed(() => {
  const activeName = String(activeBomName.value || defaultBomName.value || '').trim()
  if (!activeName) {
    return null
  }
  return (productBoms.value || []).find((row) => String(row?.name || '').trim() === activeName) || null
})
const bomCompanyOptions = computed(() => (bomContext.value?.companies || []).map((row) => ({ value: row, label: row })))
const bomCurrencyOptions = computed(() => (bomContext.value?.currencies || []).map((row) => ({ value: row, label: row })))
const bomItemsSummary = computed(() => Array.isArray(bomForm.items) ? bomForm.items : [])
const bomModifierRowsSummary = computed(() =>
  Array.isArray(bomForm.restaurant_modifier_rows) ? bomForm.restaurant_modifier_rows : [],
)
const bomReferenceOptions = computed(() =>
  (productBoms.value || []).map((row) => ({
    value: String(row?.name || '').trim(),
    label: String(row?.name || '').trim()
})).filter((row) => row.value),
)
const activeBomModifierGroupsCount = computed(() => {
  const keys = new Set(
    (bomModifierRowsSummary.value || [])
      .map((row) => String(row?.group_key || row?.modifier_group || '').trim())
      .filter(Boolean),
  )
  return keys.size
})
const priceLists = computed(() => detail.value?.pricing?.price_lists || [])
const activeCurrency = computed(() => detail.value?.report?.currency || 'IRR')
const priceListOptions = computed(() =>
  priceLists.value.map((row) => ({
    value: row.name,
    label: `${row.title} (${row.currency || activeCurrency.value})`
})),
)
const currentPriceRate = computed(() => Number(detail.value?.pricing?.current_price?.price_list_rate || 0))
const latestPriceRate = computed(() => Number(detail.value?.pricing?.latest_price?.price_list_rate || 0))
const latestPriceDate = computed(() => detail.value?.pricing?.latest_price?.effective_at || '')
const selectedCategoryLabel = computed(() => {
  const selected = String(settingsForm.restaurant_category || '').trim()
  if (!selected) return ''
  return (fieldOptions.value?.categories || []).find((row) => String(row?.value || '').trim() === selected)?.label || selected
})
const selectedSubcategoryLabel = computed(() => {
  const selected = String(settingsForm.restaurant_subcategory || '').trim()
  if (!selected) return ''
  return (fieldOptions.value?.subcategories || []).find((row) => String(row?.value || '').trim() === selected)?.label || selected
})
const productSummarySubtitle = computed(() => {
  const item = detail.value?.item || {}
  const code = String(item.item_code || item.name || '').trim()
  const category = [selectedCategoryLabel.value, selectedSubcategoryLabel.value].filter(Boolean).join(' / ')
  return [code ? `کد: ${code}` : '', category || 'بدون دسته‌بندی'].filter(Boolean).join(' • ')
})
const productSummaryChips = computed(() => [
  {
    key: 'visibility',
    label: 'وضعیت منو',
    value: settingsForm.restaurant_enabled ? 'فعال' : 'غیرفعال',
    tone: settingsForm.restaurant_enabled ? 'success' : 'danger'
},
  {
    key: 'price',
    label: 'قیمت فعلی',
    value: formatMoney(currentPriceRate.value, activeCurrency.value),
    tone: currentPriceRate.value > 0 ? 'success' : 'warn'
},
  {
    key: 'bom',
    label: 'BOM',
    value: defaultBomName.value || activeBomName.value ? 'متصل' : 'ندارد',
    tone: defaultBomName.value || activeBomName.value ? 'info' : settingsForm.restaurant_requires_bom ? 'warn' : 'neutral'
},
  {
    key: 'builder',
    label: 'سفارشی‌سازی',
    value: settingsForm.restaurant_is_customizable || hasBuilderConfig.value ? 'فعال' : 'خاموش',
    tone: settingsForm.restaurant_is_customizable || hasBuilderConfig.value ? 'info' : 'neutral'
},
  {
    key: 'slug',
    label: 'اسلاگ',
    value: settingsForm.restaurant_slug ? settingsForm.restaurant_slug : 'تنظیم نشده',
    tone: settingsForm.restaurant_slug ? 'success' : 'warn'
},
])
const customerProductUrl = computed(() => {
  const slug = String(settingsForm.restaurant_slug || detail.value?.item?.restaurant_slug || '').trim()
  if (!slug) return ''
  return `/item/${encodeURIComponent(slug)}`
})
const activeTabHint = computed(() => {
  if (activeTab.value === 'reports') {
    return 'جزئیات تحلیلی و آمار فروش این محصول در این تب نمایش داده می‌شود.'
  }
  if (activeTab.value === 'variants') {
    return 'جزئیات مدل‌ها، ویژگی‌ها و Variantهای این محصول در این تب مدیریت می‌شود.'
  }
  if (activeTab.value === 'settings') {
    return 'جزئیات فروش، نمایش، دسته‌بندی وب و قیمت‌گذاری در این تب قرار دارد.'
  }
  if (activeTab.value === 'builder') {
    return 'جزئیات سفارشی‌سازی و ساختار انتخاب‌های مشتری در این تب قرار دارد.'
  }
  return 'جزئیات کارت محصول، توضیحات و تصاویر قابل نمایش برای مشتری در این تب قرار دارد.'
})
const canSaveSettings = computed(() => !savingSettings.value && !loading.value && !!detail.value?.item?.name)
const builderTemplateOptions = computed(() => {
  const templates = detail.value?.builder_templates || []
  return templates.map((t) => ({ value: t.name, label: t.title || t.name }))
})
const hasBuilderConfig = computed(() => Boolean(builderConfig.value && Array.isArray(builderConfig.value.steps)))
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
      change_label: localizeText(kpi.change_label)
})),
    charts: (report.charts || []).map((chart) => ({
      ...chart,
      title: localizeText(chart.title || chart.key || 'نمودار'),
      subtitle: localizeText(chart.subtitle),
      labels: Array.isArray(chart.labels) ? chart.labels.map((label) => localizeAxisLabel(label)) : [],
      series: Array.isArray(chart.series)
        ? chart.series.map((row) => ({
            ...row,
            label: localizeText(row.label || row.key)
}))
        : []
})),
    tables: (report.tables || []).map((table) => ({
      ...table,
      title: localizeText(table.title || table.key || 'جدول'),
      subtitle: localizeText(table.subtitle),
      columns: (table.columns || []).map((column) => ({
        ...column,
        label: localizeText(column.label || column.key)
}))
})),
    insights: (report.insights || []).map((item) => ({
      ...item,
      text: localizeText(item.text)
}))
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
    isSecondary: url === String(settingsForm.website_image || '').trim()
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
    kitchen_print_modes: payload.kitchen_print_modes || KITCHEN_PRINT_MODE_OPTIONS,
    stock_consumption_modes:
      payload.stock_consumption_modes || STOCK_CONSUMPTION_MODE_OPTIONS
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

function createEmptyBomItemRow() {
  return {
    item_code: '',
    qty: 1,
    uom: '',
    rate: 0,
    source_warehouse: '',
    allow_alternative_item: false,
    show_in_website: true,
    restaurant_customer_label: '',
    restaurant_is_included_by_default: true,
    restaurant_can_remove: false,
    restaurant_is_required: false,
    restaurant_is_editable_qty: false,
    restaurant_min_multiplier: 0,
    restaurant_max_multiplier: 3,
    restaurant_step_multiplier: 0.5,
    restaurant_multiplier_qty: 0,
    restaurant_extra_when_added: 0,
    restaurant_nutrition_kcal: 0,
    restaurant_nutrition_protein_g: 0,
    restaurant_nutrition_carb_g: 0,
    restaurant_nutrition_sugar_g: 0,
    restaurant_nutrition_fat_g: 0,
    alternatives_count: 0,
    alternatives: []
}
}

function resetBomForm() {
  bomForm.name = ''
  bomForm.quantity = 1
  bomForm.company = String(bomContext.value?.default_company || '').trim()
  bomForm.currency = String(bomContext.value?.default_currency || activeCurrency.value || 'IRR').trim()
  bomForm.is_active = true
  bomForm.is_default = true
  bomForm.restaurant_recipe_instruction = ''
  bomForm.items = [createEmptyBomItemRow()]
  bomForm.restaurant_modifier_rows = []
}

function hydrateBomForm(doc = null) {
  if (!doc) {
    resetBomForm()
    return
  }
  bomForm.name = String(doc.name || '').trim()
  bomForm.quantity = Number(doc.quantity || 1) || 1
  bomForm.company = String(doc.company || bomContext.value?.default_company || '').trim()
  bomForm.currency = String(doc.currency || bomContext.value?.default_currency || activeCurrency.value || 'IRR').trim()
  bomForm.is_active = Number(doc.is_active ?? 1) === 1
  bomForm.is_default = Number(doc.is_default ?? 1) === 1
  bomForm.restaurant_recipe_instruction = String(doc.restaurant_recipe_instruction || '').trim()
  bomForm.items = (Array.isArray(doc.items) ? doc.items : []).map((row) => ({
    ...createEmptyBomItemRow(),
    ...row,
    item_code: String(row?.item_code || '').trim(),
    qty: Number(row?.qty || 0) || 1,
    uom: String(row?.uom || row?.stock_uom || '').trim()
})).filter((row) => row.item_code)
  bomForm.restaurant_modifier_rows = Array.isArray(doc.restaurant_modifier_rows)
    ? doc.restaurant_modifier_rows.map((row) => ({ ...row }))
    : []
  if (!bomForm.items.length) {
    bomForm.items = [createEmptyBomItemRow()]
  }
}

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
    value: String(row?.value || '').trim()
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
const productReadinessChecks = computed(() => [
  {
    key: 'image',
    label: 'تصویر اصلی',
    detail: mainImage.value ? 'تصویر محصول آماده نمایش است.' : 'برای کارت منو تصویر اضافه کنید.',
    ok: Boolean(mainImage.value)
},
  {
    key: 'slug',
    label: 'اسلاگ محصول',
    detail: settingsForm.restaurant_slug ? settingsForm.restaurant_slug : 'برای لینک صفحه مشتری اسلاگ لازم است.',
    ok: Boolean(String(settingsForm.restaurant_slug || '').trim())
},
  {
    key: 'description',
    label: 'توضیح کوتاه',
    detail: settingsForm.restaurant_short_desc ? 'متن کارت محصول تکمیل است.' : 'کارت منو بدون توضیح کوتاه ضعیف‌تر دیده می‌شود.',
    ok: Boolean(String(settingsForm.restaurant_short_desc || '').trim())
},
  {
    key: 'price',
    label: 'قیمت معتبر',
    detail: Number(priceForm.price_list_rate || currentPriceRate.value || 0) > 0 ? formatMoney(Number(priceForm.price_list_rate || currentPriceRate.value || 0), activeCurrency.value) : 'قیمت محصول صفر یا نامشخص است.',
    ok: Number(priceForm.price_list_rate || currentPriceRate.value || 0) > 0
},
  {
    key: 'category',
    label: 'دسته‌بندی',
    detail: selectedCategoryLabel.value || 'برای پیدا شدن راحت‌تر محصول، دسته انتخاب کنید.',
    ok: Boolean(selectedCategoryLabel.value)
},
])
const readinessScore = computed(() => productReadinessChecks.value.filter((check) => check.ok).length)

function getTabBadge(tabValue) {
  if (tabValue === 'overview') {
    const missingCount = productReadinessChecks.value.length - readinessScore.value
    return missingCount > 0 ? `!${missingCount.toLocaleString('fa-IR')}` : '✓'
  }
  if (tabValue === 'variants') {
    return variantRows.value.length ? variantRows.value.length.toLocaleString('fa-IR') : ''
  }
  if (tabValue === 'builder') {
    return settingsForm.restaurant_is_customizable || hasBuilderConfig.value ? 'فعال' : ''
  }
  if (tabValue === 'reports') {
    return hasReportData.value ? 'داده' : ''
  }
  return ''
}

const hasUnsavedChanges = computed(() => {
  if (!detail.value?.item?.name || !settingsSnapshot.value) {
    return false
  }
  return serializeSettingsState() !== settingsSnapshot.value
})

watch(
  () => settingsForm.restaurant_builder_template,
  (templateName) => {
    if (String(templateName || '').trim()) {
      settingsForm.restaurant_is_customizable = true
      settingsForm.restaurant_builder_active = true
    }
  },
)

watch(
  () => builderConfig.value,
  (config) => {
    if (config) {
      settingsForm.restaurant_is_customizable = true
      settingsForm.restaurant_builder_active = true
    }
  },
  { deep: true },
)

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
    if (nextTab === 'changes' && !activityLoaded) {
      await loadProductActivity()
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
      attributes: nextAttributes
}
  },
)

function cloneBuilderConfig(config = null) {
  return clonePlainObject(config)
}

// ── تب «تغییرات»: تاریخچه و نظرات ─────────────────────────────────────────
const activityLoading = ref(false)
const activityVersions = ref([])
const activityComments = ref([])
const commentDraft = ref('')
const commentSaving = ref(false)
let activityLoaded = false

const ACTIVITY_FIELD_LABELS = {
  item_name: 'نام کالا',
  item_code: 'کد کالا',
  item_group: 'گروه کالا',
  stock_uom: 'واحد',
  restaurant_enabled: 'وضعیت نمایش',
  restaurant_coming_soon: 'به‌زودی',
  restaurant_out_of_stock: 'ناموجود',
  restaurant_category: 'دسته',
  restaurant_subcategory: 'زیردسته',
  restaurant_short_desc: 'توضیح کوتاه',
  restaurant_long_desc: 'توضیح کامل',
  restaurant_sort_order: 'ترتیب نمایش',
  restaurant_prep_time_mins: 'زمان آماده‌سازی',
  restaurant_is_featured: 'محصول ویژه',
  restaurant_is_best_seller: 'پرفروش',
  restaurant_requires_bom: 'نیازمند BOM',
  restaurant_auto_add_to_order: 'افزودن خودکار',
  restaurant_branch: 'شعبه',
  restaurant_slug: 'اسلاگ',
  image: 'تصویر',
  disabled: 'غیرفعال در ERPNext',
  restaurant_packaging_price: 'هزینه بسته‌بندی',
  restaurant_show_in_website: 'نمایش در وب',
  restaurant_item_tags: 'تگ‌ها'
}

function fieldLabel(field) {
  return ACTIVITY_FIELD_LABELS[field] || field
}

function formatChangeValue(value) {
  if (value === 1 || value === true) return 'بله'
  if (value === 0 || value === false) return 'خیر'
  if (value === null || value === undefined || value === '') return '—'
  const text = String(value)
  return text.length > 60 ? `${text.slice(0, 60)}…` : text
}

function parseVersionChanges(ver) {
  try {
    const parsed = JSON.parse(ver?.data || '{}')
    const items = []
    for (const entry of parsed.changed || []) {
      if (!Array.isArray(entry) || entry.length < 3) continue
      const fieldName = String(entry[0] || '').trim()
      if (fieldName === 'modified' || fieldName === 'modified_by') continue
      items.push({
        field: String(entry[0] || '').trim(),
        old: formatChangeValue(entry[1]),
        new: formatChangeValue(entry[2])
})
    }
    return items
  } catch (_) {
    return []
  }
}

async function loadProductActivity() {
  const itemName = String(detail.value?.item?.name || detail.value?.item?.item_code || '').trim()
  if (!itemName || activityLoading.value) return
  activityLoading.value = true
  try {
    const payload = await getManagementProductActivity({ item_name: itemName })
    activityVersions.value = Array.isArray(payload?.versions) ? payload.versions : []
    activityComments.value = Array.isArray(payload?.comments) ? payload.comments : []
    activityLoaded = true
  } catch (errObj) {
    error.value = errObj?.message || 'بارگذاری تاریخچه محصول ناموفق بود.'
  } finally {
    activityLoading.value = false
  }
}

async function submitComment() {
  const itemName = String(detail.value?.item?.name || detail.value?.item?.item_code || '').trim()
  const text = String(commentDraft.value || '').trim()
  if (!itemName || !text || commentSaving.value) return
  commentSaving.value = true
  try {
    const payload = await addManagementProductComment({ item_name: itemName, content: text })
    activityComments.value = [
      {
        name: payload?.name || `c-${Date.now()}`,
        creation: payload?.creation || '',
        owner: 'شما',
        content: text
},
      ...activityComments.value,
    ]
    commentDraft.value = ''
  } catch (errObj) {
    error.value = errObj?.message || 'ثبت نظر ناموفق بود.'
  } finally {
    commentSaving.value = false
  }
}

function syncForms(payload) {
  hydrateProductSettingsForm(settingsForm, payload, allTagOptions.value)

  const item = payload?.item || {}
  builderSourceTemplateName.value = String(payload?.builder?.template_name || item.restaurant_builder_template || '').trim()
  builderConfig.value = cloneBuilderConfig(payload?.builder?.product_builder_config || null)

  selectedDefaultPriceList.value = payload?.pricing?.default_price_list || ''
  priceForm.price_list = payload?.pricing?.default_price_list || priceLists.value?.[0]?.name || ''
  priceForm.price_list_rate = Number(payload?.pricing?.current_price?.price_list_rate || item.base_price || 0)
  priceForm.valid_from = ''
  selectedImage.value = payload?.media?.main_image || ''
  settingsSnapshot.value = serializeSettingsState()
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

// ─── Tag management ──────────────────────────────────────────────────
const TAG_FIELD = 'restaurant_item_tag_table'

// Get all available tags for autocomplete
const allTagOptions = ref([])

const tagList = computed({
  get() {
    const links = settingsForm[TAG_FIELD] || []
    return links.map(l => {
      // l.tag is the link name, we need the title
      return l._tag_title || l.tag_title || l.tag || ''
    }).filter(Boolean)
  },
  set(val) {
    // Rebuild child table rows
    const current = settingsForm[TAG_FIELD] || []
    const newTags = Array.isArray(val) ? val : []

    // Remove tags not in new list
    const toRemove = current.filter(l => {
      const title = l._tag_title || l.tag_title || l.tag || ''
      return !newTags.includes(title)
    })
    for (const r of toRemove) {
      const idx = current.indexOf(r)
      if (idx >= 0) current.splice(idx, 1)
    }

    // Add new tags
    for (const t of newTags) {
      const exists = current.some(l => (l._tag_title || l.tag_title || l.tag || '') === t)
      if (!exists) {
        // Find tag doc name from options
        const opt = allTagOptions.value.find(o => o.label === t)
        current.push({
          tag: opt ? opt.value : t,
          _tag_title: t
})
      }
    }
    settingsForm[TAG_FIELD] = [...current]
  }
})

function handleCreateTagOption(rawValue) {
  const title = String(rawValue || '').trim().replace(/,$/, '').trim()
  if (!title) {
    return
  }
  if (!allTagOptions.value.some((option) => String(option?.label || option?.value || '').trim() === title)) {
    allTagOptions.value = [...allTagOptions.value, { value: title, label: title }]
  }
  if (!tagList.value.includes(title)) {
    tagList.value = [...tagList.value, title]
  }
}

async function loadTagOptions() {
  try {
    allTagOptions.value = await listRestaurantItemTags({ limit: 500 })
  } catch (tagError) {
    allTagOptions.value = []
  }
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
      date_to: filters.date_to
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
    resetBomForm()
    return
  }

  bomLoading.value = true
  bomError.value = ''
  try {
    const [rows, context] = await Promise.all([
      listManagementBoms({ item_code: normalizedItem, limit: 80 }),
      getManagementBomContext(),
    ])
    productBoms.value = Array.isArray(rows) ? rows : []
    bomContext.value = context || { companies: [], currencies: [], default_company: '', default_currency: '' }

    const targetBomName = String(activeBomName.value || defaultBomName.value || '').trim()
    if (targetBomName) {
      try {
        const doc = await getManagementBomDoc(targetBomName)
        hydrateBomForm(doc)
      } catch {
        resetBomForm()
      }
    } else {
      resetBomForm()
    }
  } catch (bomErr) {
    bomError.value = bomErr.message || 'دریافت لیست BOM ناموفق بود.'
    productBoms.value = []
    resetBomForm()
  } finally {
    bomLoading.value = false
  }
}

async function searchBomItems(query = '') {
  try {
    const rows = await listManagementBomItems({ search: query, limit: 100 })
    bomItemCatalog.value = Array.isArray(rows) ? rows : []
    bomItemOptions.value = (Array.isArray(rows) ? rows : []).map((row) => {
      const value = String(row?.item_code || row?.name || '').trim()
      const title = String(row?.item_name || row?.name || value).trim()
      return {
        value,
        label: value && title !== value ? `${title} (${value})` : title,
        stock_uom: String(row?.stock_uom || '').trim()
}
    }).filter((row) => row.value)
  } catch {
    bomItemCatalog.value = []
    bomItemOptions.value = []
  }
}

async function loadBomModifierGroupOptions() {
  try {
    const rows = await listManagementModifierGroups({ limit: 300 })
    bomModifierGroupOptions.value = (Array.isArray(rows) ? rows : []).map((row) => {
      const value = String(row?.name || '').trim()
      const label = String(row?.title || row?.name || '').trim() || value
      return { value, label }
    }).filter((row) => row.value)
  } catch {
    bomModifierGroupOptions.value = []
  }
}

async function loadBomDocIntoForm(bomName = '') {
  const normalized = String(bomName || '').trim()
  if (!normalized) {
    return
  }
  bomLoading.value = true
  bomError.value = ''
  try {
    const doc = await getManagementBomDoc(normalized)
    hydrateBomForm(doc)
  } catch (errObj) {
    bomError.value = errObj.message || 'دریافت فرمول محصول ناموفق بود.'
  } finally {
    bomLoading.value = false
  }
}

function addBomItemRow() {
  bomForm.items.push(createEmptyBomItemRow())
}

async function saveBomFromProduct() {
  const normalizedItem = String(detail.value?.item?.name || detail.value?.item?.item_code || '').trim()
  if (!normalizedItem) {
    bomError.value = 'محصول معتبری برای ثبت BOM پیدا نشد.'
    return
  }

  const normalizedItems = (Array.isArray(bomForm.items) ? bomForm.items : [])
    .map((row) => ({
      ...row,
      item_code: String(row?.item_code || '').trim(),
      qty: Number(row?.qty || 0),
      uom: String(row?.uom || '').trim()
}))
    .filter((row) => row.item_code && row.qty > 0 && row.uom)

  if (!normalizedItems.length) {
    bomError.value = 'حداقل یک ماده اولیه معتبر برای BOM وارد کنید.'
    return
  }

  bomSaving.value = true
  bomError.value = ''
  bomSaveSuccess.value = ''
  try {
    const payload = {
      name: String(bomForm.name || '').trim(),
      item: normalizedItem,
      quantity: Number(bomForm.quantity || 1) || 1,
      company: String(bomForm.company || '').trim(),
      currency: String(bomForm.currency || '').trim(),
      is_active: bomForm.is_active,
      is_default: bomForm.is_default,
      restaurant_recipe_instruction: String(bomForm.restaurant_recipe_instruction || '').trim(),
      items: normalizedItems,
      restaurant_modifier_rows: Array.isArray(bomForm.restaurant_modifier_rows)
        ? bomForm.restaurant_modifier_rows
        : []
}

    if (payload.name) {
      await updateManagementBom(payload)
      bomSaveSuccess.value = 'فرمول و رسپی محصول بروزرسانی شد.'
    } else {
      await createManagementBom(payload)
      bomSaveSuccess.value = 'فرمول و رسپی محصول ثبت شد.'
    }

    await loadProductBoms(normalizedItem)
  } catch (saveErr) {
    bomError.value = saveErr.message || 'ذخیره فرمول و رسپی ناموفق بود.'
  } finally {
    bomSaving.value = false
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
  const resolvedPriceList = String(priceForm.price_list || selectedDefaultPriceList.value || priceLists.value?.[0]?.name || '').trim()
  if (!resolvedPriceList) {
    error.value = 'برای ثبت قیمت، ابتدا یک لیست قیمت انتخاب کنید.'
    return
  }
  savingPrice.value = true
  error.value = ''
  try {
    await setManagementProductPrice({
      item_name: detail.value.item.name,
      price_list: resolvedPriceList,
      price_list_rate: Number(priceForm.price_list_rate || 0),
      valid_from: priceForm.valid_from || ''
})
    await loadDetail()
  } catch (errObj) {
    error.value = errObj.message || 'ثبت قیمت محصول ناموفق بود.'
  } finally {
    savingPrice.value = false
  }
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
        is_default: valueRow.value === normalizedValue ? 1 : 0
}))
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
      [attrName]: current.filter((value) => value !== normalizedValue)
}
    return
  }
  selectedValuesByAttribute.value = {
    ...selectedValuesByAttribute.value,
    [attrName]: [...current, normalizedValue]
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
        is_default: Number(valueRow.is_default || 0) ? 1 : 0
}))
}))

  return {
    item_name: String(detail.value?.item?.name || itemName.value || '').trim(),
    selected_attributes: Array.from(selectedSet),
    attribute_settings: attributeSettings
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

function openVariantCreationDialog() {
  variantCreationForm.value = {
    attributes: {},
    create_multiple: false
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
        [normalized]: (attr.values || []).map((row) => row.value)
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
          is_default: 0
},
      ]
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
        [normalizedAttribute]: nextRows
}
}
    return
  }

  variantCreationForm.value = {
    ...variantCreationForm.value,
    attributes: {
      ...(variantCreationForm.value.attributes || {}),
      [normalizedAttribute]: normalizedValue
}
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
      selected_values_by_attribute: selectedVals
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

const mediaPreviewItem = computed(() => {
  const item = detail.value?.item || {}
  const price = Number(priceForm.price_list_rate || item.restaurant_base_price || item.standard_rate || 0)
  return {
    name: item.name,
    title: String(settingsForm.item_name || item.item_name || item.name || '-').trim(),
    slug: String(settingsForm.restaurant_slug || item.restaurant_slug || '').trim(),
    short_desc: String(settingsForm.restaurant_short_desc || item.restaurant_short_desc || '').trim(),
    image: mainImage.value,
    base_price: price,
    category_title: selectedCategoryLabel.value || '',
    tags: Array.isArray(settingsForm.restaurant_item_tag_table)
      ? settingsForm.restaurant_item_tag_table.map((t) => t._tag_title || t.tag).filter(Boolean)
      : [],
    coming_soon: settingsForm.restaurant_coming_soon ? 1 : 0
}
})

function openMediaDialog() {
  clearMediaMessages()
  mediaDialogOpen.value = true
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
        is_private: 0
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
      image: String(url || '').trim()
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
      website_image: String(url || '').trim()
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
      file_url: normalizedUrl
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

function loadBuilderItemOptions() {
  return callMethodByPathGET('restaurant.api.list_builder_option_items', { limit: 500 })
    .then((result) => {
      const data = result?.data || result
      const rows = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
      builderItemOptions.value = rows.map((r) => ({
        value: r.value || r.name,
        label: r.label || r.item_name || r.name,
        item_name: r.item_name || r.label || r.name,
        item_code: r.item_code || r.name,
        image: r.image || '',
        standard_rate: Number(r.standard_rate) || 0,
        stock_uom: r.stock_uom || '',
        price_list: r.price_list || '',
        price_status: r.price_status || '',
        is_selectable: Number(r.is_selectable ?? 1) === 1,
        unavailable_reason: r.unavailable_reason || '',
        item_group: r.item_group || ''
}))
    })
    .catch(() => {
      builderItemOptions.value = []
    })
}

async function applyBuilderTemplateToProduct() {
  const templateName = String(settingsForm.restaurant_builder_template || '').trim()
  if (!templateName) {
    builderConfig.value = null
    return
  }
  const result = await callMethodByPathGET('restaurant.api.get_builder_template_detail', { name: templateName })
  const data = result?.data || result
  const template = data?.template || data
  builderConfig.value = cloneBuilderConfig(template)
  builderSourceTemplateName.value = templateName
}

function addBuilderStep() {
  if (!builderConfig.value) {
    builderConfig.value = {
      name: '',
      title: settingsForm.item_name || 'سفارشی‌سازی محصول',
      slug: '',
      description: '',
      is_active: true,
      layout_mode: 'vertical_steps',
      show_summary_panel: true,
      show_price_live: true,
      primary_color: 'var(--mg-primary)',
      background_image: '',
      allow_skip_steps: false,
      allow_go_back: true,
      require_all_required: true,
      max_total_selections: 0,
      steps: []
}
  }
  builderConfig.value.steps.push(createEmptyBuilderStep(builderConfig.value.steps.length))
}

function updateBuilderStep(index, updatedStep) {
  if (!builderConfig.value?.steps) return
  builderConfig.value.steps[index] = { ...updatedStep }
}

function moveBuilderStep(index, direction) {
  if (!builderConfig.value?.steps) return
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= builderConfig.value.steps.length) return
  const temp = builderConfig.value.steps[index]
  builderConfig.value.steps.splice(index, 1)
  builderConfig.value.steps.splice(newIndex, 0, temp)
  builderConfig.value.steps.forEach((row, i) => {
    row.sort_order = i
  })
}

function deleteBuilderStep(index) {
  if (!builderConfig.value?.steps) return
  builderConfig.value.steps.splice(index, 1)
  builderConfig.value.steps.forEach((row, i) => {
    row.sort_order = i
  })
}

function resetBuilderToTemplate() {
  return applyBuilderTemplateToProduct()
}

function serializeSettingsState() {
  return serializeProductSettingsState(settingsForm, builderConfig.value)
}

function buildSettingsPayload() {
  return buildProductSettingsPayload({
    itemName: detail.value?.item?.name,
    form: settingsForm,
    builderConfig: builderConfig.value
})
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

function readStoredDetailTab() {
  try {
    const raw = localStorage.getItem('management-product-detail-tab')
    if (PRODUCT_DETAIL_TABS.some((tab) => tab.value === raw)) {
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
  searchBomItems('')
  loadBomModifierGroupOptions()
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('keydown', onWindowKeydown)
  cleanupPreviewViewportListener()
  clearNavbarTitle()
})

Promise.all([loadBuilderItemOptions(), loadTagOptions(), loadDetail()])
</script>

<style scoped>
.page-breadcrumbs {
  margin-bottom: 0.35rem;
  padding-inline: 0.15rem;
}

@media (max-width: 640px) {
  .pg-image-edit-btn {
    width: 34px;
    height: 34px;
  }

  .pg-image-edit-btn svg {
    width: 16px;
    height: 16px;
  }

  .page-breadcrumbs {
    margin-bottom: 0.55rem;
    padding-inline: 0;
  }
}

/* فضای خالی پایین صفحه تا نوار ثابت ذخیره روی محتوا نیفتد */
.management-page {
  padding-bottom: 104px;
}

.page-sticky-actions {
  position: sticky;
  top: 0.85rem;
  z-index: 18;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  padding: 0.5rem;
  border: 1px solid var(--mg-border);
  border-radius: 16px;
  background: var(--mg-bg-surface);
  backdrop-filter: blur(16px);
  box-shadow: var(--mg-shadow-md);
}

.product-general-card {
  overflow: hidden;
}

.product-general-layout {
  display: grid;
  grid-template-columns: minmax(170px, 0.72fr) minmax(360px, 1.28fr) minmax(320px, 1fr);
  gap: 0.72rem;
  align-items: start;
}

/* کارت فشرده «اطلاعات کلی» */
.product-general-card--compact .product-general-layout {
  grid-template-columns: minmax(108px, 0.5fr) minmax(360px, 1.5fr);
  align-items: center;
}

.product-general-card--compact .general-image-shell {
  height: clamp(96px, 10vw, 132px);
  min-height: 96px;
}

/* دکمه شناور کوچک مدیریت تصاویر روی عکس */
.general-image-shell.is-clickable {
  cursor: pointer;
}

.pg-image-edit-btn {
  position: absolute;
  bottom: 0.4rem;
  inset-inline-end: 0.4rem;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 0.7);
  background: rgb(30 22 17 / 0.62);
  backdrop-filter: blur(4px);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  box-shadow: 0 3px 10px rgb(0 0 0 / 0.28);
  transition: background 0.15s ease, transform 0.15s ease;
}

.pg-image-edit-btn:hover {
  background: var(--mg-primary);
  transform: scale(1.06);
}

.pg-image-edit-btn:active {
  transform: scale(0.94);
}

/* مودال تصاویر */
.media-dialog-body {
  display: grid;
  gap: 0.6rem;
  min-width: 0;
}

/* پیش‌نمایش کارت محصول داخل مودال تصاویر */
.media-preview-box {
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  background: var(--mg-bg-page);
  padding: 0.7rem;
  display: grid;
  gap: 0.6rem;
}

.media-preview-head {
  display: grid;
  gap: 0.15rem;
}

.media-preview-head strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
}

.media-preview-head small {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.media-preview-card-wrap {
  display: flex;
  justify-content: center;
}

.media-preview-card-wrap :deep(.product-card) {
  max-width: 260px;
  width: 100%;
}

.media-preview-card-wrap :deep(a),
.media-preview-card-wrap :deep(button) {
  pointer-events: none !important;
  cursor: default !important;
}

.media-divider {
  height: 1px;
  background: var(--mg-border-light);
  margin: 0.2rem 0;
}

.product-general-card--compact .product-general-fields {
  display: grid;
  gap: 0.5rem;
}

.pg-name-field input {
  min-height: 2.3rem;
}

.stock-toggle-btn {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-success, #6f7b56);
  font: inherit;
  font-size: 0.76rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 0.42rem 1.1rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.stock-toggle-btn.active {
  border-color: var(--mg-danger, #a6543f);
  background: color-mix(in srgb, var(--mg-danger, #a6543f) 12%, transparent);
  color: var(--mg-danger, #a6543f);
}

.oos-toggle-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.restock-field {
  display: grid;
  gap: 0.3rem;
  padding: 0.35rem 0;
  border-bottom: 1px dashed var(--mg-border-light);
}

.pg-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.pg-status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.14rem 0.55rem;
  font-size: 0.66rem;
  font-weight: 800;
  white-space: nowrap;
}

.pg-status-pill.is-on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
}

.pg-status-pill.is-off {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent);
}

.pg-status-pill.is-soon {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.pg-status-pill.is-warn {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
}

.pg-status-pill.is-code {
  direction: ltr;
  color: var(--mg-text-muted);
  background: var(--mg-bg-soft);
  font-weight: 600;
}

.pg-status-pill--btn {
  border: 1px solid var(--mg-border-light);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.pg-status-pill--btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light));
}

.pg-status-pill.is-kitchen-on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 30%, var(--mg-border-light));
}

.pg-status-pill.is-kitchen-off {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent);
}

.pg-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.pg-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border-radius: 999px;
  padding: 0.14rem 0.55rem;
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  background: var(--mg-bg-soft);
  border: 1px solid var(--mg-border-light);
}

.pg-meta-chip strong {
  color: var(--mg-text-main);
}

.pg-readiness {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.14rem 0.55rem;
  font-size: 0.66rem;
  font-weight: 800;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

.pg-readiness.is-ready {
  color: var(--mg-success);
  background: var(--mg-success-bg);
}

.pg-quick-toggles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
}

.pg-quick-toggles .toggle-switch {
  min-height: 2.6rem;
  padding: 0.35rem 0.55rem;
}

.pg-quick-toggles .switch-copy strong {
  font-size: 0.78rem;
}

.pg-quick-toggles .switch-track {
  width: 2.35rem;
  height: 1.35rem;
}

.pg-quick-toggles .switch-thumb {
  width: 0.95rem;
  height: 0.95rem;
}

.pg-quick-toggles .toggle-switch.checked .switch-thumb {
  transform: translateX(-1rem);
}

.product-general-main,
.product-general-side {
  min-width: 0;
  display: grid;
  gap: 0.56rem;
  align-content: start;
}

.product-general-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.52rem;
  align-content: start;
}

.product-general-fields label {
  display: grid;
  gap: 0.24rem;
  color: var(--mg-text-muted);
  font-size: 0.8rem;
  font-weight: 800;
  min-width: 0;
}

.price-inline-field {
  grid-column: span 1;
  display: grid;
  gap: 0.24rem;
  color: var(--mg-text-muted);
  font-size: 0.8rem;
  font-weight: 800;
  min-width: 0;
}

.price-inline-control {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.4rem;
  align-items: center;
}

.price-preview-input {
  font-weight: 900;
  color: var(--module-600, var(--mg-primary)) !important;
  font-variant-numeric: tabular-nums;
}

.product-general-media {
  min-width: 0;
  display: grid;
  gap: 0.45rem;
  align-content: start;
}

.general-image-shell {
  position: relative;
  height: clamp(150px, 18vw, 210px);
  min-height: 150px;
  aspect-ratio: 1 / 1;
  border: 1px solid var(--mg-border);
  border-radius: var(--mg-radius-md);
  background:
    radial-gradient(circle at 18% 18%, var(--mg-bg-soft), transparent 34%),
    var(--mg-bg-surface);
  display: grid;
  place-items: center;
  overflow: hidden;
  box-shadow: var(--mg-shadow-sm);
}

.general-product-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  background: var(--bg-card, #fff);
}

.general-image-empty {
  display: grid;
  justify-items: center;
  gap: 0.4rem;
  color: var(--muted, var(--mg-text-muted));
  text-align: center;
}

.general-image-empty span {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: var(--bg-card, #fff);
  border: 1px solid var(--mg-border);
  color: var(--module-600, var(--mg-primary));
  font-size: 1.35rem;
  font-weight: 900;
}

.general-image-empty p {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 800;
}

.product-general-toggles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.42rem;
}

.product-general-toggles :deep(.toggle-switch) {
  min-height: 4.55rem;
  padding: 0.56rem 0.62rem;
}

.product-general-toggles :deep(.switch-copy) {
  gap: 0.12rem;
}

.product-general-toggles :deep(.switch-copy strong) {
  font-size: 0.78rem;
}

.product-general-toggles :deep(.switch-copy small) {
  font-size: 0.68rem;
  line-height: 1.55;
}

.product-general-nutrition {
  margin-bottom: 0;
}

.product-general-meta-row {
  display: grid;
  gap: 0.42rem;
}

.mini-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.38rem 0.65rem;
  border-radius: 999px;
  background: var(--mg-bg-soft);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
  font-size: 0.75rem;
}

.mini-meta-chip strong {
  font-size: 0.72rem;
  color: var(--mg-text-muted);
}

.mini-readiness-row {
  display: flex;
  align-items: center;
  gap: 0.34rem;
  flex-wrap: wrap;
  min-width: 0;
}

.mini-readiness-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0.22rem 0.58rem;
  border-radius: 999px;
  background: var(--module-50);
  color: var(--module-title-light);
  font-size: 0.74rem;
  font-weight: 900;
  white-space: nowrap;
}

.mini-readiness-items {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  flex-wrap: wrap;
  min-width: 0;
}

.mini-readiness-pill {
  min-height: 1.72rem;
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--mg-border);
  background: var(--mg-bg-surface);
  font-size: 0.68rem;
  font-weight: 800;
  white-space: nowrap;
}

.mini-readiness-pill.is-ok {
  border-color: color-mix(in srgb, var(--mg-success) 25%, transparent);
  background: color-mix(in srgb, var(--mg-success) 10%, transparent);
  color: var(--mg-success);
}

.mini-readiness-pill.is-missing {
  border-color: color-mix(in srgb, var(--mg-danger) 20%, transparent);
  background: color-mix(in srgb, var(--mg-danger) 8%, transparent);
  color: var(--mg-danger);
}

.quick-price-save {
  min-width: 108px;
  min-height: 2.65rem;
  white-space: nowrap;
}

.formula-workspace {
  display: grid;
  gap: 1rem;
  margin: 0.95rem 0 0.75rem;
}

.formula-block {
  display: grid;
  gap: 0.75rem;
}

.formula-block__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.formula-block__head strong {
  display: block;
  font-size: 0.95rem;
  color: var(--mg-text-main);
}

.formula-block__head small {
  display: block;
  margin-top: 0.18rem;
  color: var(--mg-text-muted);
}

.formula-block__meta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--mg-olive) 18%, transparent);
  background: color-mix(in srgb, var(--mg-bg-surface) 92%, transparent);
  color: var(--mg-text-muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.bom-inline-list {
  display: grid;
  gap: 0.55rem;
  margin: 0.75rem 0;
}

.bom-inline-card {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) minmax(120px, 0.5fr) minmax(110px, 0.45fr) auto;
  gap: 0.5rem;
  align-items: end;
  padding: 0.65rem;
  border: 1px solid var(--mg-border);
  border-radius: 14px;
  background: var(--mg-bg-soft);
}

.bom-inline-card label {
  display: grid;
  gap: 0.22rem;
  color: var(--mg-text-muted);
  font-size: 0.78rem;
  font-weight: 800;
  min-width: 0;
}

.danger-btn {
  color: var(--mg-danger) !important;
  border-color: color-mix(in srgb, var(--mg-danger) 28%, transparent) !important;
}

.section-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 0.75rem;
  border-radius: var(--mg-radius-md);
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-sm);
}

.simple-tabs {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  flex-wrap: wrap;
}

.simple-tab {
  min-height: 2.75rem;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--mg-text-muted);
  padding: 0.34rem 0.68rem;
  font-size: 0.78rem;
  font-weight: 850;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.34rem;
  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
  touch-action: manipulation;
}

.simple-tab:active {
  transform: scale(0.98);
}

.tab-badge {
  min-width: 1.32rem;
  min-height: 1.32rem;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  padding: 0 0.34rem;
  background: var(--module-50);
  color: var(--module-title-light);
  font-size: 0.66rem;
  line-height: 1;
}

.simple-tab:hover {
  background: var(--mg-bg-soft);
  border-color: var(--mg-border);
  color: var(--mg-text-main);
}

.simple-tab.active {
  background: var(--mg-bg-surface);
  border-color: color-mix(in srgb, var(--mg-primary) 28%, transparent);
  color: var(--mg-text-main);
  box-shadow: inset 0 -2px 0 color-mix(in srgb, var(--mg-primary) 55%, transparent);
}

.tab-hint {
  margin: 0.42rem 0 0;
  color: var(--mg-text-muted);
  font-size: 0.78rem;
  line-height: 1.65;
}

.unsaved-note {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
  color: var(--mg-danger);
}

.unsaved-chip {
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--mg-danger) 30%, transparent);
  background: color-mix(in srgb, var(--mg-danger) 10%, transparent);
  color: var(--mg-danger);
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

.product-changes-grid {
  display: grid;
  gap: 0.75rem;
}

.changes-timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.65rem;
}

.change-item {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.6rem 0.7rem;
  display: grid;
  gap: 0.4rem;
}

.change-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.change-item-head strong {
  font-size: 0.78rem;
  color: var(--mg-primary);
}

.change-item-date,
.comment-item-date {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
}

.change-fields {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.25rem;
}

.change-fields li {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  font-size: 0.72rem;
  padding: 0.18rem 0.4rem;
  border-radius: 8px;
  background: var(--mg-bg-page);
}

.change-field {
  font-weight: 800;
  color: var(--mg-text-main);
  min-width: 90px;
}

.change-old {
  color: var(--mg-text-muted);
  text-decoration: line-through;
  opacity: 0.75;
}

.change-arrow {
  color: var(--mg-primary);
}

.change-new {
  color: var(--mg-success);
  font-weight: 700;
}

.change-more {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.change-empty {
  margin: 0;
  font-size: 0.72rem;
}

.comments-list {
  display: grid;
  gap: 0.55rem;
  margin-bottom: 0.7rem;
}

.comment-item {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.55rem 0.65rem;
  display: grid;
  gap: 0.3rem;
}

.comment-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.comment-item-head strong {
  font-size: 0.76rem;
  color: var(--mg-text-main);
}

.comment-content {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.8;
  color: var(--mg-text-main);
  white-space: pre-wrap;
}

.comment-form {
  display: grid;
  gap: 0.5rem;
  border-top: 1px dashed var(--mg-border-light);
  padding-top: 0.65rem;
}

.comment-form-actions {
  display: flex;
  justify-content: flex-end;
}

.comment-form .textarea {
  min-height: 64px;
  background: var(--mg-bg-page);
}

.product-top-grid,
.product-settings-grid,
.charts-grid,
.tables-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.72rem;
  min-width: 0;
}

.charts-grid > *,
.tables-grid > * {
  min-width: 0;
}

.identity-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 0.58rem;
}

.identity-grid label {
  display: grid;
  gap: 0.22rem;
  color: var(--mg-text-muted);
  font-size: 0.78rem;
  font-weight: 700;
  min-width: 0;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-text-muted);
}

.field-help {
  font-size: 0.72rem;
  line-height: 1.65;
  color: var(--mg-text-muted);
}

.checks-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.42rem;
  margin: 0.45rem 0 0.62rem;
}

.nutrition-box {
  border: 1px solid var(--mg-border);
  border-radius: 12px;
  background: var(--mg-bg-soft);
  padding: 0.5rem;
  margin-bottom: 0.58rem;
}

.nutrition-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.45rem;
  margin-bottom: 0.42rem;
}

.nutrition-head strong {
  color: var(--mg-text-main);
  font-size: 0.84rem;
}

.nutrition-head small {
  color: var(--mg-text-muted);
  font-size: 0.7rem;
  line-height: 1.55;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.38rem;
}

.nutrition-grid label {
  display: grid;
  gap: 0.22rem;
  color: var(--mg-text-muted);
  font-size: 0.76rem;
  font-weight: 800;
  min-width: 0;
}

.check {
  display: inline-flex;
  align-items: center;
  min-height: 2.65rem;
  gap: 0.4rem;
  font-size: 0.84rem;
}

.check--highlight {
  background: var(--module-50);
  border-radius: 8px;
  padding: 0.45rem 0.65rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 14%, transparent);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
  margin-right: auto;
}

.status-dot.on {
  background: var(--mg-success);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-success) 20%, transparent);
}

.status-dot.off {
  background: var(--mg-danger);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--mg-danger) 20%, transparent);
}

.image-shell {
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-soft);
  min-height: 200px;
  display: grid;
  place-items: center;
  margin-bottom: 0.75rem;
  overflow: hidden;
}

.image-shell--simple {
  margin-bottom: 0.6rem;
}

.media-manage-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.main-image {
  width: 100%;
  height: min(52vh, 360px);
  max-height: 360px;
  object-fit: contain;
  object-position: center;
  background: var(--mg-bg-surface);
  border-radius: 8px;
}

.gallery {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
}

.gallery-item {
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 20%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--mg-bg-surface) 50%, transparent);
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
  margin: 0.35rem 0 0.75rem;
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
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-soft);
  padding: 0.75rem;
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
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-surface);
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
  border-bottom: 1px solid var(--mg-border);
  padding: 0.58rem 0.6rem;
  text-align: right;
  font-size: 0.77rem;
  vertical-align: middle;
}

.variant-editor-table th,
.variant-values-table th {
  background: var(--mg-bg-soft);
  color: var(--mg-text-muted);
  font-size: 0.74rem;
}

.variant-editor-table tbody tr.active {
  background: var(--module-50);
}

.variant-clickable-row {
  cursor: pointer;
}

.variant-clickable-row:hover {
  background: var(--mg-bg-soft);
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
  color: var(--mg-text-muted);
}

.variant-values-shell {
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-surface);
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

.bom-status-section {
  display: grid;
  gap: 0.55rem;
  margin: 0.1rem 0 0.2rem;
}

.bom-status-section__head {
  display: grid;
  gap: 0.12rem;
}

.bom-status-section__head strong {
  font-size: 0.84rem;
}

.bom-status-section__head small {
  color: var(--mg-text-muted);
  font-size: 0.74rem;
  line-height: 1.6;
}

.variant-attribute-mobile-card,
.variant-value-mobile-card,
.variant-mobile-card {
  border: 1px solid var(--mg-border);
  border-radius: 8px;
  background: var(--mg-bg-surface);
  padding: 0.55rem;
  display: grid;
  gap: 0.45rem;
}

.variant-attribute-mobile-card.active {
  border-color: color-mix(in srgb, var(--mg-primary) 26%, transparent);
  box-shadow: 0 14px 28px rgb(0 0 0 / 0.08);
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
  color: var(--mg-text-muted);
}

.variant-desktop-table {
  display: block;
}

.sticky-save-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 13000;
  margin: 0;
  width: 100%;
  border: none;
  border-top: 1px solid color-mix(in srgb, var(--mg-primary) 24%, transparent);
  border-radius: 0;
  background: color-mix(in srgb, var(--mg-bg-surface) 94%, transparent);
  backdrop-filter: blur(18px);
  box-shadow: 0 -12px 40px rgb(0 0 0 / 0.14);
  padding: 0.6rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
}

.sticky-save-bar:not(.is-dirty) {
  border-color: var(--mg-border-light);
  box-shadow: 0 12px 40px rgb(0 0 0 / 0.12);
  justify-content: flex-end;
}

.sticky-save-bar:not(.is-dirty) .save-spark-btn {
  opacity: 0.75;
}

.sticky-save-bar > div {
  display: grid;
  gap: 0.1rem;
}

.sticky-save-bar strong {
  color: var(--mg-text-main);
  font-size: 0.84rem;
}

.sticky-save-bar small {
  color: var(--mg-text-muted);
  font-size: 0.72rem;
}

.save-spark-btn {
  position: relative;
  overflow: hidden;
}

.save-spark-btn::after {
  content: '';
  position: absolute;
  inset: -60% auto -60% -40%;
  width: 38%;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgb(255 255 255 / 0.45), transparent);
  transform: skewX(-18deg) translateX(-140%);
  animation: save-sheen 2.8s ease-in-out infinite;
}

@keyframes save-sheen {
  0%, 58% { transform: skewX(-18deg) translateX(-140%); }
  82%, 100% { transform: skewX(-18deg) translateX(420%); }
}

@media (max-width: 1180px) {
  .product-general-layout {
    grid-template-columns: minmax(150px, 0.45fr) minmax(0, 1fr);
  }

  .product-general-side {
    grid-column: 1 / -1;
  }

  .product-general-toggles {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .page-sticky-actions {
    position: sticky;
    top: 0.65rem;
    width: 100%;
    justify-content: space-between;
    padding: 0.45rem;
    border-radius: 14px;
  }

  .page-sticky-actions > * {
    flex: 1 1 calc(50% - 0.3rem);
  }

  .page-sticky-actions .unsaved-chip {
    flex-basis: 100%;
    text-align: center;
  }

  .page-sticky-actions .primary-btn,
  .page-sticky-actions .secondary-btn {
    width: 100%;
    justify-content: center;
  }

  .product-general-layout,
  .product-top-grid,
  .product-settings-grid,
  .charts-grid,
  .tables-grid,
  .identity-grid,
  .checks-grid,
  .product-general-fields,
  .product-general-toggles,
  .nutrition-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  /* کارت فشرده اطلاعات کلی: یکردیفه می‌ماند (عکس + قیمت + سوییچ‌ها) */
  .product-general-card--compact .product-general-layout {
    grid-template-columns: minmax(80px, 0.36fr) minmax(0, 1.64fr);
    gap: 0.5rem;
  }

  .product-general-card--compact .general-image-shell {
    height: clamp(80px, 20vw, 112px);
    min-height: 80px;
  }

  .product-general-card--compact .pg-quick-toggles {
    grid-template-columns: 1fr 1fr;
  }

  .product-general-media {
    order: -1;
  }

  .product-general-side {
    grid-column: auto;
  }

  .product-general-toggles :deep(.toggle-switch) {
    min-height: auto;
  }

  .bom-inline-card {
    grid-template-columns: minmax(0, 1fr);
    align-items: stretch;
  }

  .product-general-meta-row {
    align-items: stretch;
  }

  .mini-readiness-row {
    flex: 1 1 100%;
  }

  .price-inline-field {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    min-width: 0;
  }

  .price-inline-control {
    flex: 1;
    min-width: 0;
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .quick-price-save {
    width: auto;
    white-space: nowrap;
    padding-inline: 0.65rem;
    min-height: 38px;
  }

  .section-picker {
    flex-direction: column;
    align-items: stretch;
  }

  .section-picker > .secondary-btn {
    width: 100%;
    justify-content: center;
  }

  .simple-tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.2rem;
    margin-bottom: 0.1rem;
    scrollbar-width: thin;
  }

  .simple-tab {
    flex: 0 0 auto;
    min-height: 2.6rem;
    white-space: nowrap;
  }

  .nutrition-head,
  .variant-config-head,
  .variant-values-head {
    flex-direction: column;
    align-items: stretch;
  }

  .inline-actions,
  .filters {
    flex-direction: column;
    align-items: stretch;
  }

  .inline-actions > *,
  .filters > * {
    width: 100%;
  }

  .general-image-shell {
    height: auto;
    min-height: 180px;
    aspect-ratio: 16 / 10;
  }
}

@media (max-width: 640px) {
  .product-general-card,
  .section-picker-shell,
  .nutrition-box,
  .variant-config-shell,
  .variant-values-shell,
  .bom-inline-card {
    border-radius: 12px;
  }

  .product-general-layout,
  .product-top-grid,
  .product-settings-grid,
  .variants-grid,
  .reports-content,
  .tables-grid,
  .charts-grid {
    gap: 0.56rem;
  }

  .product-general-fields label,
  .identity-grid label,
  .nutrition-grid label {
    font-size: 0.76rem;
  }

  .mini-meta-chip,
  .mini-readiness-score,
  .mini-readiness-pill {
    width: 100%;
    justify-content: center;
  }

  .sticky-save-bar {
    width: calc(100% - 0.5rem);
    bottom: 0.4rem;
    padding: 0.55rem;
    border-radius: 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .sticky-save-bar .primary-btn,
  .sticky-save-bar .secondary-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .save-spark-btn::after {
    animation: none;
  }

  .simple-tab {
    transition: none;
  }
}

.preview-static-card :deep(a),
.preview-static-card :deep(button) {
  pointer-events: none !important;
  cursor: default !important;
}
.builder-section {
  margin-top: 1rem;
}
.builder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.builder-fields {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--mg-border-light);
}
.builder-link {
  margin-top: 1.5rem;
}
.builder-hint {
  margin-top: 1rem;
  text-align: center;
  padding: 1rem;
  background: var(--mg-bg-page);
  border-radius: 8px;
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
  color: var(--mg-text-muted);
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
  padding: 0.18rem 0.54rem;
  font-size: 0.69rem;
  font-weight: 800;
}

.pill.active {
  background: var(--mg-success-bg);
  color: var(--mg-success);
}

.pill.inactive {
  background: rgb(254 243 199 / 0.95);
  color: #92400e;
}

.pill.default {
  background: var(--mg-bg-soft);
  color: var(--mg-text-main);
}

.pill.docstatus {
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
}

.pill.docstatus.submitted {
  background: var(--mg-success-bg);
  color: var(--mg-success);
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
  color: var(--mg-danger);
}

.success {
  margin: 0;
  color: var(--accent-green);
}

@media (max-width: 980px) {
  /* همه‌چیز در یک ردیف: عکس + (قیمت + سوییچ‌ها) */
  .product-general-card--compact .product-general-layout {
    grid-template-columns: minmax(96px, 0.4fr) minmax(0, 1.6fr);
    align-items: center;
    gap: 0.6rem;
  }

  .product-general-card--compact .general-image-shell {
    width: 100%;
    height: clamp(96px, 22vw, 130px);
    min-height: 96px;
    aspect-ratio: 1 / 1;
    border-radius: var(--mg-radius-md);
  }

  .product-general-card--compact .general-product-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .product-general-card--compact .product-general-main {
    display: grid;
    gap: 0.5rem;
  }

  .product-general-card--compact .price-inline-field {
    gap: 0.3rem;
    font-size: 0.72rem;
  }

  .product-general-card--compact .price-inline-control {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .product-general-card--compact .quick-price-save {
    width: auto;
    white-space: nowrap;
    padding-inline: 0.55rem;
    min-height: 36px;
    font-size: 0.72rem;
  }

  /* نام، وضعیت و چیپ‌ها در موبایل حذف می‌شوند */
  .product-general-card--compact .pg-name-field,
  .product-general-card--compact .pg-status-row,
  .product-general-card--compact .pg-meta-row {
    display: none;
  }

  .pg-quick-toggles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sticky-save-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .sticky-save-bar .primary-btn {
    width: 100%;
  }
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

  .nutrition-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .check {
    border: 1px solid var(--mg-border-light);
    border-radius: 8px;
    padding: 0.45rem 0.55rem;
    background: #fff;
  }

  .main-image {
    height: min(62vw, 300px);
  }
}

@media (max-width: 640px) {
  .section-picker-shell,
  .variant-values-shell,
  .image-shell,
  .product-changes-grid,
  .product-top-grid,
  .product-settings-grid,
  .charts-grid,
  .tables-grid {
    gap: 0.5rem;
  }

  .identity-grid {
    gap: 0.35rem;
  }

  .checks-grid {
    gap: 0.25rem;
  }

  .section-picker {
    align-items: stretch;
  }

  .section-picker .secondary-btn {
    width: 100%;
  }

  .simple-tabs {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .simple-tab {
    width: 100%;
    padding-inline: 0.45rem;
  }

  .tab-hint {
    font-size: 0.78rem;
    line-height: 1.7;
  }

  .variant-values-head,
  .row-actions {
    width: 100%;
  }

  .row-actions > button {
    flex: 1 1 0;
    font-size: 0.74rem;
    padding-inline: 0.48rem;
    min-height: 2.6rem;
  }

  .pill {
    font-size: 0.64rem;
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
  color: var(--mg-text-muted);
  line-height: 1.4;
}

.info-box {
  padding: 0.75rem 1rem;
  background: var(--mg-bg-soft);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  font-size: 0.85rem;
  color: var(--mg-text-main);
  line-height: 1.5;
  box-shadow: var(--mg-shadow-sm);
}

.delete-btn {
  border-color: rgb(var(--mg-danger-rgb, 166 84 63) / 0.3) !important;
  color: var(--mg-danger) !important;
  background: var(--mg-danger-bg) !important;
}

.delete-btn:hover:not(:disabled) {
  background: rgb(var(--mg-danger-rgb, 166 84 63) / 0.14) !important;
  border-color: rgb(var(--mg-danger-rgb, 166 84 63) / 0.45) !important;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-mini-btn {
  border-color: var(--mg-danger) !important;
  color: var(--mg-danger) !important;
}

.delete-mini-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--mg-danger) 10%, transparent) !important;
}

/* ─── Tag input ─── */
.tag-input-wrap {
  display: grid;
  gap: 0.35rem;
}

.tag-pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 18%, transparent);
  border-radius: 12px;
  padding: 0.45rem 0.55rem;
  background: var(--mg-bg-surface);
  min-height: 42px;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 8%, transparent);
  color: var(--mg-text-main);
  font-size: 0.78rem;
  font-weight: 500;
  white-space: nowrap;
}

.tag-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  color: var(--mg-text-muted);
  font-size: 0.75rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  margin-inline-start: 0.15rem;
  transition: all 0.15s;
}

.tag-remove:hover {
  background: color-mix(in srgb, var(--mg-danger) 15%, transparent);
  color: var(--mg-danger);
}

.tag-input {
  border: none;
  outline: none;
  font-size: 0.82rem;
  font-family: inherit;
  min-width: 120px;
  flex: 1;
  background: transparent;
  color: var(--mg-text-main);
  padding: 0.15rem 0;
}

.tag-input::placeholder {
  color: var(--mg-text-muted);
  font-size: 0.78rem;
}
</style>
