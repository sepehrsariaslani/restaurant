function token(value) {
  return String(value || '').trim().toLocaleLowerCase('fa-IR')
}

function sortItems(items, mode) {
  const rows = [...items]
  if (mode === 'price_asc') return rows.sort((a, b) => Number(a.base_price || 0) - Number(b.base_price || 0))
  if (mode === 'price_desc') return rows.sort((a, b) => Number(b.base_price || 0) - Number(a.base_price || 0))
  if (mode === 'name_asc') return rows.sort((a, b) => String(a.title || '').localeCompare(String(b.title || ''), 'fa'))
  return rows
}

export function buildMenuSections(categories = [], items = [], sortMode = 'default') {
  const groups = categories.map((category) => ({
    slug: String(category.slug || '').trim(),
    title: String(category.title || category.name || '').trim(),
    items: [],
    sections: [],
    subcategories: [],
    configuredSubcategories: Array.isArray(category.subcategories) ? category.subcategories : [],
  }))
  const bySlug = new Map(groups.map((group) => [group.slug, group]))
  const byTitle = new Map(groups.map((group) => [token(group.title), group]))

  for (const item of items) {
    const group = bySlug.get(String(item.category_slug || '').trim())
      || byTitle.get(token(item.category_title || item.category))
    if (group) group.items.push(item)
  }

  for (const group of groups) {
    if (!group.items.length) continue
    const sectionsBySlug = new Map()
    const sectionsByTitle = new Map()
    const configured = [...group.configuredSubcategories].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))

    function addSection(slug, title) {
      const section = { slug, title, items: [], anchorKey: `${group.slug}:${slug || 'other'}` }
      group.sections.push(section)
      if (slug) sectionsBySlug.set(slug, section)
      if (title) sectionsByTitle.set(token(title), section)
      return section
    }

    for (const sub of configured) {
      const title = String(sub.title || sub.name || '').trim()
      const slug = String(sub.slug || '').trim() || `name:${token(title)}`
      if (slug && !sectionsBySlug.has(slug)) addSection(slug, title || 'زیردسته')
    }

    let other = null
    for (const item of group.items) {
      const slug = String(item.subcategory_slug || '').trim()
      const title = String(item.subcategory_title || item.subcategory || '').trim()
      let section = sectionsBySlug.get(slug) || sectionsByTitle.get(token(title))
      if (!section && (slug || title)) section = addSection(slug || `name:${token(title)}`, title || 'زیردسته')
      if (!section) {
        other ||= addSection('', configured.length || group.sections.length ? 'سایر موارد' : '')
        section = other
      }
      section.items.push(item)
    }

    group.sections = group.sections.filter((section) => section.items.length).map((section) => ({
      ...section,
      items: sortItems(section.items, sortMode),
    }))
    group.subcategories = group.sections.filter((section) => section.slug).map((section) => ({
      slug: section.slug,
      title: section.title,
      item_count: section.items.length,
    }))
  }

  return groups.filter((group) => group.items.length)
}
