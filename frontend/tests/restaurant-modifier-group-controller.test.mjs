import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(
  new URL('../../restaurant/restaurant/doctype/restaurant_modifier_group/restaurant_modifier_group.py', import.meta.url),
  'utf8',
)

test('single modifier groups preserve explicit min_select independent of required flag', () => {
  assert.doesNotMatch(
    source,
    /self\.min_select\s*=\s*1\s+if\s+self\.required\s+else\s+0/,
    'single selection must not overwrite an explicit min_select value from Desk',
  )
  assert.match(source, /if self\.selection_mode == "single":[\s\S]*self\.max_select = 1/)
})
