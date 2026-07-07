const MODE_OPTIONS = ['preset', 'custom']
const PRESET_OPTIONS = ['steaming-bowl', 'noodle-bowl', 'burger-stack', 'club-sandwich', 'coffee-cup', 'pizza-slice', 'donut-bite']
const HEX_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/

export const defaultLoaderSettings = {
  enabled: 1,
  mode: 'preset',
  preset: 'steaming-bowl',
  title: 'در حال آماده سازی سفارش',
  subtitle: 'آشپزخانه مشغول آماده کردن سفارش شماست...',
  minDurationMs: 1400,
  overlayColor: '#F6F4ED',
  accentColor: '#6A9A6B',
  customCode: '',
}

function normalizeBoolean(value, fallback = 0) {
  if (value === undefined || value === null || value === '') {
    return Number(fallback) ? 1 : 0
  }
  return Number(value) ? 1 : 0
}

function normalizeMode(value, fallback = defaultLoaderSettings.mode) {
  const normalized = String(value || '').trim().toLowerCase()
  return MODE_OPTIONS.includes(normalized) ? normalized : fallback
}

function normalizePreset(value, fallback = defaultLoaderSettings.preset) {
  const normalized = String(value || '').trim().toLowerCase()
  const legacyAliasMap = {
    'willow-tree': 'steaming-bowl',
    'pulse-ring': 'burger-stack',
    'wave-bars': 'pizza-slice',
  }
  const mapped = legacyAliasMap[normalized] || normalized
  return PRESET_OPTIONS.includes(mapped) ? mapped : fallback
}

function normalizeColor(value, fallback) {
  const raw = String(value || '').trim()
  if (!HEX_REGEX.test(raw)) {
    return fallback
  }
  if (raw.length === 4) {
    const expanded = raw
      .slice(1)
      .split('')
      .map((char) => char + char)
      .join('')
    return `#${expanded}`.toUpperCase()
  }
  return raw.toUpperCase()
}

function clampDuration(value, fallback = defaultLoaderSettings.minDurationMs) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    return fallback
  }
  return Math.max(0, Math.min(8000, Math.round(parsed)))
}

function pickFirst(source, keys, fallback = '') {
  for (const key of keys) {
    if (source && source[key] !== undefined && source[key] !== null) {
      return source[key]
    }
  }
  return fallback
}

function normalizeCustomCode(value) {
  const raw = String(value || '')
  if (!raw.trim()) {
    return ''
  }
  return raw.slice(0, 20000)
}

export function normalizeLoaderSettings(source = {}) {
  const enabledRaw = pickFirst(source, ['enabled', 'loader_enabled'], defaultLoaderSettings.enabled)
  const modeRaw = pickFirst(source, ['mode', 'loader_mode'], defaultLoaderSettings.mode)
  const presetRaw = pickFirst(source, ['preset', 'loader_preset'], defaultLoaderSettings.preset)
  const titleRaw = pickFirst(source, ['title', 'loader_title'], defaultLoaderSettings.title)
  const subtitleRaw = pickFirst(source, ['subtitle', 'loader_subtitle'], defaultLoaderSettings.subtitle)
  const durationRaw = pickFirst(source, ['minDurationMs', 'min_duration_ms', 'loader_min_duration_ms'], defaultLoaderSettings.minDurationMs)
  const overlayRaw = pickFirst(source, ['overlayColor', 'overlay_color', 'loader_overlay_color'], defaultLoaderSettings.overlayColor)
  const accentRaw = pickFirst(source, ['accentColor', 'accent_color', 'loader_accent_color'], defaultLoaderSettings.accentColor)
  const customCodeRaw = pickFirst(source, ['customCode', 'custom_code', 'loader_custom_code'], defaultLoaderSettings.customCode)

  const mode = normalizeMode(modeRaw)

  return {
    enabled: normalizeBoolean(enabledRaw, defaultLoaderSettings.enabled),
    mode,
    preset: normalizePreset(presetRaw),
    title: String(titleRaw || '').trim() || defaultLoaderSettings.title,
    subtitle: String(subtitleRaw || '').trim() || defaultLoaderSettings.subtitle,
    minDurationMs: clampDuration(durationRaw),
    overlayColor: normalizeColor(overlayRaw, defaultLoaderSettings.overlayColor),
    accentColor: normalizeColor(accentRaw, defaultLoaderSettings.accentColor),
    customCode: mode === 'custom' ? normalizeCustomCode(customCodeRaw) : String(customCodeRaw || ''),
  }
}

function collectBootCandidates(boot = {}) {
  if (!boot || typeof boot !== 'object') {
    return []
  }
  const webSettings = boot.web_settings && typeof boot.web_settings === 'object' ? boot.web_settings : {}
  const brandingSettings = boot.branding && typeof boot.branding === 'object' ? boot.branding : {}
  return [
    boot,
    boot.loader_settings && typeof boot.loader_settings === 'object' ? boot.loader_settings : {},
    webSettings,
    webSettings.loader_settings && typeof webSettings.loader_settings === 'object' ? webSettings.loader_settings : {},
    brandingSettings.loader_settings && typeof brandingSettings.loader_settings === 'object' ? brandingSettings.loader_settings : {},
  ]
}

export function resolveLoaderSettingsFromBoot(boot = {}) {
  const merged = {}
  for (const candidate of collectBootCandidates(boot)) {
    Object.assign(merged, candidate || {})
  }
  return normalizeLoaderSettings(merged)
}

export function toLoaderWebSettingsPayload(source = {}) {
  const normalized = normalizeLoaderSettings(source)
  return {
    loader_enabled: normalized.enabled ? 1 : 0,
    loader_mode: normalized.mode,
    loader_preset: normalized.preset,
    loader_title: normalized.title,
    loader_subtitle: normalized.subtitle,
    loader_min_duration_ms: normalized.minDurationMs,
    loader_overlay_color: normalized.overlayColor,
    loader_accent_color: normalized.accentColor,
    loader_custom_code: String(normalized.customCode || ''),
  }
}
