const FEATURE_ICON_KEYS = new Set([
  'zap',
  'sliders',
  'leaf',
  'clock',
  'truck',
  'star',
  'heart',
  'shield',
  'sparkles',
])

function asArray(value) {
  return Array.isArray(value) ? value : []
}

function asObject(value) {
  return value && typeof value === 'object' ? value : {}
}

export function decodeEscapedUnicode(value) {
  return String(value ?? '').replace(/\\u([0-9a-fA-F]{4})/g, (_, code) =>
    String.fromCharCode(Number.parseInt(code, 16)),
  )
}

export function normalizeFeatureItems(items) {
  return asArray(items).map((row) => {
    const source = asObject(row)
    const icon = decodeEscapedUnicode(source.icon).trim().toLowerCase()
    return {
      icon: FEATURE_ICON_KEYS.has(icon) ? icon : 'sparkles',
      title: decodeEscapedUnicode(source.title).trim(),
      description: decodeEscapedUnicode(source.description).trim(),
    }
  })
}

export function normalizeBuilderCategories(categories) {
  return asArray(categories).map((row) => {
    const source = asObject(row)
    const title = String(source.title || source.item_group_name || source.name || '').trim()
    const slug = String(source.slug || source.restaurant_slug || source.name || '').trim()
    const items = asArray(source.items || source.products)
    return {
      name: String(source.name || '').trim(),
      title,
      slug,
      image: String(source.image || source.icon || '').trim(),
      item_count: Number(source.item_count ?? source.items_count ?? items.length) || 0,
      sort_order: Number(source.sort_order || source.restaurant_sort_order || 0) || 0,
      subcategories: asArray(source.subcategories).map((subcategory) => ({
        ...subcategory,
        title: String(subcategory?.title || subcategory?.name || '').trim(),
        slug: String(subcategory?.slug || subcategory?.restaurant_slug || subcategory?.name || '').trim(),
      })),
    }
  })
}

function draftBranding(baseBoot, settings) {
  const baseBranding = asObject(baseBoot.branding)
  const source = asObject(settings)
  const value = (key, fallback = '') => String(source[key] ?? fallback ?? '').trim()

  return {
    ...baseBranding,
    name: value('brand_name', baseBranding.name || 'Veederakht Restaurant') || 'Veederakht Restaurant',
    tagline: value('brand_tagline', baseBranding.tagline),
    hero_title: value('hero_title', baseBranding.hero_title),
    hero_subtitle: value('hero_subtitle', baseBranding.hero_subtitle),
    primary_cta_label: value('primary_cta_label', baseBranding.primary_cta_label || 'ورود به منو') || 'ورود به منو',
    hero_image: value('hero_image', baseBranding.hero_image),
    hero_section_variant: value('hero_section_variant', baseBranding.hero_section_variant || 'off') || 'off',
    hero_section_title: value('hero_section_title', baseBranding.hero_section_title),
    hero_section_description: value('hero_section_description', baseBranding.hero_section_description),
    hero_section_cta: value('hero_section_cta', baseBranding.hero_section_cta),
    hero_variant_contents: source.hero_variant_contents || baseBranding.hero_variant_contents || {},
  }
}

export function mergeBuilderBoot({
  baseBoot = {},
  settings = {},
  heroSlides = [],
  aboutSections = [],
  faqItems = [],
  menuBoot = {},
} = {}) {
  const base = asObject(baseBoot)
  const menu = asObject(menuBoot)
  const sourceCategories = Array.isArray(menu.categories) ? menu.categories : base.categories
  const sourceFeatured = Array.isArray(menu.featured_items)
    ? menu.featured_items
    : base.featured_items
  const sourceCurrency = menu.currency || settings.default_currency || base.currency || 'IRR'

  return {
    ...base,
    web_settings: {
      ...asObject(base.web_settings),
      ...asObject(settings),
    },
    branding: draftBranding(base, settings),
    categories: normalizeBuilderCategories(sourceCategories),
    featured_items: asArray(sourceFeatured),
    hero_slides: asArray(heroSlides),
    about_us_sections: asArray(aboutSections),
    faq_items: asArray(faqItems),
    currency: String(sourceCurrency || 'IRR').trim() || 'IRR',
  }
}

export { FEATURE_ICON_KEYS }
