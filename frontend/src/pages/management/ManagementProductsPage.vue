<template>
  <div class="products-page">
    <ManagementSurfaceCard tone="accent" class="products-filter-card">
      <!-- تولبار تمیز: سرچ + کالای جدید -->
      <div class="toolbar toolbar--clean">
        <div class="toolbar-search">
          <Search :size="15" class="toolbar-search-icon" />
          <input
            class="input toolbar-search-input"
            v-model="search"
            placeholder="جستجو محصول..."
            @keydown.enter.prevent="loadProducts"
          />
          <button v-if="search" type="button" class="toolbar-search-clear" @click="search = ''; loadProducts()">
            <X :size="13" />
          </button>
        </div>
        <button class="primary-btn toolbar-new-btn" type="button" @click="openCreatePopup">
          <Plus :size="15" /> کالای جدید
        </button>
      </div>

      <div class="notion-view-bar">
        <NotionViewTabs
          :views="viewSys.views.value"
          :current-view-id="viewSys.currentViewId.value"
          :is-dirty="viewSys.isViewDirty"
          @select="viewSys.selectView"
          @add="viewSys.addView"
          @rename="viewSys.renameView"
          @duplicate="viewSys.duplicateView"
          @delete="viewSys.deleteView"
          @reset="viewSys.resetView"
          @copy-link="viewCopyLink"
        />
        <div class="notion-view-tools">
          <NotionViewControls
            v-if="viewSys.currentView.value"
            :view="viewSys.currentView.value"
            :properties="PRODUCT_PROPERTIES"
          />
          <NotionViewSettings
            v-if="viewSys.currentView.value"
            :view="viewSys.currentView.value"
            :properties="PRODUCT_PROPERTIES"
            @reset="viewSys.resetView"
            @search="search = $event"
          />
        </div>
        <NotionSaveBar
          v-if="viewSys.isCurrentViewDirty.value"
          :visible="viewSys.isCurrentViewDirty.value"
          :view-name="viewSys.currentView.value?.name"
          @save-self="viewSys.saveForSelf()"
          @save-all="viewSys.saveForEveryone()"
          @discard="viewSys.resetView(viewSys.currentViewId.value)"
        />
      </div>
    </ManagementSurfaceCard>

    <p class="muted" v-if="loading">در حال بارگذاری محصولات...</p>
    <p class="error" v-if="error">{{ error }}</p>
    <p class="success-msg" v-if="successMessage">{{ successMessage }}</p>

    <ManagementSurfaceCard :title="activeViewTitle" :subtitle="activeViewSubtitle">
      <template v-if="viewMode === 'tree'">
        <div class="tree-group-bar">
          <span class="tree-group-label">درخت بر اساس</span>
          <SearchableDropdown
            :model-value="treeGroupBy"
            :options="treeGroupOptions"
            placeholder="انتخاب فیلد..."
            search-placeholder="جستجو..."
            @update:model-value="treeGroupBy = $event || 'category_title'; writeStoredTreeGroupBy(treeGroupBy)"
          />
        </div>
        <ManagementTreeView
          :nodes="productTreeNodes"
          empty-text="محصولی برای نمایش وجود ندارد."
          :node-clickable="canOpenProductTreeNode"
          @node-click="handleProductTreeNodeClick"
        >
          <template #icon="{ node }">
            <Folder v-if="node.badge === 'دسته'" :size="15" :stroke-width="2" />
            <Package v-else :size="14" :stroke-width="2" />
          </template>
        </ManagementTreeView>
      </template>

      <template v-else-if="viewMode === 'kanban'">
        <div class="kanban-group-bar">
          <span class="kanban-group-label">کانبان بر اساس</span>
          <SearchableDropdown
            :model-value="kanbanGroupBy"
            :options="kanbanGroupOptions"
            placeholder="انتخاب فیلد..."
            search-placeholder="جستجو..."
            @update:model-value="kanbanGroupBy = $event || 'category_title'; writeStoredKanbanGroupBy(kanbanGroupBy)"
          />
        </div>
        <ManagementKanbanView
          :rows="visibleProducts"
          :group-by="kanbanGroupBy"
          :group-options="kanbanGroupOptions"
          row-key="name"
          :clickable="true"
          image-field="image"
          secondary-image-field="website_image"
          :price-formatter="(value) => formatMoney(value, currency.value)"
          :row-class="rowClassOf"
          empty-text="محصولی برای نمایش وجود ندارد."
          @row-click="openProductDetail"
          @move-row="handleKanbanMove"
        />
      </template>

      <template v-else-if="viewMode === 'list'">
        <!-- گروه‌بندی Notion (دسکتاپ) -->
        <div v-if="viewGroupedRows" class="grouped-list desktop-table">
          <ManagementSurfaceCard
            v-for="group in viewGroupedRows"
            :key="`vg-${group.key}`"
            class="group-block"
            tone="soft"
          >
            <button type="button" class="group-header-btn" @click="toggleGroupCollapse(`vg-${group.key}`)">
              <strong>{{ viewGroupLabel(group.label, viewSys.currentView.value?.groupBy) }}</strong>
              <span>{{ formatNumber(totalRowsInGroup(group)) }} کالا</span>
              <span class="group-chevron">{{ isGroupCollapsed(`vg-${group.key}`) ? '▸' : '▾' }}</span>
            </button>
            <template v-if="!isGroupCollapsed(`vg-${group.key}`)">
              <template v-if="group.subgroups">
                <div v-for="sub in group.subgroups" :key="sub.key" class="subgroup-block">
                  <div class="subgroup-header">
                    <strong>{{ viewGroupLabel(sub.label, viewSys.currentView.value?.subGroupBy) }}</strong>
                    <span>{{ formatNumber(sub.rows.length) }} کالا</span>
                  </div>
                  <ManagementNotionListView
                    :rows="sub.rows"
                    row-key="name"
                    :row-clickable="true"
                    :show-code="isPropVisible('item_code')"
                    :show-tags="isPropVisible('tags')"
                    :properties="viewSys.currentView.value?.properties"
                    :property-order="currentViewPropertyOrder"
                    :chip-renderers="chipRenderers"
                    :row-class="rowClassOf"
                    @row-click="openProductDetail"
                  >
                  </ManagementNotionListView>
                </div>
              </template>
              <ManagementNotionListView
                v-else
                :rows="group.rows"
                row-key="name"
                :row-clickable="true"
                :show-code="isPropVisible('item_code')"
                :show-tags="isPropVisible('tags')"
                :properties="viewSys.currentView.value?.properties"
                :property-order="currentViewPropertyOrder"
                :chip-renderers="chipRenderers"
                :row-class="rowClassOf"
                @row-click="openProductDetail"
              >
              </ManagementNotionListView>
            </template>
          </ManagementSurfaceCard>
        </div>

        <!-- لیست تخت Notion (دسکتاپ) -->
        <ManagementNotionListView
          v-else
          class="desktop-list"
          :rows="visibleProducts"
          row-key="name"
          :row-clickable="true"
          :show-code="isPropVisible('item_code')"
          :show-tags="isPropVisible('tags')"
          :properties="viewSys.currentView.value?.properties"
          :property-order="currentViewPropertyOrder"
          :chip-renderers="chipRenderers"
          :row-class="rowClassOf"
          @row-click="openProductDetail"
        >
        </ManagementNotionListView>


      </template>

      <ManagementSheetView
        v-else-if="viewMode === 'sheet'"
        :rows="visibleProducts"
        :columns="sheetColumns"
        :select-options="viewSelectOptions"
        row-key="name"
        :frozen-columns="['item_code', 'title']"
        :cell-formatters="{
          base_price: (row) => formatMoney(row.base_price, currency.value),
          stock_qty: (row) => formatStock(row.stock_qty),
          is_active: (row) => (isProductActive(row) ? 'بله' : 'خیر'),
        }"
        @cell-change="handleSheetCellChange"
        @add-row="openCreatePopup"
        @row-open="openProductDetail"
        @bulk-action="handleSheetBulkAction"
        @export-excel="handleSheetExportExcel"
        @bulk-edit="handleSheetBulkEdit"
      />

      <ManagementCalendarView
        v-else-if="viewMode === 'calendar'"
        :rows="visibleProducts"
        :chip-renderers="chipRenderers"
        :properties="viewSys.currentView.value?.properties"
        :property-order="currentViewPropertyOrder"
        :row-class="rowClassOf"
        @open-item="openProductDetail"
        @assign-date="handleCalendarAssign"
        @clear-date="handleCalendarClear"
      />

      <ManagementGalleryView
        v-else
        :rows="visibleProducts"
        row-key="name"
        image-field="image"
        secondary-image-field="website_image"
        title-field="title"
        subtitle-field="category_title"
        :clickable="true"
        :properties="viewSys.currentView.value?.properties"
        :property-order="currentViewPropertyOrder"
        :chip-renderers="chipRenderers"
        :row-class="rowClassOf"
        @click-item="openProductDetail"
      >
        <template #overlay="{ row }">
          <span class="gallery-status" :class="isProductActive(row) ? 'on' : 'off'">
            {{ visibilityStateLabel(row) }}
          </span>
        </template>
      </ManagementGalleryView>
    </ManagementSurfaceCard>

    <div class="products-load-more" v-if="!loading && hasMoreProducts">
      <button type="button" class="secondary-btn" @click="loadMoreProducts">
        بارگذاری بیشتر
      </button>
      <small>
        {{ formatNumber(products.length) }} کالا بارگذاری شده
        <template v-if="productTotalHint"> از {{ formatNumber(productTotalHint) }}</template>
      </small>
    </div>

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
            fixed-panel
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
            fixed-panel
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
            fixed-panel
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
            fixed-panel
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
              fixed-panel
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
              fixed-panel
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

    <ManagementPopup
      v-model:open="bulkPopupOpen"
      title="عملیات گروهی محصولات"
      :subtitle="`${formatNumber(visibleProducts.length)} کالا در نمایش فعلی (با فیلترها) انتخاب شده‌اند`"
      :close-on-backdrop="!bulkBusy"
      :close-on-escape="!bulkBusy"
    >
      <div class="bulk-form">
        <p class="hint">
          عملیات انتخابی روی تمام کالاهای نمایش‌داده‌شده (با اعمال جستجو و فیلترهای فعلی) انجام می‌شود.
          برای محدود کردن لیست، ابتدا از جستجو یا فیلتر گروه استفاده کنید.
        </p>

        <div class="bulk-actions-grid">
          <button
            v-for="option in bulkActionOptions"
            :key="option.value"
            type="button"
            :class="['bulk-action-card', { active: bulkAction === option.value }]"
            @click="bulkAction = option.value"
          >
            <strong>{{ option.title }}</strong>
            <small>{{ option.desc }}</small>
          </button>
        </div>

        <p class="error" v-if="bulkError">{{ bulkError }}</p>

        <div v-if="bulkResult" class="bulk-result">
          <p class="success-msg">
            {{ formatNumber(bulkResult.updated || 0) }} کالا به‌روزرسانی شد
            <template v-if="bulkResult.failed">({{ formatNumber(bulkResult.failed) }} خطا)</template>
          </p>
          <ul v-if="bulkResult.results && bulkResult.results.some(r => r.status === 'error')" class="bulk-error-list">
            <li v-for="(row, idx) in bulkResult.results.filter(r => r.status === 'error').slice(0, 8)" :key="idx">
              {{ row.item_name }}: {{ row.message }}
            </li>
          </ul>
        </div>
      </div>

      <template #footer>
        <div class="popup-actions">
          <button class="secondary-btn" type="button" :disabled="bulkBusy" @click="bulkPopupOpen = false">بستن</button>
          <button class="primary-btn" type="button" :disabled="bulkBusy || !visibleProducts.length" @click="runBulkAction">
            {{ bulkBusy ? 'در حال اعمال...' : `اعمال روی ${formatNumber(visibleProducts.length)} کالا` }}
          </button>
        </div>
      </template>
    </ManagementPopup>

    <ManagementPopup
      v-model:open="excelSummaryOpen"
      title="نتیجه ورود اطلاعات از اکسل"
      subtitle="گزارش ایجاد و به‌روزرسانی محصولات"
    >
      <div class="excel-summary" v-if="excelSummary">
        <div class="excel-summary-grid">
          <div><small>کل سطرها</small><strong>{{ formatNumber(excelSummary.total_rows || 0) }}</strong></div>
          <div><small>ایجاد شده</small><strong>{{ formatNumber(excelSummary.created || 0) }}</strong></div>
          <div><small>به‌روزرسانی</small><strong>{{ formatNumber(excelSummary.updated || 0) }}</strong></div>
          <div><small>خطا</small><strong>{{ formatNumber((excelSummary.errors || []).length) }}</strong></div>
        </div>
        <ul v-if="(excelSummary.errors || []).length" class="bulk-error-list">
          <li v-for="(rowError, idx) in excelSummary.errors.slice(0, 10)" :key="idx">
            سطر {{ rowError.row }} {{ rowError.item_code ? `(${rowError.item_code})` : '' }}: {{ rowError.message }}
          </li>
        </ul>
      </div>
      <template #footer>
        <div class="popup-actions">
          <button class="primary-btn" type="button" @click="excelSummaryOpen = false">بستن</button>
        </div>
      </template>
    </ManagementPopup>

  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementNotionListView from '@/components/management/ManagementNotionListView.vue'
import NotionViewTabs from '@/components/management/notion/NotionViewTabs.vue'
import NotionSaveBar from '@/components/management/notion/NotionSaveBar.vue'
import NotionViewControls from '@/components/management/notion/NotionViewControls.vue'
import NotionViewSettings from '@/components/management/notion/NotionViewSettings.vue'
import {
  useViewSystem,
  applyViewFilters,
  applyViewSorts,
  groupRows,
  colorForRow,
  buildSelectOptions,
  PRODUCT_PROPERTIES,
} from '@/utils/viewSystem'
import ManagementGalleryView from '@/components/management/ManagementGalleryView.vue'
import ManagementCalendarView from '@/components/management/ManagementCalendarView.vue'
import ManagementSheetView from '@/components/management/ManagementSheetView.vue'
import ManagementKanbanView from '@/components/management/ManagementKanbanView.vue'
import ManagementTreeView from '@/components/management/ManagementTreeView.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import NumericInput from '@/components/NumericInput.vue'
import {
  bulkUpdateManagementProducts,
  createManagementProduct,
  deleteManagementProduct,
  exportManagementProductsExcel,
  getManagementProductDetail,
  getMenuBoot,
  importManagementProductsExcel,
  listManagementPriceLists,
  listManagementProducts,
  setManagementProductActive,
  setManagementProductCalendarDate,
  setManagementProductKanbanField,
  setManagementProductPrice,
  uploadFileToFrappe,
} from '@/utils/api'
import { formatMoney } from '@/utils/format'
import { jalaliToGregorian } from '@/utils/jalali'
import { Folder, Package, Plus, Search, X } from 'lucide-vue-next'

const PRODUCT_VISIBILITY_OVERRIDES_KEY = 'management-products-visibility-overrides'
const MOBILE_BREAKPOINT = 820
const PRODUCT_PAGE_SIZE = 80

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const products = ref([])
const hasMoreProducts = ref(false)
const productTotalHint = ref(0)
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
const treeGroupBy = ref(readStoredTreeGroupBy())
const kanbanGroupBy = ref(readStoredKanbanGroupBy())
const isMobileView = ref(getInitialMobileView())
const excelFileInput = ref(null)
const excelBusy = ref(false)
const excelMode = ref('')
const excelSummary = ref(null)
const excelSummaryOpen = ref(false)
const bulkBusy = ref(false)
const bulkAction = ref('show_in_menu')
const bulkResult = ref(null)
const bulkError = ref('')

const sortOptions = [
  { value: 'latest', label: 'جدیدترین' },
  { value: 'name', label: 'نام کالا' },
  { value: 'price_desc', label: 'گران‌ترین' },
  { value: 'price_asc', label: 'ارزان‌ترین' },
  { value: 'stock_desc', label: 'بیشترین موجودی' },
  { value: 'stock_asc', label: 'کمترین موجودی' },
]

const bulkActionOptions = [
  { value: 'show_in_menu', title: 'نمایش در منو', desc: 'کالاهای انتخاب‌شده فعال می‌شوند.' },
  { value: 'hide_from_menu', title: 'پنهان از منو', desc: 'کالاهای انتخاب‌شده از نمایش خارج می‌شوند.' },
  { value: 'show_in_print', title: 'نمایش در چاپ', desc: 'در رسید و گزارش چاپی نمایش داده می‌شوند.' },
  { value: 'hide_from_print', title: 'حذف از چاپ', desc: 'از چاپ‌های عملیاتی حذف می‌شوند.' },
]

const treeGroupOptions = PRODUCT_PROPERTIES
  .filter((prop) => ['select', 'boolean', 'tags'].includes(prop.type))
  .map((prop) => ({ value: prop.key, label: prop.label }))

const kanbanGroupOptions = PRODUCT_PROPERTIES
  .filter((prop) => ['select', 'boolean'].includes(prop.type))
  .map((prop) => ({ value: prop.key, label: prop.label }))

// ── سیستم View به سبک Notion ────────────────────────────────────────────────
const viewSys = useViewSystem({ storageKey: 'mg-products-notion-views-v1' })
viewSys.load()
// layout ذخیره‌شده در view را به viewMode منتقل کن (برای بار اول)
if (viewSys.currentView.value?.layout && viewMode.value !== viewSys.currentView.value.layout) {
  viewMode.value = viewSys.currentView.value.layout
}

// گزینه‌های قابل انتخاب برای فیلدهای select — از دیتای محصولات استخراج می‌شود
const viewSelectOptions = computed(() => {
  const map = {}
  const selectProps = PRODUCT_PROPERTIES.filter((p) => p.type === 'select' || p.type === 'tags')
  for (const prop of selectProps) {
    map[prop.key] = buildSelectOptions(products.value, prop.key)
  }
  return map
})

const VIEW_PROPERTY_ORDER = ['category_title', 'base_price', 'stock_qty', 'is_active', 'tags', 'item_code']
const currentViewPropertyOrder = computed(() => {
  const order = viewSys.currentView.value?.propertyOrder
  return order && order.length ? order : VIEW_PROPERTY_ORDER
})

const normalizedProductSearch = computed(() => normalizeSearchText(search.value))

const visibleProducts = computed(() => {
  const currentView = viewSys.currentView.value || {}
  let rows = Array.isArray(products.value) ? [...products.value] : []

  if (activeOnly.value) {
    rows = rows.filter(isProductActive)
  }
  if (selectedTag.value) {
    rows = rows.filter((row) => (Array.isArray(row?.tags) ? row.tags : []).includes(selectedTag.value))
  }
  if (selectedCategorySlugs.value.length) {
    const selected = new Set(selectedCategorySlugs.value.map((value) => String(value || '').trim()).filter(Boolean))
    rows = rows.filter((row) => {
      const candidates = [row?.category, row?.category_slug, row?.category_title, row?.restaurant_category]
        .map((value) => String(value || '').trim())
        .filter(Boolean)
      return candidates.some((value) => selected.has(value))
    })
  }
  if (normalizedProductSearch.value) {
    rows = rows.filter((row) => productMatchesSearch(row, normalizedProductSearch.value))
  }

  rows = applyViewFilters(rows, Array.isArray(currentView.filters) ? currentView.filters : [])
  rows = applyViewSorts(rows, Array.isArray(currentView.sorts) ? currentView.sorts : [])

  if (!currentView.sorts?.length) {
    rows.sort((a, b) => compareProducts(a, b, sortBy.value))
  }

  return rows
})

const groupedProducts = computed(() => {
  if (groupBy.value === 'none') {
    return []
  }
  const groups = new Map()
  for (const row of visibleProducts.value) {
    const group = resolveGroupKey(row)
    if (!groups.has(group.key)) {
      groups.set(group.key, { ...group, rows: [] })
    }
    groups.get(group.key).rows.push(row)
  }
  return Array.from(groups.values())
})

const activeViewTitle = computed(() => viewSys.currentView.value?.name || 'محصولات')
const activeViewSubtitle = computed(() => {
  const count = formatNumber(visibleProducts.value.length)
  const total = formatNumber(products.value.length)
  if (viewGroupedRows.value) {
    return `${count} کالا از ${total} کالا، گروه‌بندی‌شده بر اساس نما`
  }
  return `${count} کالا از ${total} کالا در نمایش فعلی`
})

const categoryOptions = computed(() => {
  const options = buildSelectOptions(products.value, 'category_title')
  return options.length ? options : normalizeOptionRows(bootFieldOptions.value.categories)
})

const createSubcategoryOptions = computed(() => {
  const selectedCategory = String(createForm.value.restaurant_category || '').trim()
  const rows = normalizeOptionRows(bootFieldOptions.value.subcategories)
  if (!selectedCategory) {
    return rows.length ? rows : buildSelectOptions(products.value, 'subcategory_title')
  }
  const filtered = rows.filter((row) => {
    const category = String(row.category || row.parent_category || row.restaurant_category || '').trim()
    return !category || category === selectedCategory
  })
  return filtered.length ? filtered : buildSelectOptions(
    products.value.filter((row) => String(row?.category_title || row?.category || '').trim() === selectedCategory),
    'subcategory_title',
  )
})

const uomOptions = computed(() => normalizeOptionRows(bootFieldOptions.value.uoms))
const itemGroupOptions = computed(() => normalizeOptionRows(bootFieldOptions.value.item_groups))

const productTreeNodes = computed(() => {
  const grouped = groupRows(visibleProducts.value, treeGroupBy.value || 'category_title', '')
  return (grouped || []).map((group) => ({
    key: `group-${group.key}`,
    label: viewGroupLabel(group.label, treeGroupBy.value),
    badge: 'دسته',
    children: (group.rows || []).map((row) => ({
      key: row.name,
      name: row.name,
      label: displayProductCode(row),
      badge: 'محصول',
      meta: formatMoney(row.base_price || 0, currency.value),
      row,
    })),
  }))
})

function isPropVisible(key) {
  return viewSys.currentView.value?.properties?.[key] !== false
}

const chipRenderers = {
  // فیلدهای متنی
  name: (row) => (row.name ? { text: row.name, cls: 'notion-chip--code' } : null),
  item_code: (row) => (row.item_code ? { text: row.item_code, cls: 'notion-chip--code' } : null),
  title: (row) => (row.title ? { text: row.title } : null),
  short_desc: (row) => (row.short_desc ? { text: row.short_desc } : null),
  custom_snapp_code: (row) => (row.custom_snapp_code ? { text: `اسنپ: ${row.custom_snapp_code}`, cls: 'notion-chip--code' } : null),
  restaurant_builder_template: (row) => (row.restaurant_builder_template ? { text: row.restaurant_builder_template, cls: 'notion-chip--soft' } : null),
  restaurant_customize_button_label: (row) => (row.restaurant_customize_button_label ? { text: row.restaurant_customize_button_label } : null),
  // فیلدهای گزینه‌ای
  category_title: (row) => (row.category_title ? { text: row.category_title, cls: 'notion-chip--soft' } : null),
  subcategory_title: (row) => (row.subcategory_title ? { text: row.subcategory_title, cls: 'notion-chip--soft' } : null),
  // فیلدهای عددی
  base_price: (row) => ({ text: formatMoney(row.base_price, currency.value) }),
  stock_qty: (row) => ({ text: `موجودی: ${formatStock(row.stock_qty)}` }),
  nutrition_kcal: (row) => (row.nutrition_kcal != null ? { text: `${formatNumber(row.nutrition_kcal)} کالری` } : null),
  nutrition_protein_g: (row) => (row.nutrition_protein_g != null ? { text: `پروتئین: ${formatNumber(row.nutrition_protein_g)}g` } : null),
  nutrition_carb_g: (row) => (row.nutrition_carb_g != null ? { text: `کربوهیدرات: ${formatNumber(row.nutrition_carb_g)}g` } : null),
  nutrition_fat_g: (row) => (row.nutrition_fat_g != null ? { text: `چربی: ${formatNumber(row.nutrition_fat_g)}g` } : null),
  sort_order: (row) => (row.sort_order != null ? { text: `ترتیب: ${formatNumber(row.sort_order)}` } : null),
  packaging_price: (row) => (row.packaging_price ? { text: `بسته‌بندی: ${formatMoney(row.packaging_price, currency.value)}` } : null),
  // فیلدهای وضعیت/بولی
  is_active: (row) => ({
    text: isProductActive(row) ? 'فعال' : 'غیرفعال',
    cls: isProductActive(row) ? 'notion-chip--on' : 'notion-chip--off',
  }),
  coming_soon: (row) => (Number(row.coming_soon) === 1 ? { text: 'به‌زودی', cls: 'notion-chip--warn' } : null),
  out_of_stock: (row) => (Number(row.out_of_stock) === 1 ? { text: 'ناموجود', cls: 'notion-chip--off' } : null),
  has_customization: (row) => (Number(row.has_customization) === 1 ? { text: 'قابل شخصی‌سازی', cls: 'notion-chip--on' } : null),
  has_bom: (row) => (Number(row.has_bom) === 1 ? { text: 'دارای BOM', cls: 'notion-chip--soft' } : null),
  // تگ‌ها جداگانه مدیریت می‌شوند (showTags)
}

function rowClassOf(row) {
  const color = colorForRow(row, viewSys.currentView.value?.colors)
  return color ? `nrow-${color}` : ''
}

const viewGroupedRows = computed(() => {
  const view = viewSys.currentView.value
  if (!view?.groupBy) return null
  return groupRows(visibleProducts.value, view.groupBy, view.subGroupBy || '')
})

function totalRowsInGroup(group) {
  if (group?.subgroups) return group.subgroups.reduce((sum, sub) => sum + sub.rows.length, 0)
  return group?.rows?.length || 0
}

function viewGroupLabel(value, propertyKey) {
  const prop = PRODUCT_PROPERTIES.find((p) => p.key === propertyKey)
  if (prop?.type === 'boolean' || prop?.type === 'select' && (value === 1 || value === 0 || value === true || value === false)) {
    return Number(value) === 1 || value === true ? 'بله' : 'خیر'
  }
  return String(value ?? '').trim() || 'بدون دسته'
}

function viewCopyLink(viewId) {
  const url = `${window.location.origin}${window.location.pathname}?view=${encodeURIComponent(viewId)}`
  try {
    navigator.clipboard?.writeText(url)
    successMessage.value = 'لینک نما کپی شد.'
  } catch (_) {
    window.prompt('لینک نما:', url)
  }
}

watch(
  () => viewSys.currentView.value?.id,
  () => {
    const layout = viewSys.currentView.value?.layout
    if (layout && viewMode.value !== layout) viewMode.value = layout
  },
)

watch(viewMode, (mode) => {
  if (viewSys.currentView.value) viewSys.updateCurrentView({ layout: mode })
})

watch(
  () => viewSys.currentView.value?.layout,
  (layout) => {
    if (layout && viewMode.value !== layout) viewMode.value = layout
  },
)

watch(
  () => viewSys.currentView.value?.groupBy,
  (group) => {
    if (group) groupBy.value = 'none'
  },
)
// ────────────────────────────────────────────────────────────────────────────
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
const bulkPopupOpen = ref(false)
async function loadProducts(append = false) {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementProducts({
      search: search.value,
      active_only: activeOnly.value ? 1 : 0,
      tag: selectedTag.value,
      limit_start: append ? products.value.length : 0,
      limit_page_length: PRODUCT_PAGE_SIZE,
    })
    const nextProducts = applyVisibilityOverrides(payload.products || [])
    products.value = append ? [...products.value, ...nextProducts] : nextProducts
    hasMoreProducts.value = Boolean(payload.has_more)
    productTotalHint.value = Number(payload.total_count || 0)

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

function loadMoreProducts() {
  if (loading.value || !hasMoreProducts.value) {
    return
  }
  loadProducts(true)
}

function openBulkPopup() {
  bulkResult.value = null
  bulkError.value = ''
  bulkPopupOpen.value = true
}

async function runBulkAction() {
  if (!visibleProducts.value.length || bulkBusy.value) {
    return
  }
  bulkBusy.value = true
  bulkError.value = ''
  bulkResult.value = null
  try {
    const names = visibleProducts.value.map((row) => String(row?.name || '').trim()).filter(Boolean)
    const payload = await bulkUpdateManagementProducts(names, bulkAction.value)
    bulkResult.value = payload
    await loadProducts()
  } catch (errObj) {
    bulkError.value = errObj?.message || '❌ عملیات گروهی ناموفق بود. لطفاً دوباره تلاش کنید.'
  } finally {
    bulkBusy.value = false
  }
}

async function exportProductsExcel() {
  if (excelBusy.value) {
    return
  }
  excelBusy.value = true
  excelMode.value = 'export'
  error.value = ''
  try {
    const payload = await exportManagementProductsExcel({ include_disabled: 1 })
    if (payload?.file_url) {
      const link = document.createElement('a')
      link.href = payload.file_url
      link.download = payload.file_name || 'restaurant-products.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      successMessage.value = `خروجی اکسل ${formatNumber(payload.rows || 0)} کالا آماده شد.`
      setTimeout(() => { successMessage.value = '' }, 4000)
    }
  } catch (errObj) {
    error.value = errObj?.message || '❌ دریافت خروجی اکسل ناموفق بود.'
  } finally {
    excelBusy.value = false
    excelMode.value = ''
  }
}

function triggerExcelImport() {
  if (excelBusy.value) {
    return
  }
  const input = excelFileInput.value
  if (input) {
    input.value = ''
    input.click()
  }
}

async function handleExcelFile(event) {
  const file = event?.target?.files?.[0]
  if (!file) {
    return
  }
  excelBusy.value = true
  excelMode.value = 'import'
  error.value = ''
  try {
    const uploaded = await uploadFileToFrappe(file, { isPrivate: true })
    const fileUrl = uploaded?.file_url || uploaded?.message?.file_url || ''
    if (!fileUrl) {
      throw new Error('آپلود فایل ناموفق بود.')
    }
    const payload = await importManagementProductsExcel({
      file_url: fileUrl,
      file_name: file.name,
      update_existing: 1,
      dry_run: 0,
    })
    excelSummary.value = payload
    excelSummaryOpen.value = true
    await loadProducts()
  } catch (errObj) {
    error.value = errObj?.message || '❌ ورود اطلاعات از اکسل ناموفق بود.'
  } finally {
    excelBusy.value = false
    excelMode.value = ''
    if (event?.target) {
      event.target.value = ''
    }
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

// وقتی وضعیت واقعاً روی سرور ست می‌شود، override محلی را حذف کن تا
// بعد از رفرش، مقدار سرور برگردد و کارت در کانبان برنگردد.
function clearVisibilityOverride(itemName) {
  const name = String(itemName || '').trim()
  if (!name) {
    return
  }
  const overrides = readVisibilityOverrides()
  if (Object.prototype.hasOwnProperty.call(overrides, name)) {
    delete overrides[name]
    writeVisibilityOverrides(overrides)
  }
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

function compareProducts(a, b, mode = 'latest') {
  const titleA = String(a?.title || a?.item_name || a?.item_code || a?.name || '')
  const titleB = String(b?.title || b?.item_name || b?.item_code || b?.name || '')
  if (mode === 'name') {
    return titleA.localeCompare(titleB, 'fa')
  }
  if (mode === 'price_desc' || mode === 'price_asc') {
    const diff = Number(a?.base_price || 0) - Number(b?.base_price || 0)
    return mode === 'price_desc' ? -diff : diff
  }
  if (mode === 'stock_desc' || mode === 'stock_asc') {
    const diff = Number(a?.stock_qty || 0) - Number(b?.stock_qty || 0)
    return mode === 'stock_desc' ? -diff : diff
  }
  const modifiedA = new Date(a?.modified || a?.creation || 0).getTime() || 0
  const modifiedB = new Date(b?.modified || b?.creation || 0).getTime() || 0
  return modifiedB - modifiedA
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

function readStoredTreeGroupBy() {
  try {
    const raw = localStorage.getItem('management-products-tree-group-by')
    if (['category_title', 'subcategory_title', 'is_active', 'tags', 'coming_soon', 'has_customization'].includes(raw)) {
      return raw
    }
  } catch (_) { /* ignore */ }
  return 'category_title'
}

function writeStoredTreeGroupBy(value) {
  try {
    localStorage.setItem('management-products-tree-group-by', String(value || 'category_title'))
  } catch (_) { /* ignore */ }
}

function readStoredKanbanGroupBy() {
  try {
    const raw = localStorage.getItem('management-products-kanban-group-by')
    if (['category_title', 'subcategory_title', 'is_active', 'coming_soon', 'out_of_stock'].includes(raw)) {
      return raw
    }
  } catch (_) { /* ignore */ }
  return 'category_title'
}

function writeStoredKanbanGroupBy(value) {
  try {
    localStorage.setItem('management-products-kanban-group-by', String(value || 'category_title'))
  } catch (_) { /* ignore */ }
}

function readStoredViewMode() {
  try {
    const raw = localStorage.getItem('management-products-view-mode')
    if (raw === 'grid') {
      return 'gallery'
    }
    if (['list', 'gallery', 'tree', 'calendar', 'sheet', 'kanban'].includes(raw)) {
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
  const params = new URLSearchParams(window.location.search)
  const viewId = params.get('view')
  if (viewId) viewSys.selectView(viewId)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', syncViewportMode)
})

loadMenuCategories()
loadProducts()
</script>

<style scoped>
/* Theme-enhanced product page styles — matching Tables / POS theme */
.tree-group-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  margin-bottom: 0.4rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-surface);
}

.tree-group-label {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--mg-text-main);
  white-space: nowrap;
}

.tree-group-bar .searchable-dropdown {
  max-width: 220px;
}

.kanban-group-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  margin-bottom: 0.4rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-surface);
}

.kanban-group-label {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--mg-text-main);
  white-space: nowrap;
}

.kanban-group-bar .searchable-dropdown {
  max-width: 220px;
}
.products-page {
  display: grid;
  gap: 1rem;
  /* جلوگیری از پهن‌شدن صفحه توسط جدول عریض: ستون‌های grid اجازه
     کوچک‌شدن تا صفر را دارند و کارت‌ها هرگز از عرض صفحه بیرون نمی‌زنند */
  grid-template-columns: minmax(0, 1fr);
  min-width: 0;
}

.products-page > * {
  min-width: 0;
}

.toolbar {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
  position: relative;
  z-index: 20;
  overflow: visible;
  padding: 0.35rem;
  border-radius: var(--mg-radius-md, 16px);
  background: var(--mg-bg-surface, #FBF7F1);
  border: 1px solid var(--mg-border-light, rgba(216, 200, 180, 0.4));
  box-shadow: var(--mg-shadow-sm, 0 8px 24px rgba(52, 38, 31, 0.06));
}

/* تولبار تمیز: سرچ + کالای جدید */
.toolbar--clean {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding: 0.45rem 0.5rem;
  border: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.toolbar-search {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 480px;
  display: flex;
  align-items: center;
}

.toolbar-search-icon {
  position: absolute;
  right: 0.75rem;
  color: var(--mg-text-muted);
  pointer-events: none;
}

.toolbar-search-input {
  width: 100%;
  min-height: 2.5rem;
  border-radius: 10px;
  padding-right: 2.4rem;
  padding-left: 2.2rem;
  font-size: 0.82rem;
}

.toolbar-search-clear {
  position: absolute;
  left: 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 50%;
  background: var(--mg-bg-soft);
  color: var(--mg-text-muted);
  cursor: pointer;
}

.toolbar-search-clear:hover {
  background: var(--mg-bg-soft);
  color: var(--mg-danger);
}

.toolbar-new-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.5rem;
  padding: 0.4rem 1.1rem;
  border-radius: 10px;
  font-weight: 700;
  white-space: nowrap;
  background: linear-gradient(135deg, var(--mg-primary) 0%, var(--mg-primary-hover) 100%);
  border: 1px solid var(--mg-primary);
  color: #fff;
  box-shadow: 0 4px 14px rgb(var(--mg-primary-rgb) / 0.3);
  transition: all 0.15s ease;
}

.toolbar-new-btn:hover {
  background: linear-gradient(135deg, var(--mg-primary-hover) 0%, var(--mg-primary) 100%);
  box-shadow: 0 6px 18px rgb(var(--mg-primary-rgb) / 0.4);
  transform: translateY(-1px);
}

.products-filter-card {
  position: relative;
  z-index: 35;
  overflow: visible !important;
  border-radius: var(--mg-radius-md);
  border-color: var(--mg-border-light);
  background: var(--mg-bg-surface);
  box-shadow: var(--mg-shadow-sm);
}

.products-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  flex-wrap: wrap;
  margin: 0.15rem 0 0.55rem;
  color: var(--mg-text-muted);
  font-size: 0.76rem;
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

.notion-view-bar {
  margin-top: 0.55rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--mg-border-light);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.notion-view-tools {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.subgroup-block {
  padding: 0.2rem 0.4rem;
}

.subgroup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  font-size: 0.72rem;
  color: var(--mg-text-muted);
  border-bottom: 1px dashed var(--mg-border-light);
  margin-bottom: 0.2rem;
}

.subgroup-header strong {
  color: var(--mg-success);
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
  border: 1px solid color-mix(in srgb, var(--mg-success) 30%, var(--mg-border-light));
  background: var(--mg-success-bg);
  color: var(--text, var(--mg-text-main));
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
  color: var(--mg-success);
}

.group-header-btn span {
  font-size: 0.74rem;
  color: var(--mg-text-muted);
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
  color: var(--mg-success);
}

.state-pill.off {
  background: rgb(254 243 199 / 0.95);
  color: #92400e;
}

.notion-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 70%, transparent);
  border-radius: 999px;
  padding: 0.08rem 0.45rem;
  white-space: nowrap;
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
  gap: 0.7rem;
  align-items: start;
}

.create-form label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.82rem;
  color: var(--mg-text-main);
  min-width: 0;
}

.create-form .input,
.create-form .textarea,
.create-form :deep(.searchable-dropdown) {
  width: 100%;
  min-width: 0;
}

.create-form :deep(.toggle-switch) {
  width: 100%;
}

.create-form .full {
  grid-column: 1 / -1;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.popup-actions .primary-btn,
.popup-actions .secondary-btn {
  flex: 0 1 auto;
  min-width: 0;
  white-space: nowrap;
  min-height: 2.3rem;
}

@media (max-width: 560px) {
  .popup-actions {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.4rem;
  }

  .popup-actions .primary-btn,
  .popup-actions .secondary-btn {
    width: 100%;
  }
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
  border: 1px solid var(--border, var(--mg-border-light));
  background: var(--bg-soft, var(--mg-bg-page));
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
  color: var(--module-600, var(--mg-primary));
  font-size: 0.84rem;
  font-weight: 700;
}

.product-card__meta {
  flex: 1;
  min-width: 0;
}

.product-card__title {
  margin: 0;
  color: var(--text, var(--mg-text-main));
  font-size: 0.96rem;
  font-weight: 800;
  line-height: 1.45;
}

.product-card__sub {
  margin: 0.18rem 0 0;
  font-size: 0.82rem;
  color: var(--muted, var(--mg-text-muted));
  line-height: 1.6;
}

.product-card__totals {
  display: flex;
  justify-content: space-between;
  gap: 0.45rem;
  padding: 0.65rem;
  border-radius: 8px;
  background: var(--bg-soft, var(--mg-bg-page));
  font-size: 0.84rem;
  color: var(--text, var(--mg-text-main));
}

.product-card__totals p {
  margin: 0;
}

.gallery-status {
  border-radius: 999px;
  padding: 0.16rem 0.5rem;
  font-size: 0.66rem;
  font-weight: 700;
  color: #fff;
  background: rgb(52 38 31 / 0.6);
  backdrop-filter: blur(3px);
}

.gallery-status.on {
  background: color-mix(in srgb, var(--mg-success) 85%, #000);
}

.gallery-status.off {
  background: rgb(146 64 14 / 0.85);
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
  background: var(--bg-soft, var(--mg-bg-page));
  color: var(--text, var(--mg-text-main));
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

.hidden-file-input {
  display: none;
}

.bulk-form {
  display: grid;
  gap: 0.9rem;
}

.bulk-form .hint {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.7;
}

.bulk-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.55rem;
}

.bulk-action-card {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
  background: transparent;
  cursor: pointer;
  display: grid;
  gap: 0.2rem;
  text-align: start;
  font: inherit;
  color: inherit;
}

.bulk-action-card.active {
  border-style: solid;
  border-color: var(--accent-green, #2f6f5c);
  background: rgba(47, 111, 92, 0.08);
}

.bulk-action-card small {
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1.5;
}

.bulk-result {
  border-top: 1px dashed var(--border-color, #d8d2c4);
  padding-top: 0.7rem;
}

.bulk-error-list {
  margin: 0.4rem 0 0;
  padding-inline-start: 1.1rem;
  color: #b84f4f;
  font-size: 0.78rem;
  display: grid;
  gap: 0.2rem;
}

.excel-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.55rem;
}

.excel-summary-grid > div {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  display: grid;
  gap: 0.2rem;
}

.excel-summary-grid small {
  color: var(--text-muted);
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
  background: var(--bg-soft, var(--mg-bg-page));
  color: var(--text, var(--mg-text-main));
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

.hidden-file-input {
  display: none;
}

.bulk-form {
  display: grid;
  gap: 0.9rem;
}

.bulk-form .hint {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.7;
}

.bulk-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.55rem;
}

.bulk-action-card {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
  background: transparent;
  cursor: pointer;
  display: grid;
  gap: 0.2rem;
  text-align: start;
  font: inherit;
  color: inherit;
}

.bulk-action-card.active {
  border-style: solid;
  border-color: var(--accent-green, #2f6f5c);
  background: rgba(47, 111, 92, 0.08);
}

.bulk-action-card small {
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1.5;
}

.bulk-result {
  border-top: 1px dashed var(--border-color, #d8d2c4);
  padding-top: 0.7rem;
}

.bulk-error-list {
  margin: 0.4rem 0 0;
  padding-inline-start: 1.1rem;
  color: #b84f4f;
  font-size: 0.78rem;
  display: grid;
  gap: 0.2rem;
}

.excel-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.55rem;
}

.excel-summary-grid > div {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  display: grid;
  gap: 0.2rem;
}

.excel-summary-grid small {
  color: var(--text-muted);
}

/* ─── دکمه ویرایش سریع روی کارت ─── */
.quick-edit-btn {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 16px rgb(52 38 31 / 0.16);
  transition: transform 0.15s ease, background 0.15s ease;
}

.quick-edit-btn:hover {
  transform: scale(1.08);
  background: color-mix(in srgb, var(--mg-primary) 12%, var(--mg-bg-surface) 88%);
}

/* ─── ساید پنل ویرایش سریع ─── */
.quick-edit-backdrop {
  position: fixed;
  inset: 0;
  z-index: 14000;
  background: rgb(10 12 10 / 0.4);
  display: flex;
  justify-content: flex-end;
}

.quick-edit-panel {
  width: min(400px, 100%);
  height: 100%;
  background: var(--bg-card, var(--mg-bg-surface));
  border-inline-start: 1px solid var(--mg-border);
  box-shadow: -18px 0 50px rgb(0 0 0 / 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.quick-edit-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: linear-gradient(135deg, var(--mg-primary), color-mix(in srgb, var(--mg-primary) 70%, var(--mg-text-main) 30%));
  color: #fff;
}

.quick-edit-kicker {
  font-size: 0.66rem;
  color: rgb(255 255 255 / 0.75);
  font-weight: 700;
}

.quick-edit-head h3 {
  margin: 0.1rem 0 0;
  font-size: 1rem;
  font-weight: 900;
}

.quick-edit-close {
  width: 30px;
  height: 30px;
  border: 1px solid rgb(255 255 255 / 0.3);
  border-radius: 10px;
  background: rgb(255 255 255 / 0.12);
  color: #fff;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}

.quick-edit-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.9rem 1rem;
  display: grid;
  gap: 0.75rem;
  align-content: start;
}

.quick-edit-name {
  margin: 0;
  font-size: 0.7rem;
  direction: ltr;
  text-align: right;
}

.qe-field {
  display: grid;
  gap: 0.3rem;
  font-size: 0.76rem;
  font-weight: 800;
  color: var(--mg-text-muted);
}

.qe-field .input {
  width: 100%;
}

.qe-textarea {
  resize: vertical;
  font-weight: 400;
}

.field-help {
  font-size: 0.7rem;
  font-weight: 400;
  color: var(--mg-text-muted);
  opacity: 0.9;
}

.quick-edit-success {
  margin: 0;
  font-size: 0.76rem;
  color: var(--mg-success, #6f7b56);
  font-weight: 700;
}

.quick-edit-foot {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--mg-border-light);
}

.quick-edit-fade-enter-active,
.quick-edit-fade-leave-active {
  transition: opacity 0.2s ease;
}

.quick-edit-fade-enter-from,
.quick-edit-fade-leave-to {
  opacity: 0;
}

.quick-edit-fade-enter-active .quick-edit-panel,
.quick-edit-fade-leave-active .quick-edit-panel {
  transition: transform 0.22s ease;
}

.quick-edit-fade-enter-from .quick-edit-panel,
.quick-edit-fade-leave-to .quick-edit-panel {
  transform: translateX(24px);
}
</style>
