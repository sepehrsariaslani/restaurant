const colorTokens = {
  primary: '--ds-color-action-primary', accent: '--ds-color-action-accent',
  surface: '--ds-color-surface', background: '--ds-color-bg-page',
  text: '--ds-color-text-primary', muted: '--ds-color-text-muted',
}
const numeric = { padding: 'padding', gap: 'gap', radius: 'radius', fontSize: 'font-size', minHeight: 'min-height', maxWidth: 'max-width' }
export function blockDesignStyle(design = {}) {
  const result = {}
  for (const device of ['desktop', 'mobile']) {
    const values = device === 'mobile' ? { ...design.desktop, ...design.mobile } : design.desktop || {}
    for (const [key, property] of Object.entries(numeric)) {
      if (values[key] === '' || values[key] == null || !Number.isFinite(Number(values[key]))) continue
      result[`--block-${device}-${property}`] = `${Math.max(0, Math.min(1920, Number(values[key])))}px`
    }
    for (const key of ['background', 'color']) {
      const value = values[key]
      if (colorTokens[value]) result[`--block-${device}-${key}`] = `var(${colorTokens[value]})`
      else if (value === 'transparent' || /^#[0-9a-f]{3,8}$/i.test(value || '')) result[`--block-${device}-${key}`] = value
    }
    if (['start', 'center', 'end'].includes(values.align)) result[`--block-${device}-align`] = values.align
    if (values.columns != null) result[`--block-${device}-columns`] = Math.max(1, Math.min(6, Number(values.columns) || 1))
    result[`--block-${device}-display`] = values.hidden ? 'none' : 'block'
  }
  return result
}
export function safeDesignUrl(value, fallback = '') {
  const text = String(value || '').trim()
  return /^(\/[^/]|#[^\s]*$|https?:\/\/|mailto:|tel:)/i.test(text) ? text : fallback
}
