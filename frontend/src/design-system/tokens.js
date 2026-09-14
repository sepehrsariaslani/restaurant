const freeze = (value) => Object.freeze(value)

const primitiveColors = freeze({
  primary: '#6F4A31',
  accent: '#C98D42',
  surface: '#FBF8F4',
  surfaceAlt: '#F1E7DB',
  background: '#F6F1EA',
  border: '#D5C3AF',
  text: '#3F2A1D',
  textSecondary: '#654A38',
  muted: '#846B58',
  success: '#2F8F5B',
  danger: '#B84F4F',
  warning: '#C67B2A',
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
      surface: freeze({ page: '--ds-color-bg-page', default: primitiveColors.background, base: '--ds-color-surface', raised: '--ds-color-surface-raised', muted: '--ds-color-surface-muted' }),
      text: freeze({ primary: '--ds-color-text-primary', secondary: '--ds-color-text-secondary', muted: '--ds-color-text-muted', inverse: '--ds-color-text-inverse' }),
      action: freeze({ primary: '--ds-color-action-primary', accent: '--ds-color-action-accent', focus: '--ds-color-focus-ring' }),
      status: freeze({ success: '--ds-color-status-success', warning: '--ds-color-status-warning', danger: '--ds-color-status-danger', info: '--ds-color-status-info' }),
    }),
  }),
  spacing: freeze({ '0': '0', '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px', '6': '24px', '8': '32px', '10': '40px', '12': '48px', '16': '64px' }),
  radius: freeze({ sm: '10px', md: '14px', lg: '18px', xl: '24px', pill: '999px' }),
  shadow: freeze({ none: 'none', sm: '0 8px 24px rgb(52 38 31 / 0.06)', md: '0 18px 40px rgb(52 38 31 / 0.10)', lg: '0 28px 70px rgb(52 38 31 / 0.14)' }),
  motion: freeze({ fast: '160ms', normal: '240ms', slow: '360ms', easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }),
  zIndex: freeze({ base: 0, sticky: 50, dropdown: 100, drawer: 200, modal: 500, overlay: 1100 }),
})

export const tokenRows = freeze([
  { group: 'رنگ معنایی', token: '--ds-color-bg-page', label: 'پس‌زمینه صفحه', value: primitiveColors.background, swatch: primitiveColors.background },
  { group: 'رنگ معنایی', token: '--ds-color-surface', label: 'سطح پایه', value: primitiveColors.surface, swatch: primitiveColors.surface },
  { group: 'رنگ معنایی', token: '--ds-color-action-primary', label: 'عمل اصلی', value: primitiveColors.primary, swatch: primitiveColors.primary },
  { group: 'رنگ معنایی', token: '--ds-color-action-accent', label: 'اکسنت', value: primitiveColors.accent, swatch: primitiveColors.accent },
  { group: 'رنگ معنایی', token: '--ds-color-text-primary', label: 'متن اصلی', value: primitiveColors.text, swatch: primitiveColors.text },
  { group: 'رنگ وضعیت', token: '--ds-color-status-success', label: 'موفقیت', value: primitiveColors.success, swatch: primitiveColors.success },
  { group: 'رنگ وضعیت', token: '--ds-color-status-warning', label: 'هشدار', value: primitiveColors.warning, swatch: primitiveColors.warning },
  { group: 'رنگ وضعیت', token: '--ds-color-status-danger', label: 'خطا', value: primitiveColors.danger, swatch: primitiveColors.danger },
])
