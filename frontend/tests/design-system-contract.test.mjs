import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const sourceRoot = new URL('../src/', import.meta.url)
const tokensSource = fs.readFileSync(new URL('design-system/tokens.js', sourceRoot), 'utf8')
const catalogSource = fs.readFileSync(new URL('design-system/catalog.js', sourceRoot), 'utf8')
const appSource = fs.readFileSync(new URL('App.vue', sourceRoot), 'utf8')
const themeSource = fs.readFileSync(new URL('theme.css', sourceRoot), 'utf8')
const layoutSource = fs.readFileSync(new URL('components/management/ManagementLayout.vue', sourceRoot), 'utf8')

test('design system tokens expose stable semantic layers for RTL restaurant UI', async () => {
  const { designTokens } = await import('../src/design-system/tokens.js')

  assert.equal(designTokens.direction, 'rtl')
  assert.equal(designTokens.font.family, 'Peyda')
  assert.ok(designTokens.color.primitive.primary)
  assert.ok(designTokens.color.semantic.surface.page)
  assert.ok(designTokens.color.semantic.text.primary)
  assert.ok(designTokens.spacing['4'])
  assert.ok(designTokens.radius.md)
  assert.ok(designTokens.shadow.sm)
  assert.ok(designTokens.motion.fast)
  assert.ok(designTokens.zIndex.overlay)
})

test('design system catalog contains the requested reference tabs and product surfaces', async () => {
  const { designSystemTabs, designSystemCatalog } = await import('../src/design-system/catalog.js')
  const tabIds = designSystemTabs.map((tab) => tab.id)

  assert.deepEqual(tabIds, ['theme', 'icons', 'components', 'patterns', 'templates'])
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'product-card'))
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'product-detail'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-search'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'products-list'))
})

test('design system route is registered in the management shell', () => {
  assert.match(appSource, /ManagementDesignSystemPage/)
  assert.match(appSource, /page === 'management-design-system'/)
  assert.match(appSource, /pathname\.startsWith\('\/management\/design-system'\)/)
  assert.match(layoutSource, /management-design-system/)
})

test('semantic design tokens are published as CSS variables while legacy aliases remain available', () => {
  for (const token of [
    '--ds-color-bg-page',
    '--ds-color-surface',
    '--ds-color-text-primary',
    '--ds-color-action-primary',
    '--ds-space-4',
    '--ds-radius-md',
    '--ds-shadow-sm',
    '--ds-motion-fast',
  ]) {
    assert.match(themeSource, new RegExp(`${token.replaceAll('-', '\\-')}\\s*:`), `${token} must be declared`)
  }
  assert.match(themeSource, /--accent-green:\s*var\(--ds-color-action-primary\)/)
  assert.match(themeSource, /--text-primary:\s*var\(--ds-color-text-primary\)/)
})

test('design system page declares all catalog tabs and reference language', () => {
  const pageSource = fs.readFileSync(new URL('../src/pages/management/ManagementDesignSystemPage.vue', import.meta.url), 'utf8')
  for (const label of ['تم و توکن‌ها', 'آیکون‌ها', 'کامپوننت‌ها', 'پترن‌ها', 'تمپلیت‌ها']) {
    assert.match(catalogSource, new RegExp(label))
  }
  assert.match(pageSource, /designSystemTabs/)
  assert.match(pageSource, /MenuProductCard/)
  assert.match(pageSource, /ManagementProductSummaryCard/)
  assert.match(pageSource, /prefers-reduced-motion/)
})

test('design primitives expose semantic variants and accessible async state', () => {
  const buttonSource = fs.readFileSync(new URL('../src/components/design/DsButton.vue', import.meta.url), 'utf8')
  const badgeSource = fs.readFileSync(new URL('../src/components/design/DsBadge.vue', import.meta.url), 'utf8')
  assert.match(buttonSource, /variant.*primary|primary.*variant/)
  assert.match(buttonSource, /aria-busy/)
  assert.match(buttonSource, /ds-button/)
  assert.match(badgeSource, /status|tone/)
  assert.match(badgeSource, /ds-badge/)
})
