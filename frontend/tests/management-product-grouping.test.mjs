import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildItemGroupOptions,
  getChildItemGroupOptions,
  resolveItemGroupSelection,
} from '../src/utils/managementProductGrouping.js'

const itemGroups = [
  { name: 'Food', item_group_name: 'غذا', parent_item_group: 'All Item Groups', is_group: 1 },
  { name: 'Pizza', item_group_name: 'پیتزا', parent_item_group: 'Food', is_group: 0 },
  { name: 'Burger', item_group_name: 'برگر', parent_item_group: 'Food', is_group: 0 },
  { name: 'Drink', item_group_name: 'نوشیدنی', parent_item_group: 'All Item Groups', is_group: 0 },
]

test('item group options expose one native hierarchy with readable paths', () => {
  assert.deepEqual(buildItemGroupOptions(itemGroups), [
    { value: 'Burger', label: 'غذا / برگر', parentValue: 'Food', parentLabel: 'غذا' },
    { value: 'Drink', label: 'نوشیدنی', parentValue: 'All Item Groups', parentLabel: 'همه گروه‌ها' },
    { value: 'Pizza', label: 'غذا / پیتزا', parentValue: 'Food', parentLabel: 'غذا' },
  ])
})

test('item group children are filtered from the same native source', () => {
  assert.deepEqual(getChildItemGroupOptions(itemGroups, 'Food').map((row) => row.value), ['Burger', 'Pizza'])
})

test('selected item group resolves parent and final leaf without restaurant category fields', () => {
  assert.deepEqual(resolveItemGroupSelection(itemGroups, 'Pizza'), {
    itemGroup: 'Pizza',
    parentItemGroup: 'Food',
    path: 'غذا / پیتزا',
  })
})
