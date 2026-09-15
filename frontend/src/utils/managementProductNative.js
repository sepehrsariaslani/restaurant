const field = (key, label, type = 'text', extra = {}) => ({ key, label, type, ...extra })
const link = (key, label, doctype, extra = {}) => field(key, label, 'link', { doctype, ...extra })
const check = (key, label, extra = {}) => field(key, label, 'check', extra)
const number = (key, label, extra = {}) => field(key, label, 'number', extra)

export const nativeFieldSections = [
  {
    id: 'classification',
    title: 'طبقه‌بندی و رفتار پایه',
    description: 'فیلدهای native که رفتار کالا را در ERPNext کنترل می‌کنند.',
    fields: [
      field('naming_series', 'سری نام‌گذاری'),
      link('brand', 'برند', 'Brand', { labelField: 'brand_name' }),
      check('disabled', 'غیرفعال در ERPNext'),
      check('allow_alternative_item', 'اجازه کالای جایگزین'),
      check('include_item_in_manufacturing', 'استفاده در تولید'),
      number('opening_stock', 'موجودی افتتاحیه'),
      number('valuation_rate', 'نرخ ارزش‌گذاری'),
      check('is_fixed_asset', 'دارایی ثابت'),
      link('asset_category', 'دسته دارایی', 'Asset Category', { showWhen: (state) => Boolean(state.fields.is_fixed_asset) }),
      field('asset_naming_series', 'سری نام‌گذاری دارایی', 'text', { showWhen: (state) => Boolean(state.fields.is_fixed_asset) }),
    ],
  },
  {
    id: 'variants',
    title: 'مدل‌ها و بارکدها',
    description: 'قالب Variant، ویژگی‌ها و بارکدهای native کالا.',
    fields: [
      check('has_variants', 'این کالا دارای مدل است'),
      link('variant_of', 'مدل پایه', 'Item', { showWhen: (state) => !state.fields.has_variants }),
      field('variant_based_on', 'مبنای مدل', 'select', { options: ['', 'Item Attribute', 'Manufacturer'], showWhen: (state) => Boolean(state.fields.has_variants) }),
    ],
  },
  {
    id: 'sales',
    title: 'سیاست فروش و درآمد',
    fields: [
      check('is_sales_item', 'قابل فروش'),
      link('sales_uom', 'واحد پیش‌فرض فروش', 'UOM'),
      number('standard_rate', 'نرخ استاندارد فروش'),
      number('max_discount', 'حداکثر تخفیف مجاز', { suffix: '٪' }),
      check('grant_commission', 'مشمول پورسانت'),
      check('enable_deferred_revenue', 'درآمد انتقالی'),
      number('no_of_months', 'تعداد ماه درآمد', { showWhen: (state) => Boolean(state.fields.enable_deferred_revenue) }),
      check('enable_deferred_expense', 'هزینه انتقالی'),
      number('no_of_months_exp', 'تعداد ماه هزینه', { showWhen: (state) => Boolean(state.fields.enable_deferred_expense) }),
    ],
  },
  {
    id: 'purchase',
    title: 'سیاست خرید و تأمین',
    fields: [
      check('is_purchase_item', 'قابل خرید'),
      link('purchase_uom', 'واحد پیش‌فرض خرید', 'UOM'),
      number('min_order_qty', 'حداقل مقدار سفارش'),
      number('safety_stock', 'موجودی اطمینان'),
      number('lead_time_days', 'زمان تأمین', { suffix: 'روز' }),
      number('last_purchase_rate', 'آخرین نرخ خرید', { readOnly: true }),
      check('is_customer_provided_item', 'کالای تأمین‌شده توسط مشتری'),
      check('delivered_by_supplier', 'ارسال مستقیم توسط تأمین‌کننده'),
      link('country_of_origin', 'کشور مبدأ', 'Country'),
      link('customs_tariff_number', 'شماره تعرفه گمرکی', 'Customs Tariff Number'),
      field('customer_code', 'کد کالا نزد مشتری', 'textarea'),
    ],
  },
  {
    id: 'inventory',
    title: 'کنترل موجودی و ردیابی',
    fields: [
      check('is_stock_item', 'نگهداری موجودی'),
      field('valuation_method', 'روش ارزش‌گذاری', 'select', { options: ['', 'FIFO', 'Moving Average', 'LIFO'] }),
      field('default_material_request_type', 'نوع درخواست پیش‌فرض', 'select', { options: ['', 'Purchase', 'Material Transfer', 'Material Issue', 'Manufacture', 'Customer Provided'] }),
      field('end_of_life', 'پایان عمر کالا', 'date'),
      number('warranty_period', 'دوره ضمانت', { suffix: 'روز' }),
      number('weight_per_unit', 'وزن هر واحد'),
      link('weight_uom', 'واحد وزن', 'UOM'),
      check('allow_negative_stock', 'اجازه موجودی منفی'),
      field('custom_stock_status', 'وضعیت سفارشی موجودی'),
      number('reorder_level', 'نقطه سفارش سفارشی'),
      number('total_projected_qty', 'موجودی پیش‌بینی‌شده کل', { readOnly: true }),
      check('has_serial_no', 'دارای شماره سریال'),
      field('serial_no_series', 'الگوی شماره سریال', 'text', { showWhen: (state) => Boolean(state.fields.has_serial_no) }),
      check('has_batch_no', 'دارای بچ'),
      check('create_new_batch', 'ساخت خودکار بچ', { showWhen: (state) => Boolean(state.fields.has_batch_no) }),
      field('batch_number_series', 'الگوی شماره بچ', 'text', { showWhen: (state) => Boolean(state.fields.has_batch_no && state.fields.create_new_batch) }),
      check('has_expiry_date', 'دارای تاریخ انقضا', { showWhen: (state) => Boolean(state.fields.has_batch_no) }),
      number('shelf_life_in_days', 'عمر نگهداری', { suffix: 'روز', showWhen: (state) => Boolean(state.fields.has_batch_no && state.fields.has_expiry_date) }),
      check('retain_sample', 'نگهداری نمونه', { showWhen: (state) => Boolean(state.fields.has_batch_no) }),
      number('sample_quantity', 'مقدار نمونه', { showWhen: (state) => Boolean(state.fields.has_batch_no && state.fields.retain_sample) }),
    ],
  },
  {
    id: 'operations',
    title: 'وب‌سایت، کیفیت و تولید',
    fields: [
      check('show_on_site', 'نمایش در وب‌سایت'),
      field('custom_url', 'لینک سفارشی وب‌سایت'),
      field('custom_website', 'وب‌سایت'),
      check('inspection_required_before_purchase', 'بازرسی پیش از خرید'),
      check('inspection_required_before_delivery', 'بازرسی پیش از تحویل'),
      link('quality_inspection_template', 'الگوی بازرسی کیفیت', 'Quality Inspection Template'),
      link('default_bom', 'BOM پیش‌فرض', 'BOM'),
      check('is_sub_contracted_item', 'کالای پیمانکاری'),
      number('production_capacity', 'ظرفیت تولید'),
      number('over_delivery_receipt_allowance', 'تلورانس تحویل/دریافت', { suffix: '٪' }),
      number('over_billing_allowance', 'تلورانس صورتحساب', { suffix: '٪' }),
      link('default_item_manufacturer', 'تولیدکننده پیش‌فرض', 'Manufacturer'),
      field('default_manufacturer_part_no', 'شماره فنی تولیدکننده'),
      check('auto_create_assets', 'ساخت خودکار دارایی'),
      check('is_grouped_asset', 'دارایی گروهی'),
    ],
  },
  {
    id: 'accounting',
    title: 'مالیات و پیش‌فرض‌های مالی',
    fields: [
      link('purchase_tax_withholding_category', 'مالیات تکلیفی خرید', 'Tax Withholding Category'),
      link('sales_tax_withholding_category', 'مالیات تکلیفی فروش', 'Tax Withholding Category'),
    ],
  },
]

export const nativeTableConfigs = [
  {
    key: 'attributes',
    section: 'variants',
    title: 'ویژگی‌های مدل',
    doctype: 'Item Variant Attribute',
    columns: [
      { key: 'attribute', label: 'ویژگی', fieldtype: 'Link', options: 'Item Attribute', width: 190 },
      { key: 'attribute_value', label: 'مقدار', width: 160 },
      { key: 'numeric_values', label: 'عددی', fieldtype: 'Check', width: 90 },
      { key: 'from_range', label: 'از', fieldtype: 'Float', width: 100 },
      { key: 'to_range', label: 'تا', fieldtype: 'Float', width: 100 },
      { key: 'increment', label: 'گام', fieldtype: 'Float', width: 100 },
      { key: 'disabled', label: 'غیرفعال', fieldtype: 'Check', width: 90 },
    ],
    showWhen: (state) => Boolean(state.fields.has_variants || state.fields.variant_of),
  },
  {
    key: 'barcodes',
    section: 'variants',
    title: 'بارکدها',
    doctype: 'Item Barcode',
    columns: [
      { key: 'barcode', label: 'بارکد', width: 220 },
      { key: 'barcode_type', label: 'نوع بارکد', fieldtype: 'Select', options: 'EAN\nUPC-A\nCODE-39\nEAN-13\nEAN-8\nGS1\nGTIN\nGTIN-14\nISBN\nISBN-10\nISBN-13\nISSN\nJAN\nPZN\nUPC', width: 150 },
      { key: 'uom', label: 'واحد', fieldtype: 'Link', options: 'UOM', width: 140 },
    ],
  },
  {
    key: 'reorder_levels',
    section: 'inventory',
    title: 'سطح سفارش به تفکیک انبار',
    doctype: 'Item Reorder',
    columns: [
      { key: 'warehouse_group', label: 'گروه انبار', fieldtype: 'Link', options: 'Warehouse', width: 190 },
      { key: 'warehouse', label: 'انبار', fieldtype: 'Link', options: 'Warehouse', width: 220 },
      { key: 'warehouse_reorder_level', label: 'نقطه سفارش', fieldtype: 'Float', width: 130 },
      { key: 'warehouse_reorder_qty', label: 'مقدار سفارش', fieldtype: 'Float', width: 130 },
      { key: 'material_request_type', label: 'نوع درخواست', fieldtype: 'Select', options: 'Purchase\nTransfer\nMaterial Issue\nManufacture', width: 160 },
    ],
  },
  {
    key: 'uoms',
    section: 'inventory',
    title: 'تبدیل واحدها',
    doctype: 'UOM Conversion Detail',
    columns: [
      { key: 'uom', label: 'واحد', fieldtype: 'Link', options: 'UOM', width: 220 },
      { key: 'conversion_factor', label: 'ضریب تبدیل', fieldtype: 'Float', width: 180 },
    ],
  },
  {
    key: 'supplier_items',
    section: 'purchase',
    title: 'کد کالا نزد تأمین‌کننده',
    doctype: 'Item Supplier',
    columns: [
      { key: 'supplier', label: 'تأمین‌کننده', fieldtype: 'Link', options: 'Supplier', width: 240 },
      { key: 'supplier_part_no', label: 'شماره فنی تأمین‌کننده', width: 240 },
    ],
  },
  {
    key: 'customer_items',
    section: 'sales',
    title: 'ارجاع مشتری به کالا',
    doctype: 'Item Customer Detail',
    columns: [
      { key: 'customer_name', label: 'مشتری', fieldtype: 'Link', options: 'Customer', width: 220 },
      { key: 'customer_group', label: 'گروه مشتری', fieldtype: 'Link', options: 'Customer Group', width: 180 },
      { key: 'ref_code', label: 'کد کالا نزد مشتری', width: 200 },
    ],
  },
  {
    key: 'taxes',
    section: 'accounting',
    title: 'قالب‌های مالیات کالا',
    doctype: 'Item Tax',
    columns: [
      { key: 'item_tax_template', label: 'قالب مالیات', fieldtype: 'Link', options: 'Item Tax Template', width: 250 },
      { key: 'tax_category', label: 'دسته مالیاتی', fieldtype: 'Link', options: 'Tax Category', width: 200 },
      { key: 'valid_from', label: 'معتبر از', fieldtype: 'Date', width: 140 },
      { key: 'minimum_net_rate', label: 'حداقل نرخ خالص', fieldtype: 'Float', width: 150 },
      { key: 'maximum_net_rate', label: 'حداکثر نرخ خالص', fieldtype: 'Float', width: 150 },
    ],
  },
  {
    key: 'item_defaults',
    section: 'accounting',
    title: 'پیش‌فرض‌های کالا',
    doctype: 'Item Default',
    columns: [
      { key: 'company', label: 'شرکت', fieldtype: 'Link', options: 'Company', width: 220 },
      { key: 'default_warehouse', label: 'انبار پیش‌فرض', fieldtype: 'Link', options: 'Warehouse', width: 230 },
      { key: 'default_supplier', label: 'تأمین‌کننده پیش‌فرض', fieldtype: 'Link', options: 'Supplier', width: 220 },
      { key: 'buying_cost_center', label: 'مرکز هزینه خرید', fieldtype: 'Link', options: 'Cost Center', width: 220 },
      { key: 'selling_cost_center', label: 'مرکز هزینه فروش', fieldtype: 'Link', options: 'Cost Center', width: 220 },
      { key: 'expense_account', label: 'حساب هزینه', fieldtype: 'Link', options: 'Account', width: 240 },
      { key: 'income_account', label: 'حساب درآمد', fieldtype: 'Link', options: 'Account', width: 240 },
      { key: 'deferred_expense_account', label: 'حساب هزینه انتقالی', fieldtype: 'Link', options: 'Account', width: 240 },
      { key: 'deferred_revenue_account', label: 'حساب درآمد انتقالی', fieldtype: 'Link', options: 'Account', width: 240 },
    ],
  },
]

export function createInitialNativeProductState() {
  return { fields: {}, tables: {} }
}

export function cloneNativeProductState(state = {}) {
  return JSON.parse(JSON.stringify({
    fields: state.fields || {},
    tables: state.tables || {},
  }))
}

export function hydrateNativeProductState(payload = {}) {
  return cloneNativeProductState(payload?.native || payload || {})
}

export function buildNativeProductPayload({ itemName = '', state = {} } = {}) {
  return {
    item_name: String(itemName || '').trim(),
    native: cloneNativeProductState(state),
  }
}

export function isNativeSectionVisible(section, state) {
  return !section?.showWhen || Boolean(section.showWhen(state))
}

export function isNativeFieldVisible(fieldConfig, state) {
  return !fieldConfig?.showWhen || Boolean(fieldConfig.showWhen(state))
}

export function isNativeTableVisible(tableConfig, state) {
  return !tableConfig?.showWhen || Boolean(tableConfig.showWhen(state))
}
