const DB_NAME = 'restaurant-pos-offline-v1'
const DB_VERSION = 1
const SNAPSHOT_STORE = 'snapshots'
const CUSTOMER_STORE = 'customers'
const ORDER_QUEUE_STORE = 'order_queue'

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'

export function normalizePosSearchText(value) {
  return String(value ?? '')
    .replace(/[۰-۹]/g, (char) => String(PERSIAN_DIGITS.indexOf(char)))
    .replace(/[٠-٩]/g, (char) => String(ARABIC_DIGITS.indexOf(char)))
    .replace(/ي/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/ة/g, 'ه')
    .replace(/\u200c/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
}

function compactSearchText(value) {
  return normalizePosSearchText(value).replace(/[\s()\-+_.]/g, '')
}

function customerSearchHaystack(row) {
  const values = [row?.key, row?.name, row?.customer, row?.customer_name, row?.label, row?.mobile, row?.phone]
  return values.filter(Boolean).map(normalizePosSearchText).join(' ')
}

export function searchCustomersInRows(rows, query, limit = 20) {
  const source = Array.isArray(rows) ? rows : []
  const normalizedQuery = normalizePosSearchText(query)
  const compactQuery = compactSearchText(query)
  if (!normalizedQuery) return source.slice(0, Math.max(0, Number(limit) || 20))

  const matches = source.filter((row) => {
    const haystack = customerSearchHaystack(row)
    if (haystack.includes(normalizedQuery)) return true
    return compactQuery && compactSearchText(haystack).includes(compactQuery)
  })
  return matches.slice(0, Math.max(0, Number(limit) || 20))
}

function makeCustomerKey(row) {
  const explicit = String(row?.key || row?.name || row?.customer || '').trim()
  if (explicit) return explicit
  const mobile = compactSearchText(row?.mobile || row?.phone || '')
  if (mobile) return `mobile:${mobile}`
  const label = normalizePosSearchText(row?.label || row?.customer_name || '')
  return label ? `label:${label}` : ''
}

function normalizeCustomerRow(row, now = Date.now()) {
  const key = makeCustomerKey(row)
  if (!key) return null
  return {
    ...row,
    key,
    label: String(row?.label || row?.customer_name || row?.name || '').trim(),
    mobile: String(row?.mobile || row?.phone || '').trim(),
    cached_at: Number(row?.cached_at || now),
  }
}

function generateClientOrderKey(now = Date.now()) {
  try {
    if (globalThis.crypto?.randomUUID) return `pos-${globalThis.crypto.randomUUID()}`
  } catch (_) {}
  return `pos-${now}-${Math.random().toString(36).slice(2, 10)}`
}

export function createOfflineOrderRecord(payload, id = '', nowFn = () => Date.now()) {
  const timestamp = Number(nowFn()) || Date.now()
  const key = String(id || payload?.client_order_key || generateClientOrderKey(timestamp)).trim()
  const safePayload = payload && typeof payload === 'object' ? { ...payload } : {}
  safePayload.client_order_key = key
  return {
    id: key,
    payload: safePayload,
    status: 'pending',
    created_at: timestamp,
    updated_at: timestamp,
    retry_count: 0,
    last_error: '',
  }
}

export function mergeQueueRecords(current, incoming) {
  const byId = new Map()
  for (const row of [...(Array.isArray(current) ? current : []), ...(Array.isArray(incoming) ? incoming : [])]) {
    const id = String(row?.id || '').trim()
    if (!id) continue
    const previous = byId.get(id)
    if (!previous || Number(row?.updated_at || 0) >= Number(previous?.updated_at || 0)) byId.set(id, { ...row, id })
  }
  return [...byId.values()].sort((a, b) => Number(a.created_at || 0) - Number(b.created_at || 0))
}

function requestResult(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('IndexedDB request failed'))
  })
}

function transactionDone(transaction) {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve(true)
    transaction.onabort = () => reject(transaction.error || new Error('IndexedDB transaction aborted'))
    transaction.onerror = () => reject(transaction.error || new Error('IndexedDB transaction failed'))
  })
}

export function createPosOfflineStore({ indexedDB: indexedDBOption, now = () => Date.now() } = {}) {
  const factory = indexedDBOption === null
    ? null
    : (indexedDBOption || (typeof globalThis !== 'undefined' ? globalThis.indexedDB : null))
  let dbPromise = null

  function openDatabase() {
    if (!factory) return Promise.resolve(null)
    if (dbPromise) return dbPromise
    dbPromise = new Promise((resolve, reject) => {
      let request
      try {
        request = factory.open(DB_NAME, DB_VERSION)
      } catch (error) {
        reject(error)
        return
      }
      request.onupgradeneeded = () => {
        const db = request.result
        if (!db.objectStoreNames.contains(SNAPSHOT_STORE)) db.createObjectStore(SNAPSHOT_STORE, { keyPath: 'key' })
        if (!db.objectStoreNames.contains(CUSTOMER_STORE)) db.createObjectStore(CUSTOMER_STORE, { keyPath: 'key' })
        if (!db.objectStoreNames.contains(ORDER_QUEUE_STORE)) db.createObjectStore(ORDER_QUEUE_STORE, { keyPath: 'id' })
      }
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error || new Error('Unable to open POS offline database'))
      request.onblocked = () => reject(new Error('POS offline database upgrade is blocked'))
    }).catch(() => null)
    return dbPromise
  }

  async function withStore(storeName, mode, action, fallback) {
    const db = await openDatabase()
    if (!db) return fallback
    try {
      const transaction = db.transaction(storeName, mode)
      const store = transaction.objectStore(storeName)
      const result = await action(store, transaction)
      if (mode !== 'readonly') await transactionDone(transaction)
      return result
    } catch (_) {
      return fallback
    }
  }

  const snapshotKey = (branch) => `pos_boot:${String(branch || 'default').trim() || 'default'}`

  async function savePosBootSnapshot(branch, payload) {
    const record = { key: snapshotKey(branch), payload, updated_at: Number(now()) || Date.now() }
    return withStore(SNAPSHOT_STORE, 'readwrite', async (store) => {
      store.put(record)
      return true
    }, false)
  }

  async function loadPosBootSnapshot(branch) {
    return withStore(SNAPSHOT_STORE, 'readonly', (store) => requestResult(store.get(snapshotKey(branch))), null)
  }

  async function readAllCustomers() {
    return withStore(CUSTOMER_STORE, 'readonly', async (store) => {
      const rows = await requestResult(store.getAll())
      return Array.isArray(rows) ? rows : []
    }, [])
  }

  async function replaceCustomerCache(rows) {
    const normalized = (Array.isArray(rows) ? rows : []).map((row) => normalizeCustomerRow(row, Number(now()) || Date.now())).filter(Boolean)
    return withStore(CUSTOMER_STORE, 'readwrite', async (store) => {
      store.clear()
      normalized.forEach((row) => store.put(row))
      return normalized.length
    }, 0)
  }

  async function mergeCustomerCache(rows) {
    const normalized = (Array.isArray(rows) ? rows : []).map((row) => normalizeCustomerRow(row, Number(now()) || Date.now())).filter(Boolean)
    return withStore(CUSTOMER_STORE, 'readwrite', async (store) => {
      normalized.forEach((row) => store.put(row))
      return normalized.length
    }, 0)
  }

  async function searchCachedCustomers(query, limit = 20) {
    return searchCustomersInRows(await readAllCustomers(), query, limit)
  }

  async function enqueueOfflineOrder(payload, id = '') {
    const record = createOfflineOrderRecord(payload, id, now)
    const persisted = await withStore(ORDER_QUEUE_STORE, 'readwrite', async (store) => {
      store.put(record)
      return true
    }, false)
    return { ...record, persisted: Boolean(persisted) }
  }

  async function listPendingOfflineOrders() {
    return withStore(ORDER_QUEUE_STORE, 'readonly', async (store) => {
      const rows = await requestResult(store.getAll())
      return (Array.isArray(rows) ? rows : [])
        .filter((row) => row?.status === 'pending')
        .sort((a, b) => Number(a.created_at || 0) - Number(b.created_at || 0))
    }, [])
  }

  async function pendingOrderCount() {
    return (await listPendingOfflineOrders()).length
  }

  async function markOfflineOrderSynced(id) {
    const key = String(id || '').trim()
    if (!key) return false
    return withStore(ORDER_QUEUE_STORE, 'readwrite', async (store) => {
      store.delete(key)
      return true
    }, false)
  }

  async function markOfflineOrderNeedsAttention(id, error = '') {
    const key = String(id || '').trim()
    if (!key) return false
    return withStore(ORDER_QUEUE_STORE, 'readwrite', async (store) => {
      const row = await requestResult(store.get(key))
      if (!row) return false
      store.put({
        ...row,
        status: 'needs_attention',
        retry_count: Number(row.retry_count || 0) + 1,
        last_error: String(error || '').trim(),
        updated_at: Number(now()) || Date.now(),
      })
      return true
    }, false)
  }

  return {
    savePosBootSnapshot,
    loadPosBootSnapshot,
    replaceCustomerCache,
    mergeCustomerCache,
    searchCachedCustomers,
    enqueueOfflineOrder,
    listPendingOfflineOrders,
    markOfflineOrderSynced,
    markOfflineOrderNeedsAttention,
    pendingOrderCount,
  }
}
