import { getManagementThemeSettings, setManagementThemeSettings } from './api'

const THEME_STORAGE_KEY = 'restaurant.theme.settings.v1'

export const defaultThemeSettings = {
  primary: '#6F4A31',
  accent: '#C98D42',
  success: '#2F8F5B',
  danger: '#B84F4F',
  warning: '#C67B2A',
  surface: '#FBF8F4',
  surfaceAlt: '#F1E7DB',
  background: '#F6F1EA',
  border: '#D5C3AF',
  text: '#3F2A1D',
  textSecondary: '#654A38',
  muted: '#846B58',
  posPrimary: '#6F4A31',
  posAccent: '#C98D42',
  posSuccess: '#0B7D4A',
  posDanger: '#AB3535',
  posWarning: '#F59E0B',
}

export const themePresets = [
  {
    id: 'nooshyar-brown',
    name: 'نوش‌یار قهوه‌ای',
    description: 'تم اصلی برند با قاعده ۶۰/۳۰/۱۰ (خنثی گرم + قهوه‌ای + اکسنت طلایی).',
    colors: {
      ...defaultThemeSettings,
    },
  },
  {
    id: 'saffron-bazaar',
    name: 'بازار زعفران',
    description: 'پایه خنثی روشن، رنگ اصلی خاکی و اکسنت زعفرانی.',
    colors: {
      primary: '#8A5A2B',
      accent: '#DFA11E',
      success: '#3F8F62',
      danger: '#B55044',
      warning: '#C67B2A',
      surface: '#FCF8F1',
      surfaceAlt: '#F3E6D0',
      background: '#F8F1E4',
      border: '#D8C0A0',
      text: '#4C311D',
      textSecondary: '#6B4628',
      muted: '#856143',
      posPrimary: '#8A5A2B',
      posAccent: '#DFA11E',
      posSuccess: '#2F8B5A',
      posDanger: '#A94545',
      posWarning: '#CF8F26',
    },
  },
  {
    id: 'persian-turquoise',
    name: 'فیروزه ایرانی',
    description: '۶۰٪ زمینه خنثی، ۳۰٪ فیروزه‌ای ایرانی، ۱۰٪ اکسنت آبی کاشی.',
    colors: {
      primary: '#176C67',
      accent: '#2BA6C4',
      success: '#1F8A63',
      danger: '#BC4B4B',
      warning: '#D49C2A',
      surface: '#F5F8F8',
      surfaceAlt: '#E4F0EF',
      background: '#EFF5F4',
      border: '#B3CECB',
      text: '#1A3E3A',
      textSecondary: '#2A5C57',
      muted: '#4D7D79',
      posPrimary: '#176C67',
      posAccent: '#2BA6C4',
      posSuccess: '#1F8A63',
      posDanger: '#A94444',
      posWarning: '#C88D2A',
    },
  },
  {
    id: 'ruby-pomegranate',
    name: 'یاقوت اناری',
    description: 'خنثی لطیف با رنگ اصلی اناری و اکسنت رز ایرانی.',
    colors: {
      primary: '#7C2E3C',
      accent: '#C44E65',
      success: '#2F8F5B',
      danger: '#B4353F',
      warning: '#C97C2B',
      surface: '#FAF5F6',
      surfaceAlt: '#F2E1E4',
      background: '#F7ECEE',
      border: '#D9B5BE',
      text: '#4A2028',
      textSecondary: '#6A3540',
      muted: '#8C5F68',
      posPrimary: '#7C2E3C',
      posAccent: '#C44E65',
      posSuccess: '#2F8F5B',
      posDanger: '#AA303A',
      posWarning: '#C97C2B',
    },
  },
  {
    id: 'hyrcanian-green',
    name: 'جنگل هیرکانی',
    description: '۶۰٪ خنثی سرد، ۳۰٪ سبز جنگلی، ۱۰٪ اکسنت زیتونی.',
    colors: {
      primary: '#2F5F47',
      accent: '#9B7E37',
      success: '#2F8F5B',
      danger: '#A84A42',
      warning: '#B4883B',
      surface: '#F4F7F3',
      surfaceAlt: '#E7EEE4',
      background: '#EEF3EC',
      border: '#C2D0BC',
      text: '#243A2F',
      textSecondary: '#355346',
      muted: '#557066',
      posPrimary: '#2F5F47',
      posAccent: '#9B7E37',
      posSuccess: '#2F8F5B',
      posDanger: '#9E433D',
      posWarning: '#B4883B',
    },
  },
]

const COLOR_KEYS = Object.keys(defaultThemeSettings)
const HEX_COLOR_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/

function normalizeHex(color, fallback) {
  const raw = String(color || '').trim()
  if (!HEX_COLOR_REGEX.test(raw)) {
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

function clampChannel(value) {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function hexToRgbTuple(hex) {
  const normalized = normalizeHex(hex, '#000000')
  const value = normalized.slice(1)
  return [
    Number.parseInt(value.slice(0, 2), 16),
    Number.parseInt(value.slice(2, 4), 16),
    Number.parseInt(value.slice(4, 6), 16),
  ]
}

function rgbStringFromHex(hex) {
  const [red, green, blue] = hexToRgbTuple(hex)
  return `${red} ${green} ${blue}`
}

function alphaColorFromHex(hex, alpha) {
  const [red, green, blue] = hexToRgbTuple(hex)
  return `rgb(${red} ${green} ${blue} / ${alpha})`
}

function tintHex(hex, whiteRatio = 0.86) {
  const safeRatio = Math.max(0, Math.min(1, Number(whiteRatio) || 0))
  const [red, green, blue] = hexToRgbTuple(hex)
  const mix = (channel) => clampChannel(channel + (255 - channel) * safeRatio)
  const parts = [mix(red), mix(green), mix(blue)].map((channel) => channel.toString(16).padStart(2, '0'))
  return `#${parts.join('')}`.toUpperCase()
}

export function sanitizeThemeSettings(partial = {}) {
  return COLOR_KEYS.reduce((acc, key) => {
    acc[key] = normalizeHex(partial[key], defaultThemeSettings[key])
    return acc
  }, {})
}

export function loadThemeSettings() {
  if (typeof window === 'undefined') {
    return { ...defaultThemeSettings }
  }
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY)
    if (!raw) {
      return { ...defaultThemeSettings }
    }
    const parsed = JSON.parse(raw)
    return sanitizeThemeSettings(parsed)
  } catch (error) {
    return { ...defaultThemeSettings }
  }
}

export function saveThemeSettings(settings = {}) {
  const normalized = sanitizeThemeSettings(settings)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(normalized))
  }
  return normalized
}

export function clearThemeSettings() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(THEME_STORAGE_KEY)
  }
}

function setCssVar(name, value) {
  if (typeof document === 'undefined') {
    return
  }
  document.documentElement.style.setProperty(name, value)
}

export function applyThemeSettings(settings = {}) {
  const normalized = sanitizeThemeSettings({ ...defaultThemeSettings, ...settings })
  const softPrimary = normalizeHex(normalized.surfaceAlt, tintHex(normalized.primary, 0.84))
  const bgSoft = normalizeHex(normalized.background, tintHex(normalized.surface, 0.35))
  const borderColor = normalizeHex(normalized.border, tintHex(normalized.primary, 0.62))

  setCssVar('--palette-deep-sapphire', normalized.primary)
  setCssVar('--palette-deep-sapphire-rgb', rgbStringFromHex(normalized.primary))
  setCssVar('--palette-june-bud', softPrimary)
  setCssVar('--palette-june-bud-rgb', rgbStringFromHex(softPrimary))
  setCssVar('--palette-deep-saffron', normalized.accent)
  setCssVar('--palette-deep-saffron-rgb', rgbStringFromHex(normalized.accent))
  setCssVar('--palette-eggshell', normalized.surface)
  setCssVar('--palette-eggshell-rgb', rgbStringFromHex(normalized.surface))
  setCssVar('--theme-surface-alt', normalized.surfaceAlt)
  setCssVar('--theme-background', bgSoft)
  setCssVar('--theme-border', borderColor)

  setCssVar('--accent-green', normalized.primary)
  setCssVar('--accent-green80', alphaColorFromHex(normalized.primary, 0.9))
  setCssVar('--accent-green60', alphaColorFromHex(normalized.primary, 0.7))
  setCssVar('--accent-green40', alphaColorFromHex(normalized.primary, 0.14))
  setCssVar('--accent-green20', alphaColorFromHex(normalized.primary, 0.08))
  setCssVar('--accent-gold', normalized.accent)
  setCssVar('--accent-gold80', alphaColorFromHex(normalized.accent, 0.9))
  setCssVar('--accent-gold50', alphaColorFromHex(normalized.accent, 0.6))
  setCssVar('--accent-gold20', alphaColorFromHex(normalized.accent, 0.12))
  setCssVar('--accent', normalized.primary)

  setCssVar('--glass-bg', normalized.surface)
  setCssVar('--glass-border', borderColor)
  setCssVar('--bg-soft', bgSoft)

  setCssVar('--text-primary', normalized.text)
  setCssVar('--text-secondary', normalized.textSecondary)
  setCssVar('--text-muted', normalized.muted)
  setCssVar('--ink-900', normalized.text)
  setCssVar('--ink-800', normalized.textSecondary)
  setCssVar('--ink-700', normalized.muted)
  setCssVar('--ink-600', tintHex(normalized.muted, 0.2))
  setCssVar('--ink-400', tintHex(normalized.muted, 0.48))
  setCssVar('--ink-200', tintHex(normalized.muted, 0.72))
  setCssVar('--management-ink', normalized.text)
  setCssVar('--danger', normalized.danger)
  setCssVar('--danger-rgb', rgbStringFromHex(normalized.danger))
  setCssVar('--success', normalized.success)
  setCssVar('--success-rgb', rgbStringFromHex(normalized.success))
  setCssVar('--warning', normalized.warning)
  setCssVar('--warning-rgb', rgbStringFromHex(normalized.warning))

  setCssVar('--pos-primary-color', normalized.posPrimary)
  setCssVar('--pos-primary-rgb', rgbStringFromHex(normalized.posPrimary))
  setCssVar('--pos-accent-color', normalized.posAccent)
  setCssVar('--pos-accent-rgb', rgbStringFromHex(normalized.posAccent))
  setCssVar('--pos-success-color', normalized.posSuccess)
  setCssVar('--pos-success-rgb', rgbStringFromHex(normalized.posSuccess))
  setCssVar('--pos-danger-color', normalized.posDanger)
  setCssVar('--pos-danger-rgb', rgbStringFromHex(normalized.posDanger))
  setCssVar('--pos-warning-color', normalized.posWarning)
  setCssVar('--pos-warning-rgb', rgbStringFromHex(normalized.posWarning))
  setCssVar('--pos-surface-color', normalized.surface)

  if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
    window.dispatchEvent(new CustomEvent('restaurant-theme-updated', { detail: normalized }))
  }

  return normalized
}

export function applySavedThemeSettings(bootSettings = null) {
  const hasBootSettings = bootSettings && typeof bootSettings === 'object'
  const saved = hasBootSettings ? sanitizeThemeSettings(bootSettings) : loadThemeSettings()
  if (hasBootSettings) {
    saveThemeSettings(saved)
  }
  return applyThemeSettings(saved)
}

export function resetThemeSettings() {
  clearThemeSettings()
  return applyThemeSettings(defaultThemeSettings)
}

export async function hydrateThemeSettingsFromServer() {
  try {
    const remote = await getManagementThemeSettings()
    const normalized = sanitizeThemeSettings(remote)
    saveThemeSettings(normalized)
    applyThemeSettings(normalized)
    return normalized
  } catch (error) {
    return loadThemeSettings()
  }
}

export async function saveThemeSettingsToServer(settings = {}) {
  const normalized = sanitizeThemeSettings(settings)
  const saved = await setManagementThemeSettings(normalized)
  const sanitizedSaved = sanitizeThemeSettings(saved)
  saveThemeSettings(sanitizedSaved)
  applyThemeSettings(sanitizedSaved)
  return sanitizedSaved
}
