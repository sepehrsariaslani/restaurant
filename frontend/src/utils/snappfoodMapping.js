export function groupSnappfoodMappingRows(rows = []) {
  const categories = []
  const categoryByKey = new Map()

  for (const row of rows || []) {
    const categoryKey = String(row.category_id || (row.category_title ? `title:${row.category_title}` : '__uncategorized__'))
    if (!categoryByKey.has(categoryKey)) {
      const category = {
        key: categoryKey,
        title: row.category_title || 'بدون گروه مشخص',
        category_id: row.category_id || '',
        products: [],
        productByKey: new Map(),
      }
      categoryByKey.set(categoryKey, category)
      categories.push(category)
    }

    const category = categoryByKey.get(categoryKey)
    const productId = String(row.product_id || '').trim()
    const groupKey = productId ? `product:${productId}` : `row:${row.external_id || row.title || category.products.length}`
    if (!category.productByKey.has(groupKey)) {
      const product = {
        key: groupKey,
        product_id: productId,
        product_hash_id: row.product_hash_id || '',
        title: row.product_title || row.title || 'بدون عنوان',
        rows: [],
        mapping_status: 'Unmapped',
        mapped_item: null,
        suggested_item: null,
      }
      category.productByKey.set(groupKey, product)
      category.products.push(product)
    }
    const product = category.productByKey.get(groupKey)
    if (!product.product_hash_id && row.product_hash_id) product.product_hash_id = row.product_hash_id
    if (!row.product_title && product.rows.length === 0 && row.title) product.title = row.title
    product.rows.push(row)
  }

  for (const category of categories) {
    delete category.productByKey
    for (const product of category.products) {
      const mapped = product.rows.filter((row) => row.mapping_status === 'Mapped' && row.mapped_item)
      const mappedNames = new Set(mapped.map((row) => row.mapped_item.name || row.mapped_item.item_name || ''))
      if (mapped.length === product.rows.length && mappedNames.size === 1) {
        product.mapping_status = 'Mapped'
        product.mapped_item = mapped[0].mapped_item
      } else if (mapped.length > 0) {
        product.mapping_status = 'Partial'
        product.mapped_item = mapped[0].mapped_item
      }
      product.suggested_item = product.rows.find((row) => row.suggested_item)?.suggested_item || null
    }
  }

  return categories
}
