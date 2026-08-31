import test from 'node:test'
import assert from 'node:assert/strict'
import { createOfflineSyncEngine } from '../src/utils/offlineSyncEngine.js'

function createStore(records) {
  const rows = records.map((row) => ({ ...row, payload: { client_order_key: row.id } }))
  const synced = []
  const pending = []
  const attention = []
  return {
    synced,
    pending,
    attention,
    async listPendingOfflineOrders() {
      return rows.filter((row) => row.status !== 'synced' && row.status !== 'needs_attention')
    },
    async markOfflineOrderSynced(id) {
      synced.push(id)
      const row = rows.find((item) => item.id === id)
      if (row) row.status = 'synced'
    },
    async markOfflineOrderPending(id, error) {
      pending.push({ id, error })
    },
    async markOfflineOrderNeedsAttention(id, error) {
      attention.push({ id, error })
      const row = rows.find((item) => item.id === id)
      if (row) row.status = 'needs_attention'
    },
  }
}

test('replays pending orders in creation order and accepts idempotent existing responses', async () => {
  const store = createStore([
    { id: 'later', created_at: 2 },
    { id: 'first', created_at: 1 },
  ])
  const calls = []
  const engine = createOfflineSyncEngine({
    store,
    replayOrder: async (payload) => {
      calls.push(payload.client_order_key)
      return { status: payload.client_order_key === 'first' ? 'created' : 'existing' }
    },
  })

  assert.deepEqual(await engine.syncPendingOrders(), {
    synced: 2,
    pending: 0,
    needsAttention: 0,
    skipped: false,
  })
  assert.deepEqual(calls, ['first', 'later'])
  assert.deepEqual(store.synced, ['first', 'later'])
})

test('keeps a transport failure pending but sends a business error for review', async () => {
  const store = createStore([{ id: 'network', created_at: 1 }, { id: 'conflict', created_at: 2 }])
  const engine = createOfflineSyncEngine({
    store,
    replayOrder: async (payload) => {
      if (payload.client_order_key === 'network') throw new TypeError('Failed to fetch')
      throw { status: 422, message: 'price changed' }
    },
  })

  assert.deepEqual(await engine.syncPendingOrders(), {
    synced: 0,
    pending: 1,
    needsAttention: 1,
    skipped: false,
  })
  assert.deepEqual(store.pending, [{ id: 'network', error: 'Failed to fetch' }])
  assert.deepEqual(store.attention, [{ id: 'conflict', error: 'price changed' }])
})

test('shares one in-flight run so reconnect events cannot replay a queue twice', async () => {
  const store = createStore([{ id: 'only', created_at: 1 }])
  let calls = 0
  let release
  const engine = createOfflineSyncEngine({
    store,
    replayOrder: () => {
      calls += 1
      return new Promise((resolve) => { release = () => resolve({ status: 'created' }) })
    },
  })

  const first = engine.syncPendingOrders()
  const second = engine.syncPendingOrders()
  await Promise.resolve()
  release()
  await Promise.all([first, second])
  assert.equal(calls, 1)
})
