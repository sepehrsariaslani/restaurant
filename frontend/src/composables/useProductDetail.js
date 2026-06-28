import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  callMethodByPathGET,
  createManagementBom,
  deleteManagementItemImageByUrl,
  generateManagementProductVariants,
  getManagementBomContext,
  getManagementBomDoc,
  getManagementProductVariantBuilder,
  getManagementProductDetail,
  listManagementBomItems,
  listManagementBoms,
  listRestaurantItemTags,
  saveManagementProductVariantBuilder,
  setManagementDefaultPriceList,
  setManagementProductPrice,
  updateManagementBom,
  uploadManagementItemImage,
  updateManagementProductSettings,
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
  localizeAxisLabel,
  localizeText,
  normalizeVariantAttributesDraft,
  resolveTemplateAttributeSelection,
  serializeProductSettingsState,
} from '@/utils/managementProductDetail'

/**
 * Injection key for the product-detail context produced by useProductDetail().
 * The page component provides the full context once; every tab/dialog component
 * injects exactly what it needs from the same reactive state.
 */
export const PRODUCT_DETAIL_CONTEXT = Symbol('product-detail-context')

const TAG_FIELD = 'restaurant_item_tag_table'
const PREVIEW_COMPACT_QUERY = '(max-width: 980px)'

/**
 * Owns the entire ManagementProductDetailPage logic in a single scope so that
 * cross-domain references (detail ⇄ pricing ⇄ bom ⇄ variants ⇄ builder ⇄ media)
 * stay intact. Behaviour is identical to the original single-file component –
 * this is purely a structural extraction.
 */
export function useProductDetail(boot = {}) {
  const query = parseQuery()
  const itemName = ref(String(query.item_name || query.item || boot?.item_name || '').trim())

  const today = new Date()
  const start = new Date(today)
  start.setDate(today.getDate() - 29)

  const filters = reactive({
    date_from: start.toISOString().slice(0, 10),
    date_to: today.toISOString().slice(0, 10),
  })

  // ─── Core state ──────────────────────────────────────────────────────
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

  const settingsForm = reactive(createInitialProductSettingsForm())

  const priceForm = reactive({
    price_list: '',
    price_list_rate: 0,
    valid_from: '',
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
  })

  const tabOptions = PRODUCT_DETAIL_TABS

  const bomColumns = [
    { key: 'name', label: 'BOM' },
    { key: 'quantity', label: 'تعداد' },
    { key: 'status', label: 'وضعیت' },
    { key: 'modified', label: 'آخرین بروزرسانی' },
    { key: 'actions', label: 'عملیات' },
  ]

  const allTagOptions = ref([])

  // ─── Page-level computed ─────────────────────────────────────────────
  const pageTitle = computed(() => detail.value?.item?.item_name || 'جزئیات محصول')
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
      tone: settingsForm.restaurant_enabled ? 'success' : 'danger',
    },
    {
      key: 'price',
      label: 'قیمت فعلی',
      value: formatMoney(currentPriceRate.value, activeCurrency.value),
      tone: currentPriceRate.value > 0 ? 'success' : 'warn',
    },
    {
      key: 'bom',
      label: 'BOM',
      value: defaultBomName.value || activeBomName.value ? 'متصل' : 'ندارد',
      tone: defaultBomName.value || activeBomName.value ? 'info' : settingsForm.restaurant_requires_bom ? 'warn' : 'neutral',
    },
    {
      key: 'builder',
      label: 'سفارشی‌سازی',
      value: settingsForm.restaurant_is_customizable || hasBuilderConfig.value ? 'فعال' : 'خاموش',
      tone: settingsForm.restaurant_is_customizable || hasBuilderConfig.value ? 'info' : 'neutral',
    },
    {
      key: 'slug',
      label: 'اسلاگ',
      value: settingsForm.restaurant_slug ? settingsForm.restaurant_slug : 'تنظیم نشده',
      tone: settingsForm.restaurant_slug ? 'success' : 'warn',
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
  const canSaveSettings = computed(() => !savingSettings.value && !loading.value && hasUnsavedChanges.value && !!detail.value?.item?.name)
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

  // ─── BOM helpers ─────────────────────────────────────────────────────
  function createEmptyBomItemRow() {
    return {
      item_code: '',
      qty: 1,
      uom: '',
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
      item_code: String(row?.item_code || '').trim(),
      qty: Number(row?.qty || 0) || 1,
      uom: String(row?.uom || row?.stock_uom || '').trim(),
    })).filter((row) => row.item_code)
    if (!bomForm.items.length) {
      bomForm.items = [createEmptyBomItemRow()]
    }
  }

  // ─── Variant computed ────────────────────────────────────────────────
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
  const productReadinessChecks = computed(() => [
    {
      key: 'image',
      label: 'تصویر اصلی',
      detail: mainImage.value ? 'تصویر محصول آماده نمایش است.' : 'برای کارت منو تصویر اضافه کنید.',
      ok: Boolean(mainImage.value),
    },
    {
      key: 'slug',
      label: 'اسلاگ محصول',
      detail: settingsForm.restaurant_slug ? settingsForm.restaurant_slug : 'برای لینک صفحه مشتری اسلاگ لازم است.',
      ok: Boolean(String(settingsForm.restaurant_slug || '').trim()),
    },
    {
      key: 'description',
      label: 'توضیح کوتاه',
      detail: settingsForm.restaurant_short_desc ? 'متن کارت محصول تکمیل است.' : 'کارت منو بدون توضیح کوتاه ضعیف‌تر دیده می‌شود.',
      ok: Boolean(String(settingsForm.restaurant_short_desc || '').trim()),
    },
    {
      key: 'price',
      label: 'قیمت معتبر',
      detail: Number(priceForm.price_list_rate || currentPriceRate.value || 0) > 0 ? formatMoney(Number(priceForm.price_list_rate || currentPriceRate.value || 0), activeCurrency.value) : 'قیمت محصول صفر یا نامشخص است.',
      ok: Number(priceForm.price_list_rate || currentPriceRate.value || 0) > 0,
    },
    {
      key: 'category',
      label: 'دسته‌بندی',
      detail: selectedCategoryLabel.value || 'برای پیدا شدن راحت‌تر محصول، دسته انتخاب کنید.',
      ok: Boolean(selectedCategoryLabel.value),
    },
  ])
  const readinessScore = computed(() => productReadinessChecks.value.filter((check) => check.ok).length)

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
      coming_soon: settingsForm.restaurant_coming_soon ? 1 : 0,
      restaurant_coming_soon: settingsForm.restaurant_coming_soon ? 1 : 0,
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
    const queryString = params.toString()
    return `/item/${encodeURIComponent(slug)}${queryString ? `?${queryString}` : ''}`
  })

  function openPreviewCard(row) {
    previewModalItem.value = row ? { ...row } : null
    previewModalOpen.value = Boolean(previewModalItem.value)
  }

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

  // ─── Watchers ────────────────────────────────────────────────────────
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

  function cloneBuilderConfig(config = null) {
    return clonePlainObject(config)
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
  const tagList = computed({
    get() {
      const links = settingsForm[TAG_FIELD] || []
      return links.map(l => {
        return l._tag_title || l.tag_title || l.tag || ''
      }).filter(Boolean)
    },
    set(val) {
      const current = settingsForm[TAG_FIELD] || []
      const newTags = Array.isArray(val) ? val : []

      const toRemove = current.filter(l => {
        const title = l._tag_title || l.tag_title || l.tag || ''
        return !newTags.includes(title)
      })
      for (const r of toRemove) {
        const idx = current.indexOf(r)
        if (idx >= 0) current.splice(idx, 1)
      }

      for (const t of newTags) {
        const exists = current.some(l => (l._tag_title || l.tag_title || l.tag || '') === t)
        if (!exists) {
          const opt = allTagOptions.value.find(o => o.label === t)
          current.push({
            tag: opt ? opt.value : t,
            _tag_title: t,
          })
        }
      }
      settingsForm[TAG_FIELD] = [...current]
    },
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

  // ─── Data loading ────────────────────────────────────────────────────
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

  async function searchBomItems(searchQuery = '') {
    try {
      const rows = await listManagementBomItems({ search: searchQuery, limit: 100 })
      bomItemOptions.value = (Array.isArray(rows) ? rows : []).map((row) => {
        const value = String(row?.item_code || row?.name || '').trim()
        const title = String(row?.item_name || row?.name || value).trim()
        return {
          value,
          label: value && title !== value ? `${title} (${value})` : title,
          stock_uom: String(row?.stock_uom || '').trim(),
        }
      }).filter((row) => row.value)
    } catch {
      bomItemOptions.value = []
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

  function removeBomItemRow(index) {
    bomForm.items.splice(index, 1)
    if (!bomForm.items.length) {
      bomForm.items.push(createEmptyBomItemRow())
    }
  }

  function updateBomItemCode(index, itemCode) {
    const normalized = String(itemCode || '').trim()
    const option = bomItemOptions.value.find((row) => String(row?.value || row?.item_code || '').trim() === normalized)
    const nextRow = bomForm.items[index]
    if (!nextRow) {
      return
    }
    nextRow.item_code = normalized
    if (option?.stock_uom && !nextRow.uom) {
      nextRow.uom = String(option.stock_uom || '').trim()
    }
  }

  async function saveBomFromProduct() {
    const normalizedItem = String(detail.value?.item?.name || detail.value?.item?.item_code || '').trim()
    if (!normalizedItem) {
      bomError.value = 'محصول معتبری برای ثبت BOM پیدا نشد.'
      return
    }

    const normalizedItems = (Array.isArray(bomForm.items) ? bomForm.items : [])
      .map((row) => ({
        item_code: String(row?.item_code || '').trim(),
        qty: Number(row?.qty || 0),
        uom: String(row?.uom || '').trim(),
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
        valid_from: priceForm.valid_from || '',
      })
      await loadDetail()
    } catch (errObj) {
      error.value = errObj.message || 'ثبت قیمت محصول ناموفق بود.'
    } finally {
      savingPrice.value = false
    }
  }

  // ─── Variant editing ─────────────────────────────────────────────────
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

  // ─── Media ───────────────────────────────────────────────────────────
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

  // ─── Report ──────────────────────────────────────────────────────────
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

  // ─── Builder ─────────────────────────────────────────────────────────
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
          item_group: r.item_group || '',
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
        primary_color: '#1a73e8',
        background_image: '',
        allow_skip_steps: false,
        allow_go_back: true,
        require_all_required: true,
        max_total_selections: 0,
        steps: [],
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

  // ─── Settings serialization ──────────────────────────────────────────
  function serializeSettingsState() {
    return serializeProductSettingsState(settingsForm, builderConfig.value)
  }

  function buildSettingsPayload() {
    return buildProductSettingsPayload({
      itemName: detail.value?.item?.name,
      form: settingsForm,
      builderConfig: builderConfig.value,
    })
  }

  // ─── Lifecycle / window handlers ─────────────────────────────────────
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
      const queryString = nextUrl.searchParams.toString()
      const targetUrl = `${nextUrl.pathname}${queryString ? `?${queryString}` : ''}${nextUrl.hash || ''}`
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
  })

  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
    window.removeEventListener('keydown', onWindowKeydown)
    cleanupPreviewViewportListener()
  })

  // Initial load (mirrors the original top-level Promise.all in the page).
  Promise.all([loadBuilderItemOptions(), loadTagOptions(), loadDetail()])

  return {
    // formatting helpers (re-exported from utils for template convenience)
    formatMoney,
    formatPersianDate,
    formatNumber,
    formatTableCell,
    formatVariantAttributes,

    // core state
    itemName,
    filters,
    loading,
    error,
    detail,
    activeTab,
    tabOptions,
    settingsForm,
    fieldOptions,
    filteredSubcategoryOptions,
    selectedCategoryLabel,
    selectedSubcategoryLabel,
    pageTitle,
    pageSubtitle,
    hasUnsavedChanges,
    canSaveSettings,
    savingSettings,
    saveSettings,
    loadDetail,
    getTabBadge,
    productReadinessChecks,
    readinessScore,
    mainImage,

    // pricing
    priceForm,
    priceLists,
    priceListOptions,
    activeCurrency,
    currentPriceRate,
    latestPriceRate,
    latestPriceDate,
    selectedDefaultPriceList,
    savingDefaultPriceList,
    savingPrice,
    saveDefaultPriceList,
    savePrice,

    // tags
    tagList,
    allTagOptions,
    handleCreateTagOption,

    // media
    mediaItems,
    galleryImages,
    selectImage,
    uploadImages,
    setCoverImage,
    setSecondaryImage,
    removeImage,
    mediaUploading,
    mediaSaving,
    mediaError,
    mediaSuccess,

    // preview
    previewModalOpen,
    previewModalItem,
    previewMenuCardRows,
    customerPreviewUrl,
    isCompactViewport,
    openPreviewCard,

    // bom
    bomForm,
    bomColumns,
    bomItemsSummary,
    bomItemOptions,
    bomCompanyOptions,
    bomCurrencyOptions,
    productBoms,
    bomError,
    bomSaving,
    bomSaveSuccess,
    addBomItemRow,
    removeBomItemRow,
    updateBomItemCode,
    loadBomDocIntoForm,
    saveBomFromProduct,

    // variants
    isVariantContext,
    hasVariantFeatureEnabled,
    resolvedTemplateName,
    resolvedTemplateLabel,
    variantBuilderLoading,
    variantBuilderError,
    variantBuilderSuccess,
    variantBuilderGenerating,
    variantAttributesDraft,
    selectedTemplateAttributes,
    selectedTemplateAttributeCount,
    activeTemplateAttributes,
    inactiveTemplateAttributes,
    variantCreationAttributes,
    variantRows,
    currentVariantAttributeRows,
    activeVariantAttributeName,
    activeVariantAttributeRow,
    activeAttributeSelectedValues,
    activeAttributeDocUrl,
    attributeValuesDialogOpen,
    variantCreationDialogOpen,
    variantCreationForm,
    showAddAttributeDialog,
    selectedNewAttribute,
    openVariantCreationDialog,
    closeVariantCreationDialog,
    createVariantsFromDialog,
    openAttributeEditor,
    countSelectedValues,
    updateAttributeToggle,
    updateAttributeDefault,
    toggleGeneratedValue,
    addVariantCreationOption,
    removeAttributeFromTemplate,
    addAttributeToTemplate,

    // builder
    builderConfig,
    builderItemOptions,
    builderSourceTemplateName,
    builderTemplateOptions,
    hasBuilderConfig,
    applyBuilderTemplateToProduct,
    resetBuilderToTemplate,
    addBuilderStep,
    updateBuilderStep,
    moveBuilderStep,
    deleteBuilderStep,

    // report
    localizedReport,
    hasReportData,
  }
}
