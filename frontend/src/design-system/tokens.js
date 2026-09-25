const freeze = (value) => Object.freeze(value)

const primitiveColors = freeze({
  primary: '#B94712',
  accent: '#DFAF2E',
  productAccent: '#DFAF2E',
  productMedia: '#FFFFFF',
  surface: '#FFFEFC',
  surfaceAlt: '#F8EBCB',
  background: '#FFF9ED',
  border: '#E2D0AB',
  text: '#382719',
  textSecondary: '#5F4930',
  muted: '#806A50',
  success: '#287347',
  danger: '#A8443C',
  warning: '#915B0B',
})

export const designTokens = freeze({
  direction: 'rtl',
  font: freeze({
    family: 'Peyda',
    weights: freeze({ regular: 400, medium: 500, semibold: 600, bold: 700, black: 900 }),
    bodySize: '1rem',
    bodyLineHeight: 1.65,
  }),
  color: freeze({
    primitive: primitiveColors,
    semantic: freeze({
      surface: freeze({ page: '--ds-color-bg-page', default: primitiveColors.background, base: '--ds-color-surface', raised: '--ds-color-surface-raised', muted: '--ds-color-surface-muted', productMedia: '--ds-color-product-media-surface' }),
      text: freeze({ primary: '--ds-color-text-primary', secondary: '--ds-color-text-secondary', muted: '--ds-color-text-muted', inverse: '--ds-color-text-inverse' }),
      action: freeze({ primary: '--ds-color-action-primary', primaryForeground: '--ds-color-action-primary-foreground', accent: '--ds-color-action-accent', accentForeground: '--ds-color-action-accent-foreground', product: '--ds-color-product-accent', focus: '--ds-color-focus-ring' }),
      status: freeze({ success: '--ds-color-status-success', successForeground: '--ds-color-status-success-foreground', warning: '--ds-color-status-warning', warningForeground: '--ds-color-status-warning-foreground', danger: '--ds-color-status-danger', dangerForeground: '--ds-color-status-danger-foreground', info: '--ds-color-status-info' }),
    }),
  }),
  spacing: freeze({ '0': '0', '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px', '6': '24px', '8': '32px', '10': '40px', '12': '48px', '16': '64px' }),
  radius: freeze({ sm: '10px', md: '16px', lg: '24px', xl: '24px', pill: '999px' }),
  shadow: freeze({ none: 'none', sm: '0 8px 24px rgb(52 38 31 / 0.06)', md: '0 18px 40px rgb(52 38 31 / 0.09)', lg: '0 28px 70px rgb(52 38 31 / 0.14)' }),
  motion: freeze({ fast: '160ms', normal: '240ms', slow: '360ms', easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }),
  zIndex: freeze({ base: 0, sticky: 50, dropdown: 100, drawer: 200, modal: 500, overlay: 1100 }),
})

export const tokenRows = freeze([
  { group: 'رنگ معنایی', token: '--ds-color-bg-page', label: 'پس‌زمینه صفحه', value: primitiveColors.background, swatch: primitiveColors.background },
  { group: 'رنگ معنایی', token: '--ds-color-surface', label: 'سطح پایه', value: primitiveColors.surface, swatch: primitiveColors.surface },
  { group: 'رنگ معنایی', token: '--ds-color-action-primary', label: 'عمل اصلی', value: primitiveColors.primary, swatch: primitiveColors.primary },
  { group: 'رنگ معنایی', token: '--ds-color-action-primary-foreground', label: 'متن روی عمل اصلی', value: 'خودکار بر پایه کنتراست', swatch: '#FFFFFF' },
  { group: 'رنگ معنایی', token: '--ds-color-action-accent', label: 'اکسنت', value: primitiveColors.accent, swatch: primitiveColors.accent },
  { group: 'رنگ معنایی', token: '--ds-color-action-accent-foreground', label: 'متن روی رنگ مکمل', value: 'خودکار بر پایه کنتراست', swatch: '#1C1A18' },
  { group: 'رنگ معنایی', token: '--ds-color-product-accent', label: 'اکسنت محصول', value: primitiveColors.productAccent, swatch: primitiveColors.productAccent },
  { group: 'رنگ معنایی', token: '--ds-color-product-media-surface', label: 'سطح تصویر محصول', value: primitiveColors.productMedia, swatch: primitiveColors.productMedia },
  { group: 'رنگ معنایی', token: '--ds-color-text-primary', label: 'متن اصلی', value: primitiveColors.text, swatch: primitiveColors.text },
  { group: 'رنگ وضعیت', token: '--ds-color-status-success', label: 'موفقیت', value: primitiveColors.success, swatch: primitiveColors.success },
  { group: 'رنگ وضعیت', token: '--ds-color-status-success-foreground', label: 'متن موفقیت', value: 'خودکار بر پایه کنتراست', swatch: '#FFFFFF' },
  { group: 'رنگ وضعیت', token: '--ds-color-status-warning', label: 'هشدار', value: primitiveColors.warning, swatch: primitiveColors.warning },
  { group: 'رنگ وضعیت', token: '--ds-color-status-warning-foreground', label: 'متن هشدار', value: 'خودکار بر پایه کنتراست', swatch: '#FFFFFF' },
  { group: 'رنگ وضعیت', token: '--ds-color-status-danger', label: 'خطا', value: primitiveColors.danger, swatch: primitiveColors.danger },
  { group: 'رنگ وضعیت', token: '--ds-color-status-danger-foreground', label: 'متن خطا', value: 'خودکار بر پایه کنتراست', swatch: '#FFFFFF' },
])
