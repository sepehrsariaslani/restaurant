<template>
  <ManagementPageScaffold :title="pageTitle" :subtitle="pageSubtitle">
    <template #actions>
      <a v-if="currentItemName" class="secondary-btn" :href="`/desk/product?item_name=${encodeURIComponent(currentItemName)}`">
        جزئیات کالا
      </a>
      <a class="secondary-btn" href="/app/item-attribute" target="_blank" rel="noreferrer">
        Item Attribute در ERP
      </a>
      <button class="secondary-btn" type="button" @click="loadVariantBuilder({ force: true })" :disabled="variantBuilderLoading || !currentItemName">
        {{ variantBuilderLoading ? 'در حال بارگذاری...' : 'بازخوانی' }}
      </button>
      <button class="secondary-btn" type="button" @click="saveVariantBuilder" :disabled="variantBuilderSaving || variantBuilderLoading || !currentItemName">
        {{ variantBuilderSaving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}
      </button>
      <button class="primary-btn" type="button" @click="generateVariantsFromBuilder" :disabled="variantBuilderGenerating || variantBuilderLoading || !currentItemName">
        {{ variantBuilderGenerating ? 'در حال ساخت...' : 'ساخت Variantها' }}
      </button>
    </template>

    <ManagementSurfaceCard title="انتخاب کالا یا تمپلیت" subtitle="نام یک Variant یا تمپلیت را وارد کنید">
      <div class="picker-row">
        <input class="input" v-model.trim="itemInput" placeholder="مثال: شیر-بدون لاکتوز-پرچرب یا شیر" />
        <button class="primary-btn" type="button" :disabled="!itemInput" @click="applyItemSelection">بارگذاری</button>
      </div>
      <p class="muted">
        تمپلیت فعال: {{ resolvedTemplateLabel || '-' }} ({{ resolvedTemplateName || '-' }})
      </p>
      <p v-if="isVariantContext" class="hint-line">
        این کالا Variant است و تنظیمات آن از تمپلیت {{ resolvedTemplateName }} مدیریت می‌شود.
      </p>
      <p v-if="currentVariantAttributesSummary !== '-'" class="muted">
        ویژگی‌های Variant فعلی: {{ currentVariantAttributesSummary }}
      </p>
      <div class="inline-actions">
        <a
          v-if="resolvedTemplateName"
          class="secondary-btn"
          :href="`/desk/product?item_name=${encodeURIComponent(resolvedTemplateName)}`"
        >
          جزئیات تمپلیت
        </a>
        <button
          v-if="resolvedTemplateName && currentItemName && resolvedTemplateName !== currentItemName"
          class="secondary-btn"
          type="button"
          @click="openBuilderForItem(resolvedTemplateName)"
        >
          مدیریت تمپلیت در این صفحه
        </button>
        <a class="secondary-btn" href="/app/item-attribute" target="_blank" rel="noreferrer">لیست کامل Item Attribute</a>
      </div>

      <p class="error" v-if="variantBuilderError">{{ variantBuilderError }}</p>
      <p class="success" v-if="variantBuilderSuccess">{{ variantBuilderSuccess }}</p>
      <p class="muted" v-if="variantBuilderLoading">در حال دریافت اطلاعات ویژگی‌ها...</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="لیست صفت‌های ERPNext" subtitle="تمام Item Attributeها را ببینید و برای ویرایش انتخاب کنید">
      <div class="picker-row">
        <input
          class="input"
          v-model.trim="attributeCatalogSearch"
          placeholder="جستجو صفت... مثال: سایز"
          @keyup.enter="loadItemAttributeCatalog({ force: true })"
        />
        <button class="secondary-btn" type="button" :disabled="attributeCatalogLoading" @click="loadItemAttributeCatalog({ force: true })">
          {{ attributeCatalogLoading ? 'در حال بارگذاری...' : 'جستجو / بازخوانی' }}
        </button>
      </div>

      <div class="variant-editor-table-wrap desktop-only-table" v-if="itemAttributeCatalog.length">
        <table class="variant-editor-table">
          <thead>
            <tr>
              <th>عملیات</th>
              <th>صفت</th>
              <th>نوع</th>
              <th>تعداد مقدار</th>
              <th>وضعیت</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in itemAttributeCatalog"
              :key="`catalog-${row.name}`"
              :class="{ active: selectedItemAttributeName === row.name }"
            >
              <td>
                <button class="secondary-btn mini-link-btn" type="button" @click="openItemAttributeEditor(row.name)">
                  ویرایش
                </button>
              </td>
              <td>
                <div class="variant-attr-meta">
                  <strong>{{ row.label || row.name }}</strong>
                  <small>{{ row.name }}</small>
                </div>
              </td>
              <td>{{ Number(row.numeric_values || 0) === 1 ? 'عددی' : 'لیستی' }}</td>
              <td>{{ Number(row.value_count || 0).toLocaleString('fa-IR') }}</td>
              <td>
                <span :class="['state-pill', Number(row.disabled || 0) ? 'off' : 'on']">
                  {{ Number(row.disabled || 0) ? 'غیرفعال' : 'فعال' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="variant-mobile-list" v-if="itemAttributeCatalog.length">
        <article
          v-for="row in itemAttributeCatalog"
          :key="`catalog-mobile-${row.name}`"
          class="variant-mobile-card"
        >
          <header>
            <strong>{{ row.label || row.name }}</strong>
            <span :class="['state-pill', Number(row.disabled || 0) ? 'off' : 'on']">
              {{ Number(row.disabled || 0) ? 'غیرفعال' : 'فعال' }}
            </span>
          </header>
          <p class="muted">کد: {{ row.name }}</p>
          <p class="muted">نوع: {{ Number(row.numeric_values || 0) === 1 ? 'عددی' : 'لیستی' }}</p>
          <p class="muted">تعداد مقدار: {{ Number(row.value_count || 0).toLocaleString('fa-IR') }}</p>
          <div class="inline-actions">
            <button class="secondary-btn mini-link-btn" type="button" @click="openItemAttributeEditor(row.name)">
              ویرایش
            </button>
            <a class="secondary-btn mini-link-btn" :href="itemAttributeDocUrl(row.name)" target="_blank" rel="noreferrer">
              ERP
            </a>
          </div>
        </article>
      </div>

      <p class="error" v-if="itemAttributeCatalogError">{{ itemAttributeCatalogError }}</p>
      <p class="muted" v-if="!itemAttributeCatalogLoading && !itemAttributeCatalog.length">صفتی پیدا نشد.</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="ویرایش صفت انتخاب‌شده" subtitle="تنظیمات ERPNext برای Item Attribute">
      <template v-if="itemAttributeEditor">
        <div class="attribute-editor-grid">
          <label>
            نام صفت
            <input class="input" :value="itemAttributeEditor.name" readonly />
          </label>
          <label>
            عنوان صفت
            <input class="input" :value="itemAttributeEditor.label" readonly />
          </label>
          <label class="check">
            <input type="checkbox" v-model="itemAttributeEditor.numeric_values" />
            مقادیر عددی
          </label>
          <label class="check">
            <input type="checkbox" v-model="itemAttributeEditor.disabled" />
            غیرفعال
          </label>
          <label class="check">
            <input type="checkbox" v-model="itemAttributeEditor.show_in_website" />
            نمایش در سایت
          </label>
          <label class="check">
            <input type="checkbox" v-model="itemAttributeEditor.selection_only" />
            انتخابی مشتری
          </label>
        </div>

        <div class="attribute-range-grid" v-if="itemAttributeEditor.numeric_values">
          <label>
            From Range
            <NumericInput v-model="itemAttributeEditor.from_range" :separator="false" />
          </label>
          <label>
            To Range
            <NumericInput v-model="itemAttributeEditor.to_range" :separator="false" />
          </label>
          <label>
            Increment
            <NumericInput v-model="itemAttributeEditor.increment" :separator="false" />
          </label>
        </div>

        <template v-else>
          <div class="inline-actions">
            <button class="secondary-btn mini-link-btn" type="button" @click="appendItemAttributeValueRow">
              افزودن مقدار
            </button>
          </div>

          <div class="variant-editor-table-wrap desktop-only-table">
            <table class="variant-values-table">
              <thead>
                <tr>
                  <th>مقدار</th>
                  <th>abbr</th>
                  <th>پیش‌فرض</th>
                  <th>حذف</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(valueRow, valueIndex) in itemAttributeEditor.values"
                  :key="`attribute-editor-value-${valueIndex}`"
                >
                  <td>
                    <input
                      class="input"
                      :value="valueRow.value"
                      @input="valueRow.value = String($event.target.value || '').trim()"
                      placeholder="مقدار"
                    />
                  </td>
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
                      name="item-attribute-default"
                      :checked="Number(valueRow.is_default || 0) === 1"
                      @change="setItemAttributeDefaultValue(valueIndex)"
                    />
                  </td>
                  <td>
                    <button class="secondary-btn mini-link-btn" type="button" @click="removeItemAttributeValueRow(valueIndex)">
                      حذف
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <div class="inline-actions">
          <button
            class="primary-btn"
            type="button"
            :disabled="itemAttributeEditorSaving || itemAttributeEditorLoading"
            @click="saveItemAttributeEditor"
          >
            {{ itemAttributeEditorSaving ? 'در حال ذخیره...' : 'ذخیره صفت' }}
          </button>
          <a class="secondary-btn mini-link-btn" :href="itemAttributeDocUrl(itemAttributeEditor.name)" target="_blank" rel="noreferrer">
            مشاهده در ERP
          </a>
        </div>
      </template>
      <p v-else class="muted">از لیست بالا یک صفت را انتخاب کنید.</p>

      <p class="error" v-if="itemAttributeEditorError">{{ itemAttributeEditorError }}</p>
      <p class="success" v-if="itemAttributeEditorSuccess">{{ itemAttributeEditorSuccess }}</p>
      <p class="muted" v-if="itemAttributeEditorLoading">در حال دریافت جزئیات صفت...</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="جدول ویژگی‌های تمپلیت" subtitle="ویرایش ویژگی‌ها و مقادیر قابل تولید">
      <template v-if="!variantBuilderLoading && variantAttributesDraft.length">
        <div class="variant-config-head">
          <strong>ویژگی‌های فعال روی قالب</strong>
          <small class="muted">{{ selectedTemplateAttributeCount.toLocaleString('fa-IR') }}</small>
          <button v-if="inactiveTemplateAttributes.length > 0" class="secondary-btn mini-link-btn" type="button" @click="showAddAttributeDialog = true">
            افزودن ویژگی
          </button>
        </div>

        <div class="variant-editor-table-wrap desktop-only-table">
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
                :class="{ active: activeVariantAttributeName === row.name }"
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
                    @change="updateAttributeToggle(row.name, 'show_in_website', $event.target.checked)"
                  />
                </td>
                <td>
                  <input
                    type="checkbox"
                    :checked="Number(row.selection_only || 0) === 1"
                    @change="updateAttributeToggle(row.name, 'selection_only', $event.target.checked)"
                  />
                </td>
                <td>
                  {{ countSelectedValues(row.name).toLocaleString('fa-IR') }} / {{ (row.values || []).length.toLocaleString('fa-IR') }}
                </td>
                <td>
                  <div class="inline-actions inline-actions--tight">
                    <button class="secondary-btn mini-link-btn" type="button" @click="openAttributeEditor(row.name)">ویرایش</button>
                    <button class="secondary-btn mini-link-btn delete-mini-btn" type="button" @click="removeAttributeFromTemplate(row.name)">حذف</button>
                    <a class="secondary-btn mini-link-btn" :href="itemAttributeDocUrl(row.name)" target="_blank" rel="noreferrer">ERP</a>
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
                  @change="updateAttributeToggle(row.name, 'show_in_website', $event.target.checked)"
                />
                نمایش در سایت
              </label>
              <label class="check">
                <input
                  type="checkbox"
                  :checked="Number(row.selection_only || 0) === 1"
                  @change="updateAttributeToggle(row.name, 'selection_only', $event.target.checked)"
                />
                انتخابی مشتری
              </label>
            </div>
            <footer>
              <span>
                مقادیر فعال: {{ countSelectedValues(row.name).toLocaleString('fa-IR') }} / {{ (row.values || []).length.toLocaleString('fa-IR') }}
              </span>
              <div class="inline-actions inline-actions--tight">
                <button class="secondary-btn mini-link-btn" type="button" @click="openAttributeEditor(row.name)">ویرایش مقادیر</button>
                <button class="secondary-btn mini-link-btn delete-mini-btn" type="button" @click="removeAttributeFromTemplate(row.name)">حذف</button>
                <a class="secondary-btn mini-link-btn" :href="itemAttributeDocUrl(row.name)" target="_blank" rel="noreferrer">ERP</a>
              </div>
            </footer>
          </article>
        </div>

        <div class="variant-values-shell" v-if="activeVariantAttributeRow">
          <header class="variant-values-head">
            <strong>مقادیر ویژگی: {{ activeVariantAttributeRow.label }}</strong>
            <div class="variant-values-head-meta">
              <small class="muted">{{ activeVariantAttributeRow.name }}</small>
              <a class="secondary-btn mini-link-btn" :href="activeAttributeDocUrl" target="_blank" rel="noreferrer">مشاهده در ERP</a>
            </div>
          </header>

          <template v-if="selectedTemplateAttributes.includes(activeVariantAttributeRow.name)">
            <div class="variant-editor-table-wrap desktop-only-table">
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
                  <tr
                    v-for="valueRow in activeVariantAttributeRow.values"
                    :key="`value-${activeVariantAttributeRow.name}-${valueRow.value}`"
                  >
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
            <div class="variant-values-mobile-list">
              <article
                v-for="valueRow in activeVariantAttributeRow.values"
                :key="`mobile-value-${activeVariantAttributeRow.name}-${valueRow.value}`"
                class="variant-value-mobile-card"
              >
                <header>
                  <strong>{{ valueRow.value }}</strong>
                  <label class="check">
                    <input
                      type="checkbox"
                      :checked="activeAttributeSelectedValues.includes(valueRow.value)"
                      @change="toggleGeneratedValue(activeVariantAttributeRow.name, valueRow.value)"
                    />
                    تولید Variant
                  </label>
                </header>
                <div class="mobile-value-fields">
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
                      :name="`mobile-default-${activeVariantAttributeRow.name}`"
                      :checked="Number(valueRow.is_default || 0) === 1"
                      @change="updateAttributeDefault(activeVariantAttributeRow.name, valueRow.value)"
                    />
                    پیش فرض
                  </label>
                </div>
              </article>
            </div>
          </template>
        </div>
      </template>
      <p v-else-if="!variantBuilderLoading" class="muted">ویژگی فعالی برای این تمپلیت ثبت نشده است.</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="Variantهای ساخته‌شده" subtitle="کالاهایی که از این تمپلیت تولید شده‌اند">
      <ManagementDataTable
        v-if="variantRows.length"
        :columns="variantColumns"
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
          <div class="inline-actions">
            <button class="secondary-btn mini-link-btn" type="button" @click="openBuilderForItem(row.name)">مدیریت</button>
            <a class="secondary-btn mini-link-btn" :href="`/desk/product?item_name=${encodeURIComponent(row.name)}`">جزئیات</a>
          </div>
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
          <div class="inline-actions">
            <button class="secondary-btn mini-link-btn" type="button" @click="openBuilderForItem(row.name)">مدیریت</button>
            <a class="secondary-btn mini-link-btn" :href="`/desk/product?item_name=${encodeURIComponent(row.name)}`">جزئیات</a>
          </div>
        </article>
      </div>
      <p v-else class="muted">هنوز وریانتی برای این تمپلیت ثبت نشده است.</p>
    </ManagementSurfaceCard>
  </ManagementPageScaffold>

  <ManagementPopup
    v-model:open="showAddAttributeDialog"
    title="افزودن ویژگی به قالب"
    subtitle="ویژگی جدید را از لیست صفت‌های ERPNext انتخاب کنید"
  >
    <div class="add-attribute-form">
      <p class="muted">ویژگی‌های زیر هنوز روی قالب فعال نشده‌اند:</p>
      <label>
        انتخاب ویژگی
        <SearchableDropdown
          v-model="selectedNewAttribute"
          :options="inactiveTemplateAttributes.map((row) => ({ value: row.name, label: row.label }))"
          placeholder="انتخاب ویژگی"
          search-placeholder="جستجوی ویژگی..."
        />
        <small class="hint">با این کار ویژگی به جدول قالب اضافه می‌شود.</small>
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
import { computed, ref, watch } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import NumericInput from '@/components/NumericInput.vue'
import {
  generateManagementProductVariants,
  getManagementItemAttribute,
  getManagementProductVariantBuilder,
  listManagementItemAttributes,
  saveManagementItemAttribute,
  saveManagementProductVariantBuilder,
} from '@/utils/api'
import { parseQuery } from '@/utils/format'

const query = parseQuery()
const currentItemName = ref(String(query.item_name || query.item || '').trim())
const itemInput = ref(currentItemName.value)

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
const itemAttributeCatalogSearch = ref('')
const itemAttributeCatalogLoading = ref(false)
const itemAttributeCatalogError = ref('')
const itemAttributeCatalog = ref([])
const selectedItemAttributeName = ref('')
const itemAttributeEditorLoading = ref(false)
const itemAttributeEditorSaving = ref(false)
const itemAttributeEditorError = ref('')
const itemAttributeEditorSuccess = ref('')
const itemAttributeEditor = ref(null)
const showAddAttributeDialog = ref(false)
const selectedNewAttribute = ref('')

const variantColumns = [
  { key: 'item_code', label: 'کد' },
  { key: 'item_name', label: 'نام' },
  { key: 'attributes', label: 'ویژگی‌ها' },
  { key: 'slug', label: 'اسلاگ' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]

const pageTitle = computed(() => 'استودیو Variant و Item Attribute')
const pageSubtitle = computed(() =>
  currentItemName.value || 'بدون انتخاب کالا هم می‌توانید صفت‌های ERPNext را ویرایش کنید',
)
const variantTemplate = computed(() => variantBuilder.value?.template || {})
const variantRows = computed(() => (Array.isArray(variantBuilder.value?.variants) ? variantBuilder.value.variants : []))
const resolvedTemplateName = computed(() => {
  const fromBuilder = String(variantTemplate.value?.name || '').trim()
  if (fromBuilder) {
    return fromBuilder
  }
  return String(currentItemName.value || '').trim()
})
const resolvedTemplateLabel = computed(() => {
  const fromBuilder = String(variantTemplate.value?.item_name || '').trim()
  if (fromBuilder) {
    return fromBuilder
  }
  return String(currentItemName.value || '').trim()
})
const isVariantContext = computed(() => {
  const currentItem = String(currentItemName.value || '').trim()
  const templateItem = String(resolvedTemplateName.value || '').trim()
  return Boolean(currentItem && templateItem && currentItem !== templateItem)
})
const selectedTemplateAttributeCount = computed(() => selectedTemplateAttributes.value.length)
const activeTemplateAttributes = computed(() => {
  return variantAttributesDraft.value.filter((row) => selectedTemplateAttributes.value.includes(row.name))
})
const inactiveTemplateAttributes = computed(() => {
  return variantAttributesDraft.value.filter((row) => !selectedTemplateAttributes.value.includes(row.name))
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
const currentVariantAttributesSummary = computed(() => {
  const currentName = String(currentItemName.value || '').trim()
  if (!currentName) {
    return '-'
  }
  const currentRow = variantRows.value.find((row) => String(row?.name || '').trim() === currentName)
  if (!currentRow) {
    return '-'
  }
  return formatVariantAttributes(currentRow)
})
const activeAttributeDocUrl = computed(() => itemAttributeDocUrl(activeVariantAttributeName.value))

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

function normalizeItemAttributeEditorPayload(payload = {}) {
  const values = Array.isArray(payload?.values)
    ? payload.values.map((row) => ({
        value: String(row?.value || '').trim(),
        abbr: String(row?.abbr || '').trim(),
        is_default: Number(row?.is_default || 0) ? 1 : 0,
      }))
    : []
  return {
    name: String(payload?.name || '').trim(),
    label: String(payload?.label || payload?.name || '').trim(),
    numeric_values: Number(payload?.numeric_values || 0) ? 1 : 0,
    disabled: Number(payload?.disabled || 0) ? 1 : 0,
    show_in_website: Number(payload?.show_in_website || 0) ? 1 : 0,
    selection_only: Number(payload?.selection_only || 0) ? 1 : 0,
    from_range: Number(payload?.from_range || 0) || 0,
    to_range: Number(payload?.to_range || 0) || 0,
    increment: Number(payload?.increment || 0) || 0,
    values,
  }
}

async function loadItemAttributeCatalog({ force = false } = {}) {
  if (!force && itemAttributeCatalogLoading.value) {
    return
  }
  itemAttributeCatalogLoading.value = true
  itemAttributeCatalogError.value = ''
  try {
    const payload = await listManagementItemAttributes({
      search: itemAttributeCatalogSearch.value,
      include_values: 0,
    })
    const rows = Array.isArray(payload?.rows) ? payload.rows : []
    itemAttributeCatalog.value = rows
    const selectedName = String(selectedItemAttributeName.value || '').trim()
    if (selectedName && !rows.some((row) => String(row?.name || '').trim() === selectedName)) {
      selectedItemAttributeName.value = ''
      itemAttributeEditor.value = null
    }
  } catch (catalogErr) {
    itemAttributeCatalog.value = []
    itemAttributeCatalogError.value = catalogErr.message || 'دریافت لیست صفت‌ها ناموفق بود.'
  } finally {
    itemAttributeCatalogLoading.value = false
  }
}

async function openItemAttributeEditor(attributeName = '') {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return
  }
  selectedItemAttributeName.value = normalized
  itemAttributeEditorLoading.value = true
  itemAttributeEditorError.value = ''
  itemAttributeEditorSuccess.value = ''
  try {
    const payload = await getManagementItemAttribute({ attribute_name: normalized })
    itemAttributeEditor.value = normalizeItemAttributeEditorPayload(payload)
  } catch (attributeErr) {
    itemAttributeEditor.value = null
    itemAttributeEditorError.value = attributeErr.message || 'دریافت جزئیات صفت ناموفق بود.'
  } finally {
    itemAttributeEditorLoading.value = false
  }
}

function appendItemAttributeValueRow() {
  if (!itemAttributeEditor.value) {
    return
  }
  itemAttributeEditor.value.values = [
    ...(itemAttributeEditor.value.values || []),
    { value: '', abbr: '', is_default: 0 },
  ]
}

function removeItemAttributeValueRow(index) {
  if (!itemAttributeEditor.value) {
    return
  }
  const nextRows = [...(itemAttributeEditor.value.values || [])]
  nextRows.splice(index, 1)
  itemAttributeEditor.value.values = nextRows
}

function setItemAttributeDefaultValue(index) {
  if (!itemAttributeEditor.value) {
    return
  }
  itemAttributeEditor.value.values = (itemAttributeEditor.value.values || []).map((row, rowIndex) => ({
    ...row,
    is_default: rowIndex === index ? 1 : 0,
  }))
}

async function saveItemAttributeEditor() {
  if (!itemAttributeEditor.value?.name) {
    return
  }
  itemAttributeEditorSaving.value = true
  itemAttributeEditorError.value = ''
  itemAttributeEditorSuccess.value = ''

  const payload = {
    name: String(itemAttributeEditor.value.name || '').trim(),
    numeric_values: Number(itemAttributeEditor.value.numeric_values || 0) ? 1 : 0,
    disabled: Number(itemAttributeEditor.value.disabled || 0) ? 1 : 0,
    show_in_website: Number(itemAttributeEditor.value.show_in_website || 0) ? 1 : 0,
    selection_only: Number(itemAttributeEditor.value.selection_only || 0) ? 1 : 0,
    from_range: Number(itemAttributeEditor.value.from_range || 0) || 0,
    to_range: Number(itemAttributeEditor.value.to_range || 0) || 0,
    increment: Number(itemAttributeEditor.value.increment || 0) || 0,
    values: Array.isArray(itemAttributeEditor.value.values)
      ? itemAttributeEditor.value.values.map((row) => ({
          value: String(row?.value || '').trim(),
          abbr: String(row?.abbr || '').trim(),
          is_default: Number(row?.is_default || 0) ? 1 : 0,
        }))
      : [],
  }

  try {
    const response = await saveManagementItemAttribute(payload)
    itemAttributeEditor.value = normalizeItemAttributeEditorPayload(response)
    itemAttributeEditorSuccess.value = 'صفت با موفقیت ذخیره شد.'
    await loadItemAttributeCatalog({ force: true })
    if (currentItemName.value) {
      await loadVariantBuilder({ force: true })
    }
  } catch (saveErr) {
    itemAttributeEditorError.value = saveErr.message || 'ذخیره صفت ناموفق بود.'
  } finally {
    itemAttributeEditorSaving.value = false
  }
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

function updateURL(itemName = '') {
  if (typeof window === 'undefined') {
    return
  }
  const normalized = String(itemName || '').trim()
  const base = '/desk/product'
  const nextUrl = normalized
    ? `${base}?item_name=${encodeURIComponent(normalized)}&variant_studio=1`
    : `${base}?variant_studio=1`
  window.history.replaceState({}, '', nextUrl)
}

async function loadVariantBuilder({ force = false } = {}) {
  const targetItem = String(currentItemName.value || '').trim()
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

function applyItemSelection() {
  const normalized = String(itemInput.value || '').trim()
  if (!normalized) {
    return
  }
  currentItemName.value = normalized
  variantBuilderLoadedKey.value = ''
  variantBuilderSuccess.value = ''
  variantBuilderError.value = ''
  updateURL(normalized)
  loadVariantBuilder({ force: true })
}

function openBuilderForItem(itemName) {
  const normalized = String(itemName || '').trim()
  if (!normalized) {
    return
  }
  itemInput.value = normalized
  currentItemName.value = normalized
  variantBuilderLoadedKey.value = ''
  variantBuilderSuccess.value = ''
  variantBuilderError.value = ''
  updateURL(normalized)
  loadVariantBuilder({ force: true })
}

function openAttributeEditor(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return
  }
  activeVariantAttributeName.value = normalized
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

function removeAttributeFromTemplate(attributeName) {
  const normalized = String(attributeName || '').trim()
  if (!normalized) {
    return
  }
  const attrLabel = variantAttributesDraft.value.find((row) => row.name === normalized)?.label || normalized
  const confirmed = window.confirm(`آیا مطمئن هستید که می‌خواهید ویژگی «${attrLabel}» را از این قالب حذف کنید؟`)
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
    const attrRow = variantAttributesDraft.value.find((row) => row.name === normalized)
    if (attrRow) {
      selectedValuesByAttribute.value = {
        ...selectedValuesByAttribute.value,
        [normalized]: (attrRow.values || []).map((row) => row.value).filter(Boolean),
      }
      activeVariantAttributeName.value = normalized
    }
  }

  showAddAttributeDialog.value = false
  selectedNewAttribute.value = ''
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
    item_name: String(currentItemName.value || '').trim(),
    selected_attributes: Array.from(selectedSet),
    attribute_settings: attributeSettings,
  }
}

async function saveVariantBuilder() {
  if (!currentItemName.value) {
    return
  }
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
  if (!currentItemName.value) {
    return
  }
  variantBuilderGenerating.value = true
  variantBuilderError.value = ''
  variantBuilderSuccess.value = ''
  try {
    const payload = await generateManagementProductVariants({
      item_name: String(currentItemName.value || '').trim(),
      selected_attributes: selectedTemplateAttributes.value,
      selected_values_by_attribute: selectedValuesByAttribute.value,
    })
    if (payload?.builder) {
      resetVariantBuilderState(payload.builder)
    }
    const createdCount = Number(payload?.created_count || 0)
    const existingCount = Number(payload?.existing_count || 0)
    variantBuilderSuccess.value = `ایجاد شد: ${createdCount.toLocaleString('fa-IR')} | موجود بود: ${existingCount.toLocaleString('fa-IR')}`
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

loadItemAttributeCatalog({ force: true })
if (currentItemName.value) {
  loadVariantBuilder({ force: true })
}
</script>

<style scoped>
.picker-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.45rem;
  margin-bottom: 0.5rem;
}

.inline-actions {
  margin: 0.25rem 0 0.45rem;
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.inline-actions--tight {
  margin: 0;
}

.variant-config-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  margin-bottom: 0.45rem;
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
  margin-top: 0.55rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 12px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.5rem;
}

.attribute-editor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.55rem;
}

.attribute-editor-grid label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.74rem;
  color: var(--text-muted);
}

.attribute-editor-grid .check {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 10px;
  padding: 0.45rem 0.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--text-primary);
}

.attribute-range-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.attribute-range-grid label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.74rem;
  color: var(--text-muted);
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

.variant-mobile-list {
  display: none;
}

.variant-attribute-mobile-list,
.variant-values-mobile-list {
  display: none;
}

.variant-mobile-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 12px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.4rem;
}

.variant-mobile-card header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.35rem;
}

.variant-attribute-mobile-card,
.variant-value-mobile-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 12px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.45rem;
}

.variant-attribute-mobile-card.active {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.35);
  box-shadow: 0 10px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.variant-attribute-mobile-card header,
.variant-value-mobile-card header,
.variant-attribute-mobile-card footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.variant-attribute-mobile-card header small {
  color: var(--text-muted);
  font-size: 0.73rem;
}

.checks-grid {
  display: grid;
  gap: 0.35rem;
}

.compact-checks .check {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.76rem;
}

.mobile-value-fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: end;
}

.mobile-value-fields label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.add-attribute-form {
  display: grid;
  gap: 0.55rem;
}

.add-attribute-form label {
  display: grid;
  gap: 0.25rem;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.delete-mini-btn {
  color: var(--danger);
  border-color: rgb(var(--danger-rgb) / 0.32);
}

.hint-line {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
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
  .picker-row {
    grid-template-columns: 1fr;
  }

  .variant-config-head,
  .variant-values-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .attribute-editor-grid,
  .attribute-range-grid {
    grid-template-columns: 1fr;
  }

  .desktop-only-table {
    display: none;
  }

  .variant-attribute-mobile-list,
  .variant-values-mobile-list,
  .variant-mobile-list {
    display: grid;
    gap: 0.5rem;
  }

  .variant-values-head-meta {
    width: 100%;
    justify-content: space-between;
  }

  .mobile-value-fields {
    grid-template-columns: 1fr;
  }
}
</style>
