import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('../src/pages/management/ManagementProductsPage.vue', import.meta.url), 'utf8')
const safeApiSource = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')

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

test('management products page requests products in bounded pages', () => {
  assert.match(source, /const\s+PRODUCT_PAGE_SIZE\s*=\s*80/, 'initial product page size should stay bounded')
  assert.match(source, /limit_page_length:\s*PRODUCT_PAGE_SIZE/, 'product request should pass page length')
  assert.match(source, /limit_start:\s*append\s*\?\s*products\.value\.length\s*:\s*0/, 'product request should pass offset')
  assert.match(source, /search:\s*search\.value/, 'search should be sent to the server-side query')
  assert.match(source, /hasMoreProducts/, 'page should track whether more products can be loaded')
  assert.match(safeApiSource, /limit_page_length\s*=\s*80/, 'safe API wrapper should default to a bounded page size')
  assert.match(safeApiSource, /limit_start/, 'safe API wrapper should pass offset to the server')
})

test('management products page refreshes server search after typing', () => {
  assert.match(source, /let\s+searchDebounceTimer\s*=\s*null/, 'search debounce timer should be tracked')
  assert.match(source, /watch\(\s*\(\)\s*=>\s*search\.value/, 'search input should be watched')
  assert.match(source, /setTimeout\(\s*\(\)\s*=>\s*loadProducts\(\)/, 'typing should trigger a fresh server query')
  assert.match(source, /clearTimeout\(searchDebounceTimer\)/, 'pending search refresh should be cancelled before scheduling another one')
})
