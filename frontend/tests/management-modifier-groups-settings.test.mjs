import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(
  new URL('../src/components/management/ManagementModifierGroupsSettings.vue', import.meta.url),
  'utf8',
)
const apiSource = fs.readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')

test('modifier group editor does not require manual price delta or option item for add-on options', () => {
  assert.doesNotMatch(source, /key:\s*['"]price_delta['"]/, 'price delta column should not be shown in modifier group editor')
  assert.doesNotMatch(source, /برای گزینه افزودنی باید آیتم انتخاب شود/, 'add-on options should be saved without manual item selection')
  assert.match(source, /آیتم مصرف\/تولید/, 'linked item field should be framed as stock/production, not pricing')
})

test('modifier group save auto-links missing add-on option items', () => {
  assert.match(apiSource, /_ensure_modifier_option_item/, 'server should create or reuse an item for missing add-on option items')
  assert.match(apiSource, /option_item = _ensure_modifier_option_item/, 'save path should auto-fill missing option_item values')
})
