import test from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizePosSearchText,
  searchCustomersInRows,
  createOfflineOrderRecord,
  createOfflineMutationRecord,
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
  assert.equal(queued.persisted, false)
  assert.equal(queued.payload.client_order_key, 'pos-safe')
  assert.equal(await store.savePosBootSnapshot('main', { items: [] }), false)
})

test('exposes non-destructive queue retry and review counters when storage is unavailable', async () => {
  const store = createPosOfflineStore({ indexedDB: null, now: () => 123 })
  assert.equal(await store.markOfflineOrderPending('pos-safe', 'network failed'), false)
  assert.deepEqual(await store.listOfflineOrders(), [])
  assert.equal(await store.needsAttentionOrderCount(), 0)
})

test('creates stable FIFO mutations for offline table and provisional-payment work', () => {
  const mutation = createOfflineMutationRecord(
    'table_add_items',
    { table_name: 'TABLE-1', items: [{ item_code: 'TEA', qty: 1 }] },
    'mutation-table-1',
    () => 100,
  )
  assert.equal(mutation.id, 'mutation-table-1')
  assert.equal(mutation.type, 'table_add_items')
  assert.equal(mutation.status, 'pending')
  assert.equal(mutation.payload.client_mutation_key, 'mutation-table-1')
})

test('exposes mutation retry and review state without silently discarding it', async () => {
  const store = createPosOfflineStore({ indexedDB: null, now: () => 123 })
  const queued = await store.enqueueOfflineMutation('table_add_items', { table_name: 'TABLE-1' }, 'mutation-safe')

  assert.equal(queued.persisted, false)
  assert.deepEqual(await store.listOfflineMutations(), [])
  assert.equal(await store.pendingMutationCount(), 0)
  assert.equal(await store.needsAttentionMutationCount(), 0)
  assert.equal(await store.markOfflineMutationPending('mutation-safe', 'network failed'), false)
  assert.equal(await store.markOfflineMutationNeedsAttention('mutation-safe', 'price changed'), false)
})
