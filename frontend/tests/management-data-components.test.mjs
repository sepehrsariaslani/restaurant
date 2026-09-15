import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'

const readOptional = (url) => (existsSync(url) ? readFileSync(url, 'utf8') : '')

const smartTable = readFileSync(new URL('../src/components/management/ManagementSmartDataTable.vue', import.meta.url), 'utf8')
const editableTable = readFileSync(new URL('../src/components/management/ManagementEditableTable.vue', import.meta.url), 'utf8')
const bomItemsTable = readFileSync(new URL('../src/components/management/catalog/ManagementBomItemsTable.vue', import.meta.url), 'utf8')
const listView = readFileSync(new URL('../src/components/management/ManagementListView.vue', import.meta.url), 'utf8')
const dataTable = readFileSync(new URL('../src/components/management/ManagementDataTable.vue', import.meta.url), 'utf8')
const catalog = readFileSync(new URL('../src/design-system/catalog.js', import.meta.url), 'utf8')
const showcase = readFileSync(new URL('../src/pages/management/design-system/ManagementDesignSystemPage.vue', import.meta.url), 'utf8')
const productCollectionShell = readOptional(new URL('../src/components/management/catalog/ManagementProductCollectionShell.vue', import.meta.url))
const productDetailShell = readOptional(new URL('../src/components/management/catalog/ManagementProductDetailShell.vue', import.meta.url))
const productsPage = readFileSync(new URL('../src/pages/management/catalog/ManagementProductsPage.vue', import.meta.url), 'utf8')
const productDetail = readFileSync(new URL('../src/pages/management/catalog/ManagementProductDetailPage.vue', import.meta.url), 'utf8')
const variantBuilder = readFileSync(new URL('../src/pages/management/catalog/ManagementVariantBuilderPage.vue', import.meta.url), 'utf8')
const inventory = readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryPage.vue', import.meta.url), 'utf8')
const purchaseDetail = readFileSync(new URL('../src/pages/management/purchasing/ManagementInventoryPurchaseDetailPage.vue', import.meta.url), 'utf8')
const coverageDoc = readFileSync(new URL('../../docs/restaurant-management-coverage.md', import.meta.url), 'utf8')
const additionalDataPages = [
  readFileSync(new URL('../src/pages/management/finance/ManagementReportsIndexPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryMaterialDetailPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/purchasing/ManagementMaterialRequestDetailPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/sales/ManagementPosProfilePage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/sales/ManagementPosDefaultsPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/sales/ManagementRegisterPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/sales/ManagementSalesDashboardPage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/pages/management/builder/ManagementBuilderTemplatePage.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/components/management/tables/ManagementReservationsPanel.vue', import.meta.url), 'utf8'),
  readFileSync(new URL('../src/components/management/tables/ManagementSessionsPanel.vue', import.meta.url), 'utf8'),
]

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

test('Restaurant SmartDataTable fills its parent and only overflows inside the table viewport', () => {
  assert.match(smartTable, /\.smart-data-table\s*\{[^}]*width:\s*100%/, 'the table root must participate in the full-width parent layout')
  assert.match(smartTable, /\.smart-data-table__scroll\s*\{[^}]*width:\s*100%[^}]*max-width:\s*100%[^}]*min-width:\s*0/, 'overflow must stay inside a full-width scroll viewport')
  assert.match(smartTable, /\.smart-data-table__table\s*\{[^}]*width:\s*max-content[^}]*min-width:\s*100%/, 'the table must fill narrow parents and grow only when its columns need more room')
  assert.match(smartTable, /maxWidth: column\.maxWidth \|\| undefined/, 'default columns must not be capped at their preferred width')
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

test('product BOM materials use one canonical heading and a versioned table view', () => {
  assert.equal((productDetail.match(/جدول مواد BOM/g) || []).length, 0, 'the product page must not duplicate the materials heading outside the table component')
  assert.match(bomItemsTable, /storage-key="restaurant:bom-items:v2"/, 'BOM columns need a versioned storage key so stale visibility settings cannot hide the table')
  assert.match(bomItemsTable, /title="جدول مواد فرمول"/, 'the reusable formula table must own the single materials heading')
  assert.match(productDetail, /v-if="productBoms\.length > 1"/, 'the existing BOM list should only appear when there is more than one BOM to switch between')
})

test('all shared management list facades resolve to SmartDataTable', () => {
  assert.match(listView, /import ManagementSmartDataTable/)
  assert.match(listView, /<ManagementSmartDataTable/)
  assert.match(dataTable, /import ManagementSmartDataTable/)
  assert.match(dataTable, /<ManagementSmartDataTable/)
  assert.doesNotMatch(listView, /import ManagementDataTable/)
})

test('data-table components are discoverable in the Restaurant design-system showcase', () => {
  assert.match(catalog, /management-smart-table/)
  assert.match(catalog, /management-editable-table/)
  assert.match(showcase, /import ManagementSmartDataTable/)
  assert.match(showcase, /import ManagementEditableTable/)
  assert.match(showcase, /<ManagementSmartDataTable/)
  assert.match(showcase, /<ManagementEditableTable/)
})

test('product reference shells are reusable in routes and the design-system catalog', () => {
  assert.match(productCollectionShell, /defineProps/, 'collection shell must expose a stable prop contract')
  assert.match(productCollectionShell, /#toolbar|name="toolbar"/, 'collection shell must expose a toolbar slot')
  assert.match(productCollectionShell, /#overlays|name="overlays"/, 'collection shell must expose an overlays slot')
  assert.match(productCollectionShell, /@click="\$emit\('retry'\)"/, 'collection shell must expose a working retry action')
  assert.doesNotMatch(productCollectionShell, /\$attrs\.onRetry/, 'collection retry must not depend on declared emits being present in attrs')
  assert.doesNotMatch(productCollectionShell, /v-if="!loading && !error"[^>]*class="product-reference-shell__body"/, 'collection content must stay mounted while loading')
  assert.match(productDetailShell, /defineProps/, 'detail shell must expose a stable prop contract')
  for (const slot of ['breadcrumb', 'hero', 'navigation', 'overlays']) {
    assert.match(productDetailShell, new RegExp(`name=["']${slot}["']`), `${slot} slot must remain part of the detail contract`)
  }
  assert.doesNotMatch(productDetailShell, /v-if="!loading && !error"[^>]*class="product-reference-shell__body"/, 'detail content must stay mounted while loading')
  assert.match(catalog, /management-product-collection-shell/)
  assert.match(catalog, /management-product-detail-shell/)
  assert.match(catalog, /product-collection-shell/)
  assert.match(catalog, /product-detail-shell/)
  assert.match(showcase, /ManagementProductCollectionShell/)
  assert.match(showcase, /ManagementProductDetailShell/)
  assert.match(productsPage, /ManagementProductCollectionShell/)
  assert.match(productDetail, /ManagementProductDetailShell/)
})

test('management data pages use shared table owners for internal data grids', () => {
  for (const [name, source] of [
    ['product detail', productDetail],
    ['variant builder', variantBuilder],
    ['inventory', inventory],
    ['purchase detail', purchaseDetail],
  ]) {
    assert.match(source, /ManagementSmartDataTable/, `${name} should use SmartDataTable for internal grids`)
    assert.doesNotMatch(source, /<table\b/, `${name} should not introduce a parallel raw data table`)
  }
})

test('coverage documentation records the canonical table ownership chain and exceptions', () => {
  assert.match(coverageDoc, /ManagementSmartDataTable/)
  assert.match(coverageDoc, /ManagementEditableTable/)
  assert.match(coverageDoc, /ManagementProductCollectionShell/)
  assert.match(coverageDoc, /ManagementProductDetailShell/)
  assert.match(coverageDoc, /ManagementSheetView/)
  assert.match(coverageDoc, /جدول میانبرهای صفحهٔ POS/)
})

test('additional management collections use the shared table owners', () => {
  for (const source of additionalDataPages) {
    assert.match(source, /ManagementSmartDataTable|ManagementListView|ManagementEditableTable/)
  }
})
