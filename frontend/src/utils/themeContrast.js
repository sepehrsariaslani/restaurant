const HEX_COLOR_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/

function normalizeHex(color, fallback) {
  const raw = String(color || '').trim()
  if (!HEX_COLOR_REGEX.test(raw)) return fallback
  if (raw.length === 4) {
    const expanded = raw.slice(1).split('').map((character) => character + character).join('')
    return `#${expanded}`.toUpperCase()
  }
  return raw.toUpperCase()
}

function toRgb(hex) {
  const value = hex.slice(1)
  return [0, 2, 4].map((offset) => Number.parseInt(value.slice(offset, offset + 2), 16))
}

function relativeLuminance(hex) {
  const channels = toRgb(hex).map((channel) => {
    const value = channel / 255
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

function contrastRatio(first, second) {
  const firstLuminance = relativeLuminance(first)
  const secondLuminance = relativeLuminance(second)
  return (Math.max(firstLuminance, secondLuminance) + 0.05) / (Math.min(firstLuminance, secondLuminance) + 0.05)
}

/** Choose whichever of black or white gives the strongest readable text contrast. */
export function readableForeground(background) {
  const safeBackground = normalizeHex(background, '#000000')
  return contrastRatio(safeBackground, '#FFFFFF') >= contrastRatio(safeBackground, '#000000')
    ? '#FFFFFF'
    : '#000000'
}

function mixHex(first, second, secondRatio) {
  const safeRatio = Math.max(0, Math.min(1, secondRatio))
  const firstChannels = toRgb(first)
  const secondChannels = toRgb(second)
  const parts = firstChannels.map((channel, index) => {
    const mixed = Math.max(0, Math.min(255, Math.round(channel + (secondChannels[index] - channel) * safeRatio)))
    return mixed.toString(16).padStart(2, '0')
  })
  return `#${parts.join('')}`.toUpperCase()
}

function tintHex(hex, whiteRatio) {
  return mixHex(hex, '#FFFFFF', whiteRatio)
}

/** Keep saved theme borders while ensuring low-contrast borders remain visible. */
export function ensureThemeBorderContrast(border, surface, primary, minimumRatio = 3) {
  const safePrimary = normalizeHex(primary, '#B94712')
  const safeSurface = normalizeHex(surface, '#FFFFFF')
  const safeBorder = normalizeHex(border, tintHex(safePrimary, 0.62))
  const targetRatio = Math.max(1, Number(minimumRatio) || 3)
  if (contrastRatio(safeBorder, safeSurface) >= targetRatio) return safeBorder

  const blackContrast = contrastRatio('#000000', safeSurface)
  const whiteContrast = contrastRatio('#FFFFFF', safeSurface)
  const target = contrastRatio(safePrimary, safeSurface) >= targetRatio
    ? safePrimary
    : blackContrast >= whiteContrast ? '#000000' : '#FFFFFF'

  let low = 0
  let high = 1
  let best = target
  for (let iteration = 0; iteration < 20; iteration += 1) {
    const middle = (low + high) / 2
    const candidate = mixHex(safeBorder, target, middle)
    if (contrastRatio(candidate, safeSurface) >= targetRatio) {
      best = candidate
      high = middle
    } else {
      low = middle
    }
  }
  return best
}
