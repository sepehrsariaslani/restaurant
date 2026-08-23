import test from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizePosSearchText,
  searchCustomersInRows,
  createOfflineOrderRecord,
  mergeQueueRecords,
  createPosOfflineStore,
} from '../src/utils/posOfflineStore.js'

test('normalizes Persian/Arabic text and digits for customer search', () => {
  assert.equal(normalizePosSearchText('  ياسر  '), 'یاسر')
  assert.equal(normalizePosSearchText('۰۹۱۲ ۱۲۳ ۴۵۶۷'), '0912 123 4567')
  assert.equal(normalizePosSearchText('كاظم'), 'کاظم')
})

test('searches cached customers by normalized name and compact mobile', () => {
  const rows = [
    { key: 'CUST-1', label: 'یاسر رضایی', customer_name: 'یاسر رضایی', mobile: '0912 123 4567', orders_count: 4 },
    { key: 'CUST-2', label: 'کاظم احمدی', mobile: '09350000000', orders_count: 1 },
  ]
  assert.equal(searchCustomersInRows(rows, 'ياسر').length, 1)
  assert.equal(searchCustomersInRows(rows, '۱۲۳۴۵۶۷').length, 1)
  assert.equal(searchCustomersInRows(rows, 'كاظم')[0].key, 'CUST-2')
})

test('creates idempotent pending records and deduplicates queue by id', () => {
  const record = createOfflineOrderRecord({ items: [{ item_name: 'A', qty: 1 }] }, 'pos-test-1', () => 100)
  assert.equal(record.id, 'pos-test-1')
  assert.equal(record.status, 'pending')
  assert.equal(record.payload.client_order_key, 'pos-test-1')
  assert.equal(record.created_at, 100)

  const updated = { ...record, status: 'needs_attention', last_error: 'stock changed', updated_at: 200 }
  const merged = mergeQueueRecords([record], [updated, record])
  assert.equal(merged.length, 1)
  assert.equal(merged[0].status, 'needs_attention')
  assert.equal(merged[0].last_error, 'stock changed')
})

test('degrades safely when IndexedDB is unavailable', async () => {
  const store = createPosOfflineStore({ indexedDB: null, now: () => 123 })
  assert.equal(await store.loadPosBootSnapshot('main'), null)
  assert.deepEqual(await store.searchCachedCustomers('یاسر'), [])
  assert.deepEqual(await store.listPendingOfflineOrders(), [])
  assert.equal(await store.pendingOrderCount(), 0)
  const queued = await store.enqueueOfflineOrder({ items: [{ item_name: 'A', qty: 1 }] }, 'pos-safe')
  assert.equal(queued.id, 'pos-safe')
  assert.equal(queued.payload.client_order_key, 'pos-safe')
  assert.equal(await store.savePosBootSnapshot('main', { items: [] }), false)
})
