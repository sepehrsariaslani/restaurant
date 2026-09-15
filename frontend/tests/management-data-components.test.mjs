import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const smartTable = readFileSync(new URL('../src/components/management/ManagementSmartDataTable.vue', import.meta.url), 'utf8')
const editableTable = readFileSync(new URL('../src/components/management/ManagementEditableTable.vue', import.meta.url), 'utf8')
const catalog = readFileSync(new URL('../src/design-system/catalog.js', import.meta.url), 'utf8')
const showcase = readFileSync(new URL('../src/pages/management/design-system/ManagementDesignSystemPage.vue', import.meta.url), 'utf8')

test('Restaurant SmartDataTable keeps the Accounts table contract with Restaurant-native behavior', () => {
  for (const token of [
    'filterable',
    'stickyHeader',
    'maxHeight',
    'rowActions',
    'expandedRowKeys',
    'frozenStorageKey',
    'columnWidthStorageKey',
    'sort-change',
    'row-toggle',
    'row-action',
    'cell-${column.key}',
    'cell.${column.key}',
  ]) {
    assert.match(smartTable, new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), `${token} must remain supported`)
  }
  assert.match(smartTable, /--mg-primary/, 'table styles must use Restaurant semantic tokens')
  assert.doesNotMatch(smartTable, /@\/components\/design\/StatePanel/, 'Restaurant must not import Accounts-only StatePanel')
})

test('Restaurant EditableTable keeps v-model/editor validation and adds persistent column settings', () => {
  for (const token of [
    'modelValue',
    'createEmptyRow',
    'normalizeRow',
    'validateRow',
    'update:modelValue',
    'row-update',
    'row-delete',
    'row-add',
    'showColumnSettings',
    'storageKey',
    'ManagementSmartDataTable',
  ]) {
    assert.match(editableTable, new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), `${token} must remain supported`)
  }
  assert.match(editableTable, /cell\.\$\{column\.key\}/, 'legacy dotted slot names should remain usable')
  assert.match(editableTable, /localStorage/, 'column visibility should persist per table')
})

test('data-table components are discoverable in the Restaurant design-system showcase', () => {
  assert.match(catalog, /management-smart-table/)
  assert.match(catalog, /management-editable-table/)
  assert.match(showcase, /import ManagementSmartDataTable/)
  assert.match(showcase, /import ManagementEditableTable/)
  assert.match(showcase, /<ManagementSmartDataTable/)
  assert.match(showcase, /<ManagementEditableTable/)
})
