const STORAGE_KEY = 'restaurant.site.authoring.draft.v1'

const DEFAULT_DRAFT = {
  theme_settings: null,
  site_settings: null,
  page_layouts: {},
  updated_at: '',
}

function clone(value) {
  try {
    return JSON.parse(JSON.stringify(value))
  } catch (_) {
    return value
  }
}

function normalizeDraft(raw = {}) {
  return {
    theme_settings: raw?.theme_settings && typeof raw.theme_settings === 'object' ? clone(raw.theme_settings) : null,
    site_settings: raw?.site_settings && typeof raw.site_settings === 'object' ? clone(raw.site_settings) : null,
    page_layouts: raw?.page_layouts && typeof raw.page_layouts === 'object' ? clone(raw.page_layouts) : {},
    updated_at: String(raw?.updated_at || '').trim(),
  }
}

export function loadSiteAuthoringDraft() {
  if (typeof window === 'undefined') {
    return clone(DEFAULT_DRAFT)
  }
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}')
    return normalizeDraft(parsed)
  } catch (_) {
    return clone(DEFAULT_DRAFT)
  }
}

export function saveSiteAuthoringDraft(partial = {}) {
  const current = loadSiteAuthoringDraft()
  const next = normalizeDraft({
    ...current,
    ...partial,
    updated_at: new Date().toISOString(),
  })
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  }
  return next
}

export function clearSiteAuthoringDraft() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(STORAGE_KEY)
  }
  return clone(DEFAULT_DRAFT)
}

export function readDraftPageLayout(page = 'home') {
  const draft = loadSiteAuthoringDraft()
  const key = String(page || 'home').trim() || 'home'
  return draft.page_layouts?.[key] ? clone(draft.page_layouts[key]) : null
}

export function writeDraftPageLayout(page = 'home', layout = {}) {
  const draft = loadSiteAuthoringDraft()
  const key = String(page || 'home').trim() || 'home'
  const pageLayouts = {
    ...(draft.page_layouts || {}),
    [key]: clone(layout),
  }
  return saveSiteAuthoringDraft({ page_layouts: pageLayouts })
}

export function readDraftThemeSettings() {
  return loadSiteAuthoringDraft().theme_settings
}

export function writeDraftThemeSettings(settings = {}) {
  return saveSiteAuthoringDraft({ theme_settings: clone(settings) })
}

export function readDraftSiteSettings() {
  return loadSiteAuthoringDraft().site_settings
}

export function writeDraftSiteSettings(settings = {}) {
  return saveSiteAuthoringDraft({ site_settings: clone(settings) })
}
