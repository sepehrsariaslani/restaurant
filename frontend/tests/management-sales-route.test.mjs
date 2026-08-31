import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const hooks = readFileSync(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8')

test('management sales has a protected Frappe route and SPA bootstrap page', () => {
  assert.match(hooks, /\{"from_route": "\/management\/sales", "to_route": "management\/sales"\}/)
  const page = readFileSync(new URL('../../restaurant/www/management/sales.html', import.meta.url), 'utf8')
  const context = readFileSync(new URL('../../restaurant/www/management/sales.py', import.meta.url), 'utf8')
  assert.match(page, /window\._PAGE = 'management-sales-dashboard'/)
  assert.match(context, /build_context\(context, "management-sales"\)/)
})
