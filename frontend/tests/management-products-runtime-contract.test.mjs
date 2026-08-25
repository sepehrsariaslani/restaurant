import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('../src/pages/management/ManagementProductsPage.vue', import.meta.url), 'utf8')

test('management products page defines runtime refs used by the template and watchers', () => {
  for (const identifier of [
    'visibleProducts',
    'groupedProducts',
    'isMobileView',
    'activeViewTitle',
    'activeViewSubtitle',
  ]) {
    assert.match(source, new RegExp(`const\\s+${identifier}\\s*=`), `${identifier} must be defined`)
  }
  assert.match(source, /function\s+compareProducts\s*\(/, 'compareProducts must be defined')
})
