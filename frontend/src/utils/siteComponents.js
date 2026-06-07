export function resolveBranding(boot = {}) {
  const fromBoot = boot.branding && typeof boot.branding === 'object' ? boot.branding : {}
  return {
    ...fromBoot,
    name: fromBoot.name || 'Veederakht Restaurant',
    tagline: fromBoot.tagline || 'منوی آنلاین تازه و قابل شخصی سازی',
    hero_title: fromBoot.hero_title || 'منوی آنلاین با انتخاب کامل مواد داخل هر غذا',
    hero_subtitle: fromBoot.hero_subtitle || '',
    primary_cta_label: fromBoot.primary_cta_label || 'ورود به منو',
    hero_image: fromBoot.hero_image || '',
    header_variant: fromBoot.header_variant || 'classic',
    menu_search_variant: fromBoot.menu_search_variant || 'search-card',
    hero_section_variant: fromBoot.hero_section_variant || 'off',
    footer_variant: fromBoot.footer_variant || 'full',
    hero_section_enabled: Number(fromBoot.hero_section_enabled || 0) ? 1 : 0,
    footer_enabled: Number(fromBoot.footer_enabled ?? 1) ? 1 : 0,
    hero_section_title: fromBoot.hero_section_title || '',
    hero_section_description: fromBoot.hero_section_description || '',
    hero_section_cta: fromBoot.hero_section_cta || '',
    footer_description: fromBoot.footer_description || '',
    footer_phone: fromBoot.footer_phone || '',
    footer_email: fromBoot.footer_email || '',
    footer_address: fromBoot.footer_address || '',
    footer_instagram: fromBoot.footer_instagram || '',
    footer_telegram: fromBoot.footer_telegram || '',
    footer_copyright: fromBoot.footer_copyright || '',
  }
}

export function resolveSiteComponents(boot = {}) {
  const branding = resolveBranding(boot)
  const fromSettings = boot.web_settings && typeof boot.web_settings === 'object' ? boot.web_settings : {}
  const source = { ...branding, ...fromSettings }
  const heroEnabled = Number(source.hero_section_enabled || 0) === 1
  const footerEnabled = Number(source.footer_enabled ?? 1) !== 0

  return {
    header_variant: normalizeHeaderVariant(source.header_variant),
    menu_search_variant: normalizeMenuSearchVariant(source.menu_search_variant),
    hero_section_variant: String(source.hero_section_variant || (heroEnabled ? 'fullscreen' : 'off')).trim() || 'off',
    footer_variant: String(source.footer_variant || (footerEnabled ? 'full' : 'off')).trim() || 'full',
  }
}

export function normalizeHeaderVariant(value = '') {
  const normalized = String(value || '').trim()
  if (normalized === 'minimal') {
    return 'minimal'
  }
  return 'classic'
}

export function normalizeMenuSearchVariant(value = '') {
  const normalized = String(value || '').trim()
  if (normalized === 'off') {
    return 'off'
  }
  return 'search-card'
}
