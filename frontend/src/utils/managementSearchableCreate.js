const text = (key, label, extra = {}) => ({ key, label, type: 'text', ...extra })
const number = (key, label, extra = {}) => ({ key, label, type: 'number', ...extra })

export const SEARCHABLE_CREATE_CONFIGS = {
  Item: {
    doctype: 'Item', label: 'کالا', title: 'ایجاد کالای جدید',
    fields: [text('item_name', 'نام کالا', { required: true }), text('item_code', 'کد کالا'), text('item_group', 'گروه کالا'), text('stock_uom', 'واحد پایه')],
  },
  'Item Group': {
    doctype: 'Item Group', label: 'گروه کالا', title: 'ایجاد گروه کالا',
    fields: [text('item_group_name', 'نام گروه', { required: true }), text('parent_item_group', 'گروه والد'), { key: 'is_group', label: 'این گروه زیرگروه می‌پذیرد', type: 'checkbox', default: false }],
  },
  Warehouse: {
    doctype: 'Warehouse', label: 'انبار', title: 'ایجاد انبار',
    fields: [text('warehouse_name', 'نام انبار', { required: true }), text('parent_warehouse', 'انبار والد'), { key: 'is_group', label: 'انبار گروهی', type: 'checkbox', default: false }],
  },
  Supplier: {
    doctype: 'Supplier', label: 'تأمین‌کننده', title: 'ایجاد تأمین‌کننده',
    fields: [text('supplier_name', 'نام تأمین‌کننده', { required: true }), text('supplier_group', 'گروه تأمین‌کننده')],
  },
  Customer: {
    doctype: 'Customer', label: 'مشتری', title: 'ایجاد مشتری',
    fields: [text('customer_name', 'نام مشتری', { required: true }), text('customer_group', 'گروه مشتری'), text('territory', 'منطقه')],
  },
  Account: {
    doctype: 'Account', label: 'حساب', title: 'ایجاد حساب',
    fields: [text('account_name', 'نام حساب', { required: true }), text('parent_account', 'حساب والد'), text('company', 'شرکت'), { key: 'is_group', label: 'حساب گروهی', type: 'checkbox', default: false }],
  },
  'Price List': {
    doctype: 'Price List', label: 'لیست قیمت', title: 'ایجاد لیست قیمت',
    fields: [text('price_list_name', 'نام لیست قیمت', { required: true }), text('currency', 'ارز')],
  },
  UOM: {
    doctype: 'UOM', label: 'واحد اندازه‌گیری', title: 'ایجاد واحد اندازه‌گیری',
    fields: [text('uom_name', 'نام واحد', { required: true })],
  },
}

export function getSearchableCreateConfig(doctype, overrides = {}) {
  const base = SEARCHABLE_CREATE_CONFIGS[String(doctype || '').trim()]
  if (!base) return null
  return {
    ...base,
    ...overrides,
    fields: Array.isArray(overrides.fields) ? overrides.fields : base.fields.map((field) => ({ ...field })),
    defaults: { ...(base.defaults || {}), ...(overrides.defaults || {}) },
  }
}

export { text, number }
