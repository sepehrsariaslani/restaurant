<template>
  <ManagementPageScaffold title="مدیریت محصولات" subtitle="کنترل وضعیت فعال/غیرفعال و قیمت‌گذاری سریع">
    <ManagementSurfaceCard tone="accent" class="products-filter-card">
      <div class="toolbar">
        <input class="input" v-model="search" placeholder="جستجو محصول..." @keydown.enter.prevent="loadProducts" />
        <ManagementToggleSwitch
          v-model="activeOnly"
          class="toolbar-toggle"
          label="فقط فعال"
        />
        <div class="filter-field">
          <SearchableDropdown
            v-model="selectedTag"
            :options="availableTagOptions"
            placeholder="فیلتر تگ..."
            search-placeholder="جستجوی تگ..."
            include-empty-option
            empty-label="همه"
          />
        </div>
        <button class="primary-btn" type="button" @click="loadProducts">جستجو</button>
        <button class="secondary-btn" type="button" @click="openCreatePopup">کالای جدید</button>
        <button class="tertiary-btn" type="button" @click="toggleAdvancedMode">
          {{ showAdvanced ? 'کمتر' : 'فیلتر بیشتر' }}
        </button>
      </div>
      <div v-if="showAdvanced" class="toolbar advanced-toolbar">
        <ManagementFilterControl
          v-model="selectedCategorySlugs"
          :options="groupOptions"
          label="فیلتر گروه"
          placeholder="انتخاب گروه‌ها"
          search-placeholder="جستجوی گروه..."
          :include-empty-option="false"
          :multiple="true"
        />
        <ManagementSortControl
          v-model="sortBy"
          :options="sortOptions"
          label="مرتب سازی"
          placeholder="انتخاب نوع مرتب سازی"
        />
        <ManagementViewSwitcher v-model="viewMode" :modes="viewModes" class="view-switcher" />
      </div>
    </ManagementSurfaceCard>

    <ManagementProductGrouping
      v-if="showAdvanced"
      v-model="groupBy"
      v-model:collapsed="collapseGroupsByDefault"
    />

    <p class="muted" v-if="loading">در حال بارگذاری محصولات...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success-msg" v-if="successMessage">{{ successMessage }}</p>

    <ManagementSurfaceCard :title="activeViewTitle" :subtitle="activeViewSubtitle">
      <template v-if="viewMode === 'tree'">
        <ManagementTreeView
          :nodes="productTreeNodes"
          empty-text="محصولی برای نمایش وجود ندارد."
          :node-clickable="canOpenProductTreeNode"
          @node-click="handleProductTreeNodeClick"
        >
          <template #actions="{ node }">
            <div v-if="canOpenProductTreeNode(node)" class="actions">
              <button :class="toggleButtonClass(node)" type="button" @click.stop="toggleActive(node)">
                {{ visibilityButtonLabel(node) }}
              </button>
              <button
                class="secondary-btn delete-btn"
                type="button"
                :disabled="isDeletingProduct(node)"
                @click.stop="removeProduct(node)"
              >
                {{ isDeletingProduct(node) ? 'در حال حذف...' : 'حذف' }}
              </button>
            </div>
          </template>
        </ManagementTreeView>
      </template>

      <template v-else-if="viewMode === 'list'">
        <div v-if="hasGroupedRows && !isMobileView" class="grouped-list desktop-table">
          <ManagementSurfaceCard
            v-for="group in groupedProducts"
            :key="`desktop-group-${group.key}`"
            class="group-block"
            tone="soft"
          >
            <button type="button" class="group-header-btn" @click="toggleGroupCollapse(group.key)">
              <strong>{{ group.label }}</strong>
              <span>{{ formatNumber(group.rows.length) }} کالا</span>
              <span class="group-chevron">{{ isGroupCollapsed(group.key) ? '▸' : '▾' }}</span>
            </button>
            <ManagementListView
              v-if="!isGroupCollapsed(group.key)"
              :columns="columns"
              :rows="group.rows"
              row-key="name"
              :row-clickable="true"
              @row-click="openProductDetail"
            >
              <template #cell-item_code="{ row }">{{ displayProductCode(row) }}</template>
              <template #cell-tags="{ row }">
                <span class="tag-pill" v-for="t in (row.tags || []).slice(0, 3)" :key="t">{{ t }}</span>
                <span class="tag-pill more" v-if="(row.tags || []).length > 3">+{{ (row.tags || []).length - 3 }}</span>
              </template>
              <template #cell-base_price="{ value }">{{ formatMoney(value, currency) }}</template>
              <template #cell-stock_qty="{ value }">{{ formatStock(value) }}</template>
              <template #cell-is_active="{ value }">
                <span :class="['state-pill', isActiveValue(value) ? 'on' : 'off']">
                  {{ visibilityStateLabel(value) }}
                </span>
              </template>
              <template #cell-actions="{ row }">
                <div class="actions">
                  <button :class="toggleButtonClass(row)" type="button" @click.stop="toggleActive(row)">
                    {{ visibilityButtonLabel(row) }}
                  </button>
                  <button
                    class="secondary-btn delete-btn"
                    type="button"
                    :disabled="isDeletingProduct(row)"
                    @click.stop="removeProduct(row)"
                  >
                    {{ isDeletingProduct(row) ? 'در حال حذف...' : 'حذف' }}
                  </button>
                </div>
              </template>
            </ManagementListView>
          </ManagementSurfaceCard>
        </div>

        <ManagementListView
          v-else-if="!isMobileView"
          class="desktop-table"
          :columns="columns"
          :rows="visibleProducts"
          row-key="name"
          :row-clickable="true"
          @row-click="openProductDetail"
        >
          <template #cell-item_code="{ row }">{{ displayProductCode(row) }}</template>
              <template #cell-tags="{ row }">
                <span class="tag-pill" v-for="t in (row.tags || []).slice(0, 3)" :key="t">{{ t }}</span>
                <span class="tag-pill more" v-if="(row.tags || []).length > 3">+{{ (row.tags || []).length - 3 }}</span>
              </template>
              <template #cell-base_price="{ value }">{{ formatMoney(value, currency) }}</template>
          <template #cell-stock_qty="{ value }">{{ formatStock(value) }}</template>
          <template #cell-is_active="{ value }">
            <span :class="['state-pill', isActiveValue(value) ? 'on' : 'off']">
              {{ visibilityStateLabel(value) }}
            </span>
          </template>
          <template #cell-actions="{ row }">
            <div class="actions">
              <button :class="toggleButtonClass(row)" type="button" @click.stop="toggleActive(row)">
                {{ visibilityButtonLabel(row) }}
              </button>
              <button
                class="secondary-btn delete-btn"
                type="button"
                :disabled="isDeletingProduct(row)"
                @click.stop="removeProduct(row)"
              >
                {{ isDeletingProduct(row) ? 'در حال حذف...' : 'حذف' }}
              </button>
            </div>
          </template>
        </ManagementListView>

        <div v-if="hasGroupedRows && isMobileView" class="grouped-mobile mobile-cards">
          <ManagementSurfaceCard
            v-for="group in groupedProducts"
            :key="`mobile-group-${group.key}`"
            class="group-block"
            tone="soft"
          >
            <button type="button" class="group-header-btn" @click="toggleGroupCollapse(group.key)">
              <strong>{{ group.label }}</strong>
              <span>{{ formatNumber(group.rows.length) }} کالا</span>
              <span class="group-chevron">{{ isGroupCollapsed(group.key) ? '▸' : '▾' }}</span>
            </button>

            <ManagementMobileCardList
              v-if="!isGroupCollapsed(group.key)"
              :rows="group.rows"
              row-key="name"
              card-class="product-card"
              empty-text="محصولی با این فیلتر پیدا نشد."
              :card-clickable="true"
              @card-click="openProductDetail"
            >
              <template #card="{ row }">
                <div class="product-card__head">
                  <div class="product-card__media">
                    <img v-if="resolveImage(row)" :src="resolveImage(row)" :alt="row.title || 'image'" />
                    <span v-else class="product-card__fallback">{{ initials(row.title || row.item_code || 'محصول') }}</span>
                  </div>
                  <div class="product-card__meta">
                    <p class="product-card__title">{{ row.title || '-' }}</p>
                    <p class="product-card__sub">{{ row.category_title || 'بدون دسته' }} • {{ displayProductCode(row) }}</p>
                    <div class="product-card__tags" v-if="row.tags && row.tags.length">
                      <span class="tag-pill" v-for="t in row.tags.slice(0, 4)" :key="t">{{ t }}</span>
                      <span class="tag-pill more" v-if="row.tags.length > 4">+{{ row.tags.length - 4 }}</span>
                    </div>
                  </div>
                  <span :class="['state-pill', isProductActive(row) ? 'on' : 'off']">
                    {{ visibilityStateLabel(row) }}
                  </span>
                </div>

                <div class="product-card__totals">
                  <p>قیمت: {{ formatMoney(row.base_price, currency) }}</p>
                  <p>موجودی: {{ formatStock(row.stock_qty) }}</p>
                </div>

                <div class="row-actions">
                  <button :class="toggleButtonClass(row)" type="button" @click.stop="toggleActive(row)">
                    {{ visibilityButtonLabel(row) }}
                  </button>
                  <button
                    class="secondary-btn delete-btn"
                    type="button"
                    :disabled="isDeletingProduct(row)"
                    @click.stop="removeProduct(row)"
                  >
                    {{ isDeletingProduct(row) ? 'در حال حذف...' : 'حذف' }}
                  </button>
                </div>
              </template>
            </ManagementMobileCardList>
          </ManagementSurfaceCard>
        </div>

        <ManagementMobileCardList
          v-else-if="isMobileView"
          class="mobile-cards"
          :rows="visibleProducts"
          row-key="name"
          card-class="product-card"
          empty-text="محصولی با این فیلتر پیدا نشد."
          :card-clickable="true"
          @card-click="openProductDetail"
        >
          <template #card="{ row }">
            <div class="product-card__head">
              <div class="product-card__media">
                <img v-if="resolveImage(row)" :src="resolveImage(row)" :alt="row.title || 'image'" />
                <span v-else class="product-card__fallback">{{ initials(row.title || row.item_code || 'محصول') }}</span>
              </div>
              <div class="product-card__meta">
                <p class="product-card__title">{{ row.title || '-' }}</p>
                <p class="product-card__sub">{{ row.category_title || 'بدون دسته' }} • {{ displayProductCode(row) }}</p>
                <div class="product-card__tags" v-if="row.tags && row.tags.length">
                  <span class="tag-pill" v-for="t in row.tags.slice(0, 4)" :key="t">{{ t }}</span>
                  <span class="tag-pill more" v-if="row.tags.length > 4">+{{ row.tags.length - 4 }}</span>
                </div>
              </div>
              <span :class="['state-pill', isProductActive(row) ? 'on' : 'off']">
                {{ visibilityStateLabel(row) }}
              </span>
            </div>

            <div class="product-card__totals">
              <p>قیمت: {{ formatMoney(row.base_price, currency) }}</p>
              <p>موجودی: {{ formatStock(row.stock_qty) }}</p>
            </div>

            <div class="row-actions">
              <button :class="toggleButtonClass(row)" type="button" @click.stop="toggleActive(row)">
                {{ visibilityButtonLabel(row) }}
              </button>
              <button
                class="secondary-btn delete-btn"
                type="button"
                :disabled="isDeletingProduct(row)"
                @click.stop="removeProduct(row)"
              >
                {{ isDeletingProduct(row) ? 'در حال حذف...' : 'حذف' }}
              </button>
            </div>
          </template>
        </ManagementMobileCardList>
      </template>

      <ManagementGalleryView
        v-else
        :rows="visibleProducts"
        row-key="name"
        image-field="image"
        secondary-image-field="website_image"
        title-field="title"
        subtitle-field="category_title"
        :clickable="true"
        @click-item="openProductDetail"
      >
        <template #caption="{ row }">
          {{ formatMoney(row.base_price, currency) }} | موجودی {{ formatStock(row.stock_qty) }}
        </template>
        <template #overlay="{ row }">
          <span class="gallery-status" :class="isProductActive(row) ? 'on' : 'off'">
            {{ visibilityStateLabel(row) }}
          </span>
        </template>
        <template #actions="{ row }">
          <div class="actions" @click.stop>
            <button :class="toggleButtonClass(row)" type="button" @click.stop="toggleActive(row)">
              {{ visibilityButtonLabel(row) }}
            </button>
            <button
              class="secondary-btn delete-btn"
              type="button"
              :disabled="isDeletingProduct(row)"
              @click.stop="removeProduct(row)"
            >
              {{ isDeletingProduct(row) ? 'در حال حذف...' : 'حذف' }}
            </button>
          </div>
        </template>
      </ManagementGalleryView>
    </ManagementSurfaceCard>

    <ManagementPopup
      v-model:open="createPopupOpen"
      title="ایجاد کالای جدید"
      subtitle="اطلاعات ضروری را وارد کنید؛ سپس می‌توانید مستقیم وارد صفحه ویرایش کامل شوید."
      :close-on-backdrop="!creatingItem"
      :close-on-escape="!creatingItem"
    >
      <div class="create-form">
        <label>
          کد کالا
          <input class="input" v-model.trim="createForm.item_code" placeholder="مثال: BURGER-001" />
          <small class="hint">کد یکتای محصول برای شناسایی در سیستم</small>
        </label>
        <label>
          نام کالا
          <input class="input" v-model.trim="createForm.item_name" placeholder="مثال: برگر مخصوص" />
          <small class="hint">نام محصول که به مشتری نمایش داده می‌شود</small>
        </label>
        <label>
          گروه کالا
          <SearchableDropdown
            v-model="createForm.item_group"
            :options="itemGroupOptions"
            placeholder="انتخاب گروه"
            search-placeholder="جستجوی گروه..."
            include-empty-option
            empty-label="همه گروه‌ها"
          />
          <small class="hint">دسته‌بندی محصول برای مدیریت بهتر</small>
        </label>
        <label>
          واحد
          <SearchableDropdown
            v-model="createForm.stock_uom"
            :options="uomOptions"
            placeholder="انتخاب واحد"
            search-placeholder="جستجوی واحد..."
          />
          <small class="hint">واحد اندازه‌گیری (مثلا: عدد، لیتر، کیلوگرم)</small>
        </label>
        <label>
          دسته رستورانی
          <SearchableDropdown
            v-model="createForm.restaurant_category"
            :options="categoryOptions"
            placeholder="بدون دسته"
            search-placeholder="جستجوی دسته..."
            include-empty-option
            empty-label="بدون دسته"
          />
        </label>
        <label>
          زیردسته
          <SearchableDropdown
            v-model="createForm.restaurant_subcategory"
            :options="createSubcategoryOptions"
            placeholder="بدون زیردسته"
            search-placeholder="جستجوی زیردسته..."
            include-empty-option
            empty-label="بدون زیردسته"
          />
        </label>
        <label class="full">
          توضیح کوتاه
          <textarea class="textarea" v-model.trim="createForm.description" placeholder="توضیح کوتاه برای تیم و نمایش اولیه"></textarea>
        </label>
        <ManagementToggleSwitch
          v-model="createForm.restaurant_enabled"
          label="نمایش در منو"
          hint="اگر روشن باشد مشتری محصول را می‌بیند."
        />
        <ManagementToggleSwitch
          v-model="createForm.show_in_print"
          label="نمایش در چاپ"
          hint="برای رسید و گزارش چاپی استفاده می‌شود."
        />
      </div>
      <p class="error" v-if="createError">{{ createError }}</p>
      <template #footer>
        <div class="popup-actions">
          <button class="secondary-btn" type="button" :disabled="creatingItem" @click="createPopupOpen = false">انصراف</button>
          <button class="primary-btn" type="button" :disabled="creatingItem" @click="submitCreate(true)">
            {{ creatingItem ? 'در حال ایجاد...' : 'ایجاد و ویرایش کامل' }}
          </button>
          <button class="secondary-btn" type="button" :disabled="creatingItem" @click="submitCreate(false)">
            {{ creatingItem ? 'در حال ایجاد...' : 'ذخیره و بازگشت' }}
          </button>
        </div>
      </template>
    </ManagementPopup>

    <ManagementPopup
      v-model:open="quickStartWizardOpen"
      title="شروع سریع - ایجاد محصول"
      :subtitle="`مرحله ${wizardStep} از ۳`"
      :close-on-backdrop="!creatingItem"
      :close-on-escape="!creatingItem"
    >
      <div class="wizard-form">
        <div v-if="wizardStep === 1" class="wizard-step">
          <h3>مرحله ۱: اطلاعات اصلی محصول</h3>
          <label>
            کد کالا
            <input class="input" v-model.trim="wizardForm.item_code" placeholder="مثال: COFFEE-001" />
            <small class="hint">کد یکتای محصول برای شناسایی در سیستم</small>
          </label>
          <label>
            نام کالا
            <input class="input" v-model.trim="wizardForm.item_name" placeholder="مثال: قهوه لته" />
            <small class="hint">نام محصول که به مشتری نمایش داده می‌شود</small>
          </label>
          <label>
            واحد
            <SearchableDropdown
              v-model="wizardForm.stock_uom"
              :options="uomOptions"
              placeholder="انتخاب واحد"
              search-placeholder="جستجوی واحد..."
            />
            <small class="hint">واحد اندازه‌گیری (مثلا: عدد، لیتر، کیلوگرم)</small>
          </label>
          <label>
            گروه کالا
            <SearchableDropdown
              v-model="wizardForm.item_group"
              :options="itemGroupOptions"
              placeholder="انتخاب گروه"
              search-placeholder="جستجوی گروه..."
            />
            <small class="hint">دسته‌بندی محصول برای مدیریت بهتر</small>
          </label>
        </div>

        <div v-if="wizardStep === 2" class="wizard-step">
          <h3>مرحله ۲: صفت‌ها و انواع (اختیاری)</h3>
          <p class="muted">اگر محصول شما انواع مختلفی دارد (مثلا سایز، رنگ)، می‌توانید بعداً از بخش "صفت محصولات" آن‌ها را تعریف کنید.</p>
          <p class="info-box">💡 این مرحله را می‌توانید رد کنید و بعداً تکمیل کنید.</p>
        </div>

        <div v-if="wizardStep === 3" class="wizard-step">
          <h3>مرحله ۳: قیمت‌گذاری اولیه</h3>
          <label>
            قیمت پایه (تومان)
            <NumericInput
              v-model="wizardForm.price"
              placeholder="مثال: 45000"
            />
            <small class="hint">قیمت فروش پیش‌فرض محصول</small>
          </label>
          <p class="info-box">💡 می‌توانید بعداً قیمت‌های متفاوت برای لیست‌های مختلف تعریف کنید.</p>
        </div>
      </div>

      <p class="error" v-if="createError">{{ createError }}</p>

      <template #footer>
        <div class="popup-actions">
          <button class="secondary-btn" type="button" :disabled="creatingItem" @click="closeQuickStartWizard">انصراف</button>
          <button v-if="wizardStep > 1" class="secondary-btn" type="button" :disabled="creatingItem" @click="wizardPrevStep">قبلی</button>
          <button v-if="wizardStep < 3" class="primary-btn" type="button" :disabled="creatingItem" @click="wizardNextStep">بعدی</button>
          <button v-if="wizardStep === 3" class="primary-btn" type="button" :disabled="creatingItem" @click="submitWizard">
            {{ creatingItem ? 'در حال ایجاد...' : 'ایجاد و مشاهده محصول' }}
          </button>
        </div>
      </template>
    </ManagementPopup>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementViewSwitcher from '@/components/management/ManagementViewSwitcher.vue'
import ManagementFilterControl from '@/components/management/ManagementFilterControl.vue'
import ManagementSortControl from '@/components/management/ManagementSortControl.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementGalleryView from '@/components/management/ManagementGalleryView.vue'
import ManagementMobileCardList from '@/components/management/ManagementMobileCardList.vue'
import ManagementTreeView from '@/components/management/ManagementTreeView.vue'
import ManagementProductGrouping from '@/components/management/ManagementProductGrouping.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import NumericInput from '@/components/NumericInput.vue'
import {
  createManagementProduct,
  deleteManagementProduct,
  getManagementProductDetail,
  getMenuBoot,
  listManagementProducts,
  setManagementProductActive,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const products = ref([])
const currency = ref('IRR')
const search = ref('')
const activeOnly = ref(false)
const selectedTag = ref('')
const availableTagOptions = ref([])
const showAdvanced = ref(false)
const quickStartWizardOpen = ref(false)
const wizardStep = ref(1)
const wizardForm = ref({
  item_code: '',
  item_name: '',
  stock_uom: '',
  item_group: '',
  attributes: [],
  price: '',
})
const selectedCategorySlugs = ref([])
const menuCategories = ref([])
const sortBy = ref(readStoredSortMode())
const viewMode = ref(readStoredViewMode())
const groupBy = ref(readStoredGroupMode())
const collapseGroupsByDefault = ref(readStoredGroupCollapseMode())
const collapsedGroupKeys = ref([])
const createPopupOpen = ref(false)
const creatingItem = ref(false)
const createError = ref('')
const deletingProductNames = ref([])
const bootFieldOptions = ref({
  uoms: [],
  item_groups: [],
  categories: [],
  subcategories: [],
})
const createForm = ref(createDefaultForm())
const MOBILE_BREAKPOINT = 760
const isMobileView = ref(getInitialMobileView())
const PRODUCT_VISIBILITY_OVERRIDES_KEY = 'restaurant.management.productVisibilityOverrides'

const columns = [
  { key: 'item_code', label: 'کد/نام' },
  { key: 'title', label: 'نام' },
  { key: 'category_title', label: 'دسته' },
  { key: 'tags', label: 'تگ‌ها' },
  { key: 'base_price', label: 'قیمت' },
  { key: 'stock_qty', label: 'موجودی' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

const sortOptions = [
  { value: 'latest', label: 'جدیدترین' },
  { value: 'title_asc', label: 'نام (الف به ی)' },
  { value: 'title_desc', label: 'نام (ی به الف)' },
  { value: 'price_desc', label: 'قیمت (بیشترین)' },
  { value: 'price_asc', label: 'قیمت (کمترین)' },
  { value: 'stock_desc', label: 'موجودی (بیشترین)' },
  { value: 'stock_asc', label: 'موجودی (کمترین)' },
]
const viewModes = [
  { value: 'list', label: 'لیست', icon: '≡' },
  { value: 'gallery', label: 'گالری', icon: '▦' },
  { value: 'tree', label: 'درخت', icon: '⋰' },
]

const groupOptions = computed(() => {
  const map = new Map()

  for (const row of menuCategories.value || []) {
    const slug = String(row?.slug || '').trim()
    const title = String(row?.title || '').trim()
    if (slug && title) {
      map.set(slug, title)
    }
  }

  for (const row of products.value || []) {
    const slug = String(row?.category_slug || '').trim()
    const title = String(row?.category_title || '').trim()
    if (slug && title && !map.has(slug)) {
      map.set(slug, title)
    }
  }

  return Array.from(map.entries())
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label, 'fa'))
})

const itemGroupOptions = computed(() => normalizeOptionRows(bootFieldOptions.value?.item_groups || []))
const uomOptions = computed(() => normalizeOptionRows(bootFieldOptions.value?.uoms || []))
const categoryOptions = computed(() => normalizeOptionRows(bootFieldOptions.value?.categories || []))
const createSubcategoryOptions = computed(() => {
  const normalizedRows = bootFieldOptions.value?.subcategories || []
  const parent = String(createForm.value.restaurant_category || '').trim()
  const next = []
  for (const row of normalizedRows) {
    const value = String(row?.value || row?.name || '').trim()
    if (!value) {
      continue
    }
    const ownerCategory = String(row?.category || row?.parent_item_group || '').trim()
    if (parent && ownerCategory && ownerCategory !== parent) {
      continue
    }
    next.push({
      value,
      label: String(row?.label || row?.item_group_name || value).trim(),
    })
  }
  return next
})

const visibleProducts = computed(() => {
  let rows = [...products.value]

  if (activeOnly.value) {
    rows = rows.filter((row) => isProductActive(row))
  }

  const query = normalizeSearchText(search.value)
  if (query) {
    rows = rows.filter((row) => productMatchesSearch(row, query))
  }

  const selectedGroups = Array.isArray(selectedCategorySlugs.value)
    ? selectedCategorySlugs.value.map((value) => String(value || '').trim()).filter(Boolean)
    : []
  if (selectedGroups.length) {
    const selectedSet = new Set(selectedGroups)
    rows = rows.filter((row) => selectedSet.has(String(row?.category_slug || '').trim()))
  }

  // Tag filter
  const tag = String(selectedTag.value || '').trim()
  if (tag) {
    rows = rows.filter((row) => {
      const tags = Array.isArray(row?.tags) ? row?.tags : []
      return tags.some((t) => String(t).trim() === tag)
    })
  }

  if (sortBy.value === 'title_asc') {
    rows.sort((a, b) => String(a?.title || '').localeCompare(String(b?.title || ''), 'fa'))
  } else if (sortBy.value === 'title_desc') {
    rows.sort((a, b) => String(b?.title || '').localeCompare(String(a?.title || ''), 'fa'))
  } else if (sortBy.value === 'price_asc') {
    rows.sort((a, b) => Number(a?.base_price || 0) - Number(b?.base_price || 0))
  } else if (sortBy.value === 'price_desc') {
    rows.sort((a, b) => Number(b?.base_price || 0) - Number(a?.base_price || 0))
  } else if (sortBy.value === 'stock_asc') {
    rows.sort((a, b) => Number(a?.stock_qty || 0) - Number(b?.stock_qty || 0))
  } else if (sortBy.value === 'stock_desc') {
    rows.sort((a, b) => Number(b?.stock_qty || 0) - Number(a?.stock_qty || 0))
  }

  return rows
})

const groupedProducts = computed(() => {
  if (groupBy.value === 'none') {
    return []
  }
  const bucket = new Map()
  for (const row of visibleProducts.value) {
    const key = resolveGroupKey(row)
    if (!bucket.has(key.key)) {
      bucket.set(key.key, {
        key: key.key,
        label: key.label,
        rows: [],
      })
    }
    bucket.get(key.key).rows.push(row)
  }
  return Array.from(bucket.values()).sort((left, right) => String(left.label || '').localeCompare(String(right.label || ''), 'fa'))
})

const hasGroupedRows = computed(() => groupBy.value !== 'none' && groupedProducts.value.length > 0)

const activeViewTitle = computed(() => {
  if (viewMode.value === 'tree') {
    return 'درخت محصولات'
  }
  if (viewMode.value === 'gallery') {
    return 'گالری محصولات'
  }
  return 'لیست محصولات'
})

const activeViewSubtitle = computed(() => {
  if (viewMode.value === 'tree') {
    return 'دسته‌بندی محصولات به‌صورت ساختار درختی'
  }
  if (viewMode.value === 'gallery') {
    return 'نمای تصویری محصولات برای مدیریت بصری'
  }
  return ''
})

const productTreeNodes = computed(() => {
  const categories = new Map()
  for (const row of visibleProducts.value || []) {
    const categoryLabel = String(row?.category_title || '').trim() || 'بدون دسته'
    const categoryKey = `category:${categoryLabel}`
    if (!categories.has(categoryKey)) {
      categories.set(categoryKey, {
        key: categoryKey,
        label: categoryLabel,
        caption: `${formatNumber(0)} کالا`,
        badge: 'دسته',
        status: null,
        children: [],
      })
    }

    const bucket = categories.get(categoryKey)
    const itemName = String(row?.title || row?.item_code || row?.name || '').trim() || '-'
    bucket.children.push({
      ...row,
      key: String(row?.name || `${categoryKey}-${bucket.children.length}`),
      label: itemName,
      caption: `${formatMoney(row?.base_price || 0, currency.value)} • موجودی ${formatStock(row?.stock_qty || 0)}`,
      badge: 'محصول',
      status: {
        label: visibilityStateLabel(row),
        tone: isProductActive(row) ? 'success' : 'warning',
      },
      children: [],
    })
    bucket.caption = `${formatNumber(bucket.children.length)} کالا`
  }

  return Array.from(categories.values()).sort((left, right) =>
    String(left?.label || '').localeCompare(String(right?.label || ''), 'fa'),
  )
})

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementProducts({
      search: '',
      active_only: 0,
      tag: '',
    })
    products.value = applyVisibilityOverrides(payload.products || [])

    // Build available tag options from loaded products
    const tagSet = new Set()
    for (const p of products.value || []) {
      for (const t of (p.tags || [])) {
        const trimmed = String(t || '').trim()
        if (trimmed) tagSet.add(trimmed)
      }
    }
    availableTagOptions.value = Array.from(tagSet)
      .sort((a, b) => a.localeCompare(b, 'fa'))
      .map(t => ({ value: t, label: t }))

    if (!bootFieldOptions.value.uoms.length || !bootFieldOptions.value.item_groups.length) {
      await loadFieldOptionsForCreate()
    }
  } catch (errObj) {
    error.value = errObj.message || '❌ متأسفانه بارگذاری لیست محصولات ناموفق بود. لطفاً اتصال اینترنت خود را بررسی کنید.'
  } finally {
    loading.value = false
  }
}

async function toggleActive(row) {
  if (!row?.name) {
    error.value = '❌ شناسه محصول یافت نشد.'
    return
  }
  error.value = ''
  successMessage.value = ''
  const previousState = isProductActive(row) ? 1 : 0
  const next = previousState ? 0 : 1
  try {
    row.is_active = next
    rememberVisibilityOverride(row.name, next)
    products.value = products.value.map((product) =>
      String(product?.name || '') === String(row.name || '') ? { ...product, is_active: next } : product,
    )
    await setManagementProductActive(row.name, next)
    await loadProducts()
    rememberVisibilityOverride(row.name, next)
    products.value = products.value.map((product) =>
      String(product?.name || '') === String(row.name || '') ? { ...product, is_active: next } : product,
    )
    successMessage.value = next ? 'محصول در سایت و منو نمایش داده می‌شود.' : 'محصول از سایت و منو پنهان شد.'
    setTimeout(() => { successMessage.value = '' }, 3000)
  } catch (errObj) {
    row.is_active = previousState
    error.value = errObj.message || '❌ متأسفانه تغییر وضعیت محصول ناموفق بود. لطفاً دوباره تلاش کنید.'
  }
}

function isDeletingProduct(row) {
  const name = String(row?.name || '').trim()
  return Boolean(name && deletingProductNames.value.includes(name))
}

function markProductDeleting(itemName, deleting) {
  const name = String(itemName || '').trim()
  if (!name) {
    return
  }
  if (deleting) {
    if (!deletingProductNames.value.includes(name)) {
      deletingProductNames.value = [...deletingProductNames.value, name]
    }
    return
  }
  deletingProductNames.value = deletingProductNames.value.filter((rowName) => rowName !== name)
}

async function removeProduct(row) {
  const itemName = String(row?.name || '').trim()
  if (!itemName || isDeletingProduct(row)) {
    return
  }
  const itemLabel = String(row?.title || row?.item_name || row?.item_code || itemName).trim()
  const confirmed = window.confirm(
    `آیا مطمئن هستید که می‌خواهید کالای «${itemLabel}» را حذف کنید؟`,
  )
  if (!confirmed) {
    return
  }

  markProductDeleting(itemName, true)
  error.value = ''
  try {
    await deleteManagementProduct(itemName, { allow_archive_on_link: 0, force_delete: 0 })
    await loadProducts()
    window.alert(`کالای «${itemLabel}» با موفقیت حذف شد.`)
  } catch (errObj) {
    if (isLinkedDeleteError(errObj)) {
      const disableConfirmed = window.confirm(
        `این کالا به اسناد فروش یا انبار متصل است و قابل حذف نیست.\n\nمی‌توانید فقط نمایش آن را در سایت خاموش کنید؛ خود کالا در ERPNext فعال می‌ماند.\n\nآیا می‌خواهید کالای «${itemLabel}» از سایت پنهان شود؟`,
      )
      if (!disableConfirmed) {
        return
      }
      try {
        await setManagementProductActive(itemName, 0)
        rememberVisibilityOverride(itemName, 0)
        products.value = products.value.map((product) =>
          String(product?.name || '') === itemName ? { ...product, is_active: 0 } : product,
        )
        window.alert(`کالای «${itemLabel}» فقط از سایت پنهان شد و در ERPNext غیرفعال نشد.`)
        await loadProducts()
      } catch (archiveErr) {
        error.value = archiveErr.message || `پنهان کردن کالای «${itemLabel}» از سایت ناموفق بود. لطفاً دوباره تلاش کنید.`
      }
      return
    }
    error.value = errObj.message || `❌ متأسفانه حذف کالای «${itemLabel}» ناموفق بود. لطفاً دوباره تلاش کنید.`
  } finally {
    markProductDeleting(itemName, false)
  }
}

function isLinkedDeleteError(errorObj) {
  const message = String(errorObj?.message || '')
  return /(disable this item|linked|link exists|cannot delete|وابسته|مرتبط|reference|dependent)/i.test(message)
}

function formatStock(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

function displayProductCode(row) {
  const title = String(row?.title || row?.item_name || '').trim()
  if (title) {
    return title
  }
  return String(row?.item_code || row?.name || '-').trim() || '-'
}

function resolveImage(row) {
  return String(row?.image || row?.website_image || '').trim()
}

function isActiveValue(value) {
  return value === true || Number(value || 0) === 1 || String(value || '').trim() === '1'
}

function isProductActive(row) {
  return isActiveValue(row?.is_active)
}

function visibilityStateLabel(source) {
  const value = source && typeof source === 'object' ? source.is_active : source
  return isActiveValue(value) ? 'نمایش در سایت' : 'پنهان از سایت'
}

function visibilityButtonLabel(row) {
  return isProductActive(row) ? 'پنهان از سایت' : 'نمایش در سایت'
}

function readVisibilityOverrides() {
  if (typeof window === 'undefined') {
    return {}
  }
  try {
    const parsed = JSON.parse(window.localStorage.getItem(PRODUCT_VISIBILITY_OVERRIDES_KEY) || '{}')
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeVisibilityOverrides(overrides) {
  if (typeof window === 'undefined') {
    return
  }
  try {
    window.localStorage.setItem(PRODUCT_VISIBILITY_OVERRIDES_KEY, JSON.stringify(overrides || {}))
  } catch {
    // Ignore local persistence failures.
  }
}

function rememberVisibilityOverride(itemName, active) {
  const name = String(itemName || '').trim()
  if (!name) {
    return
  }
  const overrides = readVisibilityOverrides()
  overrides[name] = Number(active || 0) ? 1 : 0
  writeVisibilityOverrides(overrides)
}

function applyVisibilityOverrides(rows = []) {
  const overrides = readVisibilityOverrides()
  return (rows || []).map((row) => {
    const name = String(row?.name || '').trim()
    if (name && Object.prototype.hasOwnProperty.call(overrides, name)) {
      return { ...row, is_active: Number(overrides[name] || 0) ? 1 : 0 }
    }
    return row
  })
}

function normalizeSearchText(value) {
  return String(value || '')
    .trim()
    .replace(/[ي]/g, 'ی')
    .replace(/[ك]/g, 'ک')
    .replace(/\u200c/g, ' ')
    .replace(/\s+/g, ' ')
    .toLocaleLowerCase('fa-IR')
}

function productMatchesSearch(row, normalizedQuery) {
  if (!normalizedQuery) {
    return true
  }
  const tags = Array.isArray(row?.tags) ? row.tags : []
  const haystack = [
    row?.title,
    row?.item_name,
    row?.item_code,
    row?.name,
    row?.category_title,
    row?.category,
    row?.subcategory_title,
    row?.short_desc,
    ...tags,
  ]
    .map(normalizeSearchText)
    .filter(Boolean)
    .join(' ')
  return haystack.includes(normalizedQuery)
}

function initials(value) {
  const chunks = String(value || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  return chunks.slice(0, 2).map((word) => word[0]).join('').toUpperCase() || '•'
}

function productDetailUrl(row) {
  const itemName = encodeURIComponent(String(row?.name || ''))
  return `/management/product?item_name=${itemName}`
}

function toggleButtonClass(row) {
  return isProductActive(row) ? 'primary-btn status-toggle-btn' : 'secondary-btn status-toggle-btn status-toggle-btn--inactive'
}

async function loadMenuCategories() {
  try {
    const payload = await getMenuBoot('')
    menuCategories.value = Array.isArray(payload?.categories) ? payload.categories : []
  } catch (bootError) {
    menuCategories.value = []
  }
}

async function loadFieldOptionsForCreate() {
  const sample = products.value?.[0]?.name || ''
  if (!sample) {
    return
  }
  try {
    const detailPayload = await getManagementProductDetail({
      item_name: sample,
    })
    const fieldOptions = detailPayload?.field_options || {}
    bootFieldOptions.value = {
      uoms: Array.isArray(fieldOptions?.uoms) ? fieldOptions.uoms : [],
      item_groups: Array.isArray(fieldOptions?.item_groups) ? fieldOptions.item_groups : [],
      categories: Array.isArray(fieldOptions?.categories) ? fieldOptions.categories : [],
      subcategories: Array.isArray(fieldOptions?.subcategories) ? fieldOptions.subcategories : [],
    }
    if (!createForm.value.stock_uom && bootFieldOptions.value.uoms.length) {
      createForm.value.stock_uom = String(bootFieldOptions.value.uoms[0]?.value || bootFieldOptions.value.uoms[0]?.name || '').trim()
    }
    if (!createForm.value.item_group && bootFieldOptions.value.item_groups.length) {
      createForm.value.item_group = String(bootFieldOptions.value.item_groups[0]?.value || bootFieldOptions.value.item_groups[0]?.name || '').trim()
    }
  } catch (fieldOptionsError) {
    // Keep manual entry fallback when field options cannot be loaded.
  }
}

function createDefaultForm() {
  return {
    item_code: '',
    item_name: '',
    item_group: '',
    stock_uom: '',
    restaurant_category: '',
    restaurant_subcategory: '',
    description: '',
    restaurant_enabled: true,
    show_in_print: true,
  }
}

function normalizeOptionRows(rows = []) {
  const out = []
  for (const row of rows || []) {
    const value = String(row?.value || row?.name || '').trim()
    if (!value) {
      continue
    }
    out.push({
      value,
      label: String(row?.label || row?.title || row?.item_group_name || value).trim(),
    })
  }
  return out
}

function openCreatePopup() {
  createError.value = ''
  createForm.value = createDefaultForm()
  if (uomOptions.value.length) {
    createForm.value.stock_uom = uomOptions.value[0].value
  }
  if (itemGroupOptions.value.length) {
    createForm.value.item_group = itemGroupOptions.value[0].value
  }
  createPopupOpen.value = true
}

function toggleAdvancedMode() {
  showAdvanced.value = !showAdvanced.value
}

function openQuickStartWizard() {
  wizardStep.value = 1
  wizardForm.value = {
    item_code: '',
    item_name: '',
    stock_uom: uomOptions.value.length ? uomOptions.value[0].value : '',
    item_group: itemGroupOptions.value.length ? itemGroupOptions.value[0].value : '',
    attributes: [],
    price: '',
  }
  quickStartWizardOpen.value = true
}

function closeQuickStartWizard() {
  quickStartWizardOpen.value = false
}

function wizardNextStep() {
  if (wizardStep.value < 3) {
    wizardStep.value++
  }
}

function wizardPrevStep() {
  if (wizardStep.value > 1) {
    wizardStep.value--
  }
}

async function submitWizard() {
  createError.value = ''
  const payload = {
    item_code: String(wizardForm.value.item_code || '').trim(),
    item_name: String(wizardForm.value.item_name || '').trim(),
    stock_uom: String(wizardForm.value.stock_uom || '').trim(),
    item_group: String(wizardForm.value.item_group || '').trim(),
    restaurant_enabled: 1,
  }

  if (!payload.item_code) {
    createError.value = '⚠️ لطفاً کد کالا را وارد کنید (مثال: COFFEE-001)'
    return
  }
  if (!payload.item_name) {
    createError.value = '⚠️ لطفاً نام کالا را وارد کنید (مثال: قهوه لته)'
    return
  }

  creatingItem.value = true
  try {
    const result = await createManagementProduct(payload)
    const itemName = result?.name || payload.item_code

    if (wizardForm.value.price) {
      try {
        const priceLists = await listManagementPriceLists()
        if (priceLists?.price_lists?.length) {
          const defaultPriceList =
            String(priceLists?.default_price_list || '').trim() ||
            String(priceLists.price_lists.find((row) => Number(row?.is_default || 0) === 1)?.name || '').trim() ||
            String(priceLists.price_lists[0]?.name || '').trim()
          if (defaultPriceList) {
            await setManagementProductPrice({
              item_name: itemName,
              price_list: defaultPriceList,
              price_list_rate: Number(wizardForm.value.price),
            })
          }
        }
      } catch (priceErr) {
        console.warn('قیمت‌گذاری ناموفق:', priceErr)
      }
    }

    await loadProducts()
    closeQuickStartWizard()
    window.location.href = `/management/product?item=${encodeURIComponent(itemName)}`
  } catch (errObj) {
    createError.value = errObj.message || '❌ متأسفانه ایجاد محصول ناموفق بود. لطفاً اطلاعات را بررسی کنید.'
  } finally {
    creatingItem.value = false
  }
}

async function submitCreate(openFullDetail = false) {
  createError.value = ''
  const payload = {
    item_code: String(createForm.value.item_code || '').trim(),
    item_name: String(createForm.value.item_name || '').trim(),
    stock_uom: String(createForm.value.stock_uom || '').trim(),
    item_group: String(createForm.value.item_group || '').trim(),
    restaurant_category: String(createForm.value.restaurant_category || '').trim(),
    restaurant_subcategory: String(createForm.value.restaurant_subcategory || '').trim(),
    description: String(createForm.value.description || '').trim(),
    restaurant_enabled: createForm.value.restaurant_enabled ? 1 : 0,
    show_in_print: createForm.value.show_in_print ? 1 : 0,
  }

  if (!payload.item_code) {
    createError.value = '⚠️ لطفاً کد کالا را وارد کنید (مثال: COFFEE-001)'
    return
  }
  if (!payload.item_name) {
    createError.value = '⚠️ لطفاً نام کالا را وارد کنید (مثال: قهوه لته)'
    return
  }
  if (!payload.stock_uom) {
    createError.value = '⚠️ لطفاً واحد کالا را انتخاب کنید (مثال: عدد، لیتر)'
    return
  }

  creatingItem.value = true
  try {
    const created = await createManagementProduct(payload)
    const createdName = String(created?.name || created?.item_code || payload.item_code).trim()
    createPopupOpen.value = false
    if (openFullDetail && createdName) {
      window.location.href = `/management/product?item_name=${encodeURIComponent(createdName)}`
      return
    }
    await loadProducts()
    window.alert(`✅ کالای «${payload.item_name}» با موفقیت ایجاد شد.`)
  } catch (createErr) {
    createError.value = createErr.message || '❌ متأسفانه ایجاد کالا ناموفق بود. لطفاً اطلاعات را بررسی کنید.'
  } finally {
    creatingItem.value = false
  }
}

function openProductDetail(row) {
  const target = productDetailUrl(row)
  if (!target) {
    return
  }
  window.location.href = target
}

function canOpenProductTreeNode(node) {
  return Boolean(node?.name && node?.badge === 'محصول')
}

function handleProductTreeNodeClick(node) {
  if (!canOpenProductTreeNode(node)) {
    return
  }
  openProductDetail(node)
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

function resolveGroupKey(row) {
  if (groupBy.value === 'category') {
    const label = String(row?.category_title || '').trim() || 'بدون دسته'
    return { key: `category:${label}`, label }
  }
  if (groupBy.value === 'status') {
    const isActive = Number(row?.is_active || 0) === 1
    return { key: `status:${isActive ? 'active' : 'inactive'}`, label: isActive ? 'کالاهای فعال' : 'کالاهای غیرفعال' }
  }
  if (groupBy.value === 'stock') {
    const stock = Number(row?.stock_qty || 0)
    if (stock > 0) {
      return { key: 'stock:available', label: 'موجود در انبار' }
    }
    return { key: 'stock:empty', label: 'ناموجود' }
  }
  return { key: 'all', label: 'همه کالاها' }
}

function isGroupCollapsed(groupKey) {
  return collapsedGroupKeys.value.includes(String(groupKey || ''))
}

function toggleGroupCollapse(groupKey) {
  const normalized = String(groupKey || '')
  if (!normalized) {
    return
  }
  const index = collapsedGroupKeys.value.indexOf(normalized)
  if (index >= 0) {
    const next = [...collapsedGroupKeys.value]
    next.splice(index, 1)
    collapsedGroupKeys.value = next
    return
  }
  collapsedGroupKeys.value = [...collapsedGroupKeys.value, normalized]
}

function readStoredViewMode() {
  try {
    const raw = localStorage.getItem('management-products-view-mode')
    if (raw === 'grid') {
      return 'gallery'
    }
    if (['list', 'gallery', 'tree'].includes(raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return 'list'
}

function readStoredSortMode() {
  try {
    const raw = localStorage.getItem('management-products-sort-mode')
    if (sortOptions.some((option) => option.value === raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return 'latest'
}

function readStoredGroupMode() {
  try {
    const raw = localStorage.getItem('management-products-group-mode')
    if (['none', 'category', 'status', 'stock'].includes(raw)) {
      return raw
    }
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return 'none'
}

function readStoredGroupCollapseMode() {
  try {
    return localStorage.getItem('management-products-group-collapsed') === '1'
  } catch (storageError) {
    // Ignore storage failures and keep default mode.
  }
  return false
}

watch(
  () => viewMode.value,
  (nextMode) => {
    try {
      localStorage.setItem('management-products-view-mode', nextMode)
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

watch(
  () => sortBy.value,
  (nextSort) => {
    try {
      localStorage.setItem('management-products-sort-mode', nextSort)
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

watch(
  () => groupBy.value,
  (nextGroupMode) => {
    try {
      localStorage.setItem('management-products-group-mode', nextGroupMode)
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

watch(
  () => collapseGroupsByDefault.value,
  (nextCollapsed) => {
    try {
      localStorage.setItem('management-products-group-collapsed', nextCollapsed ? '1' : '0')
    } catch (storageError) {
      // Ignore storage failures.
    }
  },
)

watch(
  [() => groupedProducts.value, () => collapseGroupsByDefault.value],
  ([groups]) => {
    if (!Array.isArray(groups) || !groups.length) {
      collapsedGroupKeys.value = []
      return
    }
    if (collapseGroupsByDefault.value) {
      collapsedGroupKeys.value = groups.map((group) => String(group.key || '')).filter(Boolean)
      return
    }
    const validKeys = new Set(groups.map((group) => String(group.key || '')).filter(Boolean))
    collapsedGroupKeys.value = collapsedGroupKeys.value.filter((key) => validKeys.has(key))
  },
  { immediate: true },
)

watch(
  () => selectedTag.value,
  () => {
    loadProducts()
  },
)

watch(
  () => createForm.value.restaurant_category,
  () => {
    const current = String(createForm.value.restaurant_subcategory || '').trim()
    if (!current) {
      return
    }
    const isValid = createSubcategoryOptions.value.some((row) => String(row?.value || '').trim() === current)
    if (!isValid) {
      createForm.value.restaurant_subcategory = ''
    }
  },
)

function handleKeydown(event) {
  const key = String(event?.key || '').toLowerCase()
  const hasModifier = Boolean(event.ctrlKey || event.metaKey)

  if (hasModifier && key === 's') {
    event.preventDefault()
    if (createPopupOpen.value && !creatingItem.value) {
      submitCreate(false)
    }
    return
  }

  if (hasModifier && key === 'k') {
    event.preventDefault()
    openQuickStartWizard()
    return
  }
}

function getInitialMobileView() {
  if (typeof window === 'undefined') {
    return false
  }
  return window.innerWidth <= MOBILE_BREAKPOINT
}

function syncViewportMode() {
  if (typeof window === 'undefined') {
    return
  }
  isMobileView.value = window.innerWidth <= MOBILE_BREAKPOINT
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  syncViewportMode()
  window.addEventListener('resize', syncViewportMode)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', syncViewportMode)
})

loadMenuCategories()
loadProducts()
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
  position: relative;
  z-index: 20;
  overflow: visible;
}

.products-filter-card {
  position: relative;
  z-index: 35;
  overflow: visible !important;
}

.toolbar .input {
  width: min(420px, 100%);
  min-height: 2.75rem;
  border-radius: 8px;
}

.toolbar-toggle {
  min-height: 2.75rem;
  width: auto;
  min-width: 8.25rem;
}

.view-switcher {
  margin-inline-start: auto;
}

.desktop-table {
  display: block;
}

.mobile-cards {
  display: none;
}

.grouped-list,
.grouped-mobile {
  display: grid;
  gap: 0.65rem;
}

.group-block {
  border-radius: 8px;
}

.group-header-btn {
  width: 100%;
  min-height: 2.85rem;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg-soft, #f1f5f9);
  color: var(--text, #0f172a);
  border-radius: 12px;
  padding: 0.58rem 0.7rem;
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 0.45rem;
  text-align: right;
  margin-bottom: 0.55rem;
}

.group-header-btn strong {
  font-size: 0.82rem;
}

.group-header-btn span {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.group-chevron {
  width: 1rem;
  text-align: center;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.84rem;
}

.state-pill {
  border-radius: 999px;
  padding: 0.2rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 800;
}

.state-pill.on {
  background: rgb(220 252 231 / 0.9);
  color: #166534;
}

.state-pill.off {
  background: rgb(254 243 199 / 0.95);
  color: #92400e;
}

.error {
  margin: 0;
  color: var(--danger);
}

.success-msg {
  margin: 0;
  color: var(--success);
  font-size: 0.82rem;
  font-weight: 600;
}

.create-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.create-form label {
  display: grid;
  gap: 0.24rem;
  font-size: 0.82rem;
}

.create-form .full {
  grid-column: 1 / -1;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.actions {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.status-toggle-btn {
  min-width: 94px;
}

.delete-btn {
  min-width: 70px;
  border-color: rgb(220 38 38 / 0.34);
  color: rgb(185 28 28);
  background: rgb(254 242 242);
}

.delete-btn:hover:not(:disabled) {
  background: rgb(220, 38, 38, 0.1);
  border-color: rgb(220, 38, 38);
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-toggle-btn--inactive {
  border-color: rgb(5 150 105 / 0.28);
  background: rgb(236 253 245);
  color: rgb(4 120 87);
}

.status-toggle-btn--inactive:hover {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.18);
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.5);
}

.row-actions {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.product-card.clickable {
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.product-card.clickable:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.28);
  box-shadow: 0 18px 40px rgb(15 23 42 / 0.1);
  transform: translateY(-2px);
}

.product-card__head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.product-card__media {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg-soft, #f1f5f9);
  flex-shrink: 0;
  display: grid;
  place-items: center;
}

.product-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-card__fallback {
  color: var(--module-600, #6f4726);
  font-size: 0.84rem;
  font-weight: 700;
}

.product-card__meta {
  flex: 1;
  min-width: 0;
}

.product-card__title {
  margin: 0;
  color: var(--text, #0f172a);
  font-size: 0.96rem;
  font-weight: 800;
  line-height: 1.45;
}

.product-card__sub {
  margin: 0.18rem 0 0;
  font-size: 0.82rem;
  color: var(--muted, #64748b);
  line-height: 1.6;
}

.product-card__totals {
  display: flex;
  justify-content: space-between;
  gap: 0.45rem;
  padding: 0.65rem;
  border-radius: 8px;
  background: var(--bg-soft, #f1f5f9);
  font-size: 0.84rem;
  color: var(--text, #0f172a);
}

.product-card__totals p {
  margin: 0;
}

.gallery-status {
  position: absolute;
  top: 0.5rem;
  inset-inline-start: 0.5rem;
  border-radius: 999px;
  padding: 0.16rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
}

.gallery-status.on {
  background: rgb(220 252 231 / 0.95);
  color: #166534;
}

.gallery-status.off {
  background: rgb(254 243 199 / 0.95);
  color: #92400e;
}

@media (max-width: 760px) {
  .toolbar {
    gap: 0.45rem;
    width: 100%;
    overflow: visible;
  }

  .toolbar .input {
    width: 100%;
    min-width: 0;
    flex: 1 1 100%;
  }

  .toolbar .primary-btn,
  .toolbar .secondary-btn,
  .toolbar .tertiary-btn {
    flex: 1 1 auto;
    min-width: 0;
    font-size: 0.8rem;
    min-height: 2.75rem;
    padding: 0.52rem 0.65rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .toolbar .check {
    flex: 0 0 auto;
  }

  .toolbar-toggle {
    flex: 1 1 100%;
    width: 100%;
  }

  .create-form {
    grid-template-columns: minmax(0, 1fr);
  }

  .view-switcher {
    margin-inline-start: 0;
  }

  .desktop-table {
    display: none;
  }

  .mobile-cards {
    display: block;
  }

  .group-header-btn {
    grid-template-columns: 1fr auto auto;
    padding: 0.42rem 0.55rem;
  }

  .group-header-btn strong {
    font-size: 0.78rem;
  }

  .group-header-btn span {
    font-size: 0.7rem;
  }

  .product-card {
    padding: 0.75rem;
    gap: 0.65rem;
  }

  .product-card__head {
    align-items: flex-start;
    gap: 0.42rem;
  }

  .product-card__media {
    width: 52px;
    height: 52px;
    border-radius: 8px;
  }

  .product-card__title {
    font-size: 0.82rem;
  }

  .product-card__sub,
  .product-card__totals {
    font-size: 0.74rem;
  }

  .state-pill {
    font-size: 0.7rem;
    padding: 0.1rem 0.46rem;
  }

  .actions,
  .row-actions {
    gap: 0.28rem;
  }

  .actions .status-toggle-btn,
  .actions .delete-btn,
  .row-actions .status-toggle-btn,
  .row-actions .delete-btn {
    min-width: 0;
    flex: 1 1 0;
    font-size: 0.74rem;
    padding-inline: 0.5rem;
  }
}
</style>

<style scoped>
.advanced-toolbar {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgb(226 232 240 / 1);
}

.wizard-form {
  display: grid;
  gap: 1.25rem;
}

.wizard-step {
  display: grid;
  gap: 1rem;
}

.wizard-step h3 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
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
  background: var(--module-50, rgb(139 94 52 / 0.075));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.14);
  border-radius: 12px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.tertiary-btn {
  background: transparent;
  border: 1px solid rgb(226 232 240 / 1);
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.tertiary-btn:hover {
  background: var(--module-50, rgb(139 94 52 / 0.075));
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.22);
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  min-height: 1.5rem;
  padding: 0.18rem 0.52rem;
  border-radius: 999px;
  background: #eef2ff;
  color: #3730a3;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  margin-inline-end: 0.25rem;
  margin-bottom: 0.15rem;
}

.tag-pill.more {
  background: var(--bg-soft, #f1f5f9);
  color: var(--text, #0f172a);
  font-weight: 600;
}

.product-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 180px;
  position: relative;
  z-index: 25;
}

@media (prefers-reduced-motion: reduce) {
  .product-card.clickable,
  .product-card.clickable:hover {
    transform: none;
  }
}

.filter-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}
</style>
